# BRIEF — Sprints 2.22.0b.15 / b.16 — DESIGN v4 screens 4–5: polished result + full report (+ DEF-12)

> **Gate-2: SIGNED BY DELEGATION («افعل الأصوب», Anas, 2026-06-10).** Gate-1: deploy-on-green per slice.
> **VALUE-INVARIANT** — display/layout/copy only; amounts/ranges/methods/floors byte-identical on the 4 anchors + V001
> (numeric contract identical to b14 §4; text/layout diffs expected BY DESIGN and listed per slice).
> **Authority:** `DESIGN_2p2x_v4_owner_journey.md` (the locked five-screen journey; screens 1–3 shipped b2.1/b2.2/b2.3)
> + `thammen_owner_flow_mockup.html` (reference mockup, NOT a spec — Phase-0 reconciles) + b14 (coherence prerequisite ✅)
> + DEF-12 (§11 Q4 multi-AI verdict "ship" — scheduled with the screen-5 report build).
> **Two slices, two deploys (marathon lesson — single purpose each):** b15 = screen 4 · b16 = screen 5 + DEF-12.
> **Baseline:** b14/v183. **STANDING HALT** on any premise break.

## §1 — Why now
Screens 1–3 (identify → confirm → improve) shipped; b14 made the result's voice coherent. What the owner journey still
lacks: a **polished result** (screen 4 — today's results card is a long undifferentiated stack of ~12 panels) and a
**shareable report** (screen 5 — today's print view is the raw stack; the Marikh PDF showed it). Screen 5 is also the
**D-3 instrument**: the artifact Anas hands valuers/brokers to collect GT.

## §2 — SLICE b15 — Screen 4: the polished result (progressive disclosure)
Principles (v4 + §2c): the number arrives as a **range that refines**; drama attaches to evidence quality, never the figure;
**explanation ≠ confidence**; staged authority (low → rises only with accountability).
1. **Hierarchy (3 tiers):** TIER-1 always visible — range headline (b3) + status label + MUC chip + the «ليس تقييماً
   معتمداً» line + evidence-quality summary (the b2.2 four-axis verdict as one row). TIER-2 collapsed-by-default
   accordions — decomposition (b14 narrative), strata, 10-Year, property-basis (b9), cap-rate panel. TIER-3 — the
   refine CTA («حسّن التقدير» with the b13 age nudge) + the report CTA («التقرير الكامل» → screen 5).
2. **No information loss:** every panel that renders today remains reachable (accordion), none deleted.
3. **Audience split respected:** buyer/owner sections keep their gating; no new authority language.
4. Mobile-first 390×844; accordions keyboard/touch accessible; zero new JS libraries (vanilla, existing patterns).

## §3 — SLICE b16 — Screen 5: the full report (+ DEF-12)
1. **Structure (print + share):** cover header (logo, date, version, PIN/address, MoJ staleness banner) → MUC/RICS
   banner → headline range + status → evidence quality → decomposition + 10-Year + strata (b14-coherent order:
   the three speak in sequence, cross-lines intact) → property basis (b9) + footprint (b10) → methodology &
   sources (CC BY 4.0 attribution a25) → buyer/owner section per audience → footer («تقدير سوقي آلي وليس
   تقييماً معتمداً» + engine version + timestamp).
2. **DEF-12 — two-values display:** Market Value (the headline range) + **Forced-Sale indication = MV × 0.90**,
   labelled «قيمة بيع جبري إرشادية (عُرف سوقي ×0.90) — ليست تقييم تصفية معتمداً» — report-only (NOT screen 4),
   convention disclosed, no engine change (display math on the existing amount).
3. **Print fidelity:** A4 print CSS (the current PDF artifacts — cut cards, orphan headers — fixed); RTL intact;
   browser print = the share path (no server-side PDF in this slice).
4. **GT hook:** one final line in the report footer: «هل لديك سعر بيع فعليّ لهذا العقار أو تقييم معتمد؟ شاركه
   لتحسين الدقّة» + the contact route Anas names (Phase-0 asks; default = the existing feedback surface, dormant-safe).

## §4 — Phase-0 recon FIRST (per slice)
b15: inventory today's results-card panel order/IDs; map each to TIER-1/2/3; flag anything whose collapse could
hide a legally-required disclosure (MUC, consent, attribution — these STAY tier-1). b16: inventory the print path +
the PDF defects (from the Marikh PDF: card splits, the buyer empty-state pre-b14); confirm DEF-12 placement;
deliver `PHASE0_b15.md` / `PHASE0_b16.md`. **HALT** if any tier demotion would hide a compliance surface.

## §5 — DoD (per slice, EXECUTED)
py_compile + node --check (inline JS) · isolated tests (b15 ≥12: tier mapping, no-panel-lost, disclosure-stays-tier-1;
b16 ≥12: report order, DEF-12 math/label, footer/attribution presence) · aggregator/security/surface + broad
(83 baseline) · local E2E: 4 anchors + V001 numeric-identical · **R14 Chromium 390×844 MANDATORY both slices**
(accordions function, 0 console errors, no overflow; b16 adds a print-emulation render A4) · live smoke post-deploy ·
`heroku auth:whoami` pre-push · CHANGELOG_v98/v99 · Session_Log §20.49/§20.50 · ENGINE_VERSION b15/b16.

## §6 — NOT in scope
Any value/method change · B-2 · server-side PDF generation · email/sharing infrastructure · apartment surfaces ·
screen 1–3 redesign (only the result/report).
