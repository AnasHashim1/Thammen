# -*- coding: utf-8 -*-
# Sprint 2.22.0b.57 — «تحصين الواجهة» frontend hardening (esc/XSS insurance + gate fallback + null-guards).
# FRONTEND-ONLY, value-invariant (engine = the 2 version-string lines only).
# Reads the REAL index.html (E14 / Rule #40 for the frontend lane) + asserts the engine bump.
#
# The hardening contract (PO chose the value-invariant frontend hardening; audit §plan):
#   - An esc() HTML-escape helper is added and applied to the PLAIN-DATA fields injected into
#     innerHTML (address / district / asset-label / GIS area-names) — defense-in-depth.
#   - The engine-authored *_ar NOTE/CLAUSE fields (which carry intended HTML markup and are
#     trusted our-engine output) are LEFT AS-IS — esc()'ing them would break formatting.
#   - Gate window._betaAck fallback honored by the pre-paint script; value_stack.cost label/sub
#     ||'' guards; openMapPicker coords coerced to Number.
#   - VALUE-INVARIANT: api.py + engine UNTOUCHED; the headline figure is never recomputed.
import re, pathlib

ROOT = pathlib.Path(__file__).parent
HTML = (ROOT / 'index.html').read_text(encoding='utf-8')
ENG  = (ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')
REP  = HTML[HTML.index('function showReport(d){'):HTML.index('function printReportA4(')]

results = []
def check(name, cond):
    results.append((name, bool(cond)))

# ── 1. esc() helper defined + escapes the dangerous chars ──
check('esc() helper defined', 'function esc(s){' in HTML)
check('esc() escapes < > & " \'',
      "'<':'&lt;'" in HTML and "'>':'&gt;'" in HTML and "'&':'&amp;'" in HTML
      and "'\"':'&quot;'" in HTML and '"\'":\'&#39;\'' in HTML)
check('esc() null-safe (s==null → empty)', "function esc(s){return s==null?'':" in HTML)

# ── 2. esc() applied to the PLAIN-DATA fields (address / district / asset-label) ──
check('address via esc (ri)', "ri(t('العنوان','Address'),esc(d.address),0,1)" in HTML
      and "ri('العنوان',d.address,0,1)" not in HTML)
check('district via esc (ri)', "ri(t('المنطقة','District'),esc(d.district))" in HTML
      and "ri('المنطقة',d.district)" not in HTML)
check('asset-label via esc (ri)', "ri(t('نوع العقار','Property type'),esc(" in HTML
      and "ri('نوع العقار',(d.asset_type" not in HTML)
check('report rep-addr via esc', '<div class="rep-addr">\'+esc(d.address)+\'</div>' in HTML)
check('report district span via esc (b81: label moved into t(), esc kept)', "t('المنطقة: ','District: ')+esc(d.district)+'</span>" in HTML)
check('short-report row address+district via esc',  # b98 R6: district dedup-guarded, still esc()
      "esc(d.address||'')" in HTML and "===-1)?(' · '+esc(d.district)):''" in HTML)
check('income cap-cell district via esc', "<span class=\"v\">'+esc(pick(d.cap_rate_provenance,'district')" in HTML)  # b80 R6: district_ar → pick(), still esc()-wrapped
check('refusal flat address+district via esc',
      "<strong>'+t('العنوان:','Address:')+'</strong> '+esc(d.address)+'</div>" in HTML
      and "<strong>'+t('المنطقة:','District:')+'</strong> '+esc(d.district)+'</div>" in HTML)
check('assetAr value esc at definition', 'const assetAr=esc(' in HTML)
# b125 R6: the result-screen keystone (with its neighbour rows) became the flat _s4bEvidence table; the
# geo NEIGHBOUR rows with a source-area name now render only in the full report (_repComparables), where
# the area name stays esc()-escaped. The XSS-insurance intent (area-name names escaped) is preserved.
check('comparable/neighbour area-name via esc (report builder)', 'esc(r.source_area' in HTML)
check('comparable-row area via esc', "row(t('المنطقة','District'),esc(c.area))" in HTML)

# ── 3. The engine-authored *_ar NOTE/CLAUSE fields are LEFT RAW (intended HTML, trusted) ──
check('condition_note_ar NOT esc-wrapped (formatting preserved)',
      'v.condition_note_ar' in HTML and 'esc(v.condition_note_ar)' not in HTML)
check('leadership.note_ar NOT esc-wrapped',
      'v.leadership.note_ar' in HTML and 'esc(v.leadership.note_ar)' not in HTML)
check('MUC clause builder NOT esc-wrapped', '_mucCardHtml(' in HTML and 'esc(muc_ar' not in HTML)
check('hbu_note_ar NOT esc-wrapped', 'v.hbu_note_ar' in HTML and 'esc(v.hbu_note_ar)' not in HTML)

# ── 4. The 3 small fixes ──
check('gate window._betaAck fallback honored (pre-paint script)',
      "sessionStorage.getItem('thammen_beta_ack')==='1'||window._betaAck){var g" in HTML)
check('value_stack.cost label/sub null-safe (b81: pick() returns "" when absent — supersedes the ||\'\' guard)',
      "pick(v.value_stack.cost,'label')" in HTML and "pick(v.value_stack.cost,'sub')" in HTML)
check('openMapPicker coords coerced to Number',
      "openMapPicker('+Number(lat)+','+Number(lon)+')" in HTML
      and "openMapPicker('+lat+','+lon+')" not in HTML)

# ── 5. VALUE-INVARIANCE — the frontend never recomputes the headline ──
check('no mutation of v.amount/v.low/v.high', not re.search(r'\bv\.(amount|low|high)\s*=[^=]', HTML))

# ── 6. No regression of the just-shipped b55/b56 surfaces ──
check('b55 note-clusters intact', 'rep-cl-h' in HTML and 'حول الرقم' in REP)
check('b56 gate trim intact (no «اعرف المزيد» fold)', 'اعرف المزيد عن النسخة' not in HTML)
check('CC BY 4.0 attribution kept on results', 'CC BY 4.0' in HTML and 'creativecommons.org/licenses/by/4.0' in HTML)
check('«ليس تقييماً معتمداً» kept', 'ليس تقييماً معتمداً' in HTML)

# ── 7. Engine version (format only — R6 / Lesson-2: no exact pin) ──
check('ENGINE_VERSION format (thammen-sprint…)',
      re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+", ENG) is not None)
check('SPRINT_TAG dotted-numeric format', re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+", ENG) is not None)
check('engine at/beyond b57 (b56 tag gone)', 'thammen-sprint2p22p0b56' not in ENG)

passed = sum(1 for _, ok in results if ok)
for name, ok in results:
    print(('PASS' if ok else 'FAIL'), '-', name)
print('\n%d/%d passed' % (passed, len(results)))
assert passed == len(results), '%d FAILED' % (len(results) - passed)
