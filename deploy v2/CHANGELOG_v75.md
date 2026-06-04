# CHANGELOG v75 — Sprint 2.22.0a.23 (R15): stock_strata land-median a18-aware

**Engine:** `thammen-sprint2p22p0a23-stratum-land-a18` · **SPRINT_TAG** `2.22.0a.23` ·
**api/health** `3.1.0-sprint2.22.0a.23` · **date** 2026-06-04
**Files changed:** `stock_strata.py` (area matching → a18 `area_match_key`) · `evaluate_unified.py`
(version) · `test_sprint_2_22_0a23.py` (new, 12 checks) · `CHANGELOG_v75.md`
**Class:** Gate-2 (strata-card **display** change, signed) — **HEADLINE value-invariant**; the B-1
`value_floor` is untouched. Audit: `docs/PHASE0_R15_stock_strata_a18.md`.

---

## 1. Why this matters
B-1 surfaced the land-value floor to users. Phase-0 §5 (R15) found `stock_strata`'s land reference —
shown on the strata cards next to that floor — was computed on a **narrower, ~+2-7% HIGHER** pool
because it matched areas with `_norm` (exact) and **dropped a18 zone-number siblings**, while the floor
(via `moj_reference`) is a18-pooled. Two land numbers in the same report disagreeing.

## 2. Root cause
`stock_strata.compute_land_median` matched MoJ areas with `_norm` exact (`stock_strata.py:249/256`).
Sprint 2.22.0a.18 wired `area_match_key` (zone-number-strip + hamza-fold) into `moj_reference` +
`compute_trend`, but **not** `stock_strata` — the same family as the open a12 `compute_trend`
categorizer-alignment debt.

## 3. What this patch does
- `compute_land_median` now pools areas with `moj_reference.area_match_key` (imported with a `_norm`
  fallback), EXACTLY as `build_reference` / the value_floor do → it no longer drops zone-number
  siblings. Everything else (bracket-then-widen, windows, n-floors) unchanged.
- **Refined finding (Rule #36):** the offline consistency check shows the a18 fix removes the genuine
  **sibling-drop** on the **area-wide** cases (e.g. المعمورة strata land **4,032 → 3,754**, now ≈ the
  floor 3,768) — but the **bracket-matched** anchors (بو هامور 3,875 · مريخ 3,212 · المعراض 2,607) are
  **unchanged**: their gap vs the area-level floor is **bracket-matching (Rule E4 by-design)**, NOT
  sibling-drop. So the fix closes the data bug it should and leaves E4's plot-bracket reference intact.
- **UNTOUCHED:** `valuation.amount` (headline), the B-1 `value_floor` (reads `moj_reference` directly),
  the bracket-matching logic, `api.py`, `index.html`.

## 4. Verification — empirical evidence
- **Isolated `test_sprint_2_22_0a23.py` = 12/12** (production `compute_land_median` + `area_match_key` on
  controlled fixtures): a zone-number sibling is now pooled (n 3→6, median 3,100→2,850 — moves toward the
  dropped lower sibling); hamza variants pool; an unrelated area is NOT over-merged; key ==
  `moj_reference.area_match_key`; unknown/empty → None.
- **DoD matrix:** aggregator **392** · security **15/15** · surface-honesty **45/45** · broad auto-walk
  **66/66** (was 65; +1 a23 test; clean pass; no existing stock_strata test broke).
- **Offline consistency:** المعمورة strata land **4,032 → 3,754** (≈ floor 3,768, was +7.0% → now −0.4%).
- **R14:** `index.html` + `api.py` **0-diff** (git-confirmed) — the strata card renders the same fields
  (only the median value changes), no new render → **N/A by construction**.
- **Live re-smoke v162 (browser-UA #61):** headline + `value_floor` **byte-identical** on the 4 anchors;
  المعمورة strata `land_reference` moves to ~3,754 (sibling-drop closed).

## 5. Deployment
```
cd /d "C:\Thammen\deploy v2"
git add stock_strata.py evaluate_unified.py test_sprint_2_22_0a23.py CHANGELOG_v75.md
git commit -m "Sprint 2.22.0a.23 (R15): stock_strata land-median a18-aware (display; headline value-invariant)"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 6. Verification curl (post-deploy, browser-UA #61)
```
curl -s -X POST https://thammen.qa/api/evaluate -A "Mozilla/5.0 ... Chrome/120 Safari/537.36" ^
  -H "Content-Type: application/json" -d "{\"zone\":56,\"street\":647,\"building\":6}" > out.json
findstr /C:"land_reference" out.json      ::  strata card land now a18-pooled (~3,754, was 4,032)
findstr /C:"value_floor" out.json         ::  floor + headline UNCHANGED
```

## 7. What's NOT in this patch
- The **headline value** + the B-1 **value_floor** (byte-identical — re-smoke confirms).
- **Bracket-matching** (Rule E4) — kept; the bracket-matched anchors' strata-vs-floor gap is by-design
  (plot-bracket reference vs area-level floor), NOT the sibling-drop, and is left as-is.
- The override-alias completeness (فريج العسيري etc., a18-deferred) + the a12 `compute_trend` categorizer
  alignment (same family, separate).

## 8. Gate
Gate-2 (strata-card **display** change) — signed by Anas ("go" on the R15 audit). Headline
value-invariant; Gate-1 deploy on the same consent.
