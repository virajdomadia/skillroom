# Skillroom

**Learn from people who do it.** A complete course platform with three sides — students who buy or subscribe, watch with resume-across-devices, pass quizzes and earn a certificate; creators who upload video and get paid; a platform admin — on our own video stack: upload → an ffmpeg worker → encrypted adaptive HLS → a key server that only answers for enrolled students.

> Status: lifecycle steps 1–7 complete (2026-09-17) — see [PRD.md](PRD.md), [docs/](docs/), the [tracker](https://claude.ai/artifact/AxgaJ1fZ6HELpWTZuBUXz6) and the [screens](https://claude.ai/artifact/U7Uy3zAL3dnPWmffQnk6fB) (direction C · Notebook). Next: step 8 Project Setup, after Offcut. One of six portfolio projects by [Viraj Domadia](https://virajdomadia.vercel.app). **Live (landing page):** https://skillroom-viraj.vercel.app — will move to `skillroom.virajdomadia.com` later.

## What it proves
Owned video pipeline (ffmpeg worker on free compute → HLS ladder → AES-128 segments → API key server as the authorization boundary) · resume across devices · three-role RBAC · Razorpay one-off purchase (v1) and subscriptions (v2) · a creator ledger that splits the subscription pool by minutes watched (v3) · offline lessons under a key lease (v4)

## Stack
Next.js (App Router) · TypeScript · Tailwind CSS 4 · hls.js · FastAPI · PostgreSQL (Neon) · Vercel Blob · ffmpeg (worker on GitHub Actions) · Razorpay · fpdf2 · Resend (v2) · pytest · Vercel

## In this repo
```
web/        Next.js 15 (App Router, TypeScript, Tailwind 4) — the landing page lives here
  src/app/            layout.tsx, page.tsx, globals.css
  src/components/     landing/ (one component per section), ui/
  src/lib/
api/        FastAPI backend — folder structure only until the build starts
  app/core · routers · models · schemas · services · worker (transcode.py, runs on Actions)
  tests/
PRD.md      product requirements v1 — locked decisions + versions table
docs/       03 requirements · 03 user flows · 04 technical design · 04 ui mockups · 05 architecture · 06 data + API · 07 plan
mockups/    landing.html (ported to web/) · direction-variants.html · screens.html · tracker.html (built by tracker-build.py) · img/ (CC photos, CREDITS.md)
brand/      logo, mark and favicon
```

### Run the landing page
```
cd web
pnpm install
pnpm dev
```

## Roadmap
v1 **Classroom** (≈ 16 h) → v2 **All-access** (≈ 11 h) → v3 **Royalties** (≈ 8 h) → v4 **Offline lessons** (≈ 3 h, the unique free feature) — rows, estimates and the add-on bucket in [docs/07-plan.md](docs/07-plan.md).
