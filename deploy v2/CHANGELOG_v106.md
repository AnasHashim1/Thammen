# CHANGELOG v106 — Sprint 2.22.0b.23 «بثّ المختصر» (short-report: scenarios + report verify)

**Engine:** `thammen-sprint2p22p0b23-short-report-verify` · **SPRINT_TAG:** `2.22.0b.23` · **Date:** 2026-06-12
**Files:** `evaluate_unified.py` (scenarios + report-identity pure fns + 2 attach sites + version) · `api.py` (`GET /verify` + shared-fn import + hmac) · `index.html` (report scenarios panel + report_ref/verify link) · `test_sprint_2_22_0b23.py` (new, 47 checks) · `docs/PLAN_short_report_rollout_v1.1.md` (the signed plan + D1–D8).
**Classification:** 🔴 micro Gate-2 **ADDITIVE-ONLY** — SIGNED (the contract enumeration); deploy-on-green conditioned on the byte-identity contract.

## 1. Why this matters
A Thammen report was a single number + a range. Two gaps: (a) an owner can't see what their property would be worth in a different condition/finish (the most-asked "what if I renovate / it's luxury / it's a teardown?"); (b) a shared report had no integrity check — a recipient couldn't tell a real figure from a doctored screenshot. «بثّ المختصر» adds both, purely additively.

## 2. What this patch does
**(1) `valuation.scenarios`** (villa/house) — 4 cost-approach what-ifs from the EXISTING pure calculators (the b11/b13 DRC `_cost_approach_value` + the B-1 land floor + the b4 demolition band) on the already-fetched context (ZERO new GIS): `as_is` (the headline mirror) · `renovated_excellent` (DRC good-finish + excellent) · `luxury_finish` (DRC luxury-finish + excellent) · `teardown_land` (land_floor − demolition). The headline (amount/low/high/method/rule/leadership) is NOT touched.
**(2) `report_ref`** = `TH-{YYYYMMDD}-{ZZSSSBBB}` (+`-{4hex}` from a plain hash of the refine inputs; `P{pin}` for land).
**(3) `report_fp`** = `HMAC-SHA256(HMAC_REPORT_KEY, "v1|addr|date|engine|amount|low|high|rule")[:12]`, per-field `\s+`-normalized; DORMANT (None) without the key (#62 — never a plain hash of low-entropy fields). `report_fp_basis` carries the signed fields (the /verify payload).
**(4) `GET /verify`** — recomputes the fingerprint from the posted core fields via the SHARED `_report_canonical`+`_report_fingerprint` (imported from the engine → can't drift), constant-time compares to the posted fp, and renders a ✓/✗ RTL page; no storage; rate-limited (the `";".join(RATE_LIMIT_LIST)` string form, slowapi lesson #35); dormant-without-key → "verification unavailable".
**(5) `index.html`** — the report (`showReport`) renders the scenarios panel + `report_ref` + a «تحقّق من صحّة التقرير ✓» link (only when `report_fp` is present, i.e. the key is configured).

## 3. The byte-identity contract (the gate)
The 22 fixtures stay byte-identical on **amount/low/high/rule** — the new keys are siblings; the code never writes amount/low/high/method/rule (isolated 7.3 proves `_attach_report_identity` leaves the valuation block UNCHANGED; the scenarios helper takes the headline as an INPUT and returns a separate list). **Any value movement in the live smoke = STOP + report.**

## 4. Verification — empirical evidence
- Isolated `test_sprint_2_22_0b23.py` **47/47** — scenario shapes on the Marikh/V001 anchors (monotonic luxury>renovated>land; teardown<land) + graceful degrade (no DRC inputs → as_is only) + the canonical `\s+`/None rules + HMAC accept/**reject-forgery**(amount & rule & wrong-key)/**dormant** + ref format + 4hex order-independence + `_attach_report_identity` byte-invariance + wiring pins (engine/api/index.html).
- DoD: aggregator **392 ALL COUNTS MATCH** · security **15/15** · surface-honesty **45/45** · broad walk **92/92 ALL GREEN** (91→92 with the new test).
- **Local E2E DEFERRED** — khazna `QARS_Point` returns the 503 ArcGIS auth-envelope from the dev host (RISK_REGISTER R5; Heroku reaches it) → the byte-identity proof on real fixtures runs in the live smoke; the structural guarantee (additive-only) holds offline.
- **R14 real-Chromium 390×844** — the report renders the scenarios panel (4 rows: 2,400,000 / 2,700,000 / 3,000,000 / 1,700,000 on the Marikh-class report) + `report_ref` + the verify link (right-edge 200<390); no overflow (390==390); **0 console errors**. `/verify` recompute MATCHES the report fp (✓ path) + a forged amount/rule MISMATCHES (✗ path); `_verify_html` renders all 3 states (ok/fail/unavailable).

## 5. Deployment
```
cd /d "C:\Thammen"
git subtree push --prefix "deploy v2" heroku master
heroku config:set HMAC_REPORT_KEY=<64-hex random>     # activates the fingerprint (#55 / D8)
git push origin master
```

## 6. Verification curl (post-deploy)
```
curl -s https://thammen.qa/api/health | findstr 2.22.0b.23
curl -s -A "Mozilla/5.0 ... Chrome/125 Safari/537.36" -X POST https://thammen.qa/api/evaluate -H "Content-Type: application/json" -d "{\"zone\":54,\"street\":541,\"building\":6}" > b23.json
findstr /C:"scenarios" b23.json
findstr /C:"report_fp" b23.json
```
(Then open the report's «تحقّق» link → ✓; tamper an amount in the URL → ✗.)

## 7. What's NOT in this patch (→ «بوابة بيانات الأنواع»)
- The compound_large GAI promise (still refuses; 44.35M computed-then-discarded) · `value_stack`/`leadership` for buildings (b20 extension) · the types-tab + coming-soon cards · buildings cap-rate calibration. Each its own signed Gate-2 under the named "types-data gate".
- No change to any valued path's amount/low/high/method/rule, b6/b11/b13/b16/b18/b20/b21/b22 logic, or the income/refusal headlines. `HMAC_REPORT_KEY` is the single env toggle (#55).
