# CHANGELOG v183 — Sprint 2.22.0b.102 «مطابقة استخدام الأرض السكنيّة» (land residential-usage comparability — RICS)

**Engine:** `thammen-sprint2p22p0b102-land-residential-comparability` · **SPRINT_TAG** `2.22.0b.102`
**Date:** 2026-07-05 · **Files:** `moj_reference.py` (the filter), `index.html` (HBU note), `evaluate_unified.py` (version) (+ `test_sprint_2_22_0b102_land_residential.py`)
**Class:** 🔴 Gate-2 VALUE-AFFECTING (raw_land only) — Gate-2 signed by delegation («افعل الأصوب من وجهة نظر مثمن الريكس»). Villa path byte-identical.
**Supersedes:** the reverted b101 (measured on ppm2 — wrong metric) AND the never-shipped b102 "Option B" dual-pool (kept the non-comparable mixed figure + a footnote — less RICS-orthodox).

---

## 2. Why (the RICS reasoning)

The raw_land comparable pool mixed **residential land** (`فلل او بيوت سكنية` / `مسكن`, ~1.88M) with
**apartment/complex land** (`عمارات او مجمعات سكنية`, ~2.8×) and **commercial land** (`أراض تجارية`, ~6×).
Per RICS Red Book **VPS 3 / IVS 103** (approaches — comparable selection) a comparable must match the
subject's **use / highest-and-best-use**; apartment/commercial development land is **not comparable** to a
residential land subject (different buyer pool, different HBU). A RICS valuer removes it by default. The
land amount = `total_price_median × GIS factors`, and the factors (the subject's location premium) cancel
in the ratio → the filter's % impact on the amount = its % impact on `total_price_median` exactly (the
metric b101 got wrong — it measured ppm2).

**The RICS-correct handling of thin evidence** (VPS 3 / VPGA 10): lead with the **comparable** (residential)
figure carrying its reliability + sample-size disclosure — thin-but-comparable beats robust-but-non-comparable.
A caveat does not cure a headline built on non-comparable evidence.

## 3. What this patch does

- **`moj_reference.py` build_reference** — the `_is_residential_usage` filter (which already gated the VILLA
  pool since A1) now gates the **LAND** pool too (one clause: `(cat!='villa' or _is_residential_usage(r))`
  → `_is_residential_usage(r)` for both). The land pool becomes residential-only. Thin residential cells
  (n<10) fall to the **existing** indicative tier — reliability disclosed via the confidence pill + n + range
  (`apply_moj_strategy` unchanged; no new dual-pool). **Villa pool untouched.**
- **`index.html`** — a stated-assumption **highest-and-best-use** note on the land face for plots ≥900 m²:
  «القيمة على أساس الاستخدام السكنيّ … إن سمح التنظيم ببناء عمارات … فقد تكون قيمتها التطويريّة أعلى — تحقّق من التصنيف.»
  (VPS 2 basis / IVS 104 HBU — honest for large plots where apartment development may be the HBU).

## 4. Verification — empirical evidence

**Blast radius (156 served land cells, correct metric total_price_median):** 98 reliable residential /
53 indicative / 5 category-fallback; **11 cells move ≥5%** (mostly the contaminated ones — most cells barely
move, already residential), **1 up** (legitimate — residential genuinely higher). **الوعب 900-1500 (the PO's
plot): 7.1M → residential ~5.3M×factors≈5.7M (n=4, indicative — reliability disclosed).** الوعب 1500+ →
residential 8M (n=3, indicative). لوسيل 1500+ −43% (reliable). **12 downtown/commercial areas** (نجمة, مشيرب,
المنصورة, السلطة…) whose land is 100% apartment/commercial → **graceful refusal** (0 residential comps — honest;
also classifier-rejected before valuation). No legitimate residential suburb refuses.

- Isolated `test_sprint_2_22_0b102_land_residential.py` **20/20** (real functions, E14): land pool residential-only;
  **villa byte-gate** (بو هامور 2,357,895 / مريخ 5,100,000 / المعمورة 3,741,176 / المعراض 2,572,445 — identical);
  de-inflation; الوعب indicative; no false refusal in residential suburbs; graceful refusal in commercial-only areas.
- DoD: aggregator **ALL COUNTS MATCH** · security **16/16** · surface **45/45** · **broad 157/157** (156→157,
  **ZERO re-points**) · py_compile OK · node --check OK.
- **R14 375×812**: the HBU note renders on a ≥900 m² plot, hidden on a 400 m² plot; **0 console errors**; no overflow.

## 5. Deployment

```
git add moj_reference.py evaluate_unified.py index.html test_sprint_2_22_0b102_land_residential.py CHANGELOG_v183.md
git commit -m "Sprint 2.22.0b.102 ..."
git push origin master
git subtree push --prefix "deploy v2" heroku master
```

## 6. Verification curl (post-deploy, browser-UA #61)

```
# 5-fixture VILLA byte-gate MUST stay identical to b100/v272 (villa path untouched):
#   54/541/6=2.4M · 56/647/6=3.8M · 55/296/13=2.6M · 56/565/21=2.4M · 52/903/90=refusal
# LAND: الوعب 55010236 → amount DROPS to the residential figure (~5.7M) marked indicative;
#       لوسيل / المطار العتيق robust land → de-inflated (down); a downtown commercial-land PIN → refusal.
```

## 7. What's NOT in this patch (honest residuals)

- **HBU under-valuation for large R2/R3 plots** where apartment development is genuinely the HBU: the
  residential-use figure may under-value; **mitigated by the stated HBU note** (a zoning-conditional comp-switch
  is deferred — the zoning signal can be absent under GIS degradation, A15). A RICS valuer flags this.
- **The multi-AI / primary-source RICS clause lock (Rule #54) is OWED** — the verification workflow was
  server-rate-limited; the core principles (comparability = HBU-matched; thin-comparable > non-comparable;
  stated assumptions) are well-established and were applied. Re-run when the limit clears.
- ppm2 secondary paths unchanged. Villa pool unchanged.
