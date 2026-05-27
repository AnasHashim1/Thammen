"""
Sprint 2.22.0a.2 Gate 2 — Heroku post-deploy smoke probe (throwaway, Rule #34).

6 anchors per docs/SPRINT_2p22p0a2_READY_FOR_PUSH.md Gate 2 plan:
  1. 52/903/90  apartment_building (comp_density_sparse — known type sparse data)
  2. 56/565/21  Bou Hamour villa (full brief renders, all patterns visible)
  3. 69/255/75  Lusail H1 (apartment_building refusal)
  4. 70/300/25  asset_type=unknown (Pattern B → classifier_failure)
  5. 51/835/17  compound_large >= 15K (E20 Patch A → asset_scale_extreme)
  6. (Pearl placeholder — skip unless Anas supplies an address)

Each anchor: assert engine_version, then grep response for forbidden
substrings from each Sprint 2.22.0a.2 pattern. Logs Heroku release
metadata + per-anchor pass/fail.
"""
import json
import os
import sys
import time
import urllib.request

BASE = "https://thammen.qa/api/evaluate"
HEALTH = "https://thammen.qa/api/health"
ENGINE_EXPECTED = "thammen-sprint2p22p0a2-arabic-surface-content-fixes"

# Forbidden substrings per pattern — these MUST NOT appear in rendered output
# at any of the value-producing anchors. (Some are valid only at specific
# anchors — see _check_anchor for the dispatch matrix.)
C1_FORBIDDEN = [
    'الحرب الإقليمية',
    'إغلاق هرمز',
    'نزوح سكاني',
    'انهيار حجم المعاملات',
    'تصحيح ما بعد المونديال',
]
C2_FORBIDDEN = [
    '(Project Instructions §3)',
    'Sprint 2.16.0 (الإصدار الحالي)',
    'الـ stratification',
    'الـ stratum',
]
C3_FORBIDDEN_TIER_BADGE = [
    # Pure tier-badge sites — must use شواهد taxonomy now
    "'موثوق' (n",
    "'إرشادي' (n",
    "تقدير موثوق",
    "تقدير إرشادي",
]
C4_FORBIDDEN = [
    'وليس تقييماً عقارياً معتمداً وفق RICS/IVS',
    'وليس تقييماً معتمداً وفق RICS/IVS',
    'وليس تقييماً عقارياً معتمداً وفق معايير RICS أو IVS',
    'لا يُصدر تقييماً عقارياً معتمداً (RICS/IVS)',
]
C5_FORBIDDEN = [
    'لا تدفع أكثر من وسيط MoJ + 10%',
    'ابدأ بعرض أقل 10% من التقييم',
]
P9_FORBIDDEN = [
    'لعقارات مشابهة بنفس الحجم',
    'صفقة مماثلة في وزارة العدل',
    'لعقارات مشابهة في وزارة العدل',
    'الصفقات المشابهة',
]

# Positive substrings — at least one must appear in rendered output
# when the corresponding code path fires.
NEW_PHRASES_BY_ANCHOR = {
    '56/565/21': [
        'شواهد كافية',                                   # C3 (n>=20 villa)
        'قريبة في النوع والمساحة',                        # §9 precision phrase
        'تقرير تثمين رسمي صادر عن مثمّن مرخّص',          # C4 reframe
        'قيوداً جوهرية على شواهد السوق المتاحة',          # C1 neutral cause
    ],
    '70/300/25': [
        'لم نتمكّن من تحديد نوع العقار',                  # Pattern B classifier_failure
        'تحقّق من بيانات العنوان',                       # B recommendation
    ],
    '51/835/17': [
        'يتجاوز أي صفقة مقارنة في قاعدة بياناتنا',        # asset_scale_extreme
    ],
}

ANCHORS = [
    ('52/903/90',  {'zone': 52, 'street': 903, 'building': 90},
     'apartment_building / known-type sparse / comp_density_sparse expected'),
    ('56/565/21',  {'zone': 56, 'street': 565, 'building': 21},
     'Bou Hamour villa / FULL BRIEF / patterns A+C1+C2+C3+C4+C5+§9 visible'),
    ('69/255/75',  {'zone': 69, 'street': 255, 'building': 75},
     'Lusail H1 apartment_building / refusal (comp_density_sparse expected)'),
    ('70/300/25',  {'zone': 70, 'street': 300, 'building': 25},
     'asset_type=unknown / Pattern B classifier_failure expected'),
    ('51/835/17',  {'zone': 51, 'street': 835, 'building': 17},
     'compound_large >=15K / asset_scale_extreme expected (E20)'),
]


def call(url, payload=None):
    if payload is not None:
        body = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url, data=body, method='POST',
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'thammen-gate2-smoke/2.22.0a.2',
                'Accept': 'application/json',
            },
        )
    else:
        req = urllib.request.Request(
            url, method='GET',
            headers={'User-Agent': 'thammen-gate2-smoke/2.22.0a.2'},
        )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            elapsed = time.time() - t0
            body_bytes = resp.read()
            return {
                'status': resp.status,
                'elapsed_s': round(elapsed, 2),
                'body': body_bytes.decode('utf-8', errors='replace'),
            }
    except Exception as e:
        return {
            'status': None,
            'elapsed_s': round(time.time() - t0, 2),
            'error': type(e).__name__ + ': ' + str(e),
        }


def _check_anchor(label, payload, description):
    print('=' * 76)
    print(f'[{label}]  {description}')
    print(f'POST {BASE}  body={payload}')

    r = call(BASE, payload)
    print(f'  status={r.get("status")}  elapsed={r.get("elapsed_s")}s')

    if r.get('status') != 200:
        print(f'  *** UNEXPECTED status; body[:200]={r.get("body", "")[:200]}')
        return {'anchor': label, 'status': r.get('status'), 'ok': False,
                'failures': ['HTTP not 200']}

    body = r['body']

    try:
        parsed = json.loads(body)
    except Exception as e:
        return {'anchor': label, 'status': 200, 'ok': False,
                'failures': [f'JSON parse: {e}']}

    failures = []

    # ENGINE_VERSION check
    ev = parsed.get('engine_version')
    if ev != ENGINE_EXPECTED:
        failures.append(f'engine_version mismatch: got={ev!r} expected={ENGINE_EXPECTED!r}')
    else:
        print(f'  engine_version OK: {ev}')

    # asset_type + refusal trigger
    at = parsed.get('asset_type')
    rt = (parsed.get('refusal_reason') or {}).get('trigger_id')
    print(f'  asset_type={at}  refusal_trigger={rt}')

    # Forbidden substring sweep
    for name, forbid_list in [
        ('C1', C1_FORBIDDEN),
        ('C2', C2_FORBIDDEN),
        ('C3', C3_FORBIDDEN_TIER_BADGE),
        ('C4', C4_FORBIDDEN),
        ('C5', C5_FORBIDDEN),
        ('§9', P9_FORBIDDEN),
    ]:
        for needle in forbid_list:
            if needle in body:
                failures.append(f'{name} regression: forbidden {needle!r}')

    # Positive substring checks for known-good anchors
    positive_expected = NEW_PHRASES_BY_ANCHOR.get(label, [])
    for needle in positive_expected:
        if needle not in body:
            failures.append(f'expected positive substring missing: {needle!r}')

    # 'negotiation' must NOT be in brief.sections[].id
    brief = parsed.get('brief') or {}
    section_ids = [s.get('id') for s in (brief.get('sections') or [])]
    if 'negotiation' in section_ids:
        failures.append(f'C5 regression: "negotiation" section still in brief.sections[].id')
    else:
        if section_ids:
            print(f'  brief.sections[].id = {section_ids}')

    if failures:
        print('  FAILURES:')
        for f in failures:
            print(f'    - {f}')
    else:
        print('  ALL CHECKS PASS')

    return {
        'anchor': label, 'status': 200, 'ok': not failures,
        'engine_version': ev, 'asset_type': at,
        'refusal_trigger': rt, 'section_ids': section_ids,
        'failures': failures,
    }


def main():
    # 1. Health check
    print('=' * 76)
    print('[health] /api/health')
    h = call(HEALTH)
    print(f'  status={h.get("status")}  elapsed={h.get("elapsed_s")}s')
    if h.get('status') == 200:
        try:
            hp = json.loads(h['body'])
            print(f'  version       = {hp.get("version")}')
            print(f'  engine_version= {hp.get("engine_version")}')
        except Exception:
            pass
    print()

    # 2. 5 anchor smokes
    results = []
    for label, payload, descr in ANCHORS:
        results.append(_check_anchor(label, payload, descr))
        time.sleep(2)

    # 3. Summary
    print()
    print('=' * 76)
    print('SUMMARY')
    print('=' * 76)
    passed = sum(1 for r in results if r['ok'])
    print(f'{passed}/{len(results)} anchors PASS')
    print()
    for r in results:
        emoji = 'OK ' if r['ok'] else 'FAIL'
        print(f'  [{emoji}]  {r["anchor"]:14s}  asset_type={r.get("asset_type", "?"):<20s}  '
              f'refusal={r.get("refusal_trigger", "(none)")}')
        for f in r.get('failures', []):
            print(f'         - {f}')

    # Write JSON output
    os.makedirs('docs/phase0', exist_ok=True)
    with open('docs/gate2_smoke_results.json', 'w', encoding='utf-8') as fh:
        json.dump(results, fh, ensure_ascii=False, indent=2)
    print()
    print(f'-> docs/gate2_smoke_results.json')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
