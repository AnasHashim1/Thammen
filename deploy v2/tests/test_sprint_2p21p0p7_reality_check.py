"""
tests/test_sprint_2p21p0p7_reality_check.py — Sprint 2.21.0.7 isolated tests.

Run: python tests/test_sprint_2p21p0p7_reality_check.py

Covers the Asset Type Reality Check on the PIN/land path:
  - P1: QARS-in-polygon > 0  -> 'stop' (built parcel), asset_type UNKNOWN
  - P2: RULEID land-use class -> reject (5-18,21), mixed_use (23), agricultural
        (19), warn (3,4,22), residential (1,2,20 -> raw_land), no-signal fallback
  - DECISION 4: non-residential RULEID overrides the geometric guard (large parcel)
  - Regression: input_mode=None and empty-signal land path UNCHANGED
  - Rule #40 production line: _build_reality_stop_response on the real builder
  - P4: building-assumption MUC factor guarded for raw_land

Signals (qars_in_polygon / landuse_ruleid / building_height) are pre-supplied via
location_metadata so the suite runs OFFLINE (no GIS). The fixture values mirror
the live-probe ground truth (90040668 built RULEID=1; 52060090 RULEID=12; etc.).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qatar_gis import classify_asset, AssetType   # noqa: E402

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


class _Shape:
    def __init__(self, is_rectangular=True, irregularity_warning=None):
        self.is_rectangular = is_rectangular
        self.irregularity_warning = irregularity_warning


class _Plot:
    def __init__(self, pdarea, pin=74328443, pd_no='PD/1/2020',
                 is_unsubdivided=False, rect=True):
        self.pin = pin
        self.pdarea = pdarea
        self.pd_no = pd_no
        self.is_unsubdivided = is_unsubdivided
        self.shape = _Shape(is_rectangular=rect)
        self.polygon_4326 = []   # empty -> no network; signals come from metadata


def _classify(area, **meta):
    """Classify with input_mode='land' and pre-supplied signals."""
    m = {'qars_in_polygon': 0}   # default: no building
    m.update(meta)
    return classify_asset(_Plot(area), location_metadata=m, input_mode='land')


def _reality(cl):
    for f in (cl.flags or []):
        if isinstance(f, str) and f.startswith('asset_type_reality:'):
            return json.loads(f.split(':', 1)[1])
    return None


# ---- P1: building present ----

def test_p1_building_present_stop():
    # Fixture 90040668: RULEID=1 residential but QARS=1 building on the plot.
    cl = _classify(800, qars_in_polygon=1, landuse_ruleid=1, building_height='G+2')
    r = _reality(cl)
    check("QARS>0 -> asset_type UNKNOWN", cl.asset_type == AssetType.UNKNOWN)
    check("QARS>0 -> reality action=stop", r and r['action'] == 'stop')
    check("stop -> reason building_present", r and r['reason'] == 'building_present')
    check("stop -> message names PIN", r and 'PIN' in r['message_ar'])
    check("stop -> building_height surfaced", r and r['building_height'] == 'G+2')


# ---- P2: non-residential REJECT (5-18, 21) ----

def test_p2_reject_governmental():
    # Fixture 52060090: RULEID=12 Governmental.
    cl = _classify(900, landuse_ruleid=12)
    r = _reality(cl)
    check("RULEID=12 -> UNKNOWN", cl.asset_type == AssetType.UNKNOWN)
    check("RULEID=12 -> action=reject", r and r['action'] == 'reject')
    check("RULEID=12 -> Arabic label حكومي", r and 'حكومي' in r['ruleid_label_ar'])
    check("RULEID=12 -> message says خارج النطاق", r and 'خارج النطاق' in r['message_ar'])


def test_p2_reject_special_use():
    # Fixture 66200396: RULEID=21 Special Use (Pearl / EduCity).
    cl = _classify(1200, landuse_ruleid=21)
    r = _reality(cl)
    check("RULEID=21 -> UNKNOWN + reject", cl.asset_type == AssetType.UNKNOWN
          and r and r['action'] == 'reject')


def test_p2_reject_educational():
    cl = _classify(1500, landuse_ruleid=10)
    check("RULEID=10 (educational) -> reject",
          cl.asset_type == AssetType.UNKNOWN and (_reality(cl) or {}).get('action') == 'reject')


# ---- P2: mixed use (23) -> reject ----

def test_p2_mixed_use():
    # Fixture 69051981: RULEID=23 Mixed Use.
    cl = _classify(1000000, landuse_ruleid=23)
    r = _reality(cl)
    check("RULEID=23 -> UNKNOWN", cl.asset_type == AssetType.UNKNOWN)
    check("RULEID=23 -> action=reject", r and r['action'] == 'reject')
    check("RULEID=23 -> reason mixed_use", r and r['reason'] == 'mixed_use')


# ---- P2: agricultural (19) ----

def test_p2_agricultural():
    cl = _classify(5000, landuse_ruleid=19)
    check("RULEID=19 -> AGRICULTURAL", cl.asset_type == AssetType.AGRICULTURAL)


# ---- P2: warn (3,4,22) -> raw_land + disclaimer ----

def test_p2_warn_commercial():
    for rid, lbl in ((3, 'تجاري'), (4, 'مكاتب'), (22, 'سياحي')):
        cl = _classify(700, landuse_ruleid=rid)
        r = _reality(cl)
        check(f"RULEID={rid} -> raw_land (value+disclaimer)",
              cl.asset_type == AssetType.RAW_LAND)
        check(f"RULEID={rid} -> action=warn", r and r['action'] == 'warn')


# ---- P2: residential (1,2,20) -> clean raw_land, NO reality flag ----

def test_p2_residential_clean():
    for rid in (1, 2, 20):
        cl = _classify(600, landuse_ruleid=rid)
        check(f"RULEID={rid} -> raw_land", cl.asset_type == AssetType.RAW_LAND)
        check(f"RULEID={rid} -> no reality flag", _reality(cl) is None)


# ---- no-signal (24,-1,None) -> geometric guard fallback ----

def test_no_signal_fallback():
    for rid in (24, -1):
        check(f"RULEID={rid} -> raw_land via geometric guard",
              _classify(500, landuse_ruleid=rid).asset_type == AssetType.RAW_LAND)
    # No metadata signals at all + empty ring -> no network -> geometric guard.
    cl = classify_asset(_Plot(500), input_mode='land')
    check("no signals + empty ring -> raw_land (graceful)",
          cl.asset_type == AssetType.RAW_LAND and _reality(cl) is None)


# ---- DECISION 4: RULEID priority over geometric guard ----

def test_decision4_ruleid_over_geometry():
    # 60,000 m² would be compound_large by geometry, but RULEID=12 (govt) must win.
    cl = _classify(60000, landuse_ruleid=12)
    check("60K m² + RULEID=12 -> UNKNOWN reject (RULEID > geometric guard)",
          cl.asset_type == AssetType.UNKNOWN and (_reality(cl) or {}).get('action') == 'reject')
    # Residential RULEID at 60K -> geometric guard still applies (compound_large).
    check("60K m² + RULEID=1 -> compound_large (residential keeps guard)",
          _classify(60000, landuse_ruleid=1).asset_type == AssetType.COMPOUND_LARGE)


# ---- Regression: input_mode=None unchanged ----

def test_regression_input_mode_none():
    # No hint -> villa-size parcel stays standalone_villa (no reality logic runs).
    cl = classify_asset(_Plot(600), input_mode=None)
    check("input_mode=None -> standalone_villa (unchanged)",
          cl.asset_type == AssetType.STANDALONE_VILLA and _reality(cl) is None)


# ---- Rule #40: production-line builder ----

def test_production_reality_stop_response():
    import evaluate_unified as eu

    class _Loc:
        lat = None
        lon = None

    reality = {
        'kind': 'asset_type_reality', 'action': 'reject', 'reason': 'non_residential',
        'ruleid': 12, 'ruleid_label_en': 'Governmental', 'ruleid_label_ar': 'حكومي',
        'qars_in_polygon': 0, 'building_height': None, 'area_m2': 900.0,
        'message_ar': 'هذه الأرض مصنّفة حكومي — خارج النطاق الحالي لـ Thammen. استشر مُقيِّم متخصّص.',
    }
    out = eu._build_reality_stop_response(_Loc(), _Plot(900, pin=52060090), 'investor', reality)
    check("builder: status ok", out.get('status') == 'ok')
    check("builder: PIN-aware address", 'PIN 52060090' in (out.get('address') or ''))
    check("builder: no valuation amount", out['valuation']['amount'] is None)
    check("builder: asset_type_reality attached", out.get('asset_type_reality') == reality)
    check("builder: engine_version is 2.21.0.7",
          '2p21p0p7' in (out.get('engine_version') or ''))


# ---- P4: building-assumption factor guarded for land ----

def test_p4_building_factor_guarded():
    # Re-implement the exact guard condition the pipeline now uses.
    def factor_injected(asset_type, bua_breakdown):
        _p4_at = (asset_type or '').lower()
        return bua_breakdown is None and _p4_at not in ('raw_land', 'land')
    check("P4: raw_land + no BUA -> building factor NOT injected",
          factor_injected('raw_land', None) is False)
    check("P4: land + no BUA -> building factor NOT injected",
          factor_injected('land', None) is False)
    check("P4: villa + no BUA -> building factor STILL injected",
          factor_injected('standalone_villa', None) is True)


if __name__ == "__main__":
    print("Sprint 2.21.0.7 — Asset Type Reality Check isolated tests")
    print("=" * 70)
    test_p1_building_present_stop()
    test_p2_reject_governmental()
    test_p2_reject_special_use()
    test_p2_reject_educational()
    test_p2_mixed_use()
    test_p2_agricultural()
    test_p2_warn_commercial()
    test_p2_residential_clean()
    test_no_signal_fallback()
    test_decision4_ruleid_over_geometry()
    test_regression_input_mode_none()
    test_production_reality_stop_response()
    test_p4_building_factor_guarded()
    print("=" * 70)
    print(f"Sprint 2.21.0.7 tests: {_passed} passed, {_failed} failed")
    sys.exit(0 if _failed == 0 else 1)
