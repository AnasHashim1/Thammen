# -*- coding: utf-8 -*-
"""validate_gt_sheet.py — the D-3 GT-sheet calibration tool (Sprint 2.22.0b.19 companion).

Takes a DOCUMENTED valuer sheet (zone/street/building + the sheet's MV + the sheet's
age basis + finish), recomputes the DRC on the SHEET'S basis (the generalized V001 ±1%
pattern: RAW age, penalty 0 — E26), measures the deviation, and appends a row to
docs/validation/VALIDATION_LOG.md. ZERO engine change — an external measurement tool:
the engine inputs (land floor + BUA) come from the LIVE response's value_stack.cost
(browser-UA curl, Rule #61); the curve comes from the PRODUCTION functions (E14).

Every documented sheet Anas brings = an instant calibration point above n=1
(SESSION_CLOSE §9: «كل شيت جديد بمستند يصادق درجة — قناة D-3»). The VALIDATION_LOG
intake rule applies: NO sheet counts without a document (سند/عقد/شيت).

Usage:
  PYTHONIOENCODING=utf-8 python validate_gt_sheet.py \
      --zone 56 --street 647 --building 6 \
      --sheet-value 3600145 --age 18 --finish high \
      [--sheet-land 2456345] [--floors 2] [--bua 602] \
      [--ref "TD-93317"] [--dry-run]

Self-check (the V001 standing gate): the example above must land within ±1%
(expected ≈ +0.35% on the engine land floor — test_sprint_2_22_0b18 §B).
"""
import argparse
import datetime
import json
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

from evaluate_unified import _cost_retention, COST_RCN_BY_FINISH  # production curve (E14)

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/125.0 Safari/537.36')
URL = 'https://thammen.qa/api/evaluate'
LOG = 'docs/validation/VALIDATION_LOG.md'


def fetch_live(zone, street, building):
    cmd = ['curl', '-s', '-m', '45', '-X', 'POST', URL, '-A', UA,
           '-H', 'Content-Type: application/json',
           '-d', json.dumps({'zone': zone, 'street': street, 'building': building})]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8',
                       errors='replace', timeout=60)
    return json.loads(r.stdout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--zone', type=int, required=True)
    ap.add_argument('--street', type=int, required=True)
    ap.add_argument('--building', type=int, required=True)
    ap.add_argument('--sheet-value', type=float, required=True,
                    help='the documented sheet MV (QAR)')
    ap.add_argument('--age', type=float, required=True,
                    help="the sheet's age basis (RAW years — E26: penalty 0)")
    ap.add_argument('--finish', required=True,
                    choices=sorted(set(COST_RCN_BY_FINISH)),
                    help="the sheet's finish tier (RCN ladder key)")
    ap.add_argument('--sheet-land', type=float, default=None,
                    help="the sheet's land component (QAR); default = the engine land floor")
    ap.add_argument('--floors', type=int, default=None,
                    help='override floors (default: trust the live BUA as-is)')
    ap.add_argument('--bua', type=float, default=None,
                    help='override BUA m² (default: live value_stack.cost.bua_m2)')
    ap.add_argument('--ref', default='', help='sheet reference (e.g. TD-93317)')
    ap.add_argument('--dry-run', action='store_true',
                    help='print only — do NOT append to the VALIDATION_LOG')
    a = ap.parse_args()

    print(f'fetching live basis for {a.zone}/{a.street}/{a.building} …')
    d = fetch_live(a.zone, a.street, a.building)
    v = d.get('valuation') or {}
    vs = (v.get('value_stack') or {}).get('cost') or {}
    land = a.sheet_land if a.sheet_land else vs.get('land_floor')
    bua = a.bua if a.bua else vs.get('bua_m2')
    if not land or not bua:
        print('ABORT: no land floor / BUA available from the live value_stack '
              f'(land={land}, bua={bua}) — supply --sheet-land/--bua.')
        sys.exit(2)
    if a.floors and vs.get('bua_m2') and not a.bua:
        # live bua assumes default floors (2); rescale if the sheet says otherwise
        bua = vs['bua_m2'] / 2.0 * a.floors

    rcn = COST_RCN_BY_FINISH[a.finish]
    ret = _cost_retention(a.age, a.finish)        # RAW sheet age, penalty 0 (E26 basis)
    building_val = bua * rcn * ret
    drc = land + building_val
    dev = (drc - a.sheet_value) / a.sheet_value * 100

    print(f'  land basis        : {land:,.0f} QAR'
          f' ({"sheet" if a.sheet_land else "engine MoJ floor"})')
    print(f'  BUA               : {bua:,.1f} m² · RCN {a.finish} = {rcn:,} ×'
          f' retention({a.age:g}) = {ret:.3f} → building {building_val:,.0f}')
    print(f'  DRC @ sheet basis : {drc:,.0f} QAR')
    print(f'  sheet MV          : {a.sheet_value:,.0f} QAR')
    verdict = 'WITHIN ±1%' if abs(dev) <= 1.0 else ('WITHIN ±5%' if abs(dev) <= 5.0
                                                    else 'DIVERGENT >5%')
    print(f'  deviation         : {dev:+.2f}%  → {verdict}')

    row = (f'| {datetime.date.today().isoformat()} | {a.zone}/{a.street}/{a.building} '
           f'| {a.ref or "—"} | {a.sheet_value:,.0f} | age {a.age:g} (raw) · {a.finish} '
           f'| land {land:,.0f} ({"sheet" if a.sheet_land else "engine"}) · bua {bua:,.0f} '
           f'| {drc:,.0f} | {dev:+.2f}% | {verdict} |')
    if a.dry_run:
        print('\n[dry-run] log row (NOT appended):\n' + row)
        return
    header = ('\n\n## GT-sheet DRC calibration rows (validate_gt_sheet.py — the D-3 kit, '
              'Sprint 2.22.0b.19)\n\n'
              '> Each row = a DOCUMENTED valuer sheet replayed on the production DRC curve '
              'at the SHEET basis (raw age, penalty 0 — E26). Intake rule: no row without '
              'a document.\n\n'
              '| date | address | ref | sheet MV | sheet basis | inputs | our DRC | dev | verdict |\n'
              '|---|---|---|---|---|---|---|---|---|\n')
    txt = open(LOG, encoding='utf-8').read()
    if 'GT-sheet DRC calibration rows' not in txt:
        txt += header
    txt += row + '\n'
    open(LOG, 'w', encoding='utf-8', newline='').write(txt)
    print(f'\nappended to {LOG}')


if __name__ == '__main__':
    main()
