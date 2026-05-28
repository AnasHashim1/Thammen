#!/usr/bin/env python3
"""
reasoning_trace.py — سلسلة الحقائق والمصادر التي قاد إليها التحليل.

الفكرة: ثمّن لا يقول "القيمة هي X". ثمّن يقول:
    "نظرنا في 22 صفقة من وزارة العدل، الوسيط Y،
     راجعنا 18 إعلاناً نشطاً في PropertyFinder، متوسطها Z،
     رسوم الخدمات للبرج W من إعلان FGRealty محدد،
     فالنتيجة: ..."

كل خطوة لها مصدر. كل مصدر له تاريخ. كل تاريخ يكشف الحداثة.

هذا ما يحمي الشركة قانونياً (شفافية كاملة) ويميّزها تجارياً (لا أحد آخر يفعل هذا).

Usage:
    from reasoning_trace import ReasoningTrace, ReasoningStep

    trace = ReasoningTrace()
    trace.add('identification',
              fact='الأصل: فيلا مستقلة، 542م²، تنظيم R2',
              source='gisqatar.org.qa/Districts',
              source_date='2026-05-09')
    trace.add('ground_truth',
              fact='MoJ يحوي 22 صفقة في الخيسة، 24 شهر، الوسيط 4,066 ر.ق/م²',
              source='data.gov.qa weekly bulletin',
              source_date='2026-05-08')
    print(trace.to_human_readable_ar())
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


# ============================================================
# Data classes
# ============================================================

@dataclass
class ReasoningStep:
    """خطوة واحدة في سلسلة المنطق."""
    step_number: int
    category: str               # 'identification' | 'ground_truth' | 'market_signal' |
                                # 'operating_cost' | 'adjustment' | 'unknown' | ...
    fact: str                   # الحقيقة بالنص العربي
    source: str                 # المصدر (URL أو اسم نظام)
    source_date: str = ''       # تاريخ البيان (YYYY-MM-DD أو YYYY-MM)
    confidence: str = 'medium'  # 'high' | 'medium' | 'low'
    details: dict = field(default_factory=dict)  # تفاصيل قابلة للحفر

    def to_dict(self) -> dict:
        return {
            'step': self.step_number,
            'category': self.category,
            'fact': self.fact,
            'source': self.source,
            'source_date': self.source_date,
            'confidence': self.confidence,
            'details': self.details,
        }


@dataclass
class SourceCitation:
    """استشهاد بمصدر — لطبقة الـ audit trail."""
    name: str                   # 'data.gov.qa' / 'qrepbe.aqarat.gov.qa' / 'fgrealty.qa'
    url: Optional[str] = None
    accessed_at: str = ''       # ISO datetime
    record_count: Optional[int] = None  # مثلاً عدد الصفقات المُحمَّلة

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'url': self.url,
            'accessed_at': self.accessed_at,
            'record_count': self.record_count,
        }


@dataclass
class ReasoningTrace:
    """
    السجل الكامل للمنطق وراء التقييم.

    يحوي:
        - steps: الخطوات الفعلية التي بنت النتيجة
        - sources_consulted: قائمة المصادر المُراجَعة
        - data_freshness: تاريخ أحدث بيان من كل مصدر
        - known_unknowns: ما لا نعرفه صراحةً
        - disclaimer: إخلاء المسؤولية القانوني
    """
    steps: List[ReasoningStep] = field(default_factory=list)
    sources_consulted: List[SourceCitation] = field(default_factory=list)
    data_freshness: dict = field(default_factory=dict)
    known_unknowns: List[str] = field(default_factory=list)
    generated_at: str = ''
    valuation_id: str = ''

    # إخلاء المسؤولية الموحَّد لكل تقرير
    # Sprint 2.22.0a.2 Gate 2 post-deploy fix (C4 9th site): this
    # reasoning_trace.disclaimer field was a C4 miss in the original
    # 8-site sweep — same defensive-negation → descriptive-provenance
    # reframe per docs/MULTI_AI_VALIDATION_BATCH_2p22p0a2.md §4.
    # Note: this site used the older long-form variant
    # ("وفق معايير RICS أو IVS") rather than the short form, but the
    # reframe is identical — name the role + artefact, not the absence
    # of certification.
    # Sprint 2.22.0a.3 T-mzad (live honesty): Mzadqatar is permanently
    # excluded from Thammen's data pipeline (T5 — auction-only listings
    # don't match the active-listing semantics the disclaimer implies).
    # Listing it here claimed a source we do not use. FGRealty +
    # PropertyFinder + arady are valid T2 sources.
    disclaimer: str = (
        "ثمّن يجمع البيانات السوقية من المصادر الحكومية (وزارة العدل، "
        "وزارة البلدية والبيئة) والإعلانات النشطة (FGRealty، PropertyFinder، "
        "arady). هذا تحليل معلوماتي للقرار، "
        "ولا يُعتبر تقرير تثمين رسمي صادر عن مثمّن مرخّص وفق معايير RICS/IVS. "
        "القرار النهائي ومسؤوليته على العميل. "
        "للأغراض الرسمية (قروض بنكية، محاكم، تقارير محاسبية) يلزم تقييم من "
        "مُقيِّم معتمد."
    )

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now().isoformat(timespec='seconds')

    def add(self, category: str, fact: str, source: str,
            source_date: str = '', confidence: str = 'medium',
            details: Optional[dict] = None) -> 'ReasoningTrace':
        """أضف خطوة جديدة. يدعم chaining."""
        step = ReasoningStep(
            step_number=len(self.steps) + 1,
            category=category,
            fact=fact,
            source=source,
            source_date=source_date,
            confidence=confidence,
            details=details or {},
        )
        self.steps.append(step)
        # حدّث freshness
        if source and source_date:
            current = self.data_freshness.get(source, '')
            if source_date > current:
                self.data_freshness[source] = source_date
        return self

    def add_source(self, name: str, url: Optional[str] = None,
                   record_count: Optional[int] = None) -> 'ReasoningTrace':
        """سجّل مصدراً تمت استشارته."""
        # تجنّب التكرار
        for s in self.sources_consulted:
            if s.name == name:
                if record_count and not s.record_count:
                    s.record_count = record_count
                return self
        self.sources_consulted.append(SourceCitation(
            name=name, url=url,
            accessed_at=datetime.now().isoformat(timespec='seconds'),
            record_count=record_count,
        ))
        return self

    def add_unknown(self, what: str) -> 'ReasoningTrace':
        """سجّل ما لا نعرفه — أهم من أي رقم نعرفه."""
        if what not in self.known_unknowns:
            self.known_unknowns.append(what)
        return self

    def to_dict(self) -> dict:
        return {
            'valuation_id': self.valuation_id,
            'generated_at': self.generated_at,
            'steps': [s.to_dict() for s in self.steps],
            'sources_consulted': [s.to_dict() for s in self.sources_consulted],
            'data_freshness': self.data_freshness,
            'known_unknowns': self.known_unknowns,
            'disclaimer': self.disclaimer,
        }

    def to_human_readable_ar(self) -> str:
        """نص عربي قابل للقراءة لكل خطوة + المصادر + المجاهيل."""
        lines = []
        lines.append("═" * 60)
        lines.append("سلسلة المنطق التي قادت إلى هذا التحليل")
        lines.append("═" * 60)

        for s in self.steps:
            conf_emoji = {'high': '✓', 'medium': '○', 'low': '?'}.get(s.confidence, '○')
            date_str = f" [{s.source_date}]" if s.source_date else ""
            lines.append(f"\n{s.step_number}. {conf_emoji} {s.fact}")
            lines.append(f"   مصدر: {s.source}{date_str}")

        if self.sources_consulted:
            lines.append("\n" + "─" * 60)
            lines.append("المصادر المُراجَعة:")
            for src in self.sources_consulted:
                rec_str = f" ({src.record_count:,} سجل)" if src.record_count else ""
                lines.append(f"  • {src.name}{rec_str}")

        if self.data_freshness:
            lines.append("\n" + "─" * 60)
            lines.append("حداثة البيانات:")
            for src, date in sorted(self.data_freshness.items()):
                lines.append(f"  • {src}: آخر تحديث {date}")

        if self.known_unknowns:
            lines.append("\n" + "─" * 60)
            lines.append("ما لم يستطع التحليل تحديده (يجب التحقق ميدانياً):")
            for u in self.known_unknowns:
                lines.append(f"  ⚠ {u}")

        lines.append("\n" + "─" * 60)
        lines.append("إخلاء مسؤولية:")
        # تقسيم النص الطويل لأسطر مقروءة
        words = self.disclaimer.split()
        line = "  "
        for word in words:
            if len(line) + len(word) > 70:
                lines.append(line)
                line = "  " + word
            else:
                line = line + " " + word if line.strip() else "  " + word
        if line.strip():
            lines.append(line)

        return "\n".join(lines)


# ============================================================
# Helpers لبناء سريع للسلسلة من مكونات evaluate_property
# ============================================================

def build_from_moj_valuation(trace: ReasoningTrace, moj_val) -> ReasoningTrace:
    """أضف خطوات MoJ من كائن MoJValuation."""
    if not moj_val:
        return trace

    n = moj_val.bracket_n or 0
    bracket = moj_val.size_bracket or 'غير محدد'

    if moj_val.moj_median_per_m2:
        confidence = 'high' if n >= 20 else ('medium' if n >= 10 else 'low')
        trace.add(
            category='ground_truth',
            fact=(f"وزارة العدل سجّلت {n} صفقة لشريحة {bracket}م² في 24 شهر؛ "
                  f"الوسيط {moj_val.moj_median_per_m2:,.0f} ر.ق/م² "
                  f"(القيمة الإجمالية {moj_val.moj_median_total:,.0f} ر.ق)"),
            source='data.gov.qa weekly-real-estates-sales-bulletin',
            confidence=confidence,
            details={'n': n, 'bracket': bracket,
                     'median_per_m2': moj_val.moj_median_per_m2,
                     'p25': moj_val.estimated_value_low,
                     'p75': moj_val.estimated_value_high},
        )
        trace.add_source('data.gov.qa', 'https://www.data.gov.qa', record_count=n)

        if n < 10:
            trace.add(
                category='material_uncertainty',
                fact=(f"تحفّظ جوهري: العينة صغيرة (n={n}). الوسيط إرشادي فقط، "
                      f"لا يصلح لاتخاذ قرار نهائي بدون تحقق إضافي."),
                source='data_quality_check',
                confidence='high',
            )

    # طبقة عوامل GIS
    if moj_val.factors_adjustment is not None and moj_val.factors_detail:
        adj_pct = moj_val.factors_adjustment * 100
        positive_factors = [f for f in moj_val.factors_detail if f.get('direction') == 'positive']
        negative_factors = [f for f in moj_val.factors_detail if f.get('direction') == 'negative']

        fact = f"تعديلات GIS: {adj_pct:+.1f}% بناءً على "
        if positive_factors:
            fact += f"{len(positive_factors)} عامل إيجابي"
        if negative_factors:
            fact += f"{' و' if positive_factors else ''}{len(negative_factors)} عامل سلبي"

        trace.add(
            category='adjustment',
            fact=fact,
            source='services.gisqatar.org.qa',
            confidence='medium',
            details={'factors': moj_val.factors_detail,
                     'adjustment_pct': adj_pct,
                     'fair_price': moj_val.fair_price_total},
        )
        trace.add_source('gisqatar.org.qa', record_count=len(moj_val.factors_detail))

    return trace


def build_from_replacement_cost(trace: ReasoningTrace, repl_cost) -> ReasoningTrace:
    """أضف خطوات منهج التكلفة."""
    if not repl_cost:
        return trace

    age = repl_cost.building_age_years
    age_str = f"{age} سنوات" if age else "غير معروف"

    trace.add(
        category='cost_approach',
        fact=(f"منهج التكلفة: قيمة الأرض {repl_cost.land_value:,.0f} + "
              f"قيمة المبنى المُستهلَك {repl_cost.depreciated_building_value:,.0f} = "
              f"{repl_cost.total_replacement_value:,.0f} (BUA={repl_cost.bua_m2:.0f}م²، "
              f"عمر={age_str}، استهلاك={repl_cost.depreciation_pct*100:.0f}%)"),
        source='internal_construction_cost_calibration',
        confidence='medium' if age else 'low',
        details={
            'land_value': repl_cost.land_value,
            'building_value': repl_cost.depreciated_building_value,
            'total': repl_cost.total_replacement_value,
            'bua': repl_cost.bua_m2,
            'age_years': age,
        },
    )
    return trace


def build_from_listing_comparison(trace: ReasoningTrace, comparison) -> ReasoningTrace:
    """أضف خطوة المقارنة بسعر الإعلان."""
    if not comparison:
        return trace

    trace.add(
        category='market_signal',
        fact=(f"سعر الإعلان {comparison.listing_price:,.0f} مقابل {comparison.benchmark_label} "
              f"{comparison.benchmark_total:,.0f} → فجوة {comparison.gap_pct*100:+.1f}%"),
        source='user_provided_listing',
        confidence='high',
        details={
            'listing': comparison.listing_price,
            'benchmark': comparison.benchmark_total,
            'gap_qar': comparison.gap_qar,
            'gap_pct': comparison.gap_pct,
        },
    )
    return trace


def build_from_listing_flags(trace: ReasoningTrace, flags) -> ReasoningTrace:
    """أضف خطوات الأعلام (red/green) من وصف الإعلان."""
    if not flags:
        return trace

    if flags.red_flags:
        labels = [f['label'] for f in flags.red_flags]
        trace.add(
            category='listing_red_flag',
            fact=f"إشارات تحذيرية في وصف الإعلان: {'، '.join(labels)}",
            source='listing_description_analysis',
            confidence='high',
            details={'red_flags': flags.red_flags},
        )

    if flags.green_flags:
        labels = [f['label'] for f in flags.green_flags]
        trace.add(
            category='listing_green_flag',
            fact=f"إشارات إيجابية في وصف الإعلان: {'، '.join(labels)}",
            source='listing_description_analysis',
            confidence='high',
            details={'green_flags': flags.green_flags},
        )

    return trace


def add_standard_unknowns(trace: ReasoningTrace, asset_type: str = 'apartment') -> ReasoningTrace:
    """أضف المجاهيل المعيارية التي لا يستطيع النظام معرفتها."""
    standard = [
        "حالة العقار الداخلية الفعلية (تشطيبات، صيانة، تكييف)",
        "أي التزامات قانونية (رهون، خلافات، إرث، حصص غير مفروزة)",
        "تاريخ آخر تجديد فعلي أو حالة الأنظمة (سباكة، كهرباء)",
        "وضع المستأجر الحالي (إن وُجد) ومدة العقد",
    ]
    if asset_type == 'apartment':
        standard.extend([
            "الإطلالة الفعلية والطابق",
            "ضوضاء البرج/المحيط أو مشاكل خاصة",
        ])
    elif asset_type in ('villa_standalone', 'villa_compound'):
        standard.extend([
            "حالة الحديقة وحوض السباحة (إن وُجد)",
            "حالة الجدران الخارجية والسقف",
            # Sprint 2.22.0a.3 T2.7 (deduped): Qatar legality gaps.
            # 3 items, deliberately distinct from the standard list above.
            # Subdivision/parcellation status is NOT re-added — it is
            # already covered by `standard[1]` ("أي التزامات قانونية
            # ... حصص غير مفروزة"). Each item below names a verification
            # path the engine cannot run from GIS/MoJ alone (municipality
            # records, SAK title, on-site).
            "تعديلات غير مرخصة من البلدية على البناء الأصلي (تجاوزات الارتدادات أو الارتفاع المسموح)",
            "ملاحق وإضافات غير موثقة في السجل العقاري (غرف خدم، مظلات، مسابح، حدائق مضافة)",
            "التحقق من شهادة إتمام الإشغال / شهادة إنجاز البناء من البلدية",
        ])

    for u in standard:
        trace.add_unknown(u)
    return trace


# ============================================================
# CLI للاختبار
# ============================================================
if __name__ == '__main__':
    # مثال شامل
    trace = ReasoningTrace(valuation_id='THM-20260509-001')

    trace.add(
        category='identification',
        fact='الأصل: فيلا مستقلة، 542م²، تنظيم R2 (سكني عادي)',
        source='gisqatar.org.qa/Districts + CadastrePlots',
        source_date='2026-05-09',
        confidence='high',
    )

    trace.add(
        category='ground_truth',
        fact='وزارة العدل سجّلت 22 صفقة لشريحة 400-600م² في الخيسة، 24 شهر؛ الوسيط 5,048 ر.ق/م²',
        source='data.gov.qa weekly-real-estates-sales-bulletin',
        source_date='2026-05-08',
        confidence='high',
        details={'n': 22, 'median': 5048, 'bracket': '400-600'},
    )

    trace.add(
        category='market_signal',
        fact='PropertyFinder يعرض 18 إعلاناً نشطاً للفلل في الخيسة بنفس الشريحة، الوسيط 6,200 ر.ق/م² (+22.8% فوق MoJ)',
        source='propertyfinder.qa',
        source_date='2026-05-09',
        confidence='medium',
    )

    trace.add(
        category='adjustment',
        fact='تعديل GIS: +5% (قطعة زاوية، قرب مدرسة)',
        source='services.gisqatar.org.qa',
        source_date='2026-05-09',
        confidence='medium',
    )

    trace.add_source('data.gov.qa', 'https://www.data.gov.qa', record_count=22)
    trace.add_source('propertyfinder.qa', 'https://www.propertyfinder.qa', record_count=18)
    trace.add_source('gisqatar.org.qa', 'https://services.gisqatar.org.qa')

    add_standard_unknowns(trace, asset_type='villa_standalone')

    print(trace.to_human_readable_ar())

    print("\n\n" + "═" * 60)
    print("نفس البيانات بصيغة JSON (للـ API):")
    print("═" * 60)
    import json
    print(json.dumps(trace.to_dict(), ensure_ascii=False, indent=2)[:1500])
