# -*- coding: utf-8 -*-
# Sprint 2.22.0b.15 — Screen-4 polished result (progressive disclosure / DESIGN v4).
# FRONTEND-ONLY, value-invariant (engine = the 2 version-string lines only). Reads the REAL
# index.html (E14 / Rule #40 for the frontend lane) + asserts the engine version bump.
#
# Verifies the brief's testable DoD: (a) TIER mapping (figure=TIER-1, detail=TIER-2
# accordions, CTAs=TIER-3, compliance=always-visible foot); (b) NO PANEL LOST (every
# detail panel still built, routed into the accordion/flat stream); (c) DISCLOSURE STAYS
# TIER-1 / always-visible (MUC chip + full clause + «ليس تقييماً معتمداً» + freshness +
# disclaimer never collapsed); (d) value-invariance (show() does not touch v.amount/range).
import re
import pathlib

ROOT = pathlib.Path(__file__).parent
HTML = (ROOT / 'index.html').read_text(encoding='utf-8')
ENG = (ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')

results = []
def check(name, cond):
    results.append((name, bool(cond)))

# ── Helpers / infrastructure ──
# 1. _acc accordion wrapper present + returns '' on empty (no empty accordion ships).
check('_acc accordion wrapper defined', 'function _acc(title,inner,open){' in HTML and "if(!inner)return '';" in HTML)
check('_acc uses native <details class="t2acc">', "'<details class=\"t2acc\"'" in HTML)
# 2. _evOneRow TIER-1 evidence summary, reusing the b2.2 ratings (derive-don't-author).
check('_evOneRow defined + reuses _evidenceRatings', 'function _evOneRow(d){' in HTML and 'var rows=_evidenceRatings(d);' in HTML)
# 3. MUC level → Arabic chip map (low/medium/moderate/high/critical).
check('MUC_LEVEL_AR map present', "const MUC_LEVEL_AR={'low':'منخفض','medium':'متوسط','moderate':'متوسط','high':'مرتفع','critical':'حرج'};" in HTML)
# 4. tier buffers declared exactly once each.
for b in ['let head=', 'let alerts=', 'let muc=', 'let a8acc=', 'let t1=', 'let t2=', 'let t3=', 'let flat=', 'let foot=']:
    check('buffer declared once: %s' % b, HTML.count(b) == 1)

# ── TIER ordering (the assembly contract) ──
# 5. valued assembly.
# b125 R6 (S4b): the valued lower half was rebuilt from accordions into flat scroll-revealed sections
# (secEv/secHow/secScn/secLim/secFull); the assembly is now head+alerts+t1+…sections…+foot+t3 (t3 = the
# sticky action bar). The full MVU clause folds inside the LIMITS section (_s4bLimits(d,muc)).
check('valued assembly head+alerts+t1+flat-sections+foot+t3 (b125 S4b)',
      'h=head+alerts+t1+secEv+secHow+secScn+secLim+secFull+foot+t3;' in HTML)
# 6. refusal assembly preserves pre-b15 flat order (compliance still shown).
check('refusal assembly head+muc+a8acc+alerts+flat+foot', 'h=head+muc+a8acc+alerts+flat+foot;' in HTML)

# ── DISCLOSURE STAYS TIER-1 / always-visible (the §4 HALT compliance set) ──
# 7. MUC level CHIP rendered in TIER-1 (first-glance compliance signpost).
# b48 re-point (R6/Lesson-2): the chip recolored red→amber (--bad→--warn) + the ⚠️ emoji became
# an inline-SVG icon. Pin the BEHAVIOUR — the chip is built into t1 (TIER-1), uses the amber token,
# and renders «عدم اليقين الجوهري: '+MUC_LEVEL_AR[mu.level]» — not the volatile emoji/exact margin.
check('MUC chip in TIER-1 (t1+=… عدم اليقين الجوهري: +MUC_LEVEL_AR)',
      "t1+='<div style=\"display:inline-block;padding:3px 10px;background:var(--warn-bg);color:var(--warn);" in HTML
      and " '+t('عدم اليقين الجوهري: ','Material uncertainty: ')+(LANG==='en'?MUC_LEVEL_EN:MUC_LEVEL_AR)[mu.level]+'</div>';" in HTML)
# 8. the FULL MVU clause is still BUILT via the shared _mucCardHtml builder (same clause, same red styling).
# b52 re-point (R6/Lesson-2): the lean pass folds the clause behind its chip (_mucFold) instead of
# always-visible — the chip + «ليس معتمداً» stay always-visible in TIER-1 (checks 7 + 9), the full clause one click away.
check('full MVU clause still built via _mucCardHtml (same red styling)',
      'muc+=_mucCardHtml(muc_ar,muc_basis,muc_review);' in HTML
      and 'background:var(--bad-bg);border:2px solid var(--bad)' in HTML)
# b125 R6 (S4b): the full MVU clause now folds inside the LIMITS section (secLim = _s4bLimits(d,muc)),
# not a standalone _mucFold. The chip + «ليس معتمداً» stay always-visible in TIER-1 (checks 7 + 9).
check('full MVU clause folds inside the LIMITS section (_s4bLimits(d,muc))',
      'secLim=_s4bLimits(d,muc);' in HTML and 'function _s4bLimits(d,muc){' in HTML)
# 9. «ليس تقييماً معتمداً» line is in TIER-1 (always visible), a20 status appended when present.
check('not-certified line in TIER-1', "t1+='<div class=\"rn\" style=\"margin-top:10px;font-size:.82rem;color:#8a6d3b;background:#fcf8e3" in HTML and 'ليس تقييماً معتمداً' in HTML)
check('a20 rics_compliant_status appended to not-certified line', 'rics_compliant_status_ar' in HTML and '_statusAr' in HTML)
# 10. evidence ONE-ROW summary sits in TIER-1 (drama on evidence, not the figure).
check('evidence one-row in TIER-1 (t1+=_evOneRow(d))', 't1+=_evOneRow(d);' in HTML)
# 11. data-freshness caveat + disclaimer + verification route to the always-visible foot (NOT collapsed).
check('data-freshness caveat → foot', "foot+='<div class=\"dfc s-'+sev+'\">'+pick(d.data_freshness,'caveat')+'</div>';" in HTML)  # b140 R6: caveat via pick (EN twin, AR fallback)
check('disclaimer card → foot', "foot+='<div class=\"rc\" style=\"border-color:var(--warn-bg)\"><div class=\"rn\" style=\"font-size:.8rem\">'+d.disclaimer+'</div></div>';" in HTML)
check('verification footer → foot', "foot+='<div class=\"verification-footer\">';" in HTML)
# 12. alert panels (A11 / reality / multi-QARS / scope / sanity) route ABOVE the number (alerts buffer).
# b48 re-point (R6/Lesson-2): the ⚠️ emoji became an inline-SVG icon — keep the Arabic + the alerts wrapper.
check('A11 mismatch → alerts (above number)', "alerts+='<div style=\"background:var(--warn-bg);border:2px solid var(--warn);border-radius:8px;padding:16px;margin-bottom:14px\">';\n    alerts+='<div style=\"font-weight:700;color:var(--warn);margin-bottom:8px;font-size:1.02rem\">" in HTML and 'تناقض في تصنيف العقار' in HTML)
check('sanity warnings → alerts (above number)', "alerts+='<div class=\"sanity-warn\">" in HTML)
check('service-scope badge → alerts', "alerts+='<div style=\"background:'+scopeBg+';border-right:4px solid '+scopeColor+';" in HTML)

# ── NO PANEL LOST (detail blocks accumulate, then wrap) ──
# 13. the scratch `h` is collapsed into ONE TIER-2 «التفاصيل الكاملة» accordion (valued) / flat (refusal).
# b48 re-point: the 🔎 emoji in the accordion title became an inline-SVG icon — pin the title text + wiring.
# b125 R6 (S4b): the analytical scratch `h` + a8acc now live inside the FULL-DETAILS fold
# (secFull, <details class="rs-full">), not a t2 accordion. Nothing lost.
# b141 R6: the fold LABEL was renamed «التفاصيل الكاملة (التحليل والمقارنات)» → «تحليل إضافيّ (التفاصيل والمقارنات)»
# to resolve the naming collision with «التقرير الكامل» (the deepest artifact). Scratch+a8acc wiring unchanged.
check('detail scratch → FULL-DETAILS fold (valued, secFull)',
      "تحليل إضافيّ (التفاصيل والمقارنات)" in HTML and '+a8acc+h' in HTML and 'details class="rs-full"' in HTML)
check('detail scratch → flat (refusal)', 'else { flat+=h; }' in HTML)
check('scratch consumed before assembly', "h='';  // scratch consumed" in HTML)
# 14. basic-info → its own TIER-2 accordion. (b31/DEF-UX11 re-point: the full evidence panel is no
#     longer a standalone «جودة الأدلّة (تفصيل)» accordion — it now folds INTO the «كيف وصلنا لهذا الرقم؟»
#     accordion alongside the 9-note parade; assertion below + test_sprint_2_22_0b31.py own the new shape.)
# b48 re-point: the 🏠 emoji became an inline-SVG icon — pin the title text + wiring.
# b125 R6 (S4b): basic-info (`_info`) now lives inside the FULL-DETAILS fold (secFull), not a t2 accordion.
check('basic-info (_info) → FULL-DETAILS fold (secFull)',
      "t('بيانات العقار الأساسية','Property basics')" in HTML and 'secFull=' in HTML and '+_info' in HTML)
# b125 R6 (S4b): the full evidence panel now folds inside the _s4bHow «تفاصيل منهجيّة» fold (how + panel).
check('full evidence panel → _s4bHow methodology fold (b31/b125)',
      'const mbody=how+evidencePanelHtml(d,acc);' in HTML)
# 15. brief sections: valued → accordion; refusal → flat (verbatim title card).
# b48 re-point: the 📄 emoji became an inline-SVG icon — pin the title expression + wiring.
# b125 R6 (S4b): the brief sections (valued) now render inside the FULL-DETAILS fold (secFull) via
# _briefSecs/_briefTitle, not a t2 accordion. The refusal path keeps them flat (check below).
check('brief sections → FULL-DETAILS fold (valued, _briefSecs)',
      "pick(br,'title')||t('تفاصيل التقرير','Report details')" in HTML and '_briefSecs=_secs;' in HTML and '+_briefSecs' in HTML)
check('brief sections → flat (refusal verbatim)', "flat+='<div class=\"rc\" style=\"background:transparent;border:none;padding:0;box-shadow:none;margin-bottom:6px\"><div class=\"rt\" style=\"font-size:1.15rem;margin-bottom:0\">'+(pick(br,'title')||t('التقرير','Report'))+'</div></div>';" in HTML)

# ── TIER-3 actions ──
# 16. TIER-3 refine + report CTAs (valued path).
# b48 re-point: the ✏️ emoji became an inline-SVG icon — pin the t3-primary class + go('refine') + the CTA text.
# b125 R6 (S4b): TIER-3 CTAs moved into the STICKY action bar (.rs-bar). refine → go('refine'), gated off
# for raw_land (b97). «حسّن التقييم» (b54 identity lock).
check('TIER-3 refine CTA → sticky bar go(refine)',
      't3+=\'<div class="rs-bar">' in HTML and "onclick=\"go(\\'refine\\')\"" in HTML and 'حسّن التقييم' in HTML)
# b17 landed: the report CTA opened screen 5 (openReport); Sprint 2.22.0b.25 (م2/D6)
# then made the SHORT report the first stop (full report one click away inside it) —
# the b15 invariant is that the TIER-3 secondary CTA leads to a REPORT surface.
# b48 re-point: the 📄 emoji became an inline-SVG icon — pin the t3-secondary class + openShortReport() + the CTA text.
# b125 R6 (S4b): the report CTAs live in the sticky bar — short report (openShortReport) + full report
# (openReport, now one direct click; additive, nothing removed).
check('TIER-3 report CTAs → sticky bar (short + full)',
      'onclick="openShortReport()"' in HTML and 'التقرير المختصر' in HTML
      and 'onclick="openReport()"' in HTML and 'التقرير الكامل' in HTML)

# ── Print parity (F1) ──
# 17. printReport force-opens the accordions before print + restores after.
# b125 R6 (S4b): printReport force-opens EVERY #rOut <details> (the flat folds are .rs-mfold/.rs-full/
# .rs-lim now, not .t2acc) + a @media print rule forces the unrevealed .rv sections visible (F1 parity).
check('printReport force-opens all result folds', "document.querySelectorAll('#rOut details')" in HTML and '_accs.forEach(a=>{a.open=true;});' in HTML)
check('printReport restores prior open-state', '_accs.forEach((a,i)=>{a.open=_wasOpen[i];});' in HTML)

# ── CSS for the new tier classes ──
check('.t2acc CSS present', '.t2acc{' in HTML and '.t2acc>summary{' in HTML)
check('.ev1row CSS present', '.ev1row{' in HTML)
check('.t3block CSS present', '.t3block{' in HTML and '.t3block .t3-primary{' in HTML)

# ── VALUE-INVARIANCE (show() does not touch the figure; range-as-lead b3 retained) ──
check('range headline label retained (range-as-lead)', 'النطاق التقديري السوقي' in HTML)
# b48 re-point (R6/Lesson-2): the RESULT-screen hero superseded the old muted marker line
# («الوسيط (التقدير المركزي) ≈ <strong>» is gone from the result). b3 «range-as-lead» is KEPT-but-evolved:
# the lead figure (rhero) + a slim range bar whose .dot.c marks where the central estimate (v.amount)
# sits within [low,high] — so the median POSITION is still surfaced, just visually not as a text line.
# The SHORT/FULL report KEEPS its «الوسيط (التقدير المركزي)» marker (report-only, _midR). Pin both.
check('central-estimate position surfaced in result hero + report median marker retained',
      'class="rhero"' in HTML
      and 'class="rng"' in HTML
      and '<span class="dot c"' in HTML
      and 'الوسيط (التقدير المركزي)' in HTML)
# b31/DEF-UX11 re-point: condition note STAYS on TIER-1 (decision-relevant); value_floor + hbu
# FOLD into the «كيف وصلنا» accordion (the `how` buffer). Strings still present — buffer changed.
check('condition note STAYS on TIER-1 (b31)', "if(v.condition_note_ar){t1+=" in HTML)
check('value_floor + hbu FOLD into «كيف وصلنا» (how buffer, b31)',
      'if(v.value_floor){' in HTML and 'how+=' in HTML and 'if(v.hbu_note_ar){how+=' in HTML)
check('moj sample-size (cite-n) rendered (b52: folded into «كيف وصلنا»)', 'صفقات البيع المسجلة لعقارات مشابهة' in HTML)
# show() does NOT mutate v.amount/v.low/v.high (no assignment to those fields anywhere).
check('no mutation of v.amount/v.low/v.high in show()', not re.search(r'\bv\.(amount|low|high)\s*=[^=]', HTML))

# ── Engine version (format only — R6 / Lesson-2: no exact pin) ──
check('ENGINE_VERSION format (thammen-sprint…)', re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+", ENG) is not None)
check('SPRINT_TAG dotted-numeric format', re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+", ENG) is not None)
# R6 / Lesson-2: NO exact version pin (it broke on the b16 bump) — assert only that the engine
# has moved AT/BEYOND b15 (the pre-b15 tag never returns; format already checked above).
check('engine at/beyond b15 (b14 tag gone)', "thammen-sprint2p22p0b14-" not in ENG)  # b140 R6: trailing '-' guards vs the b140 substring (2p22p0b14 ⊂ 2p22p0b140)

passed = sum(1 for _, ok in results if ok)
for name, ok in results:
    print(('PASS' if ok else 'FAIL'), '-', name)
print('\n%d/%d passed' % (passed, len(results)))
assert passed == len(results), '%d FAILED' % (len(results) - passed)
