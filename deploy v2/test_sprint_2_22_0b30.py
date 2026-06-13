# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.30 «share-evidence copy» — isolated structural test.

FRONTEND-ONLY / VALUE-INVARIANT. Enriches copyResult() (the clipboard share artifact)
with EVIDENCE + PROVENANCE already broadcast/shown — so a shared copy answers «من أين الرقم؟»:
  - عدد الصفقات المقارِنة (n_transactions / moj_sample_size)
  - حداثة بيانات وزارة العدل (data_freshness.latest_record_ar + days_old)
  - the «ليس تقييماً معتمداً» honesty label (valued path only)
  - report_ref + the b23 /verify URL (via _verifyUrl)
No engine change (only the 2 version lines); no new value, no methodology change.

Run: PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b30.py
"""
import io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HTML = open("index.html", encoding="utf-8").read()
m = re.search(r"function copyResult\(\)\{.*?\n\}", HTML, re.S)
FN = m.group(0) if m else ""

passed = failed = 0
def chk(label, cond, detail=""):
    global passed, failed
    if cond: passed += 1; print(f"  PASS  {label}")
    else: failed += 1; print(f"  FAIL  {label}  {detail}")

chk("copyResult() found", bool(m))
fn_ns = FN.replace(" ", "")

# (1) the enrichment reads BROADCAST fields (no invented value)
chk("reads n_transactions (fallback moj_sample_size)",
    "v.n_transactions" in fn_ns and "d.moj_sample_size" in fn_ns)
chk("reads data_freshness.latest_record_ar + days_old",
    "d.data_freshness" in fn_ns and "latest_record_ar" in FN and "days_old" in FN)
chk("emits «عدد الصفقات المقارِنة»", "عدد الصفقات المقارِنة" in FN)
chk("emits «حداثة بيانات وزارة العدل»", "حداثة بيانات وزارة العدل" in FN)

# (2) the not-certified label — valued path only (guarded on v.amount)
chk("not-certified label present", "وليس تقييماً معتمداً" in FN)
chk("not-certified label guarded on v.amount (valued only)",
    re.search(r"if\(v\.amount\)lines\.push\('تقدير سوقيّ آليّ، وليس تقييماً معتمداً", fn_ns)
    or re.search(r"if\(v\.amount\)\s*lines\.push\('تقدير", FN.replace(" ", "")))

# (3) provenance — report_ref + verify URL via the shared _verifyUrl, guarded on report_ref
chk("report_ref line guarded on d.report_ref", "if(d.report_ref)" in fn_ns)
chk("emits «مرجع التقرير»", "مرجع التقرير" in FN)
chk("verify URL via _verifyUrl (shared b23/b25 builder)", "_verifyUrl(d)" in fn_ns)
chk("verify line guarded (only when _vu truthy)", re.search(r"if\(_vu\)", fn_ns) is not None)

# (4) value-invariance: the headline copy lines are UNTOUCHED + present
chk("headline «قيمة التقدير السوقي» still emitted", "قيمة التقدير السوقي" in FN)
chk("range line still emitted", "النطاق: " in FN)
chk("refusal branch (v.reason_ar) preserved", "v.reason_ar" in fn_ns)

# (5) the new evidence lines sit INSIDE the valued branch (not on refusal)
#     i.e. «عدد الصفقات» appears after «قيمة التقدير السوقي» and before the else-reason.
i_amount = FN.find("قيمة التقدير السوقي")
i_n = FN.find("عدد الصفقات المقارِنة")
i_reason = FN.find("v.reason_ar")
chk("evidence lines are inside the valued branch (amount < n < reason)",
    i_amount != -1 and i_n != -1 and i_reason != -1 and i_amount < i_n < i_reason)

# (6) engine version format (R6 — no exact pin)
eng = open("evaluate_unified.py", encoding="utf-8").read()
mv = re.search(r"ENGINE_VERSION = '([^']+)'", eng)
chk("ENGINE_VERSION format", bool(mv) and mv.group(1).startswith("thammen-sprint"))

print(f"\n{passed} PASS / {failed} FAIL")
sys.exit(1 if failed else 0)
