# CHANGELOG v113 — Sprint 2.22.0b.30 «share-evidence copy»

**Engine:** `thammen-sprint2p22p0b30-share-evidence-copy` · **SPRINT_TAG:** `2.22.0b.30`
**Date:** 2026-06-13 · **Files:** `index.html` (+15/−2) + `evaluate_unified.py` (2 version lines only)
**Class:** 🟢 FRONTEND-ONLY / VALUE-INVARIANT — autonomous-lead (reversible display of already-broadcast data; no methodology/output-value change). Born from the 10-persona LIVE-site review.

## 2. Why this matters
The 10-persona review found the **highest-leverage SAFE win**: the shared/copied result was a bare number (address + amount + range + methodology). The broker's #1 unmet need — and the heirs'/bank's trust anchor — is a copy that answers **«من أين الرقم؟»**. All the evidence was on screen / in the broadcast but absent from the clipboard artifact.

## 3. Root cause
`copyResult()` (`index.html:1196`) pushed only address/asset/area + amount/range + methodology + footer. It never copied the sample size, the data-freshness caveat, the not-certified label, or the tamper-evident `report_ref` + `/verify` URL — exactly the provenance a recipient needs.

## 4. What this patch does
Inside the **valued branch** of `copyResult()` (guarded on `v.amount`), append (all from `window._lastResult`, already broadcast/shown):
- **عدد الصفقات المقارِنة** ← `v.n_transactions` (fallback `d.moj_sample_size`)
- **حداثة بيانات وزارة العدل** ← `d.data_freshness.latest_record_ar` + `days_old`
- the honesty label **«تقدير سوقيّ آليّ، وليس تقييماً معتمداً»** (valued path only)
- **مرجع التقرير** ← `d.report_ref` + **تحقّق من الأصالة** ← the shared `_verifyUrl(d)` (b23/b25), each guarded so a dormant-fp / no-ref payload adds nothing.

The refusal branch (`v.reason_ar`) is untouched — no evidence/ref lines. The headline copy lines (amount/range/methodology) are byte-unchanged.

## 5. Verification — empirical evidence
- Isolated `test_sprint_2_22_0b30.py` **16/16** (reads the real `index.html`: broadcast-field reads, label/ref guards, value-invariance of the headline lines, evidence lines inside the valued branch, version format).
- DoD: aggregator **ALL COUNTS MATCH** · broad walk **98/98** (97→98, +b30 test) · siblings **b29 32/32 + b25 77/77 WITHOUT re-points**.
- **R14 (390×844, live Marikh payload):** clipboard text = address + 2,400,000 + range + **«عدد الصفقات المقارِنة: 15»** + **«حداثة … حتى 31 ديسمبر 2025 (163 يوماً)»** + methodology + **not-certified label** + **«مرجع التقرير: TH-…»** + **verify URL**; refusal payload (52/903/90) → no evidence/ref lines; **0 console errors**.

## 6. Deployment
`git subtree push --prefix "deploy v2" heroku master` + `git push origin master` (heroku auth verified).

## 7. Verification curl (post-deploy)
```
curl -s https://thammen.qa/api/health | findstr /C:"2.22.0b.30"
curl -s https://thammen.qa/ -A "Mozilla/5.0" | findstr /C:"عدد الصفقات المقارِنة" /C:"مرجع التقرير"
```

## 8. What's NOT in this patch
- **NOT** the villa/house **comparable-list disclosure** (the persona keystone for bank/valuer/broker). Measured: the engine emits a comparable grid **LAND-ONLY** (`build_land_grid`); villa/house transactions exist in `geo_v2_result.primary.transactions` but are not surfaced, and surfacing them correctly (which-path comps + time-normalization + dispersion framing) is a **Gate-2** sprint needing a recon + sign — the next session's keystone.
- No engine/value/methodology change; no per-m² (basis-ambiguous, deliberately omitted); apartment/compound coverage unchanged.
