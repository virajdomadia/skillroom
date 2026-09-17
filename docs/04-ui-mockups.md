# Skillroom — UI Mockups

**Lifecycle step:** 4 of 17 (UX companion to the technical design) · **Brief locked:** 2026-09-17 · **Variants:** `mockups/direction-variants.html` (six directions × six screens, eight live motion candidates), published at https://claude.ai/artifact/JK9cTzwVjD4GrEqV36WPXi · **Chosen: C · Notebook** (Viraj, 2026-09-17)
**Pairs with:** [03-user-flows.md](03-user-flows.md) — one mockup per v1 screen (S1–S15, S19, S20) after the direction is chosen.
**Files:** `mockups/landing.html` (exists, already ported to `web/`) → `mockups/direction-variants.html` (S3 course page + S4 player + S11 studio processing + S13 admin at desktop, S1 home + S6 my learning on a 390 px phone, six directions) → `mockups/screens.html` (every v1 screen in the chosen direction) → `mockups/tracker.html` (built by `mockups/tracker-build.py`). Photos: CC from Wikimedia Commons in `mockups/img/`, credits in `mockups/img/CREDITS.md`.
**Published:** [Direction variants](https://claude.ai/artifact/JK9cTzwVjD4GrEqV36WPXi) · [Screens](https://claude.ai/artifact/U7Uy3zAL3dnPWmffQnk6fB) · [Tracker](https://claude.ai/artifact/AxgaJ1fZ6HELpWTZuBUXz6).

## Brief
**Style:** the landing set a first identity — **Onest**, paper `#F7F8F4`, moss `#3E6B48`, sage `#CFE0D2`, apricot `#F4B183`, 14 px radius — calm and craft-like. It is one candidate (A), not the answer. Course platforms live or die on two screens: **the course page** (does this feel worth ₹1,499?) and **the player** (does it get out of the way?) — plus one screen only this project has: **the studio's processing moment**, where a creator watches their upload become a stream. The variants must be genuinely different UI styles (layout DNA, type, surface, density), not chrome swaps of one system; the admin is the same system at a calmer density.

**The product is the video.** Posters must be the biggest thing on every student screen; chrome is type and rules. The player page is dark or near-dark in every direction (video needs it); everything else is free. Studio and admin are desktop.

**Real content:** the seed — six courses (wheel pottery, flatbreads, watercolour, yoga, street photography, fingerstyle guitar), six fictional Bengaluru creators with CC portraits, prices in ₹ (₹999–₹1,499, one free), 2 sections × 2 lessons each, one lesson mid-processing in the studio, a certificate for the demo student.

## Motion candidates — live in the variant page
| Candidate | What happens | Reduced-motion fallback |
|---|---|---|
| **1 · Develop** | In the studio, as the job runs, three rendition chips tick in (240p → 480p → 720p) and the poster **develops** from a blurred, desaturated frame to sharp (blur 24 → 0, saturate .2 → 1, 900 ms) when `ready`; the "Preview it" button rises under it | Chips change instantly; poster fades in |
| **2 · Resume glide** | Opening a lesson with progress: the scrub track lights from 0 to the resume point (600 ms), the playhead glides there with a slight overshoot and a "Resume at 4:12 · from your phone" toast slides up; a 3-s ring counts down to auto-play | Toast only; no glide, no auto-play |
| **3 · Curriculum draw** | On the course page, a vertical track draws down the curriculum (stroke-dashoffset, 700 ms) and each lesson row fades in as the line reaches it; completed lessons get a stroked tick | Rows appear together |
| **4 · Certificate print** | At 100 %, the certificate card feeds out from a slot (translateY, 800 ms), then the seal stamps in (scale 1.6 → 1, rotate −6° → 0) and the student's name is stroked in | Card fades in with the seal |
| **5 · Ladder** | The processing panel shows three horizontal bars — one per rendition — filling segment by segment (6-s chunks) as the worker reports; the bitrate labels count up | Bars set to their final width |
| **6 · Chapter count** | Lesson numbers render as rolling counters (01 → 02) when moving to the next lesson; section headers wipe in from a rule | Numbers change instantly |
| **7 · Spring pop** | Progress rings fill with a spring on the course card and in the sidebar when a lesson completes; the tick pops (scale .6 → 1.15 → 1) | Ring set to its value; tick appears |
| **8 · Poster scrub** | Hovering a course card scrubs the poster through four stills (the sprite) with a thin progress hairline | Static poster |

Recommendation: **1 · Develop** as the signature (it is the wow moment, and only this project has it) + **2 · Resume glide** in the player + one catalogue touch (**3** or **8**) per direction.

## Variant page (`mockups/direction-variants.html`) — six directions, six screens each
Each tab: **S3 course page** (desktop 1280, scaled) beside **S1 home** on a 390 px phone; **S4 player** (desktop) beside **S6 my learning** (phone); **S11 studio: lesson processing** (desktop) beside **S13 admin dashboard** (desktop); then a strip with the eight motion candidates live in that direction's idiom. Keys 1–6 switch tabs; every direction carries the same photos and copy.

| Direction | Style (layout DNA · surface · type) | Demonstrates |
|---|---|---|
| **A · Workshop** | The landing's craft-school system: paper, moss, sage, apricot; Onest; 14 px radius; soft cards; poster-left / sticky buy card; sidebar player | Develop + Curriculum draw |
| **B · Screening room** | Near-black, warm white, amber; Sora headings; full-bleed posters with gradients; browse as horizontal rails; course page as a backdrop with an episode list; the player is the page | Resume glide + Poster scrub |
| **C · Notebook** | Ruled paper with a red margin, ink, highlighter yellow; Fraunces headings, Caveat annotations; index-card sections; curriculum as a table of contents with dotted leaders; the video sits on the page with a notes column | Curriculum draw + Certificate print |
| **D · Blueprint** | Blueprint blue on drafting paper with a grid; Space Grotesk + JetBrains Mono; dimension lines, corner marks, dense data; the pipeline is a drawn diagram; player with segment ticks | Ladder + Chapter count |
| **E · Journal** | Editorial magazine: off-white, black, oxblood; Instrument Serif headings at 72 px, numbered chapters, thin rules, pull quotes, generous whitespace; browse as an editorial list; player in reading mode | Chapter count + Certificate print |
| **F · Playground** | Bright and chunky: cream, cobalt, tangerine, lime; Bricolage Grotesque; 24 px radius, 2 px borders, stickers, progress rings, streaks; bento tiles | Spring pop + Develop |

`prefers-reduced-motion` respected in all.

## Chosen direction — C · Notebook (locked 2026-09-17)
**Idea:** the course is a notebook you are keeping. Ruled paper with a red margin, a Fraunces heading like a chapter title, Caveat handwriting for the things a person would write (annotations, "continue →", section names), photos and the video *taped* onto the page, the price on a sticky note, the curriculum as a table of contents with dotted leaders. Progress is a highlighter mark; state is a rubber stamp. The studio and admin are the same notebook at a tidier density — ledger rules, index cards, stamps for status. Nothing floats; everything is on the page.

### Tokens (→ `web/src/app/globals.css`)
| Token | Value | Use |
|---|---|---|
| `--paper` / `--panel` / `--tile` | `#FBF9F3` / `#FFFFFF` / `#EFEBE0` | page ground (with the rule) / cards, taped photos, index cards / image placeholders |
| `--rule` · rule pitch | `#D9E3EC` · `28px` | `repeating-linear-gradient(transparent 0 27px, var(--rule) 27px 28px)` on the page; body line-height 28 px so text sits on the lines |
| `--margin` | `#E0655F` | the 2 px red margin line, handwriting accents, stamps, destructive |
| `--ink` / `--ink2` / `--muted` | `#1C2833` / `#3E4A55` / `#7A8590` | text / secondary / labels (≥ 4.5:1 on paper) |
| `--line` | `#CBD6E0` | hairlines, dotted leaders, index-card borders |
| `--hl` · `--sticky` | `#FFE86B` · `#FFF3A3` | highlighter (selected, current lesson, chips) · sticky notes (price, resume toast, publish checklist) |
| `--pen` | `#2B3A8C` | blue-pen notes (student notes, annotations) |
| `--video` | `#0E141A` | the video surface; the player page stays on paper around it |
| radii | 0–4 px (paper), 3 px stamps, 44 px phone | nothing rounded beyond a photo corner |
| type | **Fraunces** 600 (`opsz` 144 for h1 ≥ 44 px, 96 below) · **Onest** 400–700 body at 15–16 px / 28 px · **Caveat** 500–600 at 18–24 px for handwriting · tabular numerals for durations, prices, codes | `next/font/google`, `display: swap` |
| grid | course page 1fr / 330 px; player 1fr / 320 px notes; studio 200 px / 1fr; phone: one column with the margin at 36 px | |

### Motion (all with `prefers-reduced-motion` fallbacks)
| Moment | Spec | Reduced |
|---|---|---|
| **Develop + Stamp (signature, studio S11)** | rendition chips tick 240p → 480p → 720p (each 800 ms, dot blinks while running); on `ready` the poster develops from blur 22 px / saturate .2 to sharp over 900 ms `cubic-bezier(.2,.7,.2,1)`, the red rubber stamp flips from *processing* to *ready* with a 2-frame overshoot (scale 1.4 → 1, rotate −8°), "Preview it" rises 10 px | chips set, poster fades in, stamp swaps text |
| Curriculum draw (S3, S1) | the margin-side track draws down 800 ms; rows rise in with 150 ms stagger; completed ticks are stroked (dashoffset 20 → 0, 400 ms) | rows visible, ticks drawn |
| Resume glide (S4) | scrub track lights to the resume point 600 ms, the head glides with overshoot; the toast is a **sticky note** sliding up from the controls with a 3-s countdown ring | note only, no auto-seek |
| Certificate print (S7, S6) | the certificate feeds up out of a slot 800 ms, the seal stamps at 900 ms (`cubic-bezier(.2,1.4,.4,1)`), the name underlines with a red pen stroke | static with the seal |
| Taped-in entrance | photos and the video enter rotated −2° → −1° / 0° with a 300 ms settle; tape strips are static | none |
| Highlighter | selecting a tab / chip / current lesson paints a highlighter band left → right 200 ms | instant |
| Stamps for state | published / draft / takedown / failed are stamps, rotated −8°, no animation — a state, not an event | — |

### Browser surfaces
`::selection` highlighter yellow with ink · scrollbar: paper track, ink thumb, 10 px, square · focus ring 3 px `--margin`, offset 2 px · `caret-color` pen blue · `theme-color` `#FBF9F3` · favicon = the mark with a red margin stroke.

## Screens (`mockups/screens.html`)
Every v1 screen from the screen index in Notebook plus S20 states: S1 home (desktop + phone), S2 browse, S3 course page, S4 player (desktop + phone, resume moment), S5 buy sheet, S6 my learning (desktop + phone), S7 certificate + verify, S8 sign in / apply with the three demo cards, S9 studio courses, S10 course editor, S11 lesson + video (upload → processing → ready, and failed), S12 earnings, S13 admin dashboard, S14 admin creators, S15 admin courses + jobs, S19 creator page, S20 states (not enrolled, processing, takedown 404, empty). Published at https://claude.ai/artifact/U7Uy3zAL3dnPWmffQnk6fB. **Step 4 complete.**
