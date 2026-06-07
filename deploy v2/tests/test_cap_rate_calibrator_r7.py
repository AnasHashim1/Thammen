"""
tests/test_cap_rate_calibrator_r7.py — Sprint 2.19.2 (R7 income cross-check)
isolated tests for the stratified villa-yield calibration improvements.

Run (project convention — no pytest):
    PYTHONIOENCODING=utf-8 python tests/test_cap_rate_calibrator_r7.py

Two-layer verification (Operational_Rules #40 / E14): the a18 reconciliation
(resolve_key / medians_for_key) and the end-to-end calibrate() are exercised
against the REAL moj_weekly.csv + REAL engine functions (resolve_moj_area_name,
build_reference, area_match_key) — not echoes of the inputs. Structural asserts
(keys, n>0, override routing, ordering) so a MoJ refresh can't flake exact values.
"""

import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cap_rate_calibrator as cal       # noqa: E402
import moj_reference as mr              # noqa: E402

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


HERE = os.path.dirname(os.path.abspath(__file__))
MOJ_CSV = os.path.join(os.path.dirname(HERE), "moj_weekly.csv")
_HAS_CSV = os.path.exists(MOJ_CSV)


# ---- (a) standalone-villa filter ----

def _L(**kw):
    base = {"asset_type": "villa", "property_type_raw": "Villa",
            "monthly_rent": 15000.0, "size_sqm": 500.0, "rent_per_sqm": 30.0,
            "furnished": "NO", "lat": 25.24, "lon": 51.49, "id": None}
    base.update(kw)
    return base


def test_standalone_villa_filter():
    check("Villa -> standalone (kept)", cal.is_standalone_villa(_L(property_type_raw="Villa")))
    check("Townhouse -> NOT standalone (excluded)",
          not cal.is_standalone_villa(_L(property_type_raw="Townhouse")))
    check("compound gate N/A (kept)",
          cal.is_standalone_villa(_L(asset_type="compound_small", property_type_raw="Compound")))
    check("apartment gate N/A (kept)",
          cal.is_standalone_villa(_L(asset_type="apartment_building", property_type_raw="Apartment")))
    check("missing property_type_raw -> excluded (defensive)",
          not cal.is_standalone_villa(_L(property_type_raw=None)))


# ---- (e) furnished-consistent rent median ----

def test_rent_medians_furnished():
    # 4 unfurnished/partly + 1 fully-furnished outlier -> median excludes the YES
    cells = [_L(monthly_rent=12000, rent_per_sqm=24, furnished="NO"),
             _L(monthly_rent=14000, rent_per_sqm=28, furnished="NO"),
             _L(monthly_rent=16000, rent_per_sqm=32, furnished="PARTLY"),
             _L(monthly_rent=18000, rent_per_sqm=36, furnished="NO"),
             _L(monthly_rent=40000, rent_per_sqm=80, furnished="YES")]  # furnished premium
    med_rent, med_rps, n_used, furn = cal.rent_medians(cells)
    check("excludes fully-furnished from median (n_used=4)", n_used == 4)
    check("furnished YES not in median (rent <= 18000)", med_rent <= 18000)
    check("furn_counts records the split", furn.get("YES") == 1 and furn.get("NO") == 3)
    # too few non-furnished (<3) -> fall back to ALL
    few = [_L(monthly_rent=13000, furnished="YES"),
           _L(monthly_rent=14000, furnished="YES"),
           _L(monthly_rent=15000, furnished="NO")]
    _, _, n_used2, _ = cal.rent_medians(few)
    check("falls back to all when <3 non-furnished", n_used2 == 3)


# ---- (d) a18 GIS->MoJ reconciliation via the ENGINE path (real CSV) ----

def test_a18_resolve_key():
    if not _HAS_CSV:
        check("(skip: moj_weekly.csv absent) resolve_key", True)
        return
    idx = cal.MojSaleIndex(MOJ_CSV)
    check("engine a18 path active (_A18_OK)", cal._A18_OK is True)
    # zone-numbered GIS aname pools to the bare stem (a18 area_match_key)
    k_zone = idx.resolve_key("المعمورة 56")
    k_bare = idx.resolve_key("المعمورة")
    check("resolve('المعمورة 56') == area_match_key stem",
          k_zone == mr.area_match_key("المعمورة 56"))
    check("zone-numbered + bare resolve to the SAME key", k_zone == k_bare and k_zone)
    # override routing (GIS_TO_MOJ_NAME_OVERRIDES): امريخ الجنوبي -> مريخ (A16)
    k_marikh = idx.resolve_key("امريخ الجنوبي")
    check("override 'امريخ الجنوبي' -> 'مريخ'", k_marikh == "مريخ")
    # unknown area -> None (graceful)
    check("unknown GIS area -> None", idx.resolve_key("منطقة لا توجد اطلاقا") is None)


def test_a18_medians_for_key():
    if not _HAS_CSV:
        check("(skip) medians_for_key", True)
        return
    idx = cal.MojSaleIndex(MOJ_CSV)
    # عين خالد has many villa+land sales — both medians should resolve in 400-600
    key = idx.resolve_key("عين خالد")
    check("عين خالد resolves to a MoJ key", bool(key))
    v_med, l_med, v_n = idx.medians_for_key(key, "400-600")
    check("villa median present + positive", v_med and v_med > 0)
    check("villa n reported (>0)", v_n and v_n > 0)
    check("medians == build_reference (same engine pool)",
          v_med == (mr.build_reference(idx.rows, key, idx.max_date)
                    .get("categories", {}).get("villa", {})
                    .get("size_brackets", {}).get("400-600", {})
                    .get("price_per_m2_median")))
    # falsy key -> graceful (None, None, 0)
    check("None key -> (None,None,0)", idx.medians_for_key(None, "400-600") == (None, None, 0))


# ---- (c) dedupe in collect_rentals ----

def test_collect_rentals_dedupe():
    dupe = [_L(id=1, monthly_rent=12000), _L(id=1, monthly_rent=12000),  # exact dup id
            _L(id=2, monthly_rent=13000), _L(id=3, monthly_rent=14000)]
    orig = cal.pf.fetch_rentals
    try:
        cal.pf.fetch_rentals = lambda **kw: list(dupe) if kw.get("category") == "villas" else []
        out = cal.collect_rentals(log=lambda *a, **k: None)
        ids = [r["id"] for r in out]
        check("collect_rentals dedupes by id (3 unique from 4)", sorted(ids) == [1, 2, 3])
    finally:
        cal.pf.fetch_rentals = orig


# ---- end-to-end calibrate() (real MoJ index + injected listings, no network) ----

def test_calibrate_end_to_end():
    if not _HAS_CSV:
        check("(skip) calibrate end-to-end", True)
        return
    idx = cal.MojSaleIndex(MOJ_CSV)
    # Real coords from the §5 smoke -> pre-fill gis_cache so NO network fires.
    gis_cache = {}
    AIN = (25.2230, 51.4691)   # -> عين خالد
    MAA = (25.2395, 51.4992)   # -> المعمورة 56
    gis_cache[(round(AIN[0], 4), round(AIN[1], 4))] = (95, "عين خالد")
    gis_cache[(round(MAA[0], 4), round(MAA[1], 4))] = (804, "المعمورة 56")

    listings = [
        # عين خالد 400-600: 4 standalone villas (1 fully-furnished outlier) + 1 dup id
        _L(id=10, lat=AIN[0], lon=AIN[1], size_sqm=500, monthly_rent=14000, rent_per_sqm=28, furnished="NO"),
        _L(id=10, lat=AIN[0], lon=AIN[1], size_sqm=500, monthly_rent=14000, rent_per_sqm=28, furnished="NO"),  # dup (calibrate doesn't dedupe; collect does) -> still 1 cell entry test below uses sample_size
        _L(id=11, lat=AIN[0], lon=AIN[1], size_sqm=520, monthly_rent=15000, rent_per_sqm=28.8, furnished="PARTLY"),
        _L(id=12, lat=AIN[0], lon=AIN[1], size_sqm=480, monthly_rent=16000, rent_per_sqm=33.3, furnished="NO"),
        _L(id=13, lat=AIN[0], lon=AIN[1], size_sqm=500, monthly_rent=45000, rent_per_sqm=90, furnished="YES"),  # furnished premium (still plausible <200)
        # a TOWNHOUSE in عين خالد -> must be EXCLUDED from the villa pool
        _L(id=14, lat=AIN[0], lon=AIN[1], size_sqm=500, monthly_rent=20000, rent_per_sqm=40, property_type_raw="Townhouse"),
        # المعمورة 56 (villa-6 area) one villa -> keyed to the a18 stem 'المعمورة'
        _L(id=20, lat=MAA[0], lon=MAA[1], size_sqm=650, monthly_rent=16000, rent_per_sqm=24.6, furnished="NO"),
    ]
    fd, db = tempfile.mkstemp(suffix=".sqlite"); os.close(fd)
    try:
        summary = cal.calibrate(db_path=db, listings=listings, moj_index=idx,
                                gis_cache=gis_cache, log=lambda *a, **k: None)
        conn = sqlite3.connect(db); conn.row_factory = sqlite3.Row
        rows = list(conn.execute("SELECT * FROM cap_rates"))
        meta_ok = bool(list(conn.execute("SELECT 1 FROM calibration_meta LIMIT 1")))
        conn.close()
        by = {(r["district_aname"], r["size_bracket"]): r for r in rows}
        # المعمورة 650m² villa binned into the 600-900 cell (displayed under its
        # GIS aname; pooled to the a18 stem for the denominator — see resolve test).
        maa = [r for r in rows if "معمور" in (r["district_aname"] or "")
               and r["size_bracket"] == "600-900"]
        check("المعمورة 650m² villa binned into a 600-900 cell", len(maa) == 1)
        # عين خالد 400-600 cell exists, townhouse excluded -> sample_size == 5 (the 4+dup villa rows; townhouse dropped)
        ain = by.get(("عين خالد", "400-600"))
        check("عين خالد 400-600 cell built", ain is not None)
        if ain:
            check("townhouse excluded from villa pool (sample_size==5)", ain["sample_size"] == 5)
            check("furnished split recorded in notes", "furn=" in (ain["notes"] or ""))
            check("fully-furnished excluded from rent median (note present)",
                  "excl_fully_furnished" in (ain["notes"] or ""))
            check("gross_yield computed (real عين خالد denominator)", ain["gross_yield"] is not None)
            check("net < gross (opex applied)",
                  ain["net_yield"] is not None and ain["net_yield"] < ain["gross_yield"])
        check("calibration_meta written", meta_ok)
        check("summary counts present", summary.get("total_cells") == len(rows))
    finally:
        os.remove(db)


if __name__ == "__main__":
    print("Sprint 2.19.2 (R7) — stratified villa-yield calibration tests")
    print("=" * 70)
    test_standalone_villa_filter()
    test_rent_medians_furnished()
    test_a18_resolve_key()
    test_a18_medians_for_key()
    test_collect_rentals_dedupe()
    test_calibrate_end_to_end()
    print("=" * 70)
    print(f"Sprint 2.19.2 (R7) tests: {_passed} passed, {_failed} failed")
    sys.exit(0 if _failed == 0 else 1)
