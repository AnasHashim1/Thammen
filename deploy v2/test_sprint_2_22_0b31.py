# -*- coding: utf-8 -*-
# Sprint 2.22.0b.31 — DEF-UX11: TIER-1 9-note fold (the simple-owner overload kill, 21→5).
# FRONTEND-ONLY, value-invariant (engine = the 2 version-string lines only). Reads the REAL
# index.html (E14 / Rule #40 for the frontend lane) + asserts the engine version bump.
#
# What this verifies: the «9-note parade» (value-floor · HBU · old-stock · cost-triangulation ·
# leadership · age-honesty · resurvey · cost-value-line · market-dispersion) + the full evidence
# panel FOLD into ONE collapsed «🔍 كيف وصلنا لهذا الرقم؟» accordion (the `how` buffer); TIER-1 keeps
# the 5-element core (range + median + «ليس معتمداً» + evidence pill + the accordion «button»). The
# fold is a buffer swap only (t1→how) — every note's condition + HTML string is verbatim → the
# value (v.amount/low/high) is byte-identical (b24 «الرقم واحد للجميع»).
import re
import pathlib

ROOT = pathlib.Path(__file__).parent
HTML = (ROOT / 'index.html').read_text(encoding='utf-8')
ENG = (ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')

results = []
def check(name, cond):
    results.append((name, bool(cond)))

# ── 1. the `how` buffer + the ONE «كيف وصلنا» accordion ──
check('show() declares the `how` fold buffer', "let how='';" in HTML)
check('ONE «كيف وصلنا لهذا الرقم؟» accordion = how + full evidence panel',
      # b34 (DEF-UX12) added a 3rd `open` arg (role-driven density) — match without the trailing `);`.
      # b48 (de-emoji): the 🔍 emoji became an inline-SVG icon; the Arabic text is unchanged → re-anchor
      # on the stable text fragment that ends the summary string.
      "كيف وصلنا لهذا الرقم؟', how+evidencePanelHtml(d,acc)" in HTML)
# the «كيف وصلنا» accordion is built FIRST (right after the figure+MVU), before basic-info.
# b48 (de-emoji): the 🔍/🏠 emojis became inline-SVG icons; re-anchor the ORDER check on the stable
# Arabic-text + `,_info)` fragments that still uniquely identify each `t2+=_acc(...)` call.
check('«كيف وصلنا» accordion is the FIRST t2 accordion (before basic-info)',
      HTML.index("كيف وصلنا لهذا الرقم؟', how+evidencePanelHtml(d,acc)") < HTML.index("بيانات العقار الأساسية',_info);"))
# the standalone «جودة الأدلّة (تفصيل)» accordion is GONE (folded into «كيف وصلنا»).
check('standalone «جودة الأدلّة (تفصيل)» accordion REMOVED (folded)',
      "_acc('📊 جودة الأدلّة (تفصيل)',evidencePanelHtml(d,acc))" not in HTML)

# ── 2. the 9 notes now build into `how` (NOT t1) ──
check('note 1/9 value-floor → how', 'if(vf.land_floor_note_ar)how+=' in HTML and 'if(v.value_floor){' in HTML)
check('note 2/9 HBU → how', 'if(v.hbu_note_ar){how+=' in HTML)
check('note 3/9 old-stock re-anchor → how', 'v.old_stock_reanchor.note_ar){how+=' in HTML)
check('note 4/9 cost-triangulation → how', 'v.cost_triangulation.note_ar){how+=' in HTML)
check('note 5/9 leadership → how', 'v.leadership.note_ar){how+=' in HTML)
check('note 6/9 age-honesty → how', 'v.leadership.age_honesty_note_ar){how+=' in HTML)
check('note 7/9 resurvey → how', 'v.leadership.resurvey_note_ar){how+=' in HTML)
# R6/Lesson-2 re-point (b37/DEF-UX9): the cost-value line moved into a {const _vc=…; how+='…label_ar…'}
# block (the cost-mechanics BUA/RCN/retention sibling was added beside it). The cost-value note still lives
# in `how` (the «كيف وصلنا» accordion), not t1 — proven by the cost label_ar line appending to `how`.
# b48 (de-emoji): the 🏗️ emoji became an inline-SVG icon (ic-tool); the behaviour (label_ar → how) is the
# stable pin — re-anchored on the icon-close + `'+_vc.label_ar` fragment.
check('note 8/9 cost-value-line → how', '</use></svg> \'+_vc.label_ar' in HTML and 'const _vc=v.value_stack.cost;' in HTML)
check('note 9/9 market-dispersion → how', 'v.value_stack.market.dispersion_36!=null){how+=' in HTML)

# ── 3. the 9 notes are GONE from t1 (no double-render) ──
check('HBU no longer on t1', 'if(v.hbu_note_ar){t1+=' not in HTML)
check('old-stock no longer on t1', 'v.old_stock_reanchor.note_ar){t1+=' not in HTML)
check('leadership no longer on t1', 'v.leadership.note_ar){t1+=' not in HTML)
check('market-dispersion no longer on t1', 'v.value_stack.market.dispersion_36!=null){t1+=' not in HTML)
check('cost-value-line no longer on t1', 'v.value_stack.cost.value){t1+=' not in HTML)

# ── 4. the 5-element CORE stays on TIER-1 (the figure) ──
check('core 1 — range headline retained (t1, range-as-lead b3)', 'النطاق التقديري السوقي' in HTML)
# b47/b48 (result-screen HERO): the muted «الوسيط (التقدير المركزي) ≈ <strong>» marker line was
# SUPERSEDED by the navy hero band — the central estimate (median = v.amount) now LEADS as the confident
# figure (`<div class="rhero"><span class="lbl">التقدير السوقي</span><div class="num">…fmt(v.amount)…`),
# with the range in `.rng` below it. The b3 range-as-lead is KEPT-but-evolved (lead-figure + slim range
# bar). Re-point to the NEW TRUTH: the central-figure hero is present on TIER-1.
check('core 2 — central-estimate hero (median=v.amount) leads on TIER-1',
      'class="rhero"' in HTML and 'التقدير السوقي' in HTML and "'<div class=\"num\">'+fmt(v.amount)" in HTML)
check('core 3 — «ليس تقييماً معتمداً» stays t1 (compliance)',
      'ليس تقييماً معتمداً' in HTML and "color:#8a6d3b;background:#fcf8e3" in HTML)
check('core 4 — evidence ONE-ROW pill stays t1', 't1+=_evOneRow(d);' in HTML)
# b48 (de-emoji): the 🔍 emoji became an inline-SVG icon; the accordion «button» summary text is unchanged.
check('core 5 — the accordion «button» summary present', 'كيف وصلنا لهذا الرقم؟' in HTML)

# ── 5. boundary: NOT in the named-9 → STAY on t1 (decision-relevant / conditional) ──
check('condition note STAYS t1', 'if(v.condition_note_ar){t1+=' in HTML)
check('teardown note STAYS t1', 'v.teardown.note_ar){t1+=' in HTML)
check('luxury-new premium STAYS t1', 'v.luxury_new_premium.note_ar){t1+=' in HTML)
# Re-pointed for b52 (R6/Lesson-2): the result-screen lean pass moved age-sensitivity + moj sample-size
# OFF always-visible TIER-1 into the «كيف وصلنا» fold (still rendered + disclosed, one click away).
check('age-sensitivity → «كيف وصلنا» fold (b52 lean; was TIER-1)', 'v.age_sensitivity.note_ar){how+=' in HTML)
check('moj sample-size (cite-n) rendered (b52: in «كيف وصلنا» fold)', 'صفقات البيع المسجلة لعقارات مشابهة' in HTML)

# ── 6. evidence panel renderer is reused, NOT deleted (folded on result + still in showReport) ──
check('evidencePanelHtml still defined', 'function evidencePanelHtml(d,acc){' in HTML)
# Re-pointed for DEF-UX13/b32 (R6/Lesson-2): the standalone `h+=evidencePanelHtml(d,acc);`
# render is GONE everywhere — folded into the «كيف وصلنا» result accordion (b31) and dropped
# from the confirm gate (b32). The panel survives, just never as a bare standalone h+= call.
check('standalone h+=evidencePanelHtml render gone (folded b31 / confirm-removed b32)', 'h+=evidencePanelHtml(d,acc);' not in HTML)
check('evidencePanelHtml still in showReport', '_axWrap(evidencePanelHtml(d,acc))' in HTML)

# ── 7. VALUE-INVARIANCE — show() does NOT mutate v.amount/v.low/v.high (b24) ──
check('no mutation of v.amount/v.low/v.high', not re.search(r'\bv\.(amount|low|high)\s*=[^=]', HTML))
# Re-pointed for b52 (R6/Lesson-2): the result-screen lean folds the full MUC clause into a collapsed
# accordion (_mucFold) placed before t2 — the chip + «ليس معتمداً» stay always-visible in t1.
check('valued assembly (b52: MUC folds into _mucFold before t2)', 'h=head+alerts+t1+_mucFold+t2+t3+foot;' in HTML)

# ── 8. engine version (format only — R6 / Lesson-2: no exact pin) ──
check('ENGINE_VERSION format (thammen-sprint…)', re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+", ENG) is not None)
check('SPRINT_TAG dotted-numeric format', re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+", ENG) is not None)
check('engine at/beyond b30 (b29 tag gone)', 'thammen-sprint2p22p0b29' not in ENG)

passed = sum(1 for _, ok in results if ok)
for name, ok in results:
    print(('PASS' if ok else 'FAIL'), '-', name)
print('\n%d/%d passed' % (passed, len(results)))
assert passed == len(results), '%d FAILED' % (len(results) - passed)
