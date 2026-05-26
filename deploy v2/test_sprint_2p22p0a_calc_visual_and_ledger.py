"""Sprint 2.22.0a/8 — isolated tests for calculator-style visual + adjustment_ledger_directional.

Coverage:
  [1]  _adjustment_ledger_directional_section helper basics
  [2]  refusal-gating (returns None when refusal path active) — mirrors /4 + /5 pattern
  [3]  None / empty evaluation handling
  [4]  Content shape (id, title_ar, content dict, placeholder marker)
  [5]  Copy fidelity — pure Arabic note_ar (no Latin chars except "&"), no internal sprint
       nomenclature (e.g. "Sprint 2.22.0b" / "Stage 2 Q&A" / "v2") surfaced to user
  [6]  4 audience briefs (buyer/seller/investor/valuer) — section at position 4
       (after refusal_reason / tier_breakdown / use_case_banner) on value-producing path
  [7]  4 audience briefs — section ABSENT on refusal path
  [8]  Frontend: `.calc-block` CSS class applied exactly once to valuation card in index.html
  [9]  Frontend: SEC_ICONS contains 'adjustment_ledger_directional' entry
 [10]  Frontend: renderSection switch contains case for 'adjustment_ledger_directional'
 [11]  Frontend: CSS rules defined for `.calc-block`, `.calc-block .rv`, `.calc-block .ri`,
       `.alg-placeholder-badge`, `.alg-placeholder-note`
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Module under test
from output_briefs import (
    _adjustment_ledger_directional_section,
    _buyer_brief,
    _seller_brief,
    _investor_brief,
    _valuer_brief,
)

PASS = 0
FAIL = 0
FAILED = []


def check(name: str, cond: bool) -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f'  PASS  {name}')
    else:
        FAIL += 1
        FAILED.append(name)
        print(f'  FAIL  {name}')


# ──────────────────────────────────────────────────────────────────────
# Helpers for test fixtures
# ──────────────────────────────────────────────────────────────────────
def _eval_value_producing():
    return {
        'asset_type': 'standalone_villa',
        'address': '52/903/90',
        'valuation_date': '2026-05-26',
        'valuation': {'amount': 5_000_000, 'method': 'comparison_bracket'},
        'material_uncertainty': {'level': 'low', 'banner_ar': 'manageable'},
    }


def _eval_refusal_insufficient():
    return {
        'asset_type': 'compound_large',
        'address': '51/835/17',
        'valuation_date': '2026-05-26',
        'valuation': {'amount': None, 'method': 'insufficient_data'},
        'refusal_reason': {'trigger_id': 'asset_scale_extreme'},
        'material_uncertainty': {'level': 'critical', 'banner_ar': 'no comparable'},
    }


def _eval_refusal_out_of_scope():
    return {
        'asset_type': 'commercial',
        'address': '53/240/12',
        'valuation_date': '2026-05-26',
        'valuation': {'amount': None, 'method': 'out_of_scope_v1'},
        'refusal_reason': {'trigger_id': 'asset_class_out_of_scope'},
        'material_uncertainty': {'level': 'critical', 'banner_ar': 'out of scope'},
    }


# ──────────────────────────────────────────────────────────────────────
# [1] Helper basics
# ──────────────────────────────────────────────────────────────────────
print('\n[1] _adjustment_ledger_directional_section — happy path returns dict')
ev = _eval_value_producing()
sec = _adjustment_ledger_directional_section(ev)
check('section dict returned on value-producing evaluation', isinstance(sec, dict))
check("section.id == 'adjustment_ledger_directional'",
      sec.get('id') == 'adjustment_ledger_directional')
check("section.title_ar == 'سجل التعديلات الاتجاهية'",
      sec.get('title_ar') == 'سجل التعديلات الاتجاهية')
check('section.content is dict', isinstance(sec.get('content'), dict))

# ──────────────────────────────────────────────────────────────────────
# [2] Refusal-gating (returns None on 3 distinct refusal methods)
# ──────────────────────────────────────────────────────────────────────
print('\n[2] Refusal-gating — returns None on refusal paths')
check('insufficient_data → None',
      _adjustment_ledger_directional_section(_eval_refusal_insufficient()) is None)
check('out_of_scope_v1 → None',
      _adjustment_ledger_directional_section(_eval_refusal_out_of_scope()) is None)
ev_reality_stop = {
    'asset_type': 'unknown',
    'address': 'أرض في الدفنة — PIN 12345',
    'valuation_date': '2026-05-26',
    'valuation': {'amount': None, 'method': 'asset_type_reality_stop'},
    'refusal_reason': {'trigger_id': 'spatial_ambiguity'},
}
check('asset_type_reality_stop → None',
      _adjustment_ledger_directional_section(ev_reality_stop) is None)

# ──────────────────────────────────────────────────────────────────────
# [3] None / empty evaluation handling
# ──────────────────────────────────────────────────────────────────────
print('\n[3] None / empty evaluation handling')
check('None evaluation → None',
      _adjustment_ledger_directional_section(None) is None)
check('Empty dict evaluation → None',
      _adjustment_ledger_directional_section({}) is None)

# Unknown method (defensive): _tier_label_for returns None → section returns None
ev_unknown_method = {
    'asset_type': 'standalone_villa',
    'address': '52/903/90',
    'valuation_date': '2026-05-26',
    'valuation': {'amount': None, 'method': '__bogus_method__'},
}
check('Unknown method → None (mirrors /4 defensive symmetry)',
      _adjustment_ledger_directional_section(ev_unknown_method) is None)

# ──────────────────────────────────────────────────────────────────────
# [4] Content shape — id, title_ar, note_ar/en, placeholder marker
# ──────────────────────────────────────────────────────────────────────
print('\n[4] Content shape')
content = sec['content']
check('content.note_ar present and non-trivial',
      isinstance(content.get('note_ar'), str) and len(content['note_ar']) > 20)
check('content.note_en present and non-trivial',
      isinstance(content.get('note_en'), str) and len(content['note_en']) > 20)
check('content.placeholder == True (marker for /12 scan)',
      content.get('placeholder') is True)

# ──────────────────────────────────────────────────────────────────────
# [5] Copy fidelity — pure Arabic note_ar, no internal sprint nomenclature
# ──────────────────────────────────────────────────────────────────────
print('\n[5] Copy fidelity (Anas Q2 refinement)')
note_ar = content['note_ar']

# Latin character check: Arabic copy should contain no Latin letters
# (digits, spaces, and punctuation are OK; "&" is excluded by Q2 spec since
# we removed "Stage 2 Q&A" entirely — but defensively check the Q2 refinement
# explicitly drops Latin "Stage", "Q", "&", etc.)
latin_chars = re.findall(r'[A-Za-z]', note_ar)
check('note_ar contains zero Latin letters', len(latin_chars) == 0)

# No internal sprint nomenclature surfaced to user
check("note_ar does NOT contain 'Sprint'", 'Sprint' not in note_ar)
check("note_ar does NOT contain '2.22.0b'", '2.22.0b' not in note_ar)
check("note_ar does NOT contain 'Stage 2'", 'Stage 2' not in note_ar)
check("note_ar does NOT contain 'Q&A' Latin form", 'Q&A' not in note_ar)
check("note_ar does NOT contain Latin '&'", '&' not in note_ar)

# Production-facing language: "قريباً" + "مرحلة الأسئلة التفاعلية"
check("note_ar contains 'قريباً'", 'قريباً' in note_ar)
check("note_ar contains 'الأسئلة التفاعلية'", 'الأسئلة التفاعلية' in note_ar)

# English copy can have Latin (it's English), but should also avoid internal nomenclature
note_en = content['note_en']
check("note_en does NOT contain 'Sprint'", 'Sprint' not in note_en)
check("note_en does NOT contain '2.22.0b'", '2.22.0b' not in note_en)
check("note_en contains 'interactive Q&A'", 'interactive Q&A' in note_en)

# ──────────────────────────────────────────────────────────────────────
# [6] 4 audience briefs — section at position 4 on value-producing
# ──────────────────────────────────────────────────────────────────────
print('\n[6] 4 audience briefs — section at position 4 on value-producing')
ev_v = _eval_value_producing()

# Expected position-4 ordering (1-indexed):
#   1. refusal_reason         (gated OFF here — value-producing path)
#   2. tier_breakdown         (gated OFF here — no hybrid evidence in fixture)
#   3. use_case_banner        (present — non-refusal)
#   4. adjustment_ledger_directional (NEW — present, non-refusal)
# So on this fixture, use_case_banner is sections[0] and ledger is sections[1].

for audience, brief_fn in (('buyer', _buyer_brief), ('seller', _seller_brief),
                            ('investor', _investor_brief), ('valuer', _valuer_brief)):
    brief = brief_fn(ev_v, rent_data=None, adjustments=None,
                     uncertainty={'level': 'low', 'banner_ar': 'low'},
                     income_value=None)
    sections = brief.get('sections', [])
    ids = [s.get('id') for s in sections]
    # use_case_banner is at sections[0]; adjustment_ledger_directional at sections[1]
    has_ub = 'use_case_banner' in ids
    has_al = 'adjustment_ledger_directional' in ids
    check(f'[{audience}] use_case_banner present', has_ub)
    check(f'[{audience}] adjustment_ledger_directional present', has_al)
    if has_ub and has_al:
        ub_idx = ids.index('use_case_banner')
        al_idx = ids.index('adjustment_ledger_directional')
        check(f'[{audience}] adjustment_ledger_directional immediately AFTER use_case_banner',
              al_idx == ub_idx + 1)

# ──────────────────────────────────────────────────────────────────────
# [7] 4 audience briefs — section ABSENT on refusal path
# ──────────────────────────────────────────────────────────────────────
print('\n[7] 4 audience briefs — section ABSENT on refusal path')
ev_r = _eval_refusal_insufficient()
for audience, brief_fn in (('buyer', _buyer_brief), ('seller', _seller_brief),
                            ('investor', _investor_brief), ('valuer', _valuer_brief)):
    brief = brief_fn(ev_r, rent_data=None, adjustments=None,
                     uncertainty={'level': 'critical', 'banner_ar': 'crit'},
                     income_value=None)
    sections = brief.get('sections', [])
    ids = [s.get('id') for s in sections]
    check(f'[{audience}] adjustment_ledger_directional ABSENT on refusal',
          'adjustment_ledger_directional' not in ids)
    check(f'[{audience}] use_case_banner ALSO absent (refusal-gated)',
          'use_case_banner' not in ids)
    check(f'[{audience}] refusal_reason present (refusal path)',
          'refusal_reason' in ids)

# ──────────────────────────────────────────────────────────────────────
# [8] Frontend grep — `.calc-block` class applied to valuation card
# ──────────────────────────────────────────────────────────────────────
print('\n[8] Frontend grep — calc-block class on valuation card')
index_html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')
with open(index_html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Count distinct application sites (the class string in CSS selectors doesn't count)
# We look for the JS template string `class="rc calc-block"` — this is the application.
applications = html.count('class="rc calc-block"')
check('"class=\\"rc calc-block\\"" appears exactly once (valuation card only)',
      applications == 1)
check('"calc-block" CSS selector present', '.calc-block{' in html)
check('".calc-block .rv" CSS selector present (monospace scoped to numeric values)',
      '.calc-block .rv{' in html)
check('".calc-block .ri" CSS selector present (inner-bg invert for contrast)',
      '.calc-block .ri{' in html)
check('@media (max-width:480px) responsive rule for calc-block present',
      '.calc-block' in html and 'max-width:480px' in html)
check('monospace font-family declared in calc-block .rv', 'ui-monospace' in html)
check('tabular-nums declared (font-feature-settings or font-variant-numeric)',
      '"tnum"' in html or 'tabular-nums' in html)

# ──────────────────────────────────────────────────────────────────────
# [9] Frontend grep — SEC_ICONS entry for adjustment_ledger_directional
# ──────────────────────────────────────────────────────────────────────
print('\n[9] Frontend grep — SEC_ICONS entry')
check("SEC_ICONS contains 'adjustment_ledger_directional' key",
      "'adjustment_ledger_directional':" in html)

# ──────────────────────────────────────────────────────────────────────
# [10] Frontend grep — renderSection switch case for adjustment_ledger_directional
# ──────────────────────────────────────────────────────────────────────
print('\n[10] Frontend grep — renderSection switch case')
check("renderSection has case 'adjustment_ledger_directional'",
      "case 'adjustment_ledger_directional':" in html)
check("Render renders 'قريباً' badge", 'قريباً' in html)
check('Placeholder badge CSS class present', '.alg-placeholder-badge{' in html)
check('Placeholder note CSS class present', '.alg-placeholder-note{' in html)

# ──────────────────────────────────────────────────────────────────────
# [11] Frontend grep — CSS rules for badge + note
# ──────────────────────────────────────────────────────────────────────
print('\n[11] Frontend grep — CSS rules for placeholder badge + note')
check('Badge has muted color treatment', '.alg-placeholder-badge{' in html
      and 'color:var(--muted)' in html)
check('Note has muted color + line-height',
      '.alg-placeholder-note{' in html and 'line-height:1.8' in html)

# ──────────────────────────────────────────────────────────────────────
# Summary
# ──────────────────────────────────────────────────────────────────────
print()
print('=' * 60)
print(f'  PASSED: {PASS}/{PASS + FAIL}')
print(f'  FAILED: {FAIL}/{PASS + FAIL}')
print('=' * 60)
if FAIL:
    print('\nFAILED ASSERTIONS:')
    for name in FAILED:
        print(f'  - {name}')
    sys.exit(1)
sys.exit(0)
