# -*- coding: utf-8 -*-
"""
Sprint 2.22.0b.89 — «توحيد الجمهور» (Option A: remove the «من أنت؟» role selector →
one neutral entry) — isolated test (reads the REAL index.html + evaluate_unified.py, E14).

🟢 FRONTEND-ONLY / VALUE-INVARIANT. The number is audience-invariant (b24) and the hero
label is neutral (b54/b88), so the upfront role step was pure friction (Gemini r6 + PO
2026-07-01). `audience` stays 'owner' by default (engine normalizes owner→buyer). The
buyer-only financing calculator (b35 result + b63 short report) is un-gated to an OPTIONAL
collapsed toggle for EVERYONE.
"""
import io, re, sys

def _read(p):
    return io.open(p, encoding='utf-8').read()

H = _read('index.html')
EU = _read('evaluate_unified.py')
n = 0
def ok(cond, msg):
    global n
    assert cond, 'FAIL: ' + msg
    n += 1
    print('  ok:', msg)

print('Sprint 2.22.0b.89 — audience unification (Option A)')

# ── 1) the «من أنت؟» role selector is REMOVED ──────────────────────────────
ok("onclick=\"selAud(this,'owner')\"" not in H, "the owner role-button (selAud owner) is removed")
ok("onclick=\"selAud(this,'buyer')\"" not in H, "the buyer role-button (selAud buyer) is removed")
ok("onclick=\"selAud(this,'seller')\"" not in H, "the seller role-button is removed")
ok("onclick=\"selAud(this,'investor')\"" not in H, "the investor role-button is removed")
ok("onclick=\"selAud(this,'valuer')\"" not in H, "the valuer role-button is removed")
# the 5-button audience grid is gone (the remaining .aud-row is the address/PIN input tab — selTab)
ok("selTab('address')" in H and "selTab('land')" in H, "the address/PIN input tab (selTab) is UNTOUCHED")
# audience default stays 'owner' (engine normalizes owner→buyer → value-invariant)
ok(re.search(r"let\s+audience\s*=\s*'owner'", H), "audience default stays 'owner' (value-invariant)")

# ── 2) financing calculator un-gated → collapsed toggle for EVERYONE ────────
# RESULT screen (b35): old buyer-gate gone; new un-gated form + fin-toggle
ok("if(d.audience==='buyer'&&v.amount&&d.asset_type!=='raw_land')" not in H,
   "result-screen financing is NO LONGER audience==='buyer' gated")
ok("if(v.amount&&v.amount>0&&d.asset_type!=='raw_land'){" in H,
   "result-screen financing is un-gated (all valued non-land)")
# SHORT report (b63): old buyer-gate gone; new un-gated form
ok("if((d.audience||'owner')==='buyer'){" not in H,
   "short-report financing is NO LONGER (d.audience||'owner')==='buyer' gated")
ok("if(hasVal&&d.asset_type!=='raw_land'){" in H,
   "short-report financing is un-gated (valued non-land)")
# the collapsed toggle exists on BOTH surfaces
ok(H.count('class="fin-toggle"') >= 2 or H.count('fin-toggle') >= 3,
   "the fin-toggle (collapsed) wraps financing on BOTH result + short report")
ok(H.count('حاسبة التمويل الاسترشاديّة') >= 2, "the financing toggle title appears on both surfaces")
ok('.fin-toggle summary::-webkit-details-marker{display:none}' in H, "the fin-toggle marker-hide CSS is present")

# ── 3) the calculator internals are PRESERVED (DRY, b25/b35 contract) ───────
ok('bcRecalc()' in H and 'srRecalcPay()' in H, "bcRecalc + srRecalcPay reused (DRY)")
ok('_srPayment(' in H, "the shared _srPayment amortization is reused")
for _id in ('bcDown', 'bcYears', 'bcRate', 'bcPay', 'srDown', 'srYears', 'srRate', 'srPay'):
    ok('id="' + _id + '"' in H, "financing input id preserved: " + _id)
ok('استشر بنكك' in H, "the «استشر بنكك» disclosure is kept")
ok('value="20"' in H and 'value="25"' in H and 'value="4.5"' in H,
   "the signed b28 defaults (20% · 25y · 4.5%) are kept")

# ── 4) value-invariance guard: financing is display-only (never mutates the value) ──
# the gate reads v.amount but never assigns v.amount / v.low / v.high in the block
_finblk = H[H.find('Indicative financing calculator'):H.find('Indicative financing calculator')+2000]
ok('v.amount=' not in _finblk and 'v.low=' not in _finblk and 'v.high=' not in _finblk,
   "the financing block never mutates amount/low/high (display-only)")

# ── 5) engine version bumped to b89 (format, R6 — no exact-version dependence elsewhere) ──
ok(re.search(r"ENGINE_VERSION\s*=\s*'thammen-sprint2p22p0b\d", EU), "ENGINE_VERSION is a b-series tag (R6, version-agnostic)")
ok(re.search(r"SPRINT_TAG = '2\.22\.0b\.\d", EU), "SPRINT_TAG is a 2.22.0b-series tag (R6)")

print('\n%d/%d checks passed — Sprint 2.22.0b.89 GREEN' % (n, n))
