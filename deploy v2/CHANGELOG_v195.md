# CHANGELOG v195 — Sprint 2.22.0b.115 «هيكل تحميلٍ صادق أثناء انتظار GIS» (loading skeleton screen)

**Engine:** `thammen-sprint2p22p0b115-loading-skeleton` · **SPRINT_TAG** `2.22.0b.115`
**Date:** 2026-07-07 · **Files:** `index.html` (a skeleton CSS block + the `renderLoading()` rewrite + the 2 version lines) (+ `test_sprint_2_22_0b115.py`)
**Class:** 🟢 **FRONTEND-ONLY / VALUE-INVARIANT** — the loading state only; the real result still renders via `show()`, and the loading is display-only (no fetch/body change). `api.py` + the engine untouched. **The perceived-latency half of the PO-chosen «زمن الاستجابة أولاً» direction** (b114 removed the compute hotspot; ~7s of network wait remains — this makes the wait *feel* faster).

---

## 2. Why

b114's audit left ~7s of unavoidable serial-GIS network wait (the backend parallelization is a separate Gate-2/determinism-gated sprint). During that wait the app showed a bare text spinner (`.lprog`: a rotating step line + elapsed timer + an indeterminate bar). A **skeleton screen** — a shimmering silhouette of the incoming result card — reads *faster* than a spinner (the user sees the STRUCTURE of what's coming) and matches the premium brand better than a text-only spinner. This is the cheapest, safest half of the latency direction: pure perceived-latency, value-invariant, no engine touch.

## 3. What this patch does (`index.html`)

- **Skeleton CSS** (`.skl*`): a navy hero placeholder (`var(--primary)`) with a label-line + a big value-line + a range-bar-line, a row of 3 chip placeholders, and a **shimmer sweep** (`.skl-sh` + `@keyframes skl-sweep`). **Reduced-motion fallback**: `@media(prefers-reduced-motion:reduce)` turns the shimmer + the `.lbar` animation into a static pulse.
- **`renderLoading()` rewrite**: renders the skeleton silhouette (hero + chips) ABOVE the KEPT honest narrative — the 4 real GIS steps (verify address / search MoJ / analyse location / prepare report), the elapsed timer, and a new honest line **«نفحص كلّ صفقةٍ مسجّلة» / «we check every registered sale»** (the wait is part of the accuracy — an honest statement, NOT a fake progress count; the b104 self-correction against a pre-response "live count"). Bilingual (`t()`).
- The result path is untouched: `show(data)` renders the real card, then `fRes.innerHTML=''` clears the skeleton (both unchanged).

## 4. VALUE-INVARIANT

Only the loading placeholder changed. The request body, the endpoints, `show()`, and every downstream figure are untouched; `api.py` + the engine untouched (only the 2 version lines). No headline/method/rule/leadership touched.

## 5. Verification (measured)

- Isolated `test_sprint_2_22_0b115.py` **11/11** (the skeleton CSS shapes + shimmer + reduced-motion fallback · `renderLoading` builds the `.skl` block · the honest step narrative + «نفحص كلّ صفقةٍ مسجّلة» KEPT · the 4 GIS steps unchanged · the result-render + clear path untouched · loading is display-only).
- DoD: aggregator **395/395 MATCH** · security **16/16** · surface-honesty **45/45** · broad walk **169/169 ALL GREEN** · py_compile OK · `node --check` OK. **1 R6/Lesson-2 re-point:** `test_sprint_2_22_0b107.py` pinned the old `.lprog` elapsed line `t('منذ ','')+el+t(' ثانية',' s')`; b115 merged the honest «نفحص كلّ صفقة» line into the elapsed `t()` → re-pointed to the new wording (still t()-wrapped, still shows elapsed; intent preserved, zero assertion weakened) = 21/21.
- **R14 real preview 375×812** (DOM-measured, AR + EN): `run()` → the skeleton renders — navy hero (`rgb(22,50,79)` = `--primary`) + shimmer (`skl-sweep`) + 3 lines + 3 chips + the honest step («نتحقق من العنوان في خرائط GIS…» / «Verifying the address…») + elapsed + «نفحص كلّ صفقةٍ مسجّلة» / «we check every registered sale»; **EN** renders the English steps + honest line; the reduced-motion CSS rule is present; **no horizontal overflow**; **0 console errors**.

## 6. Deployment

- Ritual: `git push origin master` FIRST, then `git subtree push --prefix "deploy v2" heroku master` (§20.112). Value-invariant → deploy-on-green.

## 7. Verification curl (post-deploy)

- `/api/health` → `3.1.0-sprint2.22.0b.115`.
- served `index.html`: `.skl-hero{background:var(--primary)` present · `skl-sweep` present · «نفحص كلّ صفقةٍ مسجّلة» present.
- the 5-fixture villa byte-gate byte-identical to v277 (frontend-only).

## 8. What's NOT in this patch

- **The backend GIS-chain parallelization (~7s network)** — the durable latency fix, Gate-2/determinism-gated (Branch-B/§20.4) → its own audited sprint with an H_det harness. This slice addresses PERCEIVED latency; that one addresses ACTUAL latency.
- A per-step progress that reflects the real backend stage (the current steps are time-based, not event-driven — honest as an approximate narrative, not a live backend trace).
