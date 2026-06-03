# -*- coding: utf-8 -*-
"""
Sprint 2.22.0a.17 — clean-bracket condition caveat — isolated logic tests.

Exercises the PRODUCTION predicate `_condition_note_applies` (Rule #40 / E14:
the test imports the REAL engine function, not a replica) across the 7 brief
cases + robustness / fail-safe extras.

Copy-only sprint: the predicate decides ONLY whether the additive
`condition_note_ar/en` keys attach to valuation; it never touches the valuation
amount. Amount-invariance is guaranteed by construction (no value logic changed)
and confirmed by the 4-anchor live smoke (56/565/21 = 2,400,000 unchanged, etc.).

Run:  set PYTHONIOENCODING=utf-8  &&  python test_sprint_2_22_0a17.py
"""
import sys

from evaluate_unified import (
    _condition_note_applies,
    CONDITION_NOTE_AR,
    CONDITION_NOTE_EN,
)

# Brief-verbatim wording (locked; Rule #54 skipped per signed decision).
_EXPECT_AR = 'لم تُؤخذ حالة العقار (تجديد أو تهالك) في الحسبان. عقار في حالة أفضل من المتوسط قد يقع أعلى هذه النقطة، وعقار في حالة أدنى قد يقع تحتها.'
_EXPECT_EN = 'Property condition (renovation or wear) was not assessed. A better-than-average property may sit above this point; a poorer one may sit below.'


def _gate(gated, disp=0.20):
    """A well-formed dispersion-gate result (mirrors _stage1_dispersion_gate)."""
    return {'dispersion': disp, 'gated': gated, 'threshold': 0.30}


# (name, primary, gate, asset_type, amount, expected)
CASES = [
    # 1 — clean villa bracket (56/565/21): disp 0.208 < 0.30 → PRESENT
    ('clean villa bracket 56/565/21',
     {'method': 'comparison_bracket'}, _gate(False, 0.208), 'standalone_villa', 2400000, True),
    # 2 — widened villa (54/541/6) honest-range → ABSENT (method excluded; a10/a14 disclose)
    ('widened villa 54/541/6',
     {'method': 'comparison_widened'}, _gate(True, 0.425), 'standalone_villa', 4500000, False),
    # 3 — thin villa (55/296/13): a17 returned ABSENT; Sprint 2.22.0a.19 makes this PRESENT
    #     (path-complete — the thin SAMPLE caveat is not a CONDITION disclosure; gate None →
    #     fail-safe include). Full a19 path-coverage in test_sprint_2_22_0a19.py.
    ('thin 55/296/13 (a19: now PRESENT)',
     {'method': 'comparison_thin'}, None, 'standalone_villa', 2600000, True),
    # 4 — land clean bracket → ABSENT (no building condition; asset_type excluded)
    ('land clean bracket',
     {'method': 'comparison_bracket'}, _gate(False, 0.10), 'raw_land', 3000000, False),
    # 5 — apartment refusal (52/903/90) → ABSENT (no primary / no amount)
    ('apartment refusal 52/903/90',
     None, None, 'apartment_building', None, False),
    # 6 — dispersed bracket (disp >= 0.30) → ABSENT (a14 honest-range covers it)
    ('dispersed bracket disp>=0.30',
     {'method': 'comparison_bracket'}, _gate(True, 0.45), 'standalone_villa', 2000000, False),
    # 7 — FAIL-SAFE: villa bracket, dispersion unresolved (gate None) → PRESENT
    ('fail-safe villa bracket, gate None',
     {'method': 'comparison_bracket'}, None, 'standalone_villa', 2400000, True),

    # ── robustness extras ──
    # 8 — 'house' alias (forward-safe; today a house subject classifies standalone_villa) → PRESENT
    ('house alias clean bracket',
     {'method': 'comparison_bracket'}, _gate(False, 0.15), 'house', 1800000, True),
    # 9 — 'villa' legacy alias (locked decision: include) → PRESENT
    ('villa alias clean bracket',
     {'method': 'comparison_bracket'}, _gate(False, 0.15), 'villa', 1800000, True),
    # 10 — FAIL-SAFE: malformed gate dict (no 'gated' key) → PRESENT (gate.get('gated') is None)
    ('fail-safe malformed gate dict',
     {'method': 'comparison_bracket'}, {'dispersion': 0.4}, 'standalone_villa', 2400000, True),
    # 11 — clean villa bracket but amount None → ABSENT (no headline number to caveat)
    ('villa bracket amount None',
     {'method': 'comparison_bracket'}, _gate(False, 0.20), 'standalone_villa', None, False),
    # 12 — None primary → ABSENT
    ('none primary',
     None, _gate(False), 'standalone_villa', 2400000, False),
    # 13 — commercial bracket (defensive: not a villa/house) → ABSENT
    ('commercial clean bracket',
     {'method': 'comparison_bracket'}, _gate(False, 0.12), 'commercial', 5000000, False),
]


def run():
    passed = failed = 0
    for name, primary, gate, atype, amount, expected in CASES:
        got = _condition_note_applies(primary, gate, atype, amount)
        ok = (got == expected)
        print(f'[{"PASS" if ok else "FAIL"}] {name}: expected={expected} got={got}')
        passed += int(ok)
        failed += int(not ok)

    # Verbatim-wording guard (locked strings; Rule #54 skipped per signed decision).
    ar_ok = CONDITION_NOTE_AR == _EXPECT_AR
    en_ok = CONDITION_NOTE_EN == _EXPECT_EN
    print(f'[{"PASS" if ar_ok else "FAIL"}] CONDITION_NOTE_AR verbatim')
    print(f'[{"PASS" if en_ok else "FAIL"}] CONDITION_NOTE_EN verbatim')
    passed += int(ar_ok) + int(en_ok)
    failed += int(not ar_ok) + int(not en_ok)

    total = passed + failed
    print(f'\n{passed}/{total} passed, {failed} failed')
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(run())
