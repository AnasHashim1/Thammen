# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.146 — «التسريبات عارية-المفتاح» (the bare-key + bypass EN leaks the adversarial
completeness lens caught).

Isolated E14 test. The b145 adversarial 4-lens panel's completeness critic REJECTED the
"sequence complete" claim: fields with NO `_ar` suffix (invisible to the `_ar` scan + the scalar
rule) leak Arabic in EN mode on ALWAYS-VISIBLE default paths. b146 closes the VERIFIED set:
  (أ) en_localize: `_BARE_EN_KEYS` (disclaimer/label/window_label) + a bare-key branch in
      attach_en + catalog entries (BOTH live disclaimer variants · 3 accuracy labels · the
      location-feature labels) + 3 templates (window_label n=X · private-residential zone ·
      permitted-height).
  (ب) index.html: `pickBare()` + 4 bare-key swaps (compliance-foot disclaimer @4148 · hero
      acc.label @3805 · evidence window_label @2524 · location f.label @4100) + the A5
      recommendation pick-bypass fix + the land-grid role pick (role_en exists, b139) + the
      generic-dump `_en` guard (fixes the b142 valuer-trace DOUBLE-render side-effect).
VALUE-NEUTRAL — additive `_en` only; bare AR values untouched; amount/method/rule untouched.
"""
import io, sys, json, importlib

ROOT = r"C:\Thammen\deploy v2"
HTML = io.open(ROOT + r"\index.html", encoding="utf-8").read()
ENG  = io.open(ROOT + r"\evaluate_unified.py", encoding="utf-8").read()

sys.path.insert(0, ROOT)
en_localize = importlib.import_module("en_localize"); importlib.reload(en_localize)
_norm, attach_en, _item_en = en_localize._norm, en_localize.attach_en, en_localize._item_en

passed = failed = 0
def ck(name, cond):
    global passed, failed
    if cond: passed += 1; print("  PASS", name)
    else:    failed += 1; print("  FAIL", name)

print("Sprint 2.22.0b.146 — the bare-key + bypass EN leaks\n")

# ── (1) the bare-key rule — REAL attach_en on representative dicts ───────────
print("[bare-key rule]")
d1 = {'disclaimer': 'ثمّن يجمع البيانات السوقية من المصادر الحكومية والإعلانات النشطة. هذا تحليل معلوماتي للقرار، ولا يُعتبر تقرير تثمين رسمي صادر عن مثمّن مرخّص وفق معايير RICS/IVS. للأغراض الرسمية (قروض، محاكم، تقارير محاسبية) يلزم مُقيِّم معتمد.'}
attach_en(d1)
ck("main-path disclaimer_en (full protective content)", (d1.get('disclaimer_en') or '').startswith('Thammen compiles') and 'certified valuer is required' in d1.get('disclaimer_en',''))
d2 = {'disclaimer': 'ثمّن يجمع البيانات السوقية من المصادر الحكومية والإعلانات النشطة. هذا تحليل معلوماتي، ولا يُعتبر تقرير تثمين رسمي صادر عن مثمّن مرخّص وفق معايير RICS/IVS.'}
attach_en(d2)
ck("fast-path disclaimer_en", 'not considered an official appraisal report' in (d2.get('disclaimer_en') or ''))
d3 = {'label': 'شواهد محدودة'}
attach_en(d3)
ck("accuracy label_en (شواهد محدودة)", d3.get('label_en') == 'Limited evidence')
d4 = {'label': 'تقدير تقريبي'}; attach_en(d4)
ck("accuracy label_en (تقدير تقريبي)", d4.get('label_en') == 'Approximate estimate')
d5 = {'window_label': '37 معاملة، منها 28 خلال 24 شهراً'}
attach_en(d5)
ck("window_label_en (template, both numbers)", d5.get('window_label_en') == '37 transactions, of which 28 within the last 24 months')
d6 = {'label': 'منطقة سكنية خاصة (R1)-TYP'}; attach_en(d6)
ck("location zone label_en (template)", 'Private residential zone' in (d6.get('label_en') or ''))
d7 = {'label': 'ارتفاع مسموح: أرضي + أول + سطح'}; attach_en(d7)
ck("permitted-height AR-value variant (constant)", d7.get('label_en') == 'Permitted height: ground + first + roof')
# safety: unresolvable + clobber-guard + AR untouched
d8 = {'label': 'نص غير مفهرس 999'}; attach_en(d8)
ck("unresolvable bare key does NOT fire", 'label_en' not in d8)
d9 = {'label': 'شواهد كافية', 'label_en': 'ENGINE-SET'}; attach_en(d9)
ck("never clobbers an engine label_en (b23 scenarios contract)", d9['label_en'] == 'ENGINE-SET')
ck("bare AR value untouched", d1['disclaimer'].startswith('ثمّن يجمع'))

# ── (2) LIVE fixtures — all 5 resolve, amounts unchanged ─────────────────────
print("\n[live fixtures]")
try:
    WP = r'C:/Users/ans_h/AppData/Local/Temp/claude/C--Thammen-deploy-v2/10958cd2-1cda-4971-8ed4-ab3761017b3f/scratchpad'
    all_ok = True
    for fn in ('s1', 's2', 's3', 's4', 's5'):
        d = json.load(io.open(WP + f'/{fn}.json', encoding='utf-8'))
        a0 = (d.get('valuation') or {}).get('amount')
        attach_en(d)
        all_ok = all_ok and bool(d.get('disclaimer_en')) and ((d.get('valuation') or {}).get('amount') == a0)
    ck("all 5 live fixtures: disclaimer_en + amount unchanged", all_ok)
    d = json.load(io.open(WP + '/s1.json', encoding='utf-8')); attach_en(d)
    lf = d.get('location_features') or []
    ck("live villa: EVERY location label localized (7/7)", lf and all(f.get('label_en') for f in lf))
    ck("live villa: acc.label_en", ((d.get('accuracy') or {}).get('label_en') or '').startswith('Limited'))
except FileNotFoundError:
    print("  SKIP live fixtures (not on this machine)")

# ── (3) frontend — pickBare + the swaps + the dump guard ─────────────────────
print("\n[frontend]")
ck("pickBare helper defined", "function pickBare(o,k)" in HTML)
ck("compliance-foot disclaimer via pickBare", "pickBare(d,'disclaimer')" in HTML)
ck("hero acc.label via pickBare", "pickBare(acc,'label')" in HTML)
ck("evidence window_label via pickBare", "pickBare(_cmp,'window_label')" in HTML)
ck("location f.label via pickBare", "pickBare(f,'label')" in HTML)
ck("A5 recommendation pick-bypass fixed", "pick(d.refusal_reason,'recommendation')" in HTML)
ck("A5 raw recommendation_ar read GONE", "d.refusal_reason.recommendation_ar)||null" not in HTML)
ck("land-grid source role via pick", "pick(s,'role')||s.source" in HTML)
ck("generic dump: _en keys never dumped raw", "if(k.endsWith('_en'))return;" in HTML)
ck("generic dump: value picked per LANG", "(LANG==='en'&&c[k+'_en']!=null)?c[k+'_en']:c[k]" in HTML)

# ── (4) value-neutral + version ──────────────────────────────────────────────
print("\n[value-neutral + version]")
ck("api.py untouched (no b146 marker)", "b146" not in io.open(ROOT + r"\api.py", encoding="utf-8").read())
ck("ENGINE_VERSION format (b-series)", "thammen-sprint2p22p0b" in ENG)
ck("SPRINT_TAG format (2.22.0b)", "SPRINT_TAG = '2.22.0b." in ENG)

print(f"\n{'='*54}\n  {passed} passed, {failed} failed\n{'='*54}")
sys.exit(1 if failed else 0)
