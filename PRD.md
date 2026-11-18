# PRD — Skillroom: a video platform where we own the pipeline (shipped as a course platform)

**Status:** v1 · lifecycle steps 1–7 complete (2026-09-17) — see [docs/](docs/) · next: step 8 Project Setup (= milestone 1.0), **after Offcut** (build order 1 Tripsmith → 2 Frontrow → 3 Pagecraft → 4 Offcut → 5 Skillroom → 6 Platter; Viraj, 2026-11-19)
**Name:** Skillroom · *learn from people who do it*
**URL:** https://skillroom.virajdomadia.com (landing live at https://skillroom-viraj.vercel.app until DNS)
**Slot:** #5 · Budget ~38 h (v1 16 · v2 11 · v3 8 · v4 3) · Build fifth, after Offcut
**Live artifacts:** [Tracker](https://claude.ai/artifact/AxgaJ1fZ6HELpWTZuBUXz6) (plan rows with status, all docs, mockups, project facts) · [Screens](https://claude.ai/artifact/U7Uy3zAL3dnPWmffQnk6fB) (every v1 screen, direction C · Notebook) · [Direction variants](https://claude.ai/artifact/JK9cTzwVjD4GrEqV36WPXi) (A–F, C chosen) · Landing: https://skillroom-viraj.vercel.app

## One-liner
**A video platform where we own the pipeline** — shipped as a complete course platform with three sides — **students** who buy or subscribe, watch with resume-across-devices, pass quizzes and earn a certificate; **creators** (fictional Bengaluru coaches) who upload video and get paid; a **platform admin** who approves creators and pays out — where the video is ours end to end: **upload → an ffmpeg worker → encrypted adaptive HLS → a key server that only answers for enrolled students**. No Mux, no Stream: no per-play platform fees, and ₹0 at demo scale within free quotas (Vercel Blob Hobby ~10 GB transfer / month, Actions free minutes). Playback is **encrypted, with entitlement checks and (v3) a device limit — not DRM** (Viraj, 2026-11-19).

## Who it's for
- **Student:** learns on a phone or laptop; buys a course (v1) or subscribes to all-access (v2); expects to resume exactly where they stopped on any device.
- **Creator:** a coach or teacher who applies, gets approved, builds courses in a studio, uploads video, sees earnings and requests payouts.
- **Admin (platform):** one operator — approves creators, takes courses down, retries failed video jobs, marks payouts paid, watches revenue. A small real UI, not code.

## Why this project
- **It is a video platform first; the course is what rides on it** (Viraj, 2026-11-19). Video is the hard part most portfolios outsource. Here the pipeline is owned: an ffmpeg worker that runs on free compute, an HLS ladder with AES-128 segments, and a key endpoint that is the authorization boundary — the same design Mux sells, explained in the README instead of pointed at. What it is, honestly: encrypted playback with entitlement checks and a device limit, not DRM — an entitled user can still extract the key or screen-record; the key server decides who gets access and on how many devices, it cannot stop copying.
- **Three roles with real permission boundaries** (student / creator / admin) — the RBAC interview topic, made visible with three demo logins.
- **Money in three shapes:** one-off purchase (v1), recurring subscription with a webhook-driven state machine (v2), and a creator ledger that splits the subscription pool by minutes watched (v3).
- **The unique feature (v4, no paid service): Offline lessons.** The site installs as a PWA; a lesson downloads as encrypted segments and plays offline — **encrypted offline playback with a time-limited, device-bound entitlement (48-h lease)**. The course rides the Namma Metro, and "non-enrolled can never play" still holds; a PWA has no hardware-backed key storage, so the lease limits *time and device*, not an entitled user who digs the key out of IndexedDB.

## Locked decisions (2026-09-17) — follow these until the project ends

### 1. Identity: one platform, three roles, fictional creators
Skillroom is the platform. Roles on one `users` table: `student` (default), `creator` (after an approved application), `admin` (seeded). Creators are fictional Bengaluru people (Koramangala, Jayanagar, Malleshwaram…) with CC portraits; courses are craft and skill subjects that Wikimedia Commons has real CC video for. Prices in ₹, integer paise in the DB. Three demo logins on the landing: **student** (one course 60 % done, one completed with a certificate), **creator** (two published courses, real earnings), **admin**.

### 2. Video: our pipeline, our key server (the hard part)
- **Upload:** the creator's browser uploads the source straight to **Vercel Blob** with a client token minted by the API (≤ 500 MB, mp4 / mov / webm) → `POST /creator/lessons/{id}/video` records the source and enqueues a `video_jobs` row.
- **Worker:** `api/app/worker/transcode.py` — one Python script: claim the job → download the source → **ffmpeg** → HLS ladder **240p / 480p / 720p** (H.264 `veryfast`, 6-s segments, ~200 / 500 / 1000 kbps, AAC 48 k) with **AES-128-encrypted segments** under a per-lesson 16-byte key → poster + thumbnail sprite → upload to Blob under a random per-lesson prefix → report the manifest (renditions, segment durations, duration) to the API. **In production it runs on a GitHub Actions runner** (ffmpeg preinstalled, 4 vCPU, free minutes) fired by `repository_dispatch` from the API; locally it is `python -m app.worker.transcode --job <id>`. State machine `queued → processing → ready | failed`, attempts counted, admin retry. ~2 min from upload to playable.
- **Worker scaling path** (Viraj, 2026-11-19): the worker is a plain script that claims jobs from the `video_jobs` queue (states, attempts, retry) — the queue is the contract, not Actions. Actions is the free runner for the demo, with real limits: every job is time-capped (we set `timeout-minutes: 30`; GitHub's hard cap is 6 h), concurrent jobs per account are capped (~20 on the free plan), and runner start adds 15–30 s. At scale the same script runs as a long-lived container worker (any container host) polling the same queue — no architecture change.
- **Serving:** segments, posters and sprites are public Blob URLs (unguessable, and the segments are ciphertext). The API serves the small parts: `GET /stream/{lesson}/master.m3u8?t=` and rendition playlists (generated from the manifest, segment URLs absolute to Blob) and **`GET /stream/{lesson}/key?t=`** — the 16 bytes, only for a valid token *and* a live `can_watch()` check. The token (`POST /lessons/{id}/play`) is HMAC-signed, bound to user + lesson, expires in 1 h. Player = **hls.js**; Safari uses native HLS (the token travels in the query string so Safari's own loader can fetch the key).
- **The proof:** a non-enrolled user can hold every segment URL and still has nothing playable; a leaked token dies within the hour and opens one lesson; a refund revokes at the next key request. v3 adds a device limit at the same endpoint. **What it does not prove:** that an entitled user can't copy — the key reaches their browser, so they can extract it or screen-record. This is access control plus a device limit, not DRM (Viraj, 2026-11-19).
- **What stays ₹0 (at demo scale only):** Blob's Hobby quota (≈ 1 GB storage, 10 GB transfer / month — verified in the row that first writes to it) holds the seed at ≤ 700 MB; the worker runs on Actions' free minutes; ffmpeg is open source; nothing metered sits on the play path. There is no per-play platform fee anywhere; at scale storage, bandwidth (every view is egress) and encoding compute are real, growing costs — owning the pipeline removes the Mux / Stream margin, not the cost of video (Viraj, 2026-11-19). No DRM, no multi-region CDN — the honest size of an Indian course platform at this stage.

### 3. Money: buy in v1, subscribe in v2, split the pool in v3
- **v1 — buy a course:** Razorpay Standard Checkout, the Offcut recipe: order `pending_payment` → verify (HMAC) or webhook `payment.captured` → the same idempotent `mark_paid()` → `enrollments` row + **ledger entries** (`sale` +80 % to the creator, `fee` +20 % to the platform) in one transaction. Free courses (price 0) enroll instantly.
- **v2 — All-access ₹499 / month:** Razorpay Subscriptions (plan created once by script; `subscription.activated / charged / halted / cancelled / completed` webhooks, event ids deduped) → `subscriptions` state machine with a 3-day grace on `halted` and cancel-at-period-end. Entitlement never changes shape: `can_watch(user, lesson) = lesson.is_preview or enrolled(course) or active_subscription(user)`.
- **Payouts — a ledger, not Route:** `ledger_entries` is the source of truth (sale, fee, refund, payout, pool_share; signed paise). Creators see available / pending / paid and request a payout (v2); admin marks it paid with a bank reference. Razorpay Route (linked accounts, KYC) is an add-on behind a `PayoutProvider` protocol, not a version.
- **v3 — the pool:** monthly close: subscription revenue captured in the month × 80 % = the pool; each creator's share = pool × their subscriber-minutes ÷ all subscriber-minutes (from the player's own heartbeats, deduped and capped — [03-requirements.md](docs/03-requirements.md) R3-1) → `pool_share` entries with the math visible on the creator's earnings page.

### 4. Seed: 6 creators · 6 courses · 24 lessons · ≤ 700 MB
| Course (topic follows what Commons has good CC video of) | Creator (fictional) | Price |
|---|---|---|
| Wheel pottery: first six pots | Meera Kulkarni · Jayanagar | ₹1,499 |
| Flatbreads at home: paratha to naan | Arjun Nair · Koramangala | ₹999 |
| Watercolour landscapes | Priya Raghavan · Malleshwaram | ₹1,299 |
| Morning yoga, four weeks | Rohan Shetty · Indiranagar | **Free** |
| Street photography on a phone | Divya Menon · HSR Layout | ₹1,199 |
| Fingerstyle guitar from zero | Karthik Rao · Basavanagudi | ₹1,499 |

Each course: 2 sections × 2 lessons (the first lesson is a **preview**), ≈ 2 min per lesson, one 4-question quiz per section (v2), one resource PDF. Lessons are **real CC-BY / CC0 / PD videos from Wikimedia Commons** (`video/webm`, licence-filtered through the API with backoff), sliced by ffmpeg to 90–150 s and pushed through the *real* worker at seed time — so the seed is the pipeline's first integration test. Course thumbnails are the pipeline's poster frames. Credits in `api/app/seed/CREDITS.md`. ~40 seeded enrollments with heartbeats so earnings, retention curves and the pool split show real numbers.

### 5. Versions — base → mid → advanced
Every project is cut base → mid → advanced (rule set 2026-09-15), plus one unique free feature as v4 (rule set 2026-09-17). v1 alone is a complete, sellable course platform on our own video stack; each later version adds a money shape or a surface, never a second engine.

| Version | Ships | Proves | ~Hours |
|---|---|---|---|
| **v1 Classroom** (base) | Auth (email + password, `sr_session`, roles student / creator / admin; three demo logins) · home, browse by category, course page (curriculum, preview lesson, creator, price) · **buy a course** (Razorpay, idempotent `mark_paid`, enrollment, ledger) · **the player**: hls.js adaptive over encrypted HLS, signed key endpoint, **resume across devices** (heartbeat + beacon), mark complete, course progress · My learning · **Creator studio**: apply → course → sections → lessons, **video upload → worker → live processing status**, resources, publish · **Admin** (dashboard, creator applications, courses / takedown, video jobs / retry) · **certificate PDF** at 100 % with a public `/verify/{code}` · seed (decision 4) | The pipeline, the key server, RBAC, resume | 16 |
| **v2 All-access** (mid) | Razorpay **Subscriptions** (state machine, grace, cancel-at-period-end) · `can_watch` grows the branch · **quizzes** per section, pass mark gates the certificate · creator **earnings + payout requests**, admin marks paid · emails (Resend: receipt, certificate, payout, approval) · captions (VTT upload) + thumbnail-sprite scrubbing · Continue watching rail | Recurring billing; assessment; the ledger in use | 11 |
| **v3 Royalties** (advanced) | **Subscription pool split by minutes watched** (monthly close → `pool_share` entries, the math on the earnings page) · creator **analytics**: per-lesson retention curve and drop-off points from heartbeats · **device limit**: the key endpoint counts active playback sessions (max 2) → the access-control proof gets teeth (still not DRM) · full-text course search | Ledger computation; analytics from the player's own telemetry | 8 |
| **v4 Offline lessons** (unique, free) | Skillroom installs as a **PWA**; "Download" on a lesson stores the 480p encrypted segments in Cache Storage; **encrypted offline playback with a time-limited, device-bound entitlement** — the key arrives under a **48-h offline lease** bound to the device (no hardware-backed protection in a PWA) (`POST /lessons/{id}/offline-lease`, requires `can_watch`), refreshed on reconnect; hls.js plays from a custom loader when offline; progress queues and syncs when back online | Reach: the course leaves the network, and the entitlement model survives it (Viraj, 2026-09-17) | 3 |

### 6. Stack and setup — lean
Shared stack from [`projects/README.md`](../README.md): `web/` Next.js App Router + Tailwind 4, `api/` FastAPI on Vercel (FastAPI preset, `bom1`), Neon Postgres, Vercel Blob, own cookie-session auth (`sr_session`), Razorpay (test mode), Resend (v2). New deps: `hls.js` in web; `httpx`, `fpdf2` (certificates), `razorpay` in api; **ffmpeg** on the worker only (never in the Vercel bundle). Setup is the minimum to deploy both apps with plain CI (web typecheck + build, api ruff + pytest). OpenAPI → TS types by script, committed, not CI-gated; no Sentry, no uptime monitor. **Accounts and keys are created just-in-time** in the plan row that first needs them: Neon in S2, Vercel Blob + a GitHub fine-grained token (for `repository_dispatch`) + the Actions secrets in S3, Razorpay in F3, Resend in L4.

## The wow moment (v1, + v3) — the demo shows the engine
1. **Upload and watch it process:** drop a 200 MB screen recording into the studio. The upload bar fills; the job goes *queued → processing* live; the three renditions light up one by one (240p ✓ 480p ✓ 720p ✓); the poster develops. Two minutes later the same lesson plays on your phone, switches to 480p when the network dips, and on the laptop asks "Resume at 4:12?".
2. **Show the ciphertext:** download one `.ts` segment from its public Blob URL and open it (or `ffprobe` it) — no playable stream, just AES-128 ciphertext; without a key from the key server it is noise.
3. **Third device refused (v3):** the lesson is playing on a laptop and a phone; open it in a third browser → the key server answers `too_many_devices` and the player names the limit.

Then finish the course: a certificate PDF with your name is waiting, and anyone can verify its code. (Viraj, 2026-11-19)

## Add-ons (after v4, only from time saved)
Nice-to-have, not priority (Viraj, 2026-09-17): listed in [docs/07-plan.md](docs/07-plan.md) — Q&A per lesson · coupons · drip scheduling · Razorpay Route transfers · ratings & reviews · private podcast feed · embeddable preview player · timestamped notes & bookmarks · co-instructors. Skipping all of them is fine.

## Out of scope (all versions)
Live classes · DRM (Widevine / FairPlay) · auto-captions or any paid AI · course bundles · affiliate links · multi-currency · a mobile app (the PWA is the app) · real-money billing · mobile studio (creator = desktop) · community / forums · multiple admins.

## Success criteria
- **A non-enrolled user can never obtain a playable video** (access control, not DRM: an entitled user is trusted with the key) — covered by tests: key endpoint 403 without entitlement, expired token 401, token for lesson A refused on lesson B, refund revokes; and by a demo: a raw segment URL in a fresh tab is ciphertext.
- Upload → playable on a phone in ≤ 3 min for a 2-min 1080p source, with the ladder switching under throttling (DevTools "Slow 3G" drops to 240p without a stall > 2 s).
- Progress resumes on another device within 10 s of stopping; a completed lesson stays completed.
- A purchase on a phone in under 2 minutes from the course page (demo card); replayed webhooks are no-ops; one enrollment per paid order.
- Certificate issues exactly once at 100 % (v2: and all quizzes passed); `/verify/{code}` is public and correct.
- Lighthouse mobile ≥ 90 perf / 100 a11y / 100 SEO on home, browse and course pages (the player page excluded from the perf budget; posters via `next/image`, no CLS).
- v4: on an Android phone in airplane mode, a downloaded lesson plays from the first tap; the lease expiry is enforced.
- A visible frontend signature (chosen in step 4, direction **C · Notebook**, [docs/04-ui-mockups.md](docs/04-ui-mockups.md)): **Develop + Stamp** in the studio (renditions tick in, the poster develops, the stamp flips to *ready*), **Resume glide** with a sticky-note toast in the player, curriculum draw and certificate print, themed browser surfaces, reduced-motion fallbacks.

## Resolved questions
- *Mux / Cloudflare Stream or our own?* Our own: Blob + ffmpeg worker on Actions + AES-128 HLS + API key server (Viraj, 2026-09-17, fork 1). Mux would hide the thing the project proves; Stream is not free.
- *Purchase or subscription in v1?* Purchase in v1, subscription in v2, the pool split in v3 (fork 2).
- *Payouts: Route or a ledger?* Ledger + admin-marked payouts; Route is an add-on (fork 3).
- *Is the admin a UI?* Yes, a small one — four screens; the third role must be visible in the demo (fork 4).
- *Seed size and where the video comes from?* 6 / 24 / ≤ 700 MB, real CC video from Commons through the real worker (fork 5).
- *v4?* Offline lessons over the private podcast feed and the embeddable preview player (Viraj, 2026-09-17).
- *Certificates: which renderer?* `fpdf2` in the API (pure Python, fits the Vercel bundle); no headless browser.
- *Auth: Better Auth / Drizzle?* No — those were the old TS-stack notes; own cookie session in FastAPI like every other project.
