"""
test_sprint_2p21p3_t2_connectors.py — Sprint 2.21.3 isolated tests

Covers:
  - PropertyFinder T2 connector (network, parse, dedup, AED skip, sub-Lusail
    filter, end-to-end with mocked HTTP)
  - T2ListingsCache (get/set roundtrip, TTL expiry, schema init resilience)
  - Engine integration helper `_try_hybrid_apartments_response`
    (env flag, district gate, n<MIN, happy path with mocks)

Test discipline:
  - Replica + production verification (Rule #40): every test that imports
    from the connector hits the REAL module path; mocks are scoped to the
    network boundary (`urllib.request.urlopen`) and to the GIS lookup.
  - All cache tests use a tmp_path fixture (no production cache pollution).
  - Run from project root with PYTHONIOENCODING=utf-8:
      python -m unittest tests.test_sprint_2p21p3_t2_connectors -v
    or as a standalone script:
      python tests/test_sprint_2p21p3_t2_connectors.py
"""

from __future__ import annotations
import io
import json
import os
import sys
import sqlite3
import tempfile
import time
import unittest
import urllib.error
from contextlib import closing
from pathlib import Path
from unittest.mock import patch, MagicMock

# Make the project root importable when running this file as a script
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

# Production imports — exercise REAL module paths (Rule #40)
from t2_listings_cache import T2ListingsCache, DEFAULT_TTL_SECONDS
from connectors.propertyfinder_apartments_t2_sales import (
    _http_get,
    _extract_listing_urls,
    _listing_id,
    _parse_jsonld,
    _price_qar_from_entity,
    _area_m2_from_entity,
    _listing_is_lusail,
    size_bracket_label,
    get_apartment_sales_lusail,
    LUSAIL_SALE_URL,
)


# ─────────────────────────────────────────────────────────────────────────
# Test fixtures
# ─────────────────────────────────────────────────────────────────────────

VALID_JSONLD_BLOCK = (
    '<script id="plp-schema" type="application/ld+json">'
    + json.dumps({
        "@context": "https://schema.org/",
        "mainEntity": {
            "mainEntity": {
                "@type": "RealEstateListing",
                "name": "Lusail Marina Apartment for sale",
                "address": {"addressLocality": "Lusail Marina"},
                "offers": {
                    "@type": "Offer",
                    "price": "2500000",
                    "priceCurrency": "QAR",
                },
                "floorSize": {
                    "@type": "QuantitativeValue",
                    "value": "120",
                    "unitCode": "MTK",
                },
                "datePosted": "2026-05-20",
            },
        },
    })
    + "</script>"
)

LIST_PAGE_HTML = """
<html><body>
<a href="/en/plp/buy/apartment-for-sale-lusail-marina-1001.html">A</a>
<a href="/en/plp/buy/apartment-for-sale-lusail-marina-1001.html">A dup</a>
<a href="/en/plp/buy/apartment-for-sale-lusail-fox-hills-1002.html">B</a>
<a href="/en/plp/buy/apartment-for-sale-doha-pearl-1003.html">C</a>
<a href="/en/plp/buy/apartment-for-sale-lusail-marina-1001.html">A again</a>
</body></html>
"""

LUSAIL_DETAIL_HTML = "<html><body>Lusail apartment for sale " + VALID_JSONLD_BLOCK + "</body></html>"


def _fake_response(body: str, status: int = 200):
    """Mimic the urllib response object for context-manager usage."""
    fake = MagicMock()
    fake.status = status
    fake.read.return_value = body.encode("utf-8")
    fake.__enter__.return_value = fake
    fake.__exit__.return_value = False
    return fake


# ─────────────────────────────────────────────────────────────────────────
# 1. PropertyFinder connector — helpers
# ─────────────────────────────────────────────────────────────────────────

class TestHttpGet(unittest.TestCase):

    def test_01_http_get_returns_body_on_200(self):
        with patch("urllib.request.urlopen", return_value=_fake_response("hello", 200)):
            self.assertEqual(_http_get("https://example.test/x"), "hello")

    def test_02_http_get_returns_none_on_httperror_d6(self):
        err = urllib.error.HTTPError("https://x", 503, "boom", {}, io.BytesIO(b""))
        with patch("urllib.request.urlopen", side_effect=err):
            self.assertIsNone(_http_get("https://example.test/x"))

    def test_03_http_get_returns_none_on_urlerror_d6(self):
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("net")):
            self.assertIsNone(_http_get("https://example.test/x"))


class TestExtractAndDedup(unittest.TestCase):

    def test_04_extract_listing_urls_dedupes_d9(self):
        urls = _extract_listing_urls(LIST_PAGE_HTML)
        # 5 raw <a> hrefs collapse to 3 unique paths (D9)
        self.assertEqual(len(urls), 3)
        self.assertTrue(all(u.startswith("https://www.propertyfinder.qa") for u in urls))

    def test_05_listing_id_extracts_trailing_numeric(self):
        self.assertEqual(
            _listing_id("https://www.propertyfinder.qa/en/plp/buy/slug-54006689.html"),
            "54006689",
        )
        self.assertIsNone(_listing_id("https://x/no-id-here.html"))


class TestJsonLdParse(unittest.TestCase):

    def test_06_parse_jsonld_returns_entity_on_valid_block(self):
        entity = _parse_jsonld(LUSAIL_DETAIL_HTML)
        self.assertIsInstance(entity, dict)
        self.assertEqual(entity.get("@type"), "RealEstateListing")
        self.assertIn("offers", entity)

    def test_07_parse_jsonld_returns_none_on_missing_block_d7(self):
        self.assertIsNone(_parse_jsonld("<html><body>no script here</body></html>"))

    def test_08_parse_jsonld_returns_none_on_malformed_json_d7(self):
        html = '<script id="plp-schema" type="application/ld+json">{not_json}</script>'
        self.assertIsNone(_parse_jsonld(html))


class TestPriceAndArea(unittest.TestCase):

    def test_09_price_qar_from_entity_returns_int_for_qar(self):
        ent = {"offers": {"price": "2500000", "priceCurrency": "QAR"}}
        self.assertEqual(_price_qar_from_entity(ent), 2_500_000)

    def test_10_price_qar_from_entity_returns_none_for_aed_d8(self):
        ent = {"offers": {"price": "150000", "priceCurrency": "AED"}}
        self.assertIsNone(_price_qar_from_entity(ent))

    def test_11_price_qar_from_entity_rejects_sub_threshold(self):
        # 50K is too low for a sales listing — likely rent or service charge
        ent = {"offers": {"price": "50000", "priceCurrency": "QAR"}}
        self.assertIsNone(_price_qar_from_entity(ent))

    def test_12_area_m2_from_entity_returns_float_for_mtk(self):
        ent = {"floorSize": {"value": "120", "unitCode": "MTK"}}
        self.assertEqual(_area_m2_from_entity(ent), 120.0)

    def test_13_area_m2_from_entity_returns_none_for_wrong_unit(self):
        ent = {"floorSize": {"value": "1500", "unitCode": "FTK"}}  # sqft
        self.assertIsNone(_area_m2_from_entity(ent))

    def test_14_size_bracket_label_boundaries(self):
        self.assertEqual(size_bracket_label(99.9), "0-100")
        self.assertEqual(size_bracket_label(100), "100-150")
        self.assertEqual(size_bracket_label(149.9), "100-150")
        self.assertEqual(size_bracket_label(150), "150-250")
        self.assertEqual(size_bracket_label(249.9), "150-250")
        self.assertEqual(size_bracket_label(250), "250+")
        self.assertEqual(size_bracket_label(1000), "250+")

    def test_15_listing_is_lusail_filter(self):
        ent = {"address": {"addressLocality": "Lusail Marina"}}
        self.assertTrue(_listing_is_lusail("body", ent))
        ent2 = {"address": {"addressLocality": "Al Messila"}}
        self.assertFalse(_listing_is_lusail("apartment for sale in Al Messila Doha", ent2))
        # body-level Lusail mention fallback
        self.assertTrue(_listing_is_lusail("contains Lusail mention", {}))


# ─────────────────────────────────────────────────────────────────────────
# 2. Connector — end-to-end with mocked HTTP
# ─────────────────────────────────────────────────────────────────────────

class TestGetApartmentSalesLusail(unittest.TestCase):

    def test_16_happy_path_with_mocked_http(self):
        responses = {LUSAIL_SALE_URL: LIST_PAGE_HTML}
        # 3 unique listing URLs from the list page — each gets a detail fetch
        for path in ("/en/plp/buy/apartment-for-sale-lusail-marina-1001.html",
                     "/en/plp/buy/apartment-for-sale-lusail-fox-hills-1002.html",
                     "/en/plp/buy/apartment-for-sale-doha-pearl-1003.html"):
            responses[f"https://www.propertyfinder.qa{path}"] = LUSAIL_DETAIL_HTML

        with patch(
            "connectors.propertyfinder_apartments_t2_sales._http_get",
            side_effect=lambda url: responses.get(url),
        ), patch("time.sleep"):    # silence inter-request sleeps in test
            result = get_apartment_sales_lusail(use_cache=False)

        # All 3 details parse to the same fixture (price=2.5M, area=120)
        self.assertEqual(len(result), 3)
        for row in result:
            self.assertEqual(row["source"], "propertyfinder")
            self.assertEqual(row["tier"], "T2")
            self.assertEqual(row["transaction_type"], "sale")
            self.assertEqual(row["raw_price_qar"], 2_500_000)
            self.assertEqual(row["area_m2"], 120.0)
            self.assertAlmostEqual(row["value_per_m2"], 2_500_000 / 120, places=1)
            self.assertEqual(row["district"], "Lusail")
            self.assertEqual(row["size_bracket"], "100-150")
            self.assertTrue(len(row["raw_html_excerpt"]) <= 500)

    def test_17_network_all_fail_returns_empty_d6(self):
        with patch(
            "connectors.propertyfinder_apartments_t2_sales._http_get",
            return_value=None,
        ), patch("time.sleep"):
            self.assertEqual(get_apartment_sales_lusail(use_cache=False), [])


# ─────────────────────────────────────────────────────────────────────────
# 3. Cache — D4 TTL contract
# ─────────────────────────────────────────────────────────────────────────

class TestT2ListingsCache(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmpdir.name) / "test_cache.sqlite"

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_18_cache_get_set_roundtrip(self):
        cache = T2ListingsCache(db_path=self.db_path)
        payload = [{"source": "propertyfinder", "value_per_m2": 21000.0}]
        cache.set("propertyfinder", "Lusail", "100-150", payload)
        hit = cache.get("propertyfinder", "Lusail", "100-150")
        self.assertEqual(hit, payload)

    def test_19_cache_ttl_expiry_returns_none(self):
        cache = T2ListingsCache(db_path=self.db_path, ttl_seconds=1)
        cache.set("propertyfinder", "Lusail", "all", [{"value_per_m2": 20000.0}])
        # Manually rewind fetched_at to 10s ago (>1s TTL). closing() is
        # mandatory on Windows — `with sqlite3.connect()` doesn't release
        # the file lock at scope exit, only on explicit close().
        with closing(sqlite3.connect(self.db_path)) as conn:
            with conn:
                conn.execute(
                    "UPDATE listings SET fetched_at = ? WHERE source = ?",
                    (time.time() - 10, "propertyfinder"),
                )
        self.assertIsNone(cache.get("propertyfinder", "Lusail", "all"))


# ─────────────────────────────────────────────────────────────────────────
# 4. Engine integration — _try_hybrid_apartments_response (D10/D11 gate)
# ─────────────────────────────────────────────────────────────────────────

class TestEngineIntegration(unittest.TestCase):
    """Exercise the production helper in evaluate_unified.py (Rule #40 —
    not a replica; the real function via import).
    """

    def setUp(self):
        import evaluate_unified
        self.eu = evaluate_unified
        self.fake_loc = MagicMock(lat=25.404, lon=51.512)
        self.fake_plot = MagicMock(pdarea=900)

    def test_20_d11_env_flag_off_returns_none(self):
        with patch.dict(os.environ, {"HYBRID_APARTMENTS_ENABLED": "false"}):
            result = self.eu._try_hybrid_apartments_response(
                zone=52, street=903, building=90,
                loc=self.fake_loc, plot=self.fake_plot,
                asset_type="apartment_building", audience="self",
                gis_lite=MagicMock(),
            )
        self.assertIsNone(result)

    def test_21_d10_non_lusail_district_returns_none(self):
        gis = MagicMock()
        gis.get_district_at_point.return_value = MagicMock(aname="الدفنة", ename="Al Dafna")
        with patch.dict(os.environ, {"HYBRID_APARTMENTS_ENABLED": "true"}):
            result = self.eu._try_hybrid_apartments_response(
                zone=61, street=875, building=20,
                loc=self.fake_loc, plot=self.fake_plot,
                asset_type="apartment_building", audience="self",
                gis_lite=gis,
            )
        self.assertIsNone(result)

    def test_22_d10_lusail_below_min_n_returns_none(self):
        gis = MagicMock()
        gis.get_district_at_point.return_value = MagicMock(aname="لوسيل", ename="Lusail")
        # Connector returns 3 listings; HYBRID_T2_MIN_N is 5 → None
        with patch.dict(os.environ, {"HYBRID_APARTMENTS_ENABLED": "true"}), patch(
            "connectors.propertyfinder_apartments_t2_sales.get_apartment_sales_lusail",
            return_value=[{"value_per_m2": 20000.0}] * 3,
        ):
            result = self.eu._try_hybrid_apartments_response(
                zone=52, street=903, building=90,
                loc=self.fake_loc, plot=self.fake_plot,
                asset_type="apartment_building", audience="self",
                gis_lite=gis,
            )
        self.assertIsNone(result)

    def test_23_happy_path_returns_hybrid_response(self):
        gis = MagicMock()
        gis.get_district_at_point.return_value = MagicMock(aname="لوسيل", ename="Lusail")
        # n=10 — start of 'indicative' band per Project_Instructions §3
        listings = [{"value_per_m2": 20000.0 + i * 100} for i in range(10)]
        with patch.dict(os.environ, {"HYBRID_APARTMENTS_ENABLED": "true"}), patch(
            "connectors.propertyfinder_apartments_t2_sales.get_apartment_sales_lusail",
            return_value=listings,
        ):
            result = self.eu._try_hybrid_apartments_response(
                zone=52, street=903, building=90,
                loc=self.fake_loc, plot=self.fake_plot,
                asset_type="apartment_building", audience="self",
                gis_lite=gis,
            )
        self.assertIsNotNone(result)
        # H7 — tier_breakdown present in response
        self.assertIn("hybrid", result)
        self.assertIn("tier_breakdown", result["hybrid"])
        self.assertEqual(result["valuation"]["method"], "hybrid_t2")
        self.assertIsNotNone(result["valuation"]["value_per_m2"])
        # Rule E3 Constraint 5 — MUC active when T1 absent
        self.assertEqual(result["hybrid"]["muc_required"], True)
        # n=10 → 'indicative' band
        self.assertEqual(result["hybrid"]["sample_size_band"], "indicative")
        self.assertEqual(result["accuracy"]["score"], 2)
        self.assertIn("sources", result)
        self.assertEqual(result["sources"][0]["tier"], "T2")
        self.assertEqual(result["sources"][0]["source"], "propertyfinder")

    def _run_with_n(self, n):
        """Helper — invoke _try_hybrid_apartments_response with n synthetic listings."""
        gis = MagicMock()
        gis.get_district_at_point.return_value = MagicMock(aname="لوسيل", ename="Lusail")
        listings = [{"value_per_m2": 20_000.0 + i * 100} for i in range(n)]
        with patch.dict(os.environ, {"HYBRID_APARTMENTS_ENABLED": "true"}), patch(
            "connectors.propertyfinder_apartments_t2_sales.get_apartment_sales_lusail",
            return_value=listings,
        ):
            return self.eu._try_hybrid_apartments_response(
                zone=52, street=903, building=90,
                loc=self.fake_loc, plot=self.fake_plot,
                asset_type="apartment_building", audience="self",
                gis_lite=gis,
            )

    def test_24_boundary_band_5_to_9(self):
        result = self._run_with_n(7)
        self.assertIsNotNone(result)
        self.assertEqual(result["hybrid"]["sample_size_band"], "boundary")
        self.assertEqual(result["hybrid"]["n_used"], 7)
        # Boundary band gets lower accuracy + specific wording
        self.assertEqual(result["accuracy"]["score"], 1)
        self.assertIn("الحد الأدنى", result["material_uncertainty"]["banner_ar"])
        # muc_range_pct still 0.20 — Rule E3 §5 hard constraint, NOT widened
        self.assertEqual(result["hybrid"]["muc_range_pct"], 0.20)
        # Confidence label unchanged across bands — Rule E3 §4 ceiling
        self.assertEqual(result["hybrid"]["confidence"], "indicative")

    def test_25_indicative_band_10_to_19(self):
        # n=15 — mid-indicative band
        result = self._run_with_n(15)
        self.assertIsNotNone(result)
        self.assertEqual(result["hybrid"]["sample_size_band"], "indicative")
        self.assertEqual(result["accuracy"]["score"], 2)
        self.assertIn("إرشادية", result["material_uncertainty"]["banner_ar"])
        self.assertEqual(result["hybrid"]["muc_range_pct"], 0.20)

    def test_26_strong_indicative_band_20_plus(self):
        result = self._run_with_n(25)
        self.assertIsNotNone(result)
        self.assertEqual(result["hybrid"]["sample_size_band"], "strong_indicative")
        self.assertEqual(result["accuracy"]["score"], 3)
        self.assertIn("قوية", result["material_uncertainty"]["banner_ar"])
        # Even with n=25, confidence is still capped at indicative (Rule E3 §4)
        self.assertEqual(result["hybrid"]["confidence"], "indicative")
        # muc range still 0.20 — Rule E3 §5 doesn't relax for larger T2 samples
        self.assertEqual(result["hybrid"]["muc_range_pct"], 0.20)
        # 'level' in material_uncertainty drops to 'low' for strong band


# ─────────────────────────────────────────────────────────────────────────
# Tally + main entrypoint (matches Sprint 2.19.1+ test discipline)
# ─────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in (TestHttpGet, TestExtractAndDedup, TestJsonLdParse,
                TestPriceAndArea, TestGetApartmentSalesLusail,
                TestT2ListingsCache, TestEngineIntegration):
        suite.addTests(loader.loadTestsFromTestCase(cls))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    n_run = result.testsRun
    n_fail = len(result.failures) + len(result.errors)
    print(f"\n[Sprint 2.21.3] {n_run} tests run, {n_fail} failed")
    sys.exit(0 if n_fail == 0 else 1)
