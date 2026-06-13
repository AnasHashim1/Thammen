# PHASE-0 RECON — DEF-UX1 «كشف الصفقات المقارِنة للفيلا/البيت» (keystone comparables) — read-only, NOT shipped

> **Date:** 2026-06-13. **Engine UNCHANGED — live stays b37 / Heroku v208 (byte-identical).** No
> engine/frontend change, no deploy. Read-only §5 recon (the prerequisite the `ISSUES_LOG §4ب`
> DEF-UX1 row explicitly names: *«recon: أي مسار + التطبيع + تأطير التشتّت»*). Persisted per Rule
> #42/#63 to de-risk the Gate-2 brief. #57 handshake: b37/v208, `master==origin`, qars healthy
> (162,516), MoJ 164d. Method: CC direct grep/Read + a 4-reader parallel workflow (Explore agents).

## 0. The question

DEF-UX1 (🔴 Gate-2, **7/10 personas** — البنك·المثمّن·السمسار·المستثمر·المالك·الصحفي·المشترية): an
accordion «مقارنات مشابهة» (3–10 rows) showing the actual MoJ transactions that drove the villa
number — the **keystone** trust feature. The §4ب ledger flagged the «مبنيّ-مجاناً» (built-free) claim
as **falsified** (*«المحرك يبثّ الأرض فقط»* — the engine broadcasts only the LAND comparables) and named
three recon decisions: **أي مسار** (which data path), **التطبيع** (time-normalization), **تأطير التشتّت**
(dispersion framing). This recon answers all three + measures the real cost, value-invariance, and privacy.

## 1. «مبنيّ-مجاناً» — FALSIFIED, but the fix is modest (the rows are computed, just discarded)

- The live VILLA headline path is `evaluate_property.py:1576` → **`build_reference(rows, area_name_in_moj, max_d)`** — called **WITHOUT `return_transactions=True`**. `build_reference` (moj_reference.py:128) computes the subject-bracket comparable rows at `bracket_data['transactions']` (moj_reference.py:206-217) **only when the flag is set** → on the live path the rows are **built then dropped**; the response carries aggregate-only (n / median / p25 / p75).
- The GEO/widened path `geo_reference_v2._get_area_transactions` **does build a `txns` list** (geo_reference_v2.py:325, append at :368) — but it is likewise not attached to the villa response.
- **What a villa carries about comparables TODAY:** only `valuation.source_ar` («وسيط N معاملة في نفس الشريحة والمنطقة») + `valuation.n_transactions`. **No rows.** (The land `comparable_grid` IS broadcast — see §4.)
- **Verdict:** «built-free» is false (no villa rows in the response), **but** the rows are already computed on both paths → surfacing them is a **modest engine-additive** change: thread `return_transactions=True` + attach a new `valuation.comparables` field + render. **Not a heavy build.**

## 2. The driving comparables differ by LEADERSHIP path — the brief's core decision (b20)

This is the decisive finding. «أي مسار» has **no single answer** — it depends on which leader the b20
`_leadership_gate` picked, so the keystone panel content is leadership-dependent:

| Leadership (b20) | What drove the number | Keystone rows source | Honest framing |
|---|---|---|---|
| **matched / bracket-led** (RULE 1, e.g. أبو هامور) | the subject-bracket total-price median | the subject-bracket `build_reference(return_transactions=True)` rows — **the tightest, best «keystone» set** (exact size bracket + area) | «N صفقة في شريحتك ومنطقتك قرّرت رقمك» |
| **geo-led / widened** (RULE 2, e.g. V001 geo-full rescue) | the geo-full ppm² pool median | the `geo_v2` pool rows (`_get_area_transactions`, :368) | «حوض جغرافي أوسع — N صفقة» + the b20 «غير مطابق طبقياً» note |
| **cost-led** (E25, e.g. امريخ/Marikh) | the **DRC cost** (land + depreciated building) — **NOT a comparable median** | the geo-full pool was **considered but did NOT lead** (failed its reliability bar, disp 0.620 > 0.30) | «المجموعة السوقية التي رأيناها — ولماذا لم تقُد الرقم» (dispersion-too-high), distinct from market-led copy |
| **raw_land** | the land adjustment grid | already broadcast as `comparable_grid` (§4) | parity baseline (lands already do this) |
| **apartment/tower refusal** | — (no valuation) | none | b36 honest refusal (no comparables) |

⟹ The brief MUST specify the row-source per leadership case + the **cost-led** copy (the keystone panel
can't pretend cost-led was comparable-driven — that would misrepresent the methodology). The spec's
single-source assumption (`geo_v2.primary.transactions`) is **insufficient**: it misses that bracket-led
cases have a *tighter* set, and that cost-led cases have *no leading* comparable set.

## 3. Value-invariant (display-only)

The median/cost already drives `amount/low/high/method/rule` (b20). Surfacing the rows attaches a new
display field only — **byte-identical headline** across all anchors (the b24 «الرقم واحد» / b31..b37
discipline). Confirmed: `build_reference`'s aggregate outputs (the ones feeding the headline) are
unchanged when `return_transactions=True` (it only *adds* `transactions` to each bracket).

## 4. Land/villa asymmetry + render slot + reuse

- **Lands (Sprint 2.20)** broadcast `output['comparable_grid']` (evaluate_unified.py:5201, gated
  `asset_type in ('land','raw_land')`) with rich rows: `date, price_per_m2_raw, price_per_m2_adjusted,
  size_m2, adjustments[] (factor/pct/source/tier/n/confidence/rationale_ar)` — RICS time-normalized.
  Rendered by `build_comparable_grid_section` (output_briefs.py:215) + a client `comparable_grid` brief
  case (index.html:2830-2849, **report-only** today, not on the result screen).
- **Villas** show aggregate text only. **DEF-UX1 = bringing villa comparables up to land parity.**
- **Reuse:** NO logic reuse (land = adjustment grid; villa = bracket stratification median) — a
  **villa-specific keystone panel** is needed. BUT the **visual row-card pattern** (index.html:2830-2849:
  date · size · ppm²) is directly **adaptable** to the villa row schema.
- **Render slot:** inside the b31 **«🔍 كيف وصلنا لهذا الرقم؟»** TIER-2 accordion (index.html:2367, the
  `t2+=_acc('🔍 كيف وصلنا…', how+evidencePanelHtml(d,acc), _dense)` call) — append to the `how` buffer
  (~2310-2348). It is **density-gated (b34)**: investor/valuer see it OPEN, owner/buyer/seller collapsed
  → the raw evidence pool surfaces to those trained to read it (reduces misuse). The `_acc` wrapper
  (index.html:929) returns '' on empty → defensive.

## 5. Privacy — SAFE (E12-clean, CC BY 4.0)

The exported row (moj_reference.py:207-216) carries **only** `date, area_m2, total_price, price_per_m2,
price_per_ft2, type_ar`. **No PIN, no address, no coordinates, no municipality** — and the `property_ref`
(the E12 PN-hash) + the transaction id are **deliberately stripped** from the export. MoJ data is **CC BY
4.0 public** (data.gov.qa; attribution already live since a25). Surfacing anonymous size/price/date/type
rows is privacy-clean. Honest copy: «N صفقة قرّرت رقمك» · per-row «تاريخ · حجم · سعر/م²» · source line
«بيانات وزارة العدل — مجموع عامّ لا ترقيم/عنوان فردي — CC BY 4.0».

## 6. Honest scope (engine-additive, value-invariant, Gate-2 but LOW-RISK)

- **Engine:** thread `return_transactions=True` at the bracket call-site (`evaluate_property.py:1576`) +
  capture the geo pool rows for geo-led/cost-led cases + attach `valuation.comparables = {basis: <which
  path/leadership>, rows: [≤N anonymous rows, newest-first], n, window_months}` (and a cost-led variant
  that labels the pool «considered, did not lead»). Modest LOC; **no headline math touched**.
- **Frontend:** a villa keystone block in the b31 accordion (density-gated), adapting the
  index.html:2830 row-card visual; leadership-aware copy + dispersion framing (ties to a14/b20).
- **Gate-2:** YES (new user-facing surface + new engine field + leadership-dependent copy) — but
  **low-risk** (value-invariant, privacy-clean, public data, surfaces existing-computed rows).

## 7. Open decisions for the SIGNED brief (hand to Claude.ai)

1. **Row source per leadership case** (§2 table) + the **cost-led** framing («considered, did not lead»).
2. **التطبيع (time-normalization):** the spec says «مُطبَّعة زمنياً» — but the bracket `transactions` are
   **RAW** (not time-adjusted; the bracket median isn't time-normalized within the 24/36mo window). FORK:
   **(a)** show raw rows + dates (simpler, more transparent — the user sees recency directly) vs **(b)**
   time-normalize like the land grid (more work, matches «مُطبَّعة زمنياً», adds an adjustment column).
   **Recon recommendation: (a) raw rows + visible dates + the window label** — honest, no synthetic
   adjustment, and the dispersion/honest-range (a14) already carries the «spread» story.
3. **تأطير التشتّت:** tie the panel to the a14 dispersion gate — if the bracket is dispersed (≥0.30,
   honest-range fired), the panel says «الصفقات متفرّقة — لذلك النطاق أوسع»; if tight, «متقاربة».
4. **Row count / sort / fields:** spec = 3–10; newest-first; show date · size m² · total price · price/m²
   (hide ft²?); the n + window («من N صفقة خلال {window} شهراً»).
5. **Copy + CC BY 4.0 source line + MUC tie** (anonymous, no address).

## 8. Carried forward (Rule #42)

- `moj_db.py:398` has a faster SQLite `build_reference`-equivalent defaulting to `return_transactions=True`
  — a perf option for the threading (if the live path migrates to the DB).
- The land `comparable_grid` is **report-only** on the client today (index.html:2830) — a future parity
  pass could surface it on the result screen too (out of UX1 scope).
- **Recommend** annotating `ISSUES_LOG §4ب` DEF-UX1: *recon ✅ done → this doc; the named questions (أي
  مسار / التطبيع / تأطير التشتّت) resolved → brief decisions in §7* (planning-lane ledger edit).
- The «التقدير السوقي» term remains PROVISIONAL.
