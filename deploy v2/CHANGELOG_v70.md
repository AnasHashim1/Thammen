# CHANGELOG v70 — Sprint 2.22.0a.18 (R9): Bracket-path area-name reconciliation (sibling aggregation)

**Engine:** `thammen-sprint2p22p0a18-area-name-reconciliation` · api/health `3.1.0-sprint2.22.0a.18`
**Date:** 2026-06-03
**Files:** `evaluate_property.py` (resolution + overrides), `moj_reference.py` (pooling key + 2 area filters), `evaluate_unified.py` (ENGINE_VERSION/SPRINT_TAG), `test_sprint_2_22_0a18.py` (new, 28 checks), `docs/BRIEF_R9_area_name_reconciliation.md` (signed brief, persisted)
**Type:** VALUATION-AFFECTING — comparable-pool *selection* (the data-reconciliation of the existing Sales-Comparison method; not a new methodology). Honesty-positive (recovers correct, recent pools; dispersion-gated). `api.py` UNTOUCHED (version auto-derives from `SPRINT_TAG`).

---

## 1. Why this matters

A subject's GIS district name is matched to a MoJ area-name to build its bracket comparables. The matcher only did verbatim / «ال» drop-add / 4 overrides — **no zone-number handling**. But MoJ files the same district under several labels: a bare parent (`معيذر`) **and** zone-numbered siblings (`معيذر 53`, `معيذر 55`). So **~12% of villa lookups** keyed on one label and missed the rest of the district, and the A16/Marikh case (`امريخ الجنوبي`) starved into the dispersion-prone widened path → a 4.5M over-anchor.

## 2. Root cause (measured — and it inverted the brief's first plan)

The signed brief proposed FIX#1 = strip the trailing zone-number to the bare parent + keep "highest-transaction-count wins". **Pre-deploy validation tripped the الثمامة 46 hard gate and showed why that is wrong:** MoJ records **recent** transactions under the *sub-zone* label and **stale** ones under the *bare parent*. So "highest-total-count → bare parent" sends the subject **from recent data to stale data**:

| sub-zone (a17 live) | highest-count→bare-parent (rejected) |
|---|---|
| الثمامة 46 400-600: n=63, **n24=63** (recent), gated | n=18, **n24=0** (all stale), **−7.5%**, ungated ← hard gate trip |
| معيذر 53 400-600: n=32 recent, gated | n=24, n24=1, **−20%** |
| ازغوى 51 600-900: n=8 recent | n=2, n24=0, **−40%** |

These sub-zones were never starved — they bracket reliably today. Highest-count-wins **regressed** them. (Full finding: Session_Log §20.18.)

## 3. What this patch does — sibling AGGREGATION (the correct fix; PO «افعل الأصوب»)

Pool the bare district **and** all its zone-numbered siblings into ONE area, instead of choosing one label. The zone-number after a district name is a Qatari *addressing* artifact, not a distinct market — so the aggregate recovers **both** the recent sub-zone data and the historical parent data (max n + recency).

- **`moj_reference.area_match_key(s)`** (new) = `normalize_area_name` (whitespace/NBSP collapse + hamza fold أ/إ/آ→ا) then strip a **trailing zone-number**. «معيذر», «معيذر 53», «معيذر 55» → one key «معيذر».
- **`build_reference` + `compute_trend`** area filters now match on `area_match_key` (was exact). The `categorize` TYPE path (`'أرض فضاء'`) stays on the bare, UNFOLDED `normalize` (must not fold the literal).
- **`resolve_moj_area_name`** tallies + matches by `area_match_key`, returns `(district_key, aggregate_count)` — exactly the pool `build_reference` then builds.
- **Overrides** (`GIS_TO_MOJ_NAME_OVERRIDES`) keep the stem/spelling cases aggregation can't bridge: **A16 `امريخ الجنوبي`→`مريخ`**, `جزيرة اللؤلؤة`→`اللؤلؤة`, `اسلطة الجديدة`→`السلطة الجديدة`, `لجمليه`→`لجميليه`, plus the originals. **`المطار العتيق`→`المطار` DROPPED** (inert/mis-directed: `المطار العتيق` is itself a rich 567-txn MoJ area).
- **Hamza fold** is collision-free (0 distinct MoJ area-names merge). **Sibling aggregation** is over-merge-safe: across all 161 MoJ area-names, every multi-name collapse (15 districts) is a pure zone-number variant of ONE district — **0 distinct districts merged**.

Downstream valuation logic is unchanged: newly-correct pools flow through the existing bracket → a14 dispersion gate → a17 caveat automatically.

## 4. Verification — empirical evidence

**Isolated** `test_sprint_2_22_0a18.py`: **28/28** (area_match_key aggregation+hamza+NBSP+distinct-safe; override routing incl. A16; **negative-assert لجميل≠لجميليه**; categorize stays unfolded; dispersion gate fires on the aggregate; real-CSV: معيذر 53→معيذر n≥700, بو هامور unchanged, لجميل→None).

**DoD:** aggregator **392** · security **15** · surface-honesty **45** · broad **61** (60→61, the new test).

**Hard gate الثمامة 46 (PASS):** 400-600 (common) = n=63→**n=87, n24=87, +3.7%, GATED**. Comprehensive sweep of ALL 15 sibling districts × every sibling label × bracket = **0 silent clean-bracket regressions** (large moves like نعيجة −20% are all dispersion-GATED → honest-range fires).

**Anchors (no-regression):** Abu Hamour 56/565/21 `بو هامور` has no siblings → **2,400,000 UNCHANGED**; المعراض, اللقطة (apt refusal) unchanged. **Marikh 54/541/6** widened **4.5M → مريخ bracket** (n=13, n24=13, 5.1M, disp 0.165 + a17 condition caveat) — the A16 fix, a true same-district recent pool. **Maamoura 56/647/6** widened 3.8M → **gated** المعمورة bracket (n=7, 3.8M).

## 5. Deployment

```
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 6. Verification curl (post-deploy)

```
curl -s -A "Mozilla/5.0 ... Chrome/120 Safari/537.36" https://thammen.qa/api/health
curl -s -A "Mozilla/5.0 ... Chrome/120 Safari/537.36" -X POST https://thammen.qa/api/evaluate -H "Content-Type: application/json" -d "{\"zone\":54,\"street\":541,\"building\":6}"
```
Expect: health `…a18`; 54/541/6 resolves on `مريخ` (was widened 4.5M); 56/565/21 = 2,400,000 unchanged.

## 7. What's NOT in this patch

- **No aggregation of cross-spelling districts** beyond the explicit overrides (only zone-number siblings auto-pool).
- **`فريج العسيري` (26 villa txns) DEFERRED** — no GIS ANAME contains «العسيري»; unrecoverable this sprint (~0.25% of villa lookups remain on widened/refuse). The thin `المطار` (12) label is similarly unreached.
- **No condition / built-type fix** — Marikh's R7 over-anchor (condition) is Sprint B; a18 only fixes WHICH pool, and the a17 caveat discloses the condition gap on the clean Marikh bracket.
- **LAND pool unchanged in spirit** — `area_match_key` applies to the shared area filter (helps land too), but no land-specific logic changed.
- **`api.py` / `index.html` untouched** — backend resolution only; mobile 390×844 unaffected (git-confirmed no `index.html` change).
