"""
test_sprint_2p22p0a2_c3_shawahid_tier_badges.py — Sprint 2.22.0a.2 C3.

Validates the شواهد (evidence) taxonomy relabel of confidence tier badges:
  reliable    → شواهد كافية         (was: موثوق)
  indicative  → شواهد محدودة         (was: إرشادي)
  fallback    → شواهد غير كافية      (was: احتياطي / عينة ضعيفة)

Anas-locked override per resume KICKOFF (GPT-5 preferred شواهد as
native valuation domain term; Anas selected it over CC's original
تغطية draft).

Test scope per audit §3 taxonomy:
  - Category A (tier-badge sites): relabel applied
  - Category B (prose references): updated to quote new label
  - Category C (generic adjectives): UNCHANGED (test guards this)

Standalone test, no pytest dependency.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT))


# Category A — the new tier-badge strings that MUST appear at Category A sites
NEW_LABELS = {
    'reliable':   'شواهد كافية',
    'indicative': 'شواهد محدودة',
    'fallback':   'شواهد غير كافية',
}

# Strings that MUST NOT appear at Category A tier-badge sites (purely
# old-label sites — does NOT include Category C generic adjective usage).
FORBIDDEN_AT_CATEGORY_A_SITES = [
    "'موثوق'",       # land_conf_ar quoted literal
    "'إرشادي'",      # land_conf_ar quoted literal
    "'موثوقة'",      # _PROVENANCE_CONFIDENCE_AR / _GRID_CONFIDENCE_AR
    "'إرشادية'",     # same
    "موثوق (n",      # reliability_label_ar — exact pre-patch fragment
    "إرشادي (n",     # reliability_label_ar — exact pre-patch fragment
    "عينة ضعيفة جداً",  # reliability_label_ar fallback
    "🟢 تقدير موثوق", # accuracy.label (n≥20 cases)
    "🟡 تقدير إرشادي", # accuracy.label (n≥10 case)
]


# ─── Category A: output_briefs.py dicts ───

def test_provenance_confidence_dict_relabeled():
    """_PROVENANCE_CONFIDENCE_AR maps all 3 codes to شواهد taxonomy."""
    import output_briefs as ob
    d = ob._PROVENANCE_CONFIDENCE_AR
    assert d['reliable'] == 'شواهد كافية', d
    assert d['indicative'] == 'شواهد محدودة', d
    assert 'شواهد غير كافية' in d['fallback'], d  # has trailing explanation
    print('  PASS test_provenance_confidence_dict_relabeled')


def test_grid_confidence_dict_relabeled():
    """_GRID_CONFIDENCE_AR maps all 3 codes to شواهد taxonomy."""
    import output_briefs as ob
    d = ob._GRID_CONFIDENCE_AR
    assert d['reliable'] == 'شواهد كافية', d
    assert d['indicative'] == 'شواهد محدودة', d
    assert d['fallback'] == 'شواهد غير كافية', d
    print('  PASS test_grid_confidence_dict_relabeled')


# ─── Category A: stock_strata.py reliability_label_ar builder ───

def test_stock_strata_reliability_label_relabeled():
    """The reliability_label_ar builder emits شواهد taxonomy at all 3 thresholds."""
    import stock_strata as ss
    # Build a fake strata block by importing internals
    src = (REPO_ROOT / 'stock_strata.py').read_text(encoding='utf-8')
    # The builder is an inline f-string — assert the substrings present
    assert 'شواهد كافية (n≥10)' in src, (
        "C3: stock_strata reliability_label_ar must emit 'شواهد كافية (n≥10)' "
        "for reliable tier (RELIABLE_N=10 threshold)"
    )
    assert "'شواهد محدودة (n=' + str" in src, (
        "C3: stock_strata reliability_label_ar must emit 'شواهد محدودة (n=N)' "
        "for indicative tier"
    )
    assert "'شواهد غير كافية'" in src, (
        "C3: stock_strata reliability_label_ar fallback case must emit "
        "'شواهد غير كافية'"
    )
    # Forbidden pre-patch labels
    assert 'موثوق (n≥10)' not in src, "Old 'موثوق (n≥10)' label still present"
    assert 'عينة ضعيفة جداً' not in src, "Old 'عينة ضعيفة جداً' label still present"
    print('  PASS test_stock_strata_reliability_label_relabeled')


# ─── Category A: evaluate_unified.py land_conf_ar + accuracy.label + T2 hybrid ───

def test_evaluate_unified_land_conf_ar_relabeled():
    src = (REPO_ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')
    # The new land_conf_ar assignments
    assert "land_conf_ar = 'شواهد كافية'" in src, "land_conf_ar reliable case"
    assert "land_conf_ar = 'شواهد محدودة'" in src, "land_conf_ar indicative case"
    assert "land_conf_ar = 'شواهد غير كافية'" in src, "land_conf_ar thin/fallback case"
    # Forbidden pre-patch
    assert "land_conf_ar = 'موثوق'" not in src
    assert "land_conf_ar = 'إرشادي'" not in src
    assert "land_conf_ar = 'عينة محدودة'" not in src
    print('  PASS test_evaluate_unified_land_conf_ar_relabeled')


def test_evaluate_unified_accuracy_label_relabeled():
    """accuracy.label (lines ~4095-4109) emits شواهد taxonomy badges."""
    src = (REPO_ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')
    assert "'label': '🟢 شواهد كافية'" in src, "accuracy.label high tier"
    assert "'label': '🟡 شواهد محدودة'" in src, "accuracy.label medium tier"
    # Forbidden pre-patch
    assert "'label': '🟢 تقدير موثوق'" not in src
    assert "'label': '🟡 تقدير إرشادي'" not in src
    print('  PASS test_evaluate_unified_accuracy_label_relabeled')


def test_evaluate_unified_t2_hybrid_badges_relabeled():
    """T2 hybrid accuracy_label (lines ~2049-2079) emits شواهد taxonomy."""
    src = (REPO_ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')
    assert "'🟡 شواهد محدودة عند الحد الأدنى للعينة (T2, n<10)'" in src
    assert "'🟡 شواهد محدودة — مبنية على إعلانات (T2)'" in src
    assert "'🟢 شواهد محدودة — عينة قوية (T2 n≥20)'" in src
    # Forbidden pre-patch
    assert "'🟡 إرشادي عند الحد الأدنى للعينة (T2, n<10)'" not in src
    assert "'🟢 إرشادي قوي — عينة كبيرة (T2 n≥20)'" not in src
    print('  PASS test_evaluate_unified_t2_hybrid_badges_relabeled')


# ─── Category B: prose references quote the new label name ───

def test_category_b_prose_references_updated():
    """Prose sites that explicitly REFERENCE the tier label by name now quote
    the new label. Audit §3 Category B sites:
      - 'للوصول لـ "موثوق"' → 'للوصول لـ "شواهد كافية"' (evaluate_unified.py:2074)
      - 'لتقدير "موثوق"' → 'لتقدير في فئة "شواهد كافية"' (evaluate_unified.py:2241)
      - 'السقف "إرشادي"' → 'السقف "شواهد محدودة"' (evaluate_unified.py:2045, 2069)
      - 'السقف عند "إرشادي"' → 'السقف عند "شواهد محدودة"' (evaluate_unified.py:2075)
    """
    src = (REPO_ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')
    # Positive: new prose references present
    assert 'للوصول لـ "شواهد كافية"' in src, "B: 'للوصول لـ موثوق' update"
    assert 'في فئة "شواهد كافية"' in src, "B: reconciliation 'لتقدير موثوق' update"
    assert 'السقف "شواهد محدودة"' in src, "B: 'السقف إرشادي' update"
    assert 'السقف عند "شواهد محدودة"' in src, "B: 'السقف عند إرشادي' update"
    # Negative: old prose references absent
    assert 'للوصول لـ "موثوق"' not in src, "Category B regression: old prose still present"
    assert 'لتقدير "موثوق"' not in src, "Category B regression"
    assert 'السقف "إرشادي"' not in src, "Category B regression"
    assert 'السقف عند "إرشادي" بدون T1' not in src, "Category B regression"
    print('  PASS test_category_b_prose_references_updated')


# ─── Category C: generic adjective sites UNCHANGED ───

def test_category_c_generic_adjective_sites_unchanged():
    """Per audit §3 Category C, generic adjective usage of موثوق/الموثوقية
    in non-tier-badge contexts must remain UNTOUCHED. The KICKOFF said:
    'Category C generic-adjective sites untouched.'

    Sites:
      - refusal_reason.message_ar: 'مستوى الموثوقية المطلوب' (refusal_templates.py)
      - 'إنتاج تقييم موثوق' / 'تقييم موثوق' (evaluate_unified.py:2380, 2650, 2682)
    """
    eu_src = (REPO_ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')
    rt_src = (REPO_ROOT / 'refusal_templates.py').read_text(encoding='utf-8')
    # Category C: ordinary-adjective usage preserved
    assert 'لتقييم نهائي وموثوق' in eu_src, (
        "Category C site (note_ar): generic adjective 'موثوق' should be "
        "untouched per KICKOFF directive"
    )
    assert 'إنتاج تقييم موثوق' in eu_src, (
        "Category C site (methodology_disclaimer_ar): generic adjective "
        "'موثوق' should be untouched"
    )
    assert 'الموثوقية' in rt_src, (
        "Category C site (refusal_templates.comp_density_sparse): generic "
        "noun 'الموثوقية' should be untouched"
    )
    print('  PASS test_category_c_generic_adjective_sites_unchanged')


def main():
    tests = [
        test_provenance_confidence_dict_relabeled,
        test_grid_confidence_dict_relabeled,
        test_stock_strata_reliability_label_relabeled,
        test_evaluate_unified_land_conf_ar_relabeled,
        test_evaluate_unified_accuracy_label_relabeled,
        test_evaluate_unified_t2_hybrid_badges_relabeled,
        test_category_b_prose_references_updated,
        test_category_c_generic_adjective_sites_unchanged,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print(f'  FAIL {t.__name__}: {e}')
            failed += 1
        except Exception as e:
            print(f'  ERROR {t.__name__}: {type(e).__name__}: {e}')
            failed += 1
    print()
    print(f'Sprint 2.22.0a.2 C3 (شواهد tier badge relabel): '
          f'{len(tests) - failed}/{len(tests)} passed')
    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
