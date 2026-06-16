# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.50 — copy honesty: source/affiliation + contradiction + contact channel + de-jargon.

VALUE-INVARIANT / text-only. Asserts the persona-audit copy fixes are applied on the
REAL files (E14 — production strings + production functions), and the offending strings
are gone. No valuation logic touched → the 5-anchor value byte-gate is the live proof.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def _read(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return f.read()


_passed = _failed = 0


def check(name, cond):
    global _passed, _failed
    if cond:
        _passed += 1
        print(f"  PASS  {name}")
    else:
        _failed += 1
        print(f"  FAIL  {name}")


print("Sprint 2.22.0b.50 — copy honesty sweep\n")

HTML = _read("index.html")
API = _read("api.py")
EU = _read("evaluate_unified.py")
DF = _read("data_freshness.py")

# [1] WhatsApp number fully removed; email is the contact everywhere
print("[1] Contact channel: WhatsApp number -> info@thammen.qa")
check("no WhatsApp number '70177761' anywhere in index.html", "70177761" not in HTML)
check("info@thammen.qa present >= 6 times (2 hooks + 4 Terms lines)", HTML.count("info@thammen.qa") >= 6)
check("Terms contact reads «فريق ثمّن», not a personal name", "فريق ثمّن — <span" in HTML)
check("EN Terms contact reads «Thammen team»", "Thammen team — info@thammen.qa" in HTML)
check("personal-name contact «أنس — واتساب» gone", "أنس — واتساب" not in HTML)
check("EN «Anas — WhatsApp» gone", "Anas — WhatsApp" not in HTML)
check("GT hook reframed «اختياريّ» (report)", "اختياريّ: لتحسين دقّة ثمّن" in HTML)

# [2] Source honesty: no implied official/affiliation; open-data framed
print("\n[2] MoJ source — open-data framing, no implied affiliation")
check("home sub now «وزارة العدل المفتوحة»", "بيانات وزارة العدل المفتوحة" in HTML)
check("home officialness «العدل الفعلية» gone", "بيانات وزارة العدل الفعلية" not in HTML)
check("no-affiliation clause present in gate", "غير منتسبة لوزارة العدل" in HTML)
check("disc credit now «يستخدم بيانات وزارة العدل المفتوحة»", "يستخدم بيانات وزارة العدل المفتوحة" in HTML)
check("disc bare «بيانات وزارة العدل القطرية» credit gone", "ثمّن</span> — بيانات وزارة العدل القطرية" not in HTML)
check("api subtitle officialness «القطرية الرسمية» gone", "القطرية الرسمية" not in API)
check("api subtitle now open-data framed", "وزارة العدل المفتوحة (CC BY 4.0)" in API)

# [3] Contradiction fix: our output is «تقدير», never «تقييم»
print("\n[3] Self-reference contradiction fixed")
check("disc says «هذا التقدير إرشاديّ»", "هذا التقدير إرشاديّ" in HTML)
check("contradiction «هذا التقييم إرشادي» gone", "هذا التقييم إرشادي" not in HTML)

# [4] Trust-eroding framing softened (gate)
print("\n[4] Gate framing")
check("gate note «معلومة استرشاديّة لدعم القرار»", "معلومة استرشاديّة لدعم القرار" in HTML)
check("gate note «نتيجة بحثية» gone", "نتيجة بحثية" not in HTML)
check("gate sub «نطوّرها بملاحظاتك»", "نطوّرها بملاحظاتك" in HTML)
check("gate sub «هدفها قياس دقّة التقدير قبل الإطلاق» gone", "هدفها قياس دقّة التقدير قبل الإطلاق" not in HTML)

# [5] De-jargon: internal roadmap tag «(المرحلة الخامسة)» / «(Stage 5)» dropped from user copy
print("\n[5] De-jargon: rics_compliant status + methodology note")
import importlib
MU = importlib.import_module("material_uncertainty")
check("status AR = «بانتظار مراجعة مُقيِّم مُرخّص» (no roadmap tag)",
      MU.RICS_COMPLIANT_STATUS_PENDING_AR == "بانتظار مراجعة مُقيِّم مُرخّص")
check("status AR has no «المرحلة الخامسة»", "المرحلة الخامسة" not in MU.RICS_COMPLIANT_STATUS_PENDING_AR)
check("status EN = «Pending licensed-valuer review» (no Stage 5)",
      MU.RICS_COMPLIANT_STATUS_PENDING_EN == "Pending licensed-valuer review")
check("methodology note AR no longer carries «المرحلة الخامسة»", "المرحلة الخامسة" not in EU)
check("methodology note AR still discloses «دون مراجعة مُقيِّم مُرخّص»",
      "دون مراجعة مُقيِّم مُرخّص." in EU)

# [6] Backend emoji swept from the data-freshness banner (production functions, E14)
print("\n[6] data_freshness banner — no emoji")
DFmod = importlib.import_module("data_freshness")
for tier in ("fresh", "mild", "stale", "very_stale"):
    b = DFmod._render_banner("ديسمبر 2025", 167, tier)
    check(f"banner[{tier}] has no emoji", ("📅" not in b and "⚠" not in b))
c = DFmod._render_caveat("ديسمبر 2025", "very_stale")
check("caveat[very_stale] has no emoji", ("📅" not in c and "⚠" not in c))

# [7] Engine version bumped
print("\n[7] version")
check("ENGINE_VERSION bumped to b50", "thammen-sprint2p22p0b50-copy-honesty-source-contact" in EU)
check("SPRINT_TAG = 2.22.0b.50", "'2.22.0b.50'" in EU)

print(f"\n  {_passed} passed / {_failed} failed")
raise SystemExit(1 if _failed else 0)
