# CHANGELOG v77 — Sprint 2.22.0a.25 (CC BY 4.0 source attribution for MoJ data)

**Engine:** `thammen-sprint2p22p0a25-moj-source-attribution-ccby` · **SPRINT_TAG** `2.22.0a.25` ·
**api/health** `3.1.0-sprint2.22.0a.25` · **Date:** 2026-06-05
**Files changed:** `index.html` (footer attribution credit + CSS), `evaluate_unified.py`
(ENGINE_VERSION / SPRINT_TAG → a25), `CHANGELOG_v77.md`. **Type:** user-facing copy add /
compliance hygiene. **NO methodology / valuation change — value-invariant; every headline + the B-1
`value_floor` byte-identical.** Gate-2 (copy) SIGNED by Anas verbatim; Gate-1 (push) authorized
(standalone deploy ritual).

---

## 1. Why this matters
The MoJ datasets on `data.gov.qa` are licensed **CC BY 4.0** (verified 2026-06-05 via the OpenDataSoft
catalog API — `weekly-real-estates-sales-bulletin` + `weekly-residential-units-sales-bulletin`,
publisher = Ministry of Justice; CC BY is portal-wide). CC BY permits commercial use, derivatives and
redistribution; the sole obligation is **attribution + no-endorsement**. Thammen surfaces derived MoJ
figures with no credit rendered. This adds the required credit and closes **COMPLIANCE Q13 / RISK_REGISTER
R13 (open-data-licence sub-item)**. Hard constraint: attribution must be present before external users
first see derived MoJ figures (i.e. before the beta opens) — now satisfied.

## 2. Context (additive)
No defect. A standard-licence attribution obligation that was previously unmet on the user surface.

## 3. Dataset actually ingested (Operational §12)
The engine's comparable fetch uses **`weekly-real-estates-sales-bulletin`** (`moj_reference.py:11` /
`:289`, `reasoning_trace.py:249` / `:421`). The `weekly-residential-units-sales-bulletin` (apartments) is
**not** ingested by the engine. The credit's wording "real-estate transaction bulletins" accurately names
what is used.

## 4. What this patch does (frontend only)
- New persistent **source-attribution credit** in the results footer (`.disc`, where derived MoJ figures
  appear — alongside the a24 Terms link + the existing disclaimer). Renders verbatim AR + EN.
- The licence name is a link → `https://creativecommons.org/licenses/by/4.0/` (`target="_blank"
  rel="noopener"`), on both the AR and EN lines.
- **Bidi:** the Latin/numeric tokens (`data.gov.qa`, `4.0`, `CC BY 4.0`) are wrapped in `dir="ltr"`
  islands per the a24 pattern; the AR block is `dir="rtl"`, the EN block `dir="ltr"` left-aligned.
- CSS: `.src-credit` / `.src-credit .en` (muted, small, top-bordered). No JS change.
- ENGINE_VERSION / SPRINT_TAG → a25 (api/health auto-derives).

**Verbatim copy (as shipped):**
- AR: «مصدر البيانات: نشرات بيع العقارات الصادرة عن وزارة العدل (دولة قطر) عبر بوابة قطر للبيانات المفتوحة
  (data.gov.qa)، بموجب رخصة المشاع الإبداعي «نَسب المُصنَّف» 4.0 (CC BY 4.0). تُعالَج البيانات وتُجمَّع
  بواسطة «ثَمِّن»، والتقديرات مُشتقّة وليست تقييمات رسمية صادرة عن وزارة العدل.»
- EN: "Source data: real-estate transaction bulletins, Ministry of Justice (State of Qatar), via Qatar
  Open Data (data.gov.qa), licensed under CC BY 4.0. Figures are processed and aggregated by Thammen;
  estimates are derived and are not official Ministry of Justice valuations."

## 5. Verification — empirical evidence
- **py_compile** `evaluate_unified.py` OK (api.py untouched).
- **R14 (real Chromium, `node` absent; a25 adds no JS — inline JS byte-identical to a24, console clean):**
  results-footer credit renders; 390×844 no horizontal overflow (creditRight 350 ≤ 390); desktop 1280×800
  no overflow; computed dir = rtl (AR container) / ltr (3 islands + EN block); "CC BY 4.0" reads LTR;
  link href = `https://creativecommons.org/licenses/by/4.0/`, text "CC BY 4.0"; AR + EN verbatim.
- **DoD (PYTHONIOENCODING=utf-8):** aggregator **392/392** · security **15/15** · surface-honesty
  **45/45** · broad auto-walk **66/66** (123.7s). No new test (copy-only).
- **Post-deploy (filled at deploy):** /api/health = a25; 4 anchors byte-identical (zero value drift).

## 6. Deployment
```
cd /d "C:\Thammen\deploy v2"
git add index.html evaluate_unified.py CHANGELOG_v77.md
git commit -m "Sprint 2.22.0a.25 (CC BY 4.0 attribution): MoJ source credit in footer (Q13/R13 closure)"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 7. Verification curl (post-deploy)
```
curl -s "https://thammen.qa/api/health"
curl -s -X POST "https://thammen.qa/api/evaluate" -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124 Safari/537.36" -H "Content-Type: application/json" -d "{\"zone\":56,\"street\":565,\"building\":21}"
```
Expect: health `…a25`; 56/565/21 = 2,400,000 (unchanged). Re-smoke 54/541/6 (5.4M), 55/296/13 (2.6M),
52/903/90 (refusal) for zero drift. (The credit is rendered client-side; `curl` confirms the value
invariance, the live page confirms the footer.)

## 8. What's NOT in this patch
- **No methodology / valuation change** — value-invariant; estimates byte-identical.
- **No instrumentation, no per-dataset licence pages** (out of scope).
- **No backend route** — the credit is static frontend copy in the results footer.
- The credit lives on the results surface (where derived figures appear); the home screen shows no
  derived figures, so it is not duplicated there.
