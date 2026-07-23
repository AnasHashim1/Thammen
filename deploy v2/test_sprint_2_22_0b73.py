# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.73 — a11y contrast (sub-AA brown helper/title text -> AA tokens)
+ short-report age-clarity (registered age = a documented FLOOR).
E14: reads the REAL index.html + evaluate_unified.py. Frontend-only / value-invariant."""
import io, re

HTML = io.open('index.html', encoding='utf-8').read()
ENG  = io.open('evaluate_unified.py', encoding='utf-8').read()

passed = failed = 0
def check(name, cond):
    global passed, failed
    if cond:
        passed += 1; print('  ok  ', name)
    else:
        failed += 1; print('  FAIL', name)

# ---- (1) the five sub-AA sites moved to AA tokens ----
check('fpHint helper -> var(--muted)',
      'id="fpHint" class="rn" style="font-size:.75rem;color:var(--muted)' in HTML)
check('rental-note helper -> var(--muted)',
      'color:var(--muted);margin-top:3px"' in HTML and '>إيجار فعلي' in HTML)  # b137 R6: rental note got data-en; muted color preserved
check('footprint title -> var(--primary)',
      'color:var(--primary)"><svg class=ic aria-hidden=true><use href=#ic-ruler></use></svg>' in HTML)
check('cap-note helper -> var(--muted)',
      "color:var(--muted);margin-top:6px\">'+t('حُدِّدت مساحة البناء" in HTML)  # b138: t()-wrapped
check('assumes-typical title -> var(--primary)',
      "color:var(--primary)\">'+t('ℹ التقييم يفترض بناءً نموذجياً" in HTML)  # b138: t()-wrapped

# ---- (2) no sub-AA helper/title hex left; decorative ones preserved ----
check('only the 2 decorative #8b6e44 remain (gradient + large land-value figure)',
      HTML.count('#8b6e44') == 2)
check('decorative bronze gradient PRESERVED (not over-swept)',
      'linear-gradient(135deg,var(--bronze),#8b6e44)' in HTML)
check('no #a87000 left (the only site was the assumes-typical title)',
      HTML.count('#a87000') == 0)

# ---- (3) short-report age-clarity: registered age = a documented floor ----
check('age-floor honesty preserved (قد يكون أقدم) — b90 moved it from the strip to the age-chip tooltip; «فوق N سنة» conveys the floor on the chip',
      'قد يكون أقدم' in HTML)
check('old bare "(سجل رسمي)" attribution replaced',
      '(سجل رسمي)' not in HTML)

# ---- (4) value-invariance guards (frontend-only; engine = version lines only) ----
check('locked hero label preserved (b54 terminology lock)',
      'التقييم السوقي' in HTML)
check('forced-sale honesty preserved',
      'ليست تصفية معتمدة' in HTML)
check('engine version is a valid b-series tag (version-agnostic, R6)',
      "SPRINT_TAG = '2.22.0b." in ENG and
      "thammen-sprint2p22p0b" in ENG)
check('b72 value-clarity copy untouched (e25 on-screen + cost-led de-jargon intact)',
      'كلفةُ إعادة بناء بيتك' in HTML and 'الصفقات المماثلة القريبة كانت قليلة' in HTML)

print('\nb73:', passed, 'passed,', failed, 'failed')
raise SystemExit(1 if failed else 0)
