# Skillroom — Development Plan

**Lifecycle step:** 7 of 17 · **Written:** 2026-09-17 · **Inputs:** [03-requirements.md](03-requirements.md), [04-technical-design.md](04-technical-design.md), [06-data-and-api.md](06-data-and-api.md).
**Tracker:** row status lives at https://claude.ai/artifact/AxgaJ1fZ6HELpWTZuBUXz6 (updated per milestone; rebuild the page with `python mockups/tracker-build.py`).
**Budget:** v1 ≈ 16 h · v2 ≈ 11 h · v3 ≈ 8 h · v4 ≈ 3 h. v1 runs the whole video pipeline and the key server from milestone 1.0, so v2 and v3 add money shapes and telemetry, and v4 adds a surface — never a second engine. **Cadence:** evenings/weekends; each row = one branch + one PR, squash-merged, and **every PR shows something in the browser**. Milestones end deployed. **Build starts after Offcut** (order 1 → 2 → 4 → 5 → 3 → 6).

**Lean rules in force** (2026-09-15): setup is the minimum to deploy both apps with plain CI; no observability, contract gates, e2e workflows or tracker updates per PR; review findings fixed on the same branch; tests only from 04 §13. Hours saved go to the player, the studio's processing moment and the seed videos. **Accounts and keys are created just-in-time** — in the row that first needs them, never in a setup batch: **Neon in S2; Vercel Blob, the GitHub fine-grained dispatch token and the three Actions secrets in S3; Razorpay in F3; Resend in L4.** Videos are CC from Wikimedia Commons, fetched by script in S3.

How the lifecycle maps: step 8 = milestone 1.0; steps 9–11 and 14–15 cycle inside every row; step 12 is one checklist row at the end of v1; step 13 is the CI file in 1.0; step 16 is skipped unless something breaks; step 17 is a short doc after v3.

Column key — **Who:** 🟢 student · 🟠 creator · 🟣 admin · ⚪ platform / worker. Endpoints from 06 §C; screens from 03-user-flows.

---

## v1 — Classroom (≈ 16 h)

### Milestone 1.0 — Skeleton + the pipeline live (≈ 6 h) — step 8
Goal: both apps deployed, the worker transcoding on Actions, every seeded lesson `ready` and playable through the key server, direction chosen.

| # | Part | Who | web/ | api/ | Est. | Done when |
|---|---|---|---|---|---|---|
| S1 | **Direction + tokens** | 🟢 | Variant page per [04-ui-mockups.md](04-ui-mockups.md) (six directions × six screens, live motion candidates, CC photos) → Viraj picks → tokens + fonts in `globals.css`, themed browser surfaces | — | 1.5 h | Chosen direction recorded in 04-ui-mockups; landing restyled only if tokens changed |
| S2 | **API skeleton + DB + auth + catalogue seed** | ⚪ | `next.config.ts` rewrite `/api/*`; `lib/api.ts` typed fetch; `pnpm gen:api` | `pyproject` (uv), `main.py`, settings, error envelope, `/health`; models + Alembic `0001_v1` (06 §A); `/auth/*` (argon2, sessions, `sr_session`, `/auth/demo`, roles, `require_*`); `seed/catalog.json` — 6 creators, 6 courses, 12 sections, 24 lessons (no video yet), ~10 students; `seed.py` (idempotent); `GET /home`, `/courses`, `/courses/{slug}`, `/creators/{handle}`; **accounts needed here and no others:** Vercel project `skillroom-api` (FastAPI preset, bom1) + Neon (`DATABASE_URL`); `ci.yml` (web typecheck + build · api ruff + pytest with `postgres:17`); **test:** `rbac` | 2 h | `api.skillroom…/docs` opens in prod; `GET /courses` lists six courses with curricula; a student hitting `/admin/*` gets 404; seed runs twice cleanly; CI green |
| S3 | **The video pipeline: worker + Actions + stream + video seed** | ⚪ | — | `worker/transcode.py` + `worker/ffmpeg.py` (claim → probe → ladder + AES-128 → poster + sprite → Blob → complete), `services/jobs.py` (enqueue, GitHub dispatch, claim, complete, fail, stale), `services/blob.py`, `services/playback.py` (token sign / verify, master + media playlists), `services/entitlement.py::can_watch`, `routers/internal.py`, `routers/stream.py`, `POST /lessons/{id}/play`; `.github/workflows/transcode.yml`; `seed/fetch_videos.py` (Commons API, `video/webm`, licence filter, backoff, `CREDITS.md`) → `seed/videos/` sliced to 90–150 s by ffmpeg; `seed.py videos` enqueues 24 jobs and runs the worker `--poll` locally; `scripts/eval_stream.py`; **Vercel Blob store, GitHub dispatch token and Actions secrets created here** (`BLOB_READ_WRITE_TOKEN`, `GITHUB_DISPATCH_TOKEN`, `GITHUB_REPO`, `WORKER_SECRET`, `PLAYBACK_SECRET`); **tests:** `worker` (fixture), `playlists`, `key_endpoint`, `upload_token` | 2.5 h | All 24 seeded lessons `ready` in Blob under ≤ 700 MB; a job dispatched from prod runs on Actions and completes; `eval_stream.py` parses every master playlist; a raw segment URL in a fresh tab is ciphertext; the key endpoint 403s an unentitled session; tests green |

### Milestone 1.1 — Learn (≈ 5 h) 🟢
| # | Part | Who | web/ | api/ | Est. | Done when |
|---|---|---|---|---|---|---|
| F1 | **Home + browse + course page + creator page** | 🟢 | S1 home (hero, categories, new courses, free to start, creators); S2 browse with `CourseCard` (poster via `next/image`, price / Free), `CategoryChips` in the URL; S3 course page with `Curriculum` (preview badges, durations, ticks when enrolled), `CreatorCard`, the state button (Buy / Enrol free / Start / Continue); S19 creator page; **v1 motion touch if chosen (e.g. Curriculum draw)** | cache headers; `app/api/revalidate` contract; `POST /courses/{id}/enrol` (free) | 1.5 h | `/courses?category=pottery` is shareable and correct; Lighthouse mobile ≥ 90 / 100 / 100 on home, browse and course with no CLS; the free yoga course enrols in one tap |
| F2 | **The player + progress + resume** | 🟢 | S4 `/learn/[slug]/[lesson]`: `Player` (hls.js dynamic import, native HLS fallback, `startPosition`), `Controls` (speed, keyboard map, fullscreen), `ResumeToast` (**the resume moment**), sidebar `Curriculum` with ticks and next / previous, resources list, mark complete; S20 states: not enrolled (preview only + buy state), processing, failed | `POST /lessons/{id}/progress` (JSON + `text/plain` beacon), `/complete`, `services/progress.py` (heartbeat upsert, `resume_at`, `maybe_complete_course`), `GET /me`; **test:** `progress` | 2 h | Watch on a phone, open the laptop → "Resume at 4:12" and it seeks; throttle to Slow 3G → drops to 240p without a stall > 2 s; sign out → the key request 403s and the player shows the buy state |
| F3 | **Buy a course + ledger + My learning** | 🟢 | S5 buy sheet on the course page, `RazorpayButton` (lazy `checkout.js`, modal, verify, dismissed message); S6 `/me` (courses with progress + Continue, certificates placeholder, account); S8 sign in / up with three demo buttons | **Razorpay test account + webhook created here** (`RAZORPAY_*`); `services/checkout.py` (create order, `mark_paid` with enrollment + ledger, `expire_stale`), `services/ledger.py`, `services/razorpay.py`; `/checkout*`, `/orders`, `/webhooks/razorpay`; order numbers `SR-####`; **test:** `mark_paid` | 1.5 h | A student buys the pottery course on a phone with the test card in under 2 minutes and the Start button appears; the webhook replay is a no-op; the ledger shows +₹1,199.20 to the creator and +₹299.80 to the platform |

### Milestone 1.2 — Studio + admin + close (≈ 5 h) 🟠🟣
| # | Part | Who | web/ | api/ | Est. | Done when |
|---|---|---|---|---|---|---|
| F4 | **Creator studio: apply, courses, sections, lessons, upload** | 🟠 | S8 `/apply` + status; `(studio)` layout (404 for non-creators); S9 course list; S10 editor with `CourseForm`, `SectionList` + `LessonRow` (drag reorder, preview toggle, video state chip), publish checklist; S11 lesson page with `VideoPanel` (drop zone, `@vercel/blob/client` upload with progress, completion POST, **job status polling: queued → processing with rendition ticks → ready with the poster developing — the signature moment if chosen**, failed + retry), `ResourceList` | `/apply`; `/creator/courses*`, `/sections*`, `/lessons*` (own rows only), `/creator/lessons/{id}/video/token` (client-token protocol), `/video` (HEAD check, key + prefix, enqueue, dispatch), `/video` GET (status), `/retry`, `/resources*`; `GET /creator/earnings` (read-only in v1); revalidate on publish | 2 h | The demo creator uploads a 2-min 1080p file from the studio and watches it go ready in ≤ 3 min on prod, previews it, publishes the course, and it appears in browse; publishing with no ready lesson is refused with reasons |
| F5 | **Admin: dashboard, creators, courses, jobs** | 🟣 | `(admin)` layout (404 for non-admins); S13 dashboard; S14 `Applications` (approve / reject + note) and the creator list; S15 `CourseTable` (takedown / restore + note) and `JobsBoard` (by state, attempts, error tail, retry) | `/admin/dashboard`, `/admin/creators*`, `/admin/courses*`, `/admin/jobs*`; `services/jobs.py::stale()` on the board load | 1.5 h | Approving the demo applicant unlocks `/studio` on their next request; a takedown 404s the public page; retrying a failed job re-dispatches exactly one run on Actions |
| F6 | **Certificate + verify + v1 close** | 🟢 | S7 `/certificates/[code]` (PDF view + download) and public `/verify/[code]`; `/me` certificates list; S20 remaining states | `services/certificates.py` (fpdf2, Onest TTFs, Blob), `GET /verify/{code}` (rate-limited), issue inside `maybe_complete_course`; README "how the pipeline and the key server work" with diagrams; `docs/12-security-performance.md` (one page + Lighthouse numbers); **test:** `certificate_once` | 1.5 h | Finishing the last lesson issues one PDF with the student's name; `/verify/SR-…` is public and correct; an unknown code → not found; v1 tagged; case-study entry drafted |

**v1 total ≈ 16 h**

---

## v2 — All-access (≈ 11 h)

### Milestone 2.0 — Subscribe + assess (≈ 5 h) 🟢
| # | Part | web/ | api/ | Est. | Done when |
|---|---|---|---|---|---|
| L1 | **Subscriptions** | S18 `/all-access` (₹499 / month, subscribe → modal); `/me` subscription card (state, renews on, cancel at period end); the course page's state button knows "Included in All-access" | `scripts/create_plan.py` (**`RAZORPAY_PLAN_ID`**); `POST /subscriptions`, `/subscriptions/cancel`; webhook `subscription.*` → `services/subscriptions.py` state machine (grace 3 d, cancel-at-period-end); `active_subscription()` in `can_watch`; lazy `enrollments(source = subscription)` on first play; **test:** `subscription_states` | 3 h | Subscribe with the test card → every course plays; simulate `halted` → still plays for 3 days, then 403; cancel → access until `current_end` |
| L2 | **Quizzes** | S10 `QuizEditor` per section (pass mark, questions, options); S17 `/learn/[slug]/quiz/[id]` (answer, submit, score, retry, best attempt); the curriculum shows the quiz after the section's last lesson; certificate gate message | `quizzes`, `questions`, `attempts`; `PUT /creator/sections/{sid}/quiz`; `GET /quizzes/{id}` (no `correct`), `POST /quizzes/{id}/attempts`; `maybe_complete_course` requires every quiz passed; **test:** `quiz_gate` | 2 h | Fail a quiz → no certificate; pass → certificate issues; the correct index never appears in the questions payload |

### Milestone 2.1 — Money out + polish (≈ 6 h) 🟠🟣
| # | Part | web/ | api/ | Est. | Done when |
|---|---|---|---|---|---|
| L3 | **Earnings + payouts + refunds** | S12 `/studio/earnings` (balance available / pending / paid, entries, **Request payout**); S16 `/admin/payouts` (`PayoutQueue`: pay with reference / reject with note); admin order refund button | `payouts`; `POST /creator/payouts` (≥ ₹500, ≤ available, one open); `/admin/payouts*`; `POST /admin/orders/{id}/refund` (Razorpay refund, negative entries, enrollment removed); **test:** `payout_balance` | 2 h | Request ₹1,000 → admin pays with a UTR → the creator's paid total moves and available drops; a request above available → 422; a refunded student's next key request 403s |
| L4 | **Emails + forgot password** | Forgot / reset pages | **Resend key created here**; React Email templates: receipt, certificate issued, payout paid, creator approved / rejected, reset; `email_log`; `/auth/forgot`, `/auth/reset` | 1.5 h | The receipt arrives within a minute of `paid` with a working course link |
| L5 | **Captions + scrub preview + Continue watching + v2 close** | S11 captions upload (`.vtt`); S4 `<track>` + `c` toggle, `ScrubPreview` from the sprite geometry; S1 `Continue watching` rail for signed-in students; motion polish on the player | `captions` upload token + row; `/play` returns `sprite` + `captions`; `/home` returns `continue_watching` | 2.5 h | Hovering the bar shows the right frame within ± 5 s; captions toggle; home shows the demo student's in-progress course first; v2 tagged; case study updated |

**v2 total ≈ 11 h**

---

## v3 — Royalties (≈ 8 h)

### Milestone 3.0 — The pool, analytics, teeth (≈ 8 h) 🟠🟣🟢
| # | Part | web/ | api/ | Est. | Done when |
|---|---|---|---|---|---|
| A1 | **Subscription pool split by minutes watched** | S12 pool section ("₹4,120 · 1,240 subscriber-minutes · 12.3 % of the pool" per month, with the total pool); S13 admin **Close month** with a preview of the lines | heartbeats upsert `watch_minutes` (by source); `services/pool.py::close_month()` (pool = charges × 0.8, floor shares, remainder to the largest, `pool_share` entries, `pool_closes`), `POST /admin/pool/close`; seed adds 3 months of subscription charges + minutes; **test:** `pool_close` | 3 h | Closing a seeded month writes entries that sum to the pool exactly; closing twice → 409; the creator page shows the math |
| A2 | **Creator analytics: retention curves** | S10 analytics tab: per-lesson curve (SVG, per 10-s bucket), drop-off markers, completion %, average watched | heartbeats upsert `watch_buckets`; `GET /creator/courses/{id}/analytics` | 2 h | The curve for a seeded lesson matches a SQL check; the biggest drop-off is marked at the right second |
| A3 | **Device limit** | S20 "Playing on 2 other devices" state in the player with the limit named | `playback_sessions` upsert in the key endpoint; count active in 5 min; `403 too_many_devices`; **test:** `device_limit` | 1.5 h | Three browsers within 5 min → the third is refused; after 5 min idle it plays |
| A4 | **Course search + v3 close** | S2 search box (URL `q`), results with the matched field hinted | `courses.search` tsvector + GIN; `/courses?q=`; `docs/17-post-launch.md` (½ page); case study | 1.5 h | "naan" finds the flatbreads course by description alone; v3 tagged; case study live |

**v3 total ≈ 8 h**

---

## v4 — Offline lessons (≈ 3 h) — the unique free feature 🟢

### Milestone 4.0 — Offline (≈ 3 h)
Same core, a new place: the lesson leaves the network. ₹0 per use (Viraj, 2026-09-17).

| # | Part | web/ | api/ | Est. | Done when |
|---|---|---|---|---|---|
| U1 | **PWA + download + offline playback** | `manifest.webmanifest` (name, icons from `brand/`, `display: standalone`), hand-written `sw.js` (app shell precache, network-first pages); `DownloadButton` on S4: fetch the 480p playlist through the API + every segment into `caches.open('offline-{lesson}')`, lease into IndexedDB (`idb-keyval`); `lib/offline.ts` — hls.js custom loader serving playlist / segments / key from cache, refusing on an expired lease; `/me` downloads list with sizes + Remove | `offline_leases`; `POST /lessons/{id}/offline-lease` (requires `can_watch`, 48 h, refresh), `DELETE`; leases revoked on refund / takedown | 2 h | On an Android phone in airplane mode a downloaded lesson plays from the first tap; an expired lease refuses with "Reconnect to renew"; a refunded student's next refresh fails and the download is removed |
| U2 | **Install + sync + v4 close** | Install prompt on the player (`beforeinstallprompt`, dismissible, remembered); offline progress queue in IDB flushed on `online`; "Take it offline" card on S4 with the how-to; README section "the lesson in your pocket"; `docs/17-post-launch.md` (½ page); case study | — | 1 h | Progress made offline shows on the laptop after reconnecting; reviewer installs from the player in one tap; v4 tagged; case study live |

**v4 total ≈ 3 h** · **Project total ≈ 38 h**

---

## Whole-product summary
| Version | Milestones | Hours | Cumulative |
|---|---|---|---|
| v1 Classroom | 1.0 – 1.2 | 16 | 16 |
| v2 All-access | 2.0 – 2.1 | 11 | 27 |
| v3 Royalties | 3.0 | 8 | 35 |
| v4 Offline lessons | 4.0 | 3 | 38 |
| Add-ons (in priority order) | A Q&A (3) · B coupons (2) · C drip (2) · D Route transfers (3) · E ratings (2) · F podcast feed (3) · G embeddable preview (2) · H notes & bookmarks (2) · I co-instructors (2) | up to 21 | up to 59 |

## Add-ons (only from time saved)
**Nice-to-have, not priority** (Viraj, 2026-09-17): considered only after v4 is fully done (docs and case study included), in this order, from time saved — and skipping all of them is a fine outcome. None is a version; none changes the engine. All free to run.

| # | Add-on | What | Version it extends | ~h |
|---|---|---|---|---|
| A | **Q&A per lesson** | Threaded questions under the player with creator answers pinned; creator inbox in the studio | v1 | 3 |
| B | **Coupons** | `coupons(code, percent, max_uses, expires_at)` applied on the buy sheet; Razorpay amount reflects it | v1 | 2 |
| C | **Drip scheduling** | Sections unlock N days after enrollment; the curriculum shows "unlocks in 3 days" | v1 | 2 |
| D | **Razorpay Route transfers** | `PayoutProvider` protocol; `RouteProvider` creates a linked account per creator and a transfer per payout; the ledger stays the source of truth (needs Route enabled + KYC for live) | v2 | 3 |
| E | **Ratings & reviews** | 1–5 stars + a line, only from students ≥ 50 % through; average on the card | v1 | 2 |
| F | **Private podcast feed** | The worker adds an audio-only rendition; each enrolled student gets a tokenised RSS URL for podcast apps | v1 | 3 |
| G | **Embeddable preview player** | `/embed/[slug]` iframe + oEmbed for the preview lesson; enrol links back | v1 | 2 |
| H | **Notes & bookmarks** | Timestamped notes on the player, listed per course, exported as Markdown | v1 | 2 |
| I | **Co-instructors** | A second creator on a course with a revenue split percentage in the ledger | v2 | 2 |
