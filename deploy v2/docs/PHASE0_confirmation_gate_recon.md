# PHASE 0 — Confirmation Gate (v4 owner-journey, Screen 2) recon

> **Read-only. NO engine change, NO deploy.** Live base = b2.2 / Heroku **v168** (engine `…b2p2`).
> Brief = Gate-2 **DRAFT** «Confirmation Gate» (Claude.ai lane, unsigned — 3 §5 sub-decisions + copy pending Anas).
> Binding design = `DESIGN_2p2x_v4_owner_journey.md` + mockup `docs/thammen_owner_flow_mockup.html` (v4 wins on conflict).
> Probe = live `POST /api/evaluate {56,565,21}` (browser-UA, Rule #61) → HTTP 200, engine b2.2.
> Done under the «افعل الأصوب» delegation; **build HELD on the Gate-2 signature** (Screen 2 changes what the user sees/does).

## 1. LOAD-BEARING finding — frontend-only CONFIRMED (no Soft-Gate-3)
The brief's single contingency — *"if the preliminary-range datum isn't already in `/api/evaluate` → Soft-Gate-3, don't add valuation logic silently"* — is **CLEARED**. The live 56/565/21 response carries, **client-side already**, every datum Screen 2 needs:

| Screen-2 element | response field (live value, 56/565/21) |
|---|---|
| preliminary range (low–high) | `valuation.low` = **2,200,000** · `valuation.high` = **2,600,000** |
| median (muted «الوسيط») | `valuation.amount` = **2,400,000** |
| asset type (E7/A11 catch) | `asset_type` = `standalone_villa` |
| area name | `district` = «بو هامور» |
| plot area | `plot_area_m2` = **450.0** |
| zoning hint | `valuation.geometry.zone_max_coverage_pct` = **60** (→ R1) |
| zone / street / building | the user's own form inputs (already client-side) |
| evidence panel (4 comp.) | already rendered (b.2.2) from `accuracy.tier`, `moj_sample_size`, `data_freshness`, `valuation.geometry.footprint_basis` |

⟹ Screen 2 reads **only** fields the client already holds. **No valuation logic, no new backend field. `api.py` + `evaluate_unified.py` UNTOUCHED.** The brief's value-invariant claim HOLDS.

## 2. Flow-insertion point (current → with Screen 2)
Current `index.html`: `homeScreen` (:337) → `formScreen` identification (:366) → `run()` (:670) `POST /api/evaluate` → `show(d)` (:879) → `resultsScreen` (:468); `refineScreen` (:414) reached from the results card (b.2.1/b.2.2). Switcher = `go(n)` (:509); `goForm` (:530).
**Insertion:** `run()` fetches → render the **NEW confirm step from the SAME response object** (range + review card + evidence panel + confirm CTA + «التقرير الكامل الآن») → **explicit confirm** → proceed. **No second fetch** — the full response is already in hand.
Cleanest realization (Rule #39, matches the b.2.1 separate-screen pattern + v4's «على مراحل، ليس في نافذة واحدة»): a dedicated **`confirmScreen`** (new 4th `.screen`) inserted between `formScreen` and the result. Whether "proceed" lands on `refineScreen` (Screen 3) or `resultsScreen` first is the v4 ordering call (v4 = تعريف → تأكيد → تحسين → نتيجة) → confirm → **refine**. Final shape = build detail against v4.

## 3. Mockup ↔ brief divergence — FLAG (feeds §5.2)
Mockup Screen 2 renders ✏ correction pencils on every review row **and** an «✎ صحّح» button. Brief §5.2 **DEFERS correction** (read-only this sprint; correction = its own micro-sprint, #38). v4/mockup bind layout, but the brief explicitly scopes correction OUT.
→ **Resolve in §5.2:** recommend **read-only this sprint → review card WITHOUT pencils + confirm with only «✓ نعم، تابع»** (omit «✎ صحّح» until the correction micro-sprint), so the UI never offers an action it can't perform. The mockup pencils are design-intent for that LATER sprint.

## 4. CC recommendations on the §5 Gate-2 sub-decisions (Anas signs)
- **5.1 range placement → ALONGSIDE the review card, muted.** Matches mockup `.est` («تقدير مبدئي / ٢٫١–٢٫٧ / الوسيط ≈ ٢٫٤م») sitting above the review card — basis + provisional range seen together. Concur with the brief.
- **5.2 correction → READ-ONLY this sprint** (per §3); correction = separate micro-sprint. Concur with the brief.
- **5.3 copy → DRAFT strings OK as-is** (Arabic-primary + EN mirror); register matches the mockup. Keep «تقدير مبدئي (نطاق)» consistent with the live frame «تقدير إرشادي غير رسمي». Final wording = Anas's Gate-2 copy call.

## 5. Boundaries confirmed (no regression)
- **B-1 `value_floor` IS in the response** (`valuation.value_floor.*`, `value_decomposition.*`) but **STAYS OUT of Screen 2** (brief §3 — this was the b.2.2 first-error, already corrected). It belongs to Screen 4/report. Recon confirms present-but-not-surfaced-here.
- **Evidence panel** (b.2.2) already lives in the results render → Screen 2 **reuses** it (no new logic).
- **RICS/IVS notes, `methodology_ar`, disclaimers** — UNCHANGED (in response; rendered on the report screen).

## 6. Disposition
**Frontend-only / value-invariant CONFIRMED.** Build **HELD on Anas's Gate-2 signature** (the 3 §5 sub-decisions + copy). On signature → CC builds against v4 + mockup (production theme variables + Tajawal — **not** the mockup's IBM Plex / `--teal`/`--ink`/`--paper`; RICS/IVS + disclaimers from production/v4, not the mockup's abbreviations), with R14 real-Chromium (node absent → Chromium is the JS gate) + 4-anchor byte-identical baseline + DoD. **Ball after signature = CC builds; ball now = Anas signs.**
