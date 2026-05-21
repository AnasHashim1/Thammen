"""
adjustment_grid.py — Sprint 2.20: RICS Market-Comparison adjustment grid.

v1 scope (Sprint 2.20.0): LAND asset type, **TIME adjustment only**. Each MoJ
land comparable is normalised to the valuation date using the area's annual
price trend. Size adjustment is **deferred to 2.20.1** (the §8 stability scan
found within-bracket size→price/m² too weak: median R²≈0.05, 28.4% stable < 40%
gate). Corner is deferred until a PIN-keyed sale source exists (E12 BLOCKED).

The framework (Adjustment / Comparable / AdjustmentGrid) carries tier metadata
(E8) and structurally supports additional factors (e.g. 'size', 'corner') so
later Sprints wire them without a refactor — but v1 emits ONLY 'time'.

Empirical Findings touched:
  - E8  Source-tier weighting (T1=1.0, T2=0.7, T4=0.4).
  - E10 Transparent attribution (sources + tier + n in every output).
  - E11 Tier floor / n-gate (reliable n≥20, indicative 10–19, <10 → fallback).

Pure stdlib, no I/O, fully unit-testable.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

# E8 — source-tier weights.
TIER_WEIGHTS = {1: 1.0, 2: 0.7, 4: 0.4}
# E11 — reliability gates (project sample-size discipline).
RELIABLE_N = 20
INDICATIVE_N = 10


# --------------------------------------------------------------------------
# Small pure helpers
# --------------------------------------------------------------------------

def _median(xs):
    s = sorted(v for v in xs if v is not None)
    n = len(s)
    if not n:
        return None
    m = n // 2
    return s[m] if n % 2 else (s[m - 1] + s[m]) / 2.0


def weighted_median(pairs):
    """E8 weighted median. `pairs` = iterable of (value, weight). Weights ≤0 skipped.

    With a single tier (all weight 1.0) this reduces to the plain median.
    """
    items = sorted((v, w) for v, w in pairs if v is not None and w and w > 0)
    if not items:
        return None
    total = sum(w for _, w in items)
    half = total / 2.0
    cum = 0.0
    for v, w in items:
        cum += w
        if cum >= half:
            return v
    return items[-1][0]


def _parse_date(s):
    if isinstance(s, datetime):
        return s
    for fmt in ('%Y-%m-%d', '%Y/%m/%d'):
        try:
            return datetime.strptime(str(s)[:10], fmt)
        except (ValueError, TypeError):
            continue
    return None


def _years_between(d_from, d_to):
    """Signed years from d_from to d_to (positive when d_to is later)."""
    return (d_to - d_from).days / 365.25


# --------------------------------------------------------------------------
# Dataclasses
# --------------------------------------------------------------------------

@dataclass
class Adjustment:
    factor: str            # 'time' (v1) | 'size' | 'corner' (future)
    pct: float             # decimal multiplier delta, e.g. -0.03 = −3%
    source: str            # 'moj' | 'arady' | ...
    tier: int              # 1 (T1 ground truth) | 2 | 4
    n: int = 0
    confidence: str = 'indicative'
    rationale_ar: str = ''

    @property
    def tier_weight(self) -> float:        # E8
        return TIER_WEIGHTS.get(self.tier, 0.0)

    def to_dict(self):
        return {
            'factor': self.factor,
            'pct': round(self.pct, 5),
            'pct_display': round(self.pct * 100, 2),
            'source': self.source,
            'tier': self.tier,
            'tier_weight': self.tier_weight,
            'n': self.n,
            'confidence': self.confidence,
            'rationale_ar': self.rationale_ar,
        }


@dataclass
class Comparable:
    price_per_m2_raw: float
    date: str
    size_m2: Optional[float] = None
    adjustments: List[Adjustment] = field(default_factory=list)

    @property
    def adjusted_price_per_m2(self) -> float:
        """raw × Π(1 + adj.pct) — composes all factors (only 'time' in v1)."""
        v = self.price_per_m2_raw
        for a in self.adjustments:
            v *= (1.0 + a.pct)
        return v

    def to_dict(self):
        return {
            'date': self.date,
            'price_per_m2_raw': round(self.price_per_m2_raw, 1),
            'price_per_m2_adjusted': round(self.adjusted_price_per_m2, 1),
            'size_m2': self.size_m2,
            'adjustments': [a.to_dict() for a in self.adjustments],
        }


@dataclass
class AdjustmentGrid:
    subject: dict
    comparables: List[Comparable]
    adjusted_median_per_m2: Optional[float]
    n: int
    confidence: str                 # 'reliable' | 'indicative' | 'fallback'
    sources: list                   # E10 attribution
    fallback_used: bool
    valuation_date: str
    note_ar: str = ''

    def to_dict(self):
        return {
            'subject': self.subject,
            'n': self.n,
            'confidence': self.confidence,
            'fallback_used': self.fallback_used,
            'valuation_date': self.valuation_date,
            'adjusted_median_per_m2': (round(self.adjusted_median_per_m2, 1)
                                       if self.adjusted_median_per_m2 is not None else None),
            'sources': self.sources,                       # E10
            'comparables': [c.to_dict() for c in self.comparables],
            'note_ar': self.note_ar,
        }


# --------------------------------------------------------------------------
# Builder (v1: LAND, time-only)
# --------------------------------------------------------------------------

def build_land_grid(comparables, valuation_date=None, annual_trend_pct=0.0,
                    subject=None, reliable_n=RELIABLE_N, indicative_n=INDICATIVE_N):
    """Build a LAND adjustment grid (time-only) from MoJ comparables.

    Args:
        comparables: list of dicts with keys ``date`` ('YYYY-MM-DD'),
                     ``price_m2`` (>0), and optionally ``area_m2``.
        valuation_date: 'YYYY-MM-DD' or datetime; defaults to today.
        annual_trend_pct: area land price trend in **percent/year** (e.g. -2.07).
                          0 → no time adjustment (grid still shows comparables).
        subject: optional dict echoed back (area, bracket, plot_area_m2 …).

    Returns an ``AdjustmentGrid``. When usable comparables < ``indicative_n`` the
    grid is marked ``fallback`` (the caller should fall back to Sprint 2.16.0
    stratification and NOT render a grid).
    """
    val_dt = _parse_date(valuation_date) or datetime.utcnow()
    val_str = val_dt.strftime('%Y-%m-%d')
    subject = subject or {}

    clean = []
    for c in comparables or []:
        ppm2 = c.get('price_m2')
        d = _parse_date(c.get('date'))
        if not ppm2 or ppm2 <= 0 or d is None:
            continue
        clean.append((c, d, ppm2))

    n = len(clean)
    if n < indicative_n:
        return AdjustmentGrid(
            subject=subject, comparables=[], adjusted_median_per_m2=None,
            n=n, confidence='fallback', sources=[], fallback_used=True,
            valuation_date=val_str,
            note_ar='عدد المقارنات غير كافٍ لشبكة مقارنات (تم الرجوع إلى التصنيف الطبقي).',
        )

    rate = (annual_trend_pct or 0.0) / 100.0
    confidence = 'reliable' if n >= reliable_n else 'indicative'

    comps = []
    for c, d, ppm2 in clean:
        adjustments = []
        if rate:
            years = _years_between(d, val_dt)        # +ve when sale precedes valuation
            time_pct = rate * years                  # bring older sale to today
            adjustments.append(Adjustment(
                factor='time', pct=time_pct, source='moj', tier=1,
                n=n, confidence=confidence,
                rationale_ar=(f'تطبيع زمني إلى تاريخ التقييم بمعدّل اتجاه السوق '
                              f'{annual_trend_pct:+.1f}%/سنة'),
            ))
        comps.append(Comparable(price_per_m2_raw=ppm2, date=c.get('date'),
                                size_m2=c.get('area_m2'), adjustments=adjustments))

    adjusted_median = _median([c.adjusted_price_per_m2 for c in comps])
    sources = [{                                      # E10
        'source': 'moj', 'tier': 1, 'tier_weight': TIER_WEIGHTS[1],
        'n': n, 'role_ar': 'صفقات بيع وزارة العدل (الحقيقة السوقية)',
    }]
    note = ('شبكة مقارنات RICS: كل صفقة طُبِّعت زمنياً إلى تاريخ التقييم. '
            'لا تُغيّر القيمة الرئيسية — عرض شفاف للمقارنات.')
    return AdjustmentGrid(
        subject=subject, comparables=comps, adjusted_median_per_m2=adjusted_median,
        n=n, confidence=confidence, sources=sources, fallback_used=False,
        valuation_date=val_str, note_ar=note,
    )
