# -*- coding: utf-8 -*-
"""
Sprint 2.22.0a.19 — thin-path condition caveat (path-complete) — isolated logic tests.

Exercises the PRODUCTION predicate `_condition_note_applies` (Rule #40 / E14: the test
imports the REAL engine function + the REAL method tuple, not a replica).

a17 scoped the bidirectional condition caveat to CLEAN `comparison_bracket` villa/house
points only. Sprint 2.22.0a.18 moved Marikh (54/541/6) onto the `comparison_thin` path at
~5.4M — the subject that most needs the condition disclosure was the one missing it, because
a17's "thin already caveated" conflated the SAMPLE-size caveat with a CONDITION disclosure
(orthogonal). a19 extends the note PATH-COMPLETE to every value-bearing villa/house comparison
surface EXCEPT the dispersion-GATED pools (bracket→a14, widened→a10), whose honest-range text
already states "built type and condition not yet confirmed" → excluded by gate.get('gated') so
the note never duplicates.

Disclosure-only: the predicate decides ONLY whether the additive `condition_note_ar/en` keys
attach to valuation; it NEVER touches the valuation amount. Amount-invariance is guaranteed by
construction (no value logic changed) and confirmed by the live smoke (54/541/6 ~5.4M, 56/565/21
2,400,000 — both unchanged).

Run:  set PYTHONIOENCODING=utf-8  &&  python test_sprint_2_22_0a19.py
"""
import sys

from evaluate_unified import (
    _condition_note_applies,
    _CONDITION_NOTE_METHODS,
    CONDITION_NOTE_AR,
    CONDITION_NOTE_EN,
)

# Brief-verbatim wording (locked; unchanged from a17, Rule #54 skipped per signed decision).
_EXPECT_AR = 'لم تُؤخذ حالة العقار (تجديد أو تهالك) في الحسبان. عقار في حالة أفضل من المتوسط قد يقع أعلى هذه النقطة، وعقار في حالة أدنى قد يقع تحتها.'
_EXPECT_EN = 'Property condition (renovation or wear) was not assessed. A better-than-average property may sit above this point; a poorer one may sit below.'


def _gate(gated, disp=0.20):
    """A well-formed dispersion-gate result (mirrors _stage1_dispersion_gate)."""
    return {'dispersion': disp, 'gated': gated, 'threshold': 0.30}


# (name, primary, gate, asset_type, amount, expected)
CASES = [
    # ── a17 invariants that MUST still hold ──
    # 1 — clean villa bracket (56/565/21): disp 0.208 < 0.30, not gated → PRESENT (unchanged)
    ('clean villa bracket 56/565/21',
     {'method': 'comparison_bracket'}, _gate(False, 0.208), 'standalone_villa', 2400000, True),
    # 2 — dispersed villa bracket (disp >= 0.30, gated) → ABSENT (a14 honest-range discloses)
    ('dispersed bracket disp>=0.30',
     {'method': 'comparison_bracket'}, _gate(True, 0.45), 'standalone_villa', 2000000, False),
    # 3 — widened villa GATED (54/541/6 pre-a18, disp 0.425) → ABSENT (a10 honest-range discloses)
    ('widened villa GATED 54/541/6',
     {'method': 'comparison_widened'}, _gate(True, 0.425), 'standalone_villa', 4500000, False),

    # ── a19 NEW path-complete behavior ──
    # 4 — THE FIX: thin villa (54/541/6 post-a18, ~5.4M; gate None) → PRESENT
    ('thin villa 54/541/6 post-a18 (THE FIX)',
     {'method': 'comparison_thin'}, None, 'standalone_villa', 5400000, True),
    # 5 — thin villa 55/296/13 (gate None) → PRESENT (was ABSENT in a17)
    ('thin villa 55/296/13',
     {'method': 'comparison_thin'}, None, 'standalone_villa', 2600000, True),
    # 6 — widened villa NON-gated (disp 0.20, gated False) → PRESENT (no honest-range → fill the gap)
    ('widened villa NON-gated',
     {'method': 'comparison_widened'}, _gate(False, 0.20), 'standalone_villa', 3000000, True),
    # 7 — widened_indicative NON-gated → PRESENT
    ('widened_indicative NON-gated',
     {'method': 'comparison_widened_indicative'}, _gate(False, 0.18), 'standalone_villa', 3000000, True),
    # 8 — widened_indicative GATED → ABSENT (honest-range discloses)
    ('widened_indicative GATED',
     {'method': 'comparison_widened_indicative'}, _gate(True, 0.40), 'standalone_villa', 3000000, False),
    # 9 — preliminary villa (n<5 borderline; gate None) → PRESENT (no condition disclosure on this path)
    ('preliminary villa',
     {'method': 'comparison_preliminary'}, None, 'standalone_villa', 2200000, True),

    # ── asset_type / amount exclusions (unchanged) ──
    # 10 — land thin → ABSENT (no building condition; asset_type excluded)
    ('land thin',
     {'method': 'comparison_thin'}, None, 'raw_land', 3000000, False),
    # 11 — apartment refusal (no primary / no amount) → ABSENT
    ('apartment refusal 52/903/90',
     None, None, 'apartment_building', None, False),
    # 12 — commercial bracket (defensive: not villa/house) → ABSENT
    ('commercial clean bracket',
     {'method': 'comparison_bracket'}, _gate(False, 0.12), 'commercial', 5000000, False),
    # 13 — thin villa amount None → ABSENT (no headline number to caveat)
    ('thin villa amount None',
     {'method': 'comparison_thin'}, None, 'standalone_villa', None, False),
    # 14 — method NOT in the set (e.g. a pure income/cost surface) → ABSENT
    ('non-comparison method',
     {'method': 'income_only'}, None, 'standalone_villa', 2400000, False),

    # ── fail-safe TO DISCLOSURE (gate unresolved) ──
    # 15 — thin villa with malformed gate dict (no 'gated' key) → PRESENT (gate.get('gated') is None)
    ('fail-safe malformed gate dict on thin',
     {'method': 'comparison_thin'}, {'dispersion': 0.4}, 'standalone_villa', 5400000, True),
    # 16 — clean bracket, gate None (dispersion unresolved) → PRESENT (a17 fail-safe, unchanged)
    ('fail-safe bracket gate None',
     {'method': 'comparison_bracket'}, None, 'standalone_villa', 2400000, True),

    # ── asset aliases (forward-safe; today a house subject classifies standalone_villa) ──
    # 17 — 'house' alias on thin → PRESENT
    ('house alias thin',
     {'method': 'comparison_thin'}, None, 'house', 1800000, True),
    # 18 — 'villa' legacy alias on widened non-gated → PRESENT
    ('villa alias widened non-gated',
     {'method': 'comparison_widened'}, _gate(False, 0.22), 'villa', 1800000, True),
    # 19 — none primary → ABSENT
    ('none primary',
     None, _gate(False), 'standalone_villa', 2400000, False),
]


def run():
    passed = failed = 0
    for name, primary, gate, atype, amount, expected in CASES:
        got = _condition_note_applies(primary, gate, atype, amount)
        ok = (got == expected)
        print(f'[{"PASS" if ok else "FAIL"}] {name}: expected={expected} got={got}')
        passed += int(ok)
        failed += int(not ok)

    # Method-set membership sanity: every value-bearing comparison surface is covered, and the
    # clean-bracket case (a17) is preserved as the first member.
    expect_methods = {
        'comparison_bracket', 'comparison_thin', 'comparison_widened',
        'comparison_widened_indicative', 'comparison_preliminary',
    }
    methods_ok = set(_CONDITION_NOTE_METHODS) == expect_methods
    print(f'[{"PASS" if methods_ok else "FAIL"}] _CONDITION_NOTE_METHODS == {sorted(expect_methods)}')
    passed += int(methods_ok); failed += int(not methods_ok)

    # Verbatim-wording guard (locked strings; unchanged from a17 — copy did NOT change).
    ar_ok = CONDITION_NOTE_AR == _EXPECT_AR
    en_ok = CONDITION_NOTE_EN == _EXPECT_EN
    print(f'[{"PASS" if ar_ok else "FAIL"}] CONDITION_NOTE_AR verbatim (unchanged from a17)')
    print(f'[{"PASS" if en_ok else "FAIL"}] CONDITION_NOTE_EN verbatim (unchanged from a17)')
    passed += int(ar_ok) + int(en_ok)
    failed += int(not ar_ok) + int(not en_ok)

    total = passed + failed
    print(f'\n{passed}/{total} passed, {failed} failed')
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(run())
