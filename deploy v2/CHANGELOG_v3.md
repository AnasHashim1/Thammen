# Thammen v3 — CHANGELOG

## What's New (v3 over v2)

### 🔴 Critical Additions

#### 1. rent_reference.py — مرجع الإيجارات (360,860 معاملة)
- **Data source**: qrep.aqarat.gov.qa — قائمة معاملات الإيجار (2023-2026)
- **Coverage**: 8 بلديات × 11 نوع وحدة × 7 شرائح غرف = 216 مجموعة مرجعية
- **Functions**: `query_rent()`, `estimate_annual_rent()`, `income_approach_value()`
- **Limitation declared**: بلدية فقط — لا منطقة فرعية (disclosed in every output)
- **Sample size discipline**: same thresholds as MoJ (n≥20 reliable, 10-19 indicative, <5 insufficient)

#### 2. comparable_adjustments.py — تعديل المقارنات فردياً (RICS VPS 4 §7)
- Time adjustment: monthly rate from area price trend
- Size adjustment: per-bracket relative pricing
- Location sub-adjustment: from GIS factors (when available)
- Condition caveat: explicit "unknown" — MoJ has no condition data
- Produces per-transaction adjustment table (transparent, auditable)

#### 3. material_uncertainty.py — تحفظ مادي (RICS VPS 4 §3.2)
- Assesses uncertainty across ALL data sources (MoJ sample, rent data, trend, inspection, BUA, service charges)
- 4 levels: critical / high / moderate / low
- Arabic + English banners
- known_unknowns list
- RICS compliance flag (never True without field inspection)

#### 4. evaluate_v3.py — 3-Way Blended Valuation
- Comparison (MoJ) + Cost (replacement) + Income (rent_reference)
- Weight allocation by asset type:
  - STANDALONE_VILLA: 60% comparison + 25% cost + 15% income
  - APARTMENT/TOWER: 30% comparison + 15% cost + 55% income
  - COMPOUND_LARGE: 0% comparison + 15% cost + 85% income
  - RAW_LAND: 100% comparison
- Data quality adjustments (weak MoJ → shift to cost/income, weak rent → shift to comparison/cost)
- Divergence warning when methods spread > 30%

#### 5. output_briefs.py — 4 تقارير مخصصة
- **Buyer Brief**: هل السعر معقول؟ نطاق التفاوض. المخاطر. أسئلة الفحص.
- **Seller Brief**: قيمة العقار. استراتيجية التسعير. اتجاه السوق.
- **Investor Brief**: العائد الصافي. تحليل الحساسية. مرجع الإيجار. السياق السوقي.
- **Valuer Brief**: المنهجية. جدول التعديلات. المصادر. التحفظات. سلسلة المنطق.

#### 6. sales_merge.py — دمج مصدري البيع
- Annual XLSX from qrep.aqarat.gov.qa: 37,617 transactions (2020-2026)
- Cross-check with weekly bulletin (26,719 from data.gov.qa)
- Area-level price/ft² statistics without requiring property type
- Annual trend computation per area

---

## What Was NOT Changed in v2 Files

The following files are **untouched** — v3 is purely additive:
- evaluate_property.py (2,539 lines — v2 engine)
- moj_reference.py
- moj_db.py
- property_factors.py
- service_charge_db.py
- reasoning_trace.py
- market_position.py
- listing_db.py
- api.py (needs v3 endpoints — Phase 2)
- calibrate_construction_cost.py
- construction_costs.json
- All tests

---

## Known Gaps (honest, per the doc)

These are NOT in v3 and need Phase 2/3 work:

1. **Scrapers** — No automated listing fetching (PropertyFinder, FGRealty, arady, Mzad)
2. **Building intelligence** — No per-tower database (Marina Gate vs generic tower)
3. **Service charge coverage** — Still 5 precincts only
4. **Property factor calibration** — Weights still heuristic, not empirically validated
5. **LLM-based red flags** — Still regex only
6. **Auth + rate limiting** — API still open (api.py CORS = "*")
7. **Rental area resolution** — Municipality only, not sub-area

---

## Data Inventory

| Source | Records | Coverage | Access |
|---|---|---|---|
| MoJ weekly bulletin (data.gov.qa) | 26,719 | البيع 2020-2026 | ✅ تلقائي |
| Annual sales XLSX (qrep.aqarat.gov.qa) | 37,617 | البيع 2020-2026 | يدوي |
| Rental XLSX (qrep.aqarat.gov.qa) | 360,835 | الإيجار 2023-2026 | يدوي |
| GIS Qatar layers | 9 طبقات | مستمر | ✅ تلقائي |
| MME API (qrepbe.aqarat.gov.qa) | ~8,400 | الشقق + إيجار | ✅ تلقائي |
| Service charge DB | 5 precincts | اللؤلؤة + لوسيل | يدوي |
