"""
run_regression_2p22p0a_1.py — Sprint 2.22.0a/1 regression runner

Runs all standalone test files in deploy v2/ + deploy v2/tests/, aggregates
exit codes, reports pass/fail summary. Per CLAUDE.md regression discipline:
  - 29 standalone files = 81 tests baseline (Phase 1 audit, Sprint 2.21.4)
  - PYTHONIOENCODING=utf-8 required for Sprint 2.21.2+ tests
  - Skip test_v2_modules.py (pytest-blocked per Phase 1 audit log)

Usage:
    cd "C:\\Thammen\\deploy v2"
    python 2p22p0_pre/run_regression_2p22p0a_1.py
"""
import os
import subprocess
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Walk deploy v2/ root + deploy v2/tests/ for test files. Exclude worktrees.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEST_FILES = []

for d in [ROOT, os.path.join(ROOT, "tests")]:
    if not os.path.isdir(d):
        continue
    for fn in sorted(os.listdir(d)):
        if fn.startswith("test_") and fn.endswith(".py"):
            TEST_FILES.append(os.path.join(d, fn))

# Skip the pytest-blocked file per Phase 1 audit log
SKIP_FILES = {"test_v2_modules.py"}
TEST_FILES = [f for f in TEST_FILES if os.path.basename(f) not in SKIP_FILES]

env = os.environ.copy()
env["PYTHONIOENCODING"] = "utf-8"

print(f"=" * 80)
print(f"Sprint 2.22.0a/1 regression — {len(TEST_FILES)} test files")
print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
print(f"=" * 80)

results = []
t0 = time.time()
for i, path in enumerate(TEST_FILES, 1):
    rel = os.path.relpath(path, ROOT).replace("\\", "/")
    t_start = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, path],
            capture_output=True, text=True, timeout=120,
            cwd=ROOT, env=env,
            encoding="utf-8", errors="replace",
        )
        elapsed = time.time() - t_start
        ok = (proc.returncode == 0)
        # Take last 2 lines of stdout as summary hint
        last_lines = (proc.stdout or "").strip().split("\n")[-2:]
        summary = " | ".join(line.strip() for line in last_lines if line.strip())
        results.append({
            "file": rel, "ok": ok, "rc": proc.returncode,
            "elapsed_s": elapsed, "summary": summary[:200],
            "stderr_tail": (proc.stderr or "").strip().split("\n")[-3:] if proc.stderr else [],
        })
        status_str = "OK " if ok else "FAIL"
        print(f"  [{i:2d}/{len(TEST_FILES)}] {status_str} ({elapsed:5.1f}s) {rel}")
        if not ok:
            print(f"          rc={proc.returncode}")
            for line in results[-1]["stderr_tail"]:
                print(f"          stderr: {line[:160]}")
    except subprocess.TimeoutExpired:
        results.append({"file": rel, "ok": False, "rc": "TIMEOUT", "elapsed_s": 120, "summary": "timeout", "stderr_tail": []})
        print(f"  [{i:2d}/{len(TEST_FILES)}] TIMEOUT ({rel})")
    except Exception as e:
        results.append({"file": rel, "ok": False, "rc": str(e), "elapsed_s": 0, "summary": str(e), "stderr_tail": []})
        print(f"  [{i:2d}/{len(TEST_FILES)}] ERROR ({rel}): {e}")

wall = time.time() - t0
n_ok = sum(1 for r in results if r["ok"])
n_fail = len(results) - n_ok
print()
print(f"=" * 80)
print(f"REGRESSION SUMMARY")
print(f"=" * 80)
print(f"  Files passed:    {n_ok}/{len(results)}")
print(f"  Files failed:    {n_fail}")
print(f"  Total wall time: {wall:.1f}s")
print()

if n_fail > 0:
    print(f"FAILED FILES:")
    for r in results:
        if not r["ok"]:
            print(f"  - {r['file']} (rc={r['rc']})")
            for line in r["stderr_tail"]:
                print(f"      {line[:160]}")
    sys.exit(1)
else:
    print(f"ALL FILES GREEN — Sprint 2.22.0a/1 regression PASS")
    sys.exit(0)
