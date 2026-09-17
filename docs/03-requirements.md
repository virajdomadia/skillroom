# Skillroom — Requirements & Scope

**Lifecycle step:** 3 of 17 · **Locked:** 2026-09-17 · **Source:** [PRD.md](../PRD.md) locked decisions. Flows and screen index: [03-user-flows.md](03-user-flows.md).

Actors: **Student** (signed in to watch; browsing is public), **Creator** (approved applicant, `/studio`), **Admin** (`/admin`), **Worker** (the transcode script, server-to-server). Each requirement ends with **Accept:** — the check that closes it. Ids: R = v1, R2 = v2, R3 = v3, R4 = v4. Money in ₹, integer paise in the DB.

---

## v1 — Classroom (base, ≈ 16 h)

### R1. Auth & roles
- Email + password, cookie session (`sr_session`, HttpOnly, SameSite=Lax, 30 d); sign up / in / out. `users.role ∈ {student, creator, admin}`. Three demo logins on the landing (`POST /auth/demo`).
- `/studio/*` requires `creator` (a student with a pending application sees the application status instead); `/admin/*` requires `admin`; both return 404 to anyone else. `/learn/*`, `/me` require any session.
- **Creator application:** any student submits `display_name, area, bio, subject` → `creator_profiles.status = applied` → admin approves (role becomes `creator`) or rejects with a note.
- **Accept:** a student never sees the studio or admin; an approved application unlocks `/studio` on the next request; sessions expire after 30 days.

### R2. Catalogue
- Home: hero, category strip, "New courses", "Free to start" (preview lessons), a creator strip.
- `/courses` and `/courses?category=`: course cards (poster, title, creator, lessons · duration, price or Free); categories = pottery · baking · art · yoga · photography · music (enum).
- Course page `/c/[slug]`: poster, title, subtitle, creator card (→ `/u/[handle]`), description, **curriculum** (sections → lessons with duration, preview badge, completed ticks when enrolled), price and **Buy** / **Enrol free** / **Continue** depending on state; preview lessons play inline for anyone.
- Creator page `/u/[handle]`: portrait, bio, area, their published courses.
- **Accept:** only `published` courses with ≥ 1 `ready` lesson appear; a `takedown` course 404s publicly but stays in the studio; Lighthouse mobile ≥ 90 / 100 / 100 on home, browse and course pages with no CLS.

### R3. Buying a course
- `POST /checkout { course_id }` → order `SR-####` in `pending_payment` with the course's current price snapshotted → Razorpay order → Standard Checkout modal → `POST /checkout/{id}/verify` (HMAC) → `mark_paid()`; webhook `payment.captured` calls the same function; event ids deduped. Free course (`price_paise = 0`) → `POST /courses/{id}/enrol` creates the enrollment directly.
- `mark_paid()` in one transaction: order `paid`, `enrollments(user, course, source = purchase, order_id)` (unique per user + course), ledger entries `sale` (+80 % → `creator:{id}`) and `fee` (+20 % → `platform`).
- Buying a course you already own → 409 `already_enrolled`. An unpaid order older than 30 min is `expired` lazily (nothing to release — no stock).
- **Accept (tests):** verify-then-webhook and webhook-then-verify → exactly one enrollment and one pair of ledger entries; a replayed webhook is a no-op; the ledger sums to the order amount; a second purchase of the same course is refused.

### R4. The player & progress
- `/learn/[slug]/[lesson]`: video (hls.js; native HLS on Safari), sidebar curriculum with progress ticks, next / previous, resources list, mark complete, keyboard shortcuts (space, ←/→ 10 s, `f`, `m`), playback speed.
- `POST /lessons/{id}/play` → `{ master_url (with token), poster_url, resume_at, duration_s }` or 403 `not_entitled` (the page shows the course's buy state). `GET /stream/{lesson}/master.m3u8?t=` · `/{rendition}.m3u8?t=` · `/key?t=` — see [04-technical-design.md](04-technical-design.md) §3–4.
- **Progress:** heartbeat `POST /lessons/{id}/progress { position_s, watched_delta_s }` every 10 s while playing, on pause / seek, and on unload via `sendBeacon`. Server stores `position_s`, accumulates `watched_s`, marks `completed` at ≥ 90 % or on the button. On open, if `resume_at ≥ 5 s` and `< duration − 10 s`, the player offers **Resume at m:ss** (auto-seeks after 3 s; reduced-motion: no auto).
- Course progress = completed lessons ÷ ready lessons; the course page, `/me` and the sidebar show it.
- **Accept (tests):** key endpoint → 403 without entitlement, 401 on an expired or tampered token, 403 when the token's lesson ≠ path lesson; a preview lesson's key is public; progress written on device A is the `resume_at` on device B; `completed` never flips back to false.

### R5. My learning
- `/me`: enrolled courses with progress bars and "Continue → lesson", certificates earned, account (name, email, password). 
- **Accept:** Continue opens the first incomplete lesson at its resume position.

### R6. Creator studio — courses, sections, lessons
- `/studio`: course list (poster, title, status draft / published / takedown, lessons ready ⁄ total, enrollments, revenue). `/studio/courses/new` → title, subtitle, category, price (₹, 0 = free), description, cover (optional; default = first ready lesson's poster).
- `/studio/courses/[id]`: sections (add, rename, reorder) → lessons (add, rename, reorder, `is_preview`), each lesson row shows its video state. **Publish** requires ≥ 1 section, ≥ 1 `ready` lesson, a description; unpublish any time; a takedown by admin is shown with the note and cannot be undone by the creator.
- **Accept:** reorder persists; publishing a course with no ready lesson → 409 `not_publishable` with reasons; a published course appears in `/courses` on the next request.

### R7. Creator studio — video upload & the pipeline
- `/studio/courses/[id]/lessons/[lid]`: drop zone (mp4 / mov / webm, ≤ 500 MB) → client upload straight to Blob using a token from `POST /creator/lessons/{lid}/video/token` → on completion `POST /creator/lessons/{lid}/video { url, size }` → `video_jobs` row `queued` → API fires `repository_dispatch`. The page shows the job live (poll every 3 s): `queued → processing (rendition ticks 240p ✓ 480p ✓ 720p ✓) → ready` (poster appears, duration, "Preview it") or `failed` (error, **Retry**). Re-uploading replaces the video (old prefix deleted after the new one is ready).
- Resources: PDF / zip ≤ 20 MB per lesson via the same client-upload path; listed on the player.
- **Worker** (`api/app/worker/transcode.py`): claims the job, downloads the source, runs ffmpeg (ladder + AES-128 + poster + sprite), uploads to Blob `video/{prefix}/…`, reports `POST /internal/jobs/{id}/complete { manifest }` or `/fail { error }`. Runs on GitHub Actions (`.github/workflows/transcode.yml`) in prod, locally by hand.
- **Accept (tests):** the worker on a 10-s fixture produces three rendition playlists with `#EXT-X-KEY METHOD=AES-128`, encrypted segments (not decodable without the key), a poster and a manifest whose durations sum to the source; a second `complete` for the same job is a no-op; `/internal/*` without the worker secret → 401. **Accept (demo):** a 2-min 1080p upload is playable within 3 min on prod.

### R8. Admin
- `/admin`: revenue (7 / 30 d), enrollments, pending applications, failed jobs. `/admin/creators`: applications with approve / reject (+ note) and the creator list. `/admin/courses`: every course with takedown / restore (+ note). `/admin/jobs`: video jobs by state with retry (re-dispatch) and the worker's error text.
- **Accept:** approve → the applicant's next request sees `/studio`; takedown → the public page 404s within the cache window; retry re-queues and re-dispatches exactly one job.

### R9. Certificate
- When a course reaches 100 % (v2: and every section quiz is passed), `certificates(code 'SR-XXXX-XXXX', user, course, issued_at)` is created once and a PDF (`fpdf2`: name, course, creator, date, code, QR-less verify URL) is written to Blob. `/certificates/[code]` (owner) shows and downloads it; `/verify/[code]` is public: name, course, creator, date, valid ✓.
- **Accept (test):** completing the last lesson twice issues one certificate; `/verify` of an unknown code → "not found", never a 500.

### R10. Seed & content
- Idempotent seed: admin, demo student, 6 creators (approved), 6 courses / 12 sections / 24 lessons / 6 resources, 24 CC videos fetched by `seed/fetch_videos.py` (Commons API, licence filter, backoff, `CREDITS.md`), sliced to 90–150 s and pushed through the real worker (`seed.py videos` runs it locally against the seeded jobs); ~40 enrollments across 10 seeded students with progress and heartbeats over the last 60 days; the demo student's completed course has a certificate.
- **Accept:** `seed` runs twice without duplicates; every lesson is `ready`; Blob usage ≤ 70 % of the Hobby quota; `eval_stream.py` plays every master playlist through hls.js's parser without error.

---

## v2 — All-access (mid, ≈ 11 h)

### R2-1. Subscriptions
- `/all-access`: ₹499 / month, what's included; `POST /subscriptions` creates a Razorpay subscription on the seeded plan → hosted / modal authorisation → webhooks `subscription.authenticated / activated / charged / halted / cancelled / completed` (deduped) drive `subscriptions.state`; `current_end` from the charge. Cancel-at-period-end from `/me`. **Grace:** `halted` counts as active for 3 days.
- `can_watch` gains `active_subscription(user)`; enrollments via subscription are created lazily on first play (`source = subscription`) so progress and certificates work the same.
- **Accept (tests):** every webhook edge of the state table; a replayed event is a no-op; a `halted` sub watches for 3 days then 403s; cancel-at-period-end keeps access until `current_end`.

### R2-2. Quizzes
- Studio: one quiz per section (pass mark %, 3–8 questions, 2–4 options, one correct). Player: after the section's last lesson, `/learn/[slug]/quiz/[id]` — answer, submit, score, retry. Certificate requires every section quiz passed.
- **Accept:** a failed quiz blocks the certificate; the best attempt is shown; questions never leak the correct index to the client before submission.

### R2-3. Earnings & payouts
- `/studio/earnings`: balance available / pending / paid, entries list (sale, fee, refund, payout), **Request payout** (≥ ₹500, one open request at a time). `/admin/payouts`: requested → paid (bank reference) or rejected (note). Refunds (admin, per order) write negative `sale` / `fee` entries.
- **Accept (tests):** balance = Σ entries; a request above available → 422; marking paid writes the `payout` entry once.

### R2-4. Emails
- Resend + React Email: purchase receipt (with the course link), certificate issued (PDF link), payout paid, creator approved / rejected; forgot / reset password.
- **Accept:** the receipt arrives within a minute of `paid` with a working link.

### R2-5. Captions, scrubbing, continue watching
- Creators upload a `.vtt` per lesson (client upload) → `<track>` in the player; the v1 sprite + a generated `thumbnails.vtt` power hover-preview on the scrub bar; home shows **Continue watching** for signed-in students.
- **Accept:** captions toggle with `c`; hovering the bar shows the right frame within ±5 s.

---

## v3 — Royalties (advanced, ≈ 8 h)

### R3-1. The pool
- Heartbeats from subscription-sourced enrollments accumulate `watch_minutes(month, creator_id, course_id, user_id, seconds)`. `POST /admin/pool/close { month }` (once per month; idempotent): pool = Σ captured subscription charges × 80 %; per creator `share = pool × minutes_c ÷ minutes_total` → `pool_share` ledger entries + a `pool_closes` row (pool, total minutes, per-creator lines). The creator's earnings page shows "₹4,120 · 1,240 subscriber-minutes · 12.3 % of the pool".
- **Accept (tests):** shares sum to the pool within rounding (remainder to the largest share); closing twice is a no-op; a creator with zero minutes gets no entry.

### R3-2. Creator analytics
- Heartbeats also upsert `watch_buckets(lesson_id, bucket_10s, viewers)`; `/studio/courses/[id]/analytics`: per-lesson retention curve (viewers per 10-s bucket ÷ starters), drop-off markers on the biggest falls, completion rate, average watched %.
- **Accept:** the curve for a seeded lesson matches a SQL check; buckets never exceed starters.

### R3-3. Device limit
- `playback_sessions(user, lesson, device_id, last_seen)`; the key endpoint upserts the caller's device and counts devices active in the last 5 min; > 2 → 403 `too_many_devices` (the player names the limit). Preview lessons exempt.
- **Accept (test):** three devices within 5 min → the third is refused; after 5 min idle it is admitted.

### R3-4. Search
- `courses.search tsvector` (title A, subtitle + tags B, description C) with GIN; `/courses?q=` ranks by `ts_rank`; the browse page shows a search box.
- **Accept:** "naan" finds the flatbreads course by description alone.

---

## v4 — Offline lessons (unique, free, ≈ 3 h)

### R4-1. PWA + download
- `manifest.webmanifest`, service worker (app shell precached: `/learn/*` shell, fonts, icons), install prompt on the player (dismissible, remembered). **Download** on a lesson: the client fetches the 480p rendition playlist and every segment and stores them in Cache Storage under `offline/{lesson_id}`; `POST /lessons/{id}/offline-lease { device_id }` (requires `can_watch`) returns the key bytes + `lease_expires_at` (48 h) → IndexedDB. Storage used and "Remove" on `/me`.
- **Offline playback:** when `navigator.onLine` is false or the network fails, hls.js uses a custom loader that serves playlist, segments and key from the cache / IDB; a lease past `lease_expires_at` refuses to play ("Reconnect to renew") and is deleted. Progress writes queue in IDB and flush on reconnect (last write wins by client timestamp ≤ server time).
- **Accept:** on Android in airplane mode a downloaded lesson plays from the first tap; an expired lease refuses; a refund makes the next online lease refresh fail and the download is removed; iOS Safari gets the same download UI (Cache Storage works) with the install card hidden.

---

## Out of scope (all versions)
Live classes · DRM · auto-captions / paid AI · bundles · affiliates · multi-currency · native apps · real-money billing · mobile studio · community · multiple admins · watermarking · per-lesson pricing · instalments.
