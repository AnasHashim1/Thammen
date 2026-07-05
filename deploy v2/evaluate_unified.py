#!/usr/bin/env python3
"""
evaluate_unified.py — Thammen AVM orchestrator (Sprint 1.b)

Methodology name (RICS-aligned):
    "Sales Comparison-led AVM with Three-Approach Reconciliation"

    Primary value source: Sales Comparison Approach (RICS VPS 3 — Valuation approaches and methods)
        - Bracket comparison when bracket_n >= 20
        - Geographic widening adjustment when bracket_n < 20 (VPS 3)
    Cross-checks (NOT weighted into primary):
        - Cost Approach (sanity check for old buildings)
        - Income Approach (sentiment check for asset class)
    Reconciliation: explicit agreement/divergence indicator

Important departure from Sprint 1.a:
    Sprint 1.a wrongly blended three approaches with equal weights for a
    residential villa. This produced 2.9M for Marikh when truth was ~4.5M.
    Sprint 1.b keeps comparison as primary (correct for residential per
    IVS 103 — Valuation Approaches) and uses cost/income only for reconciliation transparency.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import asdict
from pathlib import Path
from typing import Optional, Dict

# Sprint 2.14.0 — RICS-aligned scope + MUC declaration. These modules are
# fully decoupled from engine logic; safe to import unconditionally.
from scope_of_service import classify_asset_scope, scope_to_dict


# ════════════════════════════════════════════════════════════════════
# Sprint 2.10: single source of truth for engine version.
# Bump this ONE constant when shipping a new Sprint. All response
# paths and /api/health surface the same string — no more drift.
# ════════════════════════════════════════════════════════════════════
ENGINE_VERSION = 'thammen-sprint2p22p0b101-land-usage-purity'
SPRINT_TAG = '2.22.0b.101'          # for /api/health "3.1.0-sprint{SPRINT_TAG}"

# ════════════════════════════════════════════════════════════════════
# Sprint 2.22.0a/2: tier_label TYPE category emission (KICKOFF §4.3 + F1).
#   tier_label = TYPE (analytical / indicative / broker-verified / signed);
#   accuracy_score = STRENGTH within type (independent signal).
# All 2.22.0a value-producing methods emit 'analytical_range' per Anas R2
# decision 2026-05-26. 'indicative_estimate' reserved for 2.22.0b Stage 1
# lite output. Refusal methods return None — refusal_reason carries
# surface in sub-sprint /5.
# ════════════════════════════════════════════════════════════════════
_TIER_LABEL_BY_METHOD = {
    # Value-producing methods → 'analytical_range'
    'comparison_bracket':              'analytical_range',
    'comparison_widened':              'analytical_range',
    'comparison_widened_indicative':   'analytical_range',
    'comparison_thin':                 'analytical_range',
    'comparison_preliminary':          'analytical_range',  # per R4 — n<5 borderline still emits; accuracy_score carries warning
    'hybrid_t2':                       'analytical_range',
    'listing_only_implied_rent':       'analytical_range',
    'income_approach_only':            'analytical_range',
    # Refusal methods → None (refusal_reason in /5 carries the signal)
    'insufficient_data':               None,
    'out_of_scope_v1':                 None,
    'asset_type_reality_stop':         None,
}


def _tier_label_for(method):
    """Map valuation method to public tier_label category (Sprint 2.22.0a/2).

    Returns 'analytical_range' for the 8 known value-producing methods.
    Returns None for refusal methods (insufficient_data, out_of_scope_v1,
    asset_type_reality_stop) — refusal_reason will carry surface in /5.
    Returns None defensively for unknown methods (negative test in
    test_sprint_2p22p0a_tier_labels.py guards against silent drift —
    new methods MUST be added to _TIER_LABEL_BY_METHOD explicitly).

    Per KICKOFF §4.3 + Anas R2/R4/R6 decisions 2026-05-26.
    """
    return _TIER_LABEL_BY_METHOD.get(method)


# ════════════════════════════════════════════════════════════════════
# Sprint 2.22.0a/4: USE_CASE_BANNER constant per BRIEF v3.1 §6.7
# (use-case segmentation table). Single-dimension mapping (use case →
# required stage), NO asset_type / audience / tier axes. Static
# content identical for every non-refusal response.
#
# 3 buckets per Anas Q2 decision 2026-05-26 (deliberate redundancy
# between not_suitable_for and stage5_required_for — same items,
# warning framing vs path-forward framing).
#
# Q1 decision: §6.7 canonical — investment_underwriting in suitable_for
# with caveats. Line 96 paraphrasing artifact flagged for /12.
#
# Q3 decision: Portfolio revaluation (B2B Basel 3.1) OMITTED —
# D-strategy-5 dedicated track outside retail UI.
#
# Q4 decision: bank-aware disclaimer for mortgage pre-qualification
# embedded inline in the suitable_for entry text.
#
# Emission gating happens in output_briefs._use_case_banner_section()
# via _tier_label_for() refusal check — NO per-builder injection in
# evaluate_unified (Rule #39 architecture refinement: avoid dumb
# constant passthrough through engine logic).
# ════════════════════════════════════════════════════════════════════
USE_CASE_BANNER = {
    'suitable_for': [
        'الفضول السوقي / استطلاع الأسعار',
        'التسعير قبل الإعلان (للبائعين)',
        'مرجع للعروض الشرائية',
        'التأهيل المسبق للرهن العقاري (مع تحفظات بنكية)',
        'تحليل الاستثمار (مع تحفظات)',
    ],
    'not_suitable_for': [
        'تمويل الرهن العقاري الرسمي (collateral للتمويل)',
        'النزاعات القضائية / الميراث / الطلاق',
    ],
    'stage5_required_for': [
        'تمويل الرهن العقاري الرسمي — يحتاج تقييم موقّع من مُقيّم معتمد',
        'النزاعات القضائية والميراث — يحتاج تقييم موقّع من مُقيّم معتمد',
    ],
}


# ════════════════════════════════════════════════════════════════════
# Sprint 2.22.0a/5: refusal_reason emission per BRIEF v3.1 §1.6 + §5.3
# precedence chain. 6 active triggers (5 §1.6 methodology-driven + 1
# 2.22.0a engine-capability for out_of_scope_v1 path per Anas Q1 (d)).
# Templates live in refusal_templates.py module.
#
# _compute_refusal_reason() dispatches by §5.3 precedence with defensive
# symmetry to _tier_label_for() — unknown method → silent (None).
# ════════════════════════════════════════════════════════════════════

# Density-gated districts per BRIEF v3.1 §1.7 + Phase 3 audit A5 Pearl
# self-discovery (Anas Q2 (α) decision 2026-05-26). Currently Pearl-only;
# 2.22.0b §1.7 density measurement work will expand the set as more
# zones fail the baseline floors.
_DENSITY_GATED_DISTRICTS = frozenset({'جزيرة اللؤلؤة'})

# E20 threshold (per EMPIRICAL_FINDINGS — MoJ "مجمع فلل" sampling max
# = 15,027 m²). Patch-A (qatar_gis.full_property_lookup) promotes
# compound_small → compound_large at this boundary. At the refusal site,
# asset_type='compound_large' is the post-Patch-A signal; we also accept
# explicit plot_area_m2 ≥ 15K as a stronger guarantee.
_ASSET_SCALE_EXTREME_M2 = 15000

# District regimes registry — empty skeleton in Sprint 2.22.0a per
# KICKOFF §5.4 ("live, not inert" pattern). Lazy-loaded + module cache.
_DISTRICT_REGIMES_CACHE: Optional[dict] = None


def _load_district_regimes() -> dict:
    """Sprint 2.22.0a/5: lazy-load district_regimes.json with module cache.

    Mirrors _RENT_REF_CACHE pattern (line 408-418). On 2.22.0a load, the
    file is `{"events": []}` per KICKOFF §5.4 — regime_shift trigger
    never fires. 2.22.0b operational track populates events; reading is
    fault-tolerant (FileNotFoundError / JSONDecodeError → empty events).
    """
    global _DISTRICT_REGIMES_CACHE
    if _DISTRICT_REGIMES_CACHE is not None:
        return _DISTRICT_REGIMES_CACHE
    try:
        from pathlib import Path
        path = Path(__file__).parent / 'district_regimes.json'
        with open(path, 'r', encoding='utf-8') as f:
            _DISTRICT_REGIMES_CACHE = json.load(f) or {'events': []}
    except Exception as e:
        print(f"[district_regimes] load failed, using empty: {e}", file=sys.stderr)
        _DISTRICT_REGIMES_CACHE = {'events': []}
    return _DISTRICT_REGIMES_CACHE


def _compute_refusal_reason(method, asset_type=None, district_ar=None,
                            district_en=None, plot_area_m2=None, **extra_context):
    """Sprint 2.22.0a/5: §5.3 precedence chain dispatcher.

    Returns refusal_reason dict {trigger_id, message_ar, message_en,
    recommendation_ar, context} per refusal_templates.get_refusal_template(),
    OR None for non-refusal paths.

    THREE None cases (defensive symmetry with _tier_label_for() in /2):
      1. Unknown method (not in _TIER_LABEL_BY_METHOD) → None (silent)
      2. Value-producing method (tier_label is not None) → None (silent —
         use_case_banner + tier_label fire instead)
      3. Refusal method with no precedence-chain match → falls through to
         comp_density_sparse default (§5.3 row 6)

    Precedence chain (§5.3, post-Sprint-2.22.0a.2-Pattern-B renumber):
      1. density_gated_district  — district in _DENSITY_GATED_DISTRICTS
                                    (Pearl in 2.22.0a per Q2 (α))
      2. classifier_failure      — asset_type == 'unknown' AND
                                    method != 'asset_type_reality_stop'
                                    (Sprint 2.22.0a.2 Pattern B — upstream
                                    QARS coverage gap, distinct from
                                    spatial_ambiguity which fires only
                                    after a SUCCESSFUL classification)
      3. spatial_ambiguity       — method == 'asset_type_reality_stop'
      4. asset_scale_extreme     — asset_type=='compound_large' AND
                                    plot_area_m2 >= 15K m² (E20 boundary)
      5. asset_class_out_of_scope — method == 'out_of_scope_v1' (NEW Q1 d)
      6. regime_shift            — district matches event in registry
                                    (always inert in 2.22.0a — empty
                                    registry)
      7. comp_density_sparse     — default fallback for sparse MoJ data

    First-match wins. Engine emits exactly one trigger_id per refusal.

    Context (Q3 (ii) standard fields): asset_type, district_ar are always
    forwarded when provided; plot_area_m2 forwarded for compound paths;
    extra_context forwarded as-is for trigger-specific signals.
    """
    # Defensive: unknown method → silent (mirrors /2 + /4 gating)
    if method not in _TIER_LABEL_BY_METHOD:
        return None
    # Value-producing method → silent (refusal_reason mutually exclusive
    # with tier_label per F5 + §5.3 spec)
    if _TIER_LABEL_BY_METHOD[method] is not None:
        return None

    from refusal_templates import get_refusal_template

    # Standard context kwargs (Q3 (ii)) — caller passes when available
    base_ctx = {}
    if asset_type is not None:
        base_ctx['asset_type'] = asset_type
    if district_ar is not None:
        base_ctx['district_ar'] = district_ar
    if plot_area_m2 is not None:
        base_ctx['plot_area_m2'] = plot_area_m2
    base_ctx.update(extra_context)

    # §5.3 precedence chain:

    # 1. density_gated_district overrides all (Pearl in 2.22.0a)
    if district_ar in _DENSITY_GATED_DISTRICTS:
        return get_refusal_template('density_gated_district', **base_ctx)

    # 2. classifier_failure (Sprint 2.22.0a.2 Pattern B — upstream QARS
    # coverage gap leaves asset_type='unknown'). Pre-empts row 3
    # (spatial_ambiguity stays exclusive to the reality-check stop path)
    # and row 7 (comp_density_sparse stays exclusive to known-asset-type
    # sparse-MoJ cases). The asset_type='unknown' guard is intentional:
    # only fires when the engine could not determine the property type
    # at all — not when reality-check explicitly stops a known type.
    if asset_type == 'unknown' and method != 'asset_type_reality_stop':
        return get_refusal_template('classifier_failure', **base_ctx)

    # 3. spatial_ambiguity (Sprint 2.21.0.7 reality-check path)
    if method == 'asset_type_reality_stop':
        return get_refusal_template('spatial_ambiguity', **base_ctx)

    # 4. asset_scale_extreme (E20 Patch-A boundary)
    if asset_type == 'compound_large' and plot_area_m2 is not None \
            and plot_area_m2 >= _ASSET_SCALE_EXTREME_M2:
        return get_refusal_template('asset_scale_extreme', **base_ctx)

    # 5. asset_class_out_of_scope (per Q1 d — out_of_scope_v1 path)
    if method == 'out_of_scope_v1':
        return get_refusal_template('asset_class_out_of_scope', **base_ctx)

    # 6. regime_shift (registry lookup — always inert in 2.22.0a)
    if district_ar:
        regimes = _load_district_regimes()
        events = regimes.get('events') or []
        for event in events:
            if event.get('district') == district_ar:
                # Inject event_name with leading separator for clean formatting
                event_name = event.get('name', '')
                if event_name and not event_name.startswith(' '):
                    event_name = ' — ' + event_name
                return get_refusal_template(
                    'regime_shift', event_name=event_name, **base_ctx
                )

    # 7. comp_density_sparse (default fallback for any refusal not matched above)
    return get_refusal_template('comp_density_sparse', **base_ctx)


try:
    from evaluate_property import evaluate_property, PropertyEvaluation, BuaBreakdown
    _V2_OK = True
except ImportError as e:
    _V2_OK = False
    print(f"FATAL: evaluate_property not loadable: {e}", file=sys.stderr)

try:
    from evaluate_v3 import evaluate_v3
    _V3_OK = True
except ImportError as e:
    _V3_OK = False
    print(f"Warning: evaluate_v3 not loadable: {e}", file=sys.stderr)

try:
    from geo_reference_v2 import build_reference_geo_v2
    _GEO_OK = True
except ImportError:
    _GEO_OK = False

try:
    from listings_db import fetch_active_listings, weighted_listings_median
    _LISTINGS_OK = True
except ImportError:
    _LISTINGS_OK = False

try:
    from geometric_factors import analyze_geometric_factors
    _GEOMETRIC_OK = True
except ImportError as e:
    _GEOMETRIC_OK = False
    print(f"Warning: geometric_factors not loadable: {e}", file=sys.stderr)

# ── Sprint 2.16.0: Stock Stratification (EMPIRICAL_FINDINGS Rule E4) ──
try:
    from stock_strata import build_stock_strata_result
    _STRATA_OK = True
except ImportError as e:
    _STRATA_OK = False
    print(f"Warning: stock_strata not loadable: {e}", file=sys.stderr)


# ============================================================
# Constants — RICS-aligned for Qatar market
# ============================================================

# Cap rates by asset type (Qatar empirical, RICS Income Approach)
# Source: convergence of FGREALTY data, market norms, and asset class theory
CAP_RATES_BY_ASSET = {
    # Owner-occupied / residential — lower yield because location/lifestyle dominate
    'standalone_villa':   0.040,   # 4.0%
    'villa':              0.040,
    'palace':             0.035,   # luxury — even lower
    # Investment-grade — higher yield required to compensate for management
    'compound_small':     0.060,   # 6.0%
    'compound_large':     0.075,   # 7.5%
    'apartment_building': 0.065,
    'tower':              0.060,
    # Commercial — higher yield (more volatile, depreciation risk)
    'commercial':         0.080,
    'industrial':         0.085,
    # Land — income approach not applicable
    'raw_land':           None,
    'land':               None,
    'agricultural':       None,
}

# Sample size thresholds (RICS Red Book Global Standards, effective 31 January 2025 — VPS 3 reliability tiers; Material Valuation Uncertainty disclosure per VPGA 10 + VPS 6 + IVS 106)
MIN_N_RELIABLE   = 20  # full confidence
MIN_N_INDICATIVE = 10  # use with caveat
MIN_N_BOUND_ONLY = 5   # bounds only

# Operating expense ratio (Qatar typical for residential)
OPEX_RATIO_RESIDENTIAL = 0.23   # maintenance + vacancy + management

# Sprint 2.22.0b.8 (§6 v2): OPEX ratios that MIRROR cap_rate_calibrator.OPEX_RATIO,
# so a CALIBRATED cap rate (built on these) is paired with a matching NOI. The villa
# yield is calibrated net of opex 0.20 (calibrator OPEX_RATIO['villa']=0.20 + villa
# service_charge=0 → exactly 0.20); pairing it with the flat NOI opex 0.23 under-stated
# every villa-calibrated income by 0.77/0.80 = -3.75%. Compound is 0.23 on both sides
# (already consistent). MUST stay in sync with cap_rate_calibrator.OPEX_RATIO.
_CALIB_OPEX_BY_ASSET = {
    'villa': 0.20, 'standalone_villa': 0.20, 'house': 0.20,
    'compound_small': 0.23, 'compound_large': 0.23,
}


# ============================================================
# Sprint 2.19: Calibrated cap-rate lookup (read-only, safe-fail)
# ============================================================
# cap_rates.sqlite is a COMMITTED read-only snapshot (Operational_Rules #43),
# regenerated by run_calibration.py. Any failure here falls back silently to
# the hardcoded CAP_RATES_BY_ASSET above — the engine never depends on it.
# v1 calibrates villa + compound_small only (apartment/tower -> Sprint 2.29 MME,
# land -> Sprint 2.19.1). See cap_rate_calibrator.py.

_CAP_RATES_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             'cap_rates.sqlite')
_CALIBRATABLE_ASSETS = {'villa', 'compound_small'}
_CAP_CALIB_BRACKETS = [(0, 400), (400, 600), (600, 900), (900, 1500), (1500, 10 ** 9)]


def _cap_size_bracket(area_sqm):
    if not area_sqm or area_sqm <= 0:
        return None
    for lo, hi in _CAP_CALIB_BRACKETS:
        if lo <= area_sqm < hi:
            return f"{lo}-{hi}" if hi < 10 ** 9 else "1500+"
    return None


def _cap_area_token(name):
    """Reduce a GIS area name to a comparable token (mirrors calibrator)."""
    s = re.sub(r"\s+", " ", (name or "")).strip()
    s = re.sub(r"[ً-ْ]", "", s)
    s = (s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
          .replace("ى", "ي").replace("ة", "ه"))
    s = re.sub(r"\s*\d+\s*$", "", s)
    if s.startswith("ال"):
        s = s[2:]
    return s.strip()


def _lookup_calibrated_cap_rate(asset_type, area_name, plot_area_m2, stock_class=None):
    """Return (cap_rate, provenance_dict) from cap_rates.sqlite or (None, None).

    Safe-fail by design: a missing DB, schema drift, or any exception yields
    (None, None) so the caller falls back to the hardcoded cap rate.
    """
    import sqlite3
    at = (asset_type or '').lower()
    if at == 'standalone_villa':
        at = 'villa'
    if at not in _CALIBRATABLE_ASSETS:
        return None, None
    bracket = _cap_size_bracket(plot_area_m2)
    if not bracket or not area_name:
        return None, None
    token = _cap_area_token(area_name)
    try:
        if not os.path.exists(_CAP_RATES_DB):
            return None, None
        conn = sqlite3.connect(f"file:{_CAP_RATES_DB}?mode=ro", uri=True)
        try:
            # Sprint §6 v2: pull ALL usable cells for this asset (any bracket) and
            # filter to the subject's AREA in Python, so a subject whose exact plot
            # bracket has no usable cell can BORROW the area's best usable cell from
            # an adjacent bracket. Recon (PHASE0_R7_income_v2_600-900_recon): 600-900
            # villa yield cells are not data-feasible (0/187 usable), yet net yields
            # are bracket-stable WITHIN an area (≪ the cross-area spread), so the
            # area's usable cell is a defensible yield with disclosure + MUC-high.
            rows = conn.execute(
                "SELECT district_aname, stock_class, sample_size, cap_rate, "
                "net_yield, gross_yield, confidence, last_updated, size_bracket "
                "FROM cap_rates WHERE asset_type=? "
                "AND cap_rate IS NOT NULL "
                "AND confidence IN ('reliable','indicative')",
                (at,),
            ).fetchall()
        finally:
            conn.close()
    except Exception:
        return None, None

    area_cells = [r for r in rows if _cap_area_token(r[0]) == token]
    if not area_cells:
        return None, None
    # Prefer the subject's EXACT plot bracket (byte-identical to the pre-v2 path);
    # only borrow when the exact bracket has no usable cell in this area.
    exact_bracket = [r for r in area_cells if r[8] == bracket]
    borrowed = not exact_bracket
    cands = exact_bracket if exact_bracket else area_cells
    if stock_class:
        sc = [r for r in cands if r[1] == stock_class]
        if sc:
            cands = sc
    cands.sort(key=lambda r: r[2], reverse=True)  # highest sample_size wins
    r = cands[0]
    cap_rate = r[3]
    prov = {
        'source': 'calibrated',
        'cap_rate': cap_rate,
        'cap_rate_pct': round(cap_rate * 100, 2),
        'sample_size': r[2],
        'confidence': r[6],
        'last_updated': r[7],
        'district_aname': r[0],
        'stock_class': r[1],
        'size_bracket': r[8],
        'net_yield_pct': round(r[4] * 100, 2) if r[4] is not None else None,
        'gross_yield_pct': round(r[5] * 100, 2) if r[5] is not None else None,
        'method_ar': ('معدل رسملة معايَر من إيجارات السوق ÷ وسيط بيع وزارة العدل '
                      '(Sprint 2.19)'),
    }
    if borrowed:
        prov['bracket_borrowed'] = True
        prov['subject_bracket'] = bracket
        prov['borrowed_from_bracket'] = r[8]
        prov['method_ar'] += (f' — معدل مُستعار من شريحة {r[8]} م² للمنطقة نفسها '
                              f'(شريحة العقار {bracket} م² بلا عيّنة كافية؛ '
                              f'العائد الصافي مستقر عبر شرائح المنطقة الواحدة).')
    return cap_rate, prov


# ============================================================
# Sprint 2.22.0b.71 — Condition-axis adaptable calibration (B-2 infra)
# ============================================================
# condition_adjustments.sqlite is a COMMITTED read-only snapshot (the cap_rates.sqlite
# precedent, Operational_Rules #43), built by condition_calibrator.py. It holds the
# per-grade effective-age PENALTIES the DRC reads. THE MECHANISM (this lookup + the
# _cost_approach_value pricing) NEVER changes; only the NUMBERS in the DB change when
# the GT-2 confirmed-sale corpus reaches n>=20 (the PO's «الرقم يتغيّر لا الكود»).
# Safe-fail by design: a missing DB / schema drift / any exception → (None, None) → the
# caller falls back to the hardcoded COST_CONDITION_PENALTY → byte-identical. At n=1 the
# DB is SEEDED from the V001/TD-93317 ladder (seed == COST_CONDITION_PENALTY, a sync-guard
# test enforces it), so seeding is a value no-op; the numbers are disclosed-INDICATIVE
# (the b16/E25 discipline) until the corpus calibrates them.
_COND_ADJ_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'condition_adjustments.sqlite')


def _lookup_condition_penalty(condition, area_name=None, built_type_stratum=None):
    """Return (penalty_years, provenance_dict) from condition_adjustments.sqlite, or
    (None, None) → caller falls back to the hardcoded COST_CONDITION_PENALTY.

    Future-proof signature: at n=1 only GLOBAL rows (NULL area, NULL stratum) exist, so
    area_name/built_type_stratum are accepted but don't yet matter (the global penalty
    wins). When the corpus emits per-(area, stratum, condition) cells, the SAME code
    PREFERS them — zero code change. Mirrors _lookup_calibrated_cap_rate (read-only,
    confidence-gated, highest sample_size wins, safe-fail)."""
    import sqlite3
    cond = (condition or '').strip().lower()
    if not cond:
        return None, None
    try:
        if not os.path.exists(_COND_ADJ_DB):
            return None, None
        conn = sqlite3.connect(f"file:{_COND_ADJ_DB}?mode=ro", uri=True)
        try:
            rows = conn.execute(
                "SELECT area_match_key, built_type_stratum, condition, penalty_years, "
                "sample_size, confidence, source FROM condition_adjustments "
                "WHERE condition=? AND penalty_years IS NOT NULL "
                "AND confidence IN ('reliable','indicative')",
                (cond,),
            ).fetchall()
        finally:
            conn.close()
    except Exception:
        return None, None
    if not rows:
        return None, None
    token = _cap_area_token(area_name) if area_name else None
    # PREFER (stratum match) then (area match) then global; tie-break highest sample_size.
    # (sorts, never filters → a global row always survives, so n=1 always resolves.)
    def _rank(r):
        stratum_match = 1 if (built_type_stratum and r[1] == built_type_stratum) else 0
        area_match = 1 if (token and r[0] and _cap_area_token(r[0]) == token) else 0
        return (stratum_match, area_match, r[4] or 0)
    best = max(rows, key=_rank)
    pen = best[3]
    if pen is not None and float(pen).is_integer():
        pen = int(pen)               # the integer seed → byte-identical to the hardcoded dict
    prov = {
        'source': best[6], 'penalty_years': pen, 'sample_size': best[4],
        'confidence': best[5], 'built_type_stratum': best[1], 'area_match_key': best[0],
    }
    return pen, prov


# ============================================================
# Sprint A.3: v1 scope and sanity check thresholds
# ============================================================

# v1 supports: villas, lands, palaces, small compounds + DCF fallback for large income assets.
# Politely refuses: commercial / industrial / agricultural (no usable data in MoJ).
V1_IN_SCOPE_FULL = {
    'standalone_villa', 'villa', 'raw_land', 'land',
    'palace', 'compound_small',
}
V1_IN_SCOPE_DCF_ONLY = {
    'compound_large', 'tower', 'apartment_building',
}
V1_OUT_OF_SCOPE = {
    'commercial', 'industrial', 'agricultural',
}

# Yield sanity ranges (RICS-aligned Qatar empirical norms)
# Below 3% net = property way overpriced relative to its rent
# Above 10% net = either underpriced, distressed, or rent is wrong
YIELD_NORMAL_MIN = 0.03   # 3%
YIELD_NORMAL_MAX = 0.10   # 10%
YIELD_FLAG_MIN   = 0.02   # < 2% → "very weak"
YIELD_FLAG_MAX   = 0.12   # > 12% → "implausible, check rent"

# Listing price vs reference gap thresholds (% above/below)
LISTING_GAP_OVERPRICED_WARN = 0.30   # +30% = market ceiling
LISTING_GAP_UNDERPRICED_WARN = -0.30 # -30% = check for issues

# Asset type → MoJ "نوع العقار" categories for sample availability check
# (some categories appear with NBSP \xa0 vs regular space — handled by normalize)
ASSET_TO_MOJ_CATEGORIES = {
    'standalone_villa':  ('فيلا', 'فيلا من طابقين وملحق', 'فيلتان متلاصقتان', 'فيلا واحدة'),
    'villa':             ('فيلا', 'فيلا من طابقين وملحق', 'فيلتان متلاصقتان', 'فيلا واحدة'),
    'raw_land':          ('أرض فضاء', 'ارض فضاء'),
    'land':              ('أرض فضاء', 'ارض فضاء'),
    'palace':            ('قصر',),
    'compound_small':    ('مجمع فلل', 'مجمع فلل وملحقاتها'),
}
MIN_MOJ_SAMPLES_FOR_FULL_PIPELINE = 1  # below this → use fast paths instead
# (only blocks when ZERO direct comparables exist — full pipeline can still
# widen the search to find indirect samples for n>=1 cases)


# ============================================================
# Caches
# ============================================================

_MOJ_CACHE: Dict[str, list] = {}
_RENT_REF_CACHE: Dict[str, dict] = {}

# Sprint 2.22.0a.3 T1.2 (rework): freshness cache for the staleness-
# coupled trend-gate. Parallels api.py's get_freshness() with a
# module-local cache to avoid the api ⇄ engine circular import.
# Safe-fail: any failure (missing CSV, parse error) returns None →
# the staleness gate doesn't fire → engine behaves like pre-T1.2.
# Sentinel False = "previously failed, don't retry every call".
_ENGINE_FRESHNESS_CACHE = None  # None=unknown; False=failed; FreshnessReport=cached


def _get_moj_freshness_tier() -> Optional[str]:
    """Return MoJ data_freshness.tier ('fresh'|'mild'|'stale'|'very_stale')
    or None on any failure. Module-cached after the first successful
    call. Used by the T1.2 staleness-coupled trend-gate at the emission
    site. Self-healing: when the CSV is replaced with fresh data, the
    next process restart re-computes; tier falls back to 'fresh'/'mild'
    automatically and the gate stops suppressing.
    """
    global _ENGINE_FRESHNESS_CACHE
    if _ENGINE_FRESHNESS_CACHE is False:
        return None
    if _ENGINE_FRESHNESS_CACHE is None:
        try:
            from data_freshness import compute_freshness
            csv = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'moj_weekly.csv',
            )
            _ENGINE_FRESHNESS_CACHE = compute_freshness(csv)
        except Exception:
            _ENGINE_FRESHNESS_CACHE = False
            return None
    try:
        return _ENGINE_FRESHNESS_CACHE.tier
    except Exception:
        return None


def _get_moj_rows(csv_path: str) -> list:
    key = str(Path(csv_path).resolve())
    if key in _MOJ_CACHE:
        return _MOJ_CACHE[key]
    import csv
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    _MOJ_CACHE[key] = rows
    return rows


def _count_moj_comparables(csv_path: str, district_ar: Optional[str],
                           asset_type: str) -> int:
    """Sprint A.3+: Fast count of MoJ comparables for this asset+district.

    Used before launching the full pipeline (19+ seconds) to detect cases
    where the pipeline would just produce insufficient_data anyway. If this
    returns 0 or very few samples, route to fast paths instead.

    Returns: count of MoJ transactions matching this asset class in this district.
    """
    import re
    categories = ASSET_TO_MOJ_CATEGORIES.get(asset_type)
    if not categories or not district_ar:
        return 999  # unknown asset or district → don't block full pipeline
    try:
        rows = _get_moj_rows(csv_path)
    except Exception:
        return 999  # CSV missing → defensive, let full pipeline handle it

    def norm(s):
        return re.sub(r'\s+', ' ', s or '').strip()

    district_norm = norm(district_ar)
    cat_set = {norm(c) for c in categories}
    # Match by district + asset category. Match district prefix (e.g., 'الدفنة 61'
    # should match 'الدفنة' rows). Use prefix or exact match.
    count = 0
    for r in rows:
        d = norm(r.get('اسم المنطقة', ''))
        if d != district_norm and not (d.startswith(district_norm + ' ')
                                       or district_norm.startswith(d + ' ')):
            continue
        nt = norm(r.get('نوع العقار', ''))
        if nt in cat_set:
            count += 1
    return count


def _get_rent_ref(json_path: Optional[str]) -> Optional[dict]:
    if not json_path:
        return None
    if json_path in _RENT_REF_CACHE:
        return _RENT_REF_CACHE[json_path]
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        ref = data.get('reference', data) if isinstance(data, dict) else data
        _RENT_REF_CACHE[json_path] = ref
        return ref
    except Exception as e:
        print(f"[rent_ref] load failed: {e}", file=sys.stderr)
        return None


# ============================================================
# Helpers
# ============================================================

def _condition_to_reno(condition: Optional[str]) -> tuple:
    mapping = {
        'new':         (True, True),
        'renovated':   (True, True),
        'excellent':   (True, True),
        'good':        (True, False),
        'maintenance': (False, False),
        'fair':        (False, False),
        'poor':        (False, False),
    }
    return mapping.get(condition or 'good', (False, False))


UPPER_FLOOR_RATIO_v2 = 0.85   # upper floors typically slightly smaller than ground
TYPICAL_COVERAGE = 0.55       # typical Qatari villa ground-floor coverage (R1)
MAX_COVERAGE = 0.80           # municipal max coverage ratio
DEFAULT_ANNEX_M2 = 50         # typical annex BUA
EXTERNAL_MAJLIS_M2 = 80       # typical external majlis BUA


def _typical_footprint(plot_area_m2: Optional[float]) -> float:
    """Estimate typical ground-floor footprint when user doesn't provide one.

    Replaces the legacy hardcoded 300m² assumption. Scales with plot size:
      < 350m² plot   → ~60% coverage (small plots build dense)
      350-800m² plot → ~55% coverage (typical R1 villa)
      > 800m² plot   → ~45% coverage (large plots have more garden)
    """
    if not plot_area_m2 or plot_area_m2 <= 0:
        return 300.0  # safe fallback when plot unknown
    a = float(plot_area_m2)
    if a < 350:
        return round(a * 0.60)
    elif a < 800:
        return round(a * 0.55)
    else:
        return round(a * 0.45)


def _typical_bua_for_plot(plot_area_m2: Optional[float]) -> float:
    """Typical TOTAL BUA for a Qatari villa on this plot size.

    Baseline: ground floor + 1 upper floor (the de-facto norm in Qatar R1
    zones for the past 15+ years). Basement, additional floors, annexes,
    and external majlis are TREATED AS EXTRAS that earn upward adjustment.
    """
    fp = _typical_footprint(plot_area_m2)
    # Ground (fp) + 1 upper floor (fp × 0.85)
    return fp + fp * UPPER_FLOOR_RATIO_v2


# ============================================================
# Sprint 2.22.0b — Zoning-driven ground coverage (QNMP)  [Gate-2 SIGNED]
# ============================================================
# Primary source: Qatar National Master Plan / Ministry of Municipality
# residential MAX ground-coverage ratios (brief §3):
#     R1 (low density)        → 60%
#     R2 (low-medium density) → 50%
#     compound (R1/R2)        → 40%   (Income path — never reaches this villa code)
# These make the footprint cap + the suggested default ZONING-AWARE instead of
# the flat MAX_COVERAGE=0.80 / non-zoning 45-60% default. UNKNOWN zoning falls
# back to the legacy behaviour so nothing regresses where we cannot classify.
ZONE_MAX_COVERAGE = {
    'R1': 0.60, 'R1-TYP': 0.60,
    'R2': 0.50, 'R2-TYP': 0.50,
}
# Suggest a CONSERVATIVE footprint = 80% of the zone ceiling (brief §4): a
# confirmable starting point that does NOT silently fire a substantiality
# premium (it sits at/below the typical baseline) — the user confirms/edits it
# (Gate-2 §5.2, decision B).
SUGGESTED_COVERAGE_FRACTION = 0.80


def _zone_max_coverage(zoning_code: Optional[str], fallback: float = MAX_COVERAGE) -> float:
    """QNMP max ground-coverage ratio for a zoning code (fallback = legacy cap)."""
    if not zoning_code:
        return fallback
    return ZONE_MAX_COVERAGE.get(str(zoning_code).strip().upper(), fallback)


def _suggested_footprint(plot_area_m2: Optional[float],
                         zoning_code: Optional[str]) -> Optional[int]:
    """Conservative, confirmable ground-floor footprint suggestion (brief §4).

    Known R1/R2 → plot × SUGGESTED_COVERAGE_FRACTION × zone_ceiling (~80% of the
    zone's max coverage), but CAPPED at the legacy plot-proportional
    `_typical_footprint` so the ASSUMED default can never SILENTLY INFLATE the
    comparison vs prior behaviour (Gate-2 §5.2-B — "conservative default, no
    auto-premium"; on large plots where 0.8×ceiling > legacy, keep legacy).
    UNKNOWN/other zoning → the legacy default. None when the plot is unknown.
    """
    if not plot_area_m2 or plot_area_m2 <= 0:
        return None
    legacy = int(round(_typical_footprint(plot_area_m2)))
    key = str(zoning_code).strip().upper() if zoning_code else None
    if key and key in ZONE_MAX_COVERAGE:
        zoned = int(round(plot_area_m2 * SUGGESTED_COVERAGE_FRACTION * ZONE_MAX_COVERAGE[key]))
        return min(zoned, legacy)
    return legacy


# ============================================================
# Sprint 2.22.0b.10 — Geometric footprint (DISPLAY/CONFIRM ONLY)  [Gate-2 SIGNED]
# ============================================================
# The MAX-buildable ground footprint computed FROM the plot's actual dimensions
# minus the legal R1 setbacks (Empirical E15, corrected: front 5 / side 3 /
# rear 3), bounded by the zone coverage ceiling. Surfaced for the floors-first
# confirm flow as a CEILING the user corrects DOWN to the actual building
# (brief §4 — the legal max ≠ the built area). Recon `PHASE0_2p22p0b10`:
#   - edge-PAIRING on the 4-vertex ring is exact (shoelace == pdarea); the
#     axis-aligned bbox is WRONG (Qatar rectangles are rotated vs the 2932 grid).
#   - gate on `is_rectangular`; non-rectangular → coverage-cap fallback (graceful).
#   - orientation-free OUTCOME: take the LARGER legal envelope across the two
#     orientations (a ceiling), bounded by the coverage cap → no street detection.
# 🔴 VALUE-INVARIANT (recon D1): the return feeds ONLY the geometry DISPLAY surface;
# it NEVER touches `_suggested_fp` / `_eff_fp` / substantiality / valuation.amount.
SETBACK_FRONT_R1 = 5.0
SETBACK_SIDE_R1 = 3.0
SETBACK_REAR_R1 = 3.0


def _geometry_footprint(polygon_2932, pdarea: Optional[float],
                        is_rectangular: bool,
                        zone_coverage: float = 0.60,
                        shared_effective_area: Optional[float] = None) -> Optional[dict]:
    """Max-buildable ground footprint from plot geometry (Sprint 2.22.0b.10).

    DISPLAY/CONFIRM ONLY — never feeds valuation.amount (brief §6, recon D1).
    Returns {plot_dims_m, max_buildable_footprint_m2, method, n_share?} or None.

    Sprint 2.22.0b.10.2 — multi-QARS shared plot: when `shared_effective_area` is
    given (the per-villa share of a 2+-villa parcel, `effective_per_villa`), ONE
    villa sits on that share, NOT the whole cadastral polygon. The polygon is the
    COMBINED parcel, so the per-villa shape is unknown → use the orientation-free
    coverage cap on the share (no full-plot setback envelope, which would ~double
    a single villa's footprint).
    """
    if not pdarea or pdarea <= 0:
        return None
    if (shared_effective_area and shared_effective_area > 0
            and shared_effective_area < pdarea):
        return {
            'plot_dims_m': None,
            'max_buildable_footprint_m2': int(round(zone_coverage * shared_effective_area)),
            'method': 'coverage_cap_shared',
            'effective_share_m2': int(round(shared_effective_area)),
        }
    cov_cap = zone_coverage * pdarea
    ring = polygon_2932 or []
    # ESRI returns the closing point == first; strip it
    pts = ring[:-1] if (len(ring) > 1 and ring[0] == ring[-1]) else list(ring)
    if is_rectangular and len(pts) == 4:
        # consecutive-vertex edge lengths (rotation-safe; bbox is NOT)
        es = []
        for i in range(4):
            a = pts[i]
            b = pts[(i + 1) % 4]
            es.append(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5)
        s1 = (es[0] + es[2]) / 2.0   # paired opposite edges
        s2 = (es[1] + es[3]) / 2.0
        depth_loss = SETBACK_FRONT_R1 + SETBACK_REAR_R1   # 8 (front + rear)
        width_loss = SETBACK_SIDE_R1 + SETBACK_SIDE_R1    # 6 (side + side)
        # larger legal envelope across the two orientations (a CEILING the user
        # corrects DOWN → take max; no need to know which edge faces the street)
        env = 0.0
        for depth, width in ((s1, s2), (s2, s1)):
            fd = depth - depth_loss
            fw = width - width_loss
            if fd > 0 and fw > 0:
                env = max(env, fd * fw)
        fp = min(cov_cap, env) if env > 0 else cov_cap
        return {
            'plot_dims_m': [round(s1, 1), round(s2, 1)],
            'max_buildable_footprint_m2': int(round(fp)),
            'method': 'setback_envelope',
        }
    # non-rectangular (5+ verts / irregular) → orientation-free coverage cap
    return {
        'plot_dims_m': None,
        'max_buildable_footprint_m2': int(round(cov_cap)),
        'method': 'coverage_cap',
    }


def _extract_zoning_code(ev) -> Optional[str]:
    """Parse the GIS zoning code (R1/R2/...) from an evaluation's factor detail.

    Reuses the already-fetched zoning factor (property_factors `_factor_zoning`)
    — NO extra GIS call. Shared by `_run_geometric` (HBU) and the Sprint 2.22.0b
    substantiality footprint logic so both read one source (DRY).
    """
    try:
        if ev and ev.valuation and ev.valuation.factors_detail:
            for f in ev.valuation.factors_detail:
                if f.get('code') == 'zoning':
                    ev_str = (f.get('evidence', '') or '') + ' ' + (f.get('label_ar', '') or '')
                    for code in ['R1', 'R2', 'R3', 'C1', 'C2', 'C', 'MU']:
                        if code in ev_str:
                            return code
                    break
    except Exception:
        pass
    return None


def _build_smart_bua(
    plot_area_m2: Optional[float],
    floors: Optional[int],
    annexes: Optional[int],
    basement: Optional[bool] = None,
    footprint_m2: Optional[float] = None,
    external_majlis: Optional[bool] = None,
) -> Optional['BuaBreakdown']:
    """Build a BUA breakdown that respects plot size, basement, and add-ons.

    Replaces the legacy _build_simple_bua. Key differences:
    - Footprint scales with plot area (legacy used fixed 300m² regardless)
    - Explicit basement support (legacy always set basement_m2=0)
    - `floors` is ABOVE-GROUND floor count (1=ground only, 2=ground+1st, etc.)
    - User can override footprint via footprint_m2
    - Optional external majlis adds ~80m²

    Returns None if no building info provided at all (caller decides whether
    to fall back to a "typical building" assumption or skip cost approach).
    """
    if not _V2_OK:
        return None

    # If user provided nothing at all about the building, signal that to caller
    any_input = any([
        floors and floors > 0,
        annexes and annexes > 0,
        basement is True,
        footprint_m2 and footprint_m2 > 0,
        external_majlis is True,
    ])
    if not any_input:
        return None

    # Effective above-ground floors (default 1 = ground only)
    above_floors = max(1, int(floors) if floors else 1)

    # Footprint: user-provided override, else plot-proportional default
    if footprint_m2 and footprint_m2 > 0:
        fp = float(footprint_m2)
    else:
        fp = _typical_footprint(plot_area_m2)

    # Cap footprint at plot * MAX_COVERAGE if plot known (sanity)
    if plot_area_m2 and plot_area_m2 > 0:
        fp = min(fp, plot_area_m2 * MAX_COVERAGE)

    upper_count = max(0, above_floors - 1)
    upper_area = round(fp * UPPER_FLOOR_RATIO_v2 * upper_count) if upper_count else 0

    # Basement: only when explicitly indicated, sized at footprint
    bsmt = round(fp) if basement else 0

    n_annexes = int(annexes) if annexes else 0
    annex_area = n_annexes * DEFAULT_ANNEX_M2

    ext_area = EXTERNAL_MAJLIS_M2 if external_majlis else 0

    return BuaBreakdown(
        main_footprint_m2=round(fp),
        basement_m2=bsmt,
        upper_floors_m2=upper_area,
        upper_floor_count=upper_count,
        annexes_m2=annex_area,
        annex_count=n_annexes,
        external_m2=ext_area,
    )


# Backward-compatibility shim — old callers (CLI tests) still use the simple form
def _build_simple_bua(floors: int, annexes: int) -> Optional['BuaBreakdown']:
    """DEPRECATED: kept for CLI backward compatibility. Use _build_smart_bua."""
    return _build_smart_bua(
        plot_area_m2=None, floors=floors, annexes=annexes,
        basement=None, footprint_m2=None, external_majlis=None,
    )


def _building_substantiality(
    bua: Optional['BuaBreakdown'],
    plot_area_m2: Optional[float],
) -> dict:
    """Compute how 'substantial' the building is relative to a typical villa.

    BASELINE = typical Qatari villa: ground + 1 upper floor on the same plot.
    Anything BEYOND this (basement, additional floors, annexes, external
    majlis) is an EXTRA that earns measured upward adjustment.

    Returns:
      {
        'index': float,         # 1.0 = typical, >1.0 = larger, <1.0 = smaller
        'typical_bua': float,   # ground + 1 upper for this plot size
        'actual_bua': float,    # what the user's property has (per inputs)
        'adjustment_pct': float,# sales-comp adjustment in fraction (e.g. 0.15)
        'rationale': str,
      }

    Adjustment tiers (proportional, capped to keep results sane):
      index >= 2.00 → +25% (very substantial: large basement + 3+ floors + annexes)
      index >= 1.70 → +20% (substantial: basement + 2 floors + annexes)
      index >= 1.45 → +15% (notably above typical)
      index >= 1.25 → +10% (moderately above typical)
      index >= 1.10 → +5%  (slightly above typical)
      0.85 - 1.10  → 0%  (typical, no adjustment)
      < 0.85       → -6% (below typical — only applied conservatively)
      < 0.65       → -12%
    Downward adjustments are NOT applied in the unified pipeline (only
    upward) — the substantiality function still reports them so callers
    can choose.
    """
    if not bua or not plot_area_m2 or plot_area_m2 <= 0:
        return {
            'index': 1.0, 'typical_bua': 0, 'actual_bua': 0,
            'adjustment_pct': 0.0, 'rationale': 'building details not provided',
        }

    actual = bua.total_bua
    typical = _typical_bua_for_plot(plot_area_m2)
    if typical <= 0:
        return {'index': 1.0, 'typical_bua': 0, 'actual_bua': actual,
                'adjustment_pct': 0.0, 'rationale': 'cannot compute typical baseline'}

    idx = actual / typical

    # Apply tiered adjustment
    if idx >= 2.00:
        adj, label = 0.25, 'بناء استثنائي (سرداب كبير + طوابق متعددة + ملاحق)'
    elif idx >= 1.70:
        adj, label = 0.20, 'بناء كبير جداً (سرداب + إضافات متعددة)'
    elif idx >= 1.45:
        adj, label = 0.15, 'بناء أكبر من النموذجي بشكل واضح'
    elif idx >= 1.25:
        adj, label = 0.10, 'بناء أكبر من النموذجي'
    elif idx >= 1.10:
        adj, label = 0.05, 'بناء أكبر قليلاً من النموذجي'
    elif idx > 0.85:
        adj, label = 0.0, 'بناء ضمن النطاق النموذجي'
    elif idx > 0.65:
        adj, label = -0.06, 'بناء أصغر من النموذجي'
    else:
        adj, label = -0.12, 'بناء صغير جداً'

    return {
        'index': round(idx, 2),
        'typical_bua': round(typical),
        'actual_bua': round(actual),
        'adjustment_pct': adj,
        'rationale': label,
    }


# ============================================================
# Sprint 2.3 — Qatar 10-Year Rule (age-aware adjustment)
# ============================================================
#
# Empirical market observation: in the Qatari residential market, a villa
# older than ~10 years typically trades close to bare-land value. The
# building's structural presence adds little premium because buyers prefer
# to demolish and rebuild rather than renovate older layouts/MEP.
#
# Exception: luxury construction (high-end finishing + recent full
# renovation + desirable area) may retain 15-25% building value.
#
# This module modulates Sprint 2.2's BUA substantiality adjustment based
# on building age and luxury status, so we don't add +20% to a building
# that the market would value at land + 5%.

def _age_aware_substantiality_multiplier(
    age_years: Optional[int],
    is_luxury: Optional[bool],
) -> tuple:
    """Return (multiplier, regime_label_ar) for substantiality adjustment.

    multiplier:
      1.0  → apply Sprint 2.2 adjustment in full (new building)
      0.85 → apply with mild dampening (5-10 years)
      0.50 → apply at half (≥10 years AND luxury)
      0.0  → suppress entirely (Qatar 10-Year Rule: ≥10 years, non-luxury)
      None → age unknown — keep current behavior but flag MU

    regime_label_ar describes the regime applied (for UI disclosure).
    """
    if age_years is None:
        return 1.0, 'unknown_age'

    a = int(age_years)
    if a < 5:
        return 1.0, 'new_building'
    if a < 10:
        return 0.85, 'mid_age_building'
    # a >= 10
    if is_luxury:
        return 0.50, 'old_luxury_building'
    return 0.0, 'qatar_10_year_rule'


def _ten_year_rule_disclosure_ar(age_years: int, n: Optional[int]) -> str:
    """Generate the user-facing disclosure when 10-Year Rule activates."""
    # Sprint 2.22.0a.2 §9 precision: "صفقة مماثلة" overclaims similarity;
    # we actually match by area + bracket + district. Reframed to honest.
    n_part = (
        f' بناءً على {n} صفقة قريبة في النوع والمساحة من نفس المنطقة '
        f'في وزارة العدل.' if n else '.'
    )
    return (
        f'هذا العقار يزيد عمره عن 10 سنوات (تقديرياً {age_years} سنة). '
        'في السوق القطري، المباني من هذا العمر تتداول عادةً قرب قيمة الأرض '
        'لأن المشترين يفضّلون الهدم وإعادة البناء على ترميم التصاميم القديمة '
        'وأنظمة الكهرباء والسباكة والتكييف. التقييم أعلاه يعكس هذا السلوك '
        f'السوقي ولا يضيف علاوة لكثافة البناء{n_part} '
        'إذا كان العقار يحتوي على تشطيب فاخر فعلي، اختر "بناء فاخر" وأعد التقييم — '
        'يُسعَّر التشطيب عندها عبر فرق كلفة الإحلال (مُعامل البناء)، '
        'لا بتبديل وسيط المقارنة.'
    )


def _luxury_old_disclosure_ar(age_years: int) -> str:
    """Disclosure when old building flagged as luxury — partial adjustment."""
    return (
        f'العقار قديم ({age_years} سنة) لكنك أشرت إلى تشطيب فاخر. '
        'في السوق القطري، الفلل القديمة الفاخرة تحتفظ بـ 15-25% من قيمة بنائها '
        'فقط عند توفر: تشطيب راقٍ + ترميم كامل خلال 3-5 سنوات + موقع مميز. '
        'تم تطبيق نصف التعديل المعتاد لكثافة البناء.'
    )


def _r100k(n):
    if n is None:
        return None
    return round(n / 100000) * 100000


# ============================================================
# Geo widening (the primary RICS adjustment when bracket is thin)
# ============================================================

def _run_geo_v2(ev, moj_csv_path: str, pin=None):
    lat = lon = None
    try:
        from qatar_gis import QatarGIS
        gis = QatarGIS(verbose=False)
        if pin:
            # Sprint 2.21.0: land/PIN entry has no QARS address — resolve lat/lon
            # from the Cadastre polygon centroid so geo widening (and the
            # comparable grid) work for bare-land PINs.
            _plot = gis.get_plot(pin)
            _ring = (_plot.polygon_4326 or []) if _plot else []
            if _ring:
                lon = sum(p[0] for p in _ring) / len(_ring)
                lat = sum(p[1] for p in _ring) / len(_ring)
        else:
            parts = ev.address.split('/')
            loc = gis.find_property(int(parts[0]), int(parts[1]), int(parts[2]))
            if loc:
                lat = loc.lat
                lon = loc.lon
    except Exception:
        return None
    if not lat or not lon:
        return None

    asset_to_cat = {
        'standalone_villa': 'villa', 'villa': 'villa',
        'palace': 'palace',
        'raw_land': 'land', 'land': 'land',
        'compound_small': 'compound', 'compound_large': 'compound',
    }
    cat = asset_to_cat.get(ev.asset_type, 'villa')

    # Note: signal.SIGALRM was used here but breaks in worker threads.
    # Timeout is now enforced by the outer ThreadPoolExecutor in evaluate_thammen.
    try:
        rows = _get_moj_rows(moj_csv_path)
        return build_reference_geo_v2(
            rows=rows, lat=lat, lon=lon,
            category=cat,
            plot_area_m2=ev.plot_area_m2,
            target_zoning=None,
        )
    except Exception as e:
        print(f"[geo_v2] failed: {e}", file=sys.stderr)
        return None


# ============================================================
# Sprint 2.22.0a.9 (facet a) — age/quality elasticity for the widened headline
# ============================================================
# The widened (geo_value) comparison paths take their headline from
# geo_reference_v2.build_reference_geo_v2, which already owns the LOCATION
# dimension (inter-district price normalization, geo_reference_v2.py:447).
# They never multiply by the bracket path's property-factor adjustment, so the
# widened headline had ZERO age/quality elasticity (Marikh 54/541/6: identical
# 4.5M at building_age 0 / 20 / 45 — the operator-reported symptom).
#
# Fork 1 (signed): apply ONLY the age/quality slice — building_age + plot_shape —
# to the widened headline. Location factors (zoning, commercial_street,
# main_road, landmark, permitted_height) are deliberately EXCLUDED: geo_v2
# already inter-district-normalizes them, so re-layering would double-count.
# corner/HBU are not in this adjustment at all (separate geometric_factors.py).
# Fork 2 (signed): clamp to property_factors.MAX_ADJUSTMENT (±0.10); the
# age/quality slice natural range is ≈[-6%, +3%] so the clamp ~never binds.
# Fork 3 (signed): comparison_widened + comparison_widened_indicative ONLY.
# Bracket / thin / preliminary use bracket_value (= fair_price_total, already
# the FULL adj) and are untouched.

_AGE_QUALITY_FACTOR_CODES = frozenset({'building_age', 'plot_shape'})


def _age_quality_adj(valuation, exclude_user_age=False) -> float:
    """Age/quality-only slice of the property-factor adjustment (Sprint
    2.22.0a.9 facet a). Summed from valuation.factors_detail (a list of dicts
    keyed 'code'/'weight'), clamped to ±MAX_ADJUSTMENT. Returns 0.0 when no
    factor detail is available (factors did not run) so the caller no-ops and
    the widened headline stays byte-identical to the pre-sprint output.
    Sprint 2.22.0b.18 (§A1 — AGE BASIS): when the building age came from the USER
    (age_source=='user'), the 'building_age' slice is EXCLUDED — a user-claimed age
    never moves a headline (it renders as the age-sensitivity disclosure instead);
    system-documented ages (gis_imagery) keep the a9 elasticity. VALUER-VALIDATED
    basis: TD-93317 leads on the CGIS-documented age (PHASE0_b18 §2)."""
    detail = getattr(valuation, 'factors_detail', None) if valuation else None
    if not detail:
        return 0.0
    _codes = (_AGE_QUALITY_FACTOR_CODES - {'building_age'}) if exclude_user_age \
        else _AGE_QUALITY_FACTOR_CODES
    raw = sum(
        (f.get('weight') or 0.0)
        for f in detail
        if f.get('code') in _codes
    )
    try:
        from property_factors import MAX_ADJUSTMENT as _CAP
    except Exception:
        _CAP = 0.10
    return round(max(-_CAP, min(_CAP, raw)), 4)


# ============================================================
# Primary value selection (Sales Comparison Approach)
# ============================================================

def _keystone_comparables(rows, n, window_used, cap=8, basis='matched_bracket', pool_n=None):
    """Sprint 2.22.0b.38 (DEF-UX1) / b39 (DEF-UX1.1) — build the keystone-comparables DISPLAY
    block from the MoJ transactions behind the displayed median. ANONYMOUS by construction: the
    source rows carry NO PIN / address / coordinates (E12 — the PN-hash is stripped from the
    export) → only date / size / total / ppm². DISPLAY-ONLY / value-invariant. Returns None when
    there are no usable rows; never raises into the caller.

    basis:
      'matched_bracket' (b38) — the subject SIZE-bracket rows that PRODUCED the median (market led
                                via the matched bracket). Rows pre-sorted desc by build_reference.
      'geo_widened'     (b39) — the subject's PRIMARY-area raw transactions WITHIN the geo-widened
                                pool (market led via geo_full/widened). The full pool also includes
                                location-adjusted NEIGHBOUR rows → the panel shows only the real,
                                unadjusted same-area subset + discloses the widening (the frontend
                                never claims «these decided your number» for geo). `pool_n` = the
                                full pool size for the disclosure. Geo rows key ppm² as `price_m2`.
    """
    if not rows or not isinstance(rows, (list, tuple)):
        return None
    # newest-first (the bracket path is pre-sorted; the geo pool is row-order) — idempotent on sorted input
    try:
        rows = sorted(rows, key=lambda r: (r.get('date') or '') if isinstance(r, dict) else '', reverse=True)
    except Exception:
        pass
    out = []
    for r in rows[:cap]:
        if not isinstance(r, dict):
            continue
        tot = r.get('total_price')
        area = r.get('area_m2')
        if not (tot and area):
            continue
        ppm2 = r.get('price_per_m2') or r.get('price_m2')   # bracket key vs geo key
        out.append({
            'date': (r.get('date') or '')[:10],
            'area_m2': round(area),
            'total_price': round(tot),
            'price_per_m2': round(ppm2) if ppm2 else None,
        })
    if not out:
        return None
    return {
        'basis': basis,
        'n': n,
        'pool_n': pool_n,              # b39: full geo-pool size (primary + neighbours) for the geo disclosure
        'shown': len(out),
        'window_label': window_used,   # a14 «{n36} معاملة، منها {n24} خلال 24 شهراً» when 36mo count, else None
        'rows': out,
        'source_ar': 'بيانات وزارة العدل القطرية (CC BY 4.0) — مجموعة عامّة بلا عنوان أو ترقيم فرديّ',
        'source_en': 'Qatar Ministry of Justice data (CC BY 4.0) — public aggregate, no address or per-record id',
    }


def _keystone_neighbours(accepted_areas, cap=8):
    """Sprint 2.22.0b.41 (DEF-UX1.1b) — the location-adjusted NEIGHBOUR rows of the
    geo-widened pool, the b39 sibling. On a GEO-LED villa the headline median pools the
    subject's PRIMARY-area rows (b39, weight 1.0) PLUS accepted-neighbour rows that are
    location-adjusted into the subject's area; b39 surfaced only the primary subset +
    disclosed the pool size. b41 surfaces the neighbour rows themselves, each tagged with
    its source-area NAME + the location-adjustment multiplier.

    DISPLAY-ONLY / VALUE-INVARIANT by construction: the per-row adjusted ppm² is DERIVED
    here (raw price_m2 × location_adjustment), never re-running any median — the engine's
    own `all_adjusted_prices` (geo_reference_v2 Step 5) is a throwaway local discarded
    after the weighted median, and is NOT read here. E12-safe: a row carries the source
    AREA NAME (a public GIS aggregate label) + a ratio only — never PIN / address / coords.
    Shows BOTH the raw sale ppm² AND the location-adjusted ppm² (never implies the neighbour
    sold for the adjusted figure — both are rates, ر.ق/م²). Returns None when there are no
    usable neighbour rows; never raises into the caller.
    """
    if not accepted_areas or not isinstance(accepted_areas, (list, tuple)):
        return None
    flat = []
    areas_n = 0
    for area in accepted_areas:
        if not isinstance(area, dict):
            continue
        src = area.get('name')
        adj = area.get('location_adjustment')
        txns = area.get('transactions')
        if not (src and adj and isinstance(txns, (list, tuple)) and txns):
            continue
        areas_n += 1
        for t in txns:
            if not isinstance(t, dict):
                continue
            tot = t.get('total_price')
            ar = t.get('area_m2')
            ppm = t.get('price_m2')              # geo row keys ppm² as price_m2
            if not (tot and ar):
                continue
            _ppm_disp = round(ppm) if ppm else None
            _adj_disp = round(adj, 4)            # match the engine's stored location_adjustment precision
            # adjusted = round(DISPLAYED raw × DISPLAYED factor) → the panel's arithmetic is
            # self-consistent (a reader can verify raw × ×factor = adjusted; b14 display-coherence).
            # Purely illustrative of the location adjustment — never feeds the value → value-invariant.
            flat.append({
                'date': (t.get('date') or '')[:10],
                'area_m2': round(ar),
                'total_price': round(tot),
                'price_per_m2_raw': _ppm_disp,
                'price_per_m2_adjusted': (round(_ppm_disp * _adj_disp) if _ppm_disp is not None else None),
                'source_area': src,
                'adjustment_factor': _adj_disp,
            })
    if not flat:
        return None
    try:
        flat = sorted(flat, key=lambda r: r.get('date') or '', reverse=True)   # newest-first
    except Exception:
        pass
    out = flat[:cap]
    return {
        'areas_n': areas_n,        # number of accepted neighbour areas with rows
        'total_n': len(flat),      # total neighbour transactions across those areas
        'shown': len(out),
        'rows': out,
    }


def _select_primary_comparison(ev, geo_v2, user_age=False) -> Optional[dict]:
    """
    Choose the primary comparison value following RICS VPS 3.

    Priority:
        1. Bracket median if bracket_n >= 20 (most specific, most reliable)
        2. Geographic widening if it adds substantial samples (RICS VPS 3)
        3. Bracket median with low-confidence caveat
    """
    bracket_n = (ev.valuation.bracket_n or 0) if ev.valuation else 0
    bracket_value = None
    if ev.valuation:
        bracket_value = ev.valuation.fair_price_total or ev.valuation.moj_median_total

    geo_n = (geo_v2.get('total_n') or 0) if geo_v2 else 0
    geo_value = geo_v2.get('estimated_value') if geo_v2 else None

    # Sprint 2.22.0a.9 facet (a): age/quality-only elasticity for the widened
    # (geo_value) headline. geo_v2 owns LOCATION (inter-district normalization),
    # so only building_age + plot_shape enter here (Fork 1), clamped ±0.10
    # (Fork 2). When no factor detail exists, aq=0 → values untouched
    # (byte-stable). Applied to Cases 2 & 3 only — the geo_value paths; bracket /
    # thin / preliminary use bracket_value and are unaffected (Fork 3).
    geo_low = geo_v2.get('range_low') if geo_v2 else None
    geo_high = geo_v2.get('range_high') if geo_v2 else None
    if geo_value:
        _aq = _age_quality_adj(ev.valuation, exclude_user_age=user_age)
        if _aq:
            geo_value = round(geo_value * (1 + _aq), -3)
            geo_low = round(geo_low * (1 + _aq), -3) if geo_low else geo_low
            geo_high = round(geo_high * (1 + _aq), -3) if geo_high else geo_high

    # Case 1: Bracket has strong sample
    if bracket_n >= MIN_N_RELIABLE and bracket_value:
        # Sprint 2.22.0a.14 (vi): when bracket_n is a 36mo (credibility) count, disclose the window
        # on the headline (b) + carry the 36mo ppm² dispersion for the bracket honest-range gate (a).
        _bwin = getattr(ev.valuation, 'bracket_window_used', None) if ev.valuation else None
        _bdisp = getattr(ev.valuation, 'bracket_ppm2_dispersion', None) if ev.valuation else None
        _win_sfx = ' (نافذة 36 شهراً)' if _bwin else ''
        return {
            'value': bracket_value,
            'low':   ev.valuation.estimated_value_low,
            'high':  ev.valuation.estimated_value_high,
            'method': 'comparison_bracket',
            'method_label_ar': 'مقارنة شريحية مباشرة (‎RICS VPS 3 / IVS 103‎)',
            'n': bracket_n,
            'source_ar': f'وسيط {bracket_n} معاملة في نفس الشريحة والمنطقة{_win_sfx}',
            'window_used': _bwin,        # (vi)(b) recent/total split → Methodology brief
            'ppm2_dispersion': _bdisp,   # (vi)(a) 36mo ppm² dispersion → _stage1_dispersion_gate
            # Sprint 2.22.0b.38 (DEF-UX1): the subject-bracket rows that produced this median.
            # Stashed on `primary`; SURFACED only when the market leads via this bracket (gated in
            # the b4-region — leader=='market' AND method=='comparison_bracket'). Anonymous (E12).
            'comparables': getattr(ev.valuation, 'bracket_transactions', None),
        }

    # Case 2: Bracket weak but widening succeeded
    if geo_n >= MIN_N_RELIABLE and geo_value and geo_n >= max(bracket_n * 3, 15):
        return {
            'value': geo_value,
            'low':   geo_low,
            'high':  geo_high,
            'method': 'comparison_widened',
            'method_label_ar': 'منهج المقارنة بالمبيعات (مجموعة موسَّعة جغرافياً) (‎RICS VPS 3 / IVS 103‎)',
            'n': geo_n,
            'source_ar': f'وسيط {geo_n} معاملة بعد توسيع للمناطق المجاورة مع تسوية موقع',
            # Sprint 2.22.0b.39 (DEF-UX1.1): the subject's PRIMARY-area raw transactions within the
            # geo-widened pool (real, unadjusted, same-area). Surfaced only when the market leads via
            # this widened path (gated in the b4-region). Anonymous (E12). The frontend discloses that
            # the full pool ALSO included location-adjusted neighbour rows (never overclaims).
            'comparables': (geo_v2.get('primary') or {}).get('transactions') if isinstance(geo_v2, dict) else None,
        }

    # Case 3: Use widening even if not as large (when bracket is too thin)
    if geo_n >= MIN_N_INDICATIVE and geo_value and bracket_n < MIN_N_INDICATIVE:
        return {
            'value': geo_value,
            'low':   geo_low,
            'high':  geo_high,
            'method': 'comparison_widened_indicative',
            # Sprint 2.22.0a.2 C3: relabel "إرشادي" -> "شواهد محدودة"
            'method_label_ar': 'منهج المقارنة بالمبيعات (مجموعة موسَّعة جغرافياً) — شواهد محدودة (‎RICS VPS 3 / IVS 103‎)',
            'n': geo_n,
            'source_ar': f'وسيط {geo_n} معاملة بعد توسيع — شواهد محدودة بسبب عينة صغيرة',
            # Sprint 2.22.0b.39 (DEF-UX1.1): same as Case 2 — the primary-area raw rows of the
            # geo-widened pool (anonymous; surfaced gated on market-led in the b4-region).
            'comparables': (geo_v2.get('primary') or {}).get('transactions') if isinstance(geo_v2, dict) else None,
        }

    # Case 4: Fallback — bracket only with low-confidence flag
    if bracket_value and bracket_n >= MIN_N_BOUND_ONLY:
        return {
            'value': bracket_value,
            'low':   ev.valuation.estimated_value_low,
            'high':  ev.valuation.estimated_value_high,
            'method': 'comparison_thin',
            'method_label_ar': f'مقارنة شريحية ضعيفة (n={bracket_n})',
            'n': bracket_n,
            'source_ar': f'عينة ضعيفة جداً (n={bracket_n}) — اعتبر هذا تقديراً مبدئياً',
        }

    # Case 5 (Sprint 2.4a): Preliminary estimate from very thin bracket (n=3-4).
    # MIN_N_BOUND_ONLY is 5; below that we historically returned None and
    # the user saw "insufficient_data" with no headline number. But the
    # brief downstream still computed values from cost approach / blended,
    # creating a confidence mismatch ("we don't know" + "negotiate at 3M").
    # When 3-4 transactions exist AND they yield a reasonable median, it's
    # better to surface this with a strong caveat than to hide it entirely.
    if bracket_value and bracket_n >= 3:
        return {
            'value': bracket_value,
            'low':   ev.valuation.estimated_value_low if ev.valuation else round(bracket_value * 0.80),
            'high':  ev.valuation.estimated_value_high if ev.valuation else round(bracket_value * 1.20),
            'method': 'comparison_preliminary',
            'method_label_ar': f'تقدير مبدئي (n={bracket_n})',
            'n': bracket_n,
            'source_ar': (
                f'عينة محدودة جداً (n={bracket_n} صفقات في 24 شهراً). '
                f'هذا تقدير مبدئي قابل للتعديل عند توفر بيانات إضافية.'
            ),
        }

    return None


# ============================================================
# Cross-check approaches (not weighted into primary)
# ============================================================

# ============================================================
# Sprint 2.6 — Land vs Building Value Separation (Phase 1)
# ============================================================
#
# RICS Red Book methodology distinguishes between land value and building
# (improvements) value. MoJ villa sales record TOTAL price only, but MoJ
# ALSO records pure-LAND sales when villas are demolished or empty plots
# are sold. We use the area's land-only median to estimate land value,
# then derive implied building value as residual.
#
# This empirically validates the Qatar 10-Year Rule: for old non-luxury
# villas, the implied building value is typically <10% of total —
# confirming that buyers price almost entirely off land.

def _decompose_value(
    valuation_amount: Optional[float],
    plot_area_m2: Optional[float],
    bua_m2: Optional[float],
    moj_ref_dict: Optional[dict],
) -> Optional[dict]:
    """Return a value-decomposition block: land + implied building.

    Inputs:
      valuation_amount: the final headline value (post-substantiality)
      plot_area_m2:     subject plot area
      bua_m2:           subject built-up area (for per-m² building stats)
      moj_ref_dict:     MoJ reference with .categories.land structure

    Output schema (returned dict):
      land:
        per_m2_qar, n_transactions, window_months, reliable, source_ar,
        estimated_qar, plot_area_m2
      building_implied:
        qar, qar_per_m2_bua, as_pct_of_total, interpretation_ar
      consistency:
        residual_pct, status ('plausible' | 'land_exceeds_value' | 'building_dominant')

    Returns None when land data is unavailable.
    """
    if not valuation_amount or not plot_area_m2 or plot_area_m2 <= 0:
        return None
    if not moj_ref_dict:
        return None

    # Extract MoJ land-only median (already done in evaluate_property but we
    # re-extract here so the output is self-contained and decoupled).
    categories = (moj_ref_dict or {}).get('categories') or {}
    land_data = categories.get('land') or {}
    price_per_m2_data = land_data.get('price_per_m2') or {}
    land_per_m2 = price_per_m2_data.get('median')
    land_n = land_data.get('n', 0)
    land_window = land_data.get('window_months', 24)
    land_reliable = land_data.get('reliable', False)

    if not land_per_m2 or land_per_m2 <= 0:
        return None
    if land_n < 3:
        # Too thin to be useful; refuse to decompose rather than mislead
        return None

    # Compute land value for this property
    land_value = round(plot_area_m2 * land_per_m2)

    # ─── Sprint 2.18.1.1 — Patch C: defensive sanity guard ────────────────
    # Refuse the decomposition when the per-m² × full-area land value
    # exceeds the MoJ-comparison total. Three cases this catches:
    #  1. Compound misroute (the trigger bug, 51/835/17): extent area too
    #     large for the MoJ-comparable bracket. Primarily handled by
    #     Patch A in qatar_gis.full_property_lookup (promotes
    #     compound_small → compound_large when extent ≥ 15K m², which
    #     makes ASSET_TYPE_TO_MOJ_CATEGORY[…]=None → valuation_amount=None
    #     → this function returns at line 806 before reaching here). Patch
    #     C is belt-and-suspenders for any edge case Patch A doesn't catch.
    #  2. Premium-land teardown candidates: a small old villa (200 m²) on
    #     Pearl/Lusail premium land (≥ 5K QAR/m²) → land 1.0M+ while
    #     as-built valuation may be 900K (Sprint 2.16.10-era Lusail B201
    #     dynamics).
    #  3. MoJ sample outliers that pull the bracket median below the true
    #     land value (rare but possible on small brackets, n<10).
    #
    # Returning None suppresses the value_decomposition entirely in the API
    # response (caller at line 3194: `if decomp: output[...] = decomp`).
    # Frontend at index.html:862 `if(hasValuation && v.value_decomposition)`
    # then naturally skips the broken tile.
    # Bug discovered 2026-05-23 evening: 51/835/17 → land=218M vs total=6.8M
    # (32.1× silent failure). Universal guard (NOT compound-specific) per
    # Anas's Sprint 2.18.1.1 scope decision #4: "Patch C must catch all
    # asset_types, not just compounds".
    if land_value > valuation_amount:
        return None

    # Implied building value (residual)
    bld_implied = round(valuation_amount - land_value)
    bld_per_m2 = round(bld_implied / bua_m2) if (bua_m2 and bua_m2 > 0) else None
    bld_pct = bld_implied / valuation_amount if valuation_amount > 0 else 0

    # Confidence label for land
    # Sprint 2.22.0a.2 C3: relabel tier badges to شواهد taxonomy
    # (Anas-locked شواهد override of CC's original تغطية draft).
    # Codes (reliable/indicative/thin) unchanged for back-compat.
    if land_n >= 20:
        land_conf = 'reliable'
        land_conf_ar = 'شواهد كافية'
    elif land_n >= 10:
        land_conf = 'indicative'
        land_conf_ar = 'شواهد محدودة'
    else:
        land_conf = 'thin'
        land_conf_ar = 'شواهد غير كافية'
    # Sprint 2.22.0b.84 — EN twin of the land confidence label (dormant pick() fallback)
    land_conf_en = {'reliable': 'Sufficient evidence', 'indicative': 'Limited evidence',
                    'thin': 'Insufficient evidence'}.get(land_conf, land_conf_ar)

    # Status & interpretation
    if bld_implied < 0:
        status = 'land_exceeds_value'
        interp = (
            'القيمة المُقدَّرة أقل من قيمة الأرض المنفصلة. هذا غير معتاد ويعني '
            'إما أن المبنى ينتقص من القيمة (هدم مطلوب)، أو أن العينة السوقية '
            'تحت قيمة الأرض الفعلية. يلزم مراجعة من مُقيِّم معتمد.'
        )
    elif bld_pct < 0.05:
        status = 'land_dominant'
        # Sprint 2.22.0a.3 T1.4: reframe from named "10-Year Rule" to
        # observational pattern. We haven't published "the rule" — this is
        # an observed regularity in the Qatar market, not a codified rule.
        # Sprint 2.22.0a.3 post-validation fold (Rule #54): GPT
        # flagged the prior "architectural burden" framing as
        # provocative (owners/developers/valuers) and Gemini as
        # implying universality. Reframed to a TENDENCY — leaves room
        # for exceptions and avoids the restated-rule register.
        interp = (
            f'البناء يساهم بنسبة ضئيلة جداً ({bld_pct*100:.1f}%) من قيمة العقار. '
            f'غالباً ما تتراجع مساهمة البناء في القيمة مع تقادم العقار '
            f'السكني دون تجديد، فتصبح الأرض المكوّن الأكبر في التسعير.'
        )
    elif bld_pct < 0.15:
        status = 'building_modest'
        interp = (
            f'البناء يساهم بنسبة محدودة ({bld_pct*100:.1f}%) من القيمة — '
            f'يتسق مع بناء قديم أو متهالك. القيمة الرئيسية في الأرض.'
        )
    elif bld_pct < 0.35:
        status = 'normal'
        # Sprint 2.22.0a.3 T1.1: drop "بحالة جيدة" — we have no condition
        # ground truth (no field inspection, no user-supplied condition).
        # The phrase was a fabricated fact dressed as interpretation. Keep
        # the numeric narration; let the user infer condition from other
        # signals (age, BUA breakdown if supplied).
        interp = (
            f'البناء يساهم بنسبة {bld_pct*100:.1f}% من القيمة — مساهمة '
            f'ضمن النطاق النموذجي لمبنى على هذه الأرض.'
        )
    else:
        status = 'building_dominant'
        interp = (
            f'البناء يساهم بنسبة عالية ({bld_pct*100:.1f}%) من القيمة — '
            f'يتسق مع بناء جديد أو فاخر أو ذو BUA كبيرة.'
        )

    # Sprint 2.22.0b.84 — EN twin of `interp` (keyed on status; dormant pick() fallback)
    _bp = bld_pct * 100
    if status == 'land_exceeds_value':
        interp_en = (
            'The estimated value is below the standalone land value. This is unusual — '
            'either the building detracts from value (demolition warranted) or the market '
            'sample is below the true land value. A licensed-valuer review is required.'
        )
    elif status == 'land_dominant':
        interp_en = (
            f'The building contributes a very small share ({_bp:.1f}%) of the property value. '
            f"A residential building's contribution to value tends to decline as the property "
            f'ages without renovation, so the land becomes the largest pricing component.'
        )
    elif status == 'building_modest':
        interp_en = (
            f'The building contributes a limited share ({_bp:.1f}%) of the value — '
            f'consistent with an old or worn building. The main value is in the land.'
        )
    elif status == 'normal':
        interp_en = (
            f'The building contributes {_bp:.1f}% of the value — a contribution within the '
            f'typical range for a building on this plot.'
        )
    else:
        interp_en = (
            f'The building contributes a high share ({_bp:.1f}%) of the value — '
            f'consistent with a new, luxury, or large-BUA building.'
        )

    return {
        'land': {
            'per_m2_qar': round(land_per_m2),
            'n_transactions': land_n,
            'window_months': land_window,
            'confidence': land_conf,
            'confidence_ar': land_conf_ar,
            'confidence_en': land_conf_en,
            'reliable': land_reliable,
            'estimated_qar': land_value,
            'plot_area_m2': round(plot_area_m2),
            'source_ar': (
                f'وسيط معاملات بيع الأراضي في نفس المنطقة '
                f'(n={land_n} صفقة، نافذة {land_window} شهراً)'
            ),
        },
        'building_implied': {
            'qar': bld_implied,
            'qar_per_m2_bua': bld_per_m2,
            'bua_m2': round(bua_m2) if bua_m2 else None,
            'as_pct_of_total': round(bld_pct * 100, 1),
            'interpretation_ar': interp,
            'interpretation_en': interp_en,
            'status': status,
        },
        'methodology_note_ar': (
            'يفصل ثمّن قيمة الأرض (من معاملات بيع أراضٍ نقية في نفس المنطقة) '
            'عن قيمة البناء الضمنية (الفرق بين القيمة الكلية وقيمة الأرض). '
            'هذا الفصل يكشف للمستخدم نسبة مساهمة كل عنصر — حسب RICS Red Book.'
        ),
        'methodology_note_en': (
            'Thammen separates the land value (from clean land-sale transactions in the '
            'same area) from the implied building value (the difference between the total '
            "value and the land value). This separation shows each component's contribution "
            'share — per the RICS Red Book.'
        ),
    }


def _reconcile_decomposition_narrative(output):
    """Sprint 2.22.0b.14 (ISS-A07) — report-voice reconciliation. VALUE-INVARIANT:
    rewrites ONLY the implied-building narrative TEXT (never amount/range/method/floor/
    %/strata-numbers) so the value-decomposition AGREES with the 10-Year / stratum panel.

    The implied-building residual (central − land) INHERITS any R7 over-anchor; on an OLD
    villa in a premium-dominated pool with NO user luxury/new/renovated signal the high
    building share is a POOL artifact, not real building value — say so (Case A) and
    cross-reference the 10-Year panel. Selection per BRIEF §2 (A / B / C).

    Post-pass: runs AFTER stock_strata (:5593) + property_basis (:5510) are attached —
    they are NOT available inside _decompose_value (called earlier at :4493). Wrapped in
    try/except: must NEVER break the response.
    """
    try:
        vd = (output.get('valuation') or {}).get('value_decomposition')
        if not vd:
            return
        bi = vd.get('building_implied') or {}
        if bi.get('status') != 'building_dominant':
            return  # only the building-dominant (>=35%) branch can over-state
        asset = (output.get('asset_type') or '').lower()
        if asset not in ('standalone_villa', 'house', 'villa'):
            return  # villa/house only (strata / raw_land out of scope)

        pct = bi.get('as_pct_of_total')
        dom = ((output.get('stock_strata') or {}).get('dominant_stratum') or {})
        dom_name = dom.get('name')
        dom_label = dom.get('label_ar') or 'الفئة الغالبة'
        dom_share = dom.get('share_pct')
        age_est = ((output.get('property_basis') or {}).get('building_age_estimate') or {})
        age_floor = age_est.get('age_floor_years')
        vintage_capped = (age_est.get('age_basis') == 'vintage_capped')
        ui = ((output.get('valuation') or {}).get('user_inputs') or {})
        cond = (ui.get('condition') or '').lower()
        user_premium = bool(ui.get('is_luxury')) or cond in ('new', 'renovated', 'luxury', 'excellent')

        old = (age_floor is not None and age_floor > 10) or vintage_capped
        genuinely_new = (age_floor is not None and age_floor < 5 and not vintage_capped)
        premium_pool = dom_name in ('luxury_new', 'modern_stock')

        if user_premium or genuinely_new:
            bi['narrative_case'] = 'B'
            return  # Case B — genuinely new/luxury → keep the existing «بناء جديد أو فاخر» line

        if old and premium_pool:
            # Case A — old subject, premium-dominated pool: the residual is the pool's
            # over-anchor, not real building value; agree with the 10-Year panel.
            share_txt = (f'{dom_share}% من العيّنة' if dom_share is not None else 'الفئة الغالبة')
            bi['interpretation_ar'] = (
                f'النسبة المرتفعة للبناء الضمني ({pct}%) تعكس وسيط منطقةٍ تهيمن عليه '
                f'فئة «{dom_label}» ({share_txt}) — لا قيمةَ بناءٍ فعليّة لعقارٍ بهذا العمر؛ '
                f'يتّسق هذا مع قاعدة الـ10 سنوات أدناه. إن كان عقارك بتشطيب فاخر فعليّ، '
                f'اختر «بناء فاخر» — يُسعَّر التشطيب عبر فرق كلفة الإحلال، '
                f'لا بتبديل وسيط المقارنة.'
            )
            # Sprint 2.22.0b.84 — EN twin (keeps AR/EN consistent after the reconcile overwrite)
            _dom_label_en = dom.get('label_en') or dom_label
            _share_txt_en = (f'{dom_share}% of the sample' if dom_share is not None else 'the dominant category')
            bi['interpretation_en'] = (
                f'The high implied-building share ({pct}%) reflects an area median dominated by '
                f'the «{_dom_label_en}» category ({_share_txt_en}) — there is no real building '
                f'value for a property of this age; this is consistent with the 10-year pattern '
                f'below. If your property genuinely has a luxury finish, choose «luxury build» — '
                f'the finish is priced through the replacement-cost difference, not by switching '
                f'the comparison median.'
            )
            bi['narrative_case'] = 'A'
            # reverse cross-line: ride the dominant-stratum note (the 10-Year panel surface)
            _base = dom.get('note_ar') or ''
            _xref = ('— وهذا ما يرفع نسبة «البناء الضمني» في تفصيل القيمة أعلاه: '
                     'سمة سوقٍ لهذه الفئة، لا قيمة بناءٍ فعليّة لعقارٍ قديم.')
            if _xref not in _base:
                dom['note_ar'] = (_base + ' ' + _xref).strip()
        else:
            # Case C — neutral/middle: honest upper-bound framing.
            bi['interpretation_ar'] = (
                'البناء الضمني محسوب كفرقٍ عن قيمة الأرض — وهو حدّ أعلى استدلاليّ '
                'لا قياس مباشر لقيمة البناء.'
            )
            bi['interpretation_en'] = (  # Sprint 2.22.0b.84 — EN twin
                'The implied building is computed as a difference from the land value — an '
                'indicative upper bound, not a direct measurement of building value.'
            )
            bi['narrative_case'] = 'C'
    except Exception:
        return  # never break the response


# ════════════════════════════════════════════════════════════════════
# Sprint 2.22.0a.21 (B-1) — land-floor / HBU decomposition surface
#   PRESENTATION ONLY — VALUE-INVARIANT (D4). Surfaces, next to the a17/a19
#   condition caveat, the land-value FLOOR + implied-building decomposition
#   for villa/house comparison outputs, so an old-stock buyer sees the
#   land-anchored downside the comp median hides (V001 Maamoura). The land
#   floor is an ANALYTICAL DECOMPOSITION within Sales Comparison
#   (VPS 3 / IVS 103), grounded in Highest-and-Best-Use (VPS 2 / IVS 102) —
#   NEVER a standalone "land market value".
#   F1 (Phase-0 §5): _decompose_value SUPPRESSES the whole block when
#   land >= value (Patch C, anti-negative-building). B-1 recomputes the land
#   floor INDEPENDENTLY from the SAME moj_reference land category so it still
#   surfaces for the land-priced cohort (~10% of valued villa cells, 0% of
#   reliable) — WITHOUT touching the Patch-C guard or any amount.
#   Copy = multi-AI (#54) LOCKED (GPT-5 + Gemini convergent), verbatim.
#   AR numbers are LRM-wrapped (U+200E) per Operational_Rules #25 (bidi).
# ════════════════════════════════════════════════════════════════════
# Sprint 2.22.0a.22 (B-1.1): multi-AI-validated framing tweaks (value-invariant; citations UNCHANGED).
# land floor → "indicative land component" on an HBU PREMISE (not a determination); implied building →
# "contribution / mathematical allocation" (not a "value"). See MULTI_AI_VALIDATION_BATCH_SprintB1.md.
LAND_FLOOR_NOTE_AR = (
    'تفكيك تحليلي ضمن نموذج المقارنة — مكوّن الأرض الاسترشادي: ~‎{x}‎ ر.ق '
    '(من صفقات أراضٍ مماثلة، على أساس افتراض الاستخدام الأمثل؛ وليس تقييماً مستقلاً للأرض).'
)
LAND_FLOOR_NOTE_EN = (
    'Analytical decomposition within the comparison model — indicative land component: ~{x} QAR '
    '(from comparable land sales, on a highest-and-best-use premise; '
    'not a standalone valuation of the land).'
)
IMPLIED_BLDG_NOTE_AR = (
    'مساهمة البناء الضمنية (ناتج حسابي متبقٍّ: التقدير ناقص الأرض): ~‎{y}‎ ر.ق — '
    'تخصيص حسابي، غير مُتحقَّق ميدانياً (نوع البناء والعمر والحالة غير معروفة).'
)
IMPLIED_BLDG_NOTE_EN = (
    'Implied building contribution (computational residual: estimate minus land): ~{y} QAR — '
    'a mathematical allocation, not field-verified (built type, age and condition unknown).'
)
LAND_ANCHORED_NOTE_AR = (
    'يشير النموذج إلى أن القيمة المقارنة لا تتجاوز قيمة الأرض المجردة؛ '
    'القيمة الضمنية للمبنى ≈ صفر (قد يُعتبر عقاراً للتطوير).'
)
LAND_ANCHORED_NOTE_EN = (
    'The model indicates the comparison value does not exceed bare land value; '
    'implied building value ≈ 0 (may be considered a development property).'
)
_VALUE_FLOOR_CITATION_AR = (
    'منهج المقارنة بالمبيعات (‎VPS 3‎ / ‎IVS 103‎)؛ '
    'قيمة الأرض تعكس الاستخدام الأمثل (‎VPS 2‎ / ‎IVS 102‎)'
)
_VALUE_FLOOR_CITATION_EN = (
    'Sales Comparison approach (VPS 3 / IVS 103); '
    'land value reflects Highest-and-Best-Use (VPS 2 / IVS 102)'
)


def _r10k(n):
    """Round to nearest 10,000 for human-readable ~display copy. Structured
    fields stay exact; only the {x}/{y} substituted into the notes are softened."""
    try:
        return int(round(float(n) / 10000.0) * 10000)
    except Exception:
        return n


def _villa_value_floor(amount, plot_area_m2, moj_ref_dict, existing_decomp):
    """Sprint 2.22.0a.21 (B-1) — villa-scoped land-floor / HBU decomposition block.

    PRESENTATION ONLY: never alters `amount`, never touches _decompose_value's Patch-C
    guard. Prefers the already-computed value_decomposition.land (F2); else recomputes
    land_ppm² × plot from the SAME moj_reference land category (F1) so the floor surfaces
    even when _decompose_value suppressed the block (land ≥ value — the land-priced cohort).
    Returns the value_floor dict, or None when no land basis is available.

    land_anchored: floor ≥ amount → implied building clamped to 0 (NEVER negative); the
    land-anchored disclosure replaces an implied-building number.
    """
    try:
        if not amount or not plot_area_m2 or plot_area_m2 <= 0:
            return None
        land = (existing_decomp or {}).get('land') if isinstance(existing_decomp, dict) else None
        if land and land.get('estimated_qar'):
            # F2 — reuse the already-surfaced floor (land < value case)
            land_floor = land.get('estimated_qar')
            lpm = land.get('per_m2_qar')
            ln = land.get('n_transactions')
            win = land.get('window_months')
            rel = land.get('reliable', False)
        else:
            # F1 — recompute INDEPENDENT of Patch C (land ≥ value case); same moj_ref land category
            cats = (moj_ref_dict or {}).get('categories') or {}
            ld = cats.get('land') or {}
            lpm = (ld.get('price_per_m2') or {}).get('median')
            ln = ld.get('n', 0)
            win = ld.get('window_months', 24)
            rel = ld.get('reliable', False)
            if not lpm or lpm <= 0 or ln < 3:
                return None
            land_floor = round(plot_area_m2 * lpm)
        implied_building = max(round(amount - land_floor), 0)
        land_anchored = land_floor >= amount
        _x = f'{_r10k(land_floor):,}'
        _y = f'{_r10k(implied_building):,}'
        block = {
            'land_floor': land_floor,
            'land_per_m2_qar': (round(lpm) if lpm else None),
            'land_n_transactions': ln,
            'window_months': win,
            'reliable': bool(rel),
            'implied_building_value': implied_building,
            'land_anchored': land_anchored,
            'citation_ar': _VALUE_FLOOR_CITATION_AR,
            'citation_en': _VALUE_FLOOR_CITATION_EN,
            'land_floor_note_ar': LAND_FLOOR_NOTE_AR.format(x=_x),
            'land_floor_note_en': LAND_FLOOR_NOTE_EN.format(x=_x),
            'implied_building_note_ar': IMPLIED_BLDG_NOTE_AR.format(y=_y),
            'implied_building_note_en': IMPLIED_BLDG_NOTE_EN.format(y=_y),
        }
        if land_anchored:
            block['land_anchored_note_ar'] = LAND_ANCHORED_NOTE_AR
            block['land_anchored_note_en'] = LAND_ANCHORED_NOTE_EN
        return block
    except Exception:
        return None


def _inject_value_floor_into_brief(brief, vf):
    """Surface the value_floor block in the brief's Material-Uncertainty section
    (buyer + valuer — whichever audience this brief is), per the a20 pattern. Best-effort."""
    try:
        if not brief or not isinstance(brief, dict) or not vf:
            return
        for sec in (brief.get('sections') or []):
            if isinstance(sec, dict) and sec.get('id') == 'material_uncertainty':
                c = sec.get('content')
                if isinstance(c, dict):
                    c['value_floor'] = vf
                break
    except Exception:
        pass


def _build_cost_crosscheck(ev) -> Optional[dict]:
    rc = getattr(ev, 'replacement_cost', None)
    if not rc:
        return None
    # Sprint 2.4a: field name mapping fix. The dataclass uses
    # `depreciation_pct` and `depreciated_building_value`; the output
    # was looking for `depreciation_rate_pct` and `building_value_depreciated`
    # → silent miss → fields always None. Use the real names with the legacy
    # names as fallback in case other code does set them.
    dep_pct_val = getattr(rc, 'depreciation_pct', None)
    if dep_pct_val is None:
        dep_pct_val = getattr(rc, 'depreciation_rate_pct', None)
    bld_dep_val = getattr(rc, 'depreciated_building_value', None)
    if bld_dep_val is None:
        bld_dep_val = getattr(rc, 'building_value_depreciated', None)
    bld_new_val = getattr(rc, 'construction_cost_new', None)
    if bld_new_val is None:
        bld_new_val = getattr(rc, 'building_value_new', None)
    return {
        'value': rc.total_replacement_value,
        'land_value': getattr(rc, 'land_value', None),
        'building_value_new': bld_new_val,
        'building_value_depreciated': bld_dep_val,
        'building_age_years': getattr(rc, 'building_age_years', None),
        'depreciation_rate_pct': dep_pct_val,
        'bua_m2': getattr(rc, 'bua_m2', None),
        'tier': getattr(rc, 'construction_tier', None),
        'method_label_ar': 'منهج التكلفة الإحلالية (RICS Cost Approach)',
        'role_ar': 'تأكيد منهجي — لا تدخل في القيمة النهائية لعقار سكني',
    }


def _build_income_crosscheck(rental_income, v3_rent_data, asset_type, primary_value,
                             area_name=None, plot_area_m2=None, stock_class=None) -> Optional[dict]:
    """
    Build income approach using:
      1. User's actual rent (priority)
      2. rent_reference median as fallback
    Cap rate: calibrated (Sprint 2.19) when available, else hardcoded by asset type.
    """
    cap_rate = CAP_RATES_BY_ASSET.get((asset_type or '').lower())
    if not cap_rate:
        return None  # not applicable (land, etc.)

    # Sprint 2.19: prefer an empirically calibrated cap rate when present.
    calib_rate, cap_provenance = _lookup_calibrated_cap_rate(
        asset_type, area_name, plot_area_m2, stock_class)
    if calib_rate:
        cap_rate = calib_rate
    else:
        at_norm = (asset_type or '').lower()
        # Sprint 2.19.1 (Fix #3): the villa hardcoded rate is 4.0% BY DESIGN, not a
        # bug and not a 10-Year-Rule land switch. Owner-occupied villas trade at low
        # yields because location/lifestyle dominate price over rent; the income
        # approach for a villa is a methodological cross-check that does not drive
        # the final value. Spell that out so the user does not read 4% as an error.
        if at_norm in ('villa', 'standalone_villa'):
            reason_ar = (
                'الفيلات السكنية سكن مالكي، عائدها الإيجاري منخفض لأن الموقع ونمط '
                'الحياة يغلبان على الإيجار في تسعيرها — لذا يُستخدم معدل رسملة '
                'افتراضي منخفض (4%). منهج الدخل هنا للتأكيد فقط، ولا يدخل في القيمة '
                'النهائية لعقار سكني.'
            )
        else:
            reason_ar = 'لا يوجد معدل معايَر مطابق لهذه المنطقة/الشريحة — معدل نموذجي'
        cap_provenance = {
            'source': 'hardcoded',
            'cap_rate': cap_rate,
            'cap_rate_pct': round(cap_rate * 100, 2),
            'confidence': 'fallback',
            'asset_type': at_norm,
            'reason_ar': reason_ar,
        }

    annual_rent = None
    rent_source = None
    rent_caveats = []

    if rental_income and rental_income > 0:
        annual_rent = rental_income * 12
        rent_source = 'actual_provided'
        rent_source_ar = 'إفادة العميل (الإيجار الفعلي)'
    elif v3_rent_data and v3_rent_data.get('annual_median'):
        annual_rent = v3_rent_data['annual_median']
        rent_source = 'rent_reference_municipality'
        rent_source_ar = f"وسيط البلدية (n={v3_rent_data.get('n')})"
        rent_caveats.append(
            'الإيجار من وسيط البلدية — قد يختلف للمنطقة الفرعية بـ ±30%'
        )
    else:
        return None

    # Sprint 2.22.0b.8 (§6 v2): pair the NOI opex with the opex the cap rate was
    # calibrated on — ONLY when the rate is calibrated (a hardcoded/fallback rate's
    # implied opex is unknown → keep 0.23, byte-identical). Fixes the villa-calibrated
    # -3.75% under-statement (income_led headline + the displayed income cross-check).
    opex_ratio = OPEX_RATIO_RESIDENTIAL
    if cap_provenance.get('source') == 'calibrated':
        opex_ratio = _CALIB_OPEX_BY_ASSET.get((asset_type or '').lower(),
                                              OPEX_RATIO_RESIDENTIAL)
    noi = annual_rent * (1 - opex_ratio)
    # Sprint 2.22.0b.66 (DEBUG T0-4): DEFENSIVE /0 guard. The live cap_rates.sqlite
    # audit confirms every usable (reliable/indicative) cell has cap_rate>0 (the 82
    # zero/NULL rows are all confidence='fallback' and never reach a usable lookup),
    # so this is not live-reachable today — it hardens the path against a future
    # bad row / hand-set rate. None flows gracefully (the income cross-check shows
    # no value; _income_triangulation gates on income.get('value') truthiness).
    income_value = (noi / cap_rate) if (cap_rate and cap_rate > 0) else None

    # Yields (descriptive)
    gross_yield = annual_rent / primary_value if primary_value else None
    net_yield   = noi / primary_value if primary_value else None

    yield_flag = None
    if net_yield is not None:
        if net_yield < 0.025:
            yield_flag = 'العائد الصافي منخفض جداً (<2.5%) — السوق سكني نقي، لا استثماري'
        elif net_yield > 0.07:
            yield_flag = 'العائد الصافي مرتفع (>7%) — مؤشر استثماري قوي'

    return {
        'value': round(income_value) if income_value else None,
        'annual_rent': annual_rent,
        'monthly_rent': round(annual_rent / 12),
        'rent_source': rent_source,
        'rent_source_ar': rent_source_ar,
        'opex_ratio': opex_ratio,
        'noi': round(noi),
        'cap_rate': cap_rate,
        'cap_rate_label_ar': (
            f'معدل رسملة معايَر {cap_rate*100:.1f}% '
            f'(عينة n={cap_provenance.get("sample_size")}، {cap_provenance.get("confidence")})'
            if cap_provenance.get('source') == 'calibrated'
            else f'معدل رسملة {cap_rate*100:.1f}% (نموذجي لـ {asset_type})'
        ),
        'cap_rate_provenance': cap_provenance,
        'gross_yield': round(gross_yield, 4) if gross_yield else None,
        'net_yield':   round(net_yield, 4) if net_yield else None,
        'yield_flag_ar': yield_flag,
        'caveats': rent_caveats,
        'method_label_ar': 'منهج الدخل (RICS Income Approach)',
        'role_ar': 'تأكيد منهجي — لا تدخل في القيمة النهائية لعقار سكني',
    }


# ============================================================
# Reconciliation
# ============================================================

def _rewrite_brief_anchored_sections(
    brief: dict,
    final_amount: float,
    final_low: float,
    final_high: float,
    audience: str,
    moj_direct: Optional[float] = None,
    stock_strata: Optional[dict] = None,    # Sprint 2.16.2: stratum-aware anchor
) -> None:
    """Sprint 2.4a: Mutate `brief` in place to rewrite audience-specific anchor
    sections so they use the FINAL valuation amount instead of the stale
    blended/synthesis value from output_briefs.

    Sections rewritten:
      - buyer 'negotiation'  → floor/opening/ceiling derived from final_amount
      - seller 'valuation'   → estimated_value / range_low / range_high
      - seller 'pricing'     → aggressive/realistic/quick_sale / market_ceiling
    Other sections (flags, due_diligence, trend, market_context, etc.)
    are left untouched.
    """
    if not brief or not brief.get('sections'):
        return

    final_amount = float(final_amount)
    final_low = float(final_low)
    final_high = float(final_high)

    # Sprint 2.22.0a.2 C5 DELETE: the 'negotiation' section is no longer
    # built in output_briefs.compose_buyer_brief, so the upstream
    # _negotiation_anchor + stratum-aware-negotiation post-processor
    # block that lived here is now dead. Removed both. The Sprint 2.16.2
    # stratum-aware logic remains alive elsewhere (stock_strata module
    # still emits the strata block — only its consumption by the
    # negotiation section is gone).

    for sec in brief['sections']:
        sid = sec.get('id')

        # Seller's "your property value" section
        if sid == 'valuation' and audience == 'seller':
            content = sec.get('content') or {}
            content['estimated_value'] = _r100k(final_amount)
            content['range_low']  = _r100k(final_low)
            content['range_high'] = _r100k(final_high)
            sec['content'] = content

        # Seller pricing strategy
        elif sid == 'pricing' and audience == 'seller':
            content = sec.get('content') or {}
            content['realistic_price']   = _r100k(final_amount * 1.05)
            content['aggressive_price']  = _r100k(final_amount * 1.10)
            content['quick_sale_price']  = _r100k(final_amount * 0.95)
            content['market_ceiling']    = _r100k(final_amount * 1.20)
            sec['content'] = content

        # Sprint 2.4b: trend section — convert slope from decimal to percentage.
        # The v2 baseline stores slope_annual_pct as raw decimal (e.g. -0.0207
        # meaning -2.07%/year). UI displays it as a percent and was showing
        # -0.02% by mistake. Normalize here so consumers always get percent.
        elif sid == 'trend':
            content = sec.get('content') or {}
            sa = content.get('slope_annual_pct')
            if sa is not None and -1.0 < sa < 1.0 and sa != 0:
                content['slope_annual_pct'] = round(sa * 100, 2)
            lvp = content.get('latest_vs_peak_pct')
            if lvp is not None and -1.0 < lvp < 1.0 and lvp != 0:
                content['latest_vs_peak_pct'] = round(lvp * 100, 2)
            sec['content'] = content


def _normalize_audience(audience: Optional[str]) -> str:
    """Normalize audience aliases to canonical names.

    Canonical names: 'buyer', 'seller', 'investor', 'valuer'.
    Accepted aliases:
      buyer:    buyer, مشتري
      seller:   seller, بائع
      investor: investor, مستثمر
      valuer:   valuer, valuator, مثمن, مقيم, مقيّم, مثمّن
    Unknown values fall back to 'buyer' (preserves legacy behavior).
    """
    if not audience:
        return 'buyer'
    a = str(audience).strip().lower()
    valuer_aliases = {'valuer', 'valuator', 'مثمن', 'مثمّن', 'مقيم', 'مقيّم', 'مُقيِّم', 'مُثمِّن'}
    if a in valuer_aliases or audience in valuer_aliases:
        return 'valuer'
    if a in ('buyer', 'مشتري'):
        return 'buyer'
    if a in ('seller', 'بائع'):
        return 'seller'
    if a in ('investor', 'مستثمر'):
        return 'investor'
    return 'buyer'  # safe default


def _build_investor_sections(income, v3_rent, primary):
    """Build the 4 investor-specific brief sections from corrected income data.

    Sources used (all consistent with the primary valuation):
      - `income`: corrected income cross-check (cap_rate matches asset type)
      - `v3_rent`: rent reference (n, monthly_median, confidence) — if available
      - `primary`: comparison-led valuation (used for sensitivity baseline)
    """
    sections = []

    # ── Section 1: تحليل العائد ──
    sections.append({
        'id': 'yield',
        'title_ar': 'تحليل العائد',
        'content': {
            'gross_yield_pct': round((income.get('gross_yield') or 0) * 100, 2),
            'net_yield_pct': round((income.get('net_yield') or 0) * 100, 2),
            'noi_annual': income.get('noi'),
            'annual_rent_gross': income.get('annual_rent'),
            'cap_rate_pct': round((income.get('cap_rate') or 0) * 100, 2),
            'cap_rate_label_ar': income.get('cap_rate_label_ar'),
            'rent_source_ar': income.get('rent_source_ar'),
        },
    })

    # ── Section 2: القيمة بمنهج الدخل ──
    sections.append({
        'id': 'income_value',
        'title_ar': 'القيمة بمنهج الدخل',
        'content': {
            # income.value is what _build_income_crosscheck stores (line 358);
            # income_value is the same field name used in api.py output
            'income_value': income.get('value') or income.get('income_value'),
            'cap_rate_used': income.get('cap_rate'),
            'noi': income.get('noi'),
            'role_ar': income.get('role_ar'),
            'method_label_ar': income.get('method_label_ar'),
        },
    })

    # ── Section 3: تحليل الحساسية ──
    # Cap rate ±0.5%, ±1% sensitivity on the income value
    noi = income.get('noi') or 0
    base_cap = income.get('cap_rate') or 0
    if noi > 0 and base_cap > 0:
        sensitivity = []
        for delta_pct in (-1.0, -0.5, 0, 0.5, 1.0):
            cap = base_cap + (delta_pct / 100.0)
            if cap > 0:
                sensitivity.append({
                    'cap_rate_pct': round(cap * 100, 2),
                    'income_value': round(noi / cap, -3),
                    'delta_label_ar': (
                        'الأساس' if delta_pct == 0
                        else f'{"+" if delta_pct > 0 else ""}{delta_pct}%'
                    ),
                })
        sections.append({
            'id': 'sensitivity',
            'title_ar': 'تحليل الحساسية — معدّل الرسملة',
            'content': {
                'base_cap_rate_pct': round(base_cap * 100, 2),
                'base_noi': noi,
                'scenarios': sensitivity,
                'note_ar': 'حساسية القيمة لتغير معدّل الرسملة ±1% — لأن المعدل يبقى تقديرياً.',
            },
        })

    # ── Section 4: مرجع الإيجار ──
    if v3_rent:
        sections.append({
            'id': 'rent_reference',
            'title_ar': 'مرجع الإيجار',
            'content': {
                'monthly_median': v3_rent.get('monthly_median'),
                'annual_low': v3_rent.get('annual_low'),
                'annual_high': v3_rent.get('annual_high'),
                'n': v3_rent.get('n'),
                'confidence': v3_rent.get('confidence'),
                'source_ar': v3_rent.get('source_ar', 'qrep.aqarat.gov.qa'),
                'caveats_ar': v3_rent.get('caveats', []),
            },
        })

    return sections


# Sprint 2.4b: Default cap rates per asset type for fallback yield estimation
# when no rental data is available. These align with the Qatar market norms
# used in _build_income_crosscheck.
_DEFAULT_CAP_RATES = {
    'standalone_villa': 0.04,    # 4.0% — residential villa
    'palace': 0.035,             # 3.5% — palace/luxury
    'compound_small': 0.06,      # 6.0%
    'compound_large': 0.075,     # 7.5%
    'apartment_building': 0.065, # 6.5%
}


def _build_investor_sections_fallback(asset_type, primary, plot_area_m2, v3_rent):
    """Sprint 2.4b: When `income` cross-check is None (no user rent, no
    rent_reference for area), still produce a meaningful investor brief.

    Strategy:
      - Estimate annual rent from typical Qatar yield band for the asset type
      - Show the value-implied rent the property would need to be a 4-7% asset
      - Sensitivity scenarios using cap rate ±1%
      - Explicit caveat about no actual rent data
    """
    sections = []
    if not primary or not primary.get('value'):
        return sections

    val = primary['value']
    cap_rate = _DEFAULT_CAP_RATES.get(asset_type, 0.04)

    # If v3_rent exists with at least a median, use that as the rent estimate
    estimated_monthly = None
    if v3_rent and v3_rent.get('monthly_median'):
        estimated_monthly = v3_rent['monthly_median']
        rent_source = (
            f"وسيط الإيجار للمنطقة (n={v3_rent.get('n', '?')}, "
            f"ثقة={v3_rent.get('confidence', '?')})"
        )
    else:
        # Estimate from cap rate × value
        annual_implied = val * cap_rate / (1 - 0.23)  # add back OPEX to get gross
        estimated_monthly = round(annual_implied / 12, -2)
        rent_source = (
            f'تقدير من معدّل الرسملة نموذجي ({cap_rate*100:.1f}%) — '
            f'لا توجد بيانات إيجار فعلية للمنطقة'
        )

    annual_gross = estimated_monthly * 12 if estimated_monthly else 0
    annual_net = annual_gross * (1 - 0.23)  # 23% OPEX standard
    actual_cap = annual_net / val if val > 0 else 0
    gross_yield = annual_gross / val if val > 0 else 0
    net_yield = annual_net / val if val > 0 else 0

    # ── Section 1: تحليل العائد التقديري ──
    sections.append({
        'id': 'yield_estimated',
        'title_ar': 'تحليل العائد التقديري',
        'content': {
            'value_basis': val,
            'estimated_monthly_rent': estimated_monthly,
            'annual_gross_rent': annual_gross,
            'noi_annual_estimated': round(annual_net),
            'gross_yield_pct': round(gross_yield * 100, 2),
            'net_yield_pct': round(net_yield * 100, 2),
            'cap_rate_pct': round(actual_cap * 100, 2),
            'rent_source_ar': rent_source,
            'opex_ratio': 0.23,
            'caveat_ar': (
                'لم تقدّم إيجاراً فعلياً ولم تتوفر بيانات إيجار موثوقة للمنطقة. '
                'الأرقام أعلاه تقديرية مبنية على معايير Qatar نموذجية. '
                'للحصول على تحليل دقيق، أدخل الإيجار الشهري الفعلي وأعد التقييم.'
            ),
        },
    })

    # ── Section 2: سيناريوهات الاستثمار ──
    # Different acquisition prices vs the estimated yield
    if annual_net > 0:
        scenarios = []
        for discount in (-0.10, -0.05, 0, 0.05, 0.10):
            scenario_price = round(val * (1 + discount))
            scenario_cap = annual_net / scenario_price if scenario_price > 0 else 0
            scenarios.append({
                'price_qar': scenario_price,
                'price_vs_value_pct': round(discount * 100, 1),
                'net_yield_pct': round(scenario_cap * 100, 2),
                'label_ar': (
                    'القيمة المُقدَّرة' if discount == 0
                    else (f'صفقة خاصة (-{abs(discount)*100:.0f}%)' if discount < 0
                          else f'دفع علاوة (+{discount*100:.0f}%)')
                ),
            })
        sections.append({
            'id': 'investment_scenarios',
            'title_ar': 'سيناريوهات الاستثمار',
            'content': {
                'note_ar': (
                    'كيف يتأثر العائد السنوي بسعر الشراء؟ النطاق ±10% حول القيمة المُقدَّرة.'
                ),
                'scenarios': scenarios,
            },
        })

    # ── Section 3: تحليل الحساسية ──
    sensitivity = []
    for delta in (-1.0, -0.5, 0, 0.5, 1.0):
        scen_cap = cap_rate + (delta / 100.0)
        if scen_cap > 0:
            implied_value = round(annual_net / scen_cap, -3) if annual_net > 0 else val
            sensitivity.append({
                'cap_rate_pct': round(scen_cap * 100, 2),
                'implied_value': implied_value,
                'delta_label_ar': (
                    'الأساس' if delta == 0
                    else f'{"+" if delta > 0 else ""}{delta}%'
                ),
            })
    if sensitivity:
        sections.append({
            'id': 'sensitivity',
            'title_ar': 'تحليل الحساسية — معدّل الرسملة',
            'content': {
                'base_cap_rate_pct': round(cap_rate * 100, 2),
                'base_noi': round(annual_net),
                'scenarios': sensitivity,
                'note_ar': 'القيمة الضمنية لمستويات معدّل الرسملة مختلفة (±1%).',
            },
        })

    return sections


# ============================================================

def _analyze_reconciliation(primary, cost, income) -> dict:
    """Compare approaches and produce reconciliation statement (RICS Red Book)."""
    if not primary:
        return {'status': 'no_primary', 'message_ar': 'لا توجد قيمة مقارنة — عينة غير كافية'}

    p_val = primary['value']
    methods = [('comparison', p_val)]
    if cost and cost.get('value'):
        methods.append(('cost', cost['value']))
    if income and income.get('value'):
        methods.append(('income', income['value']))

    if len(methods) < 2:
        return {'status': 'comparison_only', 'methods_count': 1}

    values = [v for _, v in methods]
    min_v, max_v = min(values), max(values)
    spread_pct = (max_v - min_v) / min_v * 100 if min_v > 0 else 100

    # Individual gaps from primary
    gaps = {}
    for name, v in methods:
        if name != 'comparison':
            gaps[name] = round((v - p_val) / p_val * 100, 1)

    if spread_pct < 15:
        return {
            'status': 'strong_convergence',
            'label_ar': 'تقارب قوي بين الطرق',
            'message_ar': 'الطرق الثلاث تتقارب — ثقة عالية في القيمة',
            'spread_pct': round(spread_pct, 1),
            'gaps_pct': gaps,
        }
    if spread_pct < 30:
        return {
            'status': 'moderate_convergence',
            'label_ar': 'تقارب معقول',
            'message_ar': 'تباين متوسط بين الطرق — قد يعكس خصوصية العقار (عمر، إيجار، حالة)',
            'spread_pct': round(spread_pct, 1),
            'gaps_pct': gaps,
        }
    return {
        'status': 'divergence',
        'label_ar': 'تباين كبير',
        'message_ar': 'تباين جوهري بين الطرق — يلزم فحص ميداني أو إعادة تقييم البيانات',
        'spread_pct': round(spread_pct, 1),
        'gaps_pct': gaps,
    }


# ============================================================
# Sprint A.1: Fast short-circuit for DCF-only assets
# ============================================================

ASSET_TYPE_AR = {
    'standalone_villa':   'فيلا منفردة',
    'compound_small':     'مجمع فلل صغير',
    'compound_large':     'مجمع فلل كبير',
    'apartment_building': 'عمارة سكنية',
    'tower':              'برج سكني',
    'palace':             'قصر',
    'raw_land':           'أرض فضاء',
    'commercial':         'تجاري',
    'industrial':         'صناعي',
    'agricultural':       'مزرعة',
    'unknown':            'غير محدد',
}


# ── Sprint 2.11: GIS context preservation for fast/out-of-scope paths ──
# Historically the 4 _build_fast_*_response + _build_out_of_scope_response
# builders hardcoded district=None and geometric_factors=None, hiding GIS
# data we already had (district name is one cheap lookup; plot facts are
# already in memory). This helper surfaces that data uniformly.
#
# Costs ~200ms (one Districts spatial query). Wrapped in try/except so the
# fast path stays fast even if GIS is slow — if the call fails, we degrade
# gracefully to the pre-2.11 behavior (district=None).
_DCF_ASSETS_FOR_REASON = frozenset({'compound_large', 'tower', 'apartment_building'})


def _attach_scope(response: dict) -> dict:
    """Sprint 2.14.0 — attach RICS VPS 1 (Terms of engagement / scope of work) scope assessment to every response.

    Mutates and returns the response dict. Always safe — falls back to
    'unknown' scope if asset_type missing. Adds the field `service_scope`
    at top level. Pure addition; no existing field renamed or removed.

    The frontend uses this to show users WHAT level of valuation they're
    getting (supported = full Sales Comparison; limited = requires user
    input; unsupported = explicitly declined).

    Sprint 2.22.0a/7 — also attach universal `verification_url` here
    (R6 architectural finding: this function is the single universal gate
    called on every response — 5 early-exit sites + main `_build_unified_output`
    via line 4446 = 6 call sites). Both `address` + `valuation_date` are
    uniformly populated at response top-level before `_attach_scope`
    runs, so universal injection here is symmetric with the existing
    `service_scope` pattern. Architectural divergence from /5 is
    deliberate: /5's `refusal_reason` is per-site because each refusal
    site carries different `method`/`asset_type`/`plot_area_m2` context;
    `verification_url` only needs the two top-level fields and is
    therefore orthogonal to method/tier_label/refusal_reason gating.
    """
    try:
        asset_type = response.get('asset_type') or 'unknown'
        scope = classify_asset_scope(asset_type)
        response['service_scope'] = scope_to_dict(scope)
    except Exception:
        # Never break the response if scope module errors.
        pass
    # Sprint 2.22.0a/7 — universal verification_url injection.
    # Returns None when address or valuation_date is falsy (Q4 (a)),
    # mirroring the tier_label=None / refusal_reason=None opt-out pattern.
    # The /verify endpoint returns 404 in 2.22.0a — UI deferred to 2.22.0.1.
    try:
        from verification_url import build_verification_url
        response['verification_url'] = build_verification_url(
            response.get('address'),
            response.get('valuation_date'),
        )
    except Exception:
        # Defensive: never break a response on the audit-trail URL.
        response['verification_url'] = None
    return response


def _building_age_estimate(surveyed_date):
    """Sprint 2.22.0b.9 — DISPLAY-ONLY building-age FLOOR from QARS SURVEYED_DATE.

    QARS_Point survey dates are epoch milliseconds (UTC). The QARS address
    point is surveyed at/after construction completion (Operational Rule #10),
    so the survey year is a reliable LOWER BOUND on building age — NOT the exact
    construction year (honest '>=' framing). Validated against the Al Manara
    bank report (TD 93317): 56/647/6 surveyed 2009 → >=17y ≈ the report's
    "18 سنة". Returns None when the date is missing / unparseable. Never raises.
    """
    if not surveyed_date or not isinstance(surveyed_date, (int, float)):
        return None
    try:
        from datetime import datetime, timezone
        yr = datetime.fromtimestamp(surveyed_date / 1000.0, tz=timezone.utc).year
        cur = datetime.now(tz=timezone.utc).year
        floor = cur - yr
        if floor < 0:
            return None
        # Sprint 2.22.0b.13 (cliff-flag R3, value-invariant disclosure): SURVEYED_DATE is the survey
        # VINTAGE, not construction — the 2009-2012 mass survey caps old stock at a floor (E24), and a
        # very recent re-survey (a sale) zeroes a several-year-old building. Either way the registered
        # age is a LOWER BOUND → nudge the owner to enter the actual age in «حسّن التقدير».
        _vintage = (floor >= 15 and 2009 <= yr <= 2012) or (floor < 2)
        _est = {
            'surveyed_year': yr,
            'age_floor_years': floor,
            'basis': 'qars_survey',
            'age_basis': ('vintage_capped' if _vintage else 'survey'),
            'note_ar': f'عمر تقديري (حدّ أدنى من تاريخ مسح GIS سنة {yr}): ≥ {floor} سنة',
            'note_en': f'Indicative age (floor, from GIS survey {yr}): >= {floor} years',
        }
        if _vintage:
            _est['vintage_note_ar'] = ('العمر المسجَّل في النظام حدٌّ أدنى — العمر الفعلي قد يكون أكبر؛ '
                                       'أدخِل العمر الفعلي في «حسّن التقدير» لدقّة أعلى.')
            _est['vintage_note_en'] = ('The registered age is a floor — the actual age may be older; '
                                       'enter the actual age under “Refine” for higher precision.')
        return _est
    except Exception:
        return None


def _build_property_basis(pin=None, electricity_no=None, water_no=None,
                          surveyed_date=None):
    """Sprint 2.22.0b.9 — property-basis traceability block (display-only).

    Surfaces the QARS_Point identifiers ALREADY fetched by find_property
    (`outFields='*'`): PIN / electricity / water, plus a building-age FLOOR
    derived from SURVEYED_DATE. Inspired by the Al Manara bank valuation
    (TD 93317), which prints الرقم المساحي + رقم الكهرباء + عمر البناء.

    🔴 VALUE-INVARIANT: DISPLAY-ONLY. The age lives under `building_age_estimate`
    and is NEVER written into `user_inputs.building_age_years` (the user-supplied
    input that drives the b4 condition/age levers + age-rent). Feeding that key
    would be a Gate-2 valuation change; this block deliberately is not.

    Returns None when nothing is available (e.g. the PIN/land path has no QARS).
    Never raises.
    """
    try:
        age = _building_age_estimate(surveyed_date)
        if pin is None and electricity_no is None and water_no is None and age is None:
            return None
        return {
            'pin': pin,
            'electricity_no': electricity_no,
            'water_no': water_no,
            'building_age_estimate': age,
        }
    except Exception:
        return None


def _enrich_fast_context(loc, plot):
    """Return cheap GIS context for fast-path response builders.

    Args:
        loc: PropertyLocation (provides lon/lat)
        plot: PlotInfo (provides pdarea, pd_no — already in memory, free)

    Returns:
        dict with 'district' (str|None) and 'geometric_factors' (dict|None).
        Never raises — degrades to (None, None) on any failure.
    """
    district_ar = None
    try:
        if loc is not None and loc.lon is not None and loc.lat is not None:
            from qatar_gis import QatarGIS
            _gis = QatarGIS(verbose=False)
            _d = _gis.get_district_at_point(loc.lon, loc.lat)
            district_ar = _d.aname if _d else None
    except Exception as _e:
        # Non-fatal — fast path continues without district
        print(f"[sprint2.11] district lookup failed: {_e}", file=sys.stderr)

    gf = None
    if plot is not None:
        # PD_NO=0 is the unsubdivided-parcel sentinel; show only real PD refs
        pd_display = None
        try:
            if plot.pd_no and str(plot.pd_no) != '0':
                pd_display = str(plot.pd_no)
        except Exception:
            pd_display = None
        gf = {
            'polygon_available': True,
            'plot_area_m2_verified': plot.pdarea,
            'pd_no': pd_display,
        }

    # Sprint 2.22.0b.9 — property-basis (PIN/electricity/water/age-floor) for the
    # fast-path builders; built from the loc QARS attributes already in hand.
    _basis = _build_property_basis(
        getattr(loc, 'pin', None), getattr(loc, 'electricity_no', None),
        getattr(loc, 'water_no', None), getattr(loc, 'surveyed_date', None),
    ) if loc else None
    return {'district': district_ar, 'geometric_factors': gf, 'property_basis': _basis}


def _enrich_material_uncertainty(mu: dict) -> dict:
    """Inject Material Valuation Uncertainty (MVU) clause fields if not already present (Sprint 2.16.8).

    Sprint 2.22.0a/12 Phase 1.5b — citation updated to current effective-edition
    canonical reference: VPGA 10 + VPS 6 (RICS Red Book Global Standards,
    effective 31 January 2025) and IVS 106 (IVS, effective 31 January 2025).
    Multi-AI validation caught the 2025-edition transition that Sprint
    2.22.0a/9 missed. See material_uncertainty.py docstring for full standards
    audit trail.

    The four `_build_fast_*` response builders below construct
    `material_uncertainty` as an inline dict literal — bypassing the v3
    path in `evaluate_v3.py:457-460` that auto-populates MUC fields for
    standard villas. As a result, towers, out-of-scope assets, and other
    fast-path responses produced material_uncertainty WITHOUT the formal
    Material Valuation Uncertainty (MVU) muc_clause_ar/en/basis/review fields per VPGA 10 + VPS 6 + IVS 106 (current effective edition, 31 January 2025).

    This helper closes the gap: it calls `regime_muc()` from
    material_uncertainty.py (which has existed and been unused since
    Sprint 2.14) and merges its output into the inline mu dict,
    preserving any keys the caller explicitly set.

    Returns the (possibly enriched) dict — never raises; on any failure
    it returns the input unchanged so requests never fail on MUC
    enrichment.
    """
    try:
        from material_uncertainty import regime_muc, rics_compliant_status_fields
        muc = regime_muc()
        out = dict(mu)
        for k, v in muc.items():
            if v is not None and k not in out:
                out[k] = v
        # Sprint 2.22.0a.20 (A7): honest "review pending" label next to rics_compliant
        # (display/label only — the bool and all values are untouched). setdefault so a
        # caller-set status is never clobbered; True → helper returns {} → no-op.
        for k, v in rics_compliant_status_fields(out.get('rics_compliant', False)).items():
            out.setdefault(k, v)
        return out
    except Exception:
        return mu


def _build_fast_insufficient_data_response(zone, street, building, loc, plot, asset_type, audience):
    """Fast response for DCF-only assets when user provided no inputs.

    The full pipeline would take 30-90s on these (compound extent detection,
    GIS factor analysis, v3 enrichment) but always produces insufficient_data
    because there's no MoJ comparable for the asset class. Returns the
    classification facts in ~1s so the user can resubmit with rental_income
    or listing_price.
    """
    from datetime import datetime
    asset_label_ar = ASSET_TYPE_AR.get(asset_type, asset_type)
    # Sprint 2.11: surface district + plot geometry (cheap, always available)
    _ctx = _enrich_fast_context(loc, plot)
    # Sprint 2.11: parenthetical applies only to DCF assets (compounds/towers);
    # palace and other in-scope assets routed here via MoJ-empty district shouldn't
    # see the "compounds and towers register by reference numbers" explanation.
    _reason_paren = (
        ' (الكومباوندات الكبيرة والأبراج تُسجَّل بأرقام مرجعية موحَّدة بدلاً من مقارنات سعر/م²)'
        if asset_type in _DCF_ASSETS_FOR_REASON
        else (f' في {_ctx["district"]}' if _ctx.get('district') else '')
    )
    return _attach_scope({
        'status': 'ok',
        'engine_version': ENGINE_VERSION,
        'tier_label': _tier_label_for('insufficient_data'),  # Sprint 2.22.0a/2 — refusal → None
        # Sprint 2.22.0a/5 — refusal_reason via §5.3 precedence dispatcher.
        # At this site, asset_type may be compound_large (Patch-A promoted)
        # → asset_scale_extreme; or Pearl district → density_gated_district;
        # default → comp_density_sparse.
        'refusal_reason': _compute_refusal_reason(
            method='insufficient_data',
            asset_type=asset_type,
            district_ar=_ctx.get('district'),
            plot_area_m2=getattr(plot, 'pdarea', None),
        ),
        'methodology_ar': (
            'تصنيف سريع مبني على بيانات GIS — لا توجد مقارنة MoJ '
            f'مباشرة لفئة "{asset_label_ar}" في قطر'
        ),
        'methodology_disclaimer_ar': (
            'تقدير الأصول من هذه الفئة يحتاج منهج الدخل (Income Approach) أو سعر '
            'إعلان قابل للمقارنة. يرجى إعادة الطلب مع إفادة بالإيجار الشهري أو سعر '
            'الإعلان للحصول على تحليل آلي.'
        ),
        'address': f'{zone}/{street}/{building}',
        'valuation_date': datetime.now().strftime('%Y-%m-%d'),
        'district': _ctx['district'],
        'plot_area_m2': plot.pdarea,
        'gps': {'lat': loc.lat, 'lon': loc.lon} if loc else None,
        'asset_type': asset_type,
        'asset_type_ar': asset_label_ar,
        'audience': audience,
        'user_inputs': {
            'listing_price': None,
            'rental_income': None,
        },
        'valuation': {
            'amount': None,
            'low': None,
            'high': None,
            'method': 'insufficient_data',
            'reason_ar': (
                f'هذا الأصل من نوع "{asset_label_ar}" — لا توجد عينة مقارنة في سجلات '
                f'وزارة العدل لهذه الفئة{_reason_paren}. '
                'لتقييم دقيق، أضف الإيجار الشهري الفعلي أو سعر الإعلان وأعد الطلب.'
            ),
        },
        'moj_sample_size': 0,
        'cost_approach': None,
        'income_approach': None,
        'reconciliation': {
            'status': 'no_primary',
            'message_ar': 'تصنيف فقط — التقييم يحتاج إفادة الإيجار أو سعر الإعلان',
        },
        'accuracy': {
            'score': 0,
            'label': 'بيانات غير كافية',
        },
        'trend': None,
        'location_features': None,
        'geometric_factors': _ctx['geometric_factors'], 'property_basis': _ctx.get('property_basis'),
        'material_uncertainty': _enrich_material_uncertainty({
            'level': 'critical',
            'banner_ar': 'تحفظ مادي حرج: لا توجد بيانات بيع مقارنة لهذه الفئة',
            'known_unknowns_ar': [
                'الإيجار الشهري للوحدات',
                'حالة المبنى والعمر',
                'مساحة البناء الإجمالية',
                'عدد الوحدات الفعلي',
            ],
            'rics_compliant': False,
        }),
        'brief': {
            'audience': audience,
            'title_ar': f'تقرير {asset_label_ar} — تحتاج بيانات إضافية',
            'sections': [{
                'id': 'next_steps',
                'title_ar': 'الخطوات المقترحة',
                'content': {
                    'note_ar': (
                        f'العنوان {zone}/{street}/{building} تابع لمساحة {plot.pdarea:,.0f} م² '
                        f'مُصنَّف كـ "{asset_label_ar}". لتحليل آلي يرجى تزويدنا بأحد التاليين:'
                    ),
                    'options_ar': [
                        'إفادة الإيجار الشهري الفعلي (لتقييم بمنهج الدخل)',
                        'سعر الإعلان أو سعر المالك (لمقارنة سوقية)',
                    ],
                },
            }],
        },
        'disclaimer': (
            'ثمّن يجمع البيانات السوقية من المصادر الحكومية والإعلانات النشطة. '
            'هذا تحليل معلوماتي، ولا يُعتبر تقرير تثمين رسمي صادر عن مثمّن مرخّص وفق معايير RICS/IVS.'
        ),
        'active_listings': {
            'available': False,
            'reason': 'تصنيف سريع — لم يُجرَ بحث إعلانات',
        },
    })


# Sprint 2.21.3 — Hybrid T2 apartments path (D10 gate + first live-path
# coupling of hybrid_valuation_v1). Minimum listings to trust an indicative
# estimate; below this, fall through to insufficient_data (more honest than
# indicative-with-n=2).
HYBRID_T2_MIN_N = 5


# Sprint 2.21.3 polish — Lusail GIS Districts substring tokens.
# Post-deploy on v114 surfaced that PIN 69/329/20 (Lusail apt confirmed
# by Anas) classifies into Districts/MapServer/0 ANAME='غار ثعيلب' —
# Lusail Fox Hills, which does NOT contain 'لوسيل' as substring. The
# original gate `'لوسيل' in district_ar` rejected it incorrectly.
#
# Authoritative capture (Rule E13, probe_lusail_districts.py on v117):
#   Lusail proper Districts → ANAME ∈ {'لوسيل 69', 'لوسيل 70',
#                                       'وادي لوسيل'} all contain 'لوسيل'
#   Lusail Fox Hills        → ANAME = 'غار ثعيلب'   (separate token)
# Marketing names (Marina, Energy City, Waterfront) are sub-zones WITHIN
# 'لوسيل 69'/'لوسيل 70' per GIS, not separate districts.
LUSAIL_AR_TOKENS = frozenset({'لوسيل', 'غار ثعيلب'})
LUSAIL_EN_TOKENS = frozenset({'lusail', 'ghar thuaileb', 'fox hills'})


def _is_lusail_district(district_ar: str, district_en: str) -> bool:
    """D10 Lusail-municipality test (Sprint 2.21.3 polish-fix).

    Substring match against authoritative token sets:
      - 'لوسيل' covers لوسيل 69 / لوسيل 70 / وادي لوسيل
      - 'غار ثعيلب' covers Fox Hills (Anas-confirmed Lusail per 69/329/20)
      - English tokens cover the ENAME column as a defensive belt+suspenders
    """
    if district_ar:
        for tok in LUSAIL_AR_TOKENS:
            if tok in district_ar:
                return True
    if district_en:
        en = district_en.lower()
        for tok in LUSAIL_EN_TOKENS:
            if tok in en:
                return True
    return False


def _t2_sample_band(n: int) -> str:
    """Map T2 sample size to discipline band (Project_Instructions §3).

    Rule E3 §4 still caps the *confidence label* at 'indicative' regardless
    of n when T1 is absent. This function affects user-facing wording and
    accuracy score only — the engine's confidence remains 'indicative' per
    hybrid_valuation_v1 Case B.

    Returns:
        'boundary'           for 5 <= n < 10   (minimum-sample band)
        'indicative'         for 10 <= n < 20  (standard indicative)
        'strong_indicative'  for n >= 20       (large sample, ceiling still indicative)
    """
    if n < 10:
        return 'boundary'
    if n < 20:
        return 'indicative'
    return 'strong_indicative'


def _t2_band_copy(band: str, n: int, muc_range_pct: float) -> dict:
    """Return user-facing wording + accuracy fields for the band.

    muc_range_pct stays 0.20 across bands (Rule E3 Constraint 5 — mandatory
    ±20% when T1 absent). Only the *wording* and *accuracy score* vary,
    so brokers can distinguish n=7 from n=27 at a glance.
    """
    pct = int(muc_range_pct * 100)
    if band == 'boundary':
        return {
            'banner_ar': (
                f'تحفظ مادي: عينة عند الحد الأدنى (n={n}<10) — تفسير حذر مطلوب. '
                f'النطاق ±{pct}% (Rule E3 §5).'
            ),
            # Sprint 2.22.0a.2 C3: tier badge relabel "إرشادي" -> "شواهد محدودة";
            # quoted Category B references updated to match the new tier name.
            'disclaimer_ar': (
                'هذا التقدير من إعلانات (تطلعات بائعين) — ليس صفقات مسجلة. '
                f'مع n={n}<10، العينة عند الحد الأدنى للاسترشاد فقط — '
                'السقف "شواهد محدودة" (Rule E3 §4) ولا يُعتمد كقيمة سوق.'
            ),
            'level':          'medium',
            'accuracy_score': 1,
            'accuracy_label': 'شواهد محدودة عند الحد الأدنى للعينة (T2, n<10)',
        }
    if band == 'indicative':
        return {
            # Sprint 2.22.0a.2 C3: tier badge + Category B prose relabel.
            'banner_ar': (
                f'تحفظ مادي: عينة في فئة "شواهد محدودة" (n={n}, 10≤n<20). '
                f'النطاق ±{pct}% — لا يُعتمد كقيمة سوق نهائية.'
            ),
            'disclaimer_ar': (
                'هذا التقدير من إعلانات (تطلعات بائعين) — ليس صفقات مسجلة. '
                'الدقة في فئة "شواهد محدودة" (Rule E3 §4): السقف "شواهد محدودة" '
                'بدون T1 (Confirmed Sales أو MME).'
            ),
            'level':          'medium',
            'accuracy_score': 2,
            'accuracy_label': 'شواهد محدودة — مبنية على إعلانات (T2)',
        }
    # strong_indicative — n >= 20
    # Sprint 2.22.0a.2 C3: tier badge ceiling stays at "شواهد محدودة" even
    # with strong sample (Rule E3 §4 — needs T1 to upgrade to "شواهد كافية").
    return {
        'banner_ar': (
            f'تحفظ مادي: عينة قوية (n={n}≥20) لكن السقف يبقى "شواهد محدودة" '
            f'بدون تأكيد وزارة العدل (Rule E3 §4). النطاق ±{pct}%.'
        ),
        'disclaimer_ar': (
            'هذا التقدير من إعلانات بحجم عينة قوي (n≥20)، لكنه يبقى T2 — '
            'للوصول لـ "شواهد كافية" يلزم تأكيد T1 (Confirmed Sales أو MME). '
            'Rule E3 §4 يثبّت السقف عند "شواهد محدودة" بدون T1.'
        ),
        'level':          'low',
        'accuracy_score': 3,
        'accuracy_label': 'شواهد محدودة — عينة قوية (T2 n≥20)',
    }


def _try_hybrid_apartments_response(
    zone, street, building, loc, plot, asset_type, audience, gis_lite,
):
    """Sprint 2.21.3 — Lusail apartments via PropertyFinder T2 listings.

    Returns a complete response dict when D10 conditions are met AND the
    hybrid framework produced a `value_per_m2`. Returns None to signal
    "fall through to the existing insufficient_data path" — callers must
    handle that case.

    D10 gate (CHANGELOG_v48 §1):
      - asset_type == 'apartment_building'  (caller has verified)
      - district == 'Lusail'                (computed here)
      - HYBRID_APARTMENTS_ENABLED env var  != 'false'  (D11; default true)

    Defensive contract: any exception → return None + log to stderr. Never
    raises. This protects existing apartment_building behaviour (the
    pre-2.21.3 insufficient_data response) against connector/network/
    parser failures (D6/D7).
    """
    import os
    # D11 feature flag — emergency rollback without code revert
    if os.getenv('HYBRID_APARTMENTS_ENABLED', 'true').lower() == 'false':
        return None

    # D10 district gate — Lusail only
    if not (loc and getattr(loc, 'lat', None) and getattr(loc, 'lon', None)):
        return None
    try:
        dist = gis_lite.get_district_at_point(loc.lon, loc.lat)
    except Exception as e:
        print(f"[hybrid-apt] district lookup failed: {e}", file=sys.stderr)
        return None
    district_ar = (dist.aname if dist else '') or ''
    district_en = (dist.ename if dist else '') or ''
    if not _is_lusail_district(district_ar, district_en):
        return None

    # Fetch T2 listings (D6 — connector swallows network errors)
    try:
        from connectors.propertyfinder_apartments_t2_sales import (
            get_apartment_sales_lusail,
        )
    except ImportError as e:
        print(f"[hybrid-apt] connector import failed: {e}", file=sys.stderr)
        return None
    try:
        listings = get_apartment_sales_lusail(size_bracket=None, use_cache=True)
    except Exception as e:
        print(f"[hybrid-apt] connector exception: {e}", file=sys.stderr)
        return None
    if not listings or len(listings) < HYBRID_T2_MIN_N:
        return None

    # Sprint 2.21.4: fetch T3 developer-inventory rows alongside T2.
    # D10 env-flag gate mirrors HYBRID_APARTMENTS_ENABLED — emergency
    # rollback via `heroku config:set T3_INVENTORY_ENABLED=false` (no
    # redeploy). Defensive: any T3 connector failure → t3_rows=None →
    # hybrid runs with T2-only (Sprint 2.21.3 baseline behaviour).
    if os.getenv('T3_INVENTORY_ENABLED', 'true').lower() != 'false':
        try:
            from connectors.developer_inventory_t3 import fetch_for_district
            t3_rows = fetch_for_district(
                district=district_ar,
                asset_type=asset_type,
            )
        except Exception as e:
            print(f"[hybrid-apt] T3 connector failure: {e}", file=sys.stderr)
            t3_rows = None
    else:
        t3_rows = None

    # Call hybrid framework. With t3_rows present and T2 also present,
    # Case B fires (no T1) and T3 contributes up to 0.15 × evidence_strength.
    # With t3_rows=None (flag off, no DB, or no matching rows) the engine
    # response shape is byte-identical to the Sprint 2.21.3 baseline.
    try:
        from hybrid_valuation import hybrid_valuation_v1
        hybrid = hybrid_valuation_v1(
            t1_values=None, t1_n_total=0,
            t2_values=listings, t3_values=t3_rows,
        )
    except Exception as e:
        print(f"[hybrid-apt] hybrid_valuation_v1 exception: {e}", file=sys.stderr)
        return None

    value_per_m2 = hybrid.get('value_per_m2')
    if value_per_m2 is None:
        return None

    # Build response — start from base insufficient_data shell, then overlay
    base = _build_fast_insufficient_data_response(
        zone, street, building, loc, plot, asset_type, audience,
    )

    muc_range_pct = hybrid.get('muc_range_pct') or 0.20
    low_per_m2 = round(value_per_m2 * (1.0 - muc_range_pct), 2)
    high_per_m2 = round(value_per_m2 * (1.0 + muc_range_pct), 2)
    confidence = hybrid.get('confidence', 'indicative')
    asset_label_ar = ASSET_TYPE_AR.get(asset_type, asset_type)

    # Sample-size band — adapts user-facing wording + accuracy score so
    # brokers can distinguish n=7 (boundary) from n=27 (strong indicative)
    # at a glance. Engine `confidence` and `muc_range_pct` are unchanged —
    # both are Rule E3 hard constraints (§4 ceiling, §5 mandatory ±20%).
    n_used = len(listings)
    band = _t2_sample_band(n_used)
    copy = _t2_band_copy(band, n_used, muc_range_pct)

    base['methodology_ar'] = (
        f'منهجية هجينة (Hybrid v1) — وسيط أسعار الإعلانات (T2) من PropertyFinder '
        f'بعد خصم تفاوضي مرجعي ~12.5%. n={n_used} إعلان شقة للبيع في لوسيل '
        f'(عينة {band}).'
    )
    base['methodology_disclaimer_ar'] = copy['disclaimer_ar']
    base['valuation'] = {
        'amount': None,                # no specific apartment area in this query
        'low': None,
        'high': None,
        'method': 'hybrid_t2',
        'value_per_m2': round(value_per_m2, 2),
        'value_per_m2_low': low_per_m2,
        'value_per_m2_high': high_per_m2,
        'reason_ar': (
            f'القيمة الإرشادية للمتر المربع لشقق {asset_label_ar} في لوسيل ≈ '
            f'{int(value_per_m2):,} ر.ق/م² '
            f'(نطاق ±{int(muc_range_pct*100)}%: '
            f'{int(low_per_m2):,} – {int(high_per_m2):,} ر.ق/م²). '
            'لقيمة شقة محددة، اضرب في مساحتها م² الفعلية.'
        ),
    }
    base['hybrid'] = {
        'case': hybrid.get('case'),
        'confidence': confidence,
        'sample_size_band': band,
        'n_used': n_used,
        'tier_breakdown': hybrid.get('tier_breakdown', []),
        'muc_required': hybrid.get('muc_required', True),
        'muc_range_pct': muc_range_pct,
        'rule_e3_compliance': hybrid.get('rule_e3_compliance'),
    }
    base['sources'] = [{
        'source': 'propertyfinder',
        'tier': 'T2',
        'n_raw': n_used,
        'role_ar': 'إعلانات بيع شقق — لوسيل',
        'url_template': 'propertyfinder.qa/en/buy/lusail/apartments-for-sale.html',
        'calibration_status': 'provisional_broker_experience_grounded',
    }]
    base['accuracy'] = {
        'score': copy['accuracy_score'],
        'label': copy['accuracy_label'],
    }
    base['reconciliation'] = {
        'status': 'hybrid_indicative',
        # Sprint 2.22.0a.2 C3: Category B reference updated to new tier name.
        'message_ar': (
            f'تقدير من مصدر T2 واحد (PropertyFinder، n={n_used}، عينة {band}). '
            'وزارة العدل لا تسجّل الشقق الفردية (تُحفظ تحت الأبراج). '
            'لتقدير في فئة "شواهد كافية" يلزم Confirmed Sales أو MME.'
        ),
    }
    base['material_uncertainty'] = _enrich_material_uncertainty({
        'level': copy['level'],
        'banner_ar': copy['banner_ar'],
        'known_unknowns_ar': [
            'مساحة الشقة المحددة',
            'الطابق + الإطلالة + التشطيب',
            'حالة الصيانة الفعلية',
            'مدى تطابق الإعلانات مع الصفقات المنجزة',
        ],
        'rics_compliant': True,        # hybrid framework satisfies Rule E3
    })
    # Sprint 2.22.0a/2 — tier_label top-level emission (Y3 helper, KICKOFF §4.3 + F1)
    base['tier_label'] = _tier_label_for(base.get('valuation', {}).get('method'))
    return base


def _build_fast_listing_only_response(zone, street, building, loc, plot, asset_type,
                                       audience, listing_price):
    """Sprint A.3 fix: Fast response for DCF asset with listing_price but no rental.

    The full pipeline would burn 30-40s on GIS extent detection that produces no
    usable comparison (no MoJ comparable for compound_large/tower/etc.). Instead,
    we reverse-engineer: at typical Cap Rate, what rent would this listing price
    require? Returns in ~1s with an actionable question for the user.
    """
    from datetime import datetime
    asset_label_ar = ASSET_TYPE_AR.get(asset_type, asset_type)

    # Reverse-engineer implied rent from listing price
    cap_rate = CAP_RATES_BY_ASSET.get(asset_type) or 0.075
    opex_ratio = OPEX_RATIO_RESIDENTIAL
    implied_annual_noi = listing_price * cap_rate
    implied_annual_rent = implied_annual_noi / (1 - opex_ratio)
    implied_monthly_rent = implied_annual_rent / 12

    # Sanity context: implied rent per m² of plot
    rent_per_m2_year = implied_annual_rent / plot.pdarea if plot.pdarea else 0

    plausibility_ar = (
        'في النطاق المعقول' if 60 <= rent_per_m2_year <= 400
        else 'مرتفع — السعر قد يكون مبالغاً فيه' if rent_per_m2_year > 400
        else 'منخفض — السعر قد يكون رخيصاً'
    )

    # Sprint 2.11: surface district + plot geometry
    _ctx = _enrich_fast_context(loc, plot)

    return _attach_scope({
        'status': 'ok',
        'engine_version': ENGINE_VERSION,
        'tier_label': _tier_label_for('listing_only_implied_rent'),  # Sprint 2.22.0a/2 — 'analytical_range'
        'methodology_ar': (
            f'تحليل سعر الإعلان لـ "{asset_label_ar}" — تقدير الإيجار الضمني المطلوب '
            'لجعل السعر منطقياً وفق معدّل الرسملة نموذجي.'
        ),
        'methodology_disclaimer_ar': (
            'هذا ليس تقييماً نهائياً، بل أداة فحص: نحسب الإيجار الذي يجب أن يُنتجه '
            'العقار لتبرير السعر المطلوب. إذا كان الإيجار الفعلي أقل بكثير من '
            'المُقدَّر، السعر مرتفع. للتقييم الكامل، أعد الطلب مع الإيجار الشهري الفعلي.'
        ),
        'address': f'{zone}/{street}/{building}',
        'valuation_date': datetime.now().strftime('%Y-%m-%d'),
        'district': _ctx['district'],
        'plot_area_m2': plot.pdarea,
        'gps': {'lat': loc.lat, 'lon': loc.lon} if loc else None,
        'asset_type': asset_type,
        'asset_type_ar': asset_label_ar,
        'audience': audience,
        'user_inputs': {
            'listing_price': listing_price,
            'rental_income': None,
        },
        'valuation': {
            'amount': None,
            'low': None,
            'high': None,
            'method': 'listing_only_implied_rent',
            'reason_ar': (
                f'لا توجد مقارنة MoJ مباشرة لـ "{asset_label_ar}". '
                f'بدلاً من تقييم بدون مرجع، نحسب الإيجار الضمني: '
                f'لتبرير سعر {listing_price:,.0f} ر.ق، يجب أن يُنتج هذا العقار '
                f'~{implied_monthly_rent:,.0f} ر.ق شهرياً. '
                'قارن هذا بالإيجار الفعلي للحكم على معقولية السعر.'
            ),
        },
        'moj_sample_size': 0,
        'cost_approach': None,
        'income_approach': None,
        'reconciliation': {
            'status': 'implied_rent_check',
            'message_ar': 'فحص ضمني — أعد الطلب مع الإيجار الفعلي للتقييم الكامل',
        },
        'accuracy': {
            'score': 30,
            'label': 'فحص ضمني فقط',
        },
        'trend': None,
        'location_features': None,
        'geometric_factors': _ctx['geometric_factors'], 'property_basis': _ctx.get('property_basis'),
        'material_uncertainty': _enrich_material_uncertainty({
            'level': 'high',
            'banner_ar': 'لا يوجد تقييم حقيقي — فقط فحص ضمني للسعر المطلوب',
            'known_unknowns_ar': [
                'الإيجار الشهري الفعلي للعقار',
                'مستوى الإشغال الحقيقي',
                'حالة المبنى والصيانة',
            ],
            'rics_compliant': False,
        }),
        'brief': {
            'audience': audience,
            'title_ar': f'فحص ضمني — {asset_label_ar}',
            'sections': [
                {
                    'id': 'implied_rent',
                    'title_ar': 'الإيجار الضمني المطلوب',
                    'content': {
                        'listing_price': listing_price,
                        'implied_monthly_rent': round(implied_monthly_rent),
                        'implied_annual_rent': round(implied_annual_rent),
                        'implied_noi': round(implied_annual_noi),
                        'cap_rate_used_pct': round(cap_rate * 100, 2),
                        'rent_per_m2_year': round(rent_per_m2_year, 1),
                        'plausibility_ar': plausibility_ar,
                        'note_ar': (
                            f'لجعل سعر {listing_price:,.0f} ر.ق منطقياً وفق معدّل الرسملة '
                            f'نموذجي ({cap_rate*100:.1f}% لـ {asset_label_ar})، يجب أن '
                            f'يُنتج هذا العقار إيجاراً شهرياً قدره '
                            f'~{implied_monthly_rent:,.0f} ر.ق.'
                        ),
                    },
                },
                {
                    'id': 'next_steps',
                    'title_ar': 'الخطوات المقترحة',
                    'content': {
                        'note_ar': 'لتقييم نهائي وموثوق:',
                        'options_ar': [
                            f'أكّد أو انفِ: هل الإيجار الفعلي قريب من {implied_monthly_rent:,.0f} ر.ق/شهر؟',
                            'إذا كان الإيجار الفعلي أقل بكثير → السعر مرتفع',
                            'إذا كان الإيجار الفعلي أعلى أو مساوياً → السعر منطقي',
                            'أعد الطلب مع الإيجار الشهري للتقييم الكامل',
                        ],
                    },
                },
            ],
        },
        'sanity_warnings': [],
        'disclaimer': (
            'ثمّن يجمع البيانات السوقية من المصادر الحكومية والإعلانات النشطة. '
            'هذا تحليل معلوماتي، ولا يُعتبر تقرير تثمين رسمي صادر عن مثمّن مرخّص وفق معايير RICS/IVS.'
        ),
        'active_listings': {
            'available': False,
            'reason': 'فحص ضمني — لم يُجرَ بحث إعلانات',
        },
    })


def _build_fast_income_only_response(zone, street, building, loc, plot, asset_type,
                                      audience, rental_income, listing_price,
                                      rent_source_ar='إفادة العميل (الإيجار الفعلي)'):
    """Sprint A.2: Fast income-only valuation for DCF-only assets.

    For compound_large / tower / commercial / apartment_building with rental_income,
    the full pipeline takes 30-90s producing comparison data that has no MoJ
    comparable anyway. The Income Approach is the ONLY valid method for these
    assets, and it needs just 4 inputs: rental, OPEX ratio, cap rate, asset size.
    All available in ~1s without GIS extent detection or geometric factors.

    The valuation produced is RICS-compliant Income Approach output. Comparison
    and Cost approaches are explicitly absent (correctly).
    """
    from datetime import datetime
    asset_label_ar = ASSET_TYPE_AR.get(asset_type, asset_type)

    # ── Income Approach computation ──
    annual_rent = (rental_income or 0) * 12
    opex_ratio = OPEX_RATIO_RESIDENTIAL
    noi = annual_rent * (1 - opex_ratio)
    cap_rate = CAP_RATES_BY_ASSET.get(asset_type) or 0.075
    income_value = round(noi / cap_rate) if cap_rate > 0 else None
    gross_yield = (annual_rent / income_value) if income_value else None
    net_yield = (noi / income_value) if income_value else None

    # Range: ±15% reflecting Cap Rate uncertainty
    value_low = round(income_value * 0.85, -4) if income_value else None
    value_high = round(income_value * 1.15, -4) if income_value else None

    # ── Listing comparison if provided ──
    listing_gap_pct = None
    if listing_price and income_value:
        listing_gap_pct = (listing_price - income_value) / income_value

    # ── Sensitivity scenarios ──
    sensitivity = []
    for delta in (-1.0, -0.5, 0, 0.5, 1.0):
        c = cap_rate + (delta / 100.0)
        if c > 0:
            sensitivity.append({
                'cap_rate_pct': round(c * 100, 2),
                'income_value': round(noi / c, -3),
                'delta_label_ar': 'الأساس' if delta == 0 else ('+' if delta > 0 else '') + f'{delta}%',
            })

    # ── Investor brief sections (rebuilt locally) ──
    sections = [
        {
            'id': 'yield',
            'title_ar': 'تحليل العائد',
            'content': {
                'gross_yield_pct': round((gross_yield or 0) * 100, 2),
                'net_yield_pct': round((net_yield or 0) * 100, 2),
                'noi_annual': noi,
                'annual_rent_gross': annual_rent,
                'cap_rate_pct': round(cap_rate * 100, 2),
                'cap_rate_label_ar': f'معدل رسملة {cap_rate*100:.1f}% (نموذجي لـ {asset_label_ar})',
                'rent_source_ar': rent_source_ar,
            },
        },
        {
            'id': 'income_value',
            'title_ar': 'القيمة بمنهج الدخل',
            'content': {
                'income_value': income_value,
                'cap_rate_used': cap_rate,
                'noi': noi,
                'role_ar': (
                    f'القيمة الأساسية المعتمدة لـ "{asset_label_ar}" (منهج الدخل '
                    'هو المنهج الأنسب لهذه الفئة وفق RICS Income Approach)'
                ),
                'method_label_ar': 'منهج الدخل (RICS Income Approach)',
            },
        },
        {
            'id': 'sensitivity',
            'title_ar': 'تحليل الحساسية — معدّل الرسملة',
            'content': {
                'base_cap_rate_pct': round(cap_rate * 100, 2),
                'base_noi': noi,
                'scenarios': sensitivity,
                'note_ar': 'حساسية القيمة لتغير معدّل الرسملة ±1% — لأن المعدل تقديري ويتأثر بحالة السوق.',
            },
        },
        {
            'id': 'market_context',
            'title_ar': 'السياق السوقي',
            'content': {
                'qatar_benchmark': f'معدّل رسملة 7-8% للكومباوندات الكبيرة في قطر = طبيعي',
                'above_6_net': 'صافي عائد > 6% = جذاب للمستثمرين',
                'below_4_net': 'صافي عائد < 4% = ضعيف، أعد التفاوض',
            },
        },
    ]

    # If listing_price provided, add comparison section
    if listing_price and income_value:
        gap_pct = listing_gap_pct * 100
        position_ar = (
            'أقل من قيمة الدخل' if gap_pct < -5
            else 'أعلى من قيمة الدخل' if gap_pct > 5
            else 'مطابق لقيمة الدخل'
        )
        sections.insert(0, {
            'id': 'verdict',
            'title_ar': 'مقارنة السعر بقيمة الدخل',
            'content': {
                'listing_price': listing_price,
                'benchmark': income_value,
                'gap_pct': listing_gap_pct,
                'position': 'above_market' if gap_pct > 5 else 'below_market' if gap_pct < -5 else 'at_market',
                'description_ar': f'السعر {position_ar} بـ {abs(gap_pct):.1f}%. القيمة محسوبة من الإيجار المُقدَّم بمنهج الدخل.',
            },
        })

    # Sprint 2.11: surface district + plot geometry
    _ctx = _enrich_fast_context(loc, plot)

    _fast_result = _attach_scope({
        'status': 'ok',
        'engine_version': ENGINE_VERSION,
        'tier_label': _tier_label_for('income_approach_only'),  # Sprint 2.22.0a/2 — 'analytical_range'
        'methodology_ar': (
            f'تقدير سريع بمنهج الدخل (RICS Income Approach) لـ "{asset_label_ar}". '
            'لا توجد مقارنة MoJ مباشرة لهذه الفئة في قطر — الدخل هو المنهج المعياريّ.'
        ),
        'methodology_disclaimer_ar': (
            'تقدير آلي مبني على الإيجار المُقدَّم من العميل و معدّل الرسملة نموذجي للفئة. '
            'للأغراض الرسمية يلزم تقييم من مُقيِّم معتمد بعد فحص ميداني وتحقق من الإيجار '
            'الفعلي عبر فترة طويلة.'
        ),
        'address': f'{zone}/{street}/{building}',
        'valuation_date': datetime.now().strftime('%Y-%m-%d'),
        'district': _ctx['district'],
        'plot_area_m2': plot.pdarea,
        'gps': {'lat': loc.lat, 'lon': loc.lon} if loc else None,
        'asset_type': asset_type,
        'asset_type_ar': asset_label_ar,
        'audience': audience,
        'user_inputs': {
            'listing_price': listing_price,
            'rental_income': rental_income,
        },
        'valuation': {
            'amount': income_value,
            'low': value_low,
            'high': value_high,
            'method': 'income_approach_only',
            'method_ar': 'منهج الدخل (المنهج المعياريّ لهذه الفئة)',
        },
        'moj_sample_size': 0,
        'cost_approach': None,
        'income_approach': {
            'income_value': income_value,
            'annual_rent': annual_rent,
            'monthly_rent': rental_income,
            'rent_source_ar': 'إفادة العميل',
            'noi': noi,
            'opex_ratio': opex_ratio,
            'cap_rate': cap_rate,
            'cap_rate_label_ar': f'معدل رسملة {cap_rate*100:.1f}% (نموذجي لـ {asset_label_ar})',
            'gross_yield': gross_yield,
            'net_yield': net_yield,
            'method_label_ar': 'منهج الدخل (RICS Income Approach)',
            'role_ar': 'القيمة الأساسية المعتمدة',
        },
        'reconciliation': {
            'status': 'income_only',
            'message_ar': (
                f'منهج واحد معتمد: الدخل. للأصول من فئة "{asset_label_ar}" '
                'لا توجد مقارنة MoJ كافية، ومنهج التكلفة لا يعكس قيمة الاستثمار.'
            ),
        },
        'accuracy': {
            'score': 55,
            'label': 'تقدير بمنهج واحد',
        },
        'trend': None,
        'location_features': None,
        'geometric_factors': _ctx['geometric_factors'], 'property_basis': _ctx.get('property_basis'),
        'material_uncertainty': _enrich_material_uncertainty({
            'level': 'high',
            'banner_ar': (
                'تحفظ مادي مرتفع: التقدير مبني على معدّل الرسملة نموذجي + إيجار مُقدَّم من '
                'العميل. للقرارات الكبيرة، يُنصح بفحص ميداني وتحقق من الإيجار التاريخي.'
            ),
            'known_unknowns_ar': [
                'مدى استقرار الإيجار التاريخي (هل الرقم المُقدَّم ثابت أم متذبذب؟)',
                'تكاليف التشغيل الفعلية (قد تختلف عن 23% النموذجي)',
                'حالة المباني والإنشاءات (تؤثر على معدّل الرسملة الفعلي)',
                'مستوى الإشغال الفعلي',
            ],
            'rics_compliant': False,
        }),
        'brief': {
            'audience': audience,
            'title_ar': (
                f'تقرير المستثمر — {asset_label_ar}' if audience == 'investor'
                else f'تقدير {asset_label_ar} بمنهج الدخل'
            ),
            'sections': sections,
        },
        'disclaimer': (
            'ثمّن يجمع البيانات السوقية من المصادر الحكومية والإعلانات النشطة. '
            'هذا تحليل معلوماتي، ولا يُعتبر تقرير تثمين رسمي صادر عن مثمّن مرخّص وفق معايير RICS/IVS.'
        ),
        'active_listings': {
            'available': False,
            'reason': 'تقدير سريع بمنهج الدخل — لم يُجرَ بحث إعلانات',
        },
    })
    # Sprint 2.22.0b.59: range-inversion guard on the fast (income-only) path too —
    # low <= amount <= high before the fingerprint (no-op on the valid income band).
    _clamp_valuation_range(_fast_result.get('valuation'))
    # Sprint 2.22.0b.23: the apartment income report is verifiable too (no scenarios —
    # those are villa/house DRC-only). Additive; never touches the income headline.
    _attach_report_identity(_fast_result, zone, street, building, None,
                            {'rental_income': rental_income, 'asking_price': listing_price})
    return _fast_result


def _build_out_of_scope_response(zone, street, building, loc, plot, asset_type, audience):
    """Sprint A.3: Polite rejection for asset types outside v1 scope.

    v1 supports: villas, lands, small compounds, palaces (full pipeline) +
    DCF fallback for large income-producing assets. v1 does NOT support:
    individual apartments, commercial shops, offices, industrial, agricultural.

    The reason: MoJ data and our rent reference don't cover these classes with
    enough density to produce defensible valuations. Better to refuse cleanly
    than to produce confidently-wrong numbers.
    """
    from datetime import datetime
    asset_label_ar = ASSET_TYPE_AR.get(asset_type, asset_type)
    suggestions = {
        'commercial': 'للمحلات التجارية، يُوصى بمُقيِّم متخصص في العقارات التجارية.',
        'industrial': 'للعقارات الصناعية، يُوصى بمُقيِّم متخصص ومسح ميداني للمنطقة الصناعية.',
        'agricultural': 'للمزارع، يلزم تقييم مخصص يشمل الرخصة الزراعية وموارد الماء.',
    }
    # Sprint 2.11: surface district + plot geometry even when refusing valuation
    _ctx = _enrich_fast_context(loc, plot)
    return _attach_scope({
        'status': 'ok',
        'engine_version': ENGINE_VERSION,
        'tier_label': _tier_label_for('out_of_scope_v1'),  # Sprint 2.22.0a/2 — refusal → None
        # Sprint 2.22.0a/5 — asset_class_out_of_scope trigger (Q1 (d) NEW 6th).
        'refusal_reason': _compute_refusal_reason(
            method='out_of_scope_v1',
            asset_type=asset_type,
            district_ar=_ctx.get('district'),
        ),
        'methodology_ar': f'الإصدار الأول من ثمّن لا يدعم فئة "{asset_label_ar}"',
        'methodology_disclaimer_ar': (
            'ثمّن في إصداره الأول مُصمَّم خصيصاً للفلل والأراضي والقصور والكومباوندات. '
            'هذه الفئات تملك بيانات MoJ كافية لإنتاج تقييم موثوق. '
            'فئات أخرى (تجاري، صناعي، مزرعة، شقق فردية) تحتاج بيانات ومنهجية مختلفة، '
            'وسيتم دعمها في إصدارات لاحقة.'
        ),
        'address': f'{zone}/{street}/{building}',
        'valuation_date': datetime.now().strftime('%Y-%m-%d'),
        'district': _ctx['district'],
        'plot_area_m2': plot.pdarea if plot else None,
        'gps': {'lat': loc.lat, 'lon': loc.lon} if loc else None,
        'asset_type': asset_type,
        'asset_type_ar': asset_label_ar,
        'audience': audience,
        'user_inputs': {},
        'valuation': {
            'amount': None, 'low': None, 'high': None,
            'method': 'out_of_scope_v1',
            'reason_ar': (
                f'هذا العقار من فئة "{asset_label_ar}" — خارج نطاق ثمّن الإصدار الأول. '
                + suggestions.get(asset_type, 'يُوصى بمُقيِّم متخصص في هذه الفئة.')
            ),
        },
        'moj_sample_size': 0,
        'cost_approach': None,
        'income_approach': None,
        'reconciliation': {
            'status': 'out_of_scope',
            'message_ar': 'فئة العقار خارج نطاق الإصدار الحالي',
        },
        'accuracy': {'score': 0, 'label': '— خارج النطاق'},
        'trend': None, 'location_features': None, 'geometric_factors': _ctx['geometric_factors'], 'property_basis': _ctx.get('property_basis'),
        'material_uncertainty': _enrich_material_uncertainty({
            'level': 'critical',
            'banner_ar': 'لا يمكن إنتاج تقييم موثوق لهذه الفئة في الإصدار الحالي',
            'known_unknowns_ar': [
                'بيانات بيع MoJ شحيحة لهذه الفئة',
                'مرجع إيجار غير كافٍ',
                'منهجية متخصصة مطلوبة',
            ],
            'rics_compliant': False,
        }),
        'brief': {
            'audience': audience,
            'title_ar': f'تقرير {asset_label_ar} — خارج النطاق',
            'sections': [{
                'id': 'out_of_scope',
                'title_ar': 'الإصدار الأول من ثمّن لا يدعم هذه الفئة',
                'content': {
                    'note_ar': (
                        f'العنوان {zone}/{street}/{building} تابع لـ "{asset_label_ar}" '
                        f'بمساحة {plot.pdarea if plot else "—"} م². '
                        'ثمّن مُصمَّم حالياً للفلل والأراضي والقصور والكومباوندات. '
                        + suggestions.get(asset_type, '')
                    ),
                    'options_ar': [
                        'استشارة مُقيِّم متخصص في هذه الفئة',
                        'العودة إلى ثمّن لاحقاً بعد إصدار النسخة الموسّعة',
                        'البحث عن عقار من الفئات المدعومة حالياً',
                    ],
                },
            }],
        },
        'sanity_warnings': [],
        'disclaimer': (
            'ثمّن يجمع البيانات السوقية من المصادر الحكومية والإعلانات النشطة. '
            'هذا تحليل معلوماتي، ولا يُعتبر تقرير تثمين رسمي صادر عن مثمّن مرخّص وفق معايير RICS/IVS.'
        ),
        'active_listings': {'available': False, 'reason': 'خارج نطاق الإصدار'},
    })


# Sprint 2.21.0.7.1 (DECISION Q3): RULEID + built → Arabic display label, so the
# prominent "نوع العقار" field shows the discovered type instead of "غير محدد".
# (bare_label, built_label); single entry → same label for both states.
_DISCOVERED_LABEL_AR = {
    1:  ('أرض سكنية (فلل)',        'فيلا سكنية'),
    2:  ('أرض سكنية (عمارات)',     'مبنى سكني'),
    3:  ('أرض تجارية',             'مبنى تجاري'),
    4:  ('أرض خدمات/مكاتب',        'مبنى خدمات/مكاتب'),
    5:  ('أرض تجارة جملة',         'مبنى تجارة جملة'),
    6:  ('أرض صناعية',             'مبنى صناعي'),
    7:  ('أرض صناعية',             'مبنى صناعي'),
    8:  ('أرض صناعية',             'مبنى صناعي'),
    9:  ('أرض صناعية',             'مبنى صناعي'),
    10: ('أرض تعليمية',            'مبنى تعليمي'),
    11: ('أرض صحية',               'مبنى صحي'),
    12: ('أرض حكومية',             'مبنى حكومي'),
    13: ('أرض مجتمعية/ثقافية',     'مبنى مجتمعي/ثقافي'),
    14: ('أرض دينية',              'مبنى ديني'),
    15: ('ساحة/حديقة',             'ساحة/حديقة'),
    16: ('أرض رياضية',             'منشأة رياضية'),
    17: ('أرض نقل/مواصلات',        'منشأة نقل/مواصلات'),
    18: ('أرض مرافق',              'منشأة مرافق'),
    19: ('أرض زراعية',             'مزرعة'),
    20: ('أرض فضاء غير مصنّفة',    'أرض فضاء غير مصنّفة'),
    21: ('تطوير خاص',              'تطوير خاص'),
    22: ('أرض سياحية',             'مبنى سياحي'),
    23: ('تطوير مختلط الاستخدام',  'تطوير مختلط الاستخدام'),
}


def _discovered_label_ar(reality):
    """Sprint 2.21.0.7.1: derive the 'نوع العقار' display label from the reality
    payload's RULEID + built state. Falls back to the RULEID's Arabic label,
    then to a generic 'أرض / قطعة'."""
    rid = reality.get('ruleid')
    built = isinstance(reality.get('qars_in_polygon'), int) and reality['qars_in_polygon'] > 0
    pair = _DISCOVERED_LABEL_AR.get(rid)
    if pair:
        return pair[1] if built else pair[0]
    return reality.get('ruleid_label_ar') or 'أرض / قطعة'


def _build_reality_stop_response(loc, plot, audience, reality):
    """Sprint 2.21.0.7: dedicated 'stop'/'reject' response for the PIN/land path
    when the Asset Type Reality Check finds the parcel is built or non-residential.

    `reality` is the parsed asset_type_reality payload (kind/action/reason/ruleid/
    labels/message_ar/discovery). Mirrors the out-of-scope shape but is PIN-aware
    (no zone/street/building) and carries the exact decision-template message.
    """
    from datetime import datetime
    _ctx = _enrich_fast_context(loc, plot)
    _district = _ctx.get('district')
    _pin = getattr(plot, 'pin', None) if plot else None
    _addr = (f'أرض في {_district} — PIN {_pin}' if _district and _pin
             else (f'PIN {_pin}' if _pin else '—'))
    _msg = reality.get('message_ar') or 'هذه القطعة خارج نطاق التقييم الحالي.'
    _reason = reality.get('reason')
    _disc_label = _discovered_label_ar(reality)   # DECISION Q3
    _title = ('قطعة عليها مبنى — ليست أرض فضاء'
              if _reason == 'building_present'
              else ('قطعة عليها مبنى غير سكني — خارج النطاق' if _reason == 'non_residential_built'
                    else ('قطعة استخدام مختلط — خارج النطاق' if _reason == 'mixed_use'
                          else f'أرض غير سكنية ({reality.get("ruleid_label_ar", "")}) — خارج النطاق')))
    return _attach_scope({
        'status': 'ok',
        'engine_version': ENGINE_VERSION,
        'tier_label': _tier_label_for('asset_type_reality_stop'),  # Sprint 2.22.0a/2 — refusal → None
        # Sprint 2.22.0a/5 — spatial_ambiguity trigger per §5.3 row 2.
        'refusal_reason': _compute_refusal_reason(
            method='asset_type_reality_stop',
            asset_type='unknown',
            district_ar=_district,
            plot_area_m2=plot.pdarea if plot else None,
        ),
        'methodology_ar': 'فحص نوع الأصل (Asset Type Reality Check)',
        'address': _addr,
        'valuation_date': datetime.now().strftime('%Y-%m-%d'),
        'district': _district,
        'plot_area_m2': plot.pdarea if plot else None,
        'gps': {'lat': loc.lat, 'lon': loc.lon} if loc else None,
        # asset_type='unknown' → service_scope badge shows "unsupported"
        # (consistent with the out-of-scope message). The precise reason lives
        # in the asset_type_reality panel; asset_type_ar keeps a friendly label.
        'asset_type': 'unknown',
        # DECISION Q3: keep asset_type='unknown' (scope badge stays unsupported),
        # but surface the DISCOVERED type here so the "نوع العقار" field shows it
        # instead of "غير محدد". The frontend prefers asset_type_ar when
        # asset_type=='unknown'.
        'asset_type_ar': _disc_label,
        'audience': audience,
        'user_inputs': {'pin': str(_pin) if _pin else None},
        'valuation': {
            'amount': None, 'low': None, 'high': None,
            'method': 'asset_type_reality_stop',
            'reason_ar': _msg,
        },
        'moj_sample_size': 0,
        'cost_approach': None,
        'income_approach': None,
        'reconciliation': {
            'status': 'out_of_scope',
            'message_ar': _title,
        },
        'accuracy': {'score': 0, 'label': '— خارج النطاق'},
        'trend': None, 'location_features': None,
        'geometric_factors': _ctx.get('geometric_factors'),
        'property_basis': _ctx.get('property_basis'),
        'material_uncertainty': _enrich_material_uncertainty({
            'level': 'critical',
            'banner_ar': _title,
            'known_unknowns_ar': [],
            'rics_compliant': False,
        }),
        # The structured reality payload — the UI renders the panel + discovery.
        'asset_type_reality': reality,
        'brief': {
            'audience': audience,
            'title_ar': _title,
            'sections': [{
                'id': 'asset_type_reality',
                'title_ar': _title,
                'content': {'note_ar': _msg},
            }],
        },
        'sanity_warnings': [],
        'disclaimer': (
            'ثمّن يجمع البيانات السوقية من المصادر الحكومية والإعلانات النشطة. '
            'هذا تحليل معلوماتي، ولا يُعتبر تقرير تثمين رسمي صادر عن مثمّن مرخّص وفق معايير RICS/IVS.'
        ),
        'active_listings': {'available': False, 'reason': 'خارج النطاق'},
    })


def _check_input_sanity(asset_type, listing_price, rental_income, plot_area):
    """Sprint A.3: Pre-evaluation input validation.

    Returns dict with:
        - warnings_ar: list of human-readable warning strings
        - rental_income_adjusted: rental to use (may be cleared if nonsensical)

    Does NOT block evaluation — only adds warnings. Out-of-scope rejection
    is handled separately via _build_out_of_scope_response.
    """
    warnings = []
    rental_use = rental_income

    # Raw land: no rent is possible (vacant land doesn't produce income)
    if asset_type in ('raw_land', 'land') and rental_income:
        warnings.append(
            f'تم تجاهل الإيجار المُدخَل ({rental_income:,.0f} ر.ق) — الأراضي '
            'الفضاء لا تُنتج دخلاً إيجارياً. التقييم على أساس قيمة الأرض من MoJ فقط.'
        )
        rental_use = None

    # Palace: rental approach is unusual but not impossible
    if asset_type == 'palace' and rental_income:
        warnings.append(
            'القصور نادراً ما تُؤجَّر — تحقق أن الإيجار المُقدَّم واقعي '
            'لأصل بهذه القيمة.'
        )

    # Sanity: zero or negative inputs
    if listing_price is not None and listing_price <= 0:
        warnings.append('سعر الإعلان يجب أن يكون أكبر من صفر.')
    if rental_income is not None and rental_income <= 0:
        warnings.append('الإيجار الشهري يجب أن يكون أكبر من صفر.')

    # Wild ranges (catch typos like 5,000,000 instead of 5,000)
    if rental_income and rental_income > 5_000_000:
        warnings.append(
            f'الإيجار الشهري {rental_income:,.0f} ر.ق مرتفع جداً — '
            'تأكد من العدد (هل أدخلت بدون فواصل، أو سنوي بدل شهري؟).'
        )
    if listing_price and listing_price > 5_000_000_000:
        warnings.append(
            f'سعر الإعلان {listing_price:,.0f} ر.ق مرتفع جداً — '
            'تأكد من العدد.'
        )

    # For DCF assets with rental: rent/m² sanity vs plot area
    # Sprint 2.16.11 — tower carve-out: plot_area for towers is NOT a
    # proxy for usable BUA (20+ floors mean BUA ≈ 20× plot). The 60-800
    # band that fits compounds produces false-positive warnings on towers.
    # Example: Lusail B201 (3,378 m² plot, ~80 units × 12K rent = 960K/month
    # → 3,552 QAR/m² of plot, but only ~178 QAR/m² of BUA — perfectly normal).
    # Until the engine has a reliable BUA estimate (floors × footprint),
    # we skip this specific check for towers. Other DCF assets keep it.
    if (asset_type in ('compound_large', 'compound_small', 'apartment_building')
            and rental_income and plot_area and plot_area > 0):
        rent_per_m2 = (rental_income * 12) / plot_area  # annual rent per m² of plot
        # Typical compound: 80-400 QAR/m²/year. Below 60 = likely partial/single-unit rent.
        # Above 800 = unrealistic for plot of that size (probably wrong input).
        if rent_per_m2 < 60:
            warnings.append(
                f'الإيجار يعادل ~{rent_per_m2:.0f} ر.ق/م² سنوياً للأرض ({plot_area:,.0f} م²) — '
                'منخفض جداً لكومباوند بهذا الحجم. '
                'هل أدخلت إيجار وحدة واحدة بدل المجمع كاملاً؟ '
                'الإيجار المتوقع لأصل بهذا الحجم: 100-300 ر.ق/م² سنوياً.'
            )
        elif rent_per_m2 > 800:
            warnings.append(
                f'الإيجار يعادل ~{rent_per_m2:.0f} ر.ق/م² سنوياً للأرض ({plot_area:,.0f} م²) — '
                'مرتفع جداً لأصل بهذا الحجم. تحقق من الرقم.'
            )

    return {'warnings_ar': warnings, 'rental_income_adjusted': rental_use}


def _check_output_sanity(result, listing_price):
    """Sprint A.3: Post-valuation cross-checks.

    Looks at the produced valuation and yields, warns on implausible results.
    Modifies result in-place by appending to sanity_warnings.

    Yield norms differ by asset class:
      - Residential (villa, palace): 2-5% net is typical
        (location/lifestyle dominate, low yield is normal)
      - Investment-grade (compound, tower, commercial): 5-10% net is typical
        (yield must compensate for management + depreciation)
    """
    warnings = result.get('sanity_warnings', [])
    asset_type = result.get('asset_type', '')

    # Yield bounds by asset class
    if asset_type in ('standalone_villa', 'villa', 'palace'):
        y_normal_min, y_normal_max = 0.02, 0.05
        y_flag_min, y_flag_max = 0.01, 0.08
    else:  # investment-grade
        y_normal_min, y_normal_max = 0.05, 0.10
        y_flag_min, y_flag_max = 0.03, 0.12

    # Net yield sanity (from income_approach if present)
    inc = result.get('income_approach') or {}
    ny = inc.get('net_yield')
    if ny is not None:
        if ny < y_flag_min:
            warnings.append(
                f'صافي العائد ({ny*100:.1f}%) منخفض جداً — أقل من '
                f'{y_flag_min*100:.0f}%. تأكد من الإيجار المُدخَل أو راجع السعر.'
            )
        elif ny > y_flag_max:
            warnings.append(
                f'صافي العائد ({ny*100:.1f}%) مرتفع جداً — أعلى من '
                f'{y_flag_max*100:.0f}%. الإيجار قد يكون مبالغاً فيه، '
                'أو القيمة منخفضة بشدة.'
            )
        elif ny > y_normal_max:
            warnings.append(
                f'صافي العائد ({ny*100:.1f}%) أعلى من النطاق الطبيعي لهذه الفئة '
                f'({y_normal_min*100:.0f}%-{y_normal_max*100:.0f}%) — '
                'فرصة تستحق الفحص.'
            )
        # NOTE: yields just below y_normal_min are common for residential and
        # don't warrant a warning (would just create alert fatigue).

    # Listing vs benchmark gap
    # Sprint 2.16.2: when stock_strata classified the subject into a specific
    # stratum (reliable, n≥10), use that stratum's estimated_total as benchmark
    # instead of the blended bracket median. Resolves the Sprint 2.16.0 reporting
    # contradiction where "asking 5M is +53% above blended" while strata card
    # says "your luxury_new tier median = 4.69M (+6.7%)".
    val = result.get('valuation') or {}
    benchmark = val.get('amount')
    benchmark_source_ar = 'المرجع'

    _strata = result.get('stock_strata') or {}
    _subject = _strata.get('subject_property') or {}
    _cls = _subject.get('classification')
    if _cls and _cls in ('land_priced', 'aging_stock', 'modern_stock', 'luxury_new'):
        _stratum_data = (_strata.get('strata') or {}).get(_cls) or {}
        _stratum_total = _stratum_data.get('estimated_total')
        # Only swap if the stratum has a reliable (n≥10) reference
        if _stratum_total and _stratum_data.get('reliable'):
            benchmark = _stratum_total
            _label = _subject.get('classification_label_ar') or _cls
            benchmark_source_ar = f'وسيط فئة "{_label}"'

    if listing_price and benchmark:
        gap = (listing_price - benchmark) / benchmark
        if gap > LISTING_GAP_OVERPRICED_WARN:
            warnings.append(
                f'السعر المطلوب ({listing_price:,.0f}) أعلى بـ {gap*100:.0f}% '
                f'من {benchmark_source_ar} — السوق غالباً يرفض السعر بهذا المستوى.'
            )
        elif gap < LISTING_GAP_UNDERPRICED_WARN:
            warnings.append(
                f'السعر المطلوب ({listing_price:,.0f}) أقل بـ {abs(gap)*100:.0f}% '
                f'من {benchmark_source_ar} — تحقق من السبب (تنازل، أقساط، خلاف، حالة المبنى).'
            )

    result['sanity_warnings'] = warnings


# ============================================================
# Unified entry point
# ============================================================

# ── Sprint 2.22.0b.22 — tower-pair fence (micro Gate-2, signed 2026-06-11) ──
# Phase-0 (docs/PHASE0_income_types_exposure.md §4) measured the Sprint 2.16.10
# (unit_count × avg_monthly_rent_per_unit) multiplication UNGATED on asset
# type: the pair on a villa was laundered into a "subject actual rent" and
# income_led drove 54/541/6 to 11.2M (signed: 2.4M cost-led). The fence
# realizes the documented §19 promise: the pair derives a building-total rent
# for MULTI-UNIT (tower-like) assets only; on anything else it is IGNORED with
# an explicit disclosure and never feeds income_led. The villa's legitimate
# single-rent path (b6, bare rental_income) is untouched.
#
# Membership note (#39 deviation from the literal §19 four-type list):
# compound_small IS tower-like here — an address-entry large compound is
# quick-classified compound_small (subtype 2/3; the E20 extent promotion runs
# AFTER the DCF fork), so excluding it would have moved the signed
# byte-identical compound behaviour (contract: «مجمع كبير ⇒ سلوكه الحالي
# بايت-مطابق»). commercial_building kept per the §19 list (no classify_asset
# branch emits it today on this path — harmless).
_TOWER_PAIR_ASSETS = frozenset({
    'tower', 'apartment_building', 'compound_large', 'compound_small',
    'commercial_building',
})
_TOWER_PAIR_IGNORED_AR = 'مدخل برجي على أصل غير برجي — تم تجاهله'
_TOWER_PAIR_IGNORED_EN = ('Tower-style input (unit count × per-unit rent) on a '
                          'non-tower asset — ignored')


def _derive_rent_from_unit_pair(qtype, unit_count, avg_monthly_rent_per_unit,
                                rental_income):
    """Pure (b22): resolve the effective monthly rent + provenance from the
    Sprint 2.16.10 (unit_count × per-unit) pair vs a bare rental_income.

    Returns (rental_income, rent_source, pair_ignored):
      - tower-like + complete pair → derived total wins (byte-identical to the
        pre-b22 strings/behaviour), rent_source kind='derived_from_units'.
      - non-tower-like + complete pair → the pair is IGNORED (pair_ignored
        carries the verbatim disclosure); a bare rental_income, if any,
        proceeds exactly as a pair-less request (the b6 path untouched).
      - incomplete pair → legacy elif: bare rental_income provenance only.
    """
    if unit_count and avg_monthly_rent_per_unit:
        if qtype in _TOWER_PAIR_ASSETS:
            _derived_total = unit_count * avg_monthly_rent_per_unit
            return _derived_total, {
                'kind': 'derived_from_units',
                'unit_count': unit_count,
                'avg_per_unit': avg_monthly_rent_per_unit,
                'derived_monthly_total': _derived_total,
                'note_ar': f'محسوب من {unit_count} وحدة × {int(avg_monthly_rent_per_unit):,} ر.ق/شهر = {int(_derived_total):,} ر.ق/شهر إجمالي',
            }, None
        pair_ignored = {
            'kind': 'tower_pair_ignored',
            'asset_type': qtype,
            'unit_count': unit_count,
            'avg_per_unit': avg_monthly_rent_per_unit,
            'note_ar': _TOWER_PAIR_IGNORED_AR,
            'note_en': _TOWER_PAIR_IGNORED_EN,
        }
    else:
        pair_ignored = None
    if rental_income:
        return rental_income, {
            'kind': 'user_total',
            'monthly_total': rental_income,
            'note_ar': f'إفادة العميل: {int(rental_income):,} ر.ق/شهر إجمالي',
        }, pair_ignored
    return rental_income, None, pair_ignored


def evaluate_thammen(
    zone: Optional[int] = None,
    street: Optional[int] = None,
    building: Optional[int] = None,
    moj_csv_path: str = 'moj_weekly.csv',
    rent_ref_path: Optional[str] = 'rent_reference.json',
    listing_price: Optional[float] = None,
    rental_income: Optional[float] = None,
    # Sprint 2.16.10 — tower/compound rental clarity:
    #   if (unit_count, avg_monthly_rent_per_unit) both provided, derive
    #   total monthly rent = unit_count * avg_monthly_rent_per_unit
    #   and use that for the income approach. If rental_income is ALSO
    #   provided, the pair wins (since it's the unambiguous form).
    unit_count: Optional[int] = None,
    avg_monthly_rent_per_unit: Optional[float] = None,
    floors: Optional[int] = None,
    condition: Optional[str] = None,
    annexes: int = 0,
    bua_breakdown: Optional['BuaBreakdown'] = None,
    # Sprint 2.2 — explicit building-improvements inputs (BUA awareness)
    basement: Optional[bool] = None,
    footprint_m2: Optional[float] = None,
    external_majlis: Optional[bool] = None,
    # Sprint 2.3 — Qatar 10-Year Rule (age-aware adjustment)
    building_age_years: Optional[int] = None,
    is_luxury: Optional[bool] = None,
    penthouse: Optional[bool] = None,
    audience: str = 'buyer',
    use_listings: bool = True,
    use_geo_v2: bool = True,
    # Sprint 2.21.0 — PIN/land entry: when `pin` is set the request is a bare
    # land plot (no QARS address); `input_mode='land'` is threaded to the
    # classifier so it types the parcel as land rather than a villa.
    pin: Optional[str] = None,
    input_mode: Optional[str] = None,
    # Sprint 2.21.0.9 — Multi-QARS user override: when set, overrides the
    # auto-detected effective_land_area used for MoJ bracket selection. UI
    # uses this for (a) the "value whole structure" toggle on attached duplexes
    # (re-submits with override=cadastral_area), and (b) the manual override
    # field on shared/ambiguous plots.
    override_land_area: Optional[float] = None,
) -> Dict:
    if not _V2_OK:
        return {'status': 'engine_unavailable', 'error': 'evaluate_property not loaded'}

    # Sprint 2.4b: normalize audience aliases (valuator/valuer/مثمن/مقيم → 'valuer')
    # so brief generation routes correctly. The frontend now sends 'valuer' but
    # the API used to silently fall back to buyer for any unrecognized value.
    audience = _normalize_audience(audience)

    # ── Sprint A.1/A.2/A.3: Fast pre-classification + scope filter + sanity checks ──
    # 1. Quick GIS lookup classifies the asset (~0.7s)
    # 2. Sprint A.3: if asset is out of v1 scope → polite rejection
    # 3. Sprint A.3: input sanity checks (rental for land? wild numbers?)
    # 4. DCF-only assets get fast paths (A.1 with no inputs, A.2 with rental)
    # 5. In-scope assets continue to full pipeline below
    DCF_ONLY = {'compound_large', 'tower', 'apartment_building'}
    _qtype = None
    _plot = None
    _loc = None
    _sanity_warnings = []
    # Sprint 2.16.14 — scope-safe init: if the Lite GIS path fails before
    # the classifier runs, the full villa pipeline still references this
    # variable. Defaulting to None means "no mismatch detected".
    _subtype_zoning_mismatch = None
    # Sprint 2.21.0.7 — scope-safe init for the asset-type reality check flag
    # (PIN/land path). None means "no reality issue detected".
    _asset_type_reality = None
    # Sprint 2.22.0b.22 — scope-safe init: if the Lite GIS path fails before the
    # rent-pair derivation runs, the attach sites below still reference this.
    # None means "no tower pair was ignored".
    _tower_pair_ignored = None

    try:
        from qatar_gis import QatarGIS, classify_asset, PropertyLocation
        _gis_lite = QatarGIS(verbose=False)
        # Sprint 2.21.0: PIN/land entry resolves the plot directly (no QARS) and
        # synthesises a location (centroid) so the district + comparable gates
        # below still work. Address entry keeps the original QARS path.
        _plot0 = None
        if pin:
            _plot0 = _gis_lite.get_plot(pin)
            _ring = (_plot0.polygon_4326 or []) if _plot0 else []
            if _ring:
                _cx = sum(p[0] for p in _ring) / len(_ring)
                _cy = sum(p[1] for p in _ring) / len(_ring)
            else:
                _cx = _cy = None
            _loc = (PropertyLocation(
                zone=zone, street=street, building=building, pin=pin,
                qars='', plot_no_old=None, lon=_cx, lat=_cy,
                electricity_no=None, water_no=None, qtel_id=None,
                building_subtype=None,
            ) if _plot0 else None)
        else:
            _loc = _gis_lite.find_property(zone, street, building)
        if _loc:
            _plot = _plot0 if pin else _gis_lite.get_plot(_loc.pin)
            if _plot:
                # Sprint 2.16.6: pass building_subtype from QARS_Point so the
                # classifier can use the authoritative type label instead of
                # area-based heuristic (fixes A1 — 15,881 polygons including
                # Lusail/West Bay towers were misclassified as "palace").
                # Sprint 2.16.14: also pass lat/lon so the classifier can
                # run a Zoning cross-check (Bug A11) — detects stale QARS
                # subtypes for buildings whose use changed after 2012.
                _meta = None
                if _loc and getattr(_loc, 'building_subtype', None) is not None:
                    _meta = {
                        'building_subtype': _loc.building_subtype,
                        'lat': getattr(_loc, 'lat', None),
                        'lon': getattr(_loc, 'lon', None),
                    }
                _quick = classify_asset(_plot, _meta, input_mode=input_mode)
                _qtype = _quick.asset_type.value

                # ── Sprint 2.16.14: extract subtype/zoning mismatch flag (Bug A11) ──
                # The classifier surfaces a contradiction when a residential
                # subtype sits inside a non-residential zone (e.g. أشغال
                # 61/875/20: subtype=6 "Flats" + Zoning=CCC). We turn that
                # raw flag into a structured warning attached to the
                # response root, mirroring the Sprint 2.16.8/9 MUC pattern.
                # (`_subtype_zoning_mismatch` was initialized to None above
                # the try-block for scope safety.)
                for _flag_str in (_quick.flags or []):
                    if isinstance(_flag_str, str) and _flag_str.startswith('subtype_zoning_mismatch:'):
                        _msg_ar = _flag_str.split(':', 1)[1].strip()
                        _subtype_zoning_mismatch = {
                            'kind': 'subtype_zoning_mismatch',
                            'message_ar': _msg_ar,
                            'qars_subtype': _loc.building_subtype if _loc else None,
                            'classified_as': _qtype,
                            'recommendation_ar': (
                                'تحقق من الاستخدام الفعلي للمبنى. لو كان تجارياً أو '
                                'حكومياً (مكاتب/خدمات)، أعد التقييم باختيار "تجاري" '
                                'في نوع العقار للحصول على منهجية تقييم صحيحة.'
                            ),
                            'data_age_note_ar': (
                                'البيانات الأصلية لـ QARS_Point لمعظم القطع جاءت من '
                                'مسوحات 2010-2012 — قد لا تعكس تحويلات الاستخدام اللاحقة.'
                            ),
                        }
                        break

                # ── Sprint 2.21.0.7: Asset Type Reality Check flag ──
                # The PIN/land classifier emits an `asset_type_reality:` flag
                # (JSON payload) when QARS finds a building on the "land" parcel
                # (action=stop), or the RULEID land-use class is non-residential
                # (action=reject) / tradable-but-non-residential (action=warn).
                for _flag_str in (_quick.flags or []):
                    if isinstance(_flag_str, str) and _flag_str.startswith('asset_type_reality:'):
                        try:
                            import json as _json_atr
                            _asset_type_reality = _json_atr.loads(_flag_str.split(':', 1)[1])
                        except Exception:
                            _asset_type_reality = None
                        break

                # GATE 0 (Sprint 2.21.0.7): a 'stop'/'reject' reality result ends
                # the evaluation with a dedicated message (no valuation). 'warn'
                # falls through and is attached to the final response below.
                if _asset_type_reality and _asset_type_reality.get('action') in ('stop', 'reject'):
                    return _build_reality_stop_response(
                        _loc, _plot, audience, _asset_type_reality,
                    )

                # ── Sprint A.3 GATE 1: out-of-scope rejection ──
                if _qtype in V1_OUT_OF_SCOPE:
                    _oos_result = _build_out_of_scope_response(
                        zone, street, building, _loc, _plot, _qtype, audience,
                    )
                    # Sprint 2.16.14 — attach Zoning cross-check flag if present
                    if _subtype_zoning_mismatch:
                        _oos_result['subtype_zoning_mismatch'] = _subtype_zoning_mismatch
                    return _oos_result

                # ── Sprint A.3 GATE 2: input sanity (modifies rental_income if needed) ──
                _sanity = _check_input_sanity(_qtype, listing_price, rental_income,
                                              _plot.pdarea if _plot else None)
                _sanity_warnings = _sanity['warnings_ar']
                rental_income = _sanity['rental_income_adjusted']

                # ── Sprint 2.16.10 / 2.22.0b.22: derive total monthly rent from the
                # (unit_count × avg_per_unit) pair — TOWER-LIKE ASSETS ONLY (the b22
                # fence). On a non-tower asset the pair is IGNORED with an explicit
                # disclosure and never overwrites rental_income (so it can never
                # feed b6 income_led); a bare rental_income proceeds untouched.
                rental_income, _rent_source, _tower_pair_ignored = (
                    _derive_rent_from_unit_pair(
                        _qtype, unit_count, avg_monthly_rent_per_unit,
                        rental_income))

                # ── Sprint A.1/A.2/A.3: DCF fast paths ──
                if _qtype in DCF_ONLY:
                    if rental_income:
                        # Sprint A.2: income-only valuation (fast)
                        # Sprint 2.16.10 — provenance label reflects how rent was supplied
                        _rs_label = (_rent_source['note_ar'] if _rent_source
                                     else 'إفادة العميل (الإيجار الفعلي)')
                        result = _build_fast_income_only_response(
                            zone, street, building, _loc, _plot, _qtype, audience,
                            rental_income, listing_price,
                            rent_source_ar=_rs_label,
                        )
                        # Sprint 2.16.10 — attach source provenance so the UI can
                        # show "calculated from N units × Y" instead of just a total.
                        if _rent_source:
                            result['rent_source'] = _rent_source
                        # Sprint 2.16.14 — attach Zoning cross-check flag
                        if _subtype_zoning_mismatch:
                            result['subtype_zoning_mismatch'] = _subtype_zoning_mismatch
                        # Apply post-valuation sanity + accumulate pre-warnings
                        result['sanity_warnings'] = _sanity_warnings + (result.get('sanity_warnings') or [])
                        _check_output_sanity(result, listing_price)
                        return result
                    elif listing_price:
                        # Sprint A.3 fix: reverse-engineer implied rent (fast)
                        result = _build_fast_listing_only_response(
                            zone, street, building, _loc, _plot, _qtype, audience,
                            listing_price,
                        )
                        # Sprint 2.16.14 — attach Zoning cross-check flag
                        if _subtype_zoning_mismatch:
                            result['subtype_zoning_mismatch'] = _subtype_zoning_mismatch
                        result['sanity_warnings'] = _sanity_warnings + (result.get('sanity_warnings') or [])
                        return result
                    else:
                        # Sprint 2.21.3 — Hybrid T2 apartments path (Lusail, D10-gated).
                        # Tries PropertyFinder T2 listings → hybrid_valuation_v1.
                        # Returns None on miss (env flag off, non-Lusail, n<5,
                        # connector/network/parse failure) → falls through to
                        # the pre-2.21.3 insufficient_data response below.
                        if _qtype == 'apartment_building':
                            _hybrid_result = _try_hybrid_apartments_response(
                                zone, street, building, _loc, _plot, _qtype, audience,
                                _gis_lite,
                            )
                            if _hybrid_result is not None:
                                if _subtype_zoning_mismatch:
                                    _hybrid_result['subtype_zoning_mismatch'] = _subtype_zoning_mismatch
                                _hybrid_result['sanity_warnings'] = (
                                    _sanity_warnings
                                    + (_hybrid_result.get('sanity_warnings') or [])
                                )
                                return _hybrid_result
                        # Sprint A.1: classification only (no inputs)
                        result = _build_fast_insufficient_data_response(
                            zone, street, building, _loc, _plot, _qtype, audience,
                        )
                        # Sprint 2.16.14 — attach Zoning cross-check flag
                        if _subtype_zoning_mismatch:
                            result['subtype_zoning_mismatch'] = _subtype_zoning_mismatch
                        result['sanity_warnings'] = _sanity_warnings + (result.get('sanity_warnings') or [])
                        return result

                # ── Sprint A.3+ GATE 3: MoJ data-availability check ──
                # Even for in-scope assets (villa, palace, land, compound_small),
                # if MoJ has no comparable in this district, the full 19s pipeline
                # would just produce insufficient_data. This catches edge cases:
                #   - Misclassified towers (as palace) in West Bay → no MoJ palaces there
                #   - Real palaces in remote districts → no MoJ comparable
                #   - Any asset in a district MoJ doesn't cover well
                # Routes to fast paths instead, saving 15-25 seconds.
                try:
                    _dist_obj = _gis_lite.get_district_at_point(_loc.lon, _loc.lat)
                    _district_ar = _dist_obj.aname if _dist_obj else None
                except Exception:
                    _district_ar = None

                _moj_n = _count_moj_comparables(moj_csv_path, _district_ar, _qtype)
                if _moj_n < MIN_MOJ_SAMPLES_FOR_FULL_PIPELINE:
                    # No useful MoJ data → route to fast paths
                    if rental_income:
                        _rs_label = (_rent_source['note_ar'] if _rent_source
                                     else 'إفادة العميل (الإيجار الفعلي)')
                        result = _build_fast_income_only_response(
                            zone, street, building, _loc, _plot, _qtype, audience,
                            rental_income, listing_price,
                            rent_source_ar=_rs_label,
                        )
                        # Sprint 2.16.10 — propagate rent_source provenance
                        if _rent_source:
                            result['rent_source'] = _rent_source
                    elif listing_price:
                        result = _build_fast_listing_only_response(
                            zone, street, building, _loc, _plot, _qtype, audience,
                            listing_price,
                        )
                    else:
                        result = _build_fast_insufficient_data_response(
                            zone, street, building, _loc, _plot, _qtype, audience,
                        )
                    # Sprint 2.16.14 — attach Zoning cross-check flag
                    if _subtype_zoning_mismatch:
                        result['subtype_zoning_mismatch'] = _subtype_zoning_mismatch
                    # Sprint 2.22.0b.22 — disclose an ignored tower pair (a non-tower
                    # asset routed to a fast path by the MoJ-thin gate).
                    if _tower_pair_ignored:
                        result['tower_pair_ignored'] = _tower_pair_ignored
                    # Add a warning explaining the routing decision
                    _sanity_warnings.append(
                        f'لا توجد مقارنة كافية في وزارة العدل لـ "{ASSET_TYPE_AR.get(_qtype, _qtype)}" '
                        f'في {_district_ar or "هذه المنطقة"} (عدد المعاملات المتاحة: {_moj_n}). '
                        'استُخدم المسار السريع بدلاً من المسار الكامل لتفادي الانتظار الطويل دون فائدة. '
                        'قد يكون تصنيف العقار غير دقيق — تحقق من نوع العقار في النتيجة.'
                    )
                    result['sanity_warnings'] = _sanity_warnings + (result.get('sanity_warnings') or [])
                    if rental_income or listing_price:
                        _check_output_sanity(result, listing_price)
                    return result
    except Exception as e:
        # Lite path failed — fall through to full pipeline (defensive)
        print(f"[fast-classify] failed: {e}", file=sys.stderr)

    # ── Step 1: v2 baseline ──
    has_reno, full_reno = _condition_to_reno(condition)

    # Sprint 2.2 — use plot-aware smart BUA builder.
    # Replaces the legacy fixed-300m² assumption.
    _plot_area_for_bua = _plot.pdarea if (_plot and getattr(_plot, 'pdarea', None)) else None
    _any_building_input = any([
        floors and floors > 0,
        annexes and annexes > 0,
        basement is True,
        footprint_m2 and footprint_m2 > 0,
        external_majlis is True,
    ])
    if bua_breakdown is None and _any_building_input:
        bua_breakdown = _build_smart_bua(
            plot_area_m2=_plot_area_for_bua,
            floors=floors,
            annexes=annexes,
            basement=basement,
            footprint_m2=footprint_m2,
            external_majlis=external_majlis,
        )

    try:
        # Sprint 2.4a: pass age + luxury into v2 baseline so cost_approach
        # applies proper depreciation (DRC) and the brief's negotiation
        # sections anchor on age-appropriate values.
        # construction_tier upgrades to 'high' for declared luxury so the
        # cost_approach uses higher per-m² construction cost.
        _tier = 'high' if is_luxury else 'mid'
        ev = evaluate_property(
            zone=zone, street=street, building=building,
            pin=pin, input_mode=input_mode,   # Sprint 2.21.0: land/PIN entry
            moj_csv_path=Path(moj_csv_path),
            listing_price=listing_price,
            bua_breakdown=bua_breakdown,
            building_age_years=building_age_years,
            construction_tier=_tier,
            has_renovation=has_reno,
            full_renovation=full_reno,
            rental_income=rental_income,
            include_age=True,
            # Sprint 2.21.0.9: user override for multi-QARS effective land area.
            # None → engine auto-detects via classify_multi_qars.
            plot_area_override=override_land_area,
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'status': 'evaluation_failed', 'error': str(e)}

    # ── Sprint 2.5: Auto-detect building age from GIS imagery ──
    # When the user didn't provide building_age_years, the v2 baseline may have
    # auto-detected it from historical satellite imagery (qatar_gis.py imagery
    # analysis via report.construction.earliest_built_year). Surface it here so:
    #   1. The Sprint 2.3 age-aware substantiality multiplier uses it
    #   2. The cost_approach already benefited from it via evaluate_property
    #   3. The UI can show a "detected from satellite imagery" badge
    age_source = 'user' if building_age_years is not None else 'unknown'
    age_confidence_years = None
    if building_age_years is None:
        # Path A: replacement_cost wrote the auto-detected age (requires BUA).
        rc = getattr(ev, 'replacement_cost', None)
        if rc:
            auto_age = getattr(rc, 'building_age_years', None)
            if auto_age and auto_age > 0:
                building_age_years = int(auto_age)
                age_source = 'gis_imagery'
                # Try to extract confidence from the construction report
                try:
                    report = getattr(ev, 'raw_property_report', None)
                    if isinstance(report, dict):
                        constr = report.get('construction') or {}
                        age_confidence_years = constr.get('confidence_years')
                    elif report is not None:
                        constr = getattr(report, 'construction', None)
                        if constr:
                            age_confidence_years = getattr(constr, 'confidence_years', None)
                except Exception:
                    pass

    # Sprint 2.15 (L4) — Path B fallback: when no BUA was provided,
    # replacement_cost is absent, but the smart imagery wrapper in
    # evaluate_property.py still populated report.construction. Surface
    # that to the response so the UI can show the "📡 detected from
    # satellite imagery" badge and the age-aware adjustments still apply.
    if building_age_years is None:
        try:
            from datetime import datetime as _dt
            report = getattr(ev, 'raw_property_report', None)
            constr = None
            if isinstance(report, dict):
                constr = report.get('construction')
            elif report is not None:
                constr = getattr(report, 'construction', None)
            if constr:
                ebt = (constr.get('earliest_built_year')
                       if isinstance(constr, dict)
                       else getattr(constr, 'earliest_built_year', None))
                ecy = (constr.get('confidence_years')
                       if isinstance(constr, dict)
                       else getattr(constr, 'confidence_years', None))
                if ebt:
                    derived_age = _dt.now().year - int(ebt)
                    if derived_age >= 0:
                        building_age_years = derived_age
                        age_source = 'gis_imagery'
                        age_confidence_years = ecy
        except Exception:
            pass

    eval_dict = asdict(ev) if hasattr(ev, '__dataclass_fields__') else ev.__dict__

    # ── Steps 1.5 + 2 + 7 — Parallelize 3 independent I/O-bound steps ──
    # All three consume `ev` but don't modify it or depend on each other:
    #   - geometric_factors: GIS landmark/HBU analysis (~3s network)
    #   - geo_v2:            geographic widening (~1.5s)
    #   - listings:          active listings fetch (~1.5s network)
    # Sequential total: ~6s. Parallel total: ~3s. Saves ~3 seconds.
    #
    # Sprint A.3+ optimization: critical for staying under Heroku's 30s timeout
    # on cold dyno + network overhead.

    def _run_geometric():
        if not _GEOMETRIC_OK:
            return None
        try:
            pin = None
            lat = lon = None
            rpr = getattr(ev, 'raw_property_report', None)
            if isinstance(rpr, dict):
                pin = rpr.get('pin')
                gps = rpr.get('gps')
                if gps and isinstance(gps, (list, tuple)) and len(gps) >= 2:
                    lon, lat = gps[0], gps[1]
            zoning_code = _extract_zoning_code(ev)
            if pin and lat and lon:
                return analyze_geometric_factors(int(pin), float(lat), float(lon), zoning_code)
        except Exception as e:
            print(f"[geometric] failed: {e}", file=sys.stderr)
        return None

    def _run_geo_widening():
        if not (use_geo_v2 and _GEO_OK):
            return None
        try:
            return _run_geo_v2(ev, moj_csv_path, pin=pin)   # Sprint 2.21.0: land/PIN
        except Exception as e:
            print(f"[geo_v2] failed: {e}", file=sys.stderr)
            return None

    def _run_listings_fetch():
        if not (use_listings and _LISTINGS_OK and ev.gis_district_aname):
            return None
        try:
            district = ev.gis_district_aname
            min_a = ev.plot_area_m2 * 0.80 if ev.plot_area_m2 else None
            max_a = ev.plot_area_m2 * 1.20 if ev.plot_area_m2 else None
            listings = fetch_active_listings(
                area=district,
                property_type='villa' if ev.asset_type in ('villa', 'standalone_villa') else 'all',
                min_area=min_a, max_area=max_a,
            )
            if not listings:
                return None
            res = weighted_listings_median(listings)
            res['sample'] = [
                {'location': l.get('location'), 'area_m2': l.get('area_m2'),
                 'price_m2': round(l.get('price_m2', 0)),
                 'age_days': l.get('age_days'), 'url': l.get('url')}
                for l in listings[:5]
            ]
            return res
        except Exception as e:
            print(f"[listings] failed: {e}", file=sys.stderr)
            return None

    # Fire all three in parallel
    with ThreadPoolExecutor(max_workers=3) as pool:
        f_geometric = pool.submit(_run_geometric)
        f_geo_v2 = pool.submit(_run_geo_widening)
        f_listings = pool.submit(_run_listings_fetch)
        try:
            geometric = f_geometric.result(timeout=18)
        except FutureTimeoutError:
            geometric = None
        try:
            geo_v2_result = f_geo_v2.result(timeout=18)
        except FutureTimeoutError:
            geo_v2_result = None
        try:
            listings_result = f_listings.result(timeout=18)
        except FutureTimeoutError:
            listings_result = None

    # ── Step 3: Select PRIMARY comparison value ──
    # b18 (§A1): a USER-claimed age is excluded from the a9 widened elasticity —
    # it renders as the age-sensitivity line instead of moving the headline.
    primary = _select_primary_comparison(ev, geo_v2_result,
                                         user_age=(age_source == 'user'))

    # ── Step 3.5 (Sprint 2.16.0): Stock Stratification ──
    # EMPIRICAL_FINDINGS Rule E4 — classify villa transactions by
    # villa/land ratio to surface land_priced / aging / modern / luxury_new
    # strata. Headline value unchanged; this is exposure-only.
    stock_strata = None
    if _STRATA_OK and ev.asset_type in ('standalone_villa', 'villa'):
        try:
            geo_primary = (geo_v2_result or {}).get('primary') or {}
            villa_txns = geo_primary.get('transactions') or []
            moj_names = set(geo_primary.get('moj_names') or [])
            if villa_txns and moj_names:
                _strata_rows = _get_moj_rows(moj_csv_path)
                # Discover the date column (NBSP-tolerant)
                _date_col = None
                if _strata_rows:
                    for _k in _strata_rows[0].keys():
                        _kn = ' '.join((_k or '').split())
                        if 'تاريخ' in _kn and 'تثبيت' in _kn:
                            _date_col = _k
                            break
                if _date_col:
                    stock_strata = build_stock_strata_result(
                        moj_rows=_strata_rows,
                        moj_area_names=moj_names,
                        villa_transactions=villa_txns,
                        plot_area_m2=getattr(ev, 'plot_area_m2', None),
                        listing_price=listing_price,
                        date_col=_date_col,
                    )
        except Exception as e:
            print(f"[stock_strata] failed: {e}", file=sys.stderr)
            stock_strata = None

    # ── Step 4: v3 layer — for income data, material uncertainty, brief ──
    # (NOT for blending — its blend_3way is ignored)
    v3_result = None
    if _V3_OK:
        rent_ref = _get_rent_ref(rent_ref_path)
        muni_hint = (
            getattr(ev, 'gis_municipality_aname', None)
            or getattr(ev, 'gis_municipality', None)
        )
        try:
            v3_result = evaluate_v3(
                zone=zone, street=street, building=building,
                rent_ref=rent_ref,
                audience=audience,
                listing_price=listing_price,
                v2_result=eval_dict,
                area_name=getattr(ev, 'gis_district_aname', None) or getattr(ev, 'moj_area_name', None),
                municipality=muni_hint,
            )
        except Exception as e:
            print(f"[v3] failed: {e}", file=sys.stderr)

    # ── Step 5: Build cross-checks (cost + income) — REBUILD income with user rent + correct cap ──
    cost = _build_cost_crosscheck(ev)

    v3_rent = v3_result.get('rent_reference') if v3_result else None
    income = _build_income_crosscheck(
        rental_income=rental_income,
        v3_rent_data=v3_rent,
        asset_type=ev.asset_type,
        primary_value=primary['value'] if primary else None,
        area_name=getattr(ev, 'gis_district_aname', None) or getattr(ev, 'moj_area_name', None),
        plot_area_m2=getattr(ev, 'plot_area_m2', None),
        stock_class=(stock_strata.get('dominant_stock_class')
                     if isinstance(stock_strata, dict) else None),
    )

    # ── Step 6: Reconciliation ──
    reconciliation = _analyze_reconciliation(primary, cost, income)

    # ── Step 7: Active listings — fetched in parallel block above ──

    # ── Step 8: Build unified output ──
    output = _build_unified_output(
        ev=ev,
        primary=primary,
        cost=cost,
        income=income,
        reconciliation=reconciliation,
        v3_result=v3_result,
        geo_v2_result=geo_v2_result,
        listings_result=listings_result,
        geometric=geometric,
        audience=audience,
        stock_strata=stock_strata,        # Sprint 2.16.0
        user_inputs={
            'listing_price': listing_price,
            'rental_income': rental_income,
            'floors': floors,
            'condition': condition,
            'annexes': annexes,
            'basement': basement,
            'footprint_m2': footprint_m2,
            'external_majlis': external_majlis,
            'building_age_years': building_age_years,
            'age_source': age_source,  # Sprint 2.5: shows if age came from user or GIS imagery
            'is_luxury': is_luxury,
        },
    )

    # ── Sprint 2.2 + 2.3: Age-Aware Building Substantiality Adjustment ──
    # Sprint 2.2 added a BUA-based substantiality adjustment (+20% for big
    # buildings, etc.). Sprint 2.3 makes it age-aware per the Qatar 10-Year
    # Rule (Sprint 2.3 strategic doc, section 4): old non-luxury villas
    # in Qatar trade close to land value regardless of BUA size, because
    # the market prefers demolish-and-rebuild over renovation.
    #
    # Multiplier matrix:
    #   age < 5         → 1.00 × Sprint 2.2 (new building, full uplift)
    #   age 5-10        → 0.85 × Sprint 2.2 (mid-age, mild dampening)
    #   age ≥ 10, lux   → 0.50 × Sprint 2.2 (old luxury, partial)
    #   age ≥ 10, std   → 0.00 × Sprint 2.2 (10-Year Rule: suppress)
    #   age unknown     → 1.00 × Sprint 2.2 + MU flag (caller's discretion)
    # Sprint 2.22.0b — zoning-driven footprint (computed for every villa/house
    # comparison path; surfaced below for the UI confirmable default).
    _zoning_code = _extract_zoning_code(ev)
    _zone_ceiling = _zone_max_coverage(_zoning_code)
    _suggested_fp = _suggested_footprint(_plot_area_for_bua, _zoning_code)
    _fp_confirmed = bool(footprint_m2 and footprint_m2 > 0)
    # Sprint 2.22.0b.2 — EFFECTIVE ground footprint actually used by the COMPARISON
    # driver, computed ONCE here (single source of truth) and reused by the
    # substantiality stage + the geometry surface (effective_footprint_m2), so the
    # surfaced value can NEVER drift from the value the engine used (brief F3):
    #   confirmed → user value, capped at the zone ceiling (anti-inflation, §5.2-B)
    #   assumed   → the conservative zoning suggestion (§4)
    if _fp_confirmed:
        _eff_fp = float(footprint_m2)
        if _plot_area_for_bua:
            _eff_fp = min(_eff_fp, _plot_area_for_bua * _zone_ceiling)
    else:
        _eff_fp = float(_suggested_fp) if _suggested_fp else None
    if (bua_breakdown is not None
            and output.get('valuation') and output['valuation'].get('amount')):
        try:
            # Above-ground comparison BUA: basement EXCLUDED (Gate-2 §5.5 — the
            # basement is captured/displayed + a future DRC input, NOT a
            # sales-comparison driver). The DISPLAY bua_breakdown (with basement,
            # for qar_per_m2_bua + DRC + capture) is left untouched.
            _subst_bua = _build_smart_bua(
                plot_area_m2=_plot_area_for_bua,
                floors=floors,
                annexes=annexes,
                basement=False,
                footprint_m2=_eff_fp,
                external_majlis=external_majlis,
            ) or bua_breakdown
            substantiality = _building_substantiality(_subst_bua, _plot_area_for_bua)
            raw_adj_pct = max(0.0, substantiality.get('adjustment_pct', 0.0))

            # Sprint 2.3: modulate by age regime
            age_mult, regime = _age_aware_substantiality_multiplier(
                building_age_years, is_luxury
            )
            adj_pct = raw_adj_pct * age_mult

            if adj_pct > 0:
                base_amount = output['valuation']['amount']
                base_low = output['valuation'].get('low') or base_amount * 0.85
                base_high = output['valuation'].get('high') or base_amount * 1.15

                output['valuation']['amount'] = _r100k(base_amount * (1 + adj_pct))
                output['valuation']['low'] = _r100k(base_low * (1 + adj_pct * 0.7))
                output['valuation']['high'] = _r100k(base_high * (1 + adj_pct * 1.1))

            # Build regime-aware methodology note
            if regime == 'qatar_10_year_rule':
                method_note = _ten_year_rule_disclosure_ar(building_age_years, primary.get('n') if primary else None)
                # Sprint 2.22.0a.3 T1.4: regime label reframed from
                # named "rule" to observed pattern (epistemic humility).
                # Internal regime key 'qatar_10_year_rule' unchanged.
                # Post-validation fold (Rule #54): short descriptive tag
                # — no 'قاعدة', no 'عبء' (both AIs flagged the latter).
                regime_label_ar = 'نمط سوقي: غلبة قيمة الأرض في العقارات القديمة'
            elif regime == 'old_luxury_building':
                method_note = _luxury_old_disclosure_ar(building_age_years)
                regime_label_ar = 'بناء قديم فاخر — تعديل جزئي'
            elif regime == 'mid_age_building':
                method_note = (
                    f'العقار متوسط العمر ({building_age_years} سنة). تم تطبيق '
                    f'85% من التعديل المعتاد لكثافة البناء لمراعاة استهلاك المبنى.'
                )
                regime_label_ar = 'بناء متوسط العمر — تعديل مخفّض'
            elif regime == 'new_building':
                method_note = (
                    f'العقار جديد ({building_age_years} سنة). تم تطبيق التعديل '
                    f'الكامل لكثافة البناء لأن البناء يضيف قيمة سوقية واضحة.'
                )
                regime_label_ar = 'بناء جديد — تعديل كامل'
            else:  # unknown_age
                method_note = (
                    'وزارة العدل تسجّل ثمن الصفقة لكن لا تسجّل تفاصيل البناء. '
                    'عمر البناء غير مُقدَّم — تم تطبيق التعديل افتراضياً لكن قد '
                    'يكون مبالغاً فيه للمباني الأقدم من 10 سنوات. أدخل العمر '
                    'التقديري لتقييم أدق.'
                ) if raw_adj_pct > 0 else 'البناء ضمن النطاق النموذجي.'
                regime_label_ar = 'عمر غير معلوم — تطبيق افتراضي'

            # Sprint 2.5: append auto-detection note when age came from GIS
            if age_source == 'gis_imagery':
                conf_part = (
                    f' (دقة ±{age_confidence_years} سنة)'
                    if age_confidence_years else ''
                )
                method_note += (
                    f'\n\nملاحظة: عمر البناء ({building_age_years} سنة) تم استخراجه '
                    f'تلقائياً من تحليل صور الأقمار الصناعية التاريخية{conf_part}. '
                    f'لو كنت تعرف العمر الفعلي، أدخله يدوياً للحصول على دقة أعلى.'
                )

            output['valuation']['building_substantiality'] = {
                'index': substantiality['index'],
                'typical_bua_m2': substantiality['typical_bua'],
                'actual_bua_m2': substantiality['actual_bua'],
                'raw_adjustment_pct': round(raw_adj_pct * 100, 1),
                'age_multiplier': age_mult,
                'adjustment_pct': round(adj_pct * 100, 1),
                'age_regime': regime,
                'age_regime_label_ar': regime_label_ar,
                'building_age_years': building_age_years,
                'age_source': age_source,                    # Sprint 2.5: 'user' | 'gis_imagery' | 'unknown'
                'age_confidence_years': age_confidence_years, # Sprint 2.5: ± years (from satellite imagery)
                'is_luxury': is_luxury,
                'rationale_ar': substantiality['rationale'],
                'methodology_note_ar': method_note,
            }
        except Exception as e:
            import sys
            print(f'[substantiality warning] {e}', file=sys.stderr)

    # ── Sprint 2.22.0b — surface the zoning footprint suggestion (UI default) ──
    # Additive: lets the UI prefill an editable, confirmable footprint and
    # disclose the assumed-vs-confirmed basis (§4/§5.2) + that the basement is
    # NOT a comparison driver (§5.5). Does NOT change valuation.amount.
    if _plot_area_for_bua and _suggested_fp and output.get('valuation'):
        # Sprint 2.22.0b.10 — max-buildable footprint from plot dims − legal R1
        # setbacks (DISPLAY/CONFIRM ONLY; recon D1 — NEVER touches _suggested_fp /
        # _eff_fp / substantiality / valuation.amount). Reuses the already-fetched
        # plot polygon → zero new GIS.
        _geom_fp = None
        try:
            _poly = getattr(_plot, 'polygon_2932', None) if _plot is not None else None
            _shape = getattr(_plot, 'shape', None) if _plot is not None else None
            # Sprint 2.22.0b.10.2 — multi-QARS shared plot: ONE villa sits on the
            # per-villa share (effective_per_villa), NOT the whole cadastral parcel.
            # Pass the share so the footprint is computed on it (the value side
            # already brackets on it; the footprint must too — else a 2-villa 900m²
            # plot shows ~528m² when one villa is ~270m²).
            _mq = getattr(ev, 'multi_qars', None) if ev is not None else None
            _villa_share = (_mq.get('effective_per_villa')
                            if (_mq and (_mq.get('n_qars') or 0) >= 2) else None)
            if _poly and _shape is not None:
                _geom_fp = _geometry_footprint(
                    _poly, _plot_area_for_bua,
                    bool(getattr(_shape, 'is_rectangular', False)),
                    _zone_ceiling,
                    shared_effective_area=_villa_share,
                )
        except Exception:
            _geom_fp = None
            _mq = None
        output['valuation']['geometry'] = {
            'zoning_code': _zoning_code,
            'zone_max_coverage_pct': round(_zone_ceiling * 100),
            'suggested_footprint_m2': _suggested_fp,
            # Sprint 2.22.0b.2 (brief F3): the post-cap footprint the comparison
            # ACTUALLY used (confirmed → capped user value; assumed → == suggestion).
            # Lets the UI show the effective figure + disclose the zone cap, instead
            # of echoing an uncapped input the engine never used (derive-don't-author).
            'effective_footprint_m2': (round(_eff_fp) if _eff_fp is not None else None),
            'footprint_basis': 'confirmed' if _fp_confirmed else 'assumed',
            'basement_in_comparison': False,
            # Sprint 2.22.0b.10 — geometry-derived MAX-buildable footprint (DISPLAY):
            # the legal ceiling from plot dims − setbacks; the user corrects DOWN.
            'plot_dims_m': (_geom_fp or {}).get('plot_dims_m'),
            'max_buildable_footprint_m2': (_geom_fp or {}).get('max_buildable_footprint_m2'),
            'footprint_method': (_geom_fp or {}).get('method'),
            # Sprint 2.22.0b.10.2 — multi-QARS shared plot: surface the per-villa
            # share the footprint was computed on + the unit count, for disclosure.
            'effective_share_m2': (_geom_fp or {}).get('effective_share_m2'),
            'n_share': ((_mq.get('n_qars') if _mq else None)
                        if (_geom_fp or {}).get('method') == 'coverage_cap_shared' else None),
            'note_ar': (
                ('هذه القطعة مشتركة بين عدّة وحدات؛ مساحة البناء الأرضي محسوبة على '
                 'الحصة الفعلية للوحدة (≈ '
                 + str((_geom_fp or {}).get('effective_share_m2') or '') +
                 ' م²) كحدّ أقصى — عدّلها لواقع مبناك.')
                if (not _fp_confirmed and _geom_fp
                    and _geom_fp.get('method') == 'coverage_cap_shared')
                else (
                    'المساحة المعروضة هي الحدّ الأقصى المسموح للبناء، محسوبة من أبعاد '
                    'قطعتك مطروحاً منها الارتدادات النظامية — عدّلها لواقع مبناك '
                    '(البناء الفعلي عادةً أصغر).'
                    if (not _fp_confirmed and _geom_fp
                        and _geom_fp.get('method') == 'setback_envelope')
                    else (
                        'مساحة البناء الأرضية المعروضة تقديرية، مبنية على حدّ التغطية '
                        'النظامي للمنطقة — عدّلها إن كنت تعرف المساحة الفعلية لتدقيق التقدير.'
                        if not _fp_confirmed else
                        'تم اعتماد مساحة البناء الأرضية التي أدخلتها.'
                    )
                )
            ),
        }

    # ── Sprint 2.22.0b (§5.2/ج) — disclose ASSUMED geometry in Material Uncertainty ──
    # When the comparison used a zoning-suggested (not user-confirmed) footprint,
    # widen the disclosure so confidence/range reflect the assumption. Confirmed
    # geometry → no caveat → tighter basis.
    if (bua_breakdown is not None and not _fp_confirmed
            and output.get('material_uncertainty')):
        try:
            _mu_g = output['material_uncertainty']
            _fp_unknown = (
                'مساحة البناء الأرضية المستخدمة في المقارنة تقديرية (مبنية على '
                'حدّ التغطية النظامي للمنطقة) وليست مؤكَّدة — تأكيدها قد يعدّل التقدير.'
            )
            _mu_u = list(_mu_g.get('known_unknowns') or [])
            if not any('مساحة البناء الأرضية' in u for u in _mu_u):
                _mu_u.insert(0, _fp_unknown)
                _mu_g['known_unknowns'] = _mu_u
            output['material_uncertainty'] = _mu_g
        except Exception as e:
            import sys
            print(f'[geometry MU warning] {e}', file=sys.stderr)

    # ── Sprint 2.2: Flag missing building details in Material Uncertainty ──
    # Sprint 2.21.0.7 (P4): a bare-land parcel has no building, so the
    # "building details not provided / assumes a typical building" factor is
    # nonsensical and leaked onto raw_land reports (bua_breakdown is always None
    # for land). Sprint 2.21.0.5 fixed the assess_uncertainty factors but NOT
    # this separate injection point. Guard it: skip for raw_land/land.
    _p4_at = (output.get('asset_type') or '').lower()
    if (bua_breakdown is None and output.get('material_uncertainty')
            and _p4_at not in ('raw_land', 'land')):
        try:
            mu = output['material_uncertainty']
            # Sprint 2.22.0a.3 T2.5: drop "±20-40%" quantitative range —
            # no calibration study backs it.
            # Post-validation fold (Rule #54): GPT pushed to replace
            # vague "بشكل ملحوظ" with causal+specific framing — name
            # the inputs that would move the estimate (condition, exact
            # area, finishes). Pairs with T1.1: T1.1 dropped the
            # fabricated condition claim; T2.5 here names condition
            # as exactly what would refine the estimate if provided.
            # Pure Arabic — em-dashes between Arabic words, no LRM needed.
            building_unknown_factor = (
                'قد يؤدي إدخال التفاصيل الفعلية للعقار — '
                'كالحالة والمساحة الدقيقة والتشطيبات — '
                'إلى تعديل جوهري في التقدير.'
            )
            building_unknown_unknown = (
                'مكوّنات البناء الفعلية (سرداب، طوابق، مجلس خارجي، حالة التشطيب)'
            )
            mu_factors = list(mu.get('factors') or [])
            if not any('تفاصيل البناء غير' in f for f in mu_factors):
                mu_factors.insert(0, building_unknown_factor)
                mu['factors'] = mu_factors
            mu_unknowns = list(mu.get('known_unknowns') or [])
            if not any('مكوّنات البناء' in u for u in mu_unknowns):
                mu_unknowns.insert(0, building_unknown_unknown)
                mu['known_unknowns'] = mu_unknowns
            mu_recs = list(mu.get('recommendations') or [])
            rec_text = 'أدخل تفاصيل العقار (طوابق، سرداب، حالة) للحصول على تقييم أدق'
            if not any('تفاصيل العقار' in r for r in mu_recs):
                mu_recs.insert(0, rec_text)
                mu['recommendations'] = mu_recs
            output['material_uncertainty'] = mu
        except Exception as e:
            import sys
            print(f'[MU enhancement warning] {e}', file=sys.stderr)

    # ── Sprint 2.6: Land vs Building Value Decomposition ──
    # Empirically validates the Qatar 10-Year Rule by separating land value
    # (from MoJ land-only sales in the area) from implied building value
    # (residual = total − land). Old non-luxury villas show <5% building
    # contribution; new/luxury villas show 25-45%.
    # Sprint 2.21.0.5 (Issue 3): a bare-land parcel has NO building, so the
    # residual "building value" is meaningless (was rendering "بناء −3.5%"). Skip
    # the decomposition for land and show a plain note instead. Buildings/villas
    # keep the decomposition unchanged (regression-safe).
    _out_at = (output.get('asset_type') or '').lower()
    if _out_at in ('raw_land', 'land'):
        if output.get('valuation'):
            output['valuation']['value_decomposition_note_ar'] = (
                'هذه قطعة أرض فضاء — التقييم على قيمة الأرض المنفصلة فقط. '
                'لا توجد قيمة بناء يحسبها هذا التقييم.'
            )
            # Sprint 2.22.0b.20 (three-value stack, land leg): for bare land the DRC
            # degenerates to the land value itself — one disclosed line, no separate math
            # (BRIEF_conditional_leadership_SIGNED §2; Phase-0 §1.2 confirmed).
            output['valuation']['cost_note_ar'] = (
                'قيمة التكلفة (نهج DRC) ≡ قيمة الأرض — لا مكوّن بناء لقطعة فضاء.')
            output['valuation']['cost_note_en'] = (
                'Cost value (DRC) ≡ the land value — no building component on bare land.')
    elif (output.get('valuation') and output['valuation'].get('amount')
            and getattr(ev, 'plot_area_m2', None)):
        try:
            # Sprint 2.6: prefer the new ev.moj_reference field
            moj_ref = (getattr(ev, 'moj_reference', None)
                       or getattr(ev, 'moj_ref_dict', None)
                       or getattr(ev, 'raw_moj_reference', None))
            if not moj_ref and v3_result:
                moj_ref = v3_result.get('moj_reference')
            # Last resort: try to extract from cost approach which already pulled land data
            if not moj_ref and cost and cost.get('land_value') and ev.plot_area_m2:
                # Synthesize minimal ref from cost approach (loses n_transactions)
                land_per_m2_inferred = cost['land_value'] / ev.plot_area_m2
                moj_ref = {'categories': {'land': {
                    'price_per_m2': {'median': land_per_m2_inferred},
                    'n': 0,  # unknown — will fail the n>=3 check unless we relax it
                    'window_months': 24,
                    'reliable': False,
                }}}

            # Get BUA for per-m² building stats
            bua = None
            if cost and cost.get('bua_m2'):
                bua = cost['bua_m2']
            else:
                rc = getattr(ev, 'replacement_cost', None)
                if rc:
                    bua = getattr(rc, 'bua_m2', None)

            decomp = _decompose_value(
                valuation_amount=output['valuation']['amount'],
                plot_area_m2=ev.plot_area_m2,
                bua_m2=bua,
                moj_ref_dict=moj_ref,
            )
            if decomp:
                output['valuation']['value_decomposition'] = decomp
                # ── Sprint 2.22.0b.14 (ISS-A07): decomposition ↔ 10-Year/stratum coherence ──
                # VALUE-INVARIANT post-pass — `output` already carries stock_strata +
                # property_basis (from _build_unified_output above); this rewrites ONLY the
                # implied-building narrative TEXT so the decomposition agrees with the
                # 10-Year/stratum panel (BRIEF §2). Never raises (helper is try/except-wrapped).
                _reconcile_decomposition_narrative(output)
            # ── Sprint 2.22.0a.21 (B-1): land-floor / HBU decomposition surface ──
            # PRESENTATION ONLY — value-invariant. Rides the a17/a19 condition gate
            # (_condition_note_applies) so the floor + the live condition_note are ONE
            # coherent villa/house surface. F1: surfaces even when _decompose_value
            # suppressed `decomp` (land ≥ value) by recomputing from the same moj_ref.
            try:
                _g_vf = _stage1_dispersion_gate(primary, geo_v2_result)
                _amt_vf = output['valuation'].get('amount')
                if _condition_note_applies(primary, _g_vf, output.get('asset_type'), _amt_vf):
                    _vf = _villa_value_floor(_amt_vf, getattr(ev, 'plot_area_m2', None), moj_ref, decomp)
                    if _vf:
                        output['valuation']['value_floor'] = _vf
                        _inject_value_floor_into_brief(output.get('brief'), _vf)
            except Exception as _e:
                import sys
                print(f'[value_floor warning] {_e}', file=sys.stderr)
            # ── Sprint 2.22.0b.12 (Bug A15): HBU not-evaluated disclosure (value-invariant) ──
            # Co-located with the B-1 value_floor; fires ONLY when the zoning layer was
            # unavailable (HBU silently skipped). Never raises into the evaluate path.
            try:
                if _hbu_note_applies(primary,
                                     _stage1_dispersion_gate(primary, geo_v2_result),
                                     output.get('asset_type'),
                                     output['valuation'].get('amount'),
                                     _extract_zoning_code(ev)):
                    output['valuation']['hbu_note_ar'] = _HBU_NOTE_AR
                    output['valuation']['hbu_note_en'] = _HBU_NOTE_EN
            except Exception as _e:
                import sys
                print(f'[hbu_note warning] {_e}', file=sys.stderr)
            # ── Sprint 2.22.0b.4 (B-2a): teardown re-anchor (Gate-2 — MOVES the headline) ──
            # Opt-in ONLY (condition='teardown'); villa/house only; never auto-detected
            # (E17 — broker states, engine values). Reuses the shipped _villa_value_floor
            # (land floor, n≥20): value = land_floor − demolition. Swallows errors so a
            # teardown edge can never break the evaluate path.
            try:
                if (condition or '').strip().lower() == 'teardown' \
                        and output.get('asset_type') in _TEARDOWN_ASSET_TYPES \
                        and output['valuation'].get('amount'):
                    _vf_td = _villa_value_floor(output['valuation']['amount'],
                                                getattr(ev, 'plot_area_m2', None), moj_ref, decomp)
                    if _vf_td and _vf_td.get('land_floor'):
                        _lf_td = _vf_td['land_floor']
                        _bua_td = bua or ((getattr(ev, 'plot_area_m2', 0) or 0) * TYPICAL_COVERAGE)
                        _demo_td = min(max(round(DEMO_QAR_PER_M2 * (_bua_td or 0)), DEMO_FLOOR_QAR), DEMO_CAP_QAR)
                        _central_td = max(_lf_td - _demo_td, 0)
                        output['valuation']['amount'] = _r100k(_central_td)
                        output['valuation']['low'] = _r100k(max(round(_central_td * 0.88), 0))
                        output['valuation']['high'] = _r100k(_lf_td)
                        output['valuation']['teardown'] = {
                            'applied': True,
                            'land_floor': _lf_td,
                            'demolition_cost': _demo_td,
                            'demolition_per_m2': DEMO_QAR_PER_M2,
                            'bua_m2': round(_bua_td or 0),
                            'note_ar': TEARDOWN_NOTE_AR.format(land=f'{_r10k(_lf_td):,}', demo=f'{_demo_td:,}'),
                            'note_en': TEARDOWN_NOTE_EN.format(land=f'{_r10k(_lf_td):,}', demo=f'{_demo_td:,}'),
                        }
                        _mu_td = output.get('material_uncertainty')
                        if isinstance(_mu_td, dict):
                            _mu_td['level'] = 'high'
            except Exception as _et:
                import sys
                print(f'[teardown warning] {_et}', file=sys.stderr)
            # ── Sprint 2.22.0b.4 (B-2b): luxury-new premium (Lever-1 — MOVES the headline UP) ──
            # Opt-in (is_luxury + new); villa/house; MUTUALLY EXCLUSIVE with teardown. Calibrated
            # on V002/V003 (+67% observed → +60% applied, conservative). Swallows errors.
            try:
                _cl = (condition or '').strip().lower()
                _is_new_l = _cl == 'new' or (isinstance(building_age_years, int) and 0 <= building_age_years < 5)
                if is_luxury and _is_new_l and _cl != 'teardown' \
                        and output.get('asset_type') in _TEARDOWN_ASSET_TYPES \
                        and output['valuation'].get('amount') \
                        and not output['valuation'].get('teardown'):
                    _vf_l = _villa_value_floor(output['valuation']['amount'],
                                               getattr(ev, 'plot_area_m2', None), moj_ref, decomp)
                    _lf_l = (_vf_l or {}).get('land_floor')
                    _plot_l = getattr(ev, 'plot_area_m2', 0) or 0
                    if _lf_l and _plot_l > 0:
                        # FULL zone coverage (luxury builds to the ceiling, not b1's ×0.8); user footprint wins.
                        _geo_l = output['valuation'].get('geometry') or {}
                        _cov_l = (_geo_l.get('zone_max_coverage_pct') or 60) / 100.0
                        _fp_l = footprint_m2 or (_plot_l * _cov_l)
                        # BUA = footprint × (floors + penthouse-half). Default for a luxury new-build =
                        # ground + first + penthouse (×2.5, the V002/V003 shape); user floors/penthouse refine.
                        _floors_l = floors or 2
                        _pent_l = 0.0 if penthouse is False else 0.5
                        _bua_l = round(_fp_l * (_floors_l + _pent_l))
                        _bld_l = round(_bua_l * LUXURY_CONSTRUCTION_QAR_PER_M2)
                        _val_l = _lf_l + _bld_l
                        output['valuation']['amount'] = _r100k(_val_l)
                        output['valuation']['low'] = _r100k(_val_l * 0.85)
                        output['valuation']['high'] = _r100k(_val_l * 1.08)
                        output['valuation']['luxury_new_premium'] = {
                            'applied': True,
                            'method': 'cost_approach_drc',
                            'land_floor': _lf_l,
                            'building_value': _bld_l,
                            'bua_m2': _bua_l,
                            'construction_qar_per_m2': LUXURY_CONSTRUCTION_QAR_PER_M2,
                            'note_ar': LUXURY_NEW_NOTE_AR.format(land=f'{_r10k(_lf_l):,}', bld=f'{_r10k(_bld_l):,}', bua=_bua_l, cost=LUXURY_CONSTRUCTION_QAR_PER_M2),
                            'note_en': LUXURY_NEW_NOTE_EN.format(land=f'{_r10k(_lf_l):,}', bld=f'{_r10k(_bld_l):,}', bua=_bua_l, cost=LUXURY_CONSTRUCTION_QAR_PER_M2),
                        }
                        _mu_l = output.get('material_uncertainty')
                        if isinstance(_mu_l, dict):
                            _mu_l['level'] = 'high'
            except Exception as _el:
                import sys
                print(f'[luxury_new warning] {_el}', file=sys.stderr)
            # ── Sprint §6 (R7): income-triangulation (Gate-2 — income LEADS / honest-widen) ──
            # Mutually exclusive with the b4 teardown + luxury-new overrides (explicit
            # statements win). Reuses _villa_value_floor (land floor = clamp / widen target)
            # + _stage1_dispersion_gate (defer dispersed pools to a10/a14). Swallows errors.
            try:
                if (output['valuation'].get('amount')
                        and not output['valuation'].get('teardown')
                        and not output['valuation'].get('luxury_new_premium')):
                    _lf_tri = (_villa_value_floor(output['valuation']['amount'],
                                                  getattr(ev, 'plot_area_m2', None),
                                                  moj_ref, decomp) or {}).get('land_floor')
                    _g_tri = _stage1_dispersion_gate(primary, geo_v2_result)
                    # Sprint 2.22.0b.21 (E26 / INV-3): the rail's ceiling is age-neutralized
                    # when the age is USER-claimed — see _age_neutral_rail_cost.
                    _tri = _income_triangulation(
                        primary, income, _age_neutral_rail_cost(cost, age_source),
                        _lf_tri, output.get('asset_type'),
                        dispersion_gated=bool(_g_tri and _g_tri.get('gated')))
                    # ── Sprint §20.9 (R7) cost-approach DOWN-re-anchor (SHIP-NOW slice) ──
                    # An independent DRC cost (land_floor + a depreciated building, from the b9
                    # SYSTEM age + the b10 footprint) re-anchors a thin/widened OVER-anchor DOWN
                    # with the COST as the informed floor (vs §6 widen_down's bare land). Preferred
                    # over widen_down when it fires; income_led (a grounded subject rent) still wins.
                    # b9 system age is a FLOOR → conservative (immune to the CGIS-vs-actual bias —
                    # METHODOLOGY_DRC_qatar_v1 §11); convergent-confirm + the UP-lift are GATED-to-next.
                    _geom_ct = output['valuation'].get('geometry') or {}
                    _age_ct = ((output.get('property_basis') or {}).get('building_age_estimate') or {}).get('age_floor_years')
                    _eff_ct = (output['valuation'].get('effective_footprint_m2')
                               if output['valuation'].get('footprint_basis') == 'confirmed' else None)
                    _cost_av = _cost_approach_value(
                        _lf_tri, _geom_ct.get('max_buildable_footprint_m2'), floors,
                        ('luxury' if is_luxury else 'ordinary'), _age_ct, condition,
                        footprint_actual=_eff_ct)
                    # Sprint 2.22.0b.20: the b11 `_cost_triangulation` branch-decider call is
                    # RETIRED — its trigger set lands in the leadership gate's else-branch
                    # (the §3.1 subsumption map). The pure fn is kept above as a calculator.
                    # ── Sprint 2.22.0b.13 (Lever 1): convergent-TRIM (actual-age cost LEADS) ──
                    # USER-supplied actual age ONLY (recon R1): age_source=='user'; effective age =
                    # max(user, system) so a user age younger than the system floor can't raise retention.
                    # DISJOINT from the reanchor above (≤30% actual vs >30% system). Lever 2 (lift) DROPPED
                    # by the Phase-0 recon (DRC cost < the V002/V003 sale → that under-anchor is B-2, not cost).
                    _ct_trim = None
                    if age_source == 'user' and building_age_years is not None:
                        _eff_trim = max(int(building_age_years), _age_ct or 0)
                        _cost_av_act = _cost_approach_value(
                            _lf_tri, _geom_ct.get('max_buildable_footprint_m2'), floors,
                            ('luxury' if is_luxury else 'ordinary'), _eff_trim, condition,
                            footprint_actual=_eff_ct)
                        _ct_trim = _cost_trim(
                            primary, _cost_av_act, _lf_tri, output.get('asset_type'),
                            bool(_g_tri and _g_tri.get('gated')), _eff_trim)
                    # ── Sprint 2.22.0b.20: gate-input assembly (the b16 `_old_stock_reanchor`
                    # branch is RETIRED — its basis pool must now pass RULE 2's reliable bar;
                    # the pure fn is kept above as a superseded calculator). output already
                    # carries stock_strata + property_basis; moj_ref carries subject_geo_full
                    # (now with `dispersion_full` — Sprint b20 additive). ──
                    _gate = None
                    try:
                        _pb20 = ((output.get('property_basis') or {})
                                 .get('building_age_estimate') or {})
                        _band20 = _e26_subject_band(_pb20.get('age_floor_years'),
                                                    _pb20.get('age_basis'))
                        _resurvey20 = (_pb20.get('age_basis') == 'vintage_capped'
                                       and (_pb20.get('age_floor_years') or 0) < 2)
                        _ss20 = output.get('stock_strata') or {}
                        _dom20 = ((_ss20.get('dominant_stratum') or {}).get('name')
                                  if isinstance(_ss20.get('dominant_stratum'), dict) else None)
                        _domshare20 = ((_ss20.get('dominant_stratum') or {}).get('share_pct')
                                       if isinstance(_ss20.get('dominant_stratum'), dict) else None)
                        _mn20 = _matched_stratum_n(_ss20.get('strata'), _band20)
                        _match20 = (None if (_band20 is None or not _dom20)
                                    else (_dom20 in _LEAD_BAND_STRATA.get(_band20, ())))
                        _eff20 = (_geom_ct.get('effective_share_m2')
                                  or getattr(ev, 'plot_area_m2', None))
                        _disp20, _dispn20 = _bracket_disp36(moj_ref, _eff20)
                        _sgf20 = (moj_ref or {}).get('subject_geo_full')
                        _gate = _leadership_gate(
                            output['valuation']['amount'], output.get('asset_type'),
                            _mn20, _disp20, _match20, _band20, _resurvey20,
                            _sgf20, _cost_av, _lf_tri)
                    except Exception:
                        _gate = None
                    if _tri and _tri['mode'] == 'income_led':
                        _capp = (round(_tri['cap_rate'] * 100, 1) if _tri['cap_rate'] else '—')
                        _xs = f"{_r10k(_tri['amount']):,}"
                        _cs = f"{_r10k(_tri['comparison_value']):,}"
                        output['valuation']['amount'] = _r100k(_tri['amount'])
                        output['valuation']['low'] = _r100k(_tri['low'])
                        output['valuation']['high'] = _r100k(_tri['high'])
                        # income LEADS → the income band is the range; clear any dispersion
                        # range-flag (a10/a14) so its built-type disclosure doesn't linger.
                        output['valuation'].pop('range_is_headline', None)
                        _note_ar = INCOME_LED_NOTE_AR.format(
                            cap=_capp, n=_tri['sample_size'], conf=_tri['confidence'],
                            x=_xs, comp=_cs)
                        _note_en = INCOME_LED_NOTE_EN.format(
                            cap=_capp, n=_tri['sample_size'], conf=_tri['confidence'],
                            x=_xs, comp=_cs)
                        if _tri.get('bracket_borrowed'):
                            _bb = _tri.get('borrowed_from_bracket')
                            _note_ar += (f' (معدل العائد مُستعار من شريحة {_bb} م² للمنطقة '
                                         f'نفسها — العائد الصافي مستقر عبر شرائح المنطقة الواحدة.)')
                            _note_en += (f' (Yield borrowed from the area’s {_bb} m² bracket — '
                                         f'net yields are stable across brackets within an area.)')
                        output['valuation']['income_triangulation'] = {
                            'mode': 'income_led',
                            'income_value': _tri['amount'],
                            'comparison_value': _tri['comparison_value'],
                            'spread_pct': _tri['spread_pct'],
                            'cap_rate': _tri['cap_rate'],
                            'net_yield_pct': _tri['net_yield_pct'],
                            'sample_size': _tri['sample_size'],
                            'confidence': _tri['confidence'],
                            'bracket_borrowed': bool(_tri.get('bracket_borrowed')),
                            'borrowed_from_bracket': _tri.get('borrowed_from_bracket'),
                            'note_ar': _note_ar,
                            'note_en': _note_en,
                        }
                        _mu_tri = output.get('material_uncertainty')
                        if isinstance(_mu_tri, dict):
                            _mu_tri['level'] = _tri['muc_level']
                        # ── Sprint 2.22.0b.67 (T0-2): ISS-A07 coherence on income_led ──
                        # income LEADS — line 5006 overrode the central with the income
                        # figure via a NON-comparison method, so the value_decomposition +
                        # B-1 value_floor built earlier (4797-4822) on the PRE-income
                        # COMPARISON amount are now STALE (they'd render a land/building split
                        # summing to the discarded comparison figure under the income headline
                        # — internal incoherence). Recompute BOTH on the income amount. This is
                        # the VERBATIM proven cost_led recompute (5138-5153, the b16 ISS-A07
                        # pattern); same helpers + `bua`/`moj_ref`/`ev.plot_area_m2` in scope.
                        # Value-invariant on amount/low/high (already set above; additive).
                        try:
                            _decompI = _decompose_value(
                                valuation_amount=output['valuation']['amount'],
                                plot_area_m2=ev.plot_area_m2, bua_m2=bua,
                                moj_ref_dict=moj_ref)
                            if _decompI:
                                output['valuation']['value_decomposition'] = _decompI
                                _reconcile_decomposition_narrative(output)
                            _vfI = _villa_value_floor(
                                output['valuation']['amount'],
                                getattr(ev, 'plot_area_m2', None), moj_ref, _decompI)
                            if _vfI:
                                output['valuation']['value_floor'] = _vfI
                                _inject_value_floor_into_brief(output.get('brief'), _vfI)
                        except Exception:
                            pass
                        # ── Sprint 2.22.0b.69 (T0-2 completeness): income leadership + value_stack ──
                        # The COMPLETENESS half of T0-2 (b67 closed the COHERENCE half). Emit a minimal
                        # leadership{leader='income'} + value_stack so the FULL report renders the leader
                        # verdict note + the DEF-12 cost row on income_led (previously OMITTED — weaker
                        # than every other leader path). leader='income' keeps b64 #4's cost-basis hero
                        # line OFF (it keys on 'cost'); note_ar/_en REUSE the already-built income note
                        # (5012-5023) → zero new copy + value-invariant text; market.median = the demoted
                        # comparison (NOT the headline). The leadership object OMITS the market-evidence
                        # fields (matched_n/dispersion/band/geo_full/thresholds) — those justify a MARKET
                        # verdict, not an income one. The DEF-12 central stays v.amount (income headline).
                        # ADDITIVE only — amount/low/high/method/rule untouched (value-invariant headline).
                        try:
                            if _cost_av:
                                _stack_cost_i = {
                                    'label_ar': COST_STACK_LABEL_AR,
                                    'label_en': COST_STACK_LABEL_EN,
                                    'sub_ar': COST_STACK_SUB_AR,
                                    'sub_en': COST_STACK_SUB_EN,
                                    'value': _cost_av['value'],
                                    'land_floor': _cost_av['land_floor'],
                                    'building_value': _cost_av['building_value'],
                                    'bua_m2': _cost_av['bua_m2'],
                                    'rcn_qar_per_m2': _cost_av['rcn_qar_per_m2'],
                                    'retention': _cost_av['retention'],
                                    'effective_age': _cost_av['effective_age'],
                                    'finish': _cost_av['finish'],
                                    'assumptions_ar': ('افتراضات: تشطيب {f} · معامل احتفاظ {r} · '
                                                       'عمر النظام (CGIS) أساس الاحتساب (E26)'
                                                       ).format(f=_cost_av['finish'],
                                                                r=_cost_av['retention']),
                                    'assumptions_en': ('Assumptions: finish {f} · retention factor {r} · '  # b87
                                                       'system (CGIS) age is the basis (E26)'
                                                       ).format(f=_cost_av['finish'],
                                                                r=_cost_av['retention']),
                                }
                            else:
                                _stack_cost_i = {'unavailable_reason_ar': None}
                            output['valuation']['value_stack'] = {
                                'market': {
                                    'median': _tri['comparison_value'],
                                    'n': output['valuation'].get('n_transactions'),
                                },
                                'cost': _stack_cost_i,
                                'income_available': True,
                            }
                            output['valuation']['leadership'] = {
                                'leader': 'income', 'rule': 'income_led',
                                'income_value': _tri['amount'],
                                'market_value': _tri['comparison_value'],
                                'cost_value': (_cost_av['value'] if _cost_av else None),
                                'cap_rate': _tri['cap_rate'],
                                'net_yield_pct': _tri['net_yield_pct'],
                                'sample_size': _tri['sample_size'],
                                'confidence': _tri['confidence'],
                                'note_ar': _note_ar,
                                'note_en': _note_en,
                            }
                        except Exception:
                            pass
                    else:
                        # ── Sprint 2.22.0b.20: EVIDENCE-CONDITIONAL LEADERSHIP application ──
                        # Replaces the retired b11 cost_reanchor_down / b16 OSR / b6 widen_down
                        # elif chain (BRIEF_conditional_leadership_SIGNED §3.1 — one decision
                        # point, no double-fire). income_led above keeps absolute precedence;
                        # the _tri 'widen_down' mode is IGNORED (subsumed by the else-branch).
                        if _gate:
                            _mkt20 = output['valuation']['amount']   # the pre-gate market figure
                            _cv20 = _gate.get('cost_value')
                            _d20 = ('غير متاح' if _gate.get('dispersion_36') is None
                                    else f"{_gate['dispersion_36']:.3f}")
                            _n20 = (_gate.get('matched_n')
                                    if _gate.get('matched_n') is not None else 'غير متاح')
                            # ── the three-value stack (G1: the DRC was always computed — now
                            # always SHOWN) + the leadership verdict (G2: dispersion in JSON) ──
                            if _cost_av:
                                _stack_cost = {
                                    'label_ar': COST_STACK_LABEL_AR,
                                    'label_en': COST_STACK_LABEL_EN,
                                    'sub_ar': COST_STACK_SUB_AR,
                                    'sub_en': COST_STACK_SUB_EN,
                                    'value': _cost_av['value'],
                                    'land_floor': _cost_av['land_floor'],
                                    'building_value': _cost_av['building_value'],
                                    'bua_m2': _cost_av['bua_m2'],
                                    'rcn_qar_per_m2': _cost_av['rcn_qar_per_m2'],
                                    'retention': _cost_av['retention'],
                                    'effective_age': _cost_av['effective_age'],
                                    'finish': _cost_av['finish'],
                                    'assumptions_ar': ('افتراضات: تشطيب {f} · معامل احتفاظ {r} · '
                                                       'عمر النظام (CGIS) أساس الاحتساب (E26)'
                                                       ).format(f=_cost_av['finish'],
                                                                r=_cost_av['retention']),
                                    'assumptions_en': ('Assumptions: finish {f} · retention factor {r} · '  # b87
                                                       'system (CGIS) age is the basis (E26)'
                                                       ).format(f=_cost_av['finish'],
                                                                r=_cost_av['retention']),
                                }
                            else:
                                _reason20 = ('أرضية الأرض غير متاحة' if not _lf_tri
                                             else ('عمر النظام غير متاح' if _age_ct is None
                                                   else 'بصمة البناء غير متاحة'))
                                _stack_cost = {'unavailable_reason_ar':
                                               LEAD_COST_UNAVAILABLE_AR.format(reason=_reason20)}
                            output['valuation']['value_stack'] = {
                                'market': {
                                    'median': _mkt20,
                                    'n': output['valuation'].get('n_transactions'),
                                    'dispersion_36': _gate.get('dispersion_36'),
                                    'bracket_n_36': _dispn20,
                                    'matched_stratum_n': _gate.get('matched_n'),
                                    'dominant_stratum': _dom20,
                                    'dominant_share_pct': _domshare20,
                                    'geo_full_n': _gate.get('geo_full_n'),
                                    'geo_full_dispersion': _gate.get('geo_full_dispersion'),
                                },
                                'cost': _stack_cost,
                                'income_available': bool(isinstance(income, dict)
                                                         and income.get('value')),
                            }
                            _lead20 = {
                                'leader': _gate['leader'], 'rule': _gate['rule'],
                                'matched_n': _gate.get('matched_n'),
                                'dispersion_36': _gate.get('dispersion_36'),
                                'stratum_match': _gate.get('stratum_match'),
                                'band': _gate.get('band'),
                                'resurvey': _gate.get('resurvey'),
                                'geo_full_n': _gate.get('geo_full_n'),
                                'geo_full_dispersion': _gate.get('geo_full_dispersion'),
                                'cost_value': _cv20,
                                'market_value': _mkt20,
                                'thresholds': _gate.get('thresholds'),
                            }
                            if _gate.get('divergence'):
                                _lead20['divergence'] = True
                            if _gate.get('resurvey'):
                                _lead20['resurvey_note_ar'] = LEAD_RESURVEY_NOTE_AR
                                _lead20['resurvey_note_en'] = LEAD_RESURVEY_NOTE_EN
                            _mu20 = output.get('material_uncertainty')
                            if _gate['rule'] == 'cost_led':
                                # F3(b) — the COST leads: range [cost … market-muted], MUC high.
                                output['valuation']['amount'] = _r100k(_cv20)
                                output['valuation']['low'] = _r100k(_gate['low'])
                                output['valuation']['high'] = _r100k(_gate['high'])
                                output['valuation']['range_is_headline'] = True
                                output['valuation']['central_estimate'] = _r100k(_cv20)
                                _lead20['note_ar'] = LEAD_COST_NOTE_AR.format(
                                    n=_n20, d=_d20, cost=f'{_r10k(_cv20):,}',
                                    comp=f'{_r10k(_mkt20):,}')
                                _lead20['note_en'] = LEAD_COST_NOTE_EN.format(
                                    n=_n20, d=_d20, cost=f'{_r10k(_cv20):,}',
                                    comp=f'{_r10k(_mkt20):,}')
                                if _gate.get('band') == 'old' or (_age_ct or 0) >= 10:
                                    # SESSION_CLOSE §6-b: age-graded cost honesty — the cost
                                    # leads here BY ELIMINATION (the pool failed), not precision.
                                    _lead20['age_honesty_note_ar'] = LEAD_COST_AGE_HONESTY_AR
                                    _lead20['age_honesty_note_en'] = LEAD_COST_AGE_HONESTY_EN
                                if isinstance(_mu20, dict):
                                    _mu20['level'] = 'high'
                                # ISS-A07 coherence (the b16 pattern): recompute the
                                # decomposition + B-1 floor on the new central + re-run b14.
                                try:
                                    _decomp20 = _decompose_value(
                                        valuation_amount=output['valuation']['amount'],
                                        plot_area_m2=ev.plot_area_m2, bua_m2=bua,
                                        moj_ref_dict=moj_ref)
                                    if _decomp20:
                                        output['valuation']['value_decomposition'] = _decomp20
                                        _reconcile_decomposition_narrative(output)
                                    _vf20 = _villa_value_floor(
                                        output['valuation']['amount'],
                                        getattr(ev, 'plot_area_m2', None), moj_ref, _decomp20)
                                    if _vf20:
                                        output['valuation']['value_floor'] = _vf20
                                        _inject_value_floor_into_brief(output.get('brief'), _vf20)
                                except Exception:
                                    pass
                            elif _gate['rule'] == 'geo_full':
                                # RULE 2 — market leads via the unmatched geo-full pool:
                                # disclosure + MUC one notch + the cost value as the range floor.
                                _gd20 = (f"{_gate['geo_full_dispersion']:.3f}"
                                         if _gate.get('geo_full_dispersion') is not None else '—')
                                _lead20['note_ar'] = LEAD_GEO_FULL_NOTE_AR.format(
                                    n=_gate.get('geo_full_n'), d=_gd20)
                                _lead20['note_en'] = LEAD_GEO_FULL_NOTE_EN.format(
                                    n=_gate.get('geo_full_n'), d=_gd20)
                                if _cv20:
                                    _lo20 = output['valuation'].get('low')
                                    if not _lo20 or _cv20 > _lo20:
                                        output['valuation']['low'] = _r100k(_cv20)
                                if isinstance(_mu20, dict):
                                    _mu20['level'] = _muc_one_notch(_mu20.get('level'))
                            elif _gate['rule'] == 'e25_capped':
                                # E25 RAIL — divergence disclosed; the market keeps the lead
                                # as the anti-inflation cap (double-weak clause: MUC >= high).
                                _lead20['note_ar'] = LEAD_E25_NOTE_AR.format(
                                    cost=f'{_r10k(_cv20):,}', comp=f'{_r10k(_mkt20):,}')
                                _lead20['note_en'] = LEAD_E25_NOTE_EN.format(
                                    cost=f'{_r10k(_cv20):,}', comp=f'{_r10k(_mkt20):,}')
                                if isinstance(_mu20, dict) and \
                                        (_mu20.get('level') or 'moderate') not in ('high', 'critical'):
                                    _mu20['level'] = 'high'
                            elif _gate['rule'] == 'cost_unavailable':
                                _lead20['note_ar'] = _stack_cost.get('unavailable_reason_ar')
                                if isinstance(_mu20, dict) and \
                                        (_mu20.get('level') or 'moderate') not in ('high', 'critical'):
                                    _mu20['level'] = 'high'
                            # rule == 'matched' → the market leads normally; emission only.
                            output['valuation']['leadership'] = _lead20
                            # ── Sprint 2.22.0b.38 (DEF-UX1): keystone comparables ──
                            # Surface the subject-bracket MoJ transactions that PRODUCED the
                            # displayed median — ONLY when the MARKET led via that exact bracket
                            # (leader=='market' AND method=='comparison_bracket' → the headline IS
                            # the bracket median). Excludes cost-led / income-led / geo-led / thin /
                            # preliminary (comparables did NOT lead) + land (its own comparable_grid)
                            # + refusals (no _gate → this block never runs). Anonymous (E12: no
                            # PIN/address), CC BY 4.0 public. DISPLAY-ONLY / value-invariant — adds a
                            # display field; amount/low/high/method/rule/leadership untouched.
                            # b38 = matched bracket (subject-bracket rows that PRODUCED the median);
                            # Sprint 2.22.0b.39 (DEF-UX1.1) extends to the geo-led market path
                            # (comparison_widened / _indicative) → the primary-area raw rows of the
                            # geo-widened pool (basis='geo_widened'; the frontend discloses the widening).
                            _kc_method = output['valuation'].get('method')
                            if (_gate['leader'] == 'market'
                                    and _kc_method in ('comparison_bracket', 'comparison_widened',
                                                       'comparison_widened_indicative')):
                                _kc_basis = ('matched_bracket' if _kc_method == 'comparison_bracket'
                                             else 'geo_widened')
                                _kc = _keystone_comparables(
                                    (primary.get('comparables')
                                     if isinstance(primary, dict) else None),
                                    output['valuation'].get('n_transactions'),
                                    output['valuation'].get('window_used'),
                                    basis=_kc_basis,
                                    pool_n=output['valuation'].get('n_transactions'))
                                if _kc:
                                    output['valuation']['comparables'] = _kc
                                    # ── Sprint 2.22.0b.41 (DEF-UX1.1b): geo neighbour rows ──
                                    # The geo-led median pools the subject's PRIMARY-area rows (the
                                    # b39 panel) PLUS location-adjusted NEIGHBOUR rows. b39 disclosed
                                    # only the pool SIZE; b41 surfaces the neighbour rows themselves —
                                    # each with its source-area NAME + ×adjustment + the DERIVED
                                    # location-adjusted ppm² (raw × factor) — nested on the geo block as
                                    # `comparables.neighbours`. From geo_v2['accepted_areas'] (retained
                                    # in-engine; the all_adjusted_prices local is NOT read). geo only —
                                    # matched_bracket (b38) has no neighbours. DISPLAY-ONLY / value-
                                    # invariant; None when no accepted neighbours (→ b39 behaviour).
                                    if _kc_basis == 'geo_widened':
                                        _kn = _keystone_neighbours(
                                            (geo_v2_result or {}).get('accepted_areas'))
                                        if _kn:
                                            _kc['neighbours'] = _kn
                            # ── Sprint 2.22.0b.40 (DEF-UX1.2a): cost-led «considered» comparables ──
                            # When the COST leads (rule=='cost_led'), the market pool was CONSIDERED but
                            # did NOT lead the number — it failed its reliability bar (the geo-full
                            # dispersion > 0.30 / thinness). Surface the subject's PRIMARY-AREA raw rows
                            # that were examined, under a NEW key `considered_comparables`
                            # (basis='cost_considered') so the frontend renders the honest «اطّلعنا عليها
                            # ولم تقُد الرقم» frame — NEVER «هي ما قرّر رقمك» (the DRC decided the number).
                            # The «why» scalars (geo_full_n + geo_full_dispersion) ride the block +
                            # value_stack.market. Rows ANONYMOUS (E12, via _keystone_comparables) + CC BY
                            # 4.0. DISPLAY-ONLY / value-invariant: amount/low/high/method/rule/leadership
                            # were all written above; this only ADDS a sibling display key. Mutually
                            # exclusive with the market-led keystone block above (market vs cost_led).
                            if _gate['rule'] == 'cost_led':
                                _cc_rows = ((geo_v2_result or {}).get('primary') or {}).get('transactions')
                                _cc = _keystone_comparables(
                                    _cc_rows,
                                    len(_cc_rows) if _cc_rows else 0,
                                    output['valuation'].get('window_used'),
                                    basis='cost_considered',
                                    pool_n=_gate.get('geo_full_n'))
                                if _cc:
                                    _cc['dispersion'] = _gate.get('geo_full_dispersion')
                                    output['valuation']['considered_comparables'] = _cc
                    # ── Sprint 2.22.0b.18 (§A1 — AGE BASIS, signed directive) ──
                    # Every LEADING cost/retention computation uses the SYSTEM (CGIS-documented)
                    # age — TD-93317: the certified valuer led on the system age («نحو 18 سنة …
                    # إسترشاداً بموقع CGIS»). A user-supplied actual age NEVER moves the headline:
                    # the b13 trim DEMOTES from lead to this SENSITIVITY line (the would-be value
                    # renders as disclosure only; headline/range/MUC untouched). The b11 system-age
                    # floor + the E24 cliff-flag stay as-is. Runs AFTER the chain — whichever branch
                    # led, the sensitivity is the same honest what-if.
                    if _ct_trim and building_age_years is not None:
                        _as_x = _r100k(_ct_trim['amount'])
                        output['valuation']['age_sensitivity'] = {
                            'claimed_age_years': int(building_age_years),
                            'value': _as_x,
                            'note_ar': AGE_SENSITIVITY_NOTE_AR.format(
                                n=int(building_age_years), x=f"{_as_x:,}"),
                            'note_en': AGE_SENSITIVITY_NOTE_EN.format(
                                n=int(building_age_years), x=f"{_as_x:,}"),
                        }
            except Exception as _etri:
                import sys
                print(f'[income_triangulation warning] {_etri}', file=sys.stderr)
        except Exception as e:
            import sys
            print(f'[value decomposition warning] {e}', file=sys.stderr)

    # ── Sprint 2.4a: Final Brief Sync ──
    # The brief was first finalized inside _build_unified_output using the
    # raw primary value. But substantiality (Sprint 2.2 + 2.3) may have
    # since adjusted output.valuation.amount. Re-sync brief headlines and
    # anchored sections so the user never sees a contradiction between
    # the main headline number and the brief's "your property value" /
    # negotiation range.
    if output.get('brief') and output.get('valuation') and output['valuation'].get('amount'):
        try:
            brief = output['brief']
            final_amount = output['valuation']['amount']
            final_low = output['valuation'].get('low') or final_amount * 0.85
            final_high = output['valuation'].get('high') or final_amount * 1.15

            brief['valuation_total'] = _r100k(final_amount)
            brief['valuation_low']   = _r100k(final_low)
            brief['valuation_high']  = _r100k(final_high)

            _rewrite_brief_anchored_sections(
                brief, final_amount, final_low, final_high,
                audience=audience,
                moj_direct=None,
                stock_strata=output.get('stock_strata'),  # Sprint 2.16.2
            )
        except Exception as e:
            import sys
            print(f'[final brief sync warning] {e}', file=sys.stderr)

    # ── Sprint 2.2: Benchmark Consistency Fix ──
    # The v2 baseline (evaluate_property.py) builds market_position using
    # `comparison.benchmark_total` which is the DIRECT-MATCH fair price
    # (MoJ n=1 × factors). But the unified output reports the WIDENED
    # valuation as `valuation.amount` (e.g. 4.5M instead of 3.0M).
    #
    # When listing_price equals our own valuation, the verdict was saying
    # "50% above market" — comparing to the wrong reference. The fix is
    # to recompute market_position using `valuation.amount` (what we
    # actually claim is the value) as the benchmark whenever widening or
    # building-substantiality adjustments have moved the headline away
    # from the v2 fair_price.
    if listing_price and output.get('valuation') and output['valuation'].get('amount'):
        try:
            from market_position import compute_position
            new_benchmark = output['valuation']['amount']
            new_n = primary.get('n') if primary else None
            new_source = (
                f"تقييم ثمّن المُوحَّد ({primary.get('method_label_ar', 'مقارنة')})"
                if primary else 'تقييم ثمّن'
            )
            pos = compute_position(
                listing_price=listing_price,
                benchmark_price=new_benchmark,
                benchmark_source=new_source,
                benchmark_n=new_n,
                listing_caveats=[],
            )
            output['market_position'] = pos.to_dict()
            # Also expose under listing_comparison for output_briefs compatibility
            output['listing_comparison'] = {
                'listing_price': listing_price,
                'benchmark_total': new_benchmark,
                'benchmark_label': new_source,
                'gap_qar': listing_price - new_benchmark,
                'gap_pct': (listing_price - new_benchmark) / new_benchmark if new_benchmark else 0,
            }
        except Exception as e:
            import sys
            print(f'[market_position rebuild warning] {e}', file=sys.stderr)

    # ── Sprint A.3: append accumulated sanity warnings + post-valuation checks ──
    output['sanity_warnings'] = _sanity_warnings + (output.get('sanity_warnings') or [])
    # Sprint 2.16.14 — attach Zoning cross-check flag (Bug A11)
    # The villa pipeline doesn't usually trigger this (subtype=1 in R1/R2/R3),
    # but defense-in-depth: if classify_asset surfaced a contradiction for any
    # reason, the full pipeline must propagate it too.
    if _subtype_zoning_mismatch:
        output['subtype_zoning_mismatch'] = _subtype_zoning_mismatch

    # Sprint 2.22.0b.22 — disclose an ignored tower pair on the full path
    # (villa/house/land + (unit_count × per-unit) ⇒ the pair never entered the
    # rent; the user must SEE that it was ignored, not wonder why the value
    # didn't move).
    if _tower_pair_ignored:
        output['tower_pair_ignored'] = _tower_pair_ignored

    # Sprint 2.21.0.7 — attach the 'warn' asset-type reality result (non-residential
    # but tradable land, valued WITH a bold disclaimer). 'stop'/'reject' returned
    # earlier at GATE 0, so anything here is a warn that flowed through valuation.
    if _asset_type_reality and _asset_type_reality.get('action') == 'warn':
        output['asset_type_reality'] = _asset_type_reality

    # ── Sprint 2.20: Land Comparable Adjustments Grid (time-only v1) ──
    # Complement, NOT replace — the headline value is untouched. For LAND only,
    # build an RICS market-comparison grid that time-normalises each MoJ
    # comparable to the valuation date (transparency + RICS time adjustment).
    # Size deferred to 2.20.1 (§8 scan); corner deferred (E12 BLOCKED). Safe-fail:
    # any error leaves the response exactly as before.
    try:
        _at = (getattr(ev, 'asset_type', '') or '').lower()
        if _at in ('land', 'raw_land') and geo_v2_result:
            import adjustment_grid as _ag
            _prim = geo_v2_result.get('primary') or {}
            _txns = _prim.get('transactions') or []
            if len(_txns) >= _ag.INDICATIVE_N:
                import moj_reference as _mr
                _rows = _get_moj_rows(moj_csv_path)
                _dates = [d for d in (_mr.parse_date(r[_mr.DATE_COL]) for r in _rows) if d]
                _max_d = max(_dates) if _dates else None
                _slope_pct = 0.0
                _moj_names = _prim.get('moj_names') or []
                if _max_d and _moj_names:
                    try:
                        _tr = _mr.compute_trend(_rows, _moj_names[0], _max_d, category='land')
                        _sa = (_tr or {}).get('slope_annual_pct')
                        if _sa is not None:
                            # Tolerant unit handling (see slope normalisation note above):
                            _slope_pct = _sa * 100 if abs(_sa) < 1 else _sa
                    except Exception:
                        _slope_pct = 0.0
                _comps = [{'date': t.get('date'), 'price_m2': t.get('price_m2'),
                           'area_m2': t.get('area_m2')} for t in _txns]
                _grid = _ag.build_land_grid(
                    _comps,
                    valuation_date=(output.get('valuation_date')
                                    or datetime.now().strftime('%Y-%m-%d')),
                    annual_trend_pct=_slope_pct,
                    subject={'area': _prim.get('gis_name'),
                             'bracket': _cap_size_bracket(getattr(ev, 'plot_area_m2', None)),
                             'plot_area_m2': getattr(ev, 'plot_area_m2', None)},
                )
                if not _grid.fallback_used:
                    output['comparable_grid'] = _grid.to_dict()
                    _brief = output.get('brief') or {}
                    if isinstance(_brief.get('sections'), list):
                        from output_briefs import build_comparable_grid_section
                        _sec = build_comparable_grid_section(
                            output['comparable_grid'], audience=audience)
                        if _sec:
                            _brief['sections'].append(_sec)
    except Exception as e:
        import sys
        print(f'[comparable_grid warning] {e}', file=sys.stderr)

    # ── Sprint 2.22.0b.59: range-inversion guard (FINAL pass over the settled range) ──
    # After every range-writing path; before scenarios + the report fingerprint. Enforces
    # low <= amount <= high so a future/edge path can never serve an inverted range.
    _clamp_valuation_range(output.get('valuation'))

    # ── Sprint 2.22.0b.23 «بثّ المختصر»: scenarios panel (villa/house) — ADDITIVE/DISPLAY ──
    # ZERO new GIS: reuses the SETTLED headline + the B-1 land floor + the b10 footprint +
    # the b9 system age, all already on `output`. The headline (amount/low/high/method/rule)
    # is NOT touched. Swallows errors so a scenario edge can never break evaluate.
    try:
        _vv = output.get('valuation') or {}
        if (_vv.get('amount') and output.get('asset_type') in _TEARDOWN_ASSET_TYPES):
            _lf_sc = (_villa_value_floor(_vv['amount'], getattr(ev, 'plot_area_m2', None),
                                         moj_ref, _vv.get('value_decomposition')) or {}).get('land_floor')
            _geom_sc = _vv.get('geometry') or {}
            _age_sc = ((output.get('property_basis') or {}).get('building_age_estimate') or {}).get('age_floor_years')
            _eff_sc = (_vv.get('effective_footprint_m2')
                       if _vv.get('footprint_basis') == 'confirmed' else None)
            _scn = _valuation_scenarios(
                _vv['amount'], _vv.get('low'), _vv.get('high'), _lf_sc,
                _geom_sc.get('max_buildable_footprint_m2'), _eff_sc, floors, _age_sc)
            if _scn and len(_scn) > 1:   # only attach when the DRC what-ifs computed (not as_is-only)
                output['valuation']['scenarios'] = {
                    'items': _scn,
                    'note_ar': SCENARIO_PANEL_NOTE_AR, 'note_en': SCENARIO_PANEL_NOTE_EN,
                }
    except Exception as _esc:
        import sys
        print(f'[scenarios warning] {_esc}', file=sys.stderr)

    # ── Sprint 2.22.0b.23: report identity + tamper-evident fingerprint (ADDITIVE) ──
    _attach_report_identity(output, zone, street, building, pin, {
        'floors': floors, 'condition': condition, 'annexes': annexes,
        'basement': basement, 'footprint_m2': footprint_m2,
        'external_majlis': external_majlis, 'building_age_years': building_age_years,
        'is_luxury': is_luxury, 'penthouse': penthouse,
        'asking_price': listing_price, 'rental_income': rental_income,
        'unit_count': unit_count, 'avg_monthly_rent_per_unit': avg_monthly_rent_per_unit,
        'override_land_area': override_land_area,
    })

    _check_output_sanity(output, listing_price)
    return output


# ============================================================
# Output builder (backward-compatible + new RICS fields)
# ============================================================

# ── Sprint 2.22.0a.10: Stage-1 honest-range dispersion gate ──
# The widened (geo_value) villa path is built-type- AND condition-BLIND (RISK_REGISTER R7):
# geo_reference_v2._categorize lumps basic / 2-story+annex / +penthouse / مسكن / مجلس into one
# 'villa', so when the size-bracketed comp pool's price/m² is highly dispersed, a precise point
# median is FALSE PRECISION for a Stage-1 subject (built-type + condition always unconfirmed).
# Gate on the pool's own spread (p75−p25)/median; when high, the engine drops the tier to
# indicative, widens the MVU, and discloses — the P25–P75 range (already in valuation.low/high)
# becomes the honest headline while the median is retained as the central indicative estimate.
# T=0.30 is a TUNABLE default calibrated on n=2 widened villas (Marikh 0.469, Maamoura 0.406 —
# both fire; bracket path excluded by method); revisit as the widened-villa sample grows.
# Presentation only — the median computation is unchanged (RICS VPS 3 / IVS uncertainty
# disclosure under thin/heterogeneous evidence; staged model E16).
STAGE1_DISPERSION_T = 0.30
_WIDENED_METHODS = ('comparison_widened', 'comparison_widened_indicative')


def _stage1_dispersion_gate(primary, geo_v2_result):
    """Return {'dispersion', 'gated', 'threshold'} for the widened (geo_value) paths OR the
    comparison_bracket success path, or None when not applicable. Gated when the pool's ppm²
    (p75 - p25)/median >= STAGE1_DISPERSION_T. Sprint 2.22.0a.14 (vi) extends the a10 gate to the
    bracket SUCCESS surface — closes R10 (the a13-rescued dispersed cells) AND the pre-existing
    dispersed-reliable cells (20/37 villa reliable cells measured dispersed). Presentation only."""
    if not primary:
        return None
    method = primary.get('method')
    if method == 'comparison_bracket':
        # (vi)(a): the bracket cell's 36mo ppm² dispersion, precomputed in apply_moj_strategy.
        disp = primary.get('ppm2_dispersion')
        if disp is None or disp <= 0:
            return None
    elif method in _WIDENED_METHODS:
        g = geo_v2_result or {}
        p25, p75, med = g.get('p25_m2'), g.get('p75_m2'), g.get('weighted_median_m2')
        if not (p25 and p75 and med) or med <= 0:
            return None
        disp = (p75 - p25) / med
    else:
        return None
    return {'dispersion': round(disp, 3), 'gated': disp >= STAGE1_DISPERSION_T,
            'threshold': STAGE1_DISPERSION_T}


# ════════════════════════════════════════════════════════════════════
# Sprint 2.22.0a.17 — condition caveat (copy-only, honesty-additive)
# Sprint 2.22.0a.19 — extended PATH-COMPLETE to the thin / non-dispersed widened / preliminary
#   villa/house value surfaces. a18 moved Marikh (54/541/6) onto the comparison_thin path at
#   ~5.4M, exposing that a17's "thin already caveated" conflated the SAMPLE-size caveat with a
#   CONDITION disclosure — orthogonal. R7 (built-type/condition blindness) is method-agnostic.
# ════════════════════════════════════════════════════════════════════
# Any villa/house headline value is condition-blind (RISK_REGISTER R7, bidirectional): a
# renovated subject may sit above the point, a worn one below. The note attaches to every
# value-bearing villa/house comparison surface EXCEPT the dispersion-GATED pools, whose
# honest-range text (a14 bracket / a10 widened, lines ~4869-4881) ALREADY states "built type
# and condition not yet confirmed" — so gate.get('gated') routes those to the existing
# disclosure and the note never duplicates. NO valuation logic — additive note only; amount
# byte-identical on every path.
CONDITION_NOTE_AR = 'لم تُؤخذ حالة العقار (تجديد أو تهالك) في الحسبان. عقار في حالة أفضل من المتوسط قد يقع أعلى هذه النقطة، وعقار في حالة أدنى قد يقع تحتها.'
CONDITION_NOTE_EN = 'Property condition (renovation or wear) was not assessed. A better-than-average property may sit above this point; a poorer one may sit below.'

# Value-bearing villa/house comparison surfaces that present a headline number the user may
# read as condition-aware. comparison_widened* with a GATED dispersion already discloses
# condition via the a10/a14 honest-range (excluded below by gate.get('gated')); non-gated
# widened + thin + preliminary carry NO such disclosure → they get the note.
_CONDITION_NOTE_METHODS = (
    'comparison_bracket',
    'comparison_thin',
    'comparison_widened',
    'comparison_widened_indicative',
    'comparison_preliminary',
)

# ── Sprint 2.22.0b.4 (B-2a) — teardown demolition down-anchor ──
# A user-STATED «must be demolished» subject is valued on HBU = redevelopment:
# land floor − demolition. The Qatar 10-Year Rule suppresses the building uplift
# but NEVER subtracts toward land — so a teardown subject stays pinned at the
# comparison median (which assumes a sound standing building) and is over-valued
# (~+35% measured on 56/565/21). This re-anchors it down.
# Demolition — PO-calibrated (Anas, Qatar market, Rule #7): roughly FLAT in a 100k-150k band,
# NOT linear with size. The PO's three points: a SMALL villa ≈ 100k, a MID villa ≈ 120k, a
# LARGE villa caps at ~150k. Modelled as per-m² (240/m² → ~120k for a ~500 m² mid-villa)
# CLAMPED to [100k, 150k] — so a small villa floors at 100k and a large one caps at 150k,
# matching all three points. (The earlier web-derived 60/m² captured LABOUR ONLY and missed
# debris haulage + municipality fees + site clearance.) Single tunable set (like D5/D6). At
# 100-150k, demolition is ~6-9% of the land floor — it moves the headline modestly; the core
# fix is the median→land re-anchor (−700K).
DEMO_QAR_PER_M2 = 240
DEMO_FLOOR_QAR = 100_000
DEMO_CAP_QAR = 150_000
_TEARDOWN_ASSET_TYPES = ('standalone_villa', 'house', 'villa')
TEARDOWN_NOTE_AR = ('التقييم على أساس الاستخدام الأمثل = إعادة التطوير: قيمة الأرض ({land} ر.ق) '
                    'مطروحاً منها تكلفة هدم تقديرية ({demo} ر.ق) — المبنى الحالي يُعدّ عبئاً لا '
                    'قيمة مضافة. تقدير الهدم استرشاديّ، والنطاق واسع لعدم اليقين.')
TEARDOWN_NOTE_EN = ('Valued on Highest-and-Best-Use = redevelopment: land value ({land} QAR) '
                    'less an indicative demolition cost ({demo} QAR) — the standing building is '
                    'a liability, not added value. Demolition is an estimate; the range is wide.')

# ── Sprint 2.22.0b.4 (B-2b) — luxury-new premium via Cost Approach / DRC (Lever-1, R7 UP) ──
# The engine is blind to finish (measured: is_luxury → no move), so a premium new-build villa is
# severely UNDER-anchored: V002/V003 (GT-2 confirmed sales, 56/565 — new luxury villas SOLD 4.0M
# each vs the engine's 2.4M median = +67%). When the user STATES is_luxury AND new, value by the
# COST APPROACH (DRC, §20.9): value = land_floor + BUA × construction_cost. Calibrated on V002/V003:
# building value 2.3M (4.0M − land 1.7M) / BUA ~657 m² → construction ≈ 3500 QAR/m². BUA uses FULL
# zone coverage (a luxury villa builds to the ceiling, NOT b1's conservative ×0.8) + the penthouse
# rule (Anas: ground + first + penthouse-half sharing the roof = footprint × 2.5). Opt-in; villa/
# house; never auto-detected. §20.27 PARK + §20.9 DRC unlocked per Anas 2026-06-07. Tunable like
# D5/D6; high MUC + wide range + a limited-sample disclosure.
LUXURY_CONSTRUCTION_QAR_PER_M2 = 3500
PENTHOUSE_BUA_MULTIPLIER = 2.5
LUXURY_NEW_NOTE_AR = ('فيلا فاخرة حديثة البناء — قُيّمت بمنهج التكلفة: قاع الأرض ({land} ر.ق) + قيمة '
                      'البناء ({bld} ر.ق = {bua} م² × {cost} ر.ق/م²). سعر بناء المتر مُعايَر على صفقات '
                      'بيع مؤكّدة محدودة؛ النطاق واسع وعدم اليقين مرتفع.')
LUXURY_NEW_NOTE_EN = ('Premium new-build villa — valued by the Cost Approach (DRC): land floor ({land} '
                      'QAR) + building value ({bld} QAR = {bua} m² × {cost} QAR/m²). Construction cost '
                      'calibrated on limited confirmed sales; the range is wide and uncertainty is high.')


def _condition_note_applies(primary, gate, asset_type, amount) -> bool:
    """Sprint 2.22.0a.17 (a19 path-complete): True when a villa/house comparison value should
    carry the bidirectional condition caveat.

    Scope (gets the note): method in _CONDITION_NOTE_METHODS AND asset_type in
    {standalone_villa, house, villa} AND a real amount is present AND the dispersion gate is
    NOT gated. Fail-safe TO DISCLOSURE: a None or malformed gate dict (dispersion unresolved —
    e.g. the thin / preliminary paths, where _stage1_dispersion_gate returns None) → include
    (uses gate.get('gated'), so a missing key never excludes). Excluded: dispersion-GATED
    bracket (a14) + widened (a10) — their honest-range already discloses condition; by
    asset_type: land + apartment/tower/commercial; refusals have no amount. Copy-only — never
    changes the valuation amount."""
    if not primary or primary.get('method') not in _CONDITION_NOTE_METHODS:
        return False
    if asset_type not in ('standalone_villa', 'house', 'villa'):
        return False
    if amount is None:
        return False
    if gate and gate.get('gated'):
        return False  # dispersed bracket (a14) / widened (a10) → honest-range already discloses condition
    return True        # clean bracket / thin / non-dispersed widened / preliminary → include


# ── Sprint 2.22.0b.12 (Bug A15): HBU not-evaluated → explicit disclosure ──
# geometric_factors gates the HBU (Highest-and-Best-Use) block on the zoning hint
# (current_zoning_code, geometric_factors.py:638); when the zoning layer is unavailable
# the hint is None → `result['hbu']` is never set → the consumer's `hbu_analysis` is
# silently dropped, conflating "no HBU upside" with "HBU NOT evaluated" — two materially
# different RICS (VPS 2 / IVS 102) disclosures. DISCLOSURE-ONLY / value-invariant: surfaces
# an explicit note; never touches the valuation amount/range/method.
_HBU_NOTE_AR = 'لم يتسنَّ تحديد فرضية الاستخدام الأفضل لهذه القطعة (طبقة التنظيم غير متاحة)'
_HBU_NOTE_EN = 'Highest-and-best-use could not be assessed for this plot (zoning layer unavailable).'


def _hbu_note_applies(primary, gate, asset_type, amount, zoning_code) -> bool:
    """True when a villa/house comparison surface had its HBU silently dropped because the
    zoning hint was absent. zoning_code is None ⟺ the zoning factor was not resolved (then
    geometric_factors skips HBU) — distinct from 'HBU evaluated, no upside' (zoning present →
    False here). Reuses _condition_note_applies for the villa/house surface scope + its
    None/malformed-gate fail-safe-to-disclosure (a malformed gate + absent zoning still
    discloses). land / apartment / tower / commercial / refusal → False via that helper."""
    if zoning_code is not None:
        return False  # zoning present → HBU WAS evaluated (upside or not) → no note
    return _condition_note_applies(primary, gate, asset_type, amount)


# ════════════════════════════════════════════════════════════════════
# Sprint §6 (R7) — income-triangulation: income SETS the villa headline
# ════════════════════════════════════════════════════════════════════
# PO decision (أ, 2026-06-07): stop pinning condition-blind comparison GUESSES
# (e.g. Marikh 54/541/6 = 5.4M, defensible ~3.0-3.4M) as confident headlines.
# Two modes, villa/house only (DECISION_income_crosscheck_villa_R7.md §6 + brief):
#   • income_led ((i)/أ) — a GROUNDED subject rent (user-provided) + a calibrated
#     reliable/indicative cap-rate cell → income LEADS: the headline = the income
#     value (rent reflects age/condition → catches the comparison's over/under-anchor),
#     clamped to [land_floor, cost_ceiling]; the comparison is demoted to a disclosed
#     sibling. CIRCULARITY GUARD (recon): only a SUBJECT-specific rent (actual_provided)
#     can lead — the area-median rent ÷ area-yield reconstructs the comparison.
#   • widen_down ((iii)) — a no-rent condition-blind THIN/uncertain villa (NOT a clean
#     reliable bracket — that good case must NOT be over-widened; NOT a dispersion-gated
#     pool — a10/a14 already own those) → widen the range DOWN to the land floor + MUC
#     high, so the high comparison guess is no longer pinned as a confident value.
# Pure: returns a decision dict or None; never mutates. Opt-in for income_led (fires only
# on a user rent → the 4 standard no-rent anchors are byte-identical on that mode).
_INCOME_LED_METHODS = ('comparison_bracket', 'comparison_thin', 'comparison_widened',
                       'comparison_widened_indicative', 'comparison_preliminary')
_WIDEN_DOWN_METHODS = ('comparison_thin', 'comparison_widened',
                       'comparison_widened_indicative', 'comparison_preliminary')

def _age_neutral_rail_cost(cost, age_source):
    """Sprint 2.22.0b.21 — the INV-3 back-door close (micro Gate-2 SIGNED 2026-06-11).

    E26: «كل حساب قائد يستخدم عمر النظام» — the income-eligibility CEILING (the b6 rail
    consumed by _income_triangulation) must NOT vary with a USER-claimed age. When the
    age came from the user, restore the v3 replacement-cost ceiling to its AGE-0 figure
    (un-depreciate the building leg: value − depreciated + new; land + external works
    unchanged) — exactly the number the rail uses when no age is supplied.

    #39 DEVIATION (measured, PHASE0 sweep 2026-06-11): the directive named the literal
    `_cost_av` (system-age DRC ≈ 2,378,094 on the lead case) as the new ceiling — measured,
    that ceiling×1.05 (≈2.50M) BLOCKS the with-rent baseline surface (income 2.79–4.66M,
    incl. every no-footprint row where the rail was inert with ceil=None) — breaching the
    signed «الحركات المتوقعة (الحصر الكامل)». THIS age-neutralized v3 ceiling reproduces
    the signed enumeration EXACTLY: only the three fp+rent breach groups return to
    income_led; everything else byte-identical. Pure; never mutates the input."""
    try:
        if (age_source == 'user' and isinstance(cost, dict) and cost.get('value')
                and cost.get('building_value_new') is not None
                and cost.get('building_value_depreciated') is not None):
            return {**cost, 'value': round(cost['value']
                                           - cost['building_value_depreciated']
                                           + cost['building_value_new'])}
    except Exception:
        pass
    return cost


def _income_triangulation(primary, income, cost, land_floor, asset_type,
                          dispersion_gated=False):
    if asset_type not in ('standalone_villa', 'house', 'villa'):
        return None
    if not primary or not primary.get('value'):
        return None
    comp = primary['value']
    method = primary.get('method')
    ceil = (cost or {}).get('value') if isinstance(cost, dict) else None

    # ── (i)/(أ): income LEADS when grounded (subject rent) + reliable + within the rails ──
    if (method in _INCOME_LED_METHODS and income and income.get('value')):
        prov = income.get('cap_rate_provenance') or {}
        grounded = (income.get('rent_source') == 'actual_provided')           # SUBJECT-specific rent
        calibrated = (prov.get('source') == 'calibrated'
                      and prov.get('confidence') in ('reliable', 'indicative'))
        inc_val = income['value']
        # within the RICS rails: land_floor ≤ income ≤ cost_ceiling (×1.05 tol). Outside →
        # the rent/yield is implausible → do NOT lead (the clamp would be a hard pull).
        within = ((land_floor is None or inc_val >= land_floor)
                  and (ceil is None or inc_val <= ceil * 1.05))
        if grounded and calibrated and within:
            central = inc_val
            if land_floor:
                central = max(central, land_floor)
            if ceil:
                central = min(central, round(ceil * 1.05))
            spread = abs(comp - central) / central if central else 0.0
            # A yield borrowed from an adjacent bracket (§6 v2) adds uncertainty →
            # force MUC high even when the income↔comparison spread is small.
            _borrowed = bool(prov.get('bracket_borrowed'))
            return {
                'mode': 'income_led',
                'amount': central,
                'low': round(central * 0.85),
                'high': round(central * 1.12),
                'muc_level': 'high' if (spread >= 0.30 or _borrowed) else 'moderate',
                'comparison_value': comp,
                'spread_pct': round(spread * 100, 1),
                'cap_rate': income.get('cap_rate'),
                'net_yield_pct': prov.get('net_yield_pct'),
                'sample_size': prov.get('sample_size'),
                'confidence': prov.get('confidence'),
                'annual_rent': income.get('annual_rent'),
                'bracket_borrowed': _borrowed,
                'borrowed_from_bracket': prov.get('borrowed_from_bracket'),
            }

    # ── (iii): honest-widen DOWN for a no-rent condition-blind THIN/uncertain villa ──
    # EXCLUDES clean reliable comparison_bracket (good case) AND dispersion-gated pools
    # (a10/a14 own those). Only widens DOWN (land_floor below the median).
    if (method in _WIDEN_DOWN_METHODS and not dispersion_gated
            and land_floor and land_floor < comp):
        return {
            'mode': 'widen_down',
            'amount': comp,                          # central unchanged (muted via range_is_headline)
            'low': land_floor,
            'high': primary.get('high') or comp,
            'muc_level': 'high',
            'land_floor': land_floor,
            'comparison_value': comp,
        }
    return None


# Sprint §6 (R7) — income-triangulation user-facing notes (AR + EN).
INCOME_LED_NOTE_AR = ('قُيّمت بمنهج الدخل: إيجار العقار الفعلي ÷ معدل رسملة معايَر '
                      '({cap}% ، عينة n={n} {conf}). القيمة المركزية {x} ر.ق. وسيط المقارنة '
                      'المنطقي ({comp} ر.ق) لا يُعتمد كأساس لأنه لا يأخذ نوع البناء والحالة، '
                      'بينما الإيجار يعكسهما.')
INCOME_LED_NOTE_EN = ('Valued by the Income approach: the property’s actual rent ÷ a calibrated '
                      'cap rate ({cap}%, n={n} {conf}). Central value {x} QAR. The area comparison '
                      'median ({comp} QAR) is not used as the basis because it ignores built type '
                      'and condition, which the rent reflects.')
CONDITION_WIDEN_NOTE_AR = ('نوع بناء العقار وحالته غير مؤكَّدين، ووسيط المقارنة لا يأخذهما — لذلك '
                           'النطاق يمتدّ من قيمة الأرض ({floor} ر.ق) حتى وسيط المقارنة. أدخِل '
                           'الإيجار الفعلي للعقار لتثبيت القيمة على أساس مؤسَّس.')
CONDITION_WIDEN_NOTE_EN = ('The property’s built type and condition are unconfirmed, and the '
                           'comparison median ignores them — so the range spans from the land value '
                           '({floor} QAR) up to the comparison median. Enter the property’s actual '
                           'rent to ground the value.')
# Sprint 2.22.0b.18 (§A1) — the user-age SENSITIVITY line (verbatim core per the signed directive).
# Lead basis = the SYSTEM (CGIS-documented) age; a user-claimed age renders as disclosed sensitivity
# (VALUER-VALIDATED: TD-93317 led on the system age — E26 candidate).
AGE_SENSITIVITY_NOTE_AR = ('حساسية العمر: لو كان العمر الفعلي {n} سنة ≈ {x} ر.ق. '
                           '(أساس القيادة = العمر الموثَّق في النظام؛ والعمر المُدخَل يُعرَض حساسيةً مُفصَحة.)')
AGE_SENSITIVITY_NOTE_EN = ('Age sensitivity: if the actual age is {n} years ≈ {x} QAR. '
                           '(The lead basis is the system-documented age; a user-entered age '
                           'renders as disclosed sensitivity.)')


# ════════════════════════════════════════════════════════════════════
# Sprint 2.22.0b.11 (§20.9) — Cost-Approach (DRC) triangulation: SHIP-NOW slice
# ════════════════════════════════════════════════════════════════════
# An INDEPENDENT secondary valuation (RICS Depreciated Replacement Cost):
#     cost = land_floor + (RCN_new(finish) × retention(effective_age)) × BUA
# SECONDARY to Market (RICS: the cost approach is last-resort for actively-traded
# assets) — it only TRIANGULATES the market headline. It is SUBJECT-INTRINSIC
# (b9 age + b10 footprint), so it needs no comparables' BUA (which MoJ lacks) → it
# escapes the R7 BUA dead-end and fixes the live default no-rent over-anchor WITHOUT
# a user rent (the decisive advantage over §6 income).
#
# Gate-2 SPLIT (METHODOLOGY_DRC_qatar_v1 §11): SHIP-NOW = the DOWN-re-anchor ONLY.
# When the market is a thin-pool / widened OVER-anchor AND the cost UNDERCUTS it by
# > THRESHOLD, present the honest range with the COST as the informed lower anchor
# (replacing §6 widen_down's BARE land floor), range_is_headline, MUC high. The
# convergent-confirm + the UP-lift are GATED-to-next (they bias on the age handling).
#
# 🔴 IMMUNITY (why ship-now is safe on the system-vs-actual age bias): b9 surfaces the
# SYSTEM (CGIS) age — typically LOWER than the actual (re-registration zeros the survey
# date). Lower age → higher retention → higher cost → a HIGHER cost floor → the down-move
# is LESS aggressive (never over-drops) AND the >THRESHOLD undercut is HARDER to reach
# (it PROTECTS convergent cases). MEASURED: V001 56/647/6 at the b9 age 17 → cost ~3.12M
# → undercut +22% < 30% → does NOT fire (correct); at the ACTUAL ~25 → ~2.91M → +30.6%
# → would WRONGLY fire. So this slice runs depreciation on the b9 SYSTEM age (a FLOOR) —
# deliberately conservative. Actual-age handling is the GATED slice's job.
#
# Params bank-calibrated (METHODOLOGY_DRC_qatar_v1 §3/§5/§7 — reproduces the certified
# valuer TD 93317 to ~1%, downgraded to a consistency-check per §11). Pure functions;
# never mutate. Value-AFFECTING (Gate-2) ONLY on the narrow set it fires on.

# RCN ladder — Replacement Cost New, QAR/m² of BUA (turnkey all-in; PO web-validated, §3).
COST_RCN_BY_FINISH = {
    'shell': 1200, 'عظم': 1200,
    'ordinary': 2200, 'average': 2200,
    'good': 2500, 'very-good': 2500, 'very_good': 2500,
    'high': 3000,
    'luxury': 3500,
}
COST_RCN_DEFAULT = 2200                  # no-input finish = ordinary (§9 #4)
COST_ECONOMIC_LIFE_Y = 50                # §5 (reproduces the valuer; within the 40-60 band)
COST_RESIDUAL_FLOOR = 0.27               # a sound shell retains value (§5; ordinary 2200×0.27≈594≈PO 600).
COST_RESIDUAL_FLOOR_LUX = 0.31           # Sprint 2.22.0b.13 (D-1): high/luxury stock retains MORE residual
                                         # value when dilapidated (premium structure). Finish-keyed in
                                         # _cost_retention; bites only on the trim of old premium stock
                                         # (eff_age > ~34). Default finish → 0.27 → byte-identical to b11/b12.
COST_CONDITION_PENALTY = {               # effective_age = chronological + penalty (§5; b13 §4.2 ladder, §11 Q1)
    'excellent': -2, 'renovated': -3, 'new': 0,   # b13: excellent −2 / renovated −3 (were 0) — the GATED-slice
    'good': 5, 'very-good': 5, 'very_good': 5,     # actual-age calibration; default condition = average (8) unchanged
    'fair': 15,
    'poor': 25, 'dilapidated': 25, 'teardown': 25,
}
COST_DEFAULT_PENALTY = 8                  # no-input condition = average (§9 #4)
COST_BUILT_RATIO = 0.77                   # actual BUA ÷ max-buildable (V001 602/782); declared +
                                          # ±20%-tested vs the 30% threshold (recon C — does not flip).
COST_DEFAULT_FLOORS = 2                   # G+1 default
COST_REANCHOR_UNDERCUT_T = 0.30           # (market − cost)/cost > this → re-anchor down (the V001/Marikh
                                          # separator: Marikh +127% fires, V001 +22% does not).
COST_REANCHOR_MIN_AGE_Y = 10              # age-gate (B): OLD stock only → closes the new-luxury mis-launch.
_COST_REANCHOR_METHODS = ('comparison_thin', 'comparison_widened',
                          'comparison_widened_indicative', 'comparison_preliminary')


def _cost_retention(effective_age, finish=None):
    """Straight-line physical depreciation, clamped to the residual floor (§5).
    Sprint 2.22.0b.13 (D-1): the floor is FINISH-KEYED — high/luxury stock retains more
    residual value when dilapidated (0.31 vs the ordinary 0.27). `finish` None/ordinary/good
    → 0.27 → byte-identical to b11/b12 (the b11 down-half passes ordinary on default)."""
    if effective_age is None:
        return None
    floor = COST_RESIDUAL_FLOOR_LUX if (finish or '').strip().lower() in ('high', 'luxury') else COST_RESIDUAL_FLOOR
    return max(floor, min(0.98, 1.0 - (effective_age / COST_ECONOMIC_LIFE_Y)))


def _cost_approach_value(land_floor, footprint_max_m2, floors, finish, age_years,
                         condition, footprint_actual=None):
    """RICS DRC = land_floor + [RCN_new(finish) × retention(effective_age)] × BUA.
    SUBJECT-INTRINSIC. BUA = (user-confirmed footprint, if any) × floors, else
    max-buildable × BUILT_RATIO × floors (actual BUA < the b10 legal CEILING — §7).
    age_years = the b9 SYSTEM age (a floor; lower = conservative). Returns a dict, or
    None when the land floor / footprint / age is unavailable (→ no down-re-anchor). Pure."""
    try:
        if not land_floor or land_floor <= 0:
            return None
        if age_years is None:
            return None                                   # depreciation needs an age
        fl = max(1, int(floors) if floors else COST_DEFAULT_FLOORS)
        if footprint_actual and footprint_actual > 0:
            bua = footprint_actual * fl                   # user-confirmed footprint = actual (no built-ratio)
        elif footprint_max_m2 and footprint_max_m2 > 0:
            bua = footprint_max_m2 * COST_BUILT_RATIO * fl    # b10 legal max → estimate actual via built-ratio
        else:
            return None
        rcn = COST_RCN_BY_FINISH.get((finish or '').strip().lower(), COST_RCN_DEFAULT)
        # Sprint 2.22.0b.71: the condition penalty is read from the swappable calibration
        # DB (condition_adjustments.sqlite — seeded n=1 from V001, so byte-identical to the
        # hardcoded ladder), safe-falling to the hardcoded dict. `is not None` keeps `new`=0
        # and the negative trims (excellent/renovated) honored. The numbers swap when the
        # GT-2 corpus calibrates them — zero code change (the PO's «الرقم يتغيّر لا الكود»).
        _cp, _ = _lookup_condition_penalty(condition)
        penalty = _cp if _cp is not None else COST_CONDITION_PENALTY.get((condition or '').strip().lower(), COST_DEFAULT_PENALTY)
        eff_age = max(0, age_years + penalty)
        retention = _cost_retention(eff_age, finish)
        building = round(bua * rcn * retention)
        return {
            'value': round(land_floor + building),
            'land_floor': land_floor,
            'building_value': building,
            'bua_m2': round(bua),
            'footprint_max_m2': footprint_max_m2,
            'built_ratio': (None if (footprint_actual and footprint_actual > 0) else COST_BUILT_RATIO),
            'floors': fl,
            'rcn_qar_per_m2': rcn,
            'finish': (finish or 'ordinary'),
            'age_years': age_years,
            'condition_penalty': penalty,
            'effective_age': eff_age,
            'retention': round(retention, 3),
        }
    except Exception:
        return None


# ── Sprint 2.22.0b.23 — «بثّ المختصر» (short-report): scenarios + report id/fingerprint ──
# ADDITIVE / DISPLAY-ONLY. The headline (amount/low/high/method/rule/leadership) is NEVER
# touched — these are sibling keys the report renders. All four scenarios reuse the EXISTING
# pure calculators (the b11/b13 DRC `_cost_approach_value` + the B-1 land floor + the b4
# teardown demolition band) on the already-fetched context → ZERO new GIS.

SCENARIO_LABELS = {
    'as_is':              ('كما هي (التقدير الحالي)',           'As-is (current estimate)'),
    'renovated_excellent':('بعد ترميم كامل — حالة ممتازة',     'Renovated to excellent condition'),
    'luxury_finish':      ('بتشطيب فاخر',                       'Luxury finish'),
    'teardown_land':      ('هدم وإعادة تطوير (قيمة الأرض − الهدم)', 'Teardown / redevelopment (land − demolition)'),
}
SCENARIO_PANEL_NOTE_AR = ('سيناريوهات استرشادية بمنهج التكلفة (DRC) على نفس الأرض والبصمة — '
                          'لا تُغيّر التقدير المعتمد أعلاه؛ تُظهر فقط أثر الحالة/التشطيب.')
SCENARIO_PANEL_NOTE_EN = ('Indicative cost-approach (DRC) what-ifs on the same plot and footprint — '
                          'they do NOT change the headline estimate above; they only show the '
                          'effect of condition / finish.')


def _valuation_scenarios(amount, low, high, land_floor, footprint_max_m2, footprint_actual,
                         floors, age_years):
    """Pure (b23): the 4-scenario what-if panel for a valued villa/house.
    as_is = the headline mirror; renovated_excellent / luxury_finish = the DRC at
    finish=good/luxury + condition=excellent; teardown_land = land_floor − demolition
    (the b4 band, clamped). Returns a list of {key,label_ar,label_en,value,low,high,
    assumptions_ar} or None when the cost inputs (land floor / footprint / age) are
    unavailable. NEVER mutates; the headline is passed in, not read from a shared dict."""
    try:
        if not amount or amount <= 0:
            return None
        out = [{
            'key': 'as_is',
            'label_ar': SCENARIO_LABELS['as_is'][0], 'label_en': SCENARIO_LABELS['as_is'][1],
            'value': amount, 'low': low, 'high': high,
            'assumptions_ar': 'التقدير المعتمد كما هو أعلاه.',
            'assumptions_en': 'The adopted estimate, as shown above.',  # b87
        }]
        # the DRC scenarios need a land floor + footprint + age; absent → as_is only.
        if not land_floor or land_floor <= 0 or age_years is None or not (
                (footprint_actual and footprint_actual > 0) or (footprint_max_m2 and footprint_max_m2 > 0)):
            return out
        for key, finish, cond in (('renovated_excellent', 'good', 'excellent'),
                                  ('luxury_finish', 'luxury', 'excellent')):
            c = _cost_approach_value(land_floor, footprint_max_m2, floors, finish,
                                     age_years, cond, footprint_actual=footprint_actual)
            if c and c.get('value'):
                v = _r100k(c['value'])
                out.append({
                    'key': key,
                    'label_ar': SCENARIO_LABELS[key][0], 'label_en': SCENARIO_LABELS[key][1],
                    'value': v,
                    'low': _r100k(round(c['value'] * 0.90)),
                    'high': _r100k(round(c['value'] * 1.10)),
                    'assumptions_ar': ('منهج التكلفة: تشطيب {f} · معامل احتفاظ {r} · '
                                       'مساحة بناء ≈ {b} م² (قابلة للتعديل).').format(
                                           f=finish, r=c['retention'], b=c['bua_m2']),
                    'assumptions_en': ('Cost approach: finish {f} · retention factor {r} · '  # b87
                                       'built-up area ≈ {b} m² (adjustable).').format(
                                           f=finish, r=c['retention'], b=c['bua_m2']),
                })
        # teardown_land — the b4 demolition band on the actual/estimated BUA.
        _bua_td = (footprint_actual * max(1, int(floors) if floors else COST_DEFAULT_FLOORS)) \
            if (footprint_actual and footprint_actual > 0) \
            else (footprint_max_m2 * COST_BUILT_RATIO * max(1, int(floors) if floors else COST_DEFAULT_FLOORS))
        demo = min(max(round(DEMO_QAR_PER_M2 * (_bua_td or 0)), DEMO_FLOOR_QAR), DEMO_CAP_QAR)
        central = max(land_floor - demo, 0)
        out.append({
            'key': 'teardown_land',
            'label_ar': SCENARIO_LABELS['teardown_land'][0], 'label_en': SCENARIO_LABELS['teardown_land'][1],
            'value': _r100k(central),
            'low': _r100k(max(round(central * 0.88), 0)),
            'high': _r100k(land_floor),
            'assumptions_ar': ('قيمة الأرض ({l} ر.ق) − هدم تقديري ({d} ر.ق) — المبنى عبء لا قيمة.').format(
                l=f'{_r10k(land_floor):,}', d=f'{demo:,}'),
            'assumptions_en': ('Land value ({l} QAR) − estimated demolition ({d} QAR) — '  # b87
                               'the building is a cost, not value.').format(
                l=f'{_r10k(land_floor):,}', d=f'{demo:,}'),
        })
        return out
    except Exception:
        return None


# ── report identity + tamper-evident fingerprint (b23) ──
# report_ref = a human-quotable id (TH-YYYYMMDD-ZZSSSBBB[-4hex]); the 4hex disambiguates
# re-evaluations of the SAME address with different refine inputs. report_fp = an
# HMAC-SHA256 over the canonical core fields, keyed on HMAC_REPORT_KEY (Heroku config) —
# DORMANT (None) without a key. The /verify endpoint recomputes report_fp from the SAME
# canonical (the shared functions below) so a forged amount/range fails. No storage.
REPORT_FP_VERSION = 'v1'


def _report_canonical(address, date, engine, amount, low, high, rule):
    """The exact signing string, whitespace-normalized PER FIELD (the spec's \\s+ rule:
    collapse runs + strip each field before the join, so no whitespace ever lands next to
    a `|` delimiter). Shared by the emit (evaluate) and the /verify recompute (api) so they
    can NEVER drift."""
    parts = [REPORT_FP_VERSION, str(address or ''), str(date or ''), str(engine or ''),
             '' if amount is None else str(amount),
             '' if low is None else str(low),
             '' if high is None else str(high),
             str(rule or '')]
    return '|'.join(re.sub(r'\s+', ' ', p).strip() for p in parts)


def _report_fingerprint(canonical, key=None):
    """HMAC-SHA256(key, canonical)[:12] hex; None when no key (DORMANT — never a plain
    hash of the low-entropy fields, #62). Reads HMAC_REPORT_KEY from env when key=None."""
    if key is None:
        key = os.environ.get('HMAC_REPORT_KEY')
    if not key:
        return None
    return hmac.new(key.encode('utf-8'), canonical.encode('utf-8'),
                    hashlib.sha256).hexdigest()[:12]


def _refine_fp4(refine_inputs):
    """4 hex of a plain SHA-256 over the sorted non-empty refine inputs (display-only
    disambiguation, NOT security → a plain hash is correct here). None when no refine
    input was supplied (a bare /api/evaluate → ref carries no suffix)."""
    items = sorted((str(k), str(v)) for k, v in (refine_inputs or {}).items()
                   if v is not None and v != '' and v is not False)
    if not items:
        return None
    return hashlib.sha256(repr(items).encode('utf-8')).hexdigest()[:4]


def _report_ref(zone, street, building, pin, valuation_date, refine_fp4=None):
    """TH-YYYYMMDD-ZZSSSBBB[-4hex]; falls back to P{pin} for a bare-land PIN entry."""
    ymd = re.sub(r'\D', '', str(valuation_date or ''))[:8] or '00000000'
    try:
        if zone is not None and street is not None and building is not None:
            loc = f'{int(zone):02d}{int(street):03d}{int(building):03d}'
        elif pin:
            loc = f'P{re.sub(r"[^0-9A-Za-z]", "", str(pin))[:12]}'
        else:
            loc = '00000000'
    except Exception:
        loc = '00000000'
    base = f'TH-{ymd}-{loc}'
    return f'{base}-{refine_fp4}' if refine_fp4 else base


def _clamp_valuation_range(valuation):
    """Sprint 2.22.0b.59 — belt-and-braces invariant: the SERVED range must satisfy
    low <= amount <= high. Enforced as a FINAL pass (after every range-writing path —
    teardown / luxury-new / income_led / leadership gate / range_expansion / a9 widened-
    elasticity — and before the report fingerprint) so a range inversion can NEVER reach a
    user, whichever path set the range. Closes the geo_full low-raise theoretical residual
    (`:5157` raises low to the cost floor without checking it against `high`) + any future
    path. PURE on the passed dict; idempotent; a NO-OP when the invariant already holds —
    verified byte-identical on the 5 fixtures + the two documented 54/788/10 + 55/1056/60
    cases (b20's leadership gate already routes them through the E25-safe cost_led path).
    Acts ONLY when amount/low/high are all present + numeric; refusals (amount None) are
    left untouched. Swallows errors → never breaks evaluate. Bool is excluded from numeric
    (isinstance(True, int) is True in Python)."""
    try:
        if not isinstance(valuation, dict):
            return
        a = valuation.get('amount')
        lo = valuation.get('low')
        hi = valuation.get('high')
        if any(v is None or isinstance(v, bool) or not isinstance(v, (int, float))
               for v in (a, lo, hi)):
            return
        new_lo = min(lo, a)   # the central figure is the ceiling for `low`
        new_hi = max(hi, a)   # ...and the floor for `high`  → low <= amount <= high (so low <= high)
        if new_lo != lo:
            valuation['low'] = new_lo
        if new_hi != hi:
            valuation['high'] = new_hi
    except Exception:
        pass


def _attach_report_identity(output, zone, street, building, pin, refine_inputs):
    """Set output['report_ref'] + output['report_fp'] + output['report_fp_basis'] from the
    SETTLED valuation (call LATE — after the headline/leadership are final). The basis dict
    is the verify payload (what /verify recomputes over). DORMANT fp (None) without a key.
    Additive — never touches amount/low/high/method/rule. Swallows errors."""
    try:
        v = output.get('valuation') or {}
        rule = ((v.get('leadership') or {}).get('rule')
                or (v.get('income_triangulation') or {}).get('mode')
                or v.get('method') or '')
        addr = output.get('address') or (f'{zone}/{street}/{building}'
                                         if zone is not None else (f'PIN {pin}' if pin else ''))
        date = output.get('valuation_date')
        engine = output.get('engine_version') or ENGINE_VERSION
        amount, low, high = v.get('amount'), v.get('low'), v.get('high')
        canonical = _report_canonical(addr, date, engine, amount, low, high, rule)
        output['report_ref'] = _report_ref(zone, street, building, pin, date,
                                            _refine_fp4(refine_inputs))
        output['report_fp'] = _report_fingerprint(canonical)   # None when no key (dormant)
        output['report_fp_basis'] = {
            'version': REPORT_FP_VERSION, 'address': addr, 'date': date, 'engine': engine,
            'amount': amount, 'low': low, 'high': high, 'rule': rule,
        }
    except Exception:
        pass


def _cost_triangulation(primary, cost, land_floor, asset_type, dispersion_gated, age_for_gate):
    """SHIP-NOW = the DOWN-re-anchor ONLY. Fires when an OLD villa on a thin/widened
    (NOT clean bracket, NOT dispersion-gated) market is over-anchored AND the cost
    UNDERCUTS the market by > THRESHOLD → reconciled range [max(land_floor, cost) …
    market(muted)], range_is_headline, MUC high, with the COST as the informed lower
    anchor (vs §6 widen_down's bare land). Returns a decision dict or None. Pure.
    Convergent-confirm + the UP-lift are GATED-to-next (need actual-not-system age)."""
    if asset_type not in ('standalone_villa', 'house', 'villa'):
        return None
    if not primary or not primary.get('value'):
        return None
    if not cost or not cost.get('value'):
        return None
    method = primary.get('method')
    comp = primary['value']
    cost_val = cost['value']
    # age-gate (B): OLD stock only (a new villa's cost ≈ full → never undercuts; belt-and-braces).
    if age_for_gate is None or age_for_gate < COST_REANCHOR_MIN_AGE_Y:
        return None
    # thin/widened path only (a10/a14 own dispersion-gated pools); over-anchored (land < market).
    if method not in _COST_REANCHOR_METHODS or dispersion_gated:
        return None
    if not (land_floor and land_floor < comp):
        return None
    # the cost must UNDERCUT the market by > THRESHOLD ((market − cost)/cost).
    if cost_val <= 0 or (comp - cost_val) / cost_val <= COST_REANCHOR_UNDERCUT_T:
        return None
    return {
        'mode': 'cost_reanchor_down',
        'amount': comp,                                   # central muted via range_is_headline
        'low': max(land_floor, cost_val),
        'high': primary.get('high') or comp,
        'muc_level': 'high',
        'cost_value': cost_val,
        'land_floor': land_floor,
        'comparison_value': comp,
        'undercut_pct': round((comp - cost_val) / cost_val * 100, 1),
        'cost_detail': cost,
    }


# §20.9 cost down-re-anchor user-facing notes (AR + EN).
COST_REANCHOR_NOTE_AR = ('وسيط المقارنة ({comp} ر.ق) مرتفع لقلّة الصفقات القريبة في النوع والمساحة '
                         'ولأنه لا يأخذ نوع البناء وحالته. منهج التكلفة (الأرض {land} ر.ق + بناءٌ مُهلَك) يضع حدّاً أدنى '
                         'مؤسَّساً عند {cost} ر.ق — فالنطاق يمتدّ منه إلى وسيط المقارنة دون تثبيت رقم '
                         'مركزي. العمر تقديريّ (حدّ أدنى) وعدم اليقين مرتفع.')
COST_REANCHOR_NOTE_EN = ('The comparison median ({comp} QAR) is high — thin comparables, and it ignores '
                         'built type and condition. The Cost approach (land {land} QAR + a depreciated '
                         'building) sets a grounded floor at {cost} QAR — so the range spans from it up '
                         'to the comparison median, with no pinned central. Age is indicative (a floor) '
                         'and uncertainty is high.')


# §20.9 GATED slice (Sprint 2.22.0b.13) — Lever 1: convergent-TRIM (down, USER-ACTUAL-AGE-GATED).
# When an OLD over-anchored thin/widened villa has a USER-supplied actual age AND the ACTUAL-age DRC
# cost sits BELOW the market by ≤ 30% (the convergent zone b11's >30% down-re-anchor leaves untouched),
# the actual-age cost becomes the LEADING reconciled figure and the market is muted inside
# [max(land_floor, cost) … market]. recon R1/R2 (PHASE0_2p22p0b13): gates on age_source=='user' +
# effective_age = max(user, system) (system stays a floor; a younger user age can't raise retention).
# DISJOINT from cost_reanchor_down at 30% (reanchor >0.30 on system cost; trim ≤0.30 on actual cost).
# Lever 2 (UP-lift) DROPPED — recon overturned it (DRC cost < the V002/V003 sale; that under-anchor is
# B-2 GT-corpus calibration, not a cost lift). Pure; never mutates.
COST_TRIM_UNDERCUT_T = 0.30
_COST_TRIM_METHODS = _COST_REANCHOR_METHODS   # thin / widened / widened_indicative / preliminary


def _cost_trim(primary, cost_act, land_floor, asset_type, dispersion_gated, eff_age):
    """Lever 1: the ACTUAL-age cost LEADS an OLD over-anchored thin/widened villa down, the market
    muted as the upper bound. Caller passes the actual-age cost (built on max(user, system) age) and
    ONLY when age_source=='user'. Returns a decision dict or None. Pure. Excludes clean bracket /
    dispersion-gated / land-anchored. DISJOINT from cost_reanchor_down (that owns undercut > 30%)."""
    if asset_type not in ('standalone_villa', 'house', 'villa'):
        return None
    if not primary or not primary.get('value'):
        return None
    if not cost_act or not cost_act.get('value'):
        return None
    if eff_age is None or eff_age < COST_REANCHOR_MIN_AGE_Y:        # OLD stock only (the b11 age-gate)
        return None
    if primary.get('method') not in _COST_TRIM_METHODS or dispersion_gated:   # thin/widened only (a10/a14 own gated)
        return None
    comp = primary['value']
    cost_val = cost_act['value']
    if not (land_floor and land_floor < comp):                     # over-anchored (NOT land-anchored)
        return None
    if cost_val <= 0 or cost_val >= comp:                          # cost must be strictly BELOW the market
        return None
    undercut = (comp - cost_val) / cost_val
    if undercut > COST_TRIM_UNDERCUT_T:                            # > 30% is b11's cost_reanchor_down, not the trim
        return None
    return {
        'mode': 'cost_trim_convergent',
        'amount': cost_val,                                        # the actual-age cost LEADS
        'low': max(land_floor, cost_val),
        'high': comp,                                              # market muted as the upper bound
        'muc_level': 'high',
        'cost_value': cost_val,
        'land_floor': land_floor,
        'comparison_value': comp,
        'undercut_pct': round(undercut * 100, 1),
        'effective_age': eff_age,
        'cost_detail': cost_act,
    }


COST_TRIM_NOTE_AR = ('استناداً إلى العمر الفعلي المُدخَل ({age} سنة)، يضع منهج التكلفة (الأرض {land} ر.ق + '
                     'بناءٌ مُهلَك) القيمةَ الأقربَ عند {cost} ر.ق؛ ووسيط المقارنة ({comp} ر.ق) — المرتفع لقلّة '
                     'الصفقات القريبة في النوع والحالة — يُمثّل الحدّ الأعلى للنطاق. عدم اليقين مرتفع.')
COST_TRIM_NOTE_EN = ('Using the entered actual age ({age}y), the Cost approach (land {land} QAR + a depreciated '
                     'building) sets the closer value at {cost} QAR; the comparison median ({comp} QAR) — high '
                     'for thin like-type/condition comparables — is the upper bound of the range. Uncertainty is high.')


# ── Sprint 2.22.0b.16 (B-2 EARLY slice) — V001-anchored OLD-STOCK central re-anchor (n=1, DISCLOSED) ──
# 🔴 Gate-2 VALUE-AFFECTING on the Marikh class ONLY: an OLD villa on a thin/widened (NOT clean-bracket,
# NOT dispersion-gated, NOT land-anchored) market whose comparable pool is DOMINATED by a premium stratum
# (luxury_new / modern_stock, share ≥ 40%) with NO user luxury/new/renovated input, where the thin median
# exceeds the re-anchor candidate by a MATERIAL margin. The candidate (bake-off PHASE0_b16_bakeoff.md,
# HALT band PASS) = M4 ≡ min(max(M3 system-age DRC cost, M1c/M2 basis), thin median):
#   M2 (precedence — the supersession ladder's first rung): the MATCHING stratum (aging_stock) median
#      ppm² × the effective plot, when that stratum has n ≥ 10;
#   M1c (else): the subject geo-bracket [plot×0.8, plot×1.2] FULL-window ppm² median × the effective plot
#      (the §20.10.1 'defensible' estimator; n ≥ 5 enforced in subject_geo_full_ppm2 — else ABSTAIN).
# Materiality T = 20% — anchored on the project's own clean-stock asking-premium ceiling (8–20%,
# Empirical_Findings §3): within 20% = normal market noise → CONVERGED, no correction (V001 measured
# +15.2% → abstains, stays 3.8M in its band); beyond = the Marikh-class distortion (Marikh +58.2% → fires).
# SUPERSESSION LADDER (documented): GT intakes log engine_estimate_at_intake (GT_INTAKE_KIT_v1 §3, manual
# channel) → at matching-stratum n≥10 M2 takes precedence over M1c automatically (wired here) → at n≥20
# the 'indicative' label upgrades (a FUTURE signed-copy step — Gate-2 wording; not invented here).
# Precedence for the central: income_led > b13 cost_trim > THIS > b11 cost_reanchor (floor-only) >
# widen_down — b11's reanchor leaves the central UN-led BY DESIGN (§20.45 'no invented central'); this
# slice UPGRADES that un-led central on the stratum-mismatch subset and INHERITS the b11 cost floor as
# its range-low (PHASE0_b16_bakeoff §3 premise resolution — the signed §4 HALT band requires it).
OSR_MARGIN_T = 0.20
OSR_DOM_SHARE_T = 40
OSR_DOM_STRATA = ('luxury_new', 'modern_stock')
OSR_M2_MIN_N = 10
_OSR_METHODS = ('comparison_thin', 'comparison_widened', 'comparison_widened_indicative')
# Verbatim signed label (brief §4) + the muted raw-median wording.
OSR_LABEL_AR = ('إعادة إرساء استرشاديّة لمخزونٍ قديم — معايَرة على تقييم معتمد واحد (V001) + '
                'النافذة الكاملة لوزارة العدل؛ تتحسّن تلقائيّاً مع كلّ صفقة موثَّقة جديدة')
OSR_LABEL_EN = ('Indicative old-stock re-anchor — calibrated on ONE certified appraisal (V001) + the '
                'full Ministry-of-Justice window; improves automatically with every documented transaction')
OSR_NOTE_AR = (OSR_LABEL_AR + '. وسيط العيّنة الخام {comp} ر.ق — مدفوع بشريحةٍ أعلى سعراً مسيطرة ({share}%)؛ '
               'أساس الإرساء: وسيط سعر المتر للنافذة الكاملة ضمن شريحة مساحة العقار (n={n})، '
               'وأرضيّة النطاق منهج التكلفة/الأرض.')
OSR_NOTE_EN = (OSR_LABEL_EN + '. The raw sample median {comp} QAR is driven by a dominant premium '
               'stratum ({share}%); the re-anchor basis is the FULL-window per-m² median within the '
               'subject size bracket (n={n}), with the cost/land floor as the range low.')


def _old_stock_reanchor(primary, sgf, aging_cell, cost, land_floor, asset_type,
                        dispersion_gated, age, age_basis, dom_name, dom_share,
                        plot_area_m2, user_premium, finish=None, finish_age=None,
                        finish_bua=None):
    """B-2 EARLY slice decision (pure; never mutates). Returns a dict or None (= ABSTAIN).
    Fires iff villa/house · thin/widened/widened_indicative · NOT dispersion-gated · OLD
    (sys/effective age ≥ 10 OR vintage_capped, E24) · dominant stratum ∈ OSR_DOM_STRATA with
    share ≥ 40 · NO user new/renovated input · over-anchored (land < market) · a basis exists
    (M2 stratum n≥10, else M1c geo-full n≥5) · margin (market − candidate)/candidate > 20%.
    Sprint 2.22.0b.18 (§A2 LUXURY-EXIT fix): a user luxury/high finish no longer ABSTAINS
    (the Phase-0-verified 3.4M→5.4M raw-median revert) — it prices THROUGH the replacement
    coefficient as a FINISH-DELTA on the plain re-anchor base (finish/finish_age/finish_bua);
    delta incomputable (no sys-age/BUA) → conservative abstain (the pre-b18 behavior)."""
    if asset_type not in ('standalone_villa', 'house', 'villa'):
        return None
    if not primary or not primary.get('value'):
        return None
    if primary.get('method') not in _OSR_METHODS or dispersion_gated:
        return None
    old = ((age is not None and age >= COST_REANCHOR_MIN_AGE_Y)
           or (age_basis == 'vintage_capped'))
    if not old:
        return None
    if user_premium:
        return None
    _fin = (finish or '').strip().lower()
    if _fin in ('high', 'luxury') and (finish_age is None or not finish_bua):
        return None                                   # b18: finish lead needs a computable delta
    if dom_name not in OSR_DOM_STRATA or not dom_share or dom_share < OSR_DOM_SHARE_T:
        return None
    comp = primary['value']
    if not (land_floor and land_floor < comp):
        return None                                   # land-anchored → not over-anchored
    basis = None
    if (aging_cell and (aging_cell.get('n') or 0) >= OSR_M2_MIN_N
            and aging_cell.get('median_per_m2') and plot_area_m2):
        basis = {'kind': 'matching_stratum', 'ppm2': aging_cell['median_per_m2'],
                 'n': aging_cell['n'],
                 'value': round(aging_cell['median_per_m2'] * plot_area_m2)}
    elif sgf and sgf.get('value_full'):
        basis = {'kind': 'geo_full', 'ppm2': sgf.get('ppm2_median_full'),
                 'n': sgf.get('n_full'), 'value': sgf['value_full']}
    if not basis or not basis['value'] or basis['value'] <= 0:
        return None                                   # no defensible basis → abstain cleanly
    cost_val = (cost or {}).get('value')
    cand = max(cost_val, basis['value']) if cost_val else basis['value']   # M4: M3 floor
    cand = min(cand, comp)                            # bounded above by the thin median
    if cand <= 0:
        return None
    margin = (comp - cand) / cand
    if margin <= OSR_MARGIN_T:
        return None                                   # converged (≤ normal asking noise) → abstain
    # ── Sprint 2.22.0b.18 (§A2 / §C(ii)): FINISH-DELTA on the plain base ──
    # delta = (RCN_finish − RCN_ordinary) × retention(RAW system age) × BUA. The retention is
    # RAW (no condition penalty): TD-93317 reproduces the certified valuer ONLY on the raw
    # documented age (PHASE0_b18 §2 — net 1,900 = RCN_high 3,000 × 0.64 = 1−18/50). The firing
    # decision (margin gate above) stays on the PLAIN candidate; the delta is pricing on top.
    # HARD MONOTONICITY RAIL: plain lead ≤ finish lead ≤ the raw thin median.
    finish_delta = 0
    if _fin in ('high', 'luxury'):
        _ret_raw = _cost_retention(finish_age, _fin)
        if _ret_raw:
            _d = round((COST_RCN_BY_FINISH[_fin] - COST_RCN_DEFAULT) * _ret_raw * finish_bua)
            _lead = max(cand, min(cand + _d, comp))
            finish_delta = _lead - cand
            cand = _lead
    low = max(land_floor, cost_val) if cost_val else land_floor
    return {
        'mode': 'old_stock_reanchor_indicative',
        'amount': cand,
        'finish': (_fin if finish_delta else None),
        'finish_delta': finish_delta,
        'low': low,
        'high': comp,                                 # the raw thin median stays visible (muted high)
        'muc_level': 'high',
        'basis': basis,
        'cost_value': cost_val,
        'land_floor': land_floor,
        'comparison_value': comp,
        'margin_pct': round(margin * 100, 1),
        'dominant_stratum': dom_name,
        'dominant_share_pct': dom_share,
    }


# ══ Sprint 2.22.0b.20 — EVIDENCE-CONDITIONAL LEADERSHIP (🔴 Gate-2 SIGNED) ══════════════
# Anas's binding F6 signature 2026-06-11: docs/SESSION_CLOSE_2026-06-11_F6_SIGNED.md §1
# (7/13 = 54% cost-led on the Phase-0 cohort, incl. امريخ 3.4M → 2,378,094); normative spec
# = docs/BRIEF_conditional_leadership_SIGNED.md §3. The headline leader is decided by
# EVIDENCE QUALITY per case (E23 — «الوسيط لا يُؤتمن بقرار ولا يُعدم بقرار — يُمتحن بالتشتت»):
#   RULE 1 — matched-stratum pool: market leads iff n>=10 matched AND disp36<0.30 AND
#            stratum match (subject band = the E26 SYSTEM-age band — the G5 proxy).
#   RULE 2 — an UNMATCHED geo-full pool sustains market leadership ONLY at the reliable
#            bar: n_geo_full>=20 AND dispersion(geo_full)<0.30 → disclosure «حوض جغرافي
#            غير مطابق طبقياً» + MUC raised one notch + the cost line/floor.
#   else (thin OR dispersed OR untestable) → COST LEADS: F3(b) range [cost … market-muted],
#            MUC high, disclosed-indicative.
# RAILS: E25 LOCKED (cost NEVER leads upward — المعراض proof; double-weak clause: when
# cost >= market AND the pool failed the gates → market keeps the lead + a MANDATORY
# divergence line + MUC >= high) · E26 (system age leads every retention) · the §4-a
# INVARIANT (the headline always lies between the cost-informed floor and the market
# figure) · no invented central · F2=B (re-surveyed age → untestable band + the verbatim
# disclosure) · F4/F5 subsumed (dispersed / strata-absent fall into the else-branch).
# SUBSUMES the b6 widen_down + b11 cost_reanchor_down + b16 old_stock_reanchor BRANCHES
# (the pure calculators above are KEPT as superseded references — their isolated tests
# stay green); income_led precedence, the b13/b18 age-sensitivity line, and the b4
# explicit teardown/luxury levers are UNCHANGED.

LEAD_MATCHED_MIN_N = 10            # RULE 1 matched-stratum depth bar
LEAD_GEO_FULL_MIN_N = 20           # RULE 2 reliable bar (geo-full pool)
LEAD_DISPERSION_T = 0.30           # the same reliability bar as STAGE1_DISPERSION_T

_LEAD_BAND_STRATA = {'old': ('land_priced', 'aging_stock'),
                     'modern': ('modern_stock',),
                     'new': ('luxury_new',)}
_LEAD_ASSET_TYPES = ('standalone_villa', 'house', 'villa')

# b19-signed verbatim labels (SESSION_CLOSE §7 — «معامل الإحلال» stays reserved for soil).
COST_STACK_LABEL_AR = 'قيمة التكلفة (أرض + بناء مُهلَك) — نهج DRC'
COST_STACK_SUB_AR = 'استرشادي، مُعايَر على تقييم معتمد واحد (V001)'
COST_STACK_LABEL_EN = 'Cost value (land + depreciated building) — DRC approach'
COST_STACK_SUB_EN = 'Indicative — calibrated on a single certified appraisal (V001)'
LEAD_COST_NOTE_AR = ('اعتمدنا كلفةَ البناء (استرشاديّة) لقلّة الصفقات المماثلة القريبة '
                     '(عددها {n}، وتشتّتها {d}). النطاق من قيمة الكلفة {cost} ر.ق إلى وسيط '
                     'السوق {comp} ر.ق (معروضاً) — لا رقم مركزيّ مُخترَع.')
LEAD_COST_NOTE_EN = ('Indicative cost leadership — the comparison pool failed the '
                     'reliability test (n={n}, dispersion={d}). The range spans the cost '
                     'value {cost} QAR up to the muted market median {comp} QAR — no '
                     'invented central.')
LEAD_COST_AGE_HONESTY_AR = ('تقدير الإهلاك يزداد ذاتيةً مع التقادم؛ معايرتنا على شيت مثمّن '
                            'وأرضية السوق تخففه.')
LEAD_COST_AGE_HONESTY_EN = ('Depreciation estimates grow more subjective with age; our '
                            'calibration on a certified appraisal sheet and the market land '
                            'floor mitigate this.')
LEAD_GEO_FULL_NOTE_AR = ('يقود السوقُ عبر حوض جغرافي غير مطابق طبقياً (n={n}، تشتت={d} — '
                         'اجتاز عتبة الموثوقية)؛ رُفع التحفظ المادي درجةً وأُدرجت قيمة '
                         'التكلفة أرضيةً للنطاق.')
LEAD_GEO_FULL_NOTE_EN = ('The market leads via a geographically-pooled, stratum-UNMATCHED '
                         'sample (n={n}, dispersion={d} — passes the reliability bar); '
                         'material uncertainty raised one notch and the cost value applied '
                         'as the range floor.')
LEAD_E25_NOTE_AR = ('كلفةُ البناء ({cost} ر.ق) أعلى من وسيط بيع السوق ({comp} ر.ق)؛ '
                    'والمباني تُباع بسعر السوق لا بكلفة بنائها، فاعتمدنا سعر السوق '
                    '(والكلفةُ أرضيةٌ لا سقفٌ للقيمة). عدم اليقين مرتفع لقلّة الصفقات المماثلة.')
LEAD_E25_NOTE_EN = ('Approach divergence: the cost value ({cost} QAR) sits ABOVE the market '
                    'median ({comp} QAR) — the market figure keeps the lead as the '
                    'anti-inflation cap (cost is a floor, never a market proxy), although '
                    'the comparison pool failed the reliability test; uncertainty is high.')
LEAD_RESURVEY_NOTE_AR = 'عمر مُعاد تسجيله — غير موثوق'          # F2=B verbatim
LEAD_RESURVEY_NOTE_EN = 'Re-registered survey age — unreliable'
LEAD_COST_UNAVAILABLE_AR = 'قيمة التكلفة غير متاحة — {reason}'
_MUC_LADDER = ('low', 'moderate', 'high', 'critical')


def _e26_subject_band(age_floor_years, age_basis):
    """The subject's expected stratum band from the E26 SYSTEM age (the G5 proxy).
    Returns 'old' | 'modern' | 'new' | None (= UNTESTABLE — incl. the F2=B re-survey
    case: vintage_capped with a near-zero system age, where the true age is unknown)."""
    if age_basis == 'vintage_capped':
        if age_floor_years is not None and age_floor_years >= 10:
            return 'old'                      # the 2009-12 survey cliff: a true age FLOOR
        return None                           # re-survey re-stamp → untestable (F2=B)
    if age_floor_years is None:
        return None
    if age_floor_years >= 10:
        return 'old'
    if age_floor_years >= 2:
        return 'modern'
    return 'new'


def _matched_stratum_n(strata_dict, band):
    """Effective n of the subject's matched stratum band (None when untestable)."""
    if band is None or not isinstance(strata_dict, dict):
        return None
    try:
        return sum(int((strata_dict.get(k) or {}).get('n') or 0)
                   for k in _LEAD_BAND_STRATA.get(band, ()))
    except Exception:
        return None


def _bracket_disp36(moj_ref_dict, plot_eff):
    """The subject-bracket 36mo ppm² dispersion + n_36 from the moj_reference villa
    brackets (the same metric the a14 gate uses). Returns (dispersion, n_36) —
    (None, None) when the cell is absent/unparsable (→ untestable, fail-safe)."""
    try:
        if not plot_eff or plot_eff <= 0:
            return None, None
        brackets = (((moj_ref_dict or {}).get('categories') or {})
                    .get('villa') or {}).get('size_brackets') or {}
        for label, cell in brackets.items():
            try:
                lo, hi = label.split('-')
                if float(lo) <= float(plot_eff) < float(hi):
                    return cell.get('ppm2_dispersion_36'), cell.get('n_36')
            except Exception:
                continue
        return None, None
    except Exception:
        return None, None


def _muc_one_notch(level):
    """Raise a MUC level by exactly one notch (RULE 2)."""
    try:
        i = _MUC_LADDER.index((level or 'moderate'))
        return _MUC_LADDER[min(i + 1, len(_MUC_LADDER) - 1)]
    except Exception:
        return 'high'


def _leadership_gate(amount, asset_type, matched_n, disp36, stratum_match, band,
                     resurvey, geo_full, cost, land_floor):
    """The SIGNED unified rule (BRIEF_conditional_leadership_SIGNED §3). PURE — returns
    the leadership decision dict, or None for out-of-scope inputs (non-villa/house, no
    market figure). Never mutates. The caller applies the decision + emissions."""
    if asset_type not in _LEAD_ASSET_TYPES:
        return None
    if not amount or amount <= 0:
        return None
    g_n = (geo_full or {}).get('n_full')
    g_disp = (geo_full or {}).get('dispersion_full')
    cost_val = (cost or {}).get('value')
    base = {
        'matched_n': matched_n, 'dispersion_36': disp36, 'stratum_match': stratum_match,
        'band': band, 'resurvey': bool(resurvey),
        'geo_full_n': g_n, 'geo_full_dispersion': g_disp,
        'cost_value': cost_val, 'land_floor': land_floor,
        'market_value': amount,
        'thresholds': {'matched_min_n': LEAD_MATCHED_MIN_N,
                       'geo_full_min_n': LEAD_GEO_FULL_MIN_N,
                       'dispersion_t': LEAD_DISPERSION_T},
    }
    # RULE 1 — matched-stratum pool.
    if (matched_n is not None and matched_n >= LEAD_MATCHED_MIN_N
            and disp36 is not None and disp36 < LEAD_DISPERSION_T
            and stratum_match is True):
        return {**base, 'leader': 'market', 'rule': 'matched'}
    # RULE 2 — unmatched geo-full pool at the reliable bar.
    if (g_n is not None and g_n >= LEAD_GEO_FULL_MIN_N
            and g_disp is not None and g_disp < LEAD_DISPERSION_T):
        return {**base, 'leader': 'market', 'rule': 'geo_full',
                'muc_notch': True, 'cost_floor': cost_val}
    # else-branch: the pool failed → cost leads, subject to the rails.
    if not cost_val or cost_val <= 0:
        # No cost figure to lead with (input-starved §6) → market keeps the lead,
        # disclosed + MUC >= high (a failed pool with no counterweight).
        return {**base, 'leader': 'market', 'rule': 'cost_unavailable',
                'muc_min_high': True}
    if cost_val >= amount:
        # E25 RAIL (LOCKED): cost NEVER leads upward — the market figure is the
        # anti-inflation cap; double-weak clause → divergence line + MUC >= high.
        return {**base, 'leader': 'market', 'rule': 'e25_capped',
                'muc_min_high': True, 'divergence': True}
    return {**base, 'leader': 'cost', 'rule': 'cost_led',
            'low': max(land_floor or 0, cost_val),       # cost >= land by construction
            'high': amount,                              # F3(b): the muted market median
            'muc_min_high': True}


def _build_unified_output(ev, primary, cost, income, reconciliation, v3_result,
                          geo_v2_result, listings_result, geometric, audience,
                          user_inputs, stock_strata=None) -> Dict:
    output = {
        'status': 'ok',
        'engine_version': ENGINE_VERSION,
        # Methodology line — universal bare statement of the basis of estimate.
        # Engine reality (Phase 0 mechanical audit, Sprint 2.22.0a.4): valuation =
        # primary['value'] = Sales Comparison alone in 100% of cases; cost/income
        # are convergence checks only, never blended into the headline number.
        # The pre-Amendment design spec'd a status-aware three-branch line; that was
        # collapsed to this single constant per the 2.22.0a.4 Amendment (multi-AI
        # validated — GPT-5 + Gemini, Rule #54). reconciliation['status'] stays
        # computed and JSON-stored (see output['reconciliation'] below) for analytics
        # and frontend secondary-surface use, but the headline asserts only the
        # approach actually applied (silence on approaches not applied).
        # Cite: RICS Red Book Global Standards (effective 31 January 2025) / IVS 106
        # (Documentation and Reporting). Sprint 2.22.0a.8 adds a secondary methodology
        # surface (rics_methodology_note_ar/en below) citing the approach (VPS 3 / IVS 103)
        # + the new models standard (VPS 5 / IVS 105) + the report (VPS 6 / IVS 106).
        # ── T2.8 (Sprint 2.22.0a.4): A→D fold (main path) ──
        # The main-path methodology_disclaimer_ar (Layer A) duplicated the
        # top-level `disclaimer` (Layer D — the canonical not-a-formal-valuation
        # C4 string). P0.1 confirmed A was JSON-only (never rendered in the UI
        # brief), so removing it is render-invisible. Per the completed multi-AI
        # Resolution (docs/MULTI_AI_VALIDATION_BATCH_2p22p0a4.md, GPT-5 + Gemini,
        # Rule #54) the redundant disclaimer half folds into D. The methodology
        # provenance is NOT promoted to the visible headline: the Resolution's
        # "reduce, not add" theme + the bare-line outcome keep methodology_ar a
        # single sentence. Sprint 2.22.0a.8 realises the previously-deferred
        # "secondary expandable surface" as rics_methodology_note_ar/en (below) +
        # a collapsible block in index.html — NOT on this bare line, which stays bare.
        # The other 5 methodology_disclaimer_ar sites carry genuine per-path
        # methodology caveats (NOT duplicates of D) and are intentionally left
        # untouched. (@2703's "إنتاج تقييم موثوق" stays — test c3 pins it.)
        'methodology_ar': 'أساس التقدير هو منهج المقارنة بالمبيعات.',
        # ── Sprint 2.22.0a.8: secondary RICS/IVS methodology + models-standard note ──
        # The "secondary expandable surface" deferred in 2.22.0a.4. Represents the AVM
        # models standard (VPS 5 / IVS 105, new in the 2025 edition) and the IVS 105
        # disclosure that an AVM is a supplementary tool — not a standalone compliant
        # valuation without a licensed valuer (Stage 5). This doubles as the A7
        # disclosure (why rics_compliant=false pre-inspection). Rendered on a quiet
        # collapsible block (index.html), NOT the headline — the bare methodology_ar
        # above is untouched. Latin standard codes are LRM-wrapped (‎) per Op. #25.
        'rics_methodology_note_ar': (
            'يستند هذا التقدير إلى منهج المقارنة بالمبيعات '
            '(‎VPS 3‎ / ‎IVS 103‎)، ضمن '
            '‎RICS Red Book Global Standards (effective 31 January 2025)‎ '
            'بما في ذلك معيار نماذج '
            'التقييم (‎VPS 5‎ / ‎IVS 105‎)، مع الإفصاح عن '
            'عدم اليقين الجوهري (‎VPGA 10‎) في التقرير '
            '(‎VPS 6‎ / ‎IVS 106‎). النموذج الآلي '
            '(‎AVM‎) أداة مساعدة ولا يُنتج بمفرده تقييماً نهائياً '
            'مطابقاً للمعايير دون مراجعة مُقيِّم مُرخّص.'
        ),
        'rics_methodology_note_en': (
            'This estimate uses the Sales Comparison approach (VPS 3 / IVS 103), '
            'within RICS Red Book Global Standards (effective 31 January 2025) '
            'including the valuation models standard (VPS 5 / IVS 105), with '
            'material valuation uncertainty disclosed (VPGA 10) in the report '
            '(VPS 6 / IVS 106). An automated valuation model (AVM) is a '
            'supplementary tool and does not by itself produce a final '
            'standards-compliant valuation without review by a licensed valuer.'
        ),
        'address': getattr(ev, 'address', None),
        'valuation_date': getattr(ev, 'valuation_date', None),
        'district': getattr(ev, 'gis_district_aname', None),
        'plot_area_m2': getattr(ev, 'plot_area_m2', None),
        'asset_type': getattr(ev, 'asset_type', None),
        'audience': audience,
        'user_inputs': user_inputs,
    }

    # ── GPS coordinates (for map links) ──
    rpr = getattr(ev, 'raw_property_report', None)
    if isinstance(rpr, dict):
        gps = rpr.get('gps')
        if gps and isinstance(gps, (list, tuple)) and len(gps) >= 2:
            # GPS stored as [lon, lat] per qatar_gis convention
            output['gps'] = {'lon': gps[0], 'lat': gps[1]}
        # Sprint 2.22.0b.9 — property-basis traceability (PIN / رقم الكهرباء /
        # water / building-age FLOOR) from the QARS attributes already carried in
        # raw_property_report. DISPLAY-ONLY / value-invariant: the age estimate is
        # NEVER written into user_inputs.building_age_years (that would be Gate-2).
        output['property_basis'] = _build_property_basis(
            rpr.get('pin'), rpr.get('electricity_no'),
            rpr.get('water_no'), rpr.get('surveyed_date'))

    # ── Primary valuation (from comparison approach only) ──
    if primary:
        output['valuation'] = {
            'amount':       _r100k(primary['value']),
            'low':          _r100k(primary.get('low')),
            'high':         _r100k(primary.get('high')),
            'method':       primary['method'],
            'method_label_ar': primary['method_label_ar'],
            'source_ar':    primary['source_ar'],
            'n_transactions': primary['n'],
            'window_used':  primary.get('window_used'),  # (vi)(b) Methodology-brief window surface
        }
    else:
        output['valuation'] = {
            'amount': None,
            'method': 'insufficient_data',
            'method_label_ar': 'بيانات غير كافية للتقييم',
            'source_ar': 'لم نجد عينة كافية من معاملات المقارنة',
        }

    # Sprint 2.22.0a/2 — tier_label top-level emission (Y3 helper, KICKOFF §4.3 + F1).
    # This is the Type-A bracket wrapper consuming _choose_primary_valuation()
    # outputs (comparison_bracket / _widened / _widened_indicative / _thin /
    # _preliminary). primary['method'] varies; helper dispatches to 'analytical_range'
    # for value-producing methods, None for insufficient_data fallback.
    output['tier_label'] = _tier_label_for(output.get('valuation', {}).get('method'))

    # Sprint 2.22.0a/5 — refusal_reason emission for Type-A else branch
    # (when primary is None, method=='insufficient_data'). When primary is
    # set (value-producing), _compute_refusal_reason returns None defensively.
    # district + plot_area_m2 from output where available.
    _method = output.get('valuation', {}).get('method')
    output['refusal_reason'] = _compute_refusal_reason(
        method=_method,
        asset_type=output.get('asset_type'),
        district_ar=output.get('district'),
        plot_area_m2=output.get('plot_area_m2'),
    )

    # ── Frontend compatibility: keep moj_sample_size field ──
    output['moj_sample_size'] = primary['n'] if primary else 0

    # ── Cross-checks (explicitly labeled as such, NOT in valuation) ──
    if cost:
        output['cost_approach'] = {
            'total_replacement_value': cost['value'],
            'land_value': cost.get('land_value'),
            'building_value_new': cost.get('building_value_new'),
            'building_value_depreciated': cost.get('building_value_depreciated'),
            'building_age_years': cost.get('building_age_years'),
            'depreciation_rate_pct': cost.get('depreciation_rate_pct'),
            'bua_m2': cost.get('bua_m2'),
            'tier': cost.get('tier'),
            'method_label_ar': cost['method_label_ar'],
            'role_ar': cost['role_ar'],
        }
    if income:
        output['income_approach'] = {
            'income_value': income['value'],
            'annual_rent': income['annual_rent'],
            'monthly_rent': income['monthly_rent'],
            'rent_source': income['rent_source'],
            'rent_source_ar': income['rent_source_ar'],
            'noi': income['noi'],
            'cap_rate': income['cap_rate'],
            'cap_rate_label_ar': income['cap_rate_label_ar'],
            'gross_yield': income['gross_yield'],
            'net_yield': income['net_yield'],
            'yield_flag_ar': income['yield_flag_ar'],
            'caveats': income.get('caveats', []),
            'method_label_ar': income['method_label_ar'],
            'role_ar': income['role_ar'],
        }

    # ── Sprint 2.16.0: Stock Stratification (EMPIRICAL_FINDINGS Rule E4) ──
    # Surfaces per-stratum villa medians (land_priced / aging / modern / luxury_new)
    # to expose under-valuation of modern stock by the blended bracket median.
    # Headline `valuation.amount` is unchanged in this sprint.
    if stock_strata:
        output['stock_strata'] = stock_strata

    # ── Reconciliation statement (RICS Red Book) ──
    output['reconciliation'] = reconciliation

    # ── Accuracy (data-quality tier with customer-friendly labels) ──
    # Labels avoid jargon like "ثقة عالية" alone — instead explain what the
    # number means in concrete terms a non-technical customer understands.
    n = output.get('moj_sample_size', 0) or 0
    # Sprint 2.22.0a.2 C3: relabel "تقدير موثوق" / "تقدير إرشادي" tier
    # badges to شواهد taxonomy (Anas-locked override per resume KICKOFF).
    if primary and primary['method'] == 'comparison_bracket' and n >= 20:
        output['accuracy'] = {
            'score': 85,
            'label': 'شواهد كافية',
            'tier': 'high',
            # Sprint 2.22.0a.2 §9 precision pass: reframed old wording
            # to honest comparable scope (district + bracket match, not
            # property-level similarity).
            'explanation_ar': f'مبني على {n} صفقة بيع فعلية مسجلة في وزارة العدل لعقارات قريبة في النوع والمساحة ضمن نفس المنطقة.',
        }
    elif primary and primary['method'] in ('comparison_bracket', 'comparison_widened') and n >= 20:
        output['accuracy'] = {
            'score': 78,
            'label': 'شواهد كافية',
            'tier': 'high',
            # Sprint 2.22.0a.2 §9 precision pass.
            'explanation_ar': f'مبني على {n} صفقة بيع فعلية مسجلة (مع توسيع النطاق الجغرافي للعثور على عدد كافٍ من الصفقات القريبة في النوع والمساحة).',
        }
    elif primary and n >= 10:
        output['accuracy'] = {
            'score': 60,
            'label': 'شواهد محدودة',
            'tier': 'medium',
            'explanation_ar': f'مبني على {n} صفقة فقط — أقل من المعدل الإحصائي المثالي (20). النتيجة قد تنحرف ±10-15% عن السعر الفعلي. يُفضّل التحقق ميدانياً.',
        }
    elif primary:
        output['accuracy'] = {
            'score': 35,
            'label': 'تقدير تقريبي',
            'tier': 'low',
            'explanation_ar': f'مبني على {n} صفقة فقط — عينة صغيرة جداً. النتيجة تقريبية، لا تعتمد عليها لقرار شراء/بيع بدون فحص ميداني أو مُقيِّم معتمد.',
        }
    else:
        output['accuracy'] = {
            'score': 0,
            'label': 'بيانات غير كافية',
            'tier': 'none',
            # Sprint 2.22.0a.2 §9 precision pass.
            'explanation_ar': 'لا توجد صفقات بيع كافية لعقارات قريبة في النوع والمساحة ضمن نفس المنطقة في وزارة العدل. لم يتم إنتاج تقييم.',
        }

    # ── Trend (only if sample sizes support it — RICS data quality standard) ──
    if getattr(ev, 'trend', None):
        slope_pct = (ev.trend.get('slope_annual_pct') or 0) * 100
        years = ev.trend.get('years', [])
        # Sprint 1.c fix: hide trend if any year has n<5 or total n<10
        # Statistical floor — fewer than this can't support a trend line
        annual_ns = [y.get('n', 0) for y in years]
        total_n = sum(annual_ns)
        min_year_n = min(annual_ns) if annual_ns else 0
        trend_supportable = (
            len(years) >= 2
            and min_year_n >= 5      # each year has enough samples
            and total_n >= 10        # total observations meaningful
        )
        if trend_supportable:
            # Sprint 2.22.0a.3 T1.2 (rework): staleness-coupled gate.
            #
            # Suppress the numeric slope_pct (and the exceptional-slope
            # warning that quotes it) when EITHER:
            #
            #   (a) MoJ source data is stale or very_stale (>= 91 days
            #       old). A precise "%/سنة" rate cannot be defended on
            #       data that pre-dates the trend window's end. This
            #       was the case the original 2.22.0a.3 gate missed:
            #       at 148-day MoJ staleness, the brief's headline
            #       case (`56/565/21` showing `استقرار 1.9%/سنة`) IS
            #       the contradiction we have to fix.
            #
            #   (b) Material Valuation Uncertainty is engaged at
            #       'critical' or 'high' level (sample shortfall or
            #       methodology breakdown). Showing a precise rate
            #       alongside a critical/high MUC banner is internally
            #       contradictory.
            #
            # Self-healing: when MoJ publishes a fresh bulletin the
            # next process restart picks up tier='fresh', the gate
            # auto-clears, and the slope returns — no code change.
            #
            # 'moderate' MUC is NOT gated. It fires on every desktop
            # valuation regardless of MoJ freshness (no field
            # inspection always = score 2, see material_uncertainty.py
            # `assess_uncertainty`). Coupling on 'moderate' would
            # over-suppress the (currently rare) fresh-data + low-MUC
            # case where the rate IS defensible.
            #
            # Suppressed output: qualitative label + years[] backing
            # detail + an Arabic historical-window string ("نافذة
            # 2020-2025") so the user sees the time span backing the
            # direction call. No slope_pct, no '%/سنة' framing.
            #
            # Float-noise rounding: slope_pct → 1 decimal (was
            # 1.8900000000000001 — float-serialization noise).
            _muc_level = (output.get('material_uncertainty') or {}).get('level')
            _fresh_tier = _get_moj_freshness_tier()
            _suppress_slope = (
                _fresh_tier in ('stale', 'very_stale')
                or _muc_level in ('high', 'critical')
            )

            # Historical window for the suppressed-headline framing.
            # Sprint 2.22.0a.3 LRM fix (Operational_Rules #25): the
            # digit-EN_DASH-digit run "YYYY–YYYY" embedded inside Arabic
            # text is the same bidi-reversal class as "31/918/99 →
            # 99/918/31" — wrap the LTR range with U+200E on both
            # sides. Matches the muc_clause_ar convention
            # (e.g. "‎VPGA 10‎", "‎effective 31 January 2025‎").
            # The "نافذة غير محددة" fallback has no Latin/digit run
            # → no LRM needed.
            _year_nums = sorted({y.get('year') for y in years
                                 if y.get('year') is not None})
            _window_ar = (
                f'نافذة ‎{_year_nums[0]}–{_year_nums[-1]}‎'
                if _year_nums else 'نافذة غير محددة'
            )

            output['trend'] = {
                'label': ev.trend.get('label'),
                'years': years,
                'historical_window_ar': _window_ar,
            }
            if not _suppress_slope:
                output['trend']['slope_pct'] = round(slope_pct, 1)
                if abs(slope_pct) > 8:
                    output['trend']['warning'] = (
                        f'اتجاه استثنائي ({slope_pct:+.1f}%/سنة) — '
                        f'لا يُستخدم للاستقراء. النمو المستدام في قطر 2-4%/سنة.'
                    )
            else:
                # Transparency: name the active suppression cause so
                # consumers can render "اتجاه تاريخي" framing instead
                # of a current-rate one.
                if _fresh_tier in ('stale', 'very_stale'):
                    # Sprint 2.22.0a.3 LRM fix: the "91" digit run
                    # inside Arabic text is wrappable per the
                    # Operational_Rules #25 detector. The "≥" is a
                    # neutral math symbol; wrap only the digit run
                    # (parallels material_uncertainty.py "‎VPGA 10‎"
                    # which wraps only the Latin run, not the
                    # surrounding spaces or punctuation).
                    output['trend']['suppressed_reason_ar'] = (
                        'بيانات وزارة العدل قديمة (≥ ‎91‎ يوماً) — '
                        'لا تدعم رقماً سنوياً دقيقاً اليوم.'
                    )
                else:
                    # No Latin/digit run in this branch — pure Arabic
                    # (uses 'عالٍ/حرج' for high/critical, not Latin
                    # level names) → no LRM wrap needed. The em-dash
                    # separates Arabic clauses on both sides.
                    output['trend']['suppressed_reason_ar'] = (
                        'تحفظ مادي عند مستوى عالٍ/حرج — '
                        'العينة أو المنهجية قاصرة عن دعم رقم محدد.'
                    )
        else:
            # Show "volatile / undeterminable" indicator instead of a misleading line
            output['trend'] = {
                'label': 'غير محدد',
                'reason_ar': (
                    f'العينة السنوية صغيرة جداً لاستخراج اتجاه موثوق '
                    f'(أصغر عينة سنوية: {min_year_n}، الإجمالي: {total_n}). '
                    f'السوق في هذه المنطقة قد يكون متذبذباً.'
                ),
                'years_observed': len(years),
                'min_year_n': min_year_n,
                'total_n': total_n,
                'undeterminable': True,
            }

    # ── Location features ──
    LABEL_FIXES = {
        'تزوير R1': 'منطقة سكنية خاصة (R1)',
        'تزوير R2': 'منطقة سكنية (R2)',
        'تزوير R3': 'منطقة سكنية مكثفة (R3)',
        'تزوير C':  'منطقة تجارية (C)',
        'تنظيم R1': 'منطقة سكنية خاصة (R1)',
        'تنظيم R2': 'منطقة سكنية (R2)',
        'تنظيم R3': 'منطقة سكنية مكثفة (R3)',
        'تنظيم C':  'منطقة تجارية (C)',
    }
    HEIGHT_FIXES = {
        'G+1+P': 'أرضي + أول + سطح',
        'G+2+P': 'أرضي + طابقين + سطح',
        'G+P':   'أرضي + سطح',
        'G+1':   'أرضي + أول',
        'G+2':   'أرضي + طابقين',
    }
    output['location_features'] = []
    if ev.valuation and ev.valuation.factors_detail:
        for f in ev.valuation.factors_detail:
            label = f.get('label_ar', '')
            for old, new in LABEL_FIXES.items():
                label = label.replace(old, new)
            for old, new in HEIGHT_FIXES.items():
                if old in label:
                    label = label.replace(old, new)
            code = f.get('code', '')
            direction = f.get('direction', 'neutral')
            # Sprint 2.9: 3-state direction.
            # Previously `is_positive = direction == 'positive'` collapsed
            # 'neutral' to False, which the UI rendered with the red-error
            # palette (loc-neg). For ~13% of Qatar (R2 zones), this made
            # standard residential zoning look like a defect. The frontend
            # already handles `null` correctly (falls through to `loc-neu`).
            if direction == 'positive':
                is_positive = True
            elif direction == 'negative':
                is_positive = False
            else:  # 'neutral' / missing / unknown
                is_positive = None
            if code == 'plot_shape':
                if 'منتظم' in label and 'غير' not in label:
                    is_positive = True
                elif 'غير منتظم' in label:
                    is_positive = False
            output['location_features'].append({'label': label, 'positive': is_positive})

    # ── NEW Sprint 2: Geometric findings (corner, HBU, named landmarks) ──
    # Disclosure-only by default — these may already be captured in comparables.
    # HBU is the exception: it's typically NOT in comparables (R1 surrounded by R1).
    if geometric:
        geo_section = {
            'polygon_available': geometric.get('polygon_available', False),
            'plot_area_m2_verified': geometric.get('plot_area_m2'),
            'pd_no': geometric.get('pd_no'),
        }

        # Corner & main road frontage (disclosure)
        corner = geometric.get('corner', {})
        if corner.get('confidence') != 'low':
            geo_section['corner_analysis'] = {
                'is_corner': corner.get('is_corner', False),
                'main_road_adjacent': corner.get('main_road_adjacent', False),
                'main_streets': corner.get('main_streets', []),
                'local_streets': corner.get('local_streets', []),
                'evidence_ar': corner.get('evidence_ar'),
                'confidence': corner.get('confidence'),
                'note_ar': (
                    'هذه الخصائص قد تَفرض علاوة سوقية. النقطة المركزية '
                    'محافظة (وسيط المقارنات) — الحد الأعلى للنطاق يَعكس الاحتمال.'
                ),
            }

        # HBU
        hbu = geometric.get('hbu', {})
        if hbu.get('hbu_potential') or hbu.get('industrial_adjacency'):
            geo_section['hbu_analysis'] = {
                'potential': hbu.get('hbu_potential', False),
                'industrial_adjacency': hbu.get('industrial_adjacency', False),
                'potential_pct': hbu.get('potential_pct', 0),
                'evidence_ar': hbu.get('evidence_ar'),
                'adjacent_zones': hbu.get('adjacent_zones', []),
                'rics_reference': 'RICS VPS 2 / IVS 102 — Highest and Best Use',
            }

        # Named landmarks (from GIS dynamic query — no hardcoded whitelist)
        nl = geometric.get('named_landmarks', {})
        if nl.get('malls') or nl.get('metros') or nl.get('mixed_use_venues'):
            geo_section['named_landmarks'] = {
                'malls': nl.get('malls', []),
                'mixed_use_venues': nl.get('mixed_use_venues', []),
                'metros': nl.get('metros', []),
                'closest_mall_m': nl.get('closest_mall_m'),
                'closest_mixed_use_m': nl.get('closest_mixed_use_m'),
                'closest_metro_m': nl.get('closest_metro_m'),
                'walkable_mall': any(m.get('walkable') for m in nl.get('malls', [])),
                'walkable_mixed_use': any(m.get('walkable') for m in nl.get('mixed_use_venues', [])),
                'walkable_metro': any(m.get('walkable') for m in nl.get('metros', [])),
            }

        if geo_section.get('polygon_available'):
            output['geometric_factors'] = geo_section

        # ── Range expansion based on geometric features (RICS Range Reporting) ──
        upper_expansion_pct = 0.0
        upper_expansion_reasons = []

        if corner.get('is_corner'):
            upper_expansion_pct += 0.10
            upper_expansion_reasons.append('زاوية (+10%)')
        if corner.get('main_road_adjacent'):
            upper_expansion_pct += 0.08
            upper_expansion_reasons.append('شارع رئيسي (+8%)')
        # Check walkable mall (within 500m) — separate from mixed-use
        walking_mall = next((m for m in nl.get('malls', []) if m.get('walkable')), None)
        if walking_mall:
            upper_expansion_pct += 0.10
            upper_expansion_reasons.append(f'{walking_mall["name_ar"]} يُمشى (+10%)')
        # Walkable mixed-use venue (e.g. Dar Al Salam with shopping access) — smaller premium
        walking_mixed = next((m for m in nl.get('mixed_use_venues', []) if m.get('walkable')), None)
        if walking_mixed and not walking_mall:  # avoid double-counting if both present
            upper_expansion_pct += 0.07
            upper_expansion_reasons.append(f'{walking_mixed["name_ar"]} يُمشى (+7%)')
        # Walkable metro
        walking_metro = next((m for m in nl.get('metros', []) if m.get('walkable')), None)
        if walking_metro:
            upper_expansion_pct += 0.08
            upper_expansion_reasons.append('مترو يُمشى (+8%)')

        upper_expansion_pct = min(upper_expansion_pct, 0.35)

        hbu_central_uplift_pct = 0.0
        if hbu.get('hbu_potential'):
            hbu_central_uplift_pct = hbu.get('potential_pct', 0) * 0.5
        elif hbu.get('industrial_adjacency'):
            hbu_central_uplift_pct = hbu.get('potential_pct', 0)

        if output.get('valuation') and output['valuation'].get('amount'):
            base_amount = output['valuation']['amount']
            base_low = output['valuation'].get('low') or base_amount * 0.85
            base_high = output['valuation'].get('high') or base_amount * 1.15

            new_amount = base_amount * (1 + hbu_central_uplift_pct)
            new_high = max(base_high, base_amount * (1 + upper_expansion_pct)) * (1 + hbu_central_uplift_pct)
            new_low = base_low * (1 + min(0, hbu_central_uplift_pct))

            output['valuation']['amount'] = _r100k(new_amount)
            output['valuation']['low'] = _r100k(new_low)
            output['valuation']['high'] = _r100k(new_high)

            output['valuation']['range_expansion'] = {
                'upper_bound_expanded_pct': round(upper_expansion_pct * 100, 1),
                'central_value_hbu_adjustment_pct': round(hbu_central_uplift_pct * 100, 1),
                'reasons_for_upper_expansion': upper_expansion_reasons,
                'methodology_note_ar': (
                    'النقطة المركزية تَستخدم وسيط المقارنات (محافظ). الحد الأعلى '
                    'يَتسع لِيَعكس الخصائص الفريدة المُكتشَفة. '
                    'HBU (إن وُجد) يُؤثر على النقطة المركزية لأنه قيمة-إضافية '
                    'غير مُتضمَّنة في عقارات المقارنة.'
                ),
            }

    # ── Material Uncertainty (RICS VPGA 10) ──
    # Sprint 1.c fix: ensure MU reflects the n actually USED in primary value
    # (not the thin bracket n that geo widening already bypassed)
    if v3_result and v3_result.get('material_uncertainty'):
        mu = dict(v3_result['material_uncertainty'])  # shallow copy
        # Sprint 2.22.0a.20 (A7): main-path honest "review pending" label next to
        # rics_compliant (display/label only — the bool and all values are untouched;
        # it survives the downstream factor/level mutations, which never touch
        # rics_compliant). Wrapped so a status-label failure can never break evaluate.
        try:
            from material_uncertainty import rics_compliant_status_fields
            for _k, _v in rics_compliant_status_fields(mu.get('rics_compliant', False)).items():
                mu.setdefault(_k, _v)
        except Exception:
            pass
        effective_n = primary['n'] if primary else 0
        # Replace any "n=1" or "n=X (thin bracket)" misleading factors with the truth
        if mu.get('factors'):
            new_factors = []
            for f in mu['factors']:
                # The factor that says "n=1 — لا يمكن إنتاج وسيط موثوق" is misleading
                # when we actually used n=42 from widening
                if 'صغيرة جداً' in f and 'لا يمكن إنتاج' in f and effective_n >= 20:
                    new_factors.append(
                        f'الشريحة المباشرة ضعيفة (n=1) — تم التعويض بالتوسيع الجغرافي '
                        f'(n={effective_n} معاملة بعد التوسيع، ‎RICS VPS 3 / IVS 103‎)'
                    )
                else:
                    new_factors.append(f)
            mu['factors'] = new_factors

        # Recompute level based on effective n
        if effective_n >= 20 and primary and primary['method'] in ('comparison_bracket', 'comparison_widened'):
            # Strong primary evidence reduces MU from "high" to "moderate"
            if mu.get('level') == 'high':
                mu['level'] = 'moderate'
                mu['banner_ar'] = (
                    'تحفّظ مادي متوسط — عينة المقارنات معقولة (n=' + str(effective_n)
                    + ') لكن لا يوجد فحص ميداني أو بيانات بناء كاملة. '
                    + 'يبقى الفحص الميداني موصى به للقرارات الكبرى.'
                )
                mu['banner_en'] = (
                    'MODERATE Material Uncertainty — Reasonable comparable sample '
                    '(n=' + str(effective_n) + ') but no field inspection or full building data. '
                    'Field inspection recommended for major decisions.'
                )

        output['material_uncertainty'] = mu

    # Sprint 2.19: surface cap-rate provenance at the canonical response root
    # (mirrors the material_uncertainty pattern — root is authoritative over
    # the brief sections, per the Sprint 2.16.9 lesson).
    if income and income.get('cap_rate_provenance'):
        output['cap_rate_provenance'] = income['cap_rate_provenance']

    # ── Audience-specific brief ──
    v3_rent = v3_result.get('rent_reference') if v3_result else None
    if v3_result and v3_result.get('brief'):
        brief = dict(v3_result['brief'])
        # Sprint A fix: the v3 yield/income/sensitivity sections use stale cap_rate (6.5%)
        # contradicting the corrected primary income_approach (4% for residential).
        # Strategy: filter the stale sections, then rebuild them from `income` (correct).
        STALE_SECTION_IDS = {'yield', 'income_value', 'sensitivity', 'rent_reference'}
        if brief.get('sections'):
            brief['sections'] = [
                s for s in brief['sections']
                if s.get('id') not in STALE_SECTION_IDS
            ]
            # Rebuild investor sections from the corrected `income` cross-check
            if audience == 'investor':
                if income:
                    # Normal path: full income-based analysis
                    rebuilt = _build_investor_sections(income, v3_rent, primary)
                else:
                    # Sprint 2.4b: income data absent (no user rent, no rent_ref).
                    # Still build a meaningful investor brief from cap-rate
                    # fallback + sensitivity scenarios.
                    rebuilt = _build_investor_sections_fallback(
                        asset_type=getattr(ev, 'asset_type', None) or 'standalone_villa',
                        primary=primary,
                        plot_area_m2=getattr(ev, 'plot_area_m2', None),
                        v3_rent=v3_rent,
                    )
                # Insert rebuilt sections BEFORE any existing ones (e.g. market_context)
                brief['sections'] = rebuilt + brief['sections']
            # If still no sections (e.g. non-investor), add a placeholder pointer
            if not brief['sections']:
                brief['sections'] = [{
                    'id': 'income_pointer',
                    'title_ar': 'تحليل الدخل والعائد',
                    'content': {
                        'note_ar': (
                            'انظر قسم "منهج الدخل" أعلاه — يحوي القيمة الصحيحة، '
                            'مصدر الإيجار، معدّل الرسملة المناسب لنوع الأصل، وصافي العائد.'
                        ),
                    },
                }]
        # Sprint 2.19: append a cap-rate provenance section (human-readable echo;
        # output['cap_rate_provenance'] at root stays authoritative).
        if income and income.get('cap_rate_provenance') and brief.get('sections') is not None:
            try:
                from output_briefs import build_cap_rate_provenance_section
                _prov_sec = build_cap_rate_provenance_section(income['cap_rate_provenance'])
                if _prov_sec:
                    brief['sections'].append(_prov_sec)
            except Exception as _e:
                print(f"[cap_rate_provenance] brief section skipped: {_e}", file=sys.stderr)

        # Also fix the brief's top-level valuation_total to match the primary value (was using v3 blend)
        if primary and primary.get('value'):
            # Sprint 2.4a: use the ACTUAL valuation.amount (which may include
            # substantiality + age adjustments) — not raw primary — for the brief
            # so brief headlines never contradict the headline number.
            final_amount = output.get('valuation', {}).get('amount') or primary['value']
            final_low = output.get('valuation', {}).get('low') or primary.get('low') or final_amount * 0.85
            final_high = output.get('valuation', {}).get('high') or primary.get('high') or final_amount * 1.15

            brief['valuation_total'] = _r100k(final_amount)
            brief['valuation_low']   = _r100k(final_low)
            brief['valuation_high']  = _r100k(final_high)

            # Sprint 2.4a: also rebuild audience-specific anchor sections
            # (negotiation, pricing, valuation) so they don't show the OLD
            # blended-cost-inflated numbers from output_briefs.
            try:
                _rewrite_brief_anchored_sections(
                    brief, final_amount, final_low, final_high,
                    audience=audience,
                    moj_direct=getattr(ev.valuation, 'fair_price_total', None) if getattr(ev, 'valuation', None) else None,
                    stock_strata=output.get('stock_strata'),  # Sprint 2.16.2
                )
            except Exception as e:
                import sys
                print(f'[brief rewrite warning] {e}', file=sys.stderr)
        output['brief'] = brief

    # ── Disclaimer ──
    output['disclaimer'] = getattr(ev, 'disclaimer', None)
    output['valuation_id'] = getattr(ev, 'valuation_id', None)

    if getattr(ev, 'reasoning_trace', None):
        output['reasoning_trace'] = ev.reasoning_trace

    # ── Listings as separate sentiment context (RICS GN 13) ──
    if listings_result:
        output['active_listings'] = {
            'note': 'إعلانات نشطة — سياق سوقي، ليست في معادلة التقييم (RICS GN 13)',
            'n': listings_result.get('n'),
            'weighted_median_m2': listings_result.get('weighted_median_m2'),
            'oldest_days': listings_result.get('oldest_days'),
            'sample': listings_result.get('sample', []),
        }
    elif _LISTINGS_OK:
        output['active_listings'] = {'available': False,
                                      'reason': 'لا توجد إعلانات نشطة مطابقة'}

    # Sprint 2.14.0 — attach RICS VPS 1 (scope of work / terms of engagement) scope assessment
    _attach_scope(output)

    # Sprint 2.21.0.9 — surface multi-QARS detection at the canonical root
    # (mirrors material_uncertainty / cap_rate_provenance pattern). When the
    # cadastral PIN carries multiple QARS-addressed villas (attached duplex /
    # separate shared plot / ambiguous), the UI renders a yellow card with the
    # effective-area split, the cadastral area for context, and (for
    # type='attached') the "value whole structure" toggle. Single source of
    # truth — the brief sections must defer to this root field (Sprint 2.16.9
    # lesson). `ev.multi_qars` is None for compound_large / tower / raw_land /
    # agricultural / non-detected → field is absent from the response by
    # default, no UI panel rendered.
    _multi_qars = getattr(ev, 'multi_qars', None) if ev else None
    if _multi_qars:
        output['multi_qars'] = _multi_qars

    # ── Sprint 2.22.0a.10: Stage-1 honest range under built-type/condition uncertainty ──
    # When the widened (geo_value) villa pool is highly dispersed (built-type/condition blind,
    # RISK_REGISTER R7), the point median is false precision. Gate → keep the P25–P75 range
    # (already in valuation.low/high) as the honest headline, drop the tier to indicative, widen
    # the MVU, and disclose (AR+EN, via the already-rendered accuracy + MVU surfaces). The median
    # is retained as the central indicative estimate (backward compat: clients reading
    # valuation.amount keep working). Presentation only; wrapped in try/except. Runs LAST so it is
    # the final word on accuracy/MVU when gated.
    try:
        _g = _stage1_dispersion_gate(primary, geo_v2_result)
        _val = output.get('valuation') or {}
        if _g and _g['gated'] and _val.get('amount') is not None:
            # (1) range stays headline; the point becomes the central indicative estimate
            _val['range_is_headline'] = True
            _val['central_estimate'] = _val.get('amount')
            _val['pool_dispersion'] = _g['dispersion']
            _val['range_disclosure_ar'] = (
                'النطاق المعروض هو التقدير الأصدق لهذا العقار في هذه المرحلة. الصفقات المقارنة '
                'المتاحة تشمل أنواع بناء وحالات متفاوتة (فيلا عادية، ملحق، بنتهاوس)، ولم يُؤكَّد بعد '
                'نوع بناء هذا العقار وحالته — لذلك القيمة المركزية إرشادية ضمن النطاق. تأكيد نوع '
                'البناء والحالة بالمعاينة الميدانية أو عبر الوسيط (المرحلة الثانية) يضيّق النطاق.'
            )
            _val['range_disclosure_en'] = (
                'The shown range is the most honest estimate at this stage. The available '
                'comparable sales span different built types and conditions (plain villa, annex, '
                'penthouse), and this property’s built type and condition are not yet '
                'confirmed, so the central value is indicative within the range. Confirming built '
                'type and condition by field inspection or a broker (Stage 2) narrows it.'
            )
            output['valuation'] = _val
            # (2) tier → indicative (lowest qualitative tier in the شواهد taxonomy)
            output['accuracy'] = {
                'score': 50,
                'label': 'شواهد محدودة',
                'tier': 'medium',
                'explanation_ar': (
                    'تقدير إرشادي بنطاق واسع: المقارنات المتاحة تختلف في نوع البناء والحالة، '
                    'ونوع بناء هذا العقار وحالته غير مؤكدين بعد. اعتمد النطاق المعروض لا الرقم '
                    'المفرد؛ المعاينة الميدانية تضيّق النطاق.'
                ),
            }
            # (3) MVU → widen / do not downgrade; state that the spread is real
            _mu = dict(output.get('material_uncertainty') or {})
            _mu['level'] = 'high'
            _mu['banner_ar'] = (
                'تحفّظ مادي مرتفع — النطاق واسع لأن الصفقات المقارنة المتاحة تختلف في نوع '
                'البناء والحالة، ولم يُؤكَّد نوع بناء العقار وحالته. النتيجة إرشادية حتى التحقق الميداني.'
            )
            _mu['banner_en'] = (
                'HIGH material uncertainty — the range is wide because the available '
                'comparable sales differ in built type and condition, and the subject’s built '
                'type and condition are unconfirmed. Indicative pending field verification.'
            )
            _facts = list(_mu.get('factors') or [])
            _facts.append(
                'تشتت المقارنات مرتفع (نوع البناء والحالة غير مؤكدين) — اعتمد النطاق المعروض لا الرقم المفرد'
            )
            _mu['factors'] = _facts
            _mu['stage1_dispersion_gated'] = True
            output['material_uncertainty'] = _mu
        # Sprint 2.22.0a.17 (a19 path-complete): villa/house value-bearing surfaces →
        # bidirectional condition caveat (R7). Dispersion-GATED pools (bracket→a14, widened→a10)
        # already disclose condition in the honest-range above and are excluded by the gate; the
        # note covers clean bracket + thin + non-dispersed widened + preliminary. a18 put Marikh
        # 54/541/6 on the thin path (~5.4M) — the subject most needing it. Amount byte-identical.
        if _condition_note_applies(primary, _g, getattr(ev, 'asset_type', None), _val.get('amount')):
            _val['condition_note_ar'] = CONDITION_NOTE_AR
            _val['condition_note_en'] = CONDITION_NOTE_EN
            output['valuation'] = _val
    except Exception as _e:
        print(f'[stage1_honest_range] skipped: {_e}', file=sys.stderr)

    return output


# ============================================================
# CLI
# ============================================================

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('zone', type=int)
    p.add_argument('street', type=int)
    p.add_argument('building', type=int)
    p.add_argument('--moj', default='moj_weekly.csv')
    p.add_argument('--rent', default='rent_reference.json')
    p.add_argument('--asking', type=float)
    p.add_argument('--rental', type=float)
    p.add_argument('--floors', type=int)
    p.add_argument('--condition', choices=['new', 'good', 'renovated', 'maintenance',
                                           'excellent', 'fair', 'poor', 'teardown'])
    p.add_argument('--annexes', type=int, default=0)
    p.add_argument('--audience', choices=['buyer', 'seller', 'investor', 'valuer'],
                   default='buyer')
    p.add_argument('--no-listings', action='store_true')
    p.add_argument('--no-geo-v2', action='store_true')
    args = p.parse_args()

    result = evaluate_thammen(
        zone=args.zone, street=args.street, building=args.building,
        moj_csv_path=args.moj,
        rent_ref_path=args.rent,
        listing_price=args.asking,
        rental_income=args.rental,
        floors=args.floors,
        condition=args.condition,
        annexes=args.annexes,
        audience=args.audience,
        use_listings=not args.no_listings,
        use_geo_v2=not args.no_geo_v2,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    main()
