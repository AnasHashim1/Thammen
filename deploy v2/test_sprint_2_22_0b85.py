# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.85 — EN twins for the STOCK-STRATIFICATION card (stock_strata.py).
E14: exercises the REAL compute_strata + classify_subject_property + asserts the static
top-level strings the module returns. BACKEND-ONLY / VALUE-INVARIANT — additive `*_en`
keys alongside the `*_ar`; EN dormant (frontend reads via pick() when LANG=='en', b77).

Sprint 2.22.0b.100 re-point (R6/Lesson-2): the strata labels/descriptions became
PRICE-POSITION (measured ratio band; the age/finish inference moved to the descriptions,
flagged «inferred from price»). AR + EN updated IN LOCKSTEP; the value-math (n /
median_per_m2 / estimated_total), the reliability labels, and the pick() wiring are
UNCHANGED — the b85 contract (twins exist + AR/EN lockstep + value-invariance) holds."""
import io
import stock_strata as ss

passed = failed = 0
def check(name, cond):
    global passed, failed
    if cond: passed += 1; print('  ok  ', name)
    else:    failed += 1; print('  FAIL', name)

# ── (1) EN label/desc maps (b100 price-position) ──
check('STRATUM_LABELS_EN complete (4, price-position)',
      ss.STRATUM_LABELS_EN == {'land_priced': 'Land-priced', 'aging_stock': 'Near land price',
                               'modern_stock': 'Mid price tier', 'luxury_new': 'Top price tier'})
check('STRATUM_DESC_EN complete (4) + luxury mentions weak sample + price-inference',
      set(ss.STRATUM_DESC_EN) == {'land_priced', 'aging_stock', 'modern_stock', 'luxury_new'}
      and 'n<5' in ss.STRATUM_DESC_EN['luxury_new']
      and 'inferred from price' in ss.STRATUM_DESC_EN['luxury_new'])
check('AR maps in lockstep (price-position label + price-inference desc)',
      ss.STRATUM_LABELS_AR['luxury_new'] == 'الشريحة الأعلى سعراً'
      and 'استدلالاً بالسعر' in ss.STRATUM_DESC_AR['aging_stock'])

# ── (2) compute_strata emits per-stratum _en (real call) ──
land_med = 3000.0
# 12 aging (ratio 1.3 → 3900), 4 luxury (ratio 2.5 → 7500)
txns = [{'price_m2': 3900}] * 12 + [{'price_m2': 7500}] * 4
strata = ss.compute_strata(txns, land_med, 500)
ag = strata['aging_stock']; lx = strata['luxury_new']
check('compute_strata: aging label_en + price-inference description_en (dominant, reliable)',
      ag['label_en'] == 'Near land price' and 'inferred from price' in ag['description_en'] and ag['n'] == 12)
check('compute_strata: reliability_label_en reliable→Sufficient (n≥10) [UNCHANGED]',
      ag['reliability_label_en'] == 'Sufficient evidence (n≥10)')
check('compute_strata: luxury reliability_label_en limited carries n + label_en',
      lx['reliability_label_en'] == 'Limited evidence (n=4)' and lx['label_en'] == 'Top price tier')
check('compute_strata: AR label lockstep + reliability_label_ar UNCHANGED',
      ag['label_ar'] == 'قريبة من سعر الأرض' and ag['reliability_label_ar'] == 'شواهد كافية (n≥10)'
      and lx['reliability_label_ar'] == 'شواهد محدودة (n=4)')
check('compute_strata: value-math untouched (n + median_per_m2 + estimated_total)',
      ag['median_per_m2'] == 3900 and ag['estimated_total'] == round(3900 * 500))

# ── (3) classify_subject_property emits _en (real call) ──
sp = ss.classify_subject_property(3900 * 500, 500, land_med)  # ratio 1.3 → aging_stock
check('classify_subject: classification_label_en (price-position)',
      sp['classification'] == 'aging_stock' and sp['classification_label_en'] == 'Near land price')
check('classify_subject: guidance_en present + references the EN label + "category"',
      'Near land price' in sp['guidance_en'] and 'category' in sp['guidance_en'])
check('classify_subject: AR label lockstep + guidance_ar prefix UNCHANGED',
      sp['classification_label_ar'] == 'قريبة من سعر الأرض'
      and sp['guidance_ar'].startswith('سعر العقار الذي أدخلته'))

# ── (4) build_stock_strata_result top-level static EN twins present (module source) ──
SRC = io.open('stock_strata.py', encoding='utf-8').read()
check('methodology_en returned (module) + cites the price/land-median method + inference framing',
      "'methodology_en'" in SRC and 'relative to the area land' in SRC and 'not an inspection of them' in SRC)
check('dominant_stratum note_en returned', "'note_en'" in SRC and 'category dominating the area sample' in SRC)
check('sprint_scope_caveat_en returned', "'sprint_scope_caveat_en'" in SRC and 'additional transparency' in SRC)
check('AR top-level UNCHANGED (methodology_ar/caveat_ar present)',
      "'methodology_ar'" in SRC and "'sprint_scope_caveat_ar'" in SRC and 'كل معاملة فيلا تُصنَّف' in SRC)

# ── (5) frontend wiring intact (index.html reads these via pick — unchanged from b83) ──
HTML = io.open('index.html', encoding='utf-8').read()
check('frontend reads pick() strata fields',
      "pick(stockStrata,'methodology')" in HTML and "pick(s,'label')" in HTML
      and "pick(s,'reliability_label')" in HTML and "pick(s,'description')" in HTML
      and "pick(sp,'classification_label')" in HTML and "pick(sp,'guidance')" in HTML
      and "pick(stockStrata.dominant_stratum,'label')" in HTML
      and "pick(stockStrata.dominant_stratum,'note')" in HTML)

print('\nb85:', passed, 'passed,', failed, 'failed')
raise SystemExit(1 if failed else 0)
