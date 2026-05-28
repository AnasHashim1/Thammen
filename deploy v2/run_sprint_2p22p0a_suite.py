"""
run_sprint_2p22p0a_suite.py — Sprint 2.22.0a isolated test suite aggregator
+ coverage gate.

Subprocess-invokes the 6 Sprint 2.22.0a isolated test files, parses each
file's `"PASSED: X/Y"` summary line, aggregates per-file counts, and
verifies the total matches the pinned `EXPECTED_TOTAL = 374` constant.

  - Preserves per-sub-sprint provenance (each test file untouched)
  - Coverage gate: any future Sprint that adds/removes assertions MUST
    update PER_FILE_EXPECTED + EXPECTED_TOTAL — fail-loud (Mitigation C)
  - Wall-time budget guard: total ≤ 30s expected (was ~13s aggregate)
  - Exit code: 0 if ALL counts match expected; 1 otherwise

Usage:
    cd "C:\\Thammen\\deploy v2"
    python run_sprint_2p22p0a_suite.py

Sibling to the broader `2p22p0_pre/run_regression_2p22p0a.py` master
runner (which walks ALL test_*.py files for full-engine regression).
This aggregator is Sprint-specific — it verifies the 374-assertion
invariant for the 6 /2-/8 isolated test files only.

Future Sprints (2.22.0b, 2.22.y) MUST update these constants when
adding/removing assertions. See 2p22p0_pre/TESTS_MANIFEST.md for the
contract.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import time


# ──────────────────────────────────────────────────────────────────────
# Pinned coverage gate per Anas Mitigation C (Sprint 2.22.0a/10)
# ──────────────────────────────────────────────────────────────────────
# Sprint 2.22.0a/11 — A2 documentation guard adds 12 assertions:
# 374 → 386.
# Sprint 2.22.0a.3 — catching up pre-existing drift: Sprint 2.22.0a.2
# Pattern B (commit 3328926, "classifier_failure refusal trigger") added
# 6 assertions to test_sprint_2p22p0a_refusal_reason.py (109 → 115) but
# did not bump the gate. 386 → 392.
EXPECTED_TOTAL = 392  # /2:32 + /3:43 + /4:64 + /5:115 + /7:64 + /8:62 + /11:12

PER_FILE_EXPECTED = {
    'test_sprint_2p22p0a_tier_labels.py':              32,   # /2
    'test_sprint_2p22p0a_tier_breakdown.py':           43,   # /3
    'test_sprint_2p22p0a_use_case_banner.py':          64,   # /4
    # Sprint 2.22.0a.3: caught up to actual count (was 109; +6 from
    # 2.22.0a.2 Pattern B, classifier_failure 7th template).
    'test_sprint_2p22p0a_refusal_reason.py':          115,   # /5
    'test_sprint_2p22p0a_verification_url.py':         64,   # /7
    'test_sprint_2p22p0a_calc_visual_and_ledger.py':   62,   # /8
    'test_sprint_2p22p0a_a2_documentation.py':         12,   # /11
}

WALL_TIME_BUDGET_S = 30.0


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────
PASSED_LINE_RE = re.compile(r'^\s*PASSED:\s*(\d+)\s*/\s*(\d+)\s*$', re.MULTILINE)


def parse_passed(stdout: str) -> tuple[int, int]:
    """Return (passed, total) from a test file's `PASSED: X/Y` summary line.

    Falls back to (-1, -1) if the line is absent (parse failure → coverage
    gate fails loud).
    """
    m = PASSED_LINE_RE.search(stdout or '')
    if not m:
        return (-1, -1)
    return int(m.group(1)), int(m.group(2))


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    root = os.path.dirname(os.path.abspath(__file__))
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'

    print('=' * 78)
    print(f'Sprint 2.22.0a isolated test suite aggregator')
    print(f'EXPECTED_TOTAL = {EXPECTED_TOTAL}  ({len(PER_FILE_EXPECTED)} files)')
    print(f'Started: {time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())}')
    print('=' * 78)

    results = []
    t0 = time.time()
    rc = 0

    for fname, expected_n in PER_FILE_EXPECTED.items():
        path = os.path.join(root, fname)
        if not os.path.isfile(path):
            print(f'  MISSING  {fname}  (expected {expected_n} assertions)')
            results.append((fname, expected_n, 0, 0, 0.0, 'missing'))
            rc = 1
            continue

        t_start = time.time()
        try:
            proc = subprocess.run(
                [sys.executable, path],
                capture_output=True, text=True, timeout=120,
                cwd=root, env=env,
                encoding='utf-8', errors='replace',
            )
        except subprocess.TimeoutExpired:
            print(f'  TIMEOUT  {fname}')
            results.append((fname, expected_n, 0, 0, 120.0, 'timeout'))
            rc = 1
            continue

        elapsed = time.time() - t_start
        passed, total = parse_passed(proc.stdout or '')

        verdict_parts = []
        if proc.returncode != 0:
            verdict_parts.append(f'rc={proc.returncode}')
            rc = 1
        if passed != expected_n:
            verdict_parts.append(f'expected {expected_n}, got {passed}')
            rc = 1
        if total != passed:
            verdict_parts.append(f'PASS≠TOTAL ({passed}/{total})')
            rc = 1

        status = 'OK ' if not verdict_parts else 'FAIL'
        verdict = '; '.join(verdict_parts) or 'matches expected'
        print(f'  [{status}] ({elapsed:5.2f}s) {fname}: '
              f'PASSED {passed}/{total} (expected {expected_n}) — {verdict}')

        results.append((fname, expected_n, passed, total, elapsed, verdict))

    wall = time.time() - t0
    actual_total = sum(r[2] for r in results)

    print()
    print('=' * 78)
    print('SUITE SUMMARY')
    print('=' * 78)
    print(f'  Files:                  {len(results)}/{len(PER_FILE_EXPECTED)}')
    print(f'  Assertions total:       {actual_total}/{EXPECTED_TOTAL} '
          f'({"MATCH" if actual_total == EXPECTED_TOTAL else "MISMATCH"})')
    print(f'  Wall time:              {wall:.2f}s '
          f'(budget {WALL_TIME_BUDGET_S}s — '
          f'{"WITHIN" if wall <= WALL_TIME_BUDGET_S else "EXCEEDED"})')
    print('=' * 78)

    if actual_total != EXPECTED_TOTAL:
        print()
        print('COVERAGE GATE FAILED:')
        print(f'  Expected {EXPECTED_TOTAL} assertions, observed {actual_total}.')
        print(f'  Per-file detail:')
        for fname, expected_n, passed, total, _, verdict in results:
            mark = '✓' if passed == expected_n else '✗'
            print(f'    {mark} {fname}: expected {expected_n}, got {passed} ({verdict})')
        print()
        print('  If this is INTENTIONAL (Sprint added/removed assertions), update')
        print('  PER_FILE_EXPECTED + EXPECTED_TOTAL in this file. See')
        print('  2p22p0_pre/TESTS_MANIFEST.md for the contract.')
        rc = 1

    if wall > WALL_TIME_BUDGET_S:
        print()
        print(f'WARNING: wall time {wall:.2f}s exceeds budget {WALL_TIME_BUDGET_S}s.')
        # Wall-time budget overage is a WARNING, not a hard failure — long
        # CI runs are still useful. Future Sprints may raise the budget
        # explicitly with documented justification.

    if rc == 0:
        print()
        print(f'ALL COUNTS MATCH — Sprint 2.22.0a coverage gate PASS')
    return rc


if __name__ == '__main__':
    sys.exit(main())
