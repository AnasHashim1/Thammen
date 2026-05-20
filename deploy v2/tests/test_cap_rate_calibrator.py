"""
tests/test_cap_rate_calibrator.py — Sprint 2.19 isolated tests.

Standalone runner (project convention: no pytest). Run:
    python tests/test_cap_rate_calibrator.py

Two-layer verification (Operational_Rules #40):
  - Layer 1 (replica/unit): pure functions in cap_rate_calibrator +
    propertyfinder_client.
  - Layer 2 (production): the REAL evaluate_unified._lookup_calibrated_cap_rate
    and _build_income_crosscheck exercised against a fixture cap_rates.sqlite.
"""

import os
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cap_rate_calibrator as cal       # noqa: E402
import propertyfinder_client as pf      # noqa: E402

_passed = 0
_failed = 0


def check(name, cond):
    global _passed, _failed
    if cond:
        _passed += 1
        print(f"  ok  {name}")
    else:
        _failed += 1
        print(f"  XX  {name}")


# ---- Layer 1: reliability gate ----

def test_reliability_gate():
    check("n=25 -> reliable", cal.confidence_for_n(25) == "reliable")
    check("n=20 -> reliable (boundary)", cal.confidence_for_n(20) == "reliable")
    check("n=15 -> indicative", cal.confidence_for_n(15) == "indicative")
    check("n=10 -> indicative (boundary)", cal.confidence_for_n(10) == "indicative")
    check("n=9 -> fallback", cal.confidence_for_n(9) == "fallback")
    check("n=0 -> fallback", cal.confidence_for_n(0) == "fallback")


# ---- Layer 1: net yield formula (corrected) ----

def test_net_yield_formula():
    # rent 40/sqm/mo, sale 5000/sqm, no service charge, opex 0.20
    gross, net = cal.compute_net_yield(40.0, 5000.0, 0, 0.20)
    # gross = 40*12/5000 = 0.096 ; net = 0.096*0.8 - 0 = 0.0768
    check("gross yield correct", abs(gross - 0.096) < 1e-6)
    check("net yield = gross*(1-opex)", abs(net - 0.0768) < 1e-6)
    # with service charge 174/sqm/yr
    g2, n2 = cal.compute_net_yield(40.0, 5000.0, 174, 0.23)
    # net = 0.096*0.77 - 174/5000 = 0.07392 - 0.0348 = 0.03912
    check("net yield subtracts service charge", abs(n2 - 0.03912) < 1e-6)
    # corrected formula must NOT go negative for realistic inputs
    check("realistic net yield positive", n2 > 0)


def test_net_yield_no_denominator():
    gross, net = cal.compute_net_yield(40.0, None, 0, 0.20)
    check("no sale median -> (None,None)", gross is None and net is None)
    g2, n2 = cal.compute_net_yield(40.0, 0, 0, 0.20)
    check("zero sale median -> (None,None)", g2 is None and n2 is None)


# ---- Layer 1: stratification (Rule E4) ----

def test_stratification():
    check("ratio<1.15 -> land_priced",
          cal.classify_villa_stock(1100, 1000) == "land_priced")
    check("1.15<=ratio<1.50 -> aging_stock",
          cal.classify_villa_stock(1400, 1000) == "aging_stock")
    check("1.50<=ratio<2.20 -> modern_stock",
          cal.classify_villa_stock(1800, 1000) == "modern_stock")
    check("ratio>=2.20 -> luxury_new",
          cal.classify_villa_stock(2500, 1000) == "luxury_new")
    check("missing land median -> None",
          cal.classify_villa_stock(1800, None) is None)


# ---- Layer 1: size bracket boundaries ----

def test_size_brackets():
    check("399 -> 0-400", cal.size_bracket_for(399) == "0-400")
    check("400 -> 400-600 (boundary)", cal.size_bracket_for(400) == "400-600")
    check("750 -> 600-900", cal.size_bracket_for(750) == "600-900")
    check("1500 -> 1500+", cal.size_bracket_for(1500) == "1500+")
    check("0 -> None", cal.size_bracket_for(0) is None)
    check("None -> None", cal.size_bracket_for(None) is None)


# ---- Layer 1: GIS area token matching ----

def test_area_token():
    # GIS 'الغرافة' should match MoJ 'غرافة الريان'
    check("GIS Gharafa == MoJ Gharafa Al-Rayyan",
          cal.area_token("الغرافة") == cal.area_token("غرافة الريان"))
    # trailing zone number stripped
    check("zone number stripped",
          cal.area_token("المعمورة 56") == cal.area_token("المعمورة"))
    # 'الدحيل' vs MoJ 'دحيل'
    check("Duhail leading-al stripped",
          cal.area_token("الدحيل") == cal.area_token("دحيل"))


# ---- Layer 1: stale row detection ----

def test_is_stale():
    now = datetime(2026, 5, 20, tzinfo=timezone.utc)
    fresh = (now - timedelta(days=5)).isoformat()
    old = (now - timedelta(days=45)).isoformat()
    check("5 days -> not stale", cal.is_stale(fresh, now=now) is False)
    check("45 days -> stale", cal.is_stale(old, now=now) is True)
    check("None -> stale", cal.is_stale(None, now=now) is True)
    check("garbage -> stale", cal.is_stale("not-a-date", now=now) is True)


# ---- Layer 1: PropertyFinder client ----

def test_pf_asset_type_mapping():
    check("Apartment -> apartment_building",
          pf.map_property_type("Apartment") == "apartment_building")
    check("Hotel Apartments -> apartment_building",
          pf.map_property_type("Hotel Apartments") == "apartment_building")
    check("Villa -> villa", pf.map_property_type("Villa") == "villa")
    check("Townhouse -> villa", pf.map_property_type("Townhouse") == "villa")
    check("Compound -> compound_small",
          pf.map_property_type("Compound") == "compound_small")
    check("unknown -> None", pf.map_property_type("Spaceship") is None)


def test_pf_next_data_malformed():
    check("missing script tag -> None",
          pf.extract_next_data("<html>no next data</html>") is None)
    check("malformed json -> None",
          pf.extract_next_data(
              '<script id="__NEXT_DATA__">{not json}</script>') is None)
    valid = '<script id="__NEXT_DATA__">{"a": 1}</script>'
    check("valid json parsed", pf.extract_next_data(valid) == {"a": 1})


def test_pf_pagination_url():
    base = "https://x/rent.html"
    check("page<=1 -> base unchanged", pf._build_page_url(base, 1) == base)
    check("page=3 -> ?page=3", pf._build_page_url(base, 3) == base + "?page=3")
    base_q = "https://x/rent.html?cat=1"
    check("existing query -> &page=3",
          pf._build_page_url(base_q, 3) == base_q + "&page=3")


def test_pf_unknown_category():
    raised = False
    try:
        pf.fetch_rentals(category="does_not_exist", max_pages=1)
    except ValueError:
        raised = True
    check("unknown category raises ValueError", raised)


def test_pf_gps_out_of_qatar():
    # listing outside Qatar bbox must be rejected
    bad = {"property": {"id": 1, "property_type": "Villa",
                        "price": {"value": 10000, "period": "monthly"},
                        "size": {"value": 300},
                        "location": {"coordinates": {"lat": 48.8, "lon": 2.3}}}}
    check("Paris coords rejected", pf.normalize_listing(bad) is None)
    good = dict(bad)
    good["property"] = dict(bad["property"])
    good["property"]["location"] = {"coordinates": {"lat": 25.3, "lon": 51.5}}
    norm = pf.normalize_listing(good)
    check("Qatar coords accepted", norm is not None and norm["asset_type"] == "villa")


def test_pf_period_normalization():
    yearly = {"property": {"id": 2, "property_type": "Apartment",
                          "price": {"value": 120000, "period": "yearly"},
                          "size": {"value": 100},
                          "location": {"coordinates": {"lat": 25.3, "lon": 51.5}}}}
    norm = pf.normalize_listing(yearly)
    check("yearly rent -> monthly", abs(norm["monthly_rent"] - 10000.0) < 1e-6)


# ---- Layer 1: SQLite schema enforcement ----

def _fixture_db(path, rows):
    conn = sqlite3.connect(path)
    conn.execute("DROP TABLE IF EXISTS cap_rates")
    cal.ensure_schema(conn)
    for r in rows:
        cal.insert_row(conn, r)
    conn.commit()
    conn.close()


def _villa_row(area, bracket, stock, n, cap, conf):
    return {
        "district_aname": area, "district_dist_no": 1, "asset_type": "villa",
        "bedrooms": None, "size_bracket": bracket, "stock_class": stock,
        "median_monthly_rent_qar": 18000, "median_rent_per_sqm": 36.0,
        "sample_size": n, "gross_yield": 0.078, "service_charge_qar_sqm_year": 0,
        "net_yield": cap, "cap_rate": cap, "confidence": conf,
        "last_updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "notes": "fixture",
    }


def test_schema_roundtrip():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    try:
        _fixture_db(path, [_villa_row("الخيسة", "400-600", "modern_stock", 24, 0.062, "reliable")])
        conn = sqlite3.connect(path)
        cols = [r[1] for r in conn.execute("PRAGMA table_info(cap_rates)").fetchall()]
        row = conn.execute("SELECT cap_rate, confidence, sample_size FROM cap_rates").fetchone()
        conn.close()
        check("schema has confidence column", "confidence" in cols)
        check("schema has cap_rate column", "cap_rate" in cols)
        check("inserted row reads back", row == (0.062, "reliable", 24))
    finally:
        os.remove(path)


# ---- Layer 2: PRODUCTION engine lookup against fixture DB ----

def test_production_calibrated_lookup():
    import evaluate_unified as eu
    real_db = eu._CAP_RATES_DB
    backup = real_db + ".bak_test"
    had = os.path.exists(real_db)
    if had:
        os.replace(real_db, backup)
    try:
        _fixture_db(real_db, [
            _villa_row("الخيسة", "400-600", "modern_stock", 24, 0.062, "reliable"),
            _villa_row("الوكير", "600-900", "aging_stock", 8, 0.05, "fallback"),
        ])
        # reliable cell -> calibrated
        rate, prov = eu._lookup_calibrated_cap_rate("villa", "الخيسة", 520, None)
        check("production: reliable cell returns calibrated rate", rate == 0.062)
        check("production: provenance source=calibrated",
              prov and prov.get("source") == "calibrated")
        # standalone_villa maps to villa
        r2, _ = eu._lookup_calibrated_cap_rate("standalone_villa", "الخيسة", 520, None)
        check("production: standalone_villa maps to villa", r2 == 0.062)
        # fallback-confidence row is NOT used (excluded by query)
        r3, p3 = eu._lookup_calibrated_cap_rate("villa", "الوكير", 750, None)
        check("production: fallback-confidence row excluded", r3 is None)
        # non-calibratable asset
        r4, p4 = eu._lookup_calibrated_cap_rate("apartment_building", "الخيسة", 520, None)
        check("production: apartment not calibratable", r4 is None and p4 is None)
        # full income cross-check uses calibrated rate + attaches provenance
        inc = eu._build_income_crosscheck(18000, None, "villa", 3_000_000,
                                          area_name="الخيسة", plot_area_m2=520)
        check("production: income uses calibrated cap_rate", inc["cap_rate"] == 0.062)
        check("production: income carries provenance",
              inc["cap_rate_provenance"]["source"] == "calibrated")
        # absent area -> hardcoded fallback path
        inc2 = eu._build_income_crosscheck(18000, None, "villa", 3_000_000,
                                           area_name="منطقة مجهولة", plot_area_m2=520)
        check("production: unknown area -> hardcoded fallback",
              inc2["cap_rate_provenance"]["source"] == "hardcoded")
    finally:
        if os.path.exists(real_db):
            os.remove(real_db)
        if had:
            os.replace(backup, real_db)


def test_production_missing_db_safe():
    import evaluate_unified as eu
    real_db = eu._CAP_RATES_DB
    backup = real_db + ".bak_test2"
    had = os.path.exists(real_db)
    if had:
        os.replace(real_db, backup)
    try:
        rate, prov = eu._lookup_calibrated_cap_rate("villa", "الخيسة", 520, None)
        check("production: missing DB -> (None,None) safe-fail",
              rate is None and prov is None)
        inc = eu._build_income_crosscheck(18000, None, "villa", 3_000_000,
                                          area_name="الخيسة", plot_area_m2=520)
        check("production: missing DB -> hardcoded cap_rate used",
              inc["cap_rate_provenance"]["source"] == "hardcoded")
    finally:
        if had:
            os.replace(backup, real_db)


if __name__ == "__main__":
    print("Sprint 2.19 — Cap Rate Calibration isolated tests")
    print("=" * 70)
    test_reliability_gate()
    test_net_yield_formula()
    test_net_yield_no_denominator()
    test_stratification()
    test_size_brackets()
    test_area_token()
    test_is_stale()
    test_pf_asset_type_mapping()
    test_pf_next_data_malformed()
    test_pf_pagination_url()
    test_pf_unknown_category()
    test_pf_gps_out_of_qatar()
    test_pf_period_normalization()
    test_schema_roundtrip()
    test_production_calibrated_lookup()
    test_production_missing_db_safe()
    print("=" * 70)
    print(f"Sprint 2.19 tests: {_passed} passed, {_failed} failed")
    sys.exit(0 if _failed == 0 else 1)
