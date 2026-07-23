# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.141 — «ترشيق شاشة النتيجة» (result-screen declutter).

Isolated E14 test (reads the REAL index.html + evaluate_unified.py). Value-neutral /
presentation-only — the result-screen de-duplication the PO reported («تفاصيل مكرّرة»):
  (1) the trend renders ONCE (the EVIDENCE `_s4bTrendSpark` sparkline); the duplicate
      bar-chart in the «تحليل إضافي» fold (show() `h` buffer) removed.
  (2) the known-unknowns render ONCE — the always-visible LIMITS `_s4bLimits`, now
      UNCAPPED (`ku` instead of `ku.slice(0,6)`); the duplicate fold card removed
      (nothing lost). The full report keeps its own trend + known-unknowns.
  (3) the «التفاصيل الكاملة» naming collision resolved: the result-screen fold →
      «تحليل إضافيّ» / "Deeper analysis"; the two nav-back-to-result labels → «النتيجة» /
      "Result", so «التقرير الكامل» is unambiguously the deepest artifact.
  (4) B1 — the market-pulse band is gated on `hasValuation` (must not render under a
      refusal card).
"""
import io, sys

ROOT = r"C:\Thammen\deploy v2"
HTML = io.open(ROOT + r"\index.html", encoding="utf-8").read()
ENG  = io.open(ROOT + r"\evaluate_unified.py", encoding="utf-8").read()

passed = failed = 0
def ck(name, cond):
    global passed, failed
    if cond: passed += 1; print("  PASS", name)
    else:    failed += 1; print("  FAIL", name)

print("Sprint 2.22.0b.141 — result-screen declutter\n")

# ── (1) trend: fold trend KEPT — the signed a3/T1.2 «اتجاه تاريخي» honesty lives here ─────
#     (deduping the fold bar-chart vs the EVIDENCE sparkline is DEFERRED to a signed honesty
#      review, since it would drop the signed suppressed-slope reframe. So Sprint 2 leaves it.)
print("[trend — kept (T1.2 honesty preserved)]")
ck("EVIDENCE sparkline present",  "h+=_s4bTrendSpark(d);" in HTML)
ck("_s4bTrendSpark defined",      "function _s4bTrendSpark(d){" in HTML)
ck("fold trend bar-chart KEPT",   'class="trend-col" style="height:${Math.max(pct,5)}%"' in HTML)
ck("T1.2 «اتجاه تاريخي» reframe KEPT", "t('اتجاه تاريخي: ','Historical trend: ')" in HTML)
ck("b141 defer note present",     "deduping it vs the EVIDENCE sparkline is deferred" in HTML)

# ── (2) known-unknowns de-dup + LIMITS uncap ────────────────────────────────
print("[known-unknowns de-dup]")
ck("LIMITS uncapped (ku.forEach)",  "ku.forEach(function(u){h+='<div class=\"li\">" in HTML)
ck("LIMITS cap REMOVED (no slice(0,6))", "ku.slice(0,6)" not in HTML)
ck("fold known-unknowns REMOVED (show() rtr)", "rtr.known_unknowns.forEach(u=>{h+='• '+u+'<br>'})" not in HTML)
# b142 R6: the report known-unknowns read now goes through pickArr (EN twin in EN mode); still KEPT + full.
ck("full-report known-unknowns KEPT (_rtrR, b142 pickArr)",  "pickArr(_rtrR,'known_unknowns').forEach(u=>{h+='• '+u+'<br>'})" in HTML)
ck("LIMITS «ما لا نراه بعد» kept", "t('ما لا نراه بعد','What we don\\'t see yet')" in HTML)

# ── (3) «التفاصيل الكاملة» naming collision resolved ─────────────────────────
print("[naming]")
ck("fold → «تحليل إضافيّ»", "t('تحليل إضافيّ (التفاصيل والمقارنات)','Deeper analysis (details &amp; comparables)')" in HTML)
ck("old fold title gone", "التفاصيل الكاملة (التحليل والمقارنات)" not in HTML)
ck("short-report back button → «النتيجة»", 'data-en="← Result">→ النتيجة</button>' in HTML)
ck("short-report link → «النتيجة»", "<a onclick=\"go(\\'results\\')\">'+t('النتيجة','Result')+'</a>" in HTML)
ck("«التفاصيل الكاملة» no longer a nav-label t()", "t('التفاصيل الكاملة','Full details')" not in HTML)
# the full report is the deepest, still labelled «التقرير الكامل»
ck("«التقرير الكامل» intact", "t('التقرير الكامل','Full report')" in HTML)

# ── (4) B1 pulse gate ───────────────────────────────────────────────────────
print("[B1 pulse gate]")
ck("pulse gated on hasValuation", "if(hasValuation&&d.district&&d.asset_type){var _pb=document.createElement('div');_pb.className='rs-sec';_pb.id='pulseBand'" in HTML)
ck("old ungated pulse gone", "if(d.district&&d.asset_type){var _pb=document.createElement('div');_pb.className='rs-sec';_pb.id='pulseBand'" not in HTML)

# ── (5) version + value-neutral ─────────────────────────────────────────────
print("[version + value-neutral]")
# b142 R6 (Lesson-2): version-agnostic — the exact-version pin broke on the b142 bump.
ck("engine version b-series", "thammen-sprint2p22p0b1" in ENG)
ck("sprint tag b-series",     "SPRINT_TAG = '2.22.0b.1" in ENG)
ck("_s4bLimits intact",   "function _s4bLimits(d,muc){" in HTML)
ck("engine has no result-screen logic (frontend-only)", "def show(" not in ENG and "_s4bTrendSpark" not in ENG)

print("\n%d passed, %d failed" % (passed, failed))
sys.exit(1 if failed else 0)
