# Skillroom — User Flows & Screen Index

**Lifecycle step:** 3 of 17 · **Locked:** 2026-09-17 · Pairs with [03-requirements.md](03-requirements.md); every screen below gets a mockup in [04-ui-mockups.md](04-ui-mockups.md).

## Flow 1 — Browse to watching (v1, the main path)

```mermaid
flowchart LR
  H[S1 Home] --> B[S2 Browse · category]
  H --> C[S3 Course page]
  B --> C
  C -->|preview lesson| P[S4 Player · preview]
  C -->|Buy| K[S5 Buy sheet → Razorpay modal]
  K -->|verify HMAC · mark_paid| C2[S3 Course page · Enrolled]
  C -->|Enrol free| C2
  C2 -->|Start / Continue| P2[S4 Player · resume]
  P2 -->|last lesson complete| CE[S7 Certificate]
  P2 --> ME[S6 My learning]
```

## Flow 2 — Video: upload → worker → playable (v1, the hard part)

```mermaid
sequenceDiagram
  participant CR as Creator (studio)
  participant BL as Vercel Blob
  participant API as FastAPI
  participant GH as GitHub Actions
  participant W as Worker (transcode.py)
  CR->>API: POST /creator/lessons/{id}/video/token
  API-->>CR: client upload token (path video-src/{lesson}/…)
  CR->>BL: PUT source (client upload, ≤ 500 MB)
  CR->>API: POST /creator/lessons/{id}/video {url, size}
  API->>API: videos row (key generated) · video_jobs queued
  API->>GH: repository_dispatch transcode {job_id}
  CR->>API: GET /creator/lessons/{id}/video (poll 3 s)
  GH->>W: run python -m app.worker.transcode --job
  W->>API: POST /internal/jobs/{id}/claim → source url, key, prefix
  W->>BL: GET source
  W->>W: ffmpeg → 240/480/720p HLS · AES-128 · poster · sprite
  W->>BL: PUT video/{prefix}/{rendition}_%03d.ts · poster.jpg · sprite.jpg
  W->>API: POST /internal/jobs/{id}/complete {manifest}
  API->>API: videos.status ready · lesson duration · course cover
  API-->>CR: status ready (poll) → "Preview it"
```

## Flow 3 — Playback and the key server (v1)

```mermaid
sequenceDiagram
  participant S as Student (player)
  participant API as FastAPI
  participant BL as Blob CDN
  S->>API: POST /lessons/{id}/play
  API->>API: can_watch(user, lesson)? → token t = HMAC(user, lesson, exp 1h)
  API-->>S: {master_url?t, poster, resume_at, duration}
  S->>API: GET /stream/{lesson}/master.m3u8?t
  API-->>S: 3 renditions → /stream/{lesson}/{r}.m3u8?t
  S->>API: GET /stream/{lesson}/480p.m3u8?t
  API-->>S: #EXT-X-KEY URI=/stream/{lesson}/key?t · segments → Blob URLs
  S->>API: GET /stream/{lesson}/key?t
  API->>API: verify t · can_watch again · (v3: device count ≤ 2)
  API-->>S: 16 bytes · no-store
  S->>BL: GET video/{prefix}/480p_000.ts (ciphertext)
  S->>S: hls.js decrypts · plays · switches rendition on bandwidth
  loop every 10 s / pause / seek / unload
    S->>API: POST /lessons/{id}/progress {position_s, watched_delta_s}
  end
```

## Flow 4 — Video job state machine (v1)

```mermaid
stateDiagram-v2
  [*] --> queued: POST /creator/lessons/{id}/video
  queued --> processing: worker claim (attempts + 1)
  processing --> ready: complete {manifest}
  processing --> failed: fail {error} · or claim older than 20 min (stale)
  failed --> queued: admin / creator retry → re-dispatch
  ready --> queued: creator re-uploads (new prefix; old deleted when ready)
```

## Flow 5 — Buy → enrol → ledger (v1) and refund (v2)

```mermaid
stateDiagram-v2
  [*] --> pending_payment: POST /checkout {course}
  pending_payment --> paid: verify or webhook payment.captured → mark_paid()
  pending_payment --> expired: 30 min lazy
  pending_payment --> failed: payment.failed
  paid --> refunded: admin refund (v2) → negative sale + fee entries, enrollment revoked
  note right of paid
    mark_paid(): order paid · enrollment(source purchase) ·
    ledger sale +80% creator · fee +20% platform — one transaction, idempotent
  end note
```

## Flow 6 — Creator lifecycle (v1) and payouts (v2)

```mermaid
flowchart LR
  A[S8 Apply] -->|creator_profiles applied| AD[S14 Admin · creators]
  AD -->|approve → role creator| ST[S9 Studio · courses]
  AD -->|reject + note| A
  ST --> ED[S10 Course editor · sections · lessons]
  ED --> LS[S11 Lesson · upload · job status]
  LS -->|ready| ED
  ED -->|publish · ≥ 1 ready lesson| PUB[Published → S2 Browse]
  subgraph v2 payouts
    EA[S12 Earnings] -->|Request payout ≥ ₹500| PO[S16 Admin · payouts]
    PO -->|mark paid + reference| EA
  end
```

## Flow 7 — Subscription state machine (v2)

```mermaid
stateDiagram-v2
  [*] --> created: POST /subscriptions
  created --> authenticated: webhook subscription.authenticated
  authenticated --> active: subscription.activated / charged (current_end set)
  active --> active: subscription.charged (current_end rolls)
  active --> halted: subscription.halted (charge failed) — 3-day grace keeps access
  halted --> active: subscription.charged
  halted --> cancelled: subscription.cancelled
  active --> cancelled: user cancel-at-period-end (access until current_end) / webhook cancelled
  active --> completed: subscription.completed
  cancelled --> [*]
```

## Flow 8 — Offline lesson (v4)

```mermaid
flowchart LR
  P[S4 Player · Download] -->|GET 480p playlist + segments| CS[(Cache Storage offline/lesson)]
  P -->|POST /lessons/id/offline-lease · can_watch| L[(IndexedDB · key + lease 48 h)]
  OFF[Offline · airplane mode] --> LD[hls.js custom loader → cache + IDB]
  LD -->|lease valid| PLAY[Plays]
  LD -->|lease expired| REN[Reconnect to renew]
  PLAY -->|progress queued| Q[(IDB queue)]
  Q -->|back online| API[POST /lessons/id/progress · lease refresh]
```

## Screen index

| # | Screen | Route | Who | Version | Notes |
|---|---|---|---|---|---|
| S1 | Home | `/` | all | v1 · Continue watching in v2 | Exists as landing; becomes the catalogue home (hero, categories, new courses, free to start, creators) |
| S2 | Browse | `/courses`, `/courses?category=` | all | v1 · search in v3 | Course cards, category chips |
| S3 | Course page | `/c/[slug]` | all | v1 | Poster, curriculum with preview badges and ticks, creator card, Buy / Enrol free / Continue |
| S4 | Player | `/learn/[slug]/[lesson]` | student | v1 · captions + scrubbing in v2 · quiz link in v2 · Download in v4 | hls.js, sidebar curriculum, resources, **Resume** moment, mark complete |
| S5 | Buy sheet | `/c/[slug]` (sheet) → Razorpay modal → back | student | v1 | Price, what you get, Pay; dismissed state |
| S6 | My learning | `/me` | student | v1 · subscription card in v2 · downloads in v4 | Enrolled courses with progress, certificates, account |
| S7 | Certificate + Verify | `/certificates/[code]`, `/verify/[code]` | student / public | v1 | PDF view + download; public verify page |
| S8 | Sign in / up + Apply | `/sign-in`, `/sign-up`, `/apply` | all | v1 | Demo buttons (student, creator, admin); creator application form + status |
| S9 | Studio: courses | `/studio` | creator | v1 | Course list with status, lessons ready ⁄ total, enrollments, revenue |
| S10 | Studio: course editor | `/studio/courses/[id]` | creator | v1 · quiz editor in v2 · analytics tab in v3 | Details, sections → lessons with video state, publish checklist |
| S11 | Studio: lesson + video | `/studio/courses/[id]/lessons/[lid]` | creator | v1 · captions in v2 | Drop zone, upload bar, **job status (queued → processing → ready)**, poster, resources |
| S12 | Studio: earnings | `/studio/earnings` | creator | v1 (read) · payouts in v2 · pool math in v3 | Balance, entries, request payout |
| S13 | Admin: dashboard | `/admin` | admin | v1 | Revenue, enrollments, pending applications, failed jobs |
| S14 | Admin: creators | `/admin/creators` | admin | v1 | Applications approve / reject; creator list |
| S15 | Admin: courses + jobs | `/admin/courses`, `/admin/jobs` | admin | v1 | Takedown / restore; jobs by state with retry and error text |
| S16 | Admin: payouts | `/admin/payouts` | admin | v2 | Requested → paid (reference) / rejected |
| S17 | Quiz | `/learn/[slug]/quiz/[id]` | student | v2 | Questions, submit, score, retry |
| S18 | All-access | `/all-access` | all | v2 | ₹499 / month, subscribe, manage from `/me` |
| S19 | Creator page | `/u/[handle]` | all | v1 | Portrait, bio, area, published courses |
| S20 | States | various | all | v1 · offline in v4 | Not enrolled (preview only), video processing, video failed, takedown 404, expired lease / offline |
