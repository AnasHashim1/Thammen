"""
tests/test_sprint_2p19p1_polish.py — Sprint 2.19.1 isolated tests.

Standalone runner (project convention: no pytest). Run:
    python tests/test_sprint_2p19p1_polish.py

Covers the six Sprint 2.19.1 polish fixes:
  #1/#2 — Arabic labels + translated source/confidence in the provenance brief.
  #3    — villa hardcoded cap rate is 4.0% BY DESIGN, with an Arabic rationale.
  #4    — villa rows with no MoJ land median are hard-guarded to fallback.
  #5    — implausible rent/m² listings are rejected, counted, and persisted.
  #6    — the subtree-push divergence procedure is documented on disk.

Two-layer verification (Operational_Rules #40):
  - Layer 1: pure functions + calibrate() with injected fakes (no network).
  - Layer 2: the REAL evaluate_unified._build_income_crosscheck and
    api._calibration_freshness exercised against fixture data.
"""

import os
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cap_rate_calibrator as cal       # noqa: E402
import output_briefs as ob              # noqa: E402
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


# ---- Fix #5: outlier filter (Layer 1) ----

def _listing(rps, asset="villa"):
    # rent_per_sqm drives the filter; keep monthly/size consistent for realism.
    size = 500.0
    return {"asset_type": asset, "monthly_rent": rps * size, "size_sqm": size,
            "rent_per_sqm": rps, "lat": 25.30, "lon": 51.50}


def test_outlier_filter():
    check("rps 0.67 rejected (too low)", pf.is_plausible_listing(_listing(0.67)) is False)
    check("rps 250 rejected (clearly impossible)", pf.is_plausible_listing(_listing(250)) is False)
    # Sprint 2.19.1 decision: the firm physical ceiling is 200, NOT lower. The
    # brief flagged 183.33 as suspect, but 183 is within reach of luxury rents,
    # and dropping the ceiling to 150 would silently reject genuine Pearl/Lusail
    # premium listings (~150-180) and bias their medians down. n=1 suspects stay
    # fallback and a median is robust to a lone in-band outlier.
    check("rps 183.33 within band (not rejected)", pf.is_plausible_listing(_listing(183.33)) is True)
    check("rps 36 accepted", pf.is_plausible_listing(_listing(36)) is True)
    check("rps 5 accepted (floor boundary)", pf.is_plausible_listing(_listing(5)) is True)
    check("rps 200 accepted (ceiling boundary)", pf.is_plausible_listing(_listing(200)) is True)
    check("rps 4.99 rejected", pf.is_plausible_listing(_listing(4.99)) is False)
    check("rps 200.01 rejected", pf.is_plausible_listing(_listing(200.01)) is False)
    # missing rent_per_sqm -> derive from monthly/size
    derived = {"monthly_rent": 18000.0, "size_sqm": 500.0}  # 36/m²
    check("derives rps when absent", pf.is_plausible_listing(derived) is True)
    check("zero size -> rejected", pf.is_plausible_listing({"monthly_rent": 1, "size_sqm": 0}) is False)
    check("None listing -> rejected", pf.is_plausible_listing(None) is False)


# ---- Fix #4 + #5: calibrate() with injected fakes (Layer 1) ----

class _FakeMoj:
    """Stand-in for MojSaleIndex returning controlled medians per area token."""
    def __init__(self, by_token):
        self._by_token = by_token

    def villa_and_land_median(self, token, bracket, gis_aname=None):
        return self._by_token.get(token, (None, None, 0, None))


def _run_calibrate(listings, by_token, aname):
    tok = cal.area_token(aname)
    moj = _FakeMoj({tok: by_token})
    # Pre-seed the GIS cache so fetch_gis_district never hits the network:
    # key is (round(lat,4), round(lon,4)) -> (dist_no, aname).
    gis_cache = {}
    for L in listings:
        gis_cache[(round(L["lat"], 4), round(L["lon"], 4))] = (1, aname)
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    summary = cal.calibrate(db_path=path, listings=listings, moj_index=moj,
                            gis_cache=gis_cache, log=lambda *a, **k: None)
    return path, summary


def test_calibrate_outlier_counter():
    # 25 in-band villa rentals + 2 outliers in الخيسة 400-600.
    listings = [_listing(36) for _ in range(25)] + [_listing(0.67), _listing(250)]
    # land median present so stock class CAN be computed (isolates Fix #5).
    path, summary = _run_calibrate(listings, (5000.0, 4000.0, 24, "الخيسة"), "الخيسة")
    try:
        check("outliers_rejected_total == 2", summary["outliers_rejected_total"] == 2)
        check("calibratable_listings_seen == 27", summary["calibratable_listings_seen"] == 27)
        check("rejection_rate ~= 0.074", abs(summary["outlier_rejection_rate"] - 2 / 27) < 1e-3)
        # meta table persisted and readable
        conn = sqlite3.connect(path)
        meta = {k: v for k, v in conn.execute("SELECT key, value FROM calibration_meta")}
        # the surviving cell used only the 25 in-band rentals
        nrow = conn.execute("SELECT sample_size FROM cap_rates").fetchone()
        conn.close()
        check("meta persists outliers_rejected_total=2", meta.get("outliers_rejected_total") == "2")
        check("outliers excluded from cell sample (n=25)", nrow and nrow[0] == 25)
    finally:
        os.remove(path)


def test_stratification_null_guard():
    # 25 in-band villa rentals, MoJ has a villa median but NO land median.
    listings = [_listing(36) for _ in range(25)]
    path, summary = _run_calibrate(listings, (5000.0, None, 30, "اللؤلؤة"), "اللؤلؤة")
    try:
        conn = sqlite3.connect(path)
        row = conn.execute(
            "SELECT stock_class, confidence, notes FROM cap_rates").fetchone()
        conn.close()
        stock_class, confidence, notes = row
        check("no land median -> stock_class NULL", stock_class is None)
        check("Fix #4: forced to fallback despite n=25", confidence == "fallback")
        check("Fix #4: note records stratification_unavailable",
              notes and "stratification_unavailable:no_moj_land_median" in notes)
    finally:
        os.remove(path)


# ---- Fix #1/#2: provenance Arabic labels + translated values (Layer 1) ----

def test_provenance_translation_calibrated():
    prov = {"source": "calibrated", "confidence": "reliable", "cap_rate_pct": 4.7,
            "sample_size": 35, "last_updated": "2026-05-20T10:00:00+00:00"}
    sec = ob.build_cap_rate_provenance_section(prov)
    c = sec["content"]
    check("calibrated source_ar", c["source_ar"] == "مُعايَر من بيانات السوق")
    check("reliable confidence_ar", c["confidence_ar"] == "موثوقة")
    check("English source retained", c["source"] == "calibrated")
    check("English confidence retained", c["confidence"] == "reliable")
    check("body_ar present", bool(c.get("body_ar")))


def test_provenance_translation_hardcoded():
    prov = {"source": "hardcoded", "confidence": "fallback", "cap_rate_pct": 4.0,
            "reason_ar": "الفيلات السكنية سكن مالكي ..."}
    sec = ob.build_cap_rate_provenance_section(prov)
    c = sec["content"]
    check("hardcoded source_ar", c["source_ar"] == "معدل افتراضي (غير مُعايَر)")
    check("fallback confidence_ar mentions 'غير كافية'", "غير كافية" in c["confidence_ar"])
    check("indicative confidence_ar",
          ob._PROVENANCE_CONFIDENCE_AR["indicative"] == "إرشادية")
    check("None provenance -> None section",
          ob.build_cap_rate_provenance_section(None) is None)


# ---- Fix #3: villa 4% is intentional, with rationale (Layer 2 / production) ----

def test_production_villa_hardcoded_rate_and_rationale():
    import evaluate_unified as eu
    # Unknown area => no calibrated match => hardcoded path, regardless of any
    # committed cap_rates.sqlite snapshot.
    inc = eu._build_income_crosscheck(18000, None, "villa", 3_000_000,
                                      area_name="منطقة غير معروفة بتاتاً", plot_area_m2=520)
    prov = inc["cap_rate_provenance"]
    check("villa hardcoded cap_rate == 0.04", inc["cap_rate"] == 0.04)
    check("provenance source == hardcoded", prov["source"] == "hardcoded")
    check("provenance carries asset_type=villa", prov.get("asset_type") == "villa")
    check("reason_ar explains the low residential rate",
          "الفيلات" in prov.get("reason_ar", "") and "4%" in prov.get("reason_ar", ""))
    # standalone_villa maps to the same 4% rate
    inc2 = eu._build_income_crosscheck(18000, None, "standalone_villa", 3_000_000,
                                       area_name="منطقة غير معروفة بتاتاً", plot_area_m2=520)
    check("standalone_villa hardcoded == 0.04", inc2["cap_rate"] == 0.04)


# ---- Fix #5: counter exposed via the production api freshness (Layer 2) ----

def test_production_api_exposes_outlier_counter():
    import api
    real_db = str(api._cap_rates_db_path())
    backup = real_db + ".bak_2p19p1_test"
    had = os.path.exists(real_db)
    if had:
        os.replace(real_db, backup)
    try:
        conn = sqlite3.connect(real_db)
        conn.execute("DROP TABLE IF EXISTS cap_rates")
        conn.execute("DROP TABLE IF EXISTS calibration_meta")
        cal.ensure_schema(conn)
        cal.insert_row(conn, {
            "district_aname": "الخيسة", "district_dist_no": 1, "asset_type": "villa",
            "bedrooms": None, "size_bracket": "400-600", "stock_class": "modern_stock",
            "median_monthly_rent_qar": 18000, "median_rent_per_sqm": 36.0,
            "sample_size": 24, "gross_yield": 0.078, "service_charge_qar_sqm_year": 0,
            "net_yield": 0.062, "cap_rate": 0.062, "confidence": "reliable",
            "last_updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "notes": "fixture",
        })
        for k, v in (("outliers_rejected_total", "7"),
                     ("calibratable_listings_seen", "120"),
                     ("outlier_rejection_rate", "0.0583")):
            conn.execute("INSERT OR REPLACE INTO calibration_meta(key,value) VALUES (?,?)", (k, v))
        conn.commit()
        conn.close()
        fresh = api._calibration_freshness()
        check("freshness exposes outliers_rejected_total=7",
              fresh.get("outliers_rejected_total") == 7)
        check("freshness exposes calibratable_listings_seen=120",
              fresh.get("calibratable_listings_seen") == 120)
        check("freshness exposes outlier_rejection_rate≈0.0583",
              abs((fresh.get("outlier_rejection_rate") or 0) - 0.0583) < 1e-6)
    finally:
        if os.path.exists(real_db):
            os.remove(real_db)
        if had:
            os.replace(backup, real_db)


def test_production_api_counter_absent_on_old_snapshot():
    """A snapshot without calibration_meta must not crash; counter -> None."""
    import api
    real_db = str(api._cap_rates_db_path())
    backup = real_db + ".bak_2p19p1_test2"
    had = os.path.exists(real_db)
    if had:
        os.replace(real_db, backup)
    try:
        conn = sqlite3.connect(real_db)
        conn.execute("DROP TABLE IF EXISTS cap_rates")
        conn.execute("DROP TABLE IF EXISTS calibration_meta")
        # cap_rates only — simulate a pre-2.19.1 snapshot.
        conn.execute(
            "CREATE TABLE cap_rates (confidence TEXT, last_updated TEXT)")
        conn.execute("INSERT INTO cap_rates VALUES ('reliable','2026-05-19T00:00:00+00:00')")
        conn.commit()
        conn.close()
        fresh = api._calibration_freshness()
        check("old snapshot still available", fresh.get("available") is True)
        check("missing counter -> None (no crash)",
              fresh.get("outliers_rejected_total") is None)
    finally:
        if os.path.exists(real_db):
            os.remove(real_db)
        if had:
            os.replace(backup, real_db)


# ---- Fix #6: divergence procedure documented on disk ----

def test_rule_subtree_divergence_documented():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(here, "docs", "Operational_Rules.md")
    with open(path, "r", encoding="utf-8") as f:
        txt = f.read()
    check("subtree split documented", "subtree split" in txt)
    check("temp-branch divergence procedure present", "heroku-deploy-tmp" in txt)
    check("force push to heroku documented", "--force" in txt and "heroku" in txt)


if __name__ == "__main__":
    print("Sprint 2.19.1 — Polish & Fixes isolated tests")
    print("=" * 70)
    test_outlier_filter()
    test_calibrate_outlier_counter()
    test_stratification_null_guard()
    test_provenance_translation_calibrated()
    test_provenance_translation_hardcoded()
    test_production_villa_hardcoded_rate_and_rationale()
    test_production_api_exposes_outlier_counter()
    test_production_api_counter_absent_on_old_snapshot()
    test_rule_subtree_divergence_documented()
    print("=" * 70)
    print(f"Sprint 2.19.1 tests: {_passed} passed, {_failed} failed")
    sys.exit(0 if _failed == 0 else 1)
