# BRIEF — Sprint 2.22.0a.18 (R9): Bracket-path area-name reconciliation

**Engine target:** `thammen-sprint2p22p0a18-area-name-reconciliation` / `3.1.0-sprint2.22.0a.18`
**Date:** 2026-06-02
**Files (CC confirm in recon):** `evaluate_property.py` (resolution + overrides + normalize), `evaluate_unified.py` (SPRINT_TAG/ENGINE_VERSION), `test_sprint_2_22_0a18.py` (new), `CHANGELOG_v70.md` (new)
**Posture:** Carried autonomously (tactical delegation). **Valuation-affecting (~12% of villa lookups)** → thorough pre-deploy validation + transparent post-deploy impact report. Honesty-positive (recovers correct comp pools; dispersion-gated). Data-reconciliation of the *existing* sales-comparison method — **not** a new methodology.

## 1. Why (authoritative sizing — CC document 8)
The bracket path resolves a subject's GIS area-name via `resolve_moj_area_name` → `_candidate_moj_names` (verbatim + «ال» drop/add + 4 hardcoded overrides), exact MoJ match, **no zone-suffix strip, no stem alias**. So a subject geocoded to «معيذر 53» keys on «معيذر 53» and can't reach the rich parent «معيذر» (392 txns) → thin/widened instead of bracket.
- **12.3% of villa txns are in MoJ areas the bracket can't exact-match.** Of these: **~11.9% rescued to the dispersion-prone widened path** (precision-degraded, disclosed) and **~0.4% truly lost** (refuse). C1→R7 coupling: rescued ≠ precise.
- **A16/Marikh:** subject geocodes to «امريخ الجنوبي»; MoJ stores «مريخ» (separate GIS district) → bracket starves → widened **4.5M over-anchor**. Stem-change, subject-direction.

## 2. The fix (extend the existing machinery — surgical)
1. **Suffix-strip → parent** in `_candidate_moj_names`: for a GIS name ending in a trailing **zone-number** suffix («معيذر 53»), also emit the bare parent stem («معيذر»). Keep the existing **"highest-count wins"** → suffixed subjects resolve to the rich parent pool → bracket. (Aggregation of bare + suffixed **deferred** — the bare parent alone is plenty.)
2. **Hamza-normalize** in `normalize`: fold أ/إ/آ → ا alongside whitespace/NBSP, so hamza variants match generically («أم بشر»↔«ام بشر»).
3. **Extend `GIS_TO_MOJ_NAME_OVERRIDES`**: add the confirmed stem-change «امريخ الجنوبي»→«مريخ» (A16). **CC completes the tail** during recon — for each remaining orphan in `_c1_gap.json` (qualifier/spelling/stem-change cases: السلطة الجديدة, الغانم العتيق, لجميليه, المطار, فريج العسيري, السد, …), geocode a representative subject → its GIS ANAME → add the GIS→MoJ override. **Flag ambiguous correspondences for my call — don't guess.**

## 3. Scope / exclusions
Bracket-path resolution only. Don't touch the geo/widened fallback (already substring-matches). No change to the comparison method, the dispersion gate, or the a17 caveat — newly-bracketing areas flow through the existing bracket → dispersion → a17/honest-range logic automatically. Aggregation deferred. Suffix-strip applies to **trailing zone-numbers only**; qualifier/spelling/stem cases go through overrides (#3).

## 4. Validation (mandatory — material valuation change; deploy ONLY if all pass)
- **Affected areas bracket with SENSIBLE values** — معيذر، نعيجة، المعمورة، ازغوى، لوسيل، مشيرب now resolve to parent and produce reasonable villa brackets. **Report before→after (method, n, value) for each.**
- **Dispersion still gates** — where the parent pool is dispersed, a14 honest-range fires (so resolving to parent can't silently over-confidently mix sub-zones).
- **A16/Marikh:** «امريخ الجنوبي» now brackets on «مريخ» (~83) → report new value vs old 4.5M-widened.
- **No regression:** الثمامة 46 (sensible even if it shifts to the richer parent pool), Abu Hamour 56/565/21, and all 6 §5 field-check anchors.
- `test_sprint_2_22_0a18.py` (≥6 cases: suffix-strip, override, hamza-norm, no-regression, fallback).
- Pre-deploy 6-item (mobile 390×844 + `findstr` **EXECUTED**, R14 discipline) + DoD re-measured + py_compile + CHANGELOG_v70 (v33/v34 style, before/after numbers).
- **If any affected area produces absurd values or a regression → STOP, do not deploy, report.**

## 5. After
- **Re-measure the a17 clean-bracket frequency** — the bracket landscape shifts once parent pools resolve; the clean/dispersed split (and which cells carry the a17 caveat) will change.
- **Impact report to Anas** (post-deploy): before/after for the affected areas + Marikh — the ~12% shift, transparently.

## 6. Deploy (Rule #43 subtree, R14 verification)
`git subtree push --prefix "deploy v2" heroku master` + `git push origin master`. Browser-UA 4-anchor smoke + `/api/health == a18`. Update CLAUDE.md §65a + Session_Log.
