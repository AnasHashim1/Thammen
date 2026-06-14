# CHANGELOG v126 — Sprint 2.22.0b.43 «نسخة-المُشغِّل: العنوان بلا بيانات شخصية»
**(operator report-copy: keep the address, strip personal data)**

> Engine `thammen-sprint2p22p0b43-report-copy-no-personal-data` / SPRINT_TAG `2.22.0b.43`
> / api-health `3.1.0-sprint2.22.0b.43`.
> **🟢 ADDITIVE / DORMANT-by-default / VALUE-INVARIANT.** `api.py` + `index.html` +
> the valuation engine UNTOUCHED; the 5-anchor value byte-gate is identical to v216 by
> construction (the email is a post-response side-effect that never enters the valuation
> path and `_scrub_personal` deep-copies, so `result` is byte-identical to the response).
> **Files changed:** `report_mailer.py`, `test_sprint_2_22_0b42.py`, `evaluate_unified.py`
> (the 2 version-string lines only). **PENDING Hard Gate 1** (Heroku deploy = explicit consent).

## 1. Why this matters
b42.2 made the operator report-copy email **LIVE + ACTIVE** (inbox-confirmed). The PO's refined
requirement: the operator email should **still receive the property ADDRESS, but WITHOUT personal
data** («اريد ان يصلني العنوان كذلك. لكن بدون بيانات شخصية»). The earlier full address-**redaction**
attempt was rejected and reverted; this is the precise middle: keep the property's identity, drop the
two fields that are genuinely a **person's** data.

## 2. What is "personal data" here (the line, defensibly drawn)
The engine `result` carries, in the person-identifying class, exactly **two** fields:
- `property_basis.electricity_no` — the **Kahramaa electricity account number** (a billing identifier).
- `property_basis.water_no` — the **Kahramaa water account number** (same).

Everything else is **property / valuation** data: the address (the PO explicitly wants it), the
cadastral **PIN** (a land-registry parcel id), the district, GPS (property *location* — the same class
as the address, kept for consistency), the valuation/range/method/tier/MUC, the age estimate, dates,
the fingerprint, and the comparables. So **"personal data" = the utility ACCOUNT numbers**; they are
the only fields tied to a *person's billing* rather than to the *parcel*. They add nothing to the
operator's memory either — the full report is regenerable on thammen.qa from `address + report_ref`.

## 3. What this patch does (`report_mailer.py`, backend-only)
- New `_PERSONAL_PB_FIELDS = ("electricity_no", "water_no")` + pure `_scrub_personal(result)` that
  returns a **deep copy** of `result` with those two `property_basis` fields removed (**never mutates**
  the caller's `result` — the isolation invariant).
- `_summary_fields`: stops reading `electricity_no` (PIN + age stay — property data).
- `_html`: drops the «كهرباء …» summary bit (PIN + age line kept).
- `build_email`: the attached JSON is now `_scrub_personal(result)` (was the full `result`) — so the
  scrub is **complete**: the account numbers leave **both** the body **and** the archive attachment.
- The subject, the address row, the cadastral PIN, age, valuation, leadership note, fingerprint, and
  the full-archive-minus-two-fields attachment are otherwise **unchanged from b42.2**.

## 4. Verification — empirical
- py_compile `report_mailer.py` + `evaluate_unified.py` OK.
- Isolated `test_sprint_2_22_0b42.py` **48/48** (42 → 48; SAMPLE gains `water_no` per E14 to match the
  real shape; +6 b43 checks: html keeps the PIN, html drops the electricity/water numbers + the «كهرباء»
  word, attachment == `_scrub_personal(SAMPLE)`, attachment keeps address+PIN, attachment dropped
  electricity_no+water_no, **ISOLATION — `build_email` did not mutate the caller's result**).
- DoD: aggregator **392 ALL COUNTS MATCH** · security **15/15** · surface honesty **45/45** ·
  broad walk **110/110 ALL GREEN** (68.9s).
- `import api` OK → **14 routes**, `_MAIL_OK=True`, `mail_enabled()=False` (dormant by default).
- **Real-result render proof** (`.b40_marikh.json`, Marikh 54/541/6, with key+recipient set):
  subject `[ثمن] TH-20260614-54541006-b052 — 54/541/6 — 2,400,000 ر.ق`; **address + PIN (54360025) +
  age kept**; electricity `161418` + the «كهرباء» word + water `131980` **gone from the body**;
  attachment keeps address+PIN+GPS but **dropped** electricity_no + water_no; the original `result`
  **still carries both** account numbers (deep-copy isolation holds).
- Diff scope: `report_mailer.py` + `test_sprint_2_22_0b42.py` + the **2** `evaluate_unified.py`
  version lines. `index.html` / `api.py` / DPIA = **0 diff** → value-invariant by construction.

## 5. Deployment (PENDING explicit consent — Hard Gate 1)
```
git add "deploy v2/report_mailer.py" "deploy v2/test_sprint_2_22_0b42.py" "deploy v2/evaluate_unified.py" "deploy v2/CHANGELOG_v126.md"
git commit -m "Sprint 2.22.0b.43 (report-copy no-personal-data): keep the address, strip the Kahramaa utility account numbers (electricity_no/water_no) from the operator email body + JSON attachment (E14 fixture + isolation); engine version bump only"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```
Post-deploy: `/api/health` = b43; the next eval delivers a copy whose body + attachment carry the
address + PIN + age + valuation but **no** electricity/water account numbers.

## 6. What's NOT in this patch
- The **a24 privacy-notice** truthful update (the live notice still says "stores nothing", which is
  false now that the operator copy retains the address) — separate, PO wording still unsettled; the
  rejected heavy-redaction posture is NOT to be re-applied. This stays the gate for **beta-wide** use
  (Rule #39); for the **operator's own** testing it is a non-issue (no third-party data).
- GPS / PIN are **kept** (property data, same class as the retained address) — not stripped.
- No engine/methodology/api/frontend change; no deploy in this commit (Hard Gate 1).
