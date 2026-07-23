# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.142 — «توائم _en لمصفوفات التحذيرات والفحص» (EN twins for the caveat/checklist arrays).

Isolated E14 test — reads the REAL en_localize / reasoning_trace / output_briefs / index.html.
Sprint B, slice 1: the two constant Arabic ARRAYS that leaked in EN (measured 14 of the 32 result-screen
leaks) get translated `{key}_en` twins via the en_localize CATALOG + an attach_en array rule; the frontend
picks the `_en` array in EN mode. VALUE-INVARIANT / additive — the `_ar` arrays are untouched, AR mode
byte-identical (pickArr returns the AR array), amount/method/rule never touched.
  (1) COVERAGE — every string the engine puts into `reasoning_trace.known_unknowns` (all asset types) and
      the brief `due_diligence` `_dd_questions` (villa + land) is in CATALOG (guards future drift).
  (2) attach_en emits `known_unknowns_en` + `content_en`, index-aligned + fully translated, additive.
  (3) the array rule is LIST-only — a dict `content` (e.g. the yield section) is NOT given a `content_en`.
  (4) frontend: `pickArr` helper + the 3 reads swapped (_s4bLimits, the report _rtrR, the due_diligence render).
  (5) engine version b142.
"""
import io, sys, ast, importlib

ROOT = r"C:\Thammen\deploy v2"
HTML = io.open(ROOT + r"\index.html", encoding="utf-8").read()
ENG  = io.open(ROOT + r"\evaluate_unified.py", encoding="utf-8").read()

sys.path.insert(0, ROOT)
en_localize = importlib.import_module("en_localize")
reasoning_trace = importlib.import_module("reasoning_trace")
_norm, CATALOG = en_localize._norm, en_localize.CATALOG

passed = failed = 0
def ck(name, cond):
    global passed, failed
    if cond: passed += 1; print("  PASS", name)
    else:    failed += 1; print("  FAIL", name)

print("Sprint 2.22.0b.142 — EN twins for the caveat/checklist arrays\n")

# ── (1) COVERAGE: every real engine array item is in CATALOG ─────────────────
print("[coverage — CATALOG covers the real engine arrays]")
KU = set()
for at in ('apartment', 'villa_standalone', 'villa_compound', 'standalone_villa', 'raw_land'):
    tr = reasoning_trace.ReasoningTrace(valuation_id='T')
    reasoning_trace.add_standard_unknowns(tr, at)
    KU |= set(tr.known_unknowns)
ku_miss = [s for s in KU if _norm(s) not in CATALOG]
ck("known_unknowns: all %d strings in CATALOG" % len(KU), not ku_miss)
if ku_miss: print("      MISSING:", ku_miss)

DD = set()
for node in ast.walk(ast.parse(io.open(ROOT + r"\output_briefs.py", encoding="utf-8").read())):
    if isinstance(node, ast.Assign):
        for tgt in node.targets:
            if isinstance(tgt, ast.Name) and tgt.id == '_dd_questions' and isinstance(node.value, ast.List):
                for el in node.value.elts:
                    if isinstance(el, ast.Constant) and isinstance(el.value, str):
                        DD.add(el.value)
dd_miss = [s for s in DD if _norm(s) not in CATALOG]
ck("due_diligence: all %d strings in CATALOG" % len(DD), bool(DD) and not dd_miss)
if dd_miss: print("      MISSING:", dd_miss)

# ── (2) attach_en emits + translates the arrays, additive/index-aligned ──────
print("[attach_en emits translated _en arrays — additive]")
ku_ar = ["حالة العقار الداخلية الفعلية (تشطيبات، صيانة، تكييف)",
         "أي التزامات قانونية (رهون، خلافات، إرث، حصص غير مفروزة)"]
dd_ar = ["اطلب بيان عقاري من وزارة العدل (يكشف الرهونات والخلافات)",
         "اسأل عن عمر البناء الحقيقي (ليس ما يقوله البائع)"]
payload = {
    "reasoning_trace": {"known_unknowns": list(ku_ar)},
    "brief": {"sections": [
        {"id": "due_diligence", "title_ar": "أسئلة يجب طرحها قبل الشراء", "content": list(dd_ar)},
        {"id": "yield", "title_ar": "العائد", "content": {"gross_yield_pct": 5.0}},  # dict content — must NOT get content_en
    ]},
}
en_localize.attach_en(payload)
kt = payload["reasoning_trace"]
ck("known_unknowns_en present + index-aligned", kt.get("known_unknowns_en") and len(kt["known_unknowns_en"]) == len(ku_ar))
ck("known_unknowns_en fully translated (0 Arabic)",
   kt.get("known_unknowns_en") and not any(any('؀' <= c <= 'ۿ' for c in x) for x in kt["known_unknowns_en"]))
ck("known_unknowns (_ar array) UNTOUCHED", kt["known_unknowns"] == ku_ar)
dd_sec = payload["brief"]["sections"][0]
yield_sec = payload["brief"]["sections"][1]
ck("due_diligence content_en present + translated",
   dd_sec.get("content_en") and len(dd_sec["content_en"]) == len(dd_ar)
   and not any(any('؀' <= c <= 'ۿ' for c in x) for x in dd_sec["content_en"]))
ck("due_diligence content (_ar array) UNTOUCHED", dd_sec["content"] == dd_ar)

# ── (3) list-only rule: a dict `content` gets NO content_en ──────────────────
print("[the array rule is LIST-only]")
ck("dict `content` (yield section) NOT given content_en", "content_en" not in yield_sec)
# uncataloged item falls back to the Arabic item (graceful), only emits when >=1 translates:
p2 = {"x": {"known_unknowns": ["سلسلة غير مفهرسة", "أي التزامات قانونية (رهون، خلافات، إرث، حصص غير مفروزة)"]}}
en_localize.attach_en(p2)
ck("mixed array: emitted + uncataloged item falls back to AR",
   p2["x"].get("known_unknowns_en") == ["سلسلة غير مفهرسة",
       CATALOG[_norm("أي التزامات قانونية (رهون، خلافات، إرث، حصص غير مفروزة)")]])
p3 = {"x": {"known_unknowns": ["سلسلة غير مفهرسة تماماً"]}}  # 0 cataloged → no _en
en_localize.attach_en(p3)
ck("all-uncataloged array: NO _en twin emitted", "known_unknowns_en" not in p3["x"])

# ── (4) frontend: pickArr + the 3 swaps ─────────────────────────────────────
print("[frontend pickArr + swaps]")
ck("pickArr helper defined", "function pickArr(o,base){" in HTML and "Array.isArray(en)" in HTML)
ck("_s4bLimits reads pickArr(known_unknowns)", "const ku=pickArr(d.reasoning_trace,'known_unknowns');" in HTML)
ck("report _rtrR reads pickArr(known_unknowns)", "pickArr(_rtrR,'known_unknowns').forEach(u=>{h+='• '+u+'<br>'});" in HTML)
ck("due_diligence renders pickArr(sec,'content')", "const ddItems = Array.isArray(c) ? pickArr(sec,'content')" in HTML)
ck("old raw known_unknowns read gone (result)", "const ku=((d.reasoning_trace||{}).known_unknowns)||[];" not in HTML)

# ── (5) version ─────────────────────────────────────────────────────────────
print("[version]")
ck("engine version b142", "thammen-sprint2p22p0b142-en-caveat-checklist-arrays" in ENG)
ck("sprint tag b142", "SPRINT_TAG = '2.22.0b.142'" in ENG)

print("\n%d passed, %d failed" % (passed, failed))
sys.exit(1 if failed else 0)
