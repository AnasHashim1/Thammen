"""
cap_rate_calibrator.py
======================

Sprint 2.19 — Cap Rate Calibration v1.

Turns PropertyFinder *rental* listings into empirically grounded cap-rate
parameters for the DCF engine, written to ``cap_rates.sqlite``.

Methodology guardrails (docs/Empirical_Findings.md §2):
  - Rule E1: listings NEVER adjust MoJ sale medians. We read MoJ sale medians
    read-only as the yield *denominator*; we never write them.
  - Rule E3 (refined): rental listings calibrate a *parameter* (cap rate),
    not a price. Output flows into DCF only.
  - Rule E4: villa cells are tagged with their stock class
    (land_priced / aging_stock / modern_stock / luxury_new) — stocks are not
    pooled. Stock class is derived per (area × bracket) from the MoJ
    villa/land median ratio (we have no per-listing sale price to classify
    each rental individually).
  - GIS is the sole authority for district name (Project_Instructions §7).
    Every listing's GPS is resolved against Vector/Districts; PropertyFinder's
    ``location.full_name`` is never trusted.

v1 SCOPE (confirmed with Anas 2026-05-20):
  - Calibrated empirically: villa (stratified), compound_small (via
    "مجمع فلل" MoJ data when present).
  - Deferred (stay hardcoded fallback, with provenance noting why):
      * apartment_building + tower → Sprint 2.29 (MME integration) — MoJ has
        no per-unit apartment sale prices, so no yield denominator exists.
      * land → Sprint 2.19.1 — needs a price-trend path, not rent÷sale.
      * compound_large → no MoJ comparable (yield-only asset) → fallback.

NET YIELD FORMULA — corrected from brief §5:
  The brief's literal ``net = gross - vacancy - mgmt - maintenance`` subtracts
  an ABSOLUTE 0.20 from the yield ratio, which drives realistic gross yields
  (~6-9%) negative. The dimensionally correct form (Operational_Rules #1, #8)
  treats vacancy/mgmt/maintenance as fractions of INCOME:

      net_yield = gross_yield * (1 - opex_ratio) - service_charge_per_sqm_year
                                                   / sale_median_per_sqm

  opex_ratio: villa 0.20 (vac .05 + mgmt .05 + maint .10);
              compound 0.23 (Operational_Rules #8).

Pure stdlib (urllib + json + re + sqlite3). No new requirements.
"""

import json
import os
import re
import sqlite3
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone

import moj_reference as mr
import propertyfinder_client as pf

# --------------------------------------------------------------------------
# Config / constants
# --------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "cap_rates.sqlite")
MOJ_CSV = os.path.join(HERE, "moj_weekly.csv")

GIS_DISTRICTS_URL = (
    "https://services.gisqatar.org.qa/server/rest/services/"
    "Vector/Districts/MapServer/0/query"
)

# Reliability gate (brief §4 confidence column).
N_RELIABLE = 20
N_INDICATIVE = 10
# A cap rate is a RATIO: rent/sqm ÷ MoJ-sale/sqm. It is only as trustworthy as
# its WEAKER input. The MoJ sale-median denominator below this many transactions
# is statistically insufficient (project sample-size discipline: <5 = "no median").
MIN_DENOMINATOR_N = 5

# Brief size-bracket labels (note '1500+' vs MoJ key '1500-99999').
SIZE_BRACKETS = [(0, 400), (400, 600), (600, 900), (900, 1500), (1500, 10 ** 9)]

# Income-side OPEX ratios (fractions of gross income).
OPEX_RATIO = {
    "villa": 0.20,
    "compound_small": 0.23,
    "compound_large": 0.23,
}
VACANCY, MGMT, MAINTENANCE = 0.05, 0.05, 0.10  # components of the villa 0.20

# Service charge QAR / sqm / year (brief §6). Villas have none.
SERVICE_CHARGE_QAR_SQM_YEAR = {
    "pearl": 174, "lusail": 144, "west_bay": 120, "msheireb": 168,
    "apartment_building_default": 96,
    "villa": 0, "land": 0,
    "compound_large": 60, "compound_small": 30,
}

# Asset types this Sprint actually calibrates from rentals (others -> fallback).
CALIBRATABLE = {"villa", "compound_small"}

# --------------------------------------------------------------------------
# Small pure helpers (unit-tested)
# --------------------------------------------------------------------------

def median(values):
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return None
    n = len(vals)
    mid = n // 2
    if n % 2:
        return vals[mid]
    return (vals[mid - 1] + vals[mid]) / 2.0


def confidence_for_n(n):
    if n >= N_RELIABLE:
        return "reliable"
    if n >= N_INDICATIVE:
        return "indicative"
    return "fallback"


def size_bracket_for(area_sqm):
    if area_sqm is None or area_sqm <= 0:
        return None
    for lo, hi in SIZE_BRACKETS:
        if lo <= area_sqm < hi:
            return f"{lo}-{hi}" if hi < 10 ** 9 else "1500+"
    return None


def _moj_bracket_key(bracket_label):
    """Map our '1500+' to MoJ's '1500-99999'; others pass through."""
    return "1500-99999" if bracket_label == "1500+" else bracket_label


def classify_villa_stock(villa_per_m2, land_per_m2):
    """Rule E4 stock classification from villa/land sale-median ratio."""
    if not villa_per_m2 or not land_per_m2:
        return None
    ratio = villa_per_m2 / land_per_m2
    if ratio < 1.15:
        return "land_priced"
    if ratio < 1.50:
        return "aging_stock"
    if ratio < 2.20:
        return "modern_stock"
    return "luxury_new"


def compute_net_yield(rent_per_sqm_monthly, sale_median_per_sqm,
                      service_charge_per_sqm_year, opex_ratio):
    """Return (gross_yield, net_yield) or (None, None) if denominator absent.

    Corrected formula (see module docstring). Both yields are fractions.
    """
    if not sale_median_per_sqm or sale_median_per_sqm <= 0:
        return None, None
    annual_rent_per_sqm = rent_per_sqm_monthly * 12.0
    gross_yield = annual_rent_per_sqm / sale_median_per_sqm
    net_yield = (gross_yield * (1.0 - opex_ratio)
                 - (service_charge_per_sqm_year or 0) / sale_median_per_sqm)
    return gross_yield, net_yield


def is_stale(last_updated_iso, now=None, days=30):
    """True if last_updated is older than `days` (used by engine + tests)."""
    if not last_updated_iso:
        return True
    now = now or datetime.now(timezone.utc)
    try:
        ts = datetime.fromisoformat(last_updated_iso.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return True
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return (now - ts).days > days


# Arabic district-name normalization for GIS<->MoJ matching ----------------

def _strip_ar(s):
    s = re.sub(r"\s+", " ", (s or "")).strip()
    s = s.replace("‎", "").replace("‏", "")
    s = re.sub(r"[ً-ْ]", "", s)          # tashkeel
    s = s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    s = s.replace("ى", "ي").replace("ة", "ه")
    return s


def area_token(name):
    """Reduce a district/area name to a comparable core token.

    Strips leading 'ال', trailing administrative suffixes (الريان/الدوحة) and
    trailing zone numbers, so GIS 'الغرافة' matches MoJ 'غرافة الريان'.
    """
    s = _strip_ar(name)
    s = re.sub(r"\s*\d+\s*$", "", s)               # trailing zone number
    for suffix in ("الريان", "الدوحه", "الدوحة", "الوكره", "الوكرة"):
        if s.endswith(" " + _strip_ar(suffix)):
            s = s[: -(len(_strip_ar(suffix)) + 1)].strip()
    if s.startswith("ال"):
        s = s[2:]
    return s.strip()


def _zone_num(name):
    """Extract a trailing zone number from a district name, else None.

    Used to prevent cross-zone contamination: 'المعمورة 56' rentals must not be
    priced against 'المعمورة 43' sales — different zones, different price levels.
    """
    m = re.search(r"(\d+)\s*$", _strip_ar(name or ""))
    return int(m.group(1)) if m else None


# --------------------------------------------------------------------------
# GIS district resolution
# --------------------------------------------------------------------------

def fetch_gis_district(lat, lon, cache=None, timeout=15, retries=2):
    """Resolve (lat, lon) -> (dist_no, aname) via Vector/Districts spatial query.

    Returns (None, None) on failure. `cache` keyed by rounded coords to keep
    the calibration polite (many listings share a district).
    """
    key = (round(lat, 4), round(lon, 4))
    if cache is not None and key in cache:
        return cache[key]
    geom = {"x": lon, "y": lat, "spatialReference": {"wkid": 4326}}
    params = {
        "geometry": json.dumps(geom),
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "ANAME,ENAME,DIST_NO",
        "returnGeometry": "false",
        "f": "json",
    }
    url = GIS_DISTRICTS_URL + "?" + urllib.parse.urlencode(params)
    result = (None, None)
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": pf.USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
            feats = data.get("features", [])
            if feats:
                attr = feats[0].get("attributes", {})
                result = (attr.get("DIST_NO"), attr.get("ANAME"))
            break
        except Exception:
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
    if cache is not None:
        cache[key] = result
    return result


# --------------------------------------------------------------------------
# MoJ sale-median index (the yield denominator) — READ ONLY
# --------------------------------------------------------------------------

class MojSaleIndex:
    """Read-only access to MoJ sale medians, keyed by area token."""

    def __init__(self, csv_path=MOJ_CSV):
        import csv as _csv
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            self.rows = list(_csv.DictReader(f))
        dates = [d for d in (mr.parse_date(r[mr.DATE_COL]) for r in self.rows) if d]
        self.max_date = max(dates)
        # token -> set of raw MoJ area names
        self._token_to_areas = defaultdict(set)
        for r in self.rows:
            raw = mr.normalize(r.get("اسم المنطقة", ""))
            if raw:
                self._token_to_areas[area_token(raw)].add(raw)
        self._ref_cache = {}

    def areas_for_token(self, token):
        return self._token_to_areas.get(token, set())

    def _reference(self, moj_area):
        if moj_area not in self._ref_cache:
            self._ref_cache[moj_area] = mr.build_reference(
                self.rows, moj_area, self.max_date
            )
        return self._ref_cache[moj_area]

    def villa_and_land_median(self, token, bracket_label, gis_aname=None):
        """Return (villa_per_m2, land_per_m2, villa_n, moj_area) for a token.

        When `gis_aname` carries an explicit zone number, MoJ areas with a
        DIFFERENT explicit zone are skipped (cross-zone contamination guard);
        zone-less MoJ areas remain eligible.
        """
        bkey = _moj_bracket_key(bracket_label)
        gis_zone = _zone_num(gis_aname) if gis_aname else None
        best = (None, None, 0, None)
        for moj_area in self.areas_for_token(token):
            if gis_zone is not None:
                mz = _zone_num(moj_area)
                if mz is not None and mz != gis_zone:
                    continue  # different zone — skip
            ref = self._reference(moj_area)
            cats = ref.get("categories", {})
            vb = cats.get("villa", {}).get("size_brackets", {}).get(bkey)
            lb = cats.get("land", {}).get("size_brackets", {}).get(bkey)
            v_med = vb.get("price_per_m2_median") if vb else None
            l_med = lb.get("price_per_m2_median") if lb else None
            v_n = vb.get("n", 0) if vb else 0
            if v_med and v_n > best[2]:
                best = (v_med, l_med, v_n, moj_area)
        return best


# --------------------------------------------------------------------------
# SQLite
# --------------------------------------------------------------------------

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS cap_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    district_aname TEXT NOT NULL,
    district_dist_no INTEGER,
    asset_type TEXT NOT NULL,
    bedrooms INTEGER,
    size_bracket TEXT NOT NULL,
    stock_class TEXT,
    median_monthly_rent_qar REAL NOT NULL,
    median_rent_per_sqm REAL NOT NULL,
    sample_size INTEGER NOT NULL,
    gross_yield REAL,
    service_charge_qar_sqm_year REAL,
    net_yield REAL,
    cap_rate REAL,
    confidence TEXT NOT NULL,
    last_updated TEXT NOT NULL,
    notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_lookup
    ON cap_rates(district_aname, asset_type, size_bracket, stock_class);
CREATE TABLE IF NOT EXISTS calibration_meta (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


def ensure_schema(conn):
    conn.executescript(SCHEMA_SQL)
    conn.commit()


def insert_row(conn, row):
    cols = ("district_aname", "district_dist_no", "asset_type", "bedrooms",
            "size_bracket", "stock_class", "median_monthly_rent_qar",
            "median_rent_per_sqm", "sample_size", "gross_yield",
            "service_charge_qar_sqm_year", "net_yield", "cap_rate",
            "confidence", "last_updated", "notes")
    conn.execute(
        f"INSERT INTO cap_rates ({','.join(cols)}) "
        f"VALUES ({','.join('?' for _ in cols)})",
        tuple(row.get(c) for c in cols),
    )


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------

def _service_charge_for(asset_type, district_token):
    if asset_type == "villa":
        return 0
    if district_token in ("لؤلؤه", "لؤلؤة", "اللؤلؤة", "لؤلؤ"):
        return SERVICE_CHARGE_QAR_SQM_YEAR["pearl"]
    return SERVICE_CHARGE_QAR_SQM_YEAR.get(asset_type, 0)


def collect_rentals(target_n_per_cat=400, max_pages=16, delay_sec=2.0, log=print):
    """Fetch villa + compound rentals, GIS-resolve, return enriched listings."""
    listings = []
    for category in ("villas",):
        log(f"[fetch] category={category} max_pages={max_pages}")
        rows = pf.fetch_rentals(category=category, target_n=target_n_per_cat,
                                max_pages=max_pages, delay_sec=delay_sec)
        log(f"[fetch] category={category} got {len(rows)} normalized rentals")
        listings.extend(rows)
    # compounds appear in the broad 'all' feed under property_type 'Compound'
    log("[fetch] category=all (compounds)")
    all_rows = pf.fetch_rentals(category="all", target_n=target_n_per_cat,
                                max_pages=max_pages, delay_sec=delay_sec)
    comp = [r for r in all_rows if r.get("asset_type") == "compound_small"]
    log(f"[fetch] compounds found in 'all': {len(comp)}")
    listings.extend(comp)
    return listings


def calibrate(db_path=DB_PATH, target_n_per_cat=400, max_pages=16,
              delay_sec=2.0, listings=None, moj_index=None, gis_cache=None,
              log=print):
    """Run the full calibration and write `db_path`. Idempotent (rebuilds table).

    `listings`/`moj_index`/`gis_cache` are injectable for testing.
    """
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    moj_index = moj_index or MojSaleIndex()
    gis_cache = {} if gis_cache is None else gis_cache

    if listings is None:
        listings = collect_rentals(target_n_per_cat, max_pages, delay_sec, log)

    # GIS-resolve + bin by (token, asset_type, bracket)
    cells = defaultdict(list)
    aname_by_token = {}
    distno_by_token = {}
    skipped_no_gis = 0
    outliers_rejected = 0
    calibratable_seen = 0
    for L in listings:
        if L.get("asset_type") not in CALIBRATABLE:
            continue
        calibratable_seen += 1
        # Sprint 2.19.1 (Fix #5): drop implausible rent/m² before it reaches a
        # median (and before we spend a GIS call on garbage).
        if not pf.is_plausible_listing(L):
            outliers_rejected += 1
            continue
        dist_no, aname = fetch_gis_district(L["lat"], L["lon"], cache=gis_cache)
        if not aname:
            skipped_no_gis += 1
            continue
        tok = area_token(aname)
        aname_by_token.setdefault(tok, aname)
        distno_by_token.setdefault(tok, dist_no)
        bracket = size_bracket_for(L["size_sqm"])
        if not bracket:
            continue
        cells[(tok, L["asset_type"], bracket)].append(L)
    rejection_rate = (outliers_rejected / calibratable_seen) if calibratable_seen else 0.0
    log(f"[bin] cells={len(cells)} skipped_no_gis={skipped_no_gis} "
        f"outliers_rejected={outliers_rejected}/{calibratable_seen} "
        f"({rejection_rate*100:.1f}%)")
    if rejection_rate > 0.10:
        # Fix #5 guard: >10% rejection signals a parsing problem, not real
        # outliers. Surface loudly so a human checks before trusting the run.
        log(f"[WARN] outlier rejection rate {rejection_rate*100:.1f}% exceeds 10% "
            f"— possible parsing problem (Sprint 2.19.1 brief §8).")

    rows_out = []
    for (tok, asset_type, bracket), cell_listings in sorted(cells.items()):
        n = len(cell_listings)
        med_rent = median([L["monthly_rent"] for L in cell_listings])
        med_rent_sqm = median([L["rent_per_sqm"] for L in cell_listings])

        gis_aname = aname_by_token.get(tok, tok)
        v_med, l_med, v_n, moj_area = moj_index.villa_and_land_median(
            tok, bracket, gis_aname=gis_aname)
        stock_class = None
        notes = []
        if asset_type == "villa":
            stock_class = classify_villa_stock(v_med, l_med)
        sale_median = v_med  # villa/compound use villa sale median per m2
        svc = _service_charge_for(asset_type, tok)

        gross, net = compute_net_yield(med_rent_sqm, sale_median, svc,
                                       OPEX_RATIO.get(asset_type, 0.20))
        if sale_median is None:
            notes.append("no_moj_sale_comparable")
            confidence = "fallback"
            cap_rate = None
        elif v_n < MIN_DENOMINATOR_N:
            # A median from <5 sales is not a usable denominator. Keep the
            # computed rate for transparency but mark it unusable.
            notes.append(f"moj_area={moj_area};moj_villa_n={v_n};denominator_insufficient")
            confidence = "fallback"
            cap_rate = net
        else:
            # Confidence is governed by the WEAKER of the rental sample and the
            # MoJ sale sample — a ratio is only as reliable as its weaker input.
            confidence = confidence_for_n(min(n, v_n))
            cap_rate = net
            notes.append(f"moj_area={moj_area};moj_villa_n={v_n};eff_n={min(n, v_n)}")
            notes.append("rent=built_sqm;sale=plot_sqm")  # basis caveat

        # Sprint 2.19.1 (Fix #4): Rule E4 requires villa stratification before a
        # cap rate may be trusted. With no MoJ land median we cannot compute the
        # stock class, so hard-guard the row to fallback regardless of sample size.
        # This prevents a growing rental sample from silently promoting an
        # unstratified villa cell to reliable/indicative (a silent Rule E4 breach).
        if asset_type == "villa" and stock_class is None and confidence != "fallback":
            confidence = "fallback"
            notes.append("stratification_unavailable:no_moj_land_median")

        rows_out.append({
            "district_aname": aname_by_token.get(tok, tok),
            "district_dist_no": distno_by_token.get(tok),
            "asset_type": asset_type,
            "bedrooms": None,
            "size_bracket": bracket,
            "stock_class": stock_class,
            "median_monthly_rent_qar": round(med_rent, 2) if med_rent else None,
            "median_rent_per_sqm": round(med_rent_sqm, 4) if med_rent_sqm else None,
            "sample_size": n,
            "gross_yield": round(gross, 5) if gross is not None else None,
            "service_charge_qar_sqm_year": svc,
            "net_yield": round(net, 5) if net is not None else None,
            "cap_rate": round(cap_rate, 5) if cap_rate is not None else None,
            "confidence": confidence,
            "last_updated": now_iso,
            "notes": "; ".join(notes) or None,
        })

    # Sprint 2.19.1 (Fix #5): persist run-level counters so /api/calibration can
    # surface outliers_rejected_total without re-crawling.
    meta = {
        "outliers_rejected_total": str(outliers_rejected),
        "calibratable_listings_seen": str(calibratable_seen),
        "outlier_rejection_rate": f"{rejection_rate:.4f}",
        "last_updated": now_iso,
    }

    # Write (idempotent: drop + recreate so reruns don't accumulate)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("DROP TABLE IF EXISTS cap_rates")
        conn.execute("DROP TABLE IF EXISTS calibration_meta")
        ensure_schema(conn)
        for r in rows_out:
            insert_row(conn, r)
        for k, v in meta.items():
            conn.execute(
                "INSERT OR REPLACE INTO calibration_meta(key, value) VALUES (?, ?)",
                (k, v),
            )
        conn.commit()
    finally:
        conn.close()

    summary = {
        "total_cells": len(rows_out),
        "reliable": sum(1 for r in rows_out if r["confidence"] == "reliable"),
        "indicative": sum(1 for r in rows_out if r["confidence"] == "indicative"),
        "fallback": sum(1 for r in rows_out if r["confidence"] == "fallback"),
        "outliers_rejected_total": outliers_rejected,
        "calibratable_listings_seen": calibratable_seen,
        "outlier_rejection_rate": round(rejection_rate, 4),
        "db_path": db_path,
        "last_updated": now_iso,
    }
    log(f"[done] {json.dumps(summary, ensure_ascii=False)}")
    return summary


if __name__ == "__main__":
    calibrate()
