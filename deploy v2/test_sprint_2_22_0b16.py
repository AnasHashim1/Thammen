# -*- coding: utf-8 -*-
# Sprint 2.22.0b.16 — B-2 EARLY slice: V001-anchored old-stock central re-anchor (n=1, disclosed).
# Isolated tests on the PRODUCTION functions (E14 / Rule #40): the pure _old_stock_reanchor firing
# matrix + abstentions + rails + the supersession ladder + guards; subject_geo_full_ppm2 on the REAL
# CSV; threading + UI + precedence presence. No network.
import re
import sys
import pathlib

sys.stdout.reconfigure(encoding='utf-8')
ROOT = pathlib.Path(__file__).parent

from evaluate_unified import (_old_stock_reanchor, OSR_MARGIN_T, OSR_DOM_SHARE_T,
                              OSR_LABEL_AR, OSR_LABEL_EN, OSR_NOTE_AR, ENGINE_VERSION, SPRINT_TAG)
from moj_reference import subject_geo_full_ppm2

results = []
def check(name, cond):
    results.append((name, bool(cond)))

# ── fixtures (the Marikh-shaped measured case, PHASE0_b16_bakeoff §4) ──
PRIM = {'method': 'comparison_thin', 'value': 5_400_000, 'high': 5_500_000}
SGF = {'ppm2_median_full': 5567, 'n_full': 51, 'value_full': 3_412_571, 'bracket': [490, 736]}
COST = {'value': 2_378_094}
LAND = 1_851_260
ARGS = dict(asset_type='standalone_villa', dispersion_gated=False, age=17,
            age_basis='vintage_capped', dom_name='luxury_new', dom_share=51.7,
            plot_area_m2=613.0, user_premium=False)

def fire(**over):
    a = dict(primary=PRIM, sgf=SGF, aging_cell={}, cost=COST, land_floor=LAND, **ARGS)
    a.update(over)
    return _old_stock_reanchor(**a)

# 1-5. THE MOVE (Marikh-shaped): fires with the exact M4 composition.
r = fire()
check('fires on the Marikh class', r is not None)
check('mode = old_stock_reanchor_indicative', r and r['mode'] == 'old_stock_reanchor_indicative')
check('amount = M4 = max(cost, M1c) bounded by comp = 3,412,571', r and r['amount'] == 3_412_571)
check('low = max(land, cost) = the b11 cost floor', r and r['low'] == 2_378_094)
check('high = the thin median (muted upper bound)', r and r['high'] == 5_400_000)
check('MUC high + margin ~58.2%', r and r['muc_level'] == 'high' and 58 <= r['margin_pct'] <= 59)
check('basis = geo_full (aging stratum thin)', r and r['basis']['kind'] == 'geo_full' and r['basis']['n'] == 51)

# 6-7. Supersession ladder rung 1: matching-stratum n>=10 takes precedence over M1c.
r2 = fire(aging_cell={'n': 17, 'median_per_m2': 5289})
check('M2 precedence at stratum n>=10', r2 and r2['basis']['kind'] == 'matching_stratum'
      and r2['basis']['value'] == round(5289 * 613.0))
r3 = fire(aging_cell={'n': 9, 'median_per_m2': 5289})
check('stratum n<10 -> M1c basis (ladder floor)', r3 and r3['basis']['kind'] == 'geo_full')

# 8-10. Materiality margin T=20% (strict >): the V001-shaped convergence ABSTAINS.
v001 = fire(primary={'method': 'comparison_widened', 'value': 3_800_000},
            sgf={'ppm2_median_full': 5058, 'n_full': 22, 'value_full': 3_297_816},
            cost={'value': 3_119_090}, land_floor=2_456_736,
            dom_name='modern_stock', dom_share=80.0, plot_area_m2=652.0)
check('V001-shaped (margin 15.2%) ABSTAINS — converged', v001 is None)
exact = fire(sgf={'ppm2_median_full': 1, 'n_full': 51, 'value_full': 4_500_000})  # margin = 0.20 exactly
check('margin exactly 20% -> abstain (strict >)', exact is None)
just = fire(sgf={'ppm2_median_full': 1, 'n_full': 51, 'value_full': 4_499_000})   # margin just > 20%
check('margin just above 20% -> fires', just is not None)

# 11-18. Exclusions / abstentions (each must return None).
check('dispersion-gated -> abstain', fire(dispersion_gated=True) is None)
check('clean bracket method -> abstain', fire(primary={'method': 'comparison_bracket', 'value': 5_400_000}) is None)
check('land-anchored (land >= comp) -> abstain', fire(land_floor=5_500_000) is None)
check('NOT old (age 5, no vintage cap) -> abstain', fire(age=5, age_basis=None) is None)
check('vintage_capped with age None -> still OLD -> fires', fire(age=None) is not None)
check('user premium (luxury/new/renovated) -> abstain', fire(user_premium=True) is None)
check('dominant share < 40 -> abstain', fire(dom_share=38.7) is None)
check('dominant = aging_stock (not premium) -> abstain', fire(dom_name='aging_stock', dom_share=70.8) is None)
check('asset raw_land -> abstain', fire(asset_type='raw_land') is None)
check('no basis (sgf None + thin stratum) -> abstain cleanly', fire(sgf=None) is None)

# 19-20. M4 composition edges.
no_cost = fire(cost=None)
check('cost None -> basis-only candidate + low = land floor', no_cost and no_cost['amount'] == 3_412_571
      and no_cost['low'] == LAND)
big_cost = fire(cost={'value': 4_000_000})
check('cost > basis -> candidate = cost (M4 max, still < comp)', big_cost and big_cost['amount'] == 4_000_000)

# 21-22. Purity: inputs are never mutated.
prim_copy = dict(PRIM)
fire()
check('primary not mutated (pure)', PRIM == prim_copy)
check('sgf not mutated (pure)', SGF['value_full'] == 3_412_571)

# 23-24. Verbatim signed copy (brief §4) + note formatting.
check('OSR_LABEL_AR verbatim (signed §4)', OSR_LABEL_AR ==
      'إعادة إرساء استرشاديّة لمخزونٍ قديم — معايَرة على تقييم معتمد واحد (V001) + '
      'النافذة الكاملة لوزارة العدل؛ تتحسّن تلقائيّاً مع كلّ صفقة موثَّقة جديدة')
note = OSR_NOTE_AR.format(comp='5,400,000', share=51.7, n=51)
check('note carries comp + dominant share + n (cite-n)', '5,400,000' in note and '51.7' in note and 'n=51' in note
      and 'وسيط العيّنة الخام' in note and 'مدفوعة' not in note)

# 25-26. subject_geo_full_ppm2 on the REAL CSV (E14): reproduces the bake-off M1c exactly.
# Production passes the RESOLVED MoJ area (a18 override: امريخ الجنوبي → مريخ) — mirror that path.
import csv
from evaluate_property import resolve_moj_area_name
with open(ROOT / 'moj_weekly.csv', 'r', encoding='utf-8-sig') as f:
    ROWS = list(csv.DictReader(f))
_resolved = resolve_moj_area_name(ROWS, 'امريخ الجنوبي')
MK_AREA = _resolved[0] if _resolved else 'مريخ'
sgf_real = subject_geo_full_ppm2(ROWS, MK_AREA, 613.0)
check('REAL-CSV M1c Marikh (resolved area) = 5567 ppm2 / n=51 / 3,412,571',
      sgf_real and sgf_real['ppm2_median_full'] == 5567 and sgf_real['n_full'] == 51
      and sgf_real['value_full'] == 3_412_571)
check('n<5 floor -> None (cite-n abstain)', subject_geo_full_ppm2(ROWS, MK_AREA, 60.0) is None)
check('bad plot -> None', subject_geo_full_ppm2(ROWS, MK_AREA, None) is None)

# 27-31. Threading + precedence + UI presence (static pins on the real sources).
EU = (ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')
EP = (ROOT / 'evaluate_property.py').read_text(encoding='utf-8')
HTML = (ROOT / 'index.html').read_text(encoding='utf-8')
check('threading: evaluate_property attaches subject_geo_full',
      "moj_ref_dict['subject_geo_full'] = _sgf" in EP)
check('precedence: b11 emission gated `elif _ct and not _osr:`', 'elif _ct and not _osr:' in EU)
check('emission: elif _osr block present + sets range_is_headline', 'elif _osr:' in EU
      and "output['valuation']['old_stock_reanchor'] = {" in EU)
check('ISS-A07: decomposition + value_floor recomputed + b14 post-pass re-run in the _osr branch',
      '_decomp_osr = _decompose_value(' in EU and '_vf_osr = _villa_value_floor(' in EU)
check('UI renders old_stock_reanchor.note_ar + cost_triangulation.note_ar (t1)',
      'v.old_stock_reanchor&&v.old_stock_reanchor.note_ar' in HTML
      and 'v.cost_triangulation&&v.cost_triangulation.note_ar' in HTML)

# 32-33. Engine version format (R6 — no exact pin) + constants sanity.
check('ENGINE_VERSION format', re.search(r"^thammen-sprint\d+p\d+p\d+", ENGINE_VERSION) is not None)
check('T=0.20 + share 40 + EN label present', OSR_MARGIN_T == 0.20 and OSR_DOM_SHARE_T == 40 and bool(OSR_LABEL_EN))

passed = sum(1 for _, ok in results if ok)
for name, ok in results:
    print(('PASS' if ok else 'FAIL'), '-', name)
print('\n%d/%d passed' % (passed, len(results)))
assert passed == len(results), '%d FAILED' % (len(results) - passed)
