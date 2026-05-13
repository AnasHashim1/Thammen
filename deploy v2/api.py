#!/usr/bin/env python3
"""
api.py — FastAPI backend for Thammen (ثمّن)

Sprint 1 hardening applied:
    - CORS restricted to thammen.qa origins only
    - Rate limiting via slowapi (10 req/min per IP for evaluate)
    - Environment variables for sensitive/configurable settings
    - Centralized logging
"""

import json
import logging
import os
import traceback
from datetime import datetime
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Rate limiting (slowapi)
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# ── Logging setup ──
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("thammen")

# ── Import our engine ──
from evaluate_property import (
    evaluate_property, BuaBreakdown, PropertyEvaluation,
    compute_max_footprint, estimate_footprint_from_imagery,
)
from moj_db import open_db, query_reference, query_trend, init_db

# ── Sprint 2.7: Data Freshness Transparency ──
from data_freshness import (
    compute_freshness,
    freshness_for_response,
    freshness_for_homepage,
    freshness_for_health,
    FreshnessReport,
)

# ── NEW v3.1: Unified engine with geo_v2 + listings ──
try:
    from evaluate_unified import evaluate_thammen
    _UNIFIED_OK = True
    log.info("Unified engine loaded (geo_v2 + listings available)")
except ImportError as e:
    _UNIFIED_OK = False
    log.warning(f"Unified engine not available: {e} — using v2 fallback")

# ── Config (via environment variables) ──
MOJ_CSV = Path(os.getenv("MOJ_CSV_PATH", "moj_weekly.csv"))
MOJ_DB = Path(os.getenv("MOJ_DB_PATH", "moj_weekly.db"))

# Initialize DB if not exists
if MOJ_CSV.exists() and not MOJ_DB.exists():
    log.info("Initializing MoJ database...")
    conn = init_db(MOJ_CSV, force=True)
    conn.close()
    log.info(f"MoJ database ready at {MOJ_DB}")
elif MOJ_DB.exists():
    log.info(f"MoJ database already exists at {MOJ_DB}")
else:
    log.warning(f"MoJ CSV not found at {MOJ_CSV}")

# ── Sprint 1 Task 7: Preload GIS districts at startup ──
# This loads 789 Qatar districts from a local JSON file (~167 KB)
# Replaces network calls to GIS during evaluations → 5-10s saved per request
try:
    from gis_preload import load_districts
    GIS_PATH = Path(os.getenv("GIS_DISTRICTS_PATH", "qatar_districts.json"))
    if GIS_PATH.exists():
        districts = load_districts(str(GIS_PATH))
        log.info(f"GIS preload: {len(districts)} districts ready (in-memory)")
    else:
        log.warning(f"GIS districts file not found at {GIS_PATH} — "
                    "fallback to network queries (slower)")
except ImportError as e:
    log.warning(f"GIS preload not available: {e}")

# ── App ──
app = FastAPI(
    title="Thammen API",
    description="Qatar Real Estate Valuation — بيانات وزارة العدل",
    version="3.1.0",
)

# ── Rate Limiting ──
# Default: 10 evaluations/minute per IP. Override via RATE_LIMIT env var.
RATE_LIMIT = os.getenv("RATE_LIMIT", "10/minute")
limiter = Limiter(key_func=get_remote_address, default_limits=[])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
log.info(f"Rate limit configured: {RATE_LIMIT} for /api/evaluate*")

# ── CORS — restricted via env var ──
# Default origins for production. Override with ALLOWED_ORIGINS env var
# (comma-separated). For local dev set ALLOWED_ORIGINS=*
_default_origins = "https://thammen.qa,https://www.thammen.qa"
_origins_env = os.getenv("ALLOWED_ORIGINS", _default_origins)
ALLOWED_ORIGINS = [o.strip() for o in _origins_env.split(",") if o.strip()]
log.info(f"CORS allowed origins: {ALLOWED_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "Authorization"],
)


# ── Sprint 2.7: Data Freshness — cache + helpers ──
# Computed once at startup; refreshed via /api/health hits so a CSV
# replacement on disk is picked up without restarting the dyno.
_freshness_cache: Optional[FreshnessReport] = None


def get_freshness() -> Optional[FreshnessReport]:
    """Return the cached freshness, computing it lazily if missing.

    Returns None on failure (missing CSV, parse error). Callers must
    handle the None case — never crash the request on a freshness fault.
    """
    global _freshness_cache
    if _freshness_cache is not None:
        return _freshness_cache
    try:
        _freshness_cache = compute_freshness(MOJ_CSV)
        log.info(
            f"Freshness: latest={_freshness_cache.latest_record} "
            f"days_old={_freshness_cache.days_old} "
            f"tier={_freshness_cache.tier}"
        )
        return _freshness_cache
    except Exception as e:
        log.warning(f"Freshness computation failed: {e}")
        return None


def refresh_freshness() -> Optional[FreshnessReport]:
    """Force a recompute. Call after the cron job replaces the CSV."""
    global _freshness_cache
    _freshness_cache = None
    return get_freshness()


def _attach_freshness(result):
    """Mutate the result dict (or simplified eval) to include the
    `data_freshness` field. Tolerates non-dict results (returns
    unchanged). Never raises — freshness is best-effort.
    """
    try:
        if not isinstance(result, dict):
            return result
        fresh = get_freshness()
        if fresh is not None:
            result["data_freshness"] = freshness_for_response(fresh)
    except Exception:
        pass
    return result


# Warm the cache at startup
try:
    get_freshness()
except Exception:
    pass


# ── Request Models ──

class EvaluateRequest(BaseModel):
    zone: int
    street: int
    building: int
    audience: Optional[str] = 'buyer'  # Sprint 1: now wired to backend


class EvaluateDetailsRequest(BaseModel):
    zone: int
    street: int
    building: int
    audience: Optional[str] = 'buyer'  # Sprint 1: now wired to backend
    floors: Optional[int] = None          # ABOVE-GROUND floors: 1, 2, 3, 4 (basement is separate)
    annexes: Optional[int] = None         # 0, 1, 2, 3
    condition: Optional[str] = None       # 'new', 'good', 'maintenance', 'renovated'
    asking_price: Optional[float] = None  # listing price (QAR)
    rental_income: Optional[float] = None # monthly rental (QAR)
    potential_rental: Optional[float] = None
    # Sprint 2.2 — explicit building improvements (RICS Red Book "subject property" specs)
    basement: Optional[bool] = None       # سرداب — adds significant unrecorded value
    footprint_m2: Optional[float] = None  # ground-floor footprint estimate (overrides default)
    external_majlis: Optional[bool] = None  # مجلس خارجي منفصل
    # Sprint 2.3 — Qatar 10-Year Rule (age-aware adjustment)
    building_age_years: Optional[int] = None  # عمر البناء التقديري بالسنوات
    is_luxury: Optional[bool] = None          # تشطيب فاخر (للاستثناء من قاعدة الـ 10 سنوات)


# ── Helpers ──

FOOTPRINT_RATIOS = {1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0}
CONDITION_TO_RENOVATION = {
    'new': (False, False),
    'good': (False, False),
    'maintenance': (False, False),
    'renovated': (True, False),
}
# Rough floor areas as fraction of footprint
UPPER_FLOOR_RATIO = 0.85  # upper floors slightly smaller than ground


def _build_bua_breakdown(footprint_m2: float, floors: int, annexes_m2: float) -> BuaBreakdown:
    """Build BUA breakdown from footprint + floor count."""
    if floors <= 1:
        return BuaBreakdown(
            main_footprint_m2=footprint_m2,
            basement_m2=0,
            upper_floors_m2=0, upper_floor_count=0,
            annexes_m2=annexes_m2, annex_count=max(1, int(annexes_m2 / 50)),
            external_m2=0,
        )
    elif floors == 2:
        return BuaBreakdown(
            main_footprint_m2=footprint_m2,
            basement_m2=0,
            upper_floors_m2=round(footprint_m2 * UPPER_FLOOR_RATIO),
            upper_floor_count=1,
            annexes_m2=annexes_m2, annex_count=max(1, int(annexes_m2 / 50)) if annexes_m2 else 0,
            external_m2=0,
        )
    else:  # 3+ (includes basement as one floor)
        upper_count = floors - 2  # ground + N upper (one floor assumed basement)
        return BuaBreakdown(
            main_footprint_m2=footprint_m2,
            basement_m2=footprint_m2,  # basement ≈ ground footprint
            upper_floors_m2=round(footprint_m2 * UPPER_FLOOR_RATIO * upper_count),
            upper_floor_count=upper_count,
            annexes_m2=annexes_m2, annex_count=max(1, int(annexes_m2 / 50)) if annexes_m2 else 0,
            external_m2=0,
        )


def _simplify_evaluation(ev: PropertyEvaluation, detailed: bool = False) -> dict:
    """Convert evaluation to simplified JSON for the frontend."""
    result = {
        'address': ev.address,
        'valuation_date': ev.valuation_date,
        'district': ev.gis_district_aname,
        'municipality': None,
        'plot_area_m2': ev.plot_area_m2,
        'asset_type': ev.asset_type,
    }

    # Valuation
    if ev.blended:
        result['valuation'] = {
            'amount': _round100k(ev.blended.blended_value),
            'low': _round100k(ev.blended.blended_low),
            'high': _round100k(ev.blended.blended_high),
            'method': 'blended',
        }
    elif ev.valuation and ev.valuation.moj_median_total:
        val = ev.valuation.fair_price_total or ev.valuation.moj_median_total
        result['valuation'] = {
            'amount': _round100k(val),
            'low': _round100k(ev.valuation.estimated_value_low),
            'high': _round100k(ev.valuation.estimated_value_high),
            'method': 'moj',
        }
    else:
        result['valuation'] = None

    # MoJ reference
    if ev.valuation:
        v = ev.valuation
        # Zoning label
        zoning = 'غير محدد'
        if v.factors_detail:
            for f in v.factors_detail:
                if f.get('code', '').startswith('zoning'):
                    zoning = f.get('label_ar', zoning)
                    break

        result['property_info'] = {
            'zoning': zoning,
            'permitted_height': None,  # filled from factors
        }

        # Extract permitted height from factors
        if v.factors_detail:
            for f in v.factors_detail:
                if 'height' in f.get('code', '') or 'ارتفاع' in f.get('label_ar', ''):
                    result['property_info']['permitted_height'] = f.get('label_ar', '')

        result['moj_sample_size'] = v.bracket_n

    # Confidence
    result['accuracy'] = {
        'score': ev.confidence_score,
        'label': ev.confidence_label,
    }

    # Trend
    if ev.trend:
        result['trend'] = {
            'label': ev.trend.get('label'),
            'slope_pct': ev.trend.get('slope_annual_pct', 0) * 100,
            'years': ev.trend.get('years', []),
        }

    # Factors (simplified with user-friendly labels)
    # Note: "تزوير" was a typo for "تنظيم" (zoning) — corrected here
    LABEL_FIXES = {
        'تزوير R1': 'منطقة سكنية خاصة (R1)',
        'تزوير R2': 'منطقة سكنية (R2)',
        'تزوير R3': 'منطقة سكنية مكثفة (R3)',
        'تزوير C': 'منطقة تجارية (C)',
        'تنظيم R1': 'منطقة سكنية خاصة (R1)',
        'تنظيم R2': 'منطقة سكنية (R2)',
        'تنظيم R3': 'منطقة سكنية مكثفة (R3)',
        'تنظيم C': 'منطقة تجارية (C)',
    }
    HEIGHT_FIXES = {
        'G': 'أرضي فقط',
        'G+P': 'أرضي + سطح',
        'G+1': 'أرضي + أول',
        'G+1+P': 'أرضي + أول + سطح',
        'G+2': 'أرضي + طابقين',
        'G+2+P': 'أرضي + طابقين + سطح',
    }

    result['location_features'] = []
    if ev.valuation and ev.valuation.factors_detail:
        for f in ev.valuation.factors_detail:
            label = f.get('label_ar', '')
            # Fix zoning labels
            for old, new in LABEL_FIXES.items():
                label = label.replace(old, new)
            # Fix height labels
            for old, new in HEIGHT_FIXES.items():
                if old in label:
                    label = label.replace(old, new)
            # Sprint 2.9: 3-state direction (positive | negative | neutral=null).
            # Was: `f.get('direction') == 'positive'` which collapsed neutral
            # to False and made the UI render R2 zoning (and other neutral
            # factors) with the red-error palette.
            direction = f.get('direction', 'neutral')
            if direction == 'positive':
                positive = True
            elif direction == 'negative':
                positive = False
            else:
                positive = None
            result['location_features'].append({
                'label': label,
                'positive': positive,
            })

    # Fix property_info labels too
    if result.get('property_info'):
        z = result['property_info'].get('zoning', '')
        for old, new in LABEL_FIXES.items():
            z = z.replace(old, new)
        result['property_info']['zoning'] = z

        h = result['property_info'].get('permitted_height', '') or ''
        for old, new in HEIGHT_FIXES.items():
            if old in h:
                h = h.replace(old, new)
        result['property_info']['permitted_height'] = h

    # ── v2: Market position (descriptive, NOT a verdict) ──
    # Replaces v1's price_comparison.verdict ('BARGAIN'/'OVERPRICED'/etc.)
    if ev.market_position:
        result['market_position'] = {
            'listing_qar': ev.market_position.get('listing_qar'),
            'benchmark_qar': ev.market_position.get('benchmark_qar'),
            'benchmark_source': ev.market_position.get('benchmark_source'),
            'benchmark_n': ev.market_position.get('benchmark_n'),
            'gap_pct': ev.market_position.get('gap_pct'),
            'position_label': ev.market_position.get('position_label'),  # 'above_market' etc.
            'description_ar': ev.market_position.get('description_ar'),
            'caveats': ev.market_position.get('caveats', []),
        }
    elif ev.listing_comparison:
        # Fallback for backward compat — but no verdict
        lc = ev.listing_comparison
        result['market_position'] = {
            'gap_pct': getattr(lc, 'gap_pct', None),
            'description_ar': 'بيانات وصفية غير متوفرة',
        }

    # Rental (if provided) — now includes itemized cost breakdown in v2
    result['rental'] = ev.rental_analysis

    # Transaction count (teaser for paywall)
    result['transaction_count'] = ev.valuation.bracket_n if ev.valuation else 0

    # ── v2: Reasoning trace (transparency layer) ──
    # هذا ما يميّز ثمّن قانونياً وتجارياً: كل رقم له مصدر، كل حقيقة لها تاريخ.
    if ev.reasoning_trace:
        result['reasoning_trace'] = ev.reasoning_trace

    # ── v2: Disclaimer (legal protection — always present) ──
    result['disclaimer'] = ev.disclaimer
    result['valuation_id'] = ev.valuation_id

    # ── Note: 'verdict' field is INTENTIONALLY OMITTED in v2 ──
    # Thammen describes positions and surfaces facts; the user decides.

    # Full transactions (only in detailed/paid mode)
    if detailed:
        result['transactions'] = []  # TODO: fill from MoJ

    return result


def _round100k(n):
    if n is None:
        return None
    return round(n / 100000) * 100000


# ── Endpoints ──

@app.get("/api/health")
async def health():
    """Health check endpoint — basic status without sensitive details."""
    db_exists = MOJ_DB.exists()
    db_size_mb = round(MOJ_DB.stat().st_size / 1024 / 1024, 1) if db_exists else 0

    # Sprint 2.7: refresh freshness cache on health-check hits so a daily
    # cron pinging /api/health keeps the banner up to date.
    fresh = refresh_freshness()

    return {
        "status": "ok",
        "version": "3.1.0-sprint2.7",
        "engine": "unified" if _UNIFIED_OK else "v2_fallback",
        "moj_db": {
            "available": db_exists,
            "size_mb": db_size_mb,
        },
        "moj_freshness": freshness_for_health(fresh) if fresh else None,
        "modules": {
            "evaluate_property_v2": True,
            "evaluate_unified_v3": _UNIFIED_OK,
        },
        "security": {
            "cors_locked": ALLOWED_ORIGINS != ["*"],
            "rate_limit": RATE_LIMIT,
        },
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/freshness")
async def freshness():
    """Sprint 2.7: public freshness state for the home-page banner.

    Returns banner_ar (sticky banner text), subtitle_ar (hero replacement
    for the legacy 'تُحدَّث أسبوعياً' line), severity (info|warning|alert),
    tier, and days_old. Frontend fetches this on page load.
    """
    fresh = get_freshness()
    if fresh is None:
        # Graceful fallback — frontend hides the banner if banner_ar is empty
        return {
            "banner_ar": "",
            "subtitle_ar": "بيانات وزارة العدل القطرية الرسمية",
            "tier": "unknown",
            "severity": "info",
            "days_old": None,
            "latest_record": None,
        }
    return freshness_for_homepage(fresh)


@app.get("/api/disclaimer")
async def disclaimer():
    """إخلاء المسؤولية الموحَّد لثمّن. يُعرض في الـ frontend بشكل دائم."""
    return {
        "disclaimer_ar": (
            "ثمّن يجمع البيانات السوقية من المصادر الحكومية (وزارة العدل، "
            "وزارة البلدية والبيئة) والإعلانات النشطة (FGRealty، PropertyFinder، "
            "arady، Mzad). هذا تحليل معلوماتي للقرار، وليس تقييماً عقارياً "
            "معتمداً وفق معايير RICS أو IVS. القرار النهائي ومسؤوليته على "
            "العميل. للأغراض الرسمية (قروض بنكية، محاكم، تقارير محاسبية) "
            "يلزم تقييم من مُقيِّم معتمد."
        ),
        "disclaimer_en": (
            "Thammen aggregates market data from government sources (Ministry "
            "of Justice, Ministry of Municipality) and active listings "
            "(FGRealty, PropertyFinder, arady, Mzad). This is informational "
            "analysis to support decisions, NOT a certified property valuation "
            "per RICS or IVS standards. Final decisions and their consequences "
            "rest with the client. For formal purposes (bank loans, courts, "
            "accounting reports), a certified valuer is required."
        ),
        "is_certified_valuer": False,
        "methodology_alignment": {
            "approaches_used": ["market_comparison", "replacement_cost", "income"],
            "transparency_level": "full",
            "comparables_disclosed": True,
            "sources_cited": True,
            "uncertainty_disclosed": True,
        },
    }


@app.get("/api/about")
async def about():
    """معلومات عن النظام والمصادر التي يعتمدها."""
    return {
        "name": "Thammen — ثمّن",
        "version": "2.0.0",
        "tagline_ar": "السوق العقاري بين يديك",
        "tagline_en": "The real estate market in your hands",
        "data_sources": {
            "government": [
                {"name": "وزارة العدل", "url": "https://www.data.gov.qa",
                 "description": "صفقات البيع المُسجّلة (فلل، أرض، مباني)"},
                {"name": "وزارة البلدية والبيئة (MME)",
                 "url": "https://qrep.aqarat.gov.qa",
                 "description": "صفقات الشقق والإيجارات"},
                {"name": "GIS Qatar", "url": "https://gisqatar.org.qa",
                 "description": "الحدود الإدارية، التنظيم، المعالم"},
            ],
            "listings": [
                {"name": "FGRealty", "url": "https://fgrealty.qa"},
                {"name": "PropertyFinder Qatar", "url": "https://www.propertyfinder.qa"},
                {"name": "arady.qa", "url": "https://arady.qa"},
                {"name": "Mzad Qatar", "url": "https://www.mzadqatar.com"},
            ],
        },
        "what_thammen_does": [
            "يجمع البيانات الحكومية الفعلية (الصفقات المُسجَّلة)",
            "يقارنها بإعلانات السوق النشطة",
            "يُظهر الفجوة بين الحقيقة والطموح",
            "يحسب العائد الصافي بتكاليف فعلية (رسوم خدمات، شغور، صيانة)",
            "يعرض كل خطوة منطقية مع مصدرها",
        ],
        "what_thammen_does_not": [
            "لا يُصدر تقييماً عقارياً معتمداً (RICS/IVS)",
            "لا يُقدّم توصيات شرائية أو بيعية",
            "لا يحلّ محل المعاينة الميدانية",
            "لا يصلح كمستند رسمي للبنوك أو المحاكم",
        ],
    }


@app.post("/api/evaluate")
@limiter.limit(RATE_LIMIT)
async def evaluate_quick(req: EvaluateRequest, request: Request):
    """Quick evaluation — address only. Returns free-tier result."""
    log.info(f"evaluate quick: {req.zone}/{req.street}/{req.building} "
             f"from {get_remote_address(request)}")
    try:
        # NEW v3.1: Use unified engine if available
        if _UNIFIED_OK:
            result = evaluate_thammen(
                zone=req.zone,
                street=req.street,
                building=req.building,
                moj_csv_path=str(MOJ_CSV),
                audience=req.audience or 'buyer',
                use_listings=True,
                use_geo_v2=True,
            )
            return _attach_freshness(result)
        # Fallback: v2 engine
        ev = evaluate_property(
            zone=req.zone,
            street=req.street,
            building=req.building,
            moj_csv_path=MOJ_CSV,
            include_age=True,
        )
        return _attach_freshness(_simplify_evaluation(ev, detailed=False))
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"evaluate failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/evaluate/details")
@limiter.limit(RATE_LIMIT)
async def evaluate_with_details(req: EvaluateDetailsRequest, request: Request):
    """Improved evaluation with building details from user."""
    log.info(f"evaluate details: {req.zone}/{req.street}/{req.building} "
             f"floors={req.floors} condition={req.condition} "
             f"basement={req.basement} footprint={req.footprint_m2} "
             f"age={req.building_age_years} luxury={req.is_luxury} "
             f"from {get_remote_address(request)}")
    try:
        # NEW v3.1: Use unified engine if available
        if _UNIFIED_OK:
            result = evaluate_thammen(
                zone=req.zone,
                street=req.street,
                building=req.building,
                moj_csv_path=str(MOJ_CSV),
                audience=req.audience or 'buyer',
                listing_price=req.asking_price,
                rental_income=req.rental_income,
                floors=req.floors,
                condition=req.condition,
                annexes=req.annexes or 0,
                # Sprint 2.2 — building improvements
                basement=req.basement,
                footprint_m2=req.footprint_m2,
                external_majlis=req.external_majlis,
                # Sprint 2.3 — Qatar 10-Year Rule
                building_age_years=req.building_age_years,
                is_luxury=req.is_luxury,
                use_listings=True,
                use_geo_v2=True,
            )
            return _attach_freshness(result)

        # Fallback: v2 engine path (original code)
        # Determine renovation from condition
        has_reno, full_reno = CONDITION_TO_RENOVATION.get(
            req.condition or 'good', (False, False)
        )

        # Estimate building age from imagery
        building_age = None  # will be auto-detected with include_age=True

        # Build BUA breakdown if floors provided
        bua_breakdown = None
        listing_bua = None

        if req.floors:
            # First get plot info to compute footprint
            try:
                from qatar_gis import QatarGIS
                gis = QatarGIS(verbose=False)
                loc = gis.find_property(req.zone, req.street, req.building)
                plot = gis.get_plot(loc['pin'])
                plot_area = plot.pdarea

                # Compute footprint from setbacks
                fp_data = compute_max_footprint(plot.polygon_4326, plot_area)
                main_fp = fp_data['max_footprint_m2'] if fp_data else plot_area * 0.55

                # Try satellite for annex estimation
                sat_fp = None
                try:
                    sat_data = estimate_footprint_from_imagery(plot.polygon_4326)
                    if sat_data and 'footprint_m2' in sat_data:
                        sat_fp = sat_data['footprint_m2']
                except Exception:
                    pass

                # Annex area = satellite footprint - setback footprint
                annex_area = 0
                if req.annexes and req.annexes > 0:
                    if sat_fp and sat_fp > main_fp:
                        annex_area = sat_fp - main_fp
                    else:
                        annex_area = req.annexes * 50  # fallback: 50m² per annex

                bua_breakdown = _build_bua_breakdown(main_fp, req.floors, annex_area)
            except Exception:
                # Fallback: rough estimate
                if req.floors:
                    listing_bua = 500 * req.floors  # very rough

        ev = evaluate_property(
            zone=req.zone,
            street=req.street,
            building=req.building,
            moj_csv_path=MOJ_CSV,
            listing_price=req.asking_price,
            bua_breakdown=bua_breakdown,
            listing_bua_m2=listing_bua,
            has_renovation=has_reno,
            full_renovation=full_reno,
            rental_income=req.rental_income,
            potential_rental=req.potential_rental,
            include_age=True,
        )
        return _attach_freshness(_simplify_evaluation(ev, detailed=False))
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"evaluate/details fallback failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── Static file serving ──
@app.get("/")
async def serve_frontend():
    return FileResponse("index.html")


@app.get("/logo.png")
async def serve_logo():
    return FileResponse("logo.png", media_type="image/png")


# ── Run (for local dev only; production uses `uvicorn api:app` via Procfile) ──
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)