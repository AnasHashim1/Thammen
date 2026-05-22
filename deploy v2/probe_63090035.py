"""probe_63090035.py — capture the full traceback for the PIN 63090035 crash
(Sprint 2.21.0.7 smoke FAIL: TypeError "'<' not supported between int and str").
Determines whether the fault is in the new land-branch code or downstream.
Run on Heroku: heroku run python probe_63090035.py
"""
import traceback


def main():
    import evaluate_unified as eu
    print("ENGINE:", eu.ENGINE_VERSION)
    try:
        out = eu.evaluate_thammen(pin="63090035", input_mode="land",
                                  audience="investor")
        print("OK status:", out.get("status"), "asset_type:", out.get("asset_type"))
    except Exception:
        traceback.print_exc()

    # Also isolate the classifier step alone (is the crash in classify_asset?).
    print("-" * 60)
    try:
        from qatar_gis import QatarGIS, classify_asset
        g = QatarGIS(verbose=False)
        plot = g.get_plot("63090035")
        print("plot:", None if not plot else f"pin={plot.pin} area={plot.pdarea} pd_no={plot.pd_no} ring_pts={len(plot.polygon_4326 or [])}")
        if plot:
            cl = classify_asset(plot, input_mode="land")
            print("classify OK ->", cl.asset_type, "| flags:", cl.flags)
    except Exception:
        traceback.print_exc()
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
