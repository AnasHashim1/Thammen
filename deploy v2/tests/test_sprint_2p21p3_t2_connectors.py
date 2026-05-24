"""
test_sprint_2p21p3_t2_connectors.py — Sprint 2.21.3 isolated tests

Covers (post-2.21.3.1 list-page refactor):
  - PropertyFinder T2 connector (network, ld+json walk, price+area extraction
    from offers[0].priceSpecification, AED skip, sub-Lusail filter, dedup)
  - T2ListingsCache (get/set roundtrip, TTL expiry)
  - Engine integration helper `_try_hybrid_apartments_response` (D10/D11
    gates, sample-size bands, Fox Hills/'غار ثعيلب' acceptance)

Test discipline:
  - Replica + production verification (Rule #40): tests import REAL module
    paths; mocks scoped to urllib boundary + GIS lookup.
  - Cache tests use tmp_path; no production cache pollution.
  - Run from project root with PYTHONIOENCODING=utf-8:
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

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from t2_listings_cache import T2ListingsCache
from connectors.propertyfinder_apartments_t2_sales import (
    _http_get,
    _extract_jsonld_listings,
    _walk_real_estate_listings,
    _price_qar_from_entity,
    _area_m2_from_entity,
    _listing_is_lusail,
    _entity_to_row,
    size_bracket_label,
    get_apartment_sales_lusail,
    LUSAIL_SALE_URL,
)


# ─────────────────────────────────────────────────────────────────────────
# Fixtures matching the REAL PF list-page JSON-LD shape (probe-verified)
# ─────────────────────────────────────────────────────────────────────────

def _real_estate_listing(price, currency, area_m2, url,
                         address_locality="Lusail",
                         address_region="Marina District"):
    """Build a JSON-LD entity in PF's exact list-page shape."""
    return {
        "@id": str(abs(hash(url)) % 10_000_000),
        "@type": ["ApartmentComplex", "RealEstateListing", "House"],
        "address": {
            "@type": "PostalAddress",
            "addressLocality": address_locality,
            "addressRegion": address_region,
        },
        "floorSize": {"@type": "QuantitativeValue", "value": area_m2, "unitText": "sqm"},
        "offers": [{
            "@type": "Offer",
            "priceSpecification": {
                "@type": "UnitPriceSpecification",
                "price": price,
                "priceCurrency": currency,
                "unitText": "sell",
            },
        }],
        "url": url,
    }


def _list_page_html_with(entities):
    """Wrap a list of entities in PF's ItemList JSON-LD container."""
    itemlist = {
        "@context": "https://schema.org/",
        "@type": "ItemList",
        "itemListElement": [
            {"@type": "WebPage", "mainEntity": ent, "position": i + 1}
            for i, ent in enumerate(entities)
        ],
    }
    block = '<script type="application/ld+json">' + json.dumps(itemlist) + "</script>"
    return f"<html><body>some text {block} more text</body></html>"


SAMPLE_LUSAIL_ENTITIES = [
    _real_estate_listing(2_100_000, "QAR", 121, "https://www.propertyfinder.qa/en/plp/buy/apt-1.html"),
    _real_estate_listing(1_240_779, "QAR", 91.56, "https://www.propertyfinder.qa/en/plp/buy/apt-2.html",
                         address_region="Marina District"),
    _real_estate_listing(1_125_000, "QAR", 75, "https://www.propertyfinder.qa/en/plp/buy/apt-3.html",
                         address_region="Al Erkyah City"),
    _real_estate_listing(1_500_000, "QAR", 100, "https://www.propertyfinder.qa/en/plp/buy/apt-4.html",
                         address_region="Fox Hills"),
    _real_estate_listing(1_800_000, "QAR", 115, "https://www.propertyfinder.qa/en/plp/buy/apt-5.html"),
]


def _fake_response(body: str, status: int = 200):
    fake = MagicMock()
    fake.status = status
    fake.read.return_value = body.encode("utf-8")
    fake.__enter__.return_value = fake
    fake.__exit__.return_value = False
    return fake


# ─────────────────────────────────────────────────────────────────────────
# 1. _http_get (D6 contract)
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


# ─────────────────────────────────────────────────────────────────────────
# 2. JSON-LD ItemList walk + extract
# ─────────────────────────────────────────────────────────────────────────

class TestJsonLdWalk(unittest.TestCase):

    def test_04_walk_finds_nested_real_estate_listings(self):
        ent = SAMPLE_LUSAIL_ENTITIES[0]
        wrapper = {"@type": "ItemList", "itemListElement": [{"mainEntity": ent}]}
        found = _walk_real_estate_listings(wrapper)
        self.assertEqual(len(found), 1)
        self.assertIs(found[0], ent)

    def test_05_walk_handles_real_estate_listing_as_list_type(self):
        """PF @type can be a list: ["ApartmentComplex","RealEstateListing","House"]"""
        ent = SAMPLE_LUSAIL_ENTITIES[0]
        self.assertIn("RealEstateListing", ent["@type"])
        found = _walk_real_estate_listings(ent)
        self.assertEqual(found, [ent])

    def test_06_extract_jsonld_listings_parses_multiple(self):
        body = _list_page_html_with(SAMPLE_LUSAIL_ENTITIES)
        listings = _extract_jsonld_listings(body)
        self.assertEqual(len(listings), 5)

    def test_07_extract_jsonld_returns_empty_on_no_block_d7(self):
        self.assertEqual(_extract_jsonld_listings("<html>no script</html>"), [])

    def test_08_extract_jsonld_skips_malformed_block_d7(self):
        body = '<script type="application/ld+json">{not_valid_json}</script>'
        self.assertEqual(_extract_jsonld_listings(body), [])


# ─────────────────────────────────────────────────────────────────────────
# 3. Per-entity price/area extraction — PF list-page shape
# ─────────────────────────────────────────────────────────────────────────

class TestEntityExtract(unittest.TestCase):

    def test_09_price_qar_from_priceSpecification(self):
        ent = SAMPLE_LUSAIL_ENTITIES[0]                # 2.1M QAR
        self.assertEqual(_price_qar_from_entity(ent), 2_100_000)

    def test_10_price_qar_skips_aed_d8(self):
        ent = _real_estate_listing(150_000, "AED", 100, "https://x/p.html")
        self.assertIsNone(_price_qar_from_entity(ent))

    def test_11_price_qar_falls_back_to_offers_direct_price(self):
        """Detail-page shape (legacy fallback) uses offers.price directly."""
        ent = {"offers": {"price": 1_500_000, "priceCurrency": "QAR"}}
        self.assertEqual(_price_qar_from_entity(ent), 1_500_000)

    def test_12_price_qar_rejects_sub_threshold(self):
        ent = _real_estate_listing(50_000, "QAR", 100, "https://x/p.html")
        self.assertIsNone(_price_qar_from_entity(ent))

    def test_13_area_m2_with_unitText_sqm(self):
        ent = SAMPLE_LUSAIL_ENTITIES[1]                # 91.56 sqm
        self.assertAlmostEqual(_area_m2_from_entity(ent), 91.56)

    def test_14_area_m2_rejects_wrong_unit(self):
        ent = {"floorSize": {"value": 1500, "unitText": "sqft"}}
        self.assertIsNone(_area_m2_from_entity(ent))

    def test_15_size_bracket_label_boundaries(self):
        self.assertEqual(size_bracket_label(99.9),  "0-100")
        self.assertEqual(size_bracket_label(100),   "100-150")
        self.assertEqual(size_bracket_label(149.9), "100-150")
        self.assertEqual(size_bracket_label(150),   "150-250")
        self.assertEqual(size_bracket_label(249.9), "150-250")
        self.assertEqual(size_bracket_label(250),   "250+")

    def test_16_listing_is_lusail_filter(self):
        # Lusail by locality
        self.assertTrue(_listing_is_lusail(SAMPLE_LUSAIL_ENTITIES[0]))
        # Fox Hills (Lusail sub-region) by region
        self.assertTrue(_listing_is_lusail(SAMPLE_LUSAIL_ENTITIES[3]))
        # Non-Lusail
        ent_messila = _real_estate_listing(2_000_000, "QAR", 120, "https://x/messila.html",
                                            address_locality="Al Messila",
                                            address_region="Doha")
        self.assertFalse(_listing_is_lusail(ent_messila))

    def test_17_entity_to_row_full_dict_shape(self):
        ent = SAMPLE_LUSAIL_ENTITIES[0]                # 2.1M / 121 sqm
        row = _entity_to_row(ent)
        self.assertIsNotNone(row)
        self.assertEqual(row["source"], "propertyfinder")
        self.assertEqual(row["tier"], "T2")
        self.assertEqual(row["transaction_type"], "sale")
        self.assertEqual(row["raw_price_qar"], 2_100_000)
        self.assertEqual(row["area_m2"], 121)
        self.assertAlmostEqual(row["value_per_m2"], 2_100_000 / 121, places=1)
        self.assertEqual(row["district"], "Lusail")
        self.assertEqual(row["size_bracket"], "100-150")
        self.assertEqual(row["address_region"], "Marina District")


# ─────────────────────────────────────────────────────────────────────────
# 4. End-to-end with mocked HTTP — list-page architecture
# ─────────────────────────────────────────────────────────────────────────

class TestGetApartmentSalesLusail(unittest.TestCase):

    def test_18_happy_path_single_page_with_mocked_http(self):
        body = _list_page_html_with(SAMPLE_LUSAIL_ENTITIES)
        with patch(
            "connectors.propertyfinder_apartments_t2_sales._http_get",
            side_effect=lambda url: body,
        ), patch("time.sleep"):
            result = get_apartment_sales_lusail(use_cache=False)
        # 5 entities × 3 pages = 15 raw, but dedup by URL → 5 unique
        self.assertEqual(len(result), 5)
        for row in result:
            self.assertEqual(row["source"], "propertyfinder")
            self.assertEqual(row["tier"], "T2")
            self.assertEqual(row["district"], "Lusail")

    def test_19_dedup_across_pages_d9(self):
        """If page 2/3 returns same URLs (PF re-renders same listings on
        subsequent pages), dedup keeps unique-by-URL only."""
        body = _list_page_html_with(SAMPLE_LUSAIL_ENTITIES[:3])
        with patch(
            "connectors.propertyfinder_apartments_t2_sales._http_get",
            return_value=body,
        ), patch("time.sleep"):
            result = get_apartment_sales_lusail(use_cache=False)
        self.assertEqual(len(result), 3)             # not 9 (3 pages × 3)

    def test_20_skips_non_lusail_entities(self):
        mixed = SAMPLE_LUSAIL_ENTITIES + [
            _real_estate_listing(2_500_000, "QAR", 130,
                                  "https://www.propertyfinder.qa/en/plp/buy/messila.html",
                                  address_locality="Al Messila",
                                  address_region="Doha"),
        ]
        body = _list_page_html_with(mixed)
        with patch(
            "connectors.propertyfinder_apartments_t2_sales._http_get",
            return_value=body,
        ), patch("time.sleep"):
            result = get_apartment_sales_lusail(use_cache=False)
        self.assertEqual(len(result), 5)             # Messila filtered out

    def test_21_network_all_fail_returns_empty_d6(self):
        with patch(
            "connectors.propertyfinder_apartments_t2_sales._http_get",
            return_value=None,
        ), patch("time.sleep"):
            self.assertEqual(get_apartment_sales_lusail(use_cache=False), [])

    def test_22_size_bracket_filter_keeps_only_matching(self):
        body = _list_page_html_with(SAMPLE_LUSAIL_ENTITIES)
        with patch(
            "connectors.propertyfinder_apartments_t2_sales._http_get",
            return_value=body,
        ), patch("time.sleep"):
            result = get_apartment_sales_lusail(size_bracket=(100, 150),
                                                use_cache=False)
        # Of the 5 fixtures, areas {121, 91.56, 75, 100, 115} → 100<=x<150 keeps 121, 100, 115
        self.assertEqual(len(result), 3)
        for row in result:
            self.assertTrue(100 <= row["area_m2"] < 150)


# ─────────────────────────────────────────────────────────────────────────
# 5. Cache (D4 TTL contract)
# ─────────────────────────────────────────────────────────────────────────

class TestT2ListingsCache(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmpdir.name) / "test_cache.sqlite"

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_23_cache_get_set_roundtrip(self):
        cache = T2ListingsCache(db_path=self.db_path)
        payload = [{"source": "propertyfinder", "value_per_m2": 21000.0}]
        cache.set("propertyfinder", "Lusail", "100-150", payload)
        self.assertEqual(cache.get("propertyfinder", "Lusail", "100-150"), payload)

    def test_24_cache_ttl_expiry_returns_none(self):
        cache = T2ListingsCache(db_path=self.db_path, ttl_seconds=1)
        cache.set("propertyfinder", "Lusail", "all", [{"value_per_m2": 20000.0}])
        with closing(sqlite3.connect(self.db_path)) as conn:
            with conn:
                conn.execute(
                    "UPDATE listings SET fetched_at = ? WHERE source = ?",
                    (time.time() - 10, "propertyfinder"),
                )
        self.assertIsNone(cache.get("propertyfinder", "Lusail", "all"))


# ─────────────────────────────────────────────────────────────────────────
# 6. Engine integration — _try_hybrid_apartments_response (D10/D11 + bands)
# ─────────────────────────────────────────────────────────────────────────

class TestEngineIntegration(unittest.TestCase):

    def setUp(self):
        import evaluate_unified
        self.eu = evaluate_unified
        self.fake_loc = MagicMock(lat=25.404, lon=51.512)
        self.fake_plot = MagicMock(pdarea=900)

    def test_25_d11_env_flag_off_returns_none(self):
        with patch.dict(os.environ, {"HYBRID_APARTMENTS_ENABLED": "false"}):
            result = self.eu._try_hybrid_apartments_response(
                zone=52, street=903, building=90,
                loc=self.fake_loc, plot=self.fake_plot,
                asset_type="apartment_building", audience="self",
                gis_lite=MagicMock(),
            )
        self.assertIsNone(result)

    def test_26_d10_non_lusail_district_returns_none(self):
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

    def test_27_d10_lusail_below_min_n_returns_none(self):
        gis = MagicMock()
        gis.get_district_at_point.return_value = MagicMock(aname="لوسيل", ename="Lusail")
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

    def _run_with_n(self, n, aname="لوسيل", ename="Lusail"):
        gis = MagicMock()
        gis.get_district_at_point.return_value = MagicMock(aname=aname, ename=ename)
        listings = [{"value_per_m2": 20_000.0 + i * 100} for i in range(n)]
        with patch.dict(os.environ, {"HYBRID_APARTMENTS_ENABLED": "true"}), patch(
            "connectors.propertyfinder_apartments_t2_sales.get_apartment_sales_lusail",
            return_value=listings,
        ):
            return self.eu._try_hybrid_apartments_response(
                zone=69, street=329, building=20,
                loc=self.fake_loc, plot=self.fake_plot,
                asset_type="apartment_building", audience="self",
                gis_lite=gis,
            )

    def test_28_happy_path_indicative_band(self):
        result = self._run_with_n(10)
        self.assertIsNotNone(result)
        self.assertIn("hybrid", result)
        self.assertEqual(result["valuation"]["method"], "hybrid_t2")
        self.assertEqual(result["hybrid"]["sample_size_band"], "indicative")
        self.assertEqual(result["accuracy"]["score"], 2)
        self.assertEqual(result["hybrid"]["muc_required"], True)
        self.assertEqual(result["hybrid"]["muc_range_pct"], 0.20)
        self.assertEqual(result["sources"][0]["source"], "propertyfinder")

    def test_29_boundary_band_5_to_9(self):
        result = self._run_with_n(7)
        self.assertEqual(result["hybrid"]["sample_size_band"], "boundary")
        self.assertEqual(result["accuracy"]["score"], 1)
        self.assertIn("الحد الأدنى", result["material_uncertainty"]["banner_ar"])

    def test_30_strong_indicative_band_20_plus(self):
        result = self._run_with_n(25)
        self.assertEqual(result["hybrid"]["sample_size_band"], "strong_indicative")
        self.assertEqual(result["accuracy"]["score"], 3)
        self.assertIn("قوية", result["material_uncertainty"]["banner_ar"])
        # Confidence ceiling still 'indicative' — Rule E3 §4
        self.assertEqual(result["hybrid"]["confidence"], "indicative")
        # MUC range hard-locked at 0.20 — Rule E3 §5
        self.assertEqual(result["hybrid"]["muc_range_pct"], 0.20)

    def test_31_d10_fox_hills_lusail_subdistrict_accepted(self):
        """Reference case PIN 69/329/20: district='غار ثعيلب', Lusail sub-district."""
        result = self._run_with_n(12, aname="غار ثعيلب", ename="Ghar Thuaileb")
        self.assertIsNotNone(result, "Fox Hills must be accepted as Lusail")
        self.assertEqual(result["valuation"]["method"], "hybrid_t2")

    def test_32_d10_lusail_69_aname_accepted(self):
        result = self._run_with_n(8, aname="لوسيل 69", ename="Lusail 69")
        self.assertIsNotNone(result)
        self.assertEqual(result["hybrid"]["sample_size_band"], "boundary")


# ─────────────────────────────────────────────────────────────────────────
# Main entrypoint
# ─────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in (TestHttpGet, TestJsonLdWalk, TestEntityExtract,
                TestGetApartmentSalesLusail, TestT2ListingsCache,
                TestEngineIntegration):
        suite.addTests(loader.loadTestsFromTestCase(cls))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    n_run = result.testsRun
    n_fail = len(result.failures) + len(result.errors)
    print(f"\n[Sprint 2.21.3] {n_run} tests run, {n_fail} failed")
    sys.exit(0 if n_fail == 0 else 1)
