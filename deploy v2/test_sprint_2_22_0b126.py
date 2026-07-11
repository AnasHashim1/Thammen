# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.126 — «.rv reveal/value collision hotfix».

Live bug (Anas, two iPhone screenshots): every INFO-ROW VALUE was invisible — on the confirm screen
(«راجِع بيانات العقار») AND inside the result-screen «التفاصيل الكاملة» fold. Root: the b120 (S0)
scroll-reveal primitive was authored as a BARE `.rv{opacity:0}` selector, which collides with the
long-standing INFO-ROW VALUE class — `ri(l,v)` renders the value into `<div class="rv">` (+ `.calc-block .rv`,
`.rv hl`). So `.rv{opacity:0}` hid every value; the value spans never receive `.rv-in`, so they stayed
opacity:0 forever. The ONLY reveal target is `.rs-sec.rv` (the single `_revealOnScroll('#rOut .rs-sec.rv')`
caller), so the fix scopes the primitive to `.rs-sec.rv` — the values are never hidden; the section reveal
is unchanged.

🟢 FRONTEND-ONLY / VALUE-NEUTRAL (CSS scope only; amount/low/high/method/rule untouched — the fix only makes
already-present values VISIBLE). Reads the REAL index.html (E14).
Run: PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b126.py
"""
import io, re, sys

HTML = io.open('index.html', encoding='utf-8').read()
ENG  = io.open('evaluate_unified.py', encoding='utf-8').read()

results = []
def check(name, cond):
    results.append((name, bool(cond)))

# ── the collision is FIXED: the reveal primitive is scoped to .rs-sec.rv, NOT a bare .rv ──
check('reveal primitive scoped to .rs-sec.rv (base + rv-in)',
      '.rs-sec.rv{opacity:0;transform:translateY(18px)}' in HTML
      and '.rs-sec.rv.rv-in{opacity:1;transform:none;transition:opacity' in HTML)
# the ONLY `.rv{opacity:0` occurrence must be part of `.rs-sec.rv{opacity:0` (preceded by `sec`);
# a bare standalone `.rv{opacity:0` (the collision) must be gone → negative lookbehind for `sec`.
check('the bare `.rv{opacity:0}` reveal rule is GONE (no longer hides info-row values)',
      re.search(r'(?<!sec)\.rv\{opacity:0', HTML) is None
      and '.rs-sec.rv{opacity:0' in HTML)
check('the bare `.rv.rv-in{opacity:1` reveal rule is GONE (superseded by .rs-sec.rv.rv-in)',
      re.search(r'(?<!sec)\.rv\.rv-in\{opacity:1', HTML) is None)

# ── the INFO-ROW VALUE class is intact (the values ri() renders) ──
check('ri() still renders the value into <div class="rv…"> (the value class)',
      'function ri(l,v,hl,fl){return' in HTML and '<div class="rv\'+(hl?\' hl\':\'\')+\'">\'+v+\'</div>' in HTML)
check('.ri .rv value styling intact (font-weight + color:var(--text))',
      '.ri .rv{font-weight:800;font-size:1.1rem;color:var(--text)}' in HTML)
check('.calc-block .rv value styling intact', '.calc-block .rv{font-family:ui-monospace' in HTML)

# ── the reveal still works on the S4b sections (the single caller unchanged) ──
check('_revealOnScroll still targets #rOut .rs-sec.rv (the section reveal)',
      "_revealOnScroll('#rOut .rs-sec.rv')" in HTML)
check('S4b sections still carry the reveal class (class="rs-sec rv")',
      HTML.count('class="rs-sec rv"') >= 5)
check('_revealOnScroll adds .rv-in (the section reveal mechanism unchanged)',
      "classList.add('rv-in')" in HTML)

# ── print parity rule scoped to .rs-sec.rv too (consistency) ──
check('print rule scoped to .rs-sec.rv (force reveal visible for print)',
      'body.printing .rs-sec.rv { opacity: 1 !important; transform: none !important; }' in HTML)

# ── _revealOnScroll is now DEFENSIVE: content is never permanently hidden if the observer never fires ──
check('_revealOnScroll reveals in-view elements immediately (no wait on the async observer)',
      'el.getBoundingClientRect().top)<vh*0.95' in HTML and 'const pending=els.filter(' in HTML)
check('_revealOnScroll SAFETY NET reveals any still-hidden element after a grace period',
      "if(!el.classList.contains('rv-in')) show(el); }); }, 1600);" in HTML)
check('_revealOnScroll keeps the IntersectionObserver for the scroll-reveal UX',
      'new IntersectionObserver(' in HTML and 'pending.forEach(el=>io.observe(el));' in HTML)

# ── value-neutral: the hotfix is CSS scope only; no engine/logic touched ──
check('no result-screen JS mutates v.amount/low/high (value-neutral)',
      not re.search(r'\bv\.(amount|low|high)\s*=[^=]', HTML))
check('ENGINE_VERSION bumped to b126 (format)',
      re.search(r"ENGINE_VERSION = 'thammen-sprint2p22p0b126", ENG) is not None)
check('SPRINT_TAG is 2.22.0b.126', "SPRINT_TAG = '2.22.0b.126'" in ENG)

passed = sum(1 for _, ok in results if ok)
for name, ok in results:
    print(('PASS' if ok else 'FAIL') + ' - ' + name)
print('\n%d/%d checks passed' % (passed, len(results)))
sys.exit(0 if passed == len(results) else 1)
