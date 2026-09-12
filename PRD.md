# PRD — Skillroom: Online course platform

**Status:** draft v0 (basic) · to be detailed together
**Name:** Skillroom · *learn from people who do it*
**URL:** https://skillroom.virajdomadia.com
**Slot:** #5 · Budget ~35 h · Build fourth

## One-liner
Creators upload video courses; students subscribe or buy, watch with resume-where-you-left, take quizzes and earn a certificate; creators get paid out.

## Who it's for
- **Student:** learning on laptop/phone.
- **Creator:** a coach/teacher publishing courses.
- **Admin (platform):** approves creators, sees revenue, handles payouts.

## Why this project
- Three roles with real permission boundaries (RBAC) — a common interview topic.
- Video streaming + recurring billing + payouts are three things most junior portfolios never touch.
- Coaches and tutors are a big freelance market in India.

## Core features (thin vertical slice)
**Student**
- Browse courses, course page (curriculum, preview lesson, price)
- Buy a course (one-time) or subscribe to all-access (Razorpay Subscriptions)
- Player: video lessons, resume position, mark complete, progress bar per course
- Quiz at end of section; certificate PDF on completion

**Creator**
- Create course → sections → lessons; upload video (processed & streamed), attach resources
- Publish/unpublish; earnings view

**Admin**
- Approve creators, revenue overview, trigger payouts

## The wow moment
Upload a video, and a minute later it streams adaptively on a phone with your progress synced across devices; finish → certificate with your name.

## Out of scope (v1)
Live classes, comments/Q&A, coupons, drip scheduling, mobile app.

## Tech notes (to discuss)
- Video: Mux (or Cloudflare Stream) — upload → webhook → playback ID; signed playback URLs so only enrolled students can watch
- Billing: Razorpay Subscriptions for all-access + one-time Checkout for single courses; entitlement check middleware
- Payouts: Razorpay Route (or a simulated ledger + manual payout for v1)
- Certificate: server-rendered PDF (React-PDF or Satori)

## Success criteria
- A non-enrolled user can never obtain a playable video URL
- Progress resumes correctly across devices

## Open questions
- Mux free tier limits vs Cloudflare Stream — which for the demo?
- Real payouts via Route (KYC needed) vs simulated ledger for v1?
