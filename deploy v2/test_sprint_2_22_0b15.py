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
# 5. valued assembly: alerts (qualifiers) → TIER-1 figure → full MVU clause → TIER-2 → TIER-3 → foot.
check('valued assembly order head+alerts+t1+muc+t2+t3+foot', 'h=head+alerts+t1+muc+t2+t3+foot;' in HTML)
# 6. refusal assembly preserves pre-b15 flat order (compliance still shown).
check('refusal assembly head+muc+a8acc+alerts+flat+foot', 'h=head+muc+a8acc+alerts+flat+foot;' in HTML)

# ── DISCLOSURE STAYS TIER-1 / always-visible (the §4 HALT compliance set) ──
# 7. MUC level CHIP rendered in TIER-1 (first-glance compliance signpost).
check('MUC chip in TIER-1 (t1+=… تحفظ مادي: +MUC_LEVEL_AR)',
      "t1+='<div style=\"display:inline-block;padding:3px 10px;background:var(--bad-bg);color:var(--bad);border-radius:12px;font-size:.74rem;margin-bottom:10px\">⚠️ تحفظ مادي: '+MUC_LEVEL_AR[mu.level]+'</div>';" in HTML)
# 8. the FULL MVU clause routes to the always-visible `muc` buffer (NOT an accordion).
# (b17 refactored the inline build into the shared _mucCardHtml builder — same clause, same buffer.)
check('full MVU clause → muc buffer (always-visible)',
      'muc+=_mucCardHtml(muc_ar,muc_basis,muc_review);' in HTML
      and 'background:var(--bad-bg);border:2px solid var(--bad)' in HTML)
check('full MVU clause is NOT wrapped in _acc (assembly keeps t1+muc+t2)',
      'h=head+alerts+t1+muc+t2+t3+foot;' in HTML and '_acc(muc' not in HTML)
# 9. «ليس تقييماً معتمداً» line is in TIER-1 (always visible), a20 status appended when present.
check('not-certified line in TIER-1', "t1+='<div class=\"rn\" style=\"margin-top:10px;font-size:.82rem;color:#8a6d3b;background:#fcf8e3" in HTML and 'ليس تقييماً معتمداً' in HTML)
check('a20 rics_compliant_status appended to not-certified line', 'rics_compliant_status_ar' in HTML and '_statusAr' in HTML)
# 10. evidence ONE-ROW summary sits in TIER-1 (drama on evidence, not the figure).
check('evidence one-row in TIER-1 (t1+=_evOneRow(d))', 't1+=_evOneRow(d);' in HTML)
# 11. data-freshness caveat + disclaimer + verification route to the always-visible foot (NOT collapsed).
check('data-freshness caveat → foot', "foot+='<div class=\"dfc s-'+sev+'\">'+d.data_freshness.caveat_ar+'</div>';" in HTML)
check('disclaimer card → foot', "foot+='<div class=\"rc\" style=\"border-color:var(--warn-bg)\"><div class=\"rn\" style=\"font-size:.8rem\">'+d.disclaimer+'</div></div>';" in HTML)
check('verification footer → foot', "foot+='<div class=\"verification-footer\">';" in HTML)
# 12. alert panels (A11 / reality / multi-QARS / scope / sanity) route ABOVE the number (alerts buffer).
check('A11 mismatch → alerts (above number)', "alerts+='<div style=\"background:var(--warn-bg);border:2px solid var(--warn);border-radius:8px;padding:16px;margin-bottom:14px\">';\n    alerts+='<div style=\"font-weight:700;color:var(--warn);margin-bottom:8px;font-size:1.02rem\">⚠️ تناقض في تصنيف العقار</div>';" in HTML)
check('sanity warnings → alerts (above number)', "alerts+='<div class=\"sanity-warn\">" in HTML)
check('service-scope badge → alerts', "alerts+='<div style=\"background:'+scopeBg+';border-right:4px solid '+scopeColor+';" in HTML)

# ── NO PANEL LOST (detail blocks accumulate, then wrap) ──
# 13. the scratch `h` is collapsed into ONE TIER-2 «التفاصيل الكاملة» accordion (valued) / flat (refusal).
check('detail scratch → TIER-2 accordion (valued)', "if(hasValuation){ t2+=_acc('🔎 التفاصيل الكاملة (التحليل والمقارنات)', a8acc+h); }" in HTML)
check('detail scratch → flat (refusal)', 'else { flat+=h; }' in HTML)
check('scratch consumed before assembly', "h='';  // scratch consumed" in HTML)
# 14. basic-info → its own TIER-2 accordion. (b31/DEF-UX11 re-point: the full evidence panel is no
#     longer a standalone «جودة الأدلّة (تفصيل)» accordion — it now folds INTO the «كيف وصلنا لهذا الرقم؟»
#     accordion alongside the 9-note parade; assertion below + test_sprint_2_22_0b31.py own the new shape.)
check('basic-info → TIER-2 accordion', "t2+=_acc('🏠 بيانات العقار الأساسية',_info);" in HTML)
check('full evidence panel → «كيف وصلنا» accordion (b31 fold)', "t2+=_acc('🔍 كيف وصلنا لهذا الرقم؟', how+evidencePanelHtml(d,acc)" in HTML)  # b34: 3rd open arg → drop trailing );
# 15. brief sections: valued → accordion; refusal → flat (verbatim title card).
check('brief sections → TIER-2 accordion (valued)', "t2+=_acc('📄 '+(br.title_ar||'تفاصيل التقرير'),_secs);" in HTML)
check('brief sections → flat (refusal verbatim)', "flat+='<div class=\"rc\" style=\"background:transparent;border:none;padding:0;box-shadow:none;margin-bottom:6px\"><div class=\"rt\" style=\"font-size:1.15rem;margin-bottom:0\">'+(br.title_ar||'التقرير')+'</div></div>';" in HTML)

# ── TIER-3 actions ──
# 16. TIER-3 refine + report CTAs (valued path).
check('TIER-3 refine CTA → go(refine)', "t3+='<button class=\"t3btn t3-primary\" onclick=\"go(\\'refine\\')\">✏️ حسّن التقدير" in HTML)
# b17 landed: the report CTA opened screen 5 (openReport); Sprint 2.22.0b.25 (م2/D6)
# then made the SHORT report the first stop (full report one click away inside it) —
# the b15 invariant is that the TIER-3 secondary CTA leads to a REPORT surface.
check('TIER-3 report CTA → report surface (b17→b25/D6 chain)', "t3+='<button class=\"t3btn t3-secondary\" onclick=\"openShortReport()\">📄 التقرير المختصر" in HTML)

# ── Print parity (F1) ──
# 17. printReport force-opens the accordions before print + restores after.
check('printReport force-opens accordions', "document.querySelectorAll('#rOut details.t2acc')" in HTML and '_accs.forEach(a=>{a.open=true;});' in HTML)
check('printReport restores prior open-state', '_accs.forEach((a,i)=>{a.open=_wasOpen[i];});' in HTML)

# ── CSS for the new tier classes ──
check('.t2acc CSS present', '.t2acc{' in HTML and '.t2acc>summary{' in HTML)
check('.ev1row CSS present', '.ev1row{' in HTML)
check('.t3block CSS present', '.t3block{' in HTML and '.t3block .t3-primary{' in HTML)

# ── VALUE-INVARIANCE (show() does not touch the figure; range-as-lead b3 retained) ──
check('range headline label retained (range-as-lead)', 'النطاق التقديري السوقي' in HTML)
check('median muted marker retained', 'الوسيط (التقدير المركزي) ≈ <strong>' in HTML)
# b31/DEF-UX11 re-point: condition note STAYS on TIER-1 (decision-relevant); value_floor + hbu
# FOLD into the «كيف وصلنا» accordion (the `how` buffer). Strings still present — buffer changed.
check('condition note STAYS on TIER-1 (b31)', "if(v.condition_note_ar){t1+=" in HTML)
check('value_floor + hbu FOLD into «كيف وصلنا» (how buffer, b31)',
      'if(v.value_floor){' in HTML and 'how+=' in HTML and 'if(v.hbu_note_ar){how+=' in HTML)
check('moj sample-size (cite-n) still on TIER-1', 'صفقات البيع المسجلة لعقارات مشابهة' in HTML)
# show() does NOT mutate v.amount/v.low/v.high (no assignment to those fields anywhere).
check('no mutation of v.amount/v.low/v.high in show()', not re.search(r'\bv\.(amount|low|high)\s*=[^=]', HTML))

# ── Engine version (format only — R6 / Lesson-2: no exact pin) ──
check('ENGINE_VERSION format (thammen-sprint…)', re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+", ENG) is not None)
check('SPRINT_TAG dotted-numeric format', re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+", ENG) is not None)
# R6 / Lesson-2: NO exact version pin (it broke on the b16 bump) — assert only that the engine
# has moved AT/BEYOND b15 (the pre-b15 tag never returns; format already checked above).
check('engine at/beyond b15 (b14 tag gone)', "thammen-sprint2p22p0b14" not in ENG)

passed = sum(1 for _, ok in results if ok)
for name, ok in results:
    print(('PASS' if ok else 'FAIL'), '-', name)
print('\n%d/%d passed' % (passed, len(results)))
assert passed == len(results), '%d FAILED' % (len(results) - passed)
