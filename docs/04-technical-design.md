# Skillroom — Technical Design

**Lifecycle step:** 4 of 17 · **Locked:** 2026-09-17 · UI companion: [04-ui-mockups.md](04-ui-mockups.md). Schema and routes: [06-data-and-api.md](06-data-and-api.md).

## 1. Stack (shared stack, one addition: the worker)
| Layer | Choice | Notes |
|---|---|---|
| web/ | Next.js 15 App Router · TypeScript strict · Tailwind 4 · pnpm | UI only; `/api/*` rewritten to the API so cookies are same-origin. New: **`hls.js`**, `@vercel/blob` (client upload helper only — the token comes from the API) |
| api/ | FastAPI (Python 3.12, uv) · SQLAlchemy 2.0 async + Alembic · pydantic · pytest | Vercel FastAPI preset, `bom1`. New: `httpx`, **`fpdf2`** (certificates), `razorpay`, `python-multipart` |
| **worker/** | `api/app/worker/transcode.py` + **ffmpeg** | Same package as the API, never imported by it; runs on a **GitHub Actions** runner in prod (`.github/workflows/transcode.yml`), by hand locally. ffmpeg is never in the Vercel bundle |
| Data | Neon Postgres | Users, courses, videos + manifests, jobs, enrollments, orders, ledger, progress |
| Files | Vercel Blob | Video sources, HLS output (encrypted), posters, sprites, resources, certificate PDFs |
| Payments | Razorpay Standard Checkout (v1) + Subscriptions (v2), test mode | Orders, verify, webhooks, refunds |
| Email (v2) | Resend + React Email | Receipts, certificate, payout, approval, reset |
| Contract | `api/openapi.json` → `openapi-typescript` → `web/src/lib/api-types.ts` | `pnpm gen:api`; committed; not CI-gated |
| CI | GitHub Actions: `web` (typecheck + build), `api` (ruff + pytest with a Postgres service; the worker test runs because ubuntu runners ship ffmpeg) | Plus the `transcode` workflow, which is not CI — it is the worker |

## 2. Domain model
- `users(role student|creator|admin)` → `creator_profiles(status applied|approved|rejected, handle, display_name, area, bio, avatar_url, payout_note)`.
- `courses(creator_id, slug, title, subtitle, category, level, price_paise, description, cover_url, status draft|published|takedown, takedown_note)` → `sections(sort)` → `lessons(sort, is_preview, duration_s)` → **`videos`** (one per lesson: `source_url, prefix, key_hex, status none|queued|processing|ready|failed, manifest jsonb, poster_url, sprite_url, duration_s`) and `video_jobs(video_id, state, attempts, error, claimed_at, finished_at)`; `resources(lesson_id, name, url, size)`.
- `enrollments(user, course, source purchase|free|subscription|admin, order_id)`; `progress(user, lesson, position_s, watched_s, completed, updated_at)`; `certificates(code, user, course, pdf_url)`.
- `orders(number 'SR-####', user, course, amount_paise, state, razorpay ids)`; `ledger_entries(account 'platform'|'creator:{id}', kind sale|fee|refund|payout|pool_share, amount_paise signed, order_id?, payout_id?, period?)`. Balance = Σ entries per account, always computed, never stored.
- Money is integer paise; the web formats ₹.

## 3. The video pipeline (worker)
`python -m app.worker.transcode --job <id>` (or `--poll` to drain the queue locally):
1. **Claim:** `POST /internal/jobs/{id}/claim` (Bearer `WORKER_SECRET`) → `{ source_url, prefix, key_hex, iv_hex, lesson_id }`; the API flips `queued → processing`, `attempts + 1`, `claimed_at`. A job already `processing` for < 20 min → 409 (another runner has it).
2. **Download** the source to a temp dir with `httpx` (streamed).
3. **Probe:** `ffprobe -show_streams -show_format` → duration, width, height, has_audio. Sources shorter than 720p only get the renditions ≤ their height (never upscale); no audio → a silent AAC track is synthesised so the ladder stays uniform.
4. **Ladder + encryption** in one ffmpeg pass:
   ```
   ffmpeg -y -i src -filter_complex "[0:v]split=3[a][b][c];[a]scale=-2:240[v0];[b]scale=-2:480[v1];[c]scale=-2:720[v2]" \
     -map [v0] -map [v1] -map [v2] -map 0:a -map 0:a -map 0:a \
     -c:v libx264 -preset veryfast -profile:v main -g 144 -keyint_min 144 -sc_threshold 0 \
     -b:v:0 200k -maxrate:v:0 240k -bufsize:v:0 400k  -b:v:1 500k -maxrate:v:1 600k -bufsize:v:1 1000k  -b:v:2 1000k -maxrate:v:2 1200k -bufsize:v:2 2000k \
     -c:a aac -b:a 48k -ac 1 \
     -f hls -hls_time 6 -hls_playlist_type vod -hls_flags independent_segments \
     -hls_key_info_file key.info -hls_segment_filename "out/%v_%03d.ts" \
     -var_stream_map "v:0,a:0,name:240p v:1,a:1,name:480p v:2,a:2,name:720p" out/%v.m3u8
   ```
   `key.info` = the placeholder URI `KEY_URI`, the local `key.bin` (16 bytes from `key_hex`), and `iv_hex`. ffmpeg writes AES-128-CBC segments; the playlists it writes are only parsed for segment durations — **the API generates the playlists it serves**.
5. **Poster** at 10 % of the duration (`-frames:v 1 -vf scale=1280:-2`, JPEG q80) and a **sprite** (`fps=1/5, scale=160:-2, tile=10xN`, one frame every 5 s) with its geometry.
6. **Upload** to Blob: `video/{prefix}/{rendition}_{nnn}.ts`, `video/{prefix}/poster.jpg`, `video/{prefix}/sprite.jpg` (Blob REST `put`, 8 parallel, retried). `prefix` = 22 random URL-safe chars per video — unguessable, and the bytes are ciphertext anyway.
7. **Complete:** `POST /internal/jobs/{id}/complete { manifest }` where `manifest = { duration_s, width, height, iv_hex, renditions: [{ name, bandwidth, width, height, codecs, segments: [6.0, 6.0, …] }], poster_url, sprite: { url, cols, rows, w, h, interval_s } }`. The API sets `videos.status = ready`, `lessons.duration_s`, the course cover if unset, deletes the old prefix on a replacement, and revalidates. Any exception → `POST /internal/jobs/{id}/fail { error }` (first 2 KB of ffmpeg's stderr). Idempotent: a second `complete` for a `ready` job → 200 no-op.

**Where it runs:** the API fires `POST https://api.github.com/repos/{GITHUB_REPO}/dispatches { event_type: "transcode", client_payload: { job_id } }` with a fine-grained token (Contents: read + write, this repo only). `transcode.yml`: `on: repository_dispatch: types: [transcode]` → checkout → `uv sync --directory api` → run the worker with `API_URL`, `WORKER_SECRET`, `BLOB_READ_WRITE_TOKEN` from Actions secrets; `timeout-minutes: 30`. Runner start ≈ 15–30 s, a 2-min 1080p source ≈ 60–90 s, upload ≈ 10 s → **≈ 2 min** upload-to-playable. Dispatch failure (GitHub down) leaves the job `queued` with `dispatch_error`; admin retry re-fires. **Locally:** the same command against `http://localhost:8000`; the seed runs it with `--poll` over the seeded jobs.

**Why Actions and not a Vercel function:** a 3-rendition encode of a 2-min 1080p file needs 2–4 CPU-minutes; Hobby functions cap at 300 s on one vCPU and ffmpeg would take a third of the 250 MB bundle. Actions gives 4 vCPU, ffmpeg preinstalled and free minutes; the worker is plain Python either way, so moving it to a container later is a change of `runs-on`, not of code.

## 4. Upload (client → Blob) and the token
Vercel functions cap request bodies at 4.5 MB, so video never passes through the API. The studio uses `@vercel/blob/client`'s `upload(pathname, file, { access: 'public', handleUploadUrl: '/api/creator/lessons/{id}/video/token', onUploadProgress })`. The API implements the handle-upload protocol: on `{ type: 'blob.generate-client-token', payload: { pathname } }` it checks the creator owns the lesson, forces `pathname = video-src/{lesson_id}/{uuid}.{ext}`, and returns a **client token** generated the way the JS SDK does it (`generateClientTokenFromReadWriteToken`: HMAC-SHA256 of the JSON payload `{ pathname, maximumSizeInBytes: 500 MB, allowedContentTypes: [video/mp4, video/quicktime, video/webm], validUntil: now + 1 h, addRandomSuffix: false }` with the store's RW token, base64-wrapped with the store id — ~20 lines, unit-tested against a token the SDK produced). The browser then PUTs straight to Blob (multipart for > 100 MB) and, on success, calls `POST /creator/lessons/{id}/video { url, size }`; the API `HEAD`s the blob with the RW token, checks the pathname prefix and size, generates `key_hex` + `iv_hex`, writes `videos` + `video_jobs(queued)`, and dispatches. Resources (PDF / zip ≤ 20 MB) and captions (v2) use the same path with their own prefixes.

## 5. Playback: playlists, token, key server
- **Token:** `POST /lessons/{id}/play { device_id }` → `can_watch(user, lesson)` → `t = b64url({ u, l, d, exp: now + 3600 }) + "." + b64url(HMAC-SHA256(PLAYBACK_SECRET, payload))`. Returned inside `master_url = /api/stream/{lesson}/master.m3u8?t=…`. Preview lessons get a token with `u = "anon"`.
- **`GET /stream/{lesson}/master.m3u8?t=`** → verify `t` (signature, `exp`, `l == lesson`) → `#EXT-X-STREAM-INF:BANDWIDTH=…,RESOLUTION=…,CODECS="avc1.4d401f,mp4a.40.2"` per rendition in the manifest → `{name}.m3u8?t=…`. `Cache-Control: private, no-store`.
- **`GET /stream/{lesson}/{name}.m3u8?t=`** → `#EXT-X-VERSION:3`, `#EXT-X-TARGETDURATION:7`, `#EXT-X-PLAYLIST-TYPE:VOD`, `#EXT-X-KEY:METHOD=AES-128,URI="key?t=…",IV=0x{iv}`, then `#EXTINF:{d},` + `https://{blob}/video/{prefix}/{name}_{nnn}.ts` per segment, `#EXT-X-ENDLIST`. Relative `key?t=` resolves against the playlist URL in every player.
- **`GET /stream/{lesson}/key?t=`** — the authorization boundary: verify `t` → **re-run `can_watch`** against the DB (a refund or a takedown revokes here, not at token expiry) → v3: upsert `playback_sessions(u, l, d, now)`, count devices seen in 5 min, `> 2 → 403 too_many_devices` → return the 16 bytes as `application/octet-stream`, `no-store`. Anonymous tokens only unlock `is_preview` lessons.
- **`can_watch(user, lesson)`** = `lesson.video.status == ready and course.status == published and (lesson.is_preview or enrolled(user, course) or active_subscription(user))` — one function in `services/entitlement.py`, used by play, key, offline-lease (v4) and the course page's state.
- **Player:** `hls.js` when `Hls.isSupported()`, else `<video src={master_url}>` (Safari, iOS). `startPosition: resume_at`; ABR left to hls.js (`capLevelToPlayerSize: true`); `xhrSetup` untouched — no headers, the token rides the URL so native HLS works. Errors: `keyLoadError` with 403 → "This lesson isn't in your library" and the buy state; 401 → re-request `/play` once (expired token) and reload the source.

## 6. Progress and resume
`POST /lessons/{id}/progress { position_s, watched_delta_s, client_ts }` every 10 s while playing, on pause, on seek, and on `pagehide` via `navigator.sendBeacon` (a `text/plain` JSON body so it stays a simple request). Server: `progress` upsert with `position_s = $pos`, `watched_s += min(delta, 15)`, `completed = completed or pos ≥ 0.9 × duration`, `updated_at = now()`; the response echoes `course_progress`. `/play` returns `resume_at = position_s` unless `completed` (then 0) or `position_s > duration − 10`. The player shows **Resume at m:ss** for 3 s then seeks (reduced motion: shows the button, no auto-seek). Two devices writing at once: last write wins by server time — the acceptable behaviour for a course player. Marking complete is `POST /lessons/{id}/complete`; completion is monotonic. Certificate check runs inside the same transaction: if every ready lesson is `completed` (v2: and every section quiz has a passing attempt) and no certificate exists → `issue_certificate()`.

## 7. Money
- **Checkout (v1):** `POST /checkout { course_id }` → 409 `already_enrolled` / 422 `free_course` → `orders(pending_payment, amount = course.price_paise)` → Razorpay `order.create` → `{ order_id, number, razorpay_order_id, key_id, amount_paise }`. Verify and webhook both call **`mark_paid(order, payment_id)`** under `select … for update`: if `pending_payment` → `paid`, `enrollments` insert (`on conflict do nothing`), two ledger entries; else no-op. `webhook_events.id` unique → replay = 200. Expiry lazy at 30 min (nothing to release).
- **Ledger:** `sale = round(amount × 0.80)`, `fee = amount − sale` (no rounding drift). Refund (v2, admin): Razorpay refund → `refunded` → entries `refund` −sale to the creator, −fee to the platform → enrollment deleted (progress kept).
- **Subscriptions (v2):** plan `SR-ALLACCESS-499` created once by `scripts/create_plan.py` → `POST /subscriptions` → Razorpay `subscription.create(total_count 120)` → the checkout modal with `subscription_id` → webhooks drive `subscriptions.state` (table in 03-user-flows Flow 7); `active_subscription(user)` = `state in (active, authenticated) or (state = halted and updated_at > now − 3 d) or (state = cancelled and current_end > now)`.
- **Payouts (v2):** `POST /creator/payouts { amount }` → 422 unless `≤ available` and `≥ 50000` paise and no open request → `payouts(requested)`; admin `POST /admin/payouts/{id}/pay { reference }` → `payout` entry −amount, `paid`. Available = balance − Σ requested.
- **Pool (v3):** `POST /admin/pool/close { month }` → `pool = Σ subscription charges captured in month × 0.80`; `minutes_c` from `watch_minutes` where `source = subscription`; `share_c = floor(pool × minutes_c / total)`; the remainder goes to the largest share; entries `pool_share` with `period = month`; `pool_closes` row; re-running → 409 `already_closed`.

## 8. Certificates
`services/certificates.py::issue(user, course)` → `code = 'SR-' + 2 × 4 base32 chars`, `fpdf2` A4 landscape with the bundled Onest TTFs, the course title, student name, creator, date, code and `https://skillroom.virajdomadia.com/verify/{code}` → Blob `certificates/{code}.pdf` → row. `/verify/{code}` is a public API read (`GET /verify/{code}` → name, course, creator, issued_at) rendered server-side with `noindex`.

## 9. Web
- **Rendering:** home, browse, course, creator pages are dynamic with tag caching (`courses`, `course:{slug}`) and `revalidate: 300`; the API calls `POST web/api/revalidate` on publish / takedown / video ready. Player, `/me`, studio, admin: dynamic `no-store`. `next/image` for posters (Blob host in `remotePatterns`, `sizes` per grid), aspect boxes reserved (no CLS).
- **Player page:** one client component (`components/player/Player.tsx`): `/play` on mount → `hls.js` (dynamic import) → `useHeartbeat` (10-s interval bound to `playing`, flush on pause / seek / `pagehide`) → sidebar `Curriculum` with ticks → `ResumeToast` → keyboard map. Sprite scrubbing (v2) reads the manifest's sprite geometry; captions (v2) add `<track>`.
- **Studio upload:** `components/studio/VideoPanel.tsx`: drop zone → `upload()` with progress → completion POST → `useJobStatus` polling `GET /creator/lessons/{id}/video` every 3 s until `ready | failed` → rendition ticks, poster reveal, "Preview it" (plays through the real key server with the creator's own entitlement — creators can always watch their own lessons).
- **Studio / admin shells:** `app/(studio)/studio/*` and `app/(admin)/admin/*` behind layouts that 404 for the wrong role (role from `/auth/me`, re-checked by the API on every call).
- **Offline (v4):** `manifest.webmanifest`, `sw.js` (Workbox-free, hand-written: precache the app shell, network-first for pages, cache-first for `/offline/*`). Download = fetch the 480p playlist through the API, then every segment URL into `caches.open('offline-{lesson}')`, plus the key + lease into IndexedDB (`idb-keyval`). Custom hls.js `loader` (extends the default `XhrLoader`): if the URL is a cached segment / playlist / key and (offline or cache-first flag) → serve from cache; the key loader checks `lease_expires_at`. Progress: `useHeartbeat` writes to an IDB queue when offline; `online` event flushes in order.
- **Motion signature and visual direction:** decided in [04-ui-mockups.md](04-ui-mockups.md) from the variant page. On the table: *Develop* (the poster develops from blur as renditions tick in), *Resume glide* (the playhead glides to the resume point along a lit track), *Curriculum draw* (the course outline draws itself, ticks are stroked), *Certificate print* (the certificate feeds out and the seal stamps), *Ladder* (renditions build as three bars, segments tick), *Chapter count* (lesson numbers roll like a counter).

## 10. Auth & access
Own session auth as the other projects: `users(email citext, password_hash argon2, name, role)`, `sessions(id, user_id, expires_at)`, cookie `sr_session` HttpOnly SameSite=Lax 30 d. `POST /auth/demo { as: student|creator|admin }` for the landing buttons. Dependencies `require_user`, `require_creator` (404 otherwise), `require_admin` (404), `require_worker` (Bearer `WORKER_SECRET`, 401). Creators may only read / write their own courses (`course.creator_id == me`), checked in every studio route.

## 11. Caching & rendering
Catalogue reads: `s-maxage=300, stale-while-revalidate=600` + web tag cache. `/stream/*`, `/lessons/*`, `/me`, studio, admin: `private, no-store`. Blob objects are immutable by name (new prefix per upload) so the CDN caches them forever. Posters via `next/image` with 1-year cache.

## 12. Failure modes worth handling
| Failure | Behaviour |
|---|---|
| GitHub dispatch fails | Job stays `queued` with `dispatch_error`; studio shows "Waiting for a worker"; admin / creator retry re-dispatches |
| Runner never claims (Actions outage) | `queued` > 10 min shows the same message; a `workflow_dispatch` of `transcode.yml` with `--poll` drains the queue by hand |
| ffmpeg fails / unsupported codec | `failed` with the stderr tail; creator sees the reason, can re-upload or retry |
| Worker dies mid-job | `processing` > 20 min is treated as stale: claimable again, `attempts` capped at 3 then `failed` |
| Blob quota reached | `put` 4xx → `failed: storage_quota`; admin dashboard shows Blob usage from the seed script's last count |
| Token expired mid-lesson | hls.js `keyLoadError` 401 → the player calls `/play` again once and reloads at the current position |
| Refund / takedown while watching | The next key request 403s (keys are fetched once per playlist, so the current session ends at the next rendition switch or reload) |
| Two devices playing (v3) | The third device's key request → 403 `too_many_devices`, named in the player |
| Razorpay modal dismissed | Order stays `pending_payment` 30 min; the buy sheet can re-open the same order |
| Webhook before verify / replayed | `mark_paid` idempotent; `webhook_events.id` unique |
| Client upload completes but the completion POST never arrives | The source sits unreferenced in `video-src/`; `scripts/gc_blob.py` lists and deletes orphans older than a day (run by hand) |
| Offline lease expired (v4) | Player refuses with "Reconnect to renew"; the next online `/play` refreshes the lease silently |
| Safari / iOS | Native HLS; key via query token; no `hls.js` custom loader → v4 offline is Chromium/Android-first, iOS keeps Download hidden |

## 13. Testing (only these)
- `test_rbac`: student → `/studio/*`, `/admin/*` = 404; creator → other creator's course = 404; worker routes without the secret = 401.
- `test_key_endpoint`: no entitlement 403; preview lesson anonymous 200; expired token 401; tampered signature 401; token for lesson A on lesson B 403; after refund 403.
- `test_playlists`: master and media playlists generated from a manifest fixture parse (m3u8 grammar), carry `EXT-X-KEY` with the IV and absolute segment URLs, durations match.
- `test_worker` (skipped if no ffmpeg): a 10-s colour-bar fixture → three rendition playlists, encrypted segments that fail to demux without the key and demux with it, a poster, a manifest whose durations sum to 10 ± 0.5 s; run with a `FakeBlob` that writes to a temp dir and a fake API.
- `test_upload_token`: the client token matches one generated by the JS SDK for the same payload (fixture).
- `test_mark_paid`: verify-then-webhook and webhook-then-verify → one enrollment, one sale + one fee summing to the amount; replay no-op; `already_enrolled` 409.
- `test_progress`: heartbeat from device A → `/play` on device B returns `resume_at`; completion monotonic; `watched_delta` capped at 15 s.
- `test_certificate_once`: last lesson completed twice → one certificate; `/verify/unknown` → 404 envelope.
- v2: `test_subscription_states` (every webhook edge, grace, cancel-at-period-end), `test_quiz_gate`, `test_payout_balance`. v3: `test_pool_close` (shares sum to the pool, idempotent), `test_device_limit`. v4: manual on a phone.

## 14. Environment
`api/`: `DATABASE_URL`, `SESSION_SECRET`, `PLAYBACK_SECRET`, `WORKER_SECRET`, `WEB_URL`, `API_URL`, `REVALIDATE_SECRET`, `BLOB_READ_WRITE_TOKEN`, `GITHUB_DISPATCH_TOKEN`, `GITHUB_REPO`, `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`; v2: `RESEND_API_KEY`, `RAZORPAY_PLAN_ID`. `web/`: `API_URL`, `REVALIDATE_SECRET`, `NEXT_PUBLIC_RAZORPAY_KEY_ID`, `NEXT_PUBLIC_BLOB_HOST`. **Actions secrets (worker):** `API_URL`, `WORKER_SECRET`, `BLOB_READ_WRITE_TOKEN`.
