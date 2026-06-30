# -*- coding: utf-8 -*-
# Sprint 2.22.0b.58 — «إسقاط تأطير التجريبية» (drop the beta/trial framing).
# FRONTEND-ONLY, value-invariant (engine = the 2 version-string lines only).
#
# PO directive (2026-06-18): «الموقع يعمل بالفعل … احذف اي ذكر لكلمة تجريبية». Thammen is a LIVE
# product, NOT a beta. Remove «تجريبية / بالدعوة / beta / invite-only / before public launch /
# this beta» from the user-facing copy (gate affirmation + Terms/Privacy AR+EN + the English fold).
# PRESERVE the real cover (separate from the word "beta"): «ليس تقييماً معتمداً» + free + the
# consent + «غير منتسبة لوزارة العدل» + the CC BY 4.0 MoJ open-data attribution.
import re, pathlib

ROOT = pathlib.Path(__file__).parent
HTML = (ROOT / 'index.html').read_text(encoding='utf-8')
ENG  = (ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')
# only the user-VISIBLE body (strip HTML comments so internal-id comments don't count).
VIS  = re.sub(r'<!--.*?-->', '', HTML, flags=re.S)

results = []
def check(name, cond):
    results.append((name, bool(cond)))

# ── 1. NO user-facing beta/trial framing remains ──
check('no «تجريبية»', 'تجريبية' not in VIS)
check('no «بالدعوة» (invite-only)', 'بالدعوة' not in VIS)
check('no EN «free beta» / «accuracy beta»', 'free beta' not in VIS and 'accuracy beta' not in VIS)
check('no EN «invite-only»', 'invite-only' not in VIS)
check('no «before public launch»', 'before public launch' not in VIS and 'الإطلاق العام' not in VIS)
check('no «in this beta» / «this beta»', 'this beta' not in VIS)
check('no «في هذه النسخة» (beta-edition phrasing)', 'في هذه النسخة' not in VIS)

# ── 2. The reworded copy is present (live service, not beta) ──
check('Terms header «الخدمة المجانية»', 'الخدمة المجانية' in HTML)
check('Terms §1 title «الموافقة على الاستخدام»', '1) الموافقة على الاستخدام' in HTML)
check('Terms §1 body «هذه خدمة مجانية»', 'هذه خدمة مجانية. باستخدامك' in HTML)
check('Terms §3 «بياناتك في هذه الخدمة»', 'بياناتك في هذه الخدمة' in HTML)
check('gate affirmation «وأوافق على الاستخدام»', 'وأوافق على الاستخدام على الأساس' in HTML)
check('EN Terms header «(free service)»', 'Terms of Use &amp; Privacy Notice (free service)' in HTML)
check('EN Terms §1 «A free service»', 'A free service. By using the tool' in HTML)
check('EN §3 «Your data» (not «in this beta»)', '<h4>3) Your data</h4>' in HTML)

# ── 3. The real cover is PRESERVED (free + not-certified + consent + no-affiliation + CC-BY) ──
check('«ليس تقييماً معتمداً» kept', 'ليس تقييماً معتمداً' in HTML)
check('free framing kept («خدمة مجانية»)', 'خدمة مجانية' in HTML)
check('consent affirmation core kept',
      'أُقرّ بأنني فهمت أن ثمّن تقييم سوقيّ آليّ للدعم وليس تقييماً معتمداً' in HTML)
check('«غير منتسبة لوزارة العدل» kept', 'غير منتسبة لوزارة العدل' in HTML)
check('CC BY 4.0 attribution kept', 'CC BY 4.0' in HTML and 'creativecommons.org/licenses/by/4.0' in HTML)
check('consent gate dialog kept (id internal, not user-facing)', 'id="betaGate"' in HTML and 'role="dialog"' in HTML)
check('Terms modal still reachable (openTerms)', 'openTerms()' in HTML)

# ── 4. No regression of b57 (esc) / value-invariance ──
check('b57 esc() helper intact', 'function esc(s){' in HTML and "ri(t('العنوان','Address'),esc(d.address),0,1)" in HTML)
check('no mutation of v.amount/v.low/v.high', not re.search(r'\bv\.(amount|low|high)\s*=[^=]', HTML))

# ── 5. Engine version (format only — R6 / Lesson-2: no exact pin) ──
check('ENGINE_VERSION format (thammen-sprint…)',
      re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+", ENG) is not None)
check('SPRINT_TAG dotted-numeric format', re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+", ENG) is not None)
check('engine at/beyond b58 (b57 tag gone)', 'thammen-sprint2p22p0b57' not in ENG)

passed = sum(1 for _, ok in results if ok)
for name, ok in results:
    print(('PASS' if ok else 'FAIL'), '-', name)
print('\n%d/%d passed' % (passed, len(results)))
assert passed == len(results), '%d FAILED' % (len(results) - passed)
