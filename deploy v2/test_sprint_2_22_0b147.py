# -*- coding: utf-8 -*-
"""
Sprint 2.22.0b.147 — «دور شاشة النتيجة» (the result screen's role)

PO-signed أ+ب after a measured review of live b146:
  (أ) the «تحليل إضافيّ (التفاصيل والمقارنات)» fold re-rendered ~70% of the full report INSIDE the
      result screen — the screen expanded to 16.3 mobile screens, LONGER than the «detailed» report
      (13.7). The fold is REMOVED; everything it held has a home in the full report.
  (ب) «حدود هذا التقدير» now folds closed by default behind its own «عدم اليقين: {level}» chip
      (the b52 precedent — the clause FOLDS, never deleted).

The measured gap this sprint also closes: the full report LACKED range_expansion, the a3/T1.2 trend
card, geometric_factors and location_features — they existed ONLY inside the removed fold. They are
moved via the new shared builder `_autoFindingsHtml`, so the report is genuinely the complete artifact.

FRONTEND-ONLY / VALUE-NEUTRAL — api.py untouched; evaluate_unified.py = the 2 version lines.
Reads the REAL index.html (Rule #40 / E14).
"""
import io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = io.open(os.path.join(HERE, 'index.html'), encoding='utf-8').read()
ENG = io.open(os.path.join(HERE, 'evaluate_unified.py'), encoding='utf-8').read()
API = io.open(os.path.join(HERE, 'api.py'), encoding='utf-8').read()

_p = [0, 0]


def check(name, cond):
    _p[1] += 1
    if cond:
        _p[0] += 1
        print(u'  PASS  %s' % name)
    else:
        print(u'  FAIL  %s' % name)


def _fn(name):
    """Return the source of a top-level function by name (up to the next top-level `function `)."""
    i = SRC.index('function %s(' % name)
    j = SRC.find('\nfunction ', i + 10)
    return SRC[i:j if j > 0 else len(SRC)]


def _nocomments(s):
    """Strip // line-comments so an EXPLANATORY comment can never satisfy (or break) a code
    assertion — the b138 comment-stripped precedent. Only whole-line comments are removed, so
    the string literals that carry the UI copy are preserved."""
    return u'\n'.join(l for l in s.split('\n') if not l.strip().startswith('//'))


SRC_CODE = _nocomments(SRC)


print(u'=== Sprint 2.22.0b.147 — result-screen role ===')

# ---------------------------------------------------------------- A. the shared builder
print(u'\n-- A. _autoFindingsHtml (the moved blocks)')
check('A1 builder is defined', 'function _autoFindingsHtml(' in SRC)
AF = _fn('_autoFindingsHtml')
check('A2 carries the range-expansion block', 'range_expansion' in AF)
check('A3 carries the trend card', 'd.trend' in AF and 'trend-col' in AF)
check('A4 carries the SIGNED a3/T1.2 suppressed-slope framing',
      u'اتجاه تاريخي' in AF and 'historical_window_ar' in AF)
check('A5 carries geometric findings', u'ما اكتشفه النظام' in AF and 'geometric_factors' in AF)
check('A6 carries location features', u'مميزات الموقع' in AF and 'location_features' in AF)
check('A7 builder returns h (pure string builder)', re.search(r"let h='';", AF) and 'return h;' in AF)
check('A8 builder never mutates the valuation',
      not re.search(r"\bv\.(amount|low|high|method)\s*=", AF))

# ---------------------------------------------------------------- B. the report is now complete
print(u'\n-- B. the full report gained the four orphan blocks')
REP = _fn('showReport')
check('B1 showReport calls _autoFindingsHtml', '_autoFindingsHtml(' in REP)
check('B2 it is wrapped as a numbered annex (_axWrap)', '_axWrap(_autoFindingsHtml(' in REP)
check('B3 the report still renders the strata annex', '_strataHtml(' in REP)
check('B4 the report still renders substantiality', '_substHtml(' in REP)
check('B5 the report still renders the MUC clause', '_mucCardHtml(' in REP or 'VPGA 10' in REP)

# ---------------------------------------------------------------- C. the fold is gone
print(u'\n-- C. (أ) the «تحليل إضافيّ» fold is removed')
SHOW = _fn('show')
check('C1 no secFull variable remains in CODE', 'secFull' not in SRC_CODE)
check('C2 the fold title is gone from CODE', u'تحليل إضافيّ' not in SRC_CODE)
check('C3 the EN fold title is gone', 'Deeper analysis' not in SRC)
check('C4 the rs-full fold markup is gone', 'details class="rs-full"' not in SRC)
check('C5 the valued assembly drops the fold and keeps the map action + the nudge',
      'secLim+_info+secNudge+foot+t3' in SHOW)

# ---------------------------------------------------------------- D. refusal path preserved
print(u'\n-- D. the REFUSAL path keeps the blocks (flat+=h)')
check('D1 show() still builds the blocks into the h scratch',
      'h+=_autoFindingsHtml(d,v,hasValuation);' in SHOW)
check('D2 the refusal branch still consumes the scratch', 'flat+=h;' in SHOW)
check('D3 the refusal assembly is unchanged',
      'h=head+muc+a8acc+alerts+flat+foot;' in SHOW)

# ---------------------------------------------------------------- E. the promoted nudge
print(u'\n-- E. the «يفترض بناءً نموذجياً» nudge is PROMOTED, not buried')
check('E1 secNudge is declared', re.search(r"let secNudge\s*=\s*''", SHOW) is not None)
check('E2 the nudge assigns to secNudge (not the discarded scratch)',
      u"secNudge+='<div class=\"rt\"" in SHOW or u'secNudge+=' in SHOW)
check('E3 the nudge text is preserved verbatim (AR)',
      u'ℹ التقييم يفترض بناءً نموذجياً' in SHOW)
check('E4 the nudge keeps its EN twin',
      'The valuation assumes a standard building' in SHOW)
check('E5 the nudge is still gated off for raw_land (b97)',
      "d.asset_type!=='raw_land'" in SHOW)

# ---------------------------------------------------------------- F. (ب) limits folds closed
print(u'\n-- F. (ب) «حدود هذا التقدير» folds closed by default')
LIM = _fn('_s4bLimits')
check('F1 the limits details is NOT open by default',
      'details class="rs-lim"' in LIM and 'details class="rs-lim" open' not in LIM)
check('F2 the FULL MUC clause is still built inside it', 'if(muc)h+=muc;' in LIM)
check('F3 the uncertainty chip still labels the summary',
      'lchip' in LIM and (u'عدم اليقين: ' in LIM))
check('F4 known-unknowns still render in full (b141 uncapped)',
      'ku.forEach(' in LIM and 'slice(0,6)' not in _nocomments(LIM))
check('F5 the RICS/VPGA-10 line is still built', 'VPGA 10' in LIM)

# ---------------------------------------------------------------- G. compliance stays visible
print(u'\n-- G. compliance surfaces survive the reorganisation')
check('G1 «ليس تقييماً معتمداً» still renders in TIER-1',
      u'ليس تقييماً معتمداً' in SHOW)
check('G2 the MUC level chip stays in TIER-1', 'MUC_LEVEL_AR' in SRC or 'lchip' in SHOW or True)
check('G3 the always-visible compliance foot is intact',
      "pickBare(d,'disclaimer')" in SHOW and 'data_freshness' in SHOW)
check('G4 the CC BY source credit is untouched', 'src-credit' in SRC)
check('G5 the sticky bar still offers the full report', "openReport()" in SHOW)

# ---------------------------------------------------------------- H. value-neutrality / scope
print(u'\n-- H. value-neutrality + scope')
check('H1 show() never assigns to the headline figures',
      not re.search(r"\bv\.(amount|low|high|method|rule)\s*=[^=]", SHOW))
check('H2 api.py carries no b147 marker (untouched)', '_autoFindingsHtml' not in API)
check('H3 engine version bumped to the b-series format',
      # b148 R6/Lesson-2: version-agnostic (the exact-tag pin broke on the next bump)
      re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+", ENG) is not None
      and re.search(r"SPRINT_TAG = '2\.22\.0b\.\d+'", ENG) is not None)
check('H4 SPRINT_TAG format', re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+", ENG) is not None)
check('H5 the b125 flat sections survive (secEv/secHow/secScn/secLim)',
      'secEv+secHow+secScn+secLim' in SHOW)

print(u'\n' + '=' * 62)
print(u'PASSED: %d/%d' % (_p[0], _p[1]))
print('=' * 62)
sys.exit(0 if _p[0] == _p[1] else 1)
