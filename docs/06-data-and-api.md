# Skillroom — Database + API Design

**Lifecycle step:** 6 of 17 · **Locked:** 2026-09-17 · Behaviour in [04-technical-design.md](04-technical-design.md). Alembic `0001_v1` creates everything under **A**; v2 / v3 / v4 tables get their own migrations.

## A. Postgres schema (v1)

```sql
create type user_role       as enum ('student','creator','admin');
create type creator_status  as enum ('applied','approved','rejected');
create type course_status   as enum ('draft','published','takedown');
create type category        as enum ('pottery','baking','art','yoga','photography','music');
create type video_status    as enum ('none','queued','processing','ready','failed');
create type job_state       as enum ('queued','processing','ready','failed');
create type enrol_source    as enum ('purchase','free','subscription','admin');
create type order_state     as enum ('pending_payment','paid','failed','expired','refunded');
create type ledger_kind     as enum ('sale','fee','refund','payout','pool_share');

users            (id uuid pk, email citext unique, password_hash text, name text, role user_role default 'student', created_at)
sessions         (id text pk, user_id uuid fk, expires_at timestamptz, created_at)                        index (user_id)
creator_profiles (user_id uuid pk fk, handle citext unique, display_name text, area text, bio text, subject text,
                  avatar_url text null, status creator_status default 'applied', note text null, payout_note text null,
                  applied_at, decided_at null, decided_by uuid fk null)

courses          (id uuid pk, creator_id uuid fk, slug citext unique, title text, subtitle text, category category, level text,
                  price_paise int check (price_paise >= 0), description text, cover_url text null,
                  status course_status default 'draft', takedown_note text null, published_at null, created_at, updated_at)
                  index (creator_id) · index (status, category)
sections         (id uuid pk, course_id fk, title text, sort int)                                          index (course_id, sort)
lessons          (id uuid pk, section_id fk, course_id fk, title text, sort int, is_preview bool default false,
                  duration_s int null, created_at)                                                        index (section_id, sort) · index (course_id)
videos           (id uuid pk, lesson_id uuid fk unique, source_url text, source_bytes bigint, prefix text unique,
                  key_hex char(32), iv_hex char(32), status video_status default 'queued',
                  manifest jsonb null, poster_url text null, sprite_url text null, duration_s int null, created_at, ready_at null)
video_jobs       (id uuid pk, video_id fk, state job_state default 'queued', attempts int default 0, error text null,
                  dispatch_error text null, claimed_at null, finished_at null, created_at)                  index (state, created_at)
resources        (id uuid pk, lesson_id fk, name text, url text, bytes int, created_at)                    index (lesson_id)

enrollments      (id uuid pk, user_id fk, course_id fk, source enrol_source, order_id uuid fk null, created_at)
                  unique (user_id, course_id) · index (course_id)
progress         (user_id fk, lesson_id fk, course_id fk, position_s int default 0, watched_s int default 0,
                  completed bool default false, completed_at null, updated_at, primary key (user_id, lesson_id))  index (user_id, course_id)
certificates     (id uuid pk, code text unique, user_id fk, course_id fk, pdf_url text, issued_at)         unique (user_id, course_id)

orders           (id uuid pk, number text unique,                      -- 'SR-1042', sequence-backed
                  user_id fk, course_id fk, amount_paise int, state order_state,
                  razorpay_order_id text unique, razorpay_payment_id text null, refund_id text null,
                  created_at, paid_at null, updated_at)                                                     index (user_id, created_at desc) · index (state, created_at)
ledger_entries   (id uuid pk, account text,                            -- 'platform' | 'creator:{user_id}'
                  kind ledger_kind, amount_paise int,                  -- signed
                  order_id fk null, payout_id uuid null, period char(7) null, note text null, created_at)  index (account, created_at)
webhook_events   (id text pk, event text, received_at)
```

`videos.key_hex` never leaves the API except to the worker's claim response and the key endpoint's 16-byte body. `videos.manifest` is the worker's report (renditions with segment durations, sprite geometry) — playlists are generated from it on every request, never stored. `progress.completed` is monotonic (the upsert uses `completed or excluded.completed`). `orders.amount_paise` is a snapshot of the price at checkout. `ledger_entries` is append-only; balances are sums.

**mark_paid recipe** (verify and webhook share it):
```sql
begin;
  select * from orders where id = $1 for update;                                  -- if state <> 'pending_payment' → commit, no-op
  update orders set state = 'paid', razorpay_payment_id = $2, paid_at = now() where id = $1;
  insert into enrollments (user_id, course_id, source, order_id) values ($u, $c, 'purchase', $1) on conflict do nothing;
  insert into ledger_entries (account, kind, amount_paise, order_id) values ('creator:'||$creator, 'sale', round($amt * 0.8), $1),
                                                                            ('platform', 'fee', $amt - round($amt * 0.8), $1);
commit;
```

**Heartbeat recipe:**
```sql
insert into progress (user_id, lesson_id, course_id, position_s, watched_s, completed, completed_at, updated_at)
values ($u, $l, $c, $pos, least($delta, 15), $pos >= 0.9 * $dur, case when $pos >= 0.9 * $dur then now() end, now())
on conflict (user_id, lesson_id) do update set
  position_s = excluded.position_s, watched_s = progress.watched_s + excluded.watched_s,
  completed = progress.completed or excluded.completed,
  completed_at = coalesce(progress.completed_at, excluded.completed_at), updated_at = now();
-- then: if every ready lesson of the course is completed and no certificate exists → issue()
```

**v2 additions:** `subscriptions (id, user_id fk, razorpay_subscription_id text unique, plan_id text, state text, current_end timestamptz null, cancel_at_period_end bool, created_at, updated_at)` index (user_id); `quizzes (id, section_id fk unique, pass_pct int)`; `questions (id, quiz_id fk, text, options jsonb, correct int, sort)`; `attempts (id, user_id fk, quiz_id fk, answers jsonb, score_pct int, passed bool, created_at)` index (user_id, quiz_id); `payouts (id, creator_id fk, amount_paise int, state text requested|paid|rejected, reference text null, note text null, requested_at, decided_at null, decided_by fk null)`; `captions (lesson_id pk fk, url, lang)`; `email_log (id, user_id fk, kind, sent_at)`; `users.reset_token`, `reset_expires_at`.
**v3 additions:** `watch_minutes (month char(7), creator_id fk, course_id fk, user_id fk, source enrol_source, seconds int, primary key (month, course_id, user_id))`; `watch_buckets (lesson_id fk, bucket int, viewers int, primary key (lesson_id, bucket))`; `playback_sessions (user_id fk, lesson_id fk, device_id text, last_seen timestamptz, primary key (user_id, lesson_id, device_id))`; `pool_closes (month char(7) pk, pool_paise int, total_seconds bigint, lines jsonb, closed_at, closed_by fk)`; `courses.search tsvector` generated (title A, subtitle B, description C) + GIN.
**v4 additions:** `offline_leases (id uuid pk, user_id fk, lesson_id fk, device_id text, expires_at timestamptz, revoked bool default false, created_at)` unique (user_id, lesson_id, device_id).

## B. Blob keys
| Prefix | Written by | Deleted when |
|---|---|---|
| `video-src/{lesson_id}/{uuid}.{ext}` | Creator's browser (client token from the API) | Job `ready` (source no longer needed) or orphan GC |
| `video/{prefix}/{rendition}_{nnn}.ts` · `poster.jpg` · `sprite.jpg` | Worker | Video replaced (after the new one is `ready`) or lesson deleted |
| `resources/{lesson_id}/{uuid}.{ext}` | Creator's browser (client token) | Resource removed |
| `captions/{lesson_id}/{lang}.vtt` (v2) | Creator's browser | Replaced |
| `certificates/{code}.pdf` | API (`issue()`) | Never |
| `avatars/{user_id}.jpg` | Seed / creator profile | Replaced |

## C. REST API (`/api/*` from the browser; FastAPI serves `/docs`)

Error envelope everywhere: `{ "error": { "code": "not_entitled", "message": "…", "details": {…} } }`. Auth via cookie; `🔒` = signed in, `🎓` = creator (404 otherwise, and only own courses), `👑` = admin (404 otherwise), `⚙` = worker secret / server-to-server, `🎟` = playback token in `?t=`. Money fields are paise integers.

### Auth
| Method | Path | Body → Returns |
|---|---|---|
| POST | `/auth/sign-up` | `{ email, password, name }` → `Me` |
| POST | `/auth/sign-in` | `{ email, password }` → `Me` |
| POST | `/auth/sign-out` | → 204 |
| GET | `/auth/me` | `Me { id, name, email, role, creator_status? }` · 401 |
| POST | `/auth/demo` | `{ as: 'student' \| 'creator' \| 'admin' }` → `Me` |
| POST 🔒 | `/apply` | `{ display_name, handle, area, bio, subject }` → `CreatorProfile` · 409 `already_applied` |

### Catalogue (public)
| Method | Path | Returns |
|---|---|---|
| GET | `/home` | `{ new_courses: CourseCard[], free_to_start: LessonCard[], categories: {key, count, cover}[], creators: CreatorCard[], continue_watching?: ContinueCard[] (v2, 🔒) }` · `s-maxage=300` |
| GET | `/courses?category=&q= (v3)&page=` | `Page<CourseCard>` — published with ≥ 1 ready lesson |
| GET | `/courses/{slug}` | `Course` (sections → lessons with duration, `is_preview`, and — signed in — `completed`, `enrolled`, `progress_pct`, `certificate_code?`) · 404 if draft / takedown |
| GET | `/creators/{handle}` | `CreatorPage { profile, courses: CourseCard[] }` |
| GET | `/verify/{code}` | `{ name, course_title, creator_name, issued_at }` · 404 (rate-limited 30/min/IP) |

### Learning 🔒
| Method | Path | Body → Returns |
|---|---|---|
| POST | `/lessons/{id}/play` | `{ device_id }` → `Play { master_url, poster_url, resume_at, duration_s, sprite?: SpriteMeta (v2), captions?: [] (v2) }` · 403 `not_entitled` · 409 `video_not_ready` |
| POST | `/lessons/{id}/progress` | `{ position_s, watched_delta_s, client_ts }` → `{ completed, course_progress_pct, certificate_code? }` (also accepts a `text/plain` JSON body for `sendBeacon`) |
| POST | `/lessons/{id}/complete` | → same as progress |
| POST | `/courses/{id}/enrol` | → `Enrollment` — free courses only · 422 `not_free` · 409 `already_enrolled` |
| GET | `/me` | `MePage { courses: [{ course: CourseCard, progress_pct, continue_lesson: {id, title, resume_at} }], certificates: CertificateCard[], subscription?: Subscription (v2), downloads?: [] (v4) }` |
| GET | `/certificates/{code}` | `Certificate { code, course, name, issued_at, pdf_url }` — owner only |

### Streaming 🎟
| Method | Path | Returns |
|---|---|---|
| GET | `/stream/{lesson_id}/master.m3u8?t=` | `application/vnd.apple.mpegurl` · 401 `bad_token` |
| GET | `/stream/{lesson_id}/{rendition}.m3u8?t=` | media playlist with `EXT-X-KEY` and absolute Blob segment URLs |
| GET | `/stream/{lesson_id}/key?t=` | 16 bytes `application/octet-stream`, `private, no-store` · 401 `bad_token` · 403 `not_entitled` · 403 `too_many_devices` (v3) |

### Checkout
| Method | Path | Body → Returns |
|---|---|---|
| POST 🔒 | `/checkout` | `{ course_id }` → `{ order_id, number, razorpay_order_id, key_id, amount_paise }` · 409 `already_enrolled` · 422 `free_course` |
| POST 🔒 | `/checkout/{order_id}/verify` | `{ razorpay_payment_id, razorpay_signature }` → `Order` · 400 `bad_signature` |
| GET 🔒 | `/orders` | `OrderCard[]` |

### Creator studio 🎓
| Method | Path | Body → Returns |
|---|---|---|
| GET | `/creator/courses` | `StudioCourseRow[]` (cover, title, status, lessons_ready, lessons_total, enrollments, revenue_paise) |
| POST | `/creator/courses` | `{ title, subtitle, category, level, price_paise, description }` → `StudioCourse` (slug generated) |
| GET/PATCH | `/creator/courses/{id}` | `StudioCourse` (sections → lessons with `video: { status, poster_url, duration_s, error? }`, `publish_checklist`) |
| POST | `/creator/courses/{id}/publish` · `/unpublish` | → `StudioCourse` · 409 `not_publishable { reasons }` |
| POST/PATCH/DELETE | `/creator/courses/{id}/sections` · `/sections/{sid}` | `{ title, sort }` |
| POST/PATCH/DELETE | `/creator/sections/{sid}/lessons` · `/creator/lessons/{lid}` | `{ title, sort, is_preview }` |
| POST | `/creator/lessons/{lid}/video/token` | `{ type: 'blob.generate-client-token', payload }` → `{ type, clientToken }` (the `@vercel/blob/client` protocol) |
| POST | `/creator/lessons/{lid}/video` | `{ url, size }` → `VideoStatus` — records the source, generates key + prefix, enqueues, dispatches · 422 `bad_source` |
| GET | `/creator/lessons/{lid}/video` | `VideoStatus { status, job: { state, attempts, error?, claimed_at? }, renditions_done: string[], poster_url?, duration_s? }` (polled) |
| POST | `/creator/lessons/{lid}/video/retry` | → `VideoStatus` (only from `failed` / stale) |
| POST | `/creator/lessons/{lid}/resources/token` · `/resources` · DELETE `/creator/resources/{id}` | same client-upload pattern, ≤ 20 MB |
| GET | `/creator/earnings` | `Earnings { balance_paise, available_paise, pending_paise, paid_paise, entries: LedgerEntry[], payouts: Payout[] (v2), pool: PoolLine[] (v3) }` |

### Admin 👑
| Method | Path | Body → Returns |
|---|---|---|
| GET | `/admin/dashboard?days=7\|30` | `{ revenue_paise, enrollments, new_students, pending_applications, failed_jobs, blob_bytes }` |
| GET | `/admin/creators?status=` | `CreatorProfile[]` |
| POST | `/admin/creators/{user_id}/decide` | `{ approve: bool, note? }` → `CreatorProfile` (approve sets `users.role = creator`) |
| GET | `/admin/courses?status=` | `AdminCourseRow[]` |
| POST | `/admin/courses/{id}/takedown` · `/restore` | `{ note? }` → `AdminCourseRow` |
| GET | `/admin/jobs?state=` | `JobRow[]` (course, lesson, state, attempts, error, timings) |
| POST | `/admin/jobs/{id}/retry` | → `JobRow` (re-queue + dispatch) |
| POST | `/admin/orders/{id}/refund` (v2) | → `Order` (Razorpay refund, negative entries, enrollment removed) |

### Worker ⚙ (Bearer `WORKER_SECRET`)
| Method | Path | Body → Returns |
|---|---|---|
| POST | `/internal/jobs/{id}/claim` | → `{ source_url, prefix, key_hex, iv_hex, lesson_id }` · 409 `already_claimed` · 410 `not_queued` |
| POST | `/internal/jobs/{id}/complete` | `{ manifest }` → 200 (no-op if already `ready`) |
| POST | `/internal/jobs/{id}/fail` | `{ error }` → 200 |
| GET | `/internal/jobs/next` | → the oldest `queued` job or 204 (for `--poll`) |

### Server-to-server ⚙
| Method | Path | Notes |
|---|---|---|
| POST | `/webhooks/razorpay` | `X-Razorpay-Signature` HMAC over the raw body; `webhook_events.id` unique; `payment.captured → mark_paid`, `payment.failed → failed if pending`; v2: `subscription.*` → state machine |
| POST (web) | `{WEB_URL}/api/revalidate` | `{ tags: [], secret }` — on publish / takedown / video ready / profile change |

### v2
| Method | Path | Notes |
|---|---|---|
| POST 🔒 | `/subscriptions` | → `{ razorpay_subscription_id, key_id }` · 409 `already_subscribed` |
| POST 🔒 | `/subscriptions/cancel` | → `Subscription` (cancel-at-period-end) |
| GET 🔒 | `/quizzes/{id}` · POST `/quizzes/{id}/attempts` | questions without `correct`; `{ answers: int[] }` → `Attempt { score_pct, passed, correct: int[] }` |
| 🎓 | `/creator/sections/{sid}/quiz` (PUT) · `/creator/lessons/{lid}/captions/token` · `/captions` | quiz editor; captions upload |
| POST 🎓 | `/creator/payouts` | `{ amount_paise }` → `Payout` · 422 `insufficient` / `open_request` |
| 👑 | `GET /admin/payouts` · `POST /admin/payouts/{id}/pay { reference }` · `/reject { note }` | |
| POST | `/auth/forgot` · `/auth/reset` | Resend link |

### v3
`POST 👑 /admin/pool/close { month }` → `PoolClose` · 409 `already_closed` · `GET 🎓 /creator/courses/{id}/analytics` → `{ lessons: [{ id, title, starters, completion_pct, curve: number[] (per 10-s bucket, ratio of starters), dropoffs: [{ at_s, fall_pct }] }] }` · `GET /courses?q=` full-text · key endpoint device limit (`403 too_many_devices { limit: 2 }`).

### v4
`POST 🔒 /lessons/{id}/offline-lease { device_id }` → `{ key_hex, iv_hex, expires_at, rendition: '480p', playlist: string, segments: string[] }` (requires `can_watch`; refreshes an existing lease) · `DELETE /lessons/{id}/offline-lease` · `/manifest.webmanifest` · `/sw.js` (web only).

## D. Payload shapes that matter
```ts
type CourseCard = { id: string; slug: string; title: string; subtitle: string; category: Category; level: string; price_paise: number;
                    cover: { url: string; width: number; height: number } | null; creator: { handle: string; display_name: string; avatar_url?: string };
                    lessons: number; duration_s: number; enrolled?: boolean; progress_pct?: number };
type Course = CourseCard & { description: string; status: 'published';
                    sections: { id: string; title: string; lessons: { id: string; title: string; duration_s: number; is_preview: boolean; completed?: boolean; ready: boolean }[]; quiz?: { id: string; passed?: boolean } }[];
                    certificate_code?: string };
type Play = { master_url: string; poster_url: string; resume_at: number; duration_s: number; sprite?: SpriteMeta; captions?: { lang: string; url: string }[] };
type SpriteMeta = { url: string; cols: number; rows: number; w: number; h: number; interval_s: number };
type VideoStatus = { status: 'none'|'queued'|'processing'|'ready'|'failed'; job?: { state: string; attempts: number; error?: string; claimed_at?: string; dispatch_error?: string };
                     renditions_done: string[]; poster_url?: string; duration_s?: number; source_bytes?: number };
type Manifest = { duration_s: number; width: number; height: number; iv_hex: string;
                  renditions: { name: '240p'|'480p'|'720p'; bandwidth: number; width: number; height: number; codecs: string; segments: number[] }[];
                  poster_url: string; sprite: SpriteMeta };
type CheckoutStart = { order_id: string; number: string; razorpay_order_id: string; key_id: string; amount_paise: number };
type Earnings = { balance_paise: number; available_paise: number; pending_paise: number; paid_paise: number;
                  entries: { kind: LedgerKind; amount_paise: number; note?: string; order_number?: string; period?: string; at: string }[];
                  payouts?: Payout[]; pool?: { month: string; pool_paise: number; my_seconds: number; total_seconds: number; share_pct: number; amount_paise: number }[] };
type Me = { id: string; name: string; email: string; role: 'student'|'creator'|'admin'; creator_status?: 'applied'|'approved'|'rejected' };
```
