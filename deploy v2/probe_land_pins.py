"""
probe_land_pins.py — Sprint 2.21.0 pre-Sprint audit (items 1-3, 5).

Given known LAND PINs, exercises the REAL production path (Rule #40):
  qatar_gis.QatarGIS.get_plot(pin)  -> CadastrePlots polygon/PDAREA/PD_NO
  get_district_at_point(centroid)   -> area name (Districts)
  classify_asset(plot)              -> asset_type

and reports whether each PIN would be classified as land/raw_land (so the
Sprint 2.20 Land Grid triggers) or mis-classified (e.g. STANDALONE_VILLA),
which would mean the classifier needs a fix BEFORE PIN input is wired
(audit item 4).

⚠️ Run on HEROKU (GIS is unreachable from the Claude container):
    heroku run python probe_land_pins.py 51500109 61050014 ...
Locally it will fail to reach GIS — that's expected.
"""
import sys


def main(pins):
    import qatar_gis as qg
    gis = qg.QatarGIS(verbose=False)
    print("=" * 70)
    print(f"Sprint 2.21.0 land-PIN audit — {len(pins)} PIN(s)")
    print("grid triggers only when asset_type ∈ {land, raw_land}")
    print("=" * 70)
    land_ok = 0
    for pin in pins:
        try:
            plot = gis.get_plot(pin)
        except Exception as e:
            print(f"  PIN {pin}: get_plot ERROR {type(e).__name__}: {str(e)[:90]}")
            continue
        if not plot:
            print(f"  PIN {pin}: NOT FOUND in CadastrePlots")
            continue
        ring = plot.polygon_4326 or []
        area_name = None
        if ring:
            cx = sum(p[0] for p in ring) / len(ring)
            cy = sum(p[1] for p in ring) / len(ring)
            try:
                d = gis.get_district_at_point(cx, cy)
                area_name = getattr(d, 'aname', None) if d else None
            except Exception:
                area_name = None
        try:
            cls = qg.classify_asset(plot, location_metadata=None)
            at = cls.asset_type.value if hasattr(cls.asset_type, 'value') else str(cls.asset_type)
            conf = cls.confidence
        except Exception as e:
            at, conf = f'CLASSIFY_ERROR:{str(e)[:60]}', '-'
        triggers = at in ('land', 'raw_land')
        land_ok += 1 if triggers else 0
        print(f"  PIN {pin}: PDAREA={plot.pdarea:,.0f} PD_NO={plot.pd_no} "
              f"area={area_name} -> asset_type={at} ({conf}) "
              f"| grid_triggers={'YES' if triggers else 'NO'}")
    print("-" * 70)
    print(f"land/raw_land (grid would trigger): {land_ok}/{len(pins)}")
    if land_ok < len(pins):
        print("VERDICT: classifier does NOT emit land for all parcels — "
              "classifier fix REQUIRED before PIN input wiring (audit item 4).")
    else:
        print("VERDICT: classifier emits land for all — PIN input can proceed.")
    print("=" * 70)
    return 0


if __name__ == '__main__':
    args = [a.strip() for a in sys.argv[1:] if a.strip()]
    if not args:
        print("usage: python probe_land_pins.py <PIN> [<PIN> ...]")
        sys.exit(2)
    sys.exit(main(args))
