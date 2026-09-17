# Skillroom — Architecture

**Lifecycle step:** 5 of 17 · **Locked:** 2026-09-17

## 1. System diagram

```mermaid
flowchart LR
  subgraph Browser
    ST[Student · phone / laptop<br/>browse · buy · player · offline v4]
    CR[Creator studio · desktop<br/>courses · upload · earnings]
    AD[Admin · desktop<br/>creators · courses · jobs · payouts]
  end
  subgraph Vercel
    WEB[web · skillroom<br/>Next.js: catalogue (tag-cached) · player · studio · admin<br/>rewrites /api/* →]
    API[api · skillroom-api<br/>FastAPI bom1<br/>REST · playlists · key server · webhooks · fpdf2]
  end
  subgraph GitHub
    GHA[Actions runner · transcode.yml<br/>worker: ffmpeg → HLS ladder · AES-128 · poster · sprite]
  end
  PG[(Neon Postgres<br/>users · courses · videos + manifests · jobs<br/>enrollments · orders · ledger · progress)]
  BL[Vercel Blob<br/>video-src · video/{prefix} (encrypted) · posters · resources · certificates]
  RZ[Razorpay<br/>orders · subscriptions v2 · refunds]
  RS[Resend · v2]

  ST & CR & AD -->|same-origin /api/*| WEB --> API
  CR -->|client upload · token from API| BL
  ST -.->|Standard Checkout modal| RZ
  API --> PG
  API -->|repository_dispatch| GHA
  GHA -->|claim · complete| API
  GHA -->|GET source · PUT segments| BL
  API -->|playlists · key| ST
  BL -->|encrypted .ts · posters| ST
  API -->|create order · refund| RZ
  RZ -->|payment / subscription webhooks| API
  API -->|revalidate tags| WEB
  API -->|mails| RS
```

## 2. Boundaries
| Component | Owns | Never does |
|---|---|---|
| **web/** | Every screen; the hls.js player and heartbeat; the upload UI (progress, polling); the Razorpay modal; the service worker and offline cache (v4) | Touch the DB, Razorpay's server API or Blob's RW token; decide entitlement; generate playlists |
| **api/** | Auth and RBAC, catalogue, `can_watch`, playback tokens, playlists, **the key server**, progress, checkout / verify / webhooks, ledger, certificates, job dispatch and the `/internal` job routes, upload tokens, seed | Run ffmpeg; serve video bytes; hold a key in a URL |
| **worker/** | Everything between "source in Blob" and "manifest reported": probe, ladder, encryption, poster, sprite, upload | Touch the DB (it only talks to `/internal/*`); decide anything about entitlement |
| **Postgres** | Everything durable, including manifests and per-video keys | Store video bytes |
| **Blob** | Bytes: sources, encrypted segments, posters, sprites, resources, PDFs | Decide who may read (segments are ciphertext; access is the key endpoint) |
| **GitHub Actions** | Free compute for the worker | Anything the worker script does not already do locally |
| **Razorpay** | Taking the money and telling us via webhook | Deciding enrollment — `mark_paid` is ours |

Contract: `api/openapi.json` → `web/src/lib/api-types.ts` via `pnpm gen:api`. Web client (`web/src/lib/api.ts`) = typed `fetch` forwarding cookies, trusting only the `{ error: { code, message, details } }` envelope.

## 3. api/ layout
```
api/app/
  main.py            app factory, request-id middleware, error envelope
  config.py          pydantic-settings
  db.py              async engine
  models/            user, session, creator_profile, course, section, lesson, video, video_job, resource,
                     enrollment, progress, certificate, order, ledger_entry, webhook_event,
                     subscription · quiz · question · attempt · payout (v2), watch_minute · watch_bucket · playback_session · pool_close (v3), offline_lease (v4)
  schemas/           pydantic request/response models (= the OpenAPI contract)
  routers/           auth, catalog (home, courses, creators), lessons (play, progress, complete), stream (master, media, key),
                     checkout, me, creator (courses, sections, lessons, video, resources, earnings), admin, internal (jobs), webhooks,
                     subscriptions (v2), quizzes (v2), payouts (v2), pool (v3), offline (v4)
  services/
    entitlement.py   can_watch(), active_subscription()
    playback.py      sign_token(), verify_token(), master_playlist(), media_playlist()
    jobs.py          enqueue(), dispatch() (GitHub), claim(), complete(), fail(), stale()
    blob.py          put / head / delete via REST; client_upload_token()
    checkout.py      create order, mark_paid, expire_stale
    ledger.py        post(), balance(), available()
    razorpay.py      order create, signature verify, webhook verify, refund, subscriptions (v2)
    progress.py      heartbeat(), resume_at(), maybe_complete_course()
    certificates.py  issue() (fpdf2) · verify()
    pool.py          close_month() (v3)
  worker/
    transcode.py     the worker CLI (claim → probe → ffmpeg → upload → complete)
    ffmpeg.py        command builders, playlist parsing
  assets/            Onest-*.ttf (certificates), colour-bars.mp4 (test fixture)
  seed/              catalog.json · fetch_videos.py · videos/ (+ CREDITS.md) · seed.py (users, courses, jobs → worker --poll → enrollments, progress)
scripts/             create_plan.py (v2) · gc_blob.py · eval_stream.py
tests/               the tests listed in 04 §13 only
.github/workflows/   ci.yml · transcode.yml (the worker)
```

## 4. web/ layout
```
web/src/
  app/(site)/            page.tsx (home) · courses · c/[slug] · u/[handle] · verify/[code] · all-access (v2)
  app/(learn)/           learn/[slug]/[lesson] · learn/[slug]/quiz/[id] (v2) · me · certificates/[code]
  app/(auth)/            sign-in · sign-up · apply
  app/(studio)/studio/   layout (404 non-creators) · page · courses/new · courses/[id] · courses/[id]/lessons/[lid] · earnings · courses/[id]/analytics (v3)
  app/(admin)/admin/     layout (404 non-admins) · page · creators · courses · jobs · payouts (v2)
  app/api/revalidate/    route.ts
  components/site/       CourseCard · CourseGrid · CategoryChips · Curriculum · CreatorCard · BuySheet · RazorpayButton
  components/player/     Player · Controls · ResumeToast · Curriculum (sidebar) · ScrubPreview (v2) · DownloadButton (v4)
  components/studio/     CourseForm · SectionList · LessonRow · VideoPanel (upload + job status) · ResourceList · EarningsTable · QuizEditor (v2)
  components/admin/      Applications · CourseTable · JobsBoard · PayoutQueue (v2)
  components/landing/    (exists)
  components/ui/
  lib/api.ts · api-types.ts (generated) · session.ts · hls.ts (player setup) · heartbeat.ts · upload.ts · money.ts · offline.ts (v4)
  public/manifest.webmanifest · sw.js (v4)
```

## 5. Deployment topology
- Two Vercel projects per repo: `skillroom` (root `web/`) and `skillroom-api` (root `api/`, FastAPI preset, `bom1`). `web/next.config.ts` rewrites `/api/:path*` → `API_URL`; cookies are first-party; no CORS. Blob's own CORS (`*`) covers segment fetches from the Blob host.
- Neon: one project; `main` = production, a `dev` branch for local; CI uses the `postgres:17` image.
- Blob store on `skillroom-api`; `NEXT_PUBLIC_BLOB_HOST` in `remotePatterns`.
- GitHub: `transcode.yml` on `repository_dispatch` with the three worker secrets; a fine-grained token for the API to dispatch. The repo is public → unlimited Actions minutes.
- Razorpay test mode; webhook → `https://skillroom.virajdomadia.com/api/webhooks/razorpay` (via the web rewrite so the URL survives an API host change).
- Previews: Vercel previews per PR for `web/` against the production API.
- CI: `web` = pnpm typecheck + build; `api` = ruff + pytest (ubuntu runner has ffmpeg, so `test_worker` runs). That is all.

## 6. Request paths worth drawing
**Upload:** creator drops `lesson-3.mp4` (180 MB) → `/api/creator/lessons/42/video/token` → client token → multipart PUT to Blob (progress bar) → `POST /api/creator/lessons/42/video` → `videos` (key generated) + `video_jobs(queued)` → `repository_dispatch` → runner claims in ~20 s → ffmpeg ≈ 80 s → 3 × ~20 segments + poster + sprite to Blob → `complete` → `ready`; the studio's poll flips the status and the poster develops.
**Play:** `/learn/wheel-pottery/centering` → `POST /api/lessons/42/play` → `can_watch` → token → `master.m3u8?t` → `480p.m3u8?t` → `key?t` (403 for the wrong person) → segments from the Blob CDN → hls.js decrypts and climbs to 720p; heartbeats every 10 s.
**Buy:** `/c/wheel-pottery` → Buy → `POST /api/checkout` → modal → `POST /api/checkout/{id}/verify` → `mark_paid` → enrollment + ledger → the course page shows Start; the webhook arrives seconds later → no-op.
**Certificate:** last lesson's heartbeat crosses 90 % → `maybe_complete_course` → `issue()` → fpdf2 → Blob → `/me` shows the certificate; `/verify/SR-7Q2M-K9XD` is public.
**Offline (v4):** Download → 480p playlist + segments into Cache Storage, key + 48-h lease into IDB → airplane mode → custom loader serves from cache → progress queues → back online → flush + lease refresh.

## 7. Security notes (the short list)
Cookie session HttpOnly + SameSite=Lax; argon2 passwords; studio and admin 404 for the wrong role and creators are scoped to their own rows; **the key endpoint re-checks entitlement on every call** and never caches; playback tokens are HMAC-signed, bound to user + lesson + device, 1-h expiry; per-video keys live only in Postgres and in the worker's temp dir for the duration of a job; segments are AES-128 ciphertext on a public CDN under a random prefix; upload tokens are scoped to one pathname, one content-type set, 500 MB, 1 h; `/internal/*` needs the worker secret; Razorpay signatures checked on verify and webhooks, event ids deduped; prices come from the DB, never the client; certificate codes are random base32; `/verify` is rate-limited 30/min/IP; no PII in logs; the GC and eval scripts never run against production without `--yes`.
