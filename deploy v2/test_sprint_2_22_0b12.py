# Sprint 2.22.0b.12 (Bug A15) — isolated test for the HBU not-evaluated disclosure.
# Exercises the PRODUCTION helpers (E14 / Rule #40): _hbu_note_applies + _extract_zoning_code
# + _condition_note_applies + the verbatim constants. Disclosure-only / value-invariant.
import sys, types, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import evaluate_unified as E

P, F = 0, 0
def ok(cond, name):
    global P, F
    if cond:
        P += 1; print(f"[PASS] {name}")
    else:
        F += 1; print(f"[FAIL] {name}")

M = E._CONDITION_NOTE_METHODS[0]          # a valid villa comparison method (e.g. comparison_bracket)
GOOD = {'gated': False}                   # a resolved, non-dispersed gate
prim = {'method': M}

def mk_ev(factors):
    return types.SimpleNamespace(valuation=types.SimpleNamespace(factors_detail=factors))

# ── _extract_zoning_code (production parser) ──
ok(E._extract_zoning_code(mk_ev([{'code': 'zoning', 'evidence': 'التصنيف R1 سكني', 'label_ar': ''}])) == 'R1',
   "zoning R1 parsed from factor evidence")
ok(E._extract_zoning_code(mk_ev([{'code': 'zoning', 'evidence': '', 'label_ar': 'منطقة R2'}])) == 'R2',
   "zoning R2 parsed from label_ar")
ok(E._extract_zoning_code(mk_ev([{'code': 'landmarks', 'evidence': 'something'}])) is None,
   "no zoning factor -> None (the A15 trigger)")
ok(E._extract_zoning_code(mk_ev([])) is None, "empty factors_detail -> None")
ok(E._extract_zoning_code(None) is None, "ev=None -> None (fail-safe)")

# ── _hbu_note_applies: core brief cases ──
ok(E._hbu_note_applies(prim, GOOD, 'standalone_villa', 2_400_000, None) is True,
   "absent-zoning + villa + amount -> NOTE FIRES")
ok(E._hbu_note_applies(prim, GOOD, 'standalone_villa', 2_400_000, 'R1') is False,
   "present-zoning (R1) -> NO note (HBU was evaluated)")
ok(E._hbu_note_applies(prim, GOOD, 'standalone_villa', 2_400_000, 'C') is False,
   "present-zoning (C) -> NO note")

# land / apartment / tower / commercial = N/A
ok(E._hbu_note_applies(prim, GOOD, 'raw_land', 2_400_000, None) is False, "land N/A (no note even if zoning absent)")
ok(E._hbu_note_applies(prim, GOOD, 'apartment_building', 2_400_000, None) is False, "apartment N/A")
ok(E._hbu_note_applies(prim, GOOD, 'tower', 2_400_000, None) is False, "tower N/A")
ok(E._hbu_note_applies(prim, GOOD, 'commercial', 2_400_000, None) is False, "commercial N/A")

# villa/house aliases
ok(E._hbu_note_applies(prim, GOOD, 'house', 2_400_000, None) is True, "house alias -> note")
ok(E._hbu_note_applies(prim, GOOD, 'villa', 2_400_000, None) is True, "villa alias -> note")

# amount + method guards
ok(E._hbu_note_applies(prim, GOOD, 'standalone_villa', None, None) is False, "amount None -> no note")
ok(E._hbu_note_applies({'method': 'insufficient_data'}, GOOD, 'standalone_villa', 2_400_000, None) is False,
   "refusal method -> no note")
ok(E._hbu_note_applies(None, GOOD, 'standalone_villa', 2_400_000, None) is False, "primary None -> no note")

# malformed-gate fail-safe-to-disclosure (mirrors value_floor / condition_note)
ok(E._hbu_note_applies(prim, None, 'standalone_villa', 2_400_000, None) is True,
   "gate=None (malformed) + absent zoning -> NOTE FIRES (fail-safe to disclosure)")
ok(E._hbu_note_applies(prim, {}, 'standalone_villa', 2_400_000, None) is True,
   "gate={} (malformed) + absent zoning -> note fires (fail-safe)")

# dispersion-GATED surface -> excluded (coupled to value_floor's _condition_note_applies)
ok(E._hbu_note_applies(prim, {'gated': True}, 'standalone_villa', 2_400_000, None) is False,
   "dispersed/gated surface -> NO note (a10/a14 honest-range already discloses)")

# zoning present ALWAYS wins, even on a fail-safe gate
ok(E._hbu_note_applies(prim, None, 'standalone_villa', 2_400_000, 'R1') is False,
   "zoning present overrides malformed gate -> no note")

# parity with the sibling predicate (zoning-absent path == _condition_note_applies)
ok(E._hbu_note_applies(prim, GOOD, 'standalone_villa', 2_400_000, None)
   == E._condition_note_applies(prim, GOOD, 'standalone_villa', 2_400_000),
   "zoning-absent gate == _condition_note_applies (value_floor co-location)")

# ── constants (verbatim brief AR + EN twin + bidi safety) ──
ok(E._HBU_NOTE_AR == 'لم يتسنَّ تحديد فرضية الاستخدام الأفضل لهذه القطعة (طبقة التنظيم غير متاحة)',
   "AR copy is the signed brief string verbatim")
ok(isinstance(E._HBU_NOTE_EN, str) and 'best' in E._HBU_NOTE_EN.lower() and len(E._HBU_NOTE_EN) > 10,
   "EN twin present + non-empty")
ok(not any('a' <= c.lower() <= 'z' for c in E._HBU_NOTE_AR), "AR copy carries NO Latin letters (bidi-safe)")
ok(any('؀' <= c <= 'ۿ' for c in E._HBU_NOTE_AR), "AR copy is Arabic")

print(f"\n=== Sprint 2.22.0b.12 (A15) isolated: {P} passed, {F} failed ===")
sys.exit(1 if F else 0)
