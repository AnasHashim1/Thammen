"""
test_sprint_2p22p0a_a2_documentation.py — Sprint 2.22.0a/11 documentation guard

Verifies the BRIEF v2 §4.5 audit-PIN row A2 in `CHANGELOG_pre_2p22p0_v2.md`
matches the audit-recommended text from `AUDIT_FINDINGS_2p22p0.md` (§4.5.a
finding #8 + line 379). The row was mislabeled "Villa" through v1; Sprint
2.22.0a/11 corrected it to "apartment_building (DCF refusal — canonical
apt-Stage-2 case)" verbatim per the audit recommendation.

Regression guard purpose: catches silent revert of the data fix if a
future edit (or autotool / merge) re-introduces "Villa" or otherwise
drops the canonical wording.

Standalone runner per CLAUDE.md convention; uses shared Reporter from
`_test_helpers` (Sprint 2.22.0a/10).

Run:
    python test_sprint_2p22p0a_a2_documentation.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Sprint 2.22.0a/10 — shared test infrastructure (Anas Q1.5: generic name)
from _test_helpers import Reporter, set_stdout_utf8

set_stdout_utf8()

_REPORTER = Reporter()
_check = _REPORTER.check


# ──────────────────────────────────────────────────────────────────────
# Locate + read CHANGELOG_pre_2p22p0_v2.md §4.5 row A2
# ──────────────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_DOC_PATH = os.path.join(_HERE, '2p22p0_pre', 'CHANGELOG_pre_2p22p0_v2.md')

print('\n[setup] Reading audit-PIN row A2 from CHANGELOG_pre_2p22p0_v2.md §4.5')
_check(os.path.isfile(_DOC_PATH),
       f'CHANGELOG_pre_2p22p0_v2.md exists at {_DOC_PATH}')

with open(_DOC_PATH, encoding='utf-8') as f:
    content = f.read()

# Locate §4.5 audit PINs table and extract row A2
# Row format: `| A2 | <PIN> | <Asset> | <Why> |`
import re
section_start = content.find('### 4.5 Audit PINs')
_check(section_start >= 0, '§4.5 "Audit PINs" section header found')

section_after = content[section_start:]
# Match a line starting with `| A2 |`
row_match = re.search(r'^\|\s*A2\s*\|.*$', section_after, re.MULTILINE)
_check(row_match is not None, '§4.5 row A2 located')

row_a2 = row_match.group(0) if row_match else ''
print(f'\n[setup] Row A2 text:\n  {row_a2}')


# ──────────────────────────────────────────────────────────────────────
# [1] A2 row contains the canonical asset_type — must say apartment_building
# ──────────────────────────────────────────────────────────────────────
print('\n[1] A2 row contains the canonical classification (apartment_building)')
_check('apartment_building' in row_a2,
       "Row A2 contains 'apartment_building' (production engine classification)")

# ──────────────────────────────────────────────────────────────────────
# [2] A2 row does NOT contain the legacy mislabel "Villa"
# ──────────────────────────────────────────────────────────────────────
print('\n[2] A2 row does NOT contain the legacy mislabel "Villa"')
_check('Villa' not in row_a2,
       "Row A2 does NOT contain 'Villa' (legacy v1 mislabel — must stay corrected)")

# ──────────────────────────────────────────────────────────────────────
# [3] A2 row preserves the PIN identifier 52/903/90
# ──────────────────────────────────────────────────────────────────────
print('\n[3] A2 row preserves the PIN identifier (52/903/90)')
_check('52/903/90' in row_a2,
       "Row A2 contains '52/903/90' (canonical apt-Stage-2 PIN preserved)")

# ──────────────────────────────────────────────────────────────────────
# [4] A2 row contains the full audit-findings recommendation text
# ──────────────────────────────────────────────────────────────────────
print('\n[4] A2 row contains the full audit-findings recommendation text')
# Per AUDIT_FINDINGS_2p22p0.md line 379:
#   "apartment_building (DCF refusal — canonical apt-Stage-2 case)"
_canonical = 'apartment_building (DCF refusal — canonical apt-Stage-2 case)'
_check(_canonical in row_a2,
       f"Row A2 contains the canonical audit-recommended text: "
       f"'{_canonical}'")

# ──────────────────────────────────────────────────────────────────────
# [5] A2 row preserves the original "Why" column intent (Bug A6 known-safe)
# ──────────────────────────────────────────────────────────────────────
print('\n[5] A2 row preserves the original "Why" column intent')
_check('Bug A6 known-safe' in row_a2,
       "Row A2 preserves the 'Bug A6 known-safe' rationale (purpose unchanged)")
_check('Safe smoke' in row_a2,
       "Row A2 preserves 'Safe smoke' qualifier")

# ──────────────────────────────────────────────────────────────────────
# [6] Amendment provenance note present (Sprint 2.22.0a/11 audit trail)
# ──────────────────────────────────────────────────────────────────────
print('\n[6] Amendment provenance note present immediately after the table')
_check('Amendment (Sprint 2.22.0a/11' in section_after,
       'Provenance note cites Sprint 2.22.0a/11')
_check('AUDIT_FINDINGS_2p22p0.md' in section_after[:5000],
       'Provenance note cites AUDIT_FINDINGS_2p22p0.md source')
_check('apartment_building' in section_after[:5000],
       'Provenance note re-asserts the corrected classification')


# ──────────────────────────────────────────────────────────────────────
# Summary — Sprint 2.22.0a/10 unified via _test_helpers.Reporter
# ──────────────────────────────────────────────────────────────────────
sys.exit(_REPORTER.report())
