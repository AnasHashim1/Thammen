"""
run_calibration.py
==================

Entry point for the Sprint 2.19 cap-rate calibration.

Usage:
    python run_calibration.py                # full crawl, write cap_rates.sqlite
    python run_calibration.py --quick        # shallow crawl (smoke / CI)

Persistence model (Operational_Rules #43 + Sprint 2.19 decision):
    Heroku's filesystem is ephemeral, so a DB written by a one-off dyno is NOT
    seen by the web dyno and is wiped on restart. Therefore cap_rates.sqlite is
    a COMMITTED, read-only snapshot — exactly like building_age_cache.sqlite.
    Refresh = run this script (locally or `heroku run`), then commit + deploy.

    Idempotent: rebuilds the cap_rates table from scratch on every run, so
    re-running never accumulates stale rows.

Logs a JSON summary to stdout (last line) so a future scheduler / CI step can
parse pass/fail. Exit code 0 on success, 1 if zero usable cells were produced.
"""

import argparse
import json
import sys

import cap_rate_calibrator as cal


def main(argv=None):
    parser = argparse.ArgumentParser(description="Thammen cap-rate calibration")
    parser.add_argument("--quick", action="store_true",
                        help="shallow crawl for smoke/CI (fewer pages)")
    parser.add_argument("--db", default=cal.DB_PATH, help="output sqlite path")
    args = parser.parse_args(argv)

    if args.quick:
        target_n, max_pages, delay = 80, 4, 1.0
    else:
        target_n, max_pages, delay = 600, 24, 2.0

    print(f"[run_calibration] starting (quick={args.quick}, db={args.db})")
    summary = cal.calibrate(
        db_path=args.db,
        target_n_per_cat=target_n,
        max_pages=max_pages,
        delay_sec=delay,
    )
    # Final machine-parseable line.
    print("CALIBRATION_SUMMARY " + json.dumps(summary, ensure_ascii=False))

    usable = summary.get("reliable", 0) + summary.get("indicative", 0)
    if usable == 0:
        print("[run_calibration] WARNING: no reliable/indicative cells produced",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
