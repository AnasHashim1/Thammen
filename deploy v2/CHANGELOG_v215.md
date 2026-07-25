# CHANGELOG v215 — Sprint 2.22.0b.144 «إنجليزيّة الأدلّة الهندسيّة» (EN twins for the corner/HBU geometric evidence)

**Engine:** `thammen-sprint2p22p0b144-en-geometric-evidence` · **api-health:** `3.1.0-sprint2.22.0b.144`
**Files:** `geometric_factors.py` (evidence_en beside evidence_ar — corner 5 branches + HBU industrial + HBU main) · `evaluate_unified.py` (2 geo_section `evidence_en` passthrough lines + the 2 version lines) · `test_sprint_2_22_0b144.py` (new) · `test_sprint_2_22_0b143.py` (proactive Lesson-2 version-pin relax).
🟢 **ENGINE DISPLAY-COPY / VALUE-NEUTRAL** — `api.py` + `index.html` UNTOUCHED; only additive `_en` STRING keys; `evidence_ar` byte-identical; `potential_pct`/`is_corner`/the range-expansion inputs untouched.

## 1. Why this matters
The result-screen **Geometric Findings card** reads `pick(ca,'evidence')` / `pick(hbu,'evidence')` since b140 — but the engine emitted only `evidence_ar`, and these are **INTERPOLATED sentences** (street numbers / zone codes / +N%) that the constant en_localize CATALOG cannot cover. In EN mode the card leaked Arabic. Sprint B slice 3 of the A(b140)→ترشيق(b141)→B sequence (b142 arrays · b143 scope).

## 2. Root cause
Interpolation → no catalog key can match; and `evaluate_unified.py`'s `geo_section` REBUILDS the corner/hbu dicts copying only `evidence_ar` (:7285/:7301) — so even an engine-side `_en` needed the passthrough copies.

## 3. What this patch does
`geometric_factors.py`: `detect_corner` builds `evidence_en` beside `evidence` with the SAME street-list interpolations (5 branches: corner+main / corner-internal / fronting-main / fronting-internal / no-street) + returns it; `analyze_adjacent_zoning` emits `evidence_en` on the two RENDERED returns — industrial ("Adjacent industrial zoning (…) — may reduce the value") + the main rezoning evidence ("Rezoning potential: {flag_en} (…). The value may rise by +N% if the change is approved (RICS HBU — VPS 2 / IVS 102).") with `flag_en` ∈ {adjacent mixed use (MU) / adjacent commercial (codes) / adjacent higher-density zoning}. The GATED-OUT returns (confidence-low corner debug + same-zoning/no-data/already-commercial HBU) are deliberately NOT localized (the b139 dead-field discipline — `geo_section` gates them out). `evaluate_unified.py`: the 2 `geo_section` passthrough copies. **Frontend UNTOUCHED** (pick already there).

## 4. Verification — empirical evidence
- py_compile OK · isolated `test_sprint_2_22_0b144.py` **24/24** (E14 — the REAL `detect_corner` with stubbed-empty GIS → both `_ar`+`_en` emitted; the REAL `analyze_adjacent_zoning` with fixture zoning → MU/commercial/higher-density/industrial branches each emit English with the exact interpolations; gated-out branch has NO `_en`; structural passthroughs; AR byte-identical; frontend untouched).
- DoD: aggregator **ALL COUNTS MATCH** · security **16/16** · surface **45/45** · broad walk **196/196 ALL GREEN** (195→196; zero re-points beyond the proactive b143 pin relax).
- **R14 real-Chromium 390×844** (served static + the live Marikh payload enriched with the b144 fields): **AR** — corner «مطل على شارع داخلي» + HBU «إمكانية تعديل رخصة» render, 0 EN leak, dir=rtl, amount ٢٬٤٠٠٬٠٠٠, no overflow (390==390); **EN** — dir=ltr, "Fronting an internal street (internal streets: [541, 692])" + "Rezoning potential: adjacent commercial (C2)… +25%… RICS HBU" render, ZERO AR leak on the card, amount 2,400,000 unchanged; **AR restore byte-identical**; **0 console errors**.
- Personas: lawyer APPROVE (the EN keeps the honest conditional «may rise… if approved» + the RICS citation + the industrial negative disclosure — no new claim); linguist APPROVE (b78 termbase).

## 5. Deployment
origin FIRST → `git subtree push --prefix "deploy v2" heroku master`.

## 6. Verification curl (post-deploy)
`/api/health` = b144 · the 5-fixture value byte-gate byte-identical to v307 · the villa response carries `geometric_factors.corner_analysis.evidence_en` (English).

## 7. What's NOT in this patch
**b145** = MUC `factors`+`recommendations` EN (recon RESHAPED the anticipated dataclass-threading design → an en_localize array-rule extension [catalog constants + a regex-template table for the interpolated n=X shapes] + frontend `pickArr` swaps — the api.py:262 post-pass sees the FINAL mutated arrays, alignment automatic). The gated-out geometric returns stay AR-only (never rendered). No value/methodology change.
