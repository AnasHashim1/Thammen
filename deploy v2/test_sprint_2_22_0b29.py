# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.29 «هبوط المختصر» (إتمام D6) — isolated structural tests.

FRONTEND-ONLY / VALUE-INVARIANT. Reads the REAL index.html (E14) and pins:
  (1) the post-refine landing branch inside thammenReEvalGeometry (short-first,
      gated: non-valuer + b20-journey family [villa/house/raw_land] + amount>0);
  (2) run()'s confirm routing UNTOUCHED (the v4 two-path);
  (3) the signed two buttons in the short report («التفاصيل الكاملة» -> b15 screen
      + «التقرير الكامل» -> the full report) + the wrapper relabel;
  (4) the report screen's wrapper UNTOUCHED;
  (5) a Python mirror of the landing gate over the 8 routing shapes.

Run: PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b29.py
"""
import io
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HTML = open("index.html", encoding="utf-8").read()

passed = failed = 0
def chk(label, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS  {label}")
    else:
        failed += 1
        print(f"  FAIL  {label}  {detail}")


# ── (1) the landing branch lives INSIDE thammenReEvalGeometry ────────────────
m = re.search(r"async function thammenReEvalGeometry\(\)\{.*?\n\}", HTML, re.S)
chk("thammenReEvalGeometry found", bool(m))
fn = m.group(0) if m else ""

chk("landing: show(data) still precedes the branch (b15 buffer stays populated)",
    fn.find("show(data);") >= 0 and fn.find("show(data);") < fn.find("_sr29"))
chk("landing: asset gate = _b2IsBuilding || raw_land",
    "_sr29=(_b2IsBuilding(data.asset_type)||data.asset_type==='raw_land')" in fn.replace(" ", "")
    or re.search(r"_sr29\s*=\s*\(\s*_b2IsBuilding\(data\.asset_type\)\s*\|\|\s*data\.asset_type==='raw_land'\s*\)", fn))
chk("landing: valuer gate mirrors run() (audience!=='valuer')",
    "audience!=='valuer'&&_sr29" in fn.replace(" ", ""))
chk("landing: value gate amount!=null && amount>0",
    "_v29.amount!=null&&_v29.amount>0" in fn.replace(" ", ""))
chk("landing: short branch = showShortReport(data) + go('shortReport')",
    re.search(r"showShortReport\(data\);\s*go\('shortReport'\)", fn))
chk("landing: else branch keeps go('results')",
    re.search(r"else\{\s*go\('results'\);?\s*\}", fn))

# ── (2) run()'s confirm routing untouched (the v4 two-path) ──────────────────
mrun = re.search(r"async function run\(\)\{.*?\n\}", HTML, re.S)
run_fn = mrun.group(0) if mrun else ""
chk("run() found", bool(mrun))
chk("run(): confirm gate verbatim (valued non-valuer -> confirm)",
    "if(audience!=='valuer'&&_cgv.amount!=null&&_cgv.amount>0){showConfirm(data);go('confirm');}" in run_fn)
chk("run(): valuer/refusal fallback go('results') intact",
    "else{go('results');}" in run_fn.replace(" ", "").replace("\n", "")
    or re.search(r"else\{go\('results'\);\}", run_fn))
chk("run(): does NOT short-land (no showShortReport in run())",
    "showShortReport" not in run_fn)

# ── (3) the signed two buttons + the wrapper relabel ─────────────────────────
mbtn = re.search(r"<div class=\"thmr-btns\">.*?</div>';", HTML[HTML.find("function showShortReport"):], re.S)
# the VALUED body's button row (the refusal stub has its own single-button row)
rows = re.findall(r"thmr-btns(?:\\?'|\")>(.*?)</div>'", HTML, re.S)
valued_row = next((r for r in rows if "التفاصيل الكاملة" in r), "")
chk("short report: «التفاصيل الكاملة» button present in the thmr-btns row", bool(valued_row))
chk("short report: «التفاصيل الكاملة» targets go('results') (the b15 screen)",
    re.search(r"onclick=\\?\"go\(\\?'results\\?'\)\\?\">التفاصيل الكاملة", valued_row.replace("\\'", "'"))
    or "onclick=\"go('results')\">التفاصيل الكاملة" in valued_row.replace("\\'", "'"))
chk("short report: «التقرير الكامل» (الكامل) still targets openReport()",
    "openReport()" in valued_row and "التقرير الكامل" in valued_row)
chk("short report: button order الملحق -> التفاصيل -> الكامل -> طباعة",
    valued_row.find("الملحق المتخصص") < valued_row.find("التفاصيل الكاملة")
    < valued_row.find("التقرير الكامل") < valued_row.find("طباعة"))
chk("short report: refusal stub still routes to openReport (untouched)",
    re.search(r"لم يصدر تقدير لهذا العقار.*?openReport\(\)", HTML, re.S))

# the shortReportScreen wrapper relabel
msr = re.search(r"id=\"shortReportScreen\".*?<div id=\"srOut\"", HTML, re.S)
sr_wrap = msr.group(0) if msr else ""
sr_wrap_buttons = re.findall(r"<button[^>]*>([^<]*)</button>", sr_wrap)
chk("shortReportScreen wrapper: button relabeled «→ التفاصيل الكاملة» (old label gone from buttons)",
    any("→ التفاصيل الكاملة" in b for b in sr_wrap_buttons)
    and not any("رجوع للنتيجة" in b for b in sr_wrap_buttons))
chk("shortReportScreen wrapper: still targets go('results')",
    re.search(r"onclick=\"go\('results'\)\">→ التفاصيل الكاملة", sr_wrap))

# ── (4) the FULL report screen's wrapper untouched ───────────────────────────
mrep = re.search(r"id=\"reportScreen\".*?<div id=\"repOut\"", HTML, re.S)
rep_wrap = mrep.group(0) if mrep else ""
chk("reportScreen wrapper: «→ رجوع للنتيجة» untouched", "→ رجوع للنتيجة" in rep_wrap)

# ── (5) CSS: the 4-button row wraps on mobile ────────────────────────────────
chk("CSS: .thmr-btns has flex-wrap:wrap", re.search(r"\.thmr-btns\{[^}]*flex-wrap:wrap", HTML))
chk("CSS: .thmr-btn flex-basis allows a 2x2 grid", re.search(r"\.thmr-btn\{flex:1 1 4\d%", HTML))

# ── (6) the b15 TIER-3 entry still short-first (D6 at the report entry) ──────
chk("b15 TIER-3 CTA still -> openShortReport (untouched)", "openShortReport()" in HTML)

# ── (7) engine version: format-only (R6 — no exact pin) ─────────────────────
eng = open("evaluate_unified.py", encoding="utf-8").read()
mv = re.search(r"ENGINE_VERSION = '([^']+)'", eng)
mt = re.search(r"SPRINT_TAG = '([^']+)'", eng)
chk("ENGINE_VERSION format", bool(mv) and mv.group(1).startswith("thammen-sprint"))
chk("SPRINT_TAG dotted-numeric format", bool(mt) and re.match(r"^\d+\.\d+\.\d+", mt.group(1)))

# ── (8) Python mirror of the landing gate over the routing shapes ───────────
def lands_on_short(audience, asset_type, amount):
    """Mirror of the b29 governing expression (pinned above)."""
    sr_ok = asset_type in ("standalone_villa", "villa", "house") or asset_type == "raw_land"
    return audience != "valuer" and sr_ok and amount is not None and amount > 0

SHAPES = [
    ("villa owner valued -> SHORT",        ("owner",  "standalone_villa", 2_400_000), True),
    ("house buyer valued -> SHORT",        ("buyer",  "house",            2_500_000), True),
    ("raw land owner valued -> SHORT",     ("owner",  "raw_land",         1_200_000), True),
    ("villa VALUER valued -> results",     ("valuer", "standalone_villa", 2_400_000), False),
    ("apartment valued -> results (gate)", ("owner",  "apartment_building", 8_529_231), False),
    ("compound valued -> results (gate)",  ("owner",  "compound_large",   44_000_000), False),
    ("villa refusal (None) -> results",    ("owner",  "standalone_villa", None),      False),
    ("villa zero amount -> results",       ("owner",  "standalone_villa", 0),         False),
]
for label, args, want in SHAPES:
    chk(f"mirror: {label}", lands_on_short(*args) == want)

print(f"\n{passed} PASS / {failed} FAIL")
sys.exit(1 if failed else 0)
