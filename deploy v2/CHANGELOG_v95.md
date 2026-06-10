# CHANGELOG v95 — Sprint 2.22.0b.12 (Bug A15: HBU not-evaluated → explicit disclosure)

**Engine:** `thammen-sprint2p22p0b12-hbu-disclosure` · **api-health:** `3.1.0-sprint2.22.0b.12`
**Date:** 2026-06-10 · **Files:** `evaluate_unified.py` (+predicate/constants/emission/version), `index.html` (+1 render), `test_sprint_2_22_0b12.py` (new)
**Class:** Gate-2 (adds a user-facing disclosure field) — **DISCLOSURE-ONLY / VALUE-INVARIANT** (4 anchors byte-identical). Brief signed in-message. Closes **Bug A15**.

## 1 — Why this matters
HBU (Highest-and-Best-Use, RICS VPS 2 / IVS 102 — a villa's rezoning option value) is computed only when a zoning code is available. When the **zoning layer is unavailable** (QARS / zoning-layer degradation), the HBU block is **silently skipped** and the user-facing `hbu_analysis` simply doesn't appear — **indistinguishable from "HBU evaluated, no upside."** Two materially different RICS disclosures are conflated. This is the catalogued **Bug A15** (Medium, §20.5), reachable in production under zoning degradation.

## 2 — Root cause
- `geometric_factors.py:638` — `_run_hbu()` returns `analyze_adjacent_zoning(...)` **only if `current_zoning_code`** is truthy; else `None`, and `result['hbu']` is then **never set** (`:654`).
- Consumer `evaluate_unified.py` (`geo_section`) builds `hbu_analysis` only when `hbu.get('hbu_potential') or hbu.get('industrial_adjacency')` — which is False both when zoning is **absent** (`hbu = {}`) AND when zoning is present but there's **no potential**. The user cannot tell "not evaluated" from "no upside."

## 3 — What this patch does
- **New pure predicate** `_hbu_note_applies(primary, gate, asset_type, amount, zoning_code)` (next to its sibling `_condition_note_applies`): returns True iff `zoning_code is None` (zoning factor unresolved → HBU skipped) **AND** the villa/house surface gate `_condition_note_applies(...)` holds (reusing its scope + None/malformed-gate fail-safe-to-disclosure). `zoning_code` present ⇒ False (HBU *was* evaluated).
- **Verbatim constants** `_HBU_NOTE_AR` = «لم يتسنَّ تحديد فرضية الاستخدام الأفضل لهذه القطعة (طبقة التنظيم غير متاحة)» + `_HBU_NOTE_EN` twin.
- **Emission** (co-located with the B-1 `value_floor`, in its own error-swallowing try): when the predicate holds, set `valuation.hbu_note_ar` + `hbu_note_en`. The zoning signal = the pure, no-GIS `_extract_zoning_code(ev)` (the same reader the HBU gate's hint derives from). Never touches amount / range / method.
- **Frontend** (`index.html`): one muted `.rn` div rendered directly under the `value_floor` block — `if(v.hbu_note_ar){…}` (reuses the a17/a21-proven class).
- **Scope:** villa/house only (via `_condition_note_applies`); land / apartment / tower / commercial / refusal → no note. Dispersion-**gated** surfaces (a10/a14) are excluded — their honest-range already discloses condition (the note rides value_floor's gate for one coherent surface).
- **Version** bumped → b12.

## 4 — Verification (empirical)
- py_compile OK. Isolated `test_sprint_2_22_0b12.py` **26/26** (production helpers — `_extract_zoning_code` parse + None; predicate: absent-zoning fires / present-zoning no-note / land+apt+tower+commercial N/A / house+villa aliases / amount-None / refusal-method / **malformed-gate fail-safe** / dispersed-gated excluded / zoning-present-overrides / parity with `_condition_note_applies` / verbatim AR + EN twin + AR-no-Latin).
- DoD: aggregator **392** (ALL COUNTS MATCH) · security **15/15** · surface-honesty **45/45** · broad auto-walk **81/81** (80→81, clean, 247.7s, no flake).
- **Local E2E (real engine, live GIS):** 4 anchors **byte-identical** (56/565/21 2.4M comparison_bracket · 54/541/6 5.4M comparison_thin · 55/296/13 2.6M · 52/903/90 None refusal) + **hbu_note ABSENT** (zoning present). **Zoning-absent simulation** (patch `_extract_zoning_code`→None on 56/565/21): **amount stays 2,400,000** (value-invariant) + **hbu_note FIRED** verbatim → proves the emission wires through the real `_build_unified_output` path AND is value-invariant when the note fires.
- **R14 real-Chromium 390×844** (node absent → Chromium is the JS gate, EXECUTED): real-payload `show()` render — hbu `.rn` renders verbatim, visible, right-edge **350 < 390**, scrollW==clientW (no internal overflow), **document no horizontal overflow** (390==390), **0 console errors**.

## 5 — Deployment
```
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 6 — Verification curl (post-deploy)
```
curl -s -A "Mozilla/5.0 ... Chrome/120 Safari/537.36" -X POST https://thammen.qa/api/evaluate ^
  -H "Content-Type: application/json" -d "{\"zone\":56,\"street\":565,\"building\":21}"
:: expect amount 2,400,000, NO hbu_note_ar (zoning present) — byte-identical to b11
curl -s https://thammen.qa/api/health   :: expect 3.1.0-sprint2.22.0b.12
```

## 7 — What's NOT in this patch
- **No valuation logic** — disclosure-only; amount/range/method/MUC/decomposition untouched. The HBU *value* contribution path (VPS 2 uplift) is unchanged.
- **The note does not self-fetch the subject zone** (Option B, §20.5) — that would change output + add a GIS call. We disclose the absence, we don't fix the data.
- **Dispersion-gated (a10/a14) villa surfaces** keep their own honest-range condition disclosure (no duplicate HBU note there) — a marginal HBU-disclosure gap on already-heavily-caveated surfaces (acceptable; flagged).
