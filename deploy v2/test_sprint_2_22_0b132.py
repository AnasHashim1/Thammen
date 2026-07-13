# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.132 — «الإدخال» (S6 split, part 1 of 2; refine = b133) redesign v2: the ENTRY /
identification screen (#formScreen) recreated in the v2 idiom — 🟢 FRONTEND / VALUE-NEUTRAL
(api.py + valuation engine untouched; only the 2 version lines bumped).

What changed: the identification card gets the v2 look (elevated .ent-card, centered logo + heading,
an asset-type selector, v2 fields, a trust row). The two type cards ARE the input-mode selector and
KEEP the tabAddr/tabLand ids so selTab's .sel toggle + grpAddr/grpLand reveal are byte-identical.

R-B / R-E landmine (the handoff's own trap): the mock splits type into villa / land / **عمارة قريباً
(disabled)**. Building IS supported via address (towerRentSection) and the engine classifies asset
type from the QARS-in-polygon reality-check — so a disabled «عمارة» would both MISLEAD and REGRESS a
live path. We drop it (intentional deviation, logged R-E) and fold building into the «فيلا أو مبنى»
(by-address) card. This test FAILS if that regression sneaks back, or if any pinned id/handler/copy
was weakened.

E14: reads the REAL index.html + evaluate_unified.py."""
import io, re
HTML = io.open('index.html', encoding='utf-8').read()
ENG  = io.open('evaluate_unified.py', encoding='utf-8').read()
passed = failed = 0
def check(name, cond, msg=''):
    global passed, failed
    if cond: passed += 1; print('  ok  ', name)
    else:    failed += 1; print('  FAIL', name, ('[' + msg + ']') if msg else '')

# ── isolate the ENTRY screen (#formScreen → #refineScreen) ──
_fs = HTML.find('id="formScreen"')
_fe = HTML.find('id="refineScreen"')
FORM = HTML[_fs:_fe] if (_fs >= 0 and _fe > _fs) else ''
check('#formScreen region isolated', bool(FORM))
# the grpAddr sub-region (for ordering assertions, mirrors the b33 suite)
_ga = FORM.find('id="grpAddr"'); _gl = FORM.find('id="grpLand"')
GRPADDR = FORM[_ga:_gl] if (_ga >= 0 and _gl > _ga) else ''

# ═══ (1) the v2 ENTRY card + centered header ═══
check('elevated .ent-card present', 'class="ent-card"' in FORM)
check('centered heading «ما العقار الذي نُقدّره؟»', 'ما العقار الذي نُقدّره؟' in FORM)
check('heading bilingual', 'data-en="Which property are we valuing?"' in FORM)
check('transparent logo (logo_t.png) in the header', 'src="logo_t.png"' in FORM and 'class="ent-logo"' in FORM)
check('subtitle present', 'أدخِل العنوان أو رقم القطعة — الباقي علينا.' in FORM)

# ═══ (2) the asset-type selector = the input-mode selector (v2 restyle of the tabs) ═══
# the two type cards only (the [ "] class-boundary excludes the .ent-types container)
_types = FORM[FORM.find('class="ent-types"'):FORM.find('id="grpAddr"')]
check('two v2 type cards (.ent-type)', len(re.findall(r'class="ent-type[ "]', _types)) == 2)
check('type label «نوع العقار»', 'نوع العقار' in FORM and 'data-en="Property type"' in FORM)
check('villa/building card → address mode', 'فيلا أو مبنى' in FORM and 'بالعنوان' in FORM)
check('land card → PIN mode', 'أرض / قطعة' in FORM and 'بالرقم المساحي (PIN)' in FORM)
check('type cards use sprite icons (home/ruler)', '#ic-home' in FORM and '#ic-ruler' in FORM)

# ═══ (3) R-E honesty guard — the misleading disabled «عمارة قريباً» is NOT reintroduced ═══
# (check the rendered type-card region, not the whole FORM — the design-rationale comment
#  legitimately names «عمارة قريباً» when explaining why the chip was dropped.)
check('R-E: no disabled «عمارة قريباً» coming-soon type chip', 'قريباً' not in _types)
check('R-E: building stays reachable (folded into the by-address card, not dropped)',
      'فيلا أو مبنى' in FORM)
# the type cards drive ONLY selTab (input mode) — they do NOT introduce a user-picked asset-type
# that would override the engine's QARS-in-polygon reality-check.
check('R-E: type cards call selTab only (no engine-overriding type setter)',
      _types.count('onclick="selTab(') == 2 and 'selAud(' not in _types and 'assetType' not in _types)

# ═══ (4) trust row (from the handoff — honest, real) ═══
check('trust row present (.ent-trust)', 'class="ent-trust"' in FORM)
check('trust copy «مجاني · بلا حساب · بلا تتبّع»',
      'مجاني' in FORM and 'بلا حساب' in FORM and 'بلا تتبّع' in FORM)
check('trust row bilingual', 'data-en="Free"' in FORM and 'data-en="No account"' in FORM and 'data-en="No tracking"' in FORM)

# ═══ (5) PINNED HOOKS PRESERVED — selTab wiring byte-identical (b89) ═══
check('selTab(address) + selTab(land) UNTOUCHED', "selTab('address')" in FORM and "selTab('land')" in FORM)
check('tabAddr/tabLand ids kept (selTab toggles .sel on them)', 'id="tabAddr"' in FORM and 'id="tabLand"' in FORM)
check('the address card is pre-selected (.ent-type sel on tabAddr)',
      re.search(r'class="ent-type sel"\s+id="tabAddr"', FORM) is not None)
check('grpAddr / grpLand reveal targets kept', 'id="grpAddr"' in FORM and 'id="grpLand"' in FORM)
check('grpLand still hidden by default', re.search(r'id="grpLand"[^>]*style="[^"]*display:none', FORM) is not None)

# ═══ (6) PINNED HOOKS PRESERVED — fields / handlers / identity store (b33) ═══
for fid in ['zone', 'street', 'building', 'pin']:
    check('field id kept: ' + fid, ('id="%s"' % fid) in FORM)
check('clrIdent + clearIdentity() kept', 'id="clrIdent"' in FORM and 'clearIdentity()' in FORM)
check('sBtn + run() kept', 'id="sBtn"' in FORM and 'onclick="run()"' in FORM)
check('fRes results container kept', 'id="fRes"' in FORM)
check('audLegacy hidden input kept (value=owner, b89 value-invariant)',
      re.search(r'id="audLegacy"\s+value="owner"', FORM) is not None)
check('b89: dead selAud role buttons stay gone', "onclick=\"selAud(this,'owner')\"" not in HTML)

# ═══ (7) PINNED COPY VERBATIM — the b33 كهرماء help line + PIN hint ═══
check('كهرماء help line VERBATIM, class="br-note", inside grpAddr',
      re.search(r'class="br-note"[^>]*>هذه الأرقام على لوحة عنوان', GRPADDR) is not None)
check('help line comes AFTER the building field (b33 ordering)',
      GRPADDR.find('id="building"') >= 0 and GRPADDR.find('id="building"') < GRPADDR.find('لوحة عنوان المبنى'))
check('PIN source hint kept (untouched)', 'أدخل رقم القطعة من شهادة الملكية أو خرائط GIS' in FORM)

# ═══ (8) v2 field styling scoped — shared .fcard/.aud-btn/.sbtn NOT globally restyled (refine=b133) ═══
check('.ent-* CSS block added (b120 tokens)', '.ent-card{' in HTML and '.ent-type{' in HTML)
check('.ent-in field style scoped (v2 inputs)', '.ent-in{' in HTML)
check('shared .sbtn button reused (not forked)', 'class="sbtn" id="sBtn"' in FORM)

# ═══ (9) VALUE-NEUTRALITY — engine/api untouched, only the version marker moved ═══
check('ENTRY is input-only (never computes a value)', 'v.amount=' not in FORM and 'v.low=' not in FORM)
# b133: version-pin relaxed to the b129/b130 prefix convention (superseded when b133 bumped SPRINT_TAG;
# the b132 markup guards above are what this test protects — the version string is just the deploy tag).
check('ENGINE_VERSION present (thammen-sprint…)', 'thammen-sprint2p22p0b' in ENG)
check('SPRINT_TAG present (2.22.0b.…)', "SPRINT_TAG = '2.22.0b." in ENG)

print('\n%d passed, %d failed' % (passed, failed))
import sys; sys.exit(1 if failed else 0)
