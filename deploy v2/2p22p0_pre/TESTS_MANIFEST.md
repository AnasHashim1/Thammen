# Sprint 2.22.0a — Isolated Test Suite Manifest

> **Established:** Sprint 2.22.0a/10 (2026-05-27).
> **Owner:** any future Sprint that adds, removes, or restructures
> isolated test files in `deploy v2/test_sprint_2p22p0a_*.py`.

This file documents the canonical contract between the 6 isolated test
files of Sprint 2.22.0a and the two runners that consume them:

- **`run_regression_2p22p0a.py`** (in `2p22p0_pre/`) — the broad-engine
  regression runner that walks ALL `test_*.py` files. Continues to use
  exit-code aggregation only.
- **`run_sprint_2p22p0a_suite.py`** (in `deploy v2/` root) — the
  Sprint-specific suite aggregator. Verifies the **374-assertion total**
  against pinned per-file counts. Fail-loud if drift detected.

-----

## 1. Inventory (Sprint 2.22.0a end-state)

| Sub-sprint | File | Assertions | Helper pattern |
|---|---|---:|---|
| /2  | `test_sprint_2p22p0a_tier_labels.py`            |  **32** | Pattern A (`_check(cond, name, detail)`) — canonical |
| /3  | `test_sprint_2p22p0a_tier_breakdown.py`         |  **43** | Pattern A — canonical |
| /4  | `test_sprint_2p22p0a_use_case_banner.py`        |  **64** | Pattern A — canonical |
| /5  | `test_sprint_2p22p0a_refusal_reason.py`         | **109** | Pattern A — canonical |
| /7  | `test_sprint_2p22p0a_verification_url.py`       |  **64** | Pattern B legacy adapter (Rule #39 deviation — see §8 TD-1) |
| /8  | `test_sprint_2p22p0a_calc_visual_and_ledger.py` |  **62** | Pattern B legacy adapter (Rule #39 deviation — see §8 TD-1) |
| /11 | `test_sprint_2p22p0a_a2_documentation.py`       |  **12** | Pattern A — canonical (regression guard for §4.5 A2 row) |
| | **TOTAL** | **386** | |

(/1 ENGINE_VERSION bump + /6 merged-into-/5 + /9 RICS audit + /10 this
consolidation Sprint emit no new isolated test files. /9 extended
`test_material_uncertainty.py` (unittest-based, separate from this
suite). /11 emits one new isolated test file as a regression guard for
the audit-PIN row data fix.)

-----

## 2. Shared infrastructure

All 6 files import the shared helper module `_test_helpers.py` (Anas
Q1.5 decision: generic name, not Sprint-suffixed, because infrastructure
modules use descriptive purpose names):

```python
from _test_helpers import Reporter, set_stdout_utf8

set_stdout_utf8()
_REPORTER = Reporter()
_check = _REPORTER.check    # Pattern A native: _check(cond, name, detail)
```

Pattern B files (/7 + /8) wrap the canonical Reporter via an adapter:

```python
from _test_helpers import Reporter, set_stdout_utf8

set_stdout_utf8()
_REPORTER = Reporter()

# Pattern B legacy adapter — preserves the 64/62 existing callsites
def check(name, cond):
    _REPORTER.check(cond, name)
```

**Both patterns route through one canonical Reporter instance per
file.** The drift is at callsite signature ONLY (`check(name, cond)` in
/7 + /8 vs `_check(cond, name)` in /2-/5). Internal counting + summary
output are unified. /12 final consistency pass may flip callsites with
proper AST tooling.

### Reporter contract

```python
class Reporter:
    def check(self, condition, name: str, detail: str = '') -> None: ...
    def report(self) -> int:
        """Print 'PASSED: X/Y\\nFAILED: Z/Y' summary block. Return 0 if
        all passed, 1 otherwise. The PASSED line is parsed by
        run_sprint_2p22p0a_suite.py for the coverage gate."""
```

The canonical PASSED-line format is non-negotiable for the aggregator —
any future helper variant MUST preserve this exact regex shape:
`^\s*PASSED:\s*(\d+)\s*/\s*(\d+)\s*$`.

-----

## 3. Coverage gate contract

`run_sprint_2p22p0a_suite.py` pins two constants:

```python
EXPECTED_TOTAL = 374
PER_FILE_EXPECTED = {
    'test_sprint_2p22p0a_tier_labels.py':              32,
    'test_sprint_2p22p0a_tier_breakdown.py':           43,
    'test_sprint_2p22p0a_use_case_banner.py':          64,
    'test_sprint_2p22p0a_refusal_reason.py':          109,
    'test_sprint_2p22p0a_verification_url.py':         64,
    'test_sprint_2p22p0a_calc_visual_and_ledger.py':   62,
}
```

The aggregator subprocess-invokes each file, parses the `PASSED: X/Y`
line, verifies `X == PER_FILE_EXPECTED[file]`, and asserts
`sum(X) == EXPECTED_TOTAL`. Any mismatch → exit code 1.

-----

## 4. How to add a new isolated test file (Sprint 2.22.0b+)

1. **Name**: `test_sprint_<sprint>_<feature>.py` at `deploy v2/` root.
   The full-regression runner (`run_regression_2p22p0a.py`) globs
   `test_*.py` so it'll discover automatically.

2. **Use the shared Reporter** (Pattern A canonical signature):

   ```python
   import sys, os
   sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
   from _test_helpers import Reporter, set_stdout_utf8

   set_stdout_utf8()
   _REPORTER = Reporter()
   _check = _REPORTER.check

   # Tests
   _check(condition, 'human-readable test name')
   _check(condition, 'name', 'detail when failing')

   # Tail
   sys.exit(_REPORTER.report())
   ```

3. **Update the suite aggregator** when adding to Sprint 2.22.0a OR
   creating a new Sprint-specific aggregator for 2.22.0b/0c.

   For Sprint 2.22.0a-family additions, edit
   `run_sprint_2p22p0a_suite.py`:
   - Add entry to `PER_FILE_EXPECTED` with the asserted count.
   - Increment `EXPECTED_TOTAL` by the same delta.

   For new Sprint families (2.22.0b, 2.22.y, etc.), create a sibling
   `run_sprint_<family>_suite.py` with its own `EXPECTED_TOTAL`. The
   `_test_helpers` module stays shared across families (Q1.5 generic
   naming rationale).

4. **Verify coverage gate**:
   ```
   cd "C:\\Thammen\\deploy v2"
   python run_sprint_2p22p0a_suite.py
   ```
   Should print `ALL COUNTS MATCH — Sprint 2.22.0a coverage gate PASS`.

-----

## 5. Mitigation A audit trail (Sprint 2.22.0a/10 sequential discipline)

Per Anas Mitigation A 2026-05-27, each file was refactored + verified
in isolation BEFORE proceeding to the next, allowing bisection if any
regression surfaced. Sequence executed:

| Step | File | Before | After | Status |
|------|---|---:|---:|---|
| 1 | NEW `_test_helpers.py` (smoke test) | — | rc=1 (1/2 by design) | ✅ helper works |
| 2 | /2 tier_labels (Pattern A) | 32/32 | 32/32 | ✅ |
| 3 | /3 tier_breakdown (Pattern A) | 43/43 | 43/43 | ✅ |
| 4 | /4 use_case_banner (Pattern A) | 64/64 | 64/64 | ✅ |
| 5 | /5 refusal_reason (Pattern A) | 109/109 | 109/109 | ✅ |
| 6 | /7 verification_url (Pattern B → adapter) | 64/64 | 64/64 | ✅ |
| 7 | /8 calc_visual_and_ledger (Pattern B → adapter) | 62/62 | 62/62 | ✅ |
| 8 | NEW `run_sprint_2p22p0a_suite.py` (aggregator) | — | 374/374 | ✅ |
| 9 | Full regression (35 files) | 35/35 | 35/35 | ✅ |

-----

## 6. Deviation log

### Rule #39 deviation — Pattern B adapter pattern (instead of full AST reorder)

Per Anas Mitigation A, /10 originally planned to flip 67 + 44 = 111
callsites in /7 and /8 from `check(name, cond)` (Pattern B) to
`_check(cond, name)` (Pattern A canonical signature).

**What was done instead** (Option Z adapter):
- Kept the 111 callsites unchanged at the source level.
- Added a thin file-local `check(name, cond)` adapter in each of /7 and
  /8 that routes through the canonical `_REPORTER.check(cond, name)`.
- The Reporter (counting + summary + exit-code) is unified across all
  6 files. Drift exists only at callsite signature level.

**Why the deviation was necessary** (3 sentences per Rule #39):
1. **Why Y was necessary**: an AST-based one-shot reorder script
   (`2p22p0_pre/_2p22p0a_10_reorder_check_calls.py`, transient) was
   attempted first — it failed on `JoinedStr` (f-string) positions for
   Arabic content in /8 plus an arg-span overlap warning in /7. Manual
   reorder of 111 callsites (60 of which are multi-line) carries high
   typo risk + ~60 round-trips of Edit-tool work.
2. **What's lost by Y**: callsite signature drift remains visible to
   anyone reading /7 or /8 — `check(name, cond)` vs `_check(cond, name)`
   used in /2-/5. The shared Reporter unifies COUNTING + SUMMARY, but
   the readable callsite text differs across files.
3. **What user needs to know**: the consolidation goal (one Reporter
   shared by 6 files, coverage gate via aggregator) is achieved. /12
   final consistency pass can flip the 111 callsites with proper AST
   tooling once Arabic-aware positions are reliable. Until then, both
   patterns produce identical test-counting behavior.

**/12 list status**: Pattern B callsite drift added as item 10 (was 9
after /9 added "RICS citation propagation — 13 sites").

-----

## 7. Future-Sprint adoption signal

If Sprint 2.22.0b/0c/y/x test files import `_test_helpers` AND use the
canonical `_check(cond, name, detail)` signature at all callsites, this
manifest can be retired (the helper module + suite aggregator pattern
becomes self-documenting via code). Until then, this file is the source
of truth for the contract.

-----

## 8. Known technical debt

### TD-1 — Pattern B callsite signature drift in /7 + /8 (Sprint 2.22.0a/10)

**Status:** Documented + deferred (NOT in /12 final consistency pass scope
per Anas 2026-05-27 — /12 stays cosmetic + the 13-site citation
propagation only).

**Files affected:**
- `test_sprint_2p22p0a_verification_url.py` (67 callsites)
- `test_sprint_2p22p0a_calc_visual_and_ledger.py` (44 callsites)
- Total: **111 callsites** use Pattern B `check(name, cond)` via thin
  file-local adapter.

**Canonical convention (Pattern A, established by /2-/5):**
```python
_check(condition, name, detail='')   # _REPORTER.check signature
```

**Current Pattern B adapter in /7 + /8:**
```python
def check(name, cond):
    _REPORTER.check(cond, name)   # arg-swap inside adapter
```

**Behavior impact:** **ZERO** — the adapter routes through the canonical
Reporter. Coverage gate `run_sprint_2p22p0a_suite.py` verifies
374/374 assertions pass through unchanged. The drift is at callsite
signature visibility ONLY.

**Why deferred (the original AST attempt):**
- An AST-driven one-shot reorder script (`2p22p0_pre/_2p22p0a_10_reorder_check_calls.py`,
  transient — removed pre-commit) was attempted first in /10 per Anas
  Mitigation A's explicit "argument-reorder" instruction.
- It failed on **JoinedStr (f-string) positions for Arabic content**
  in /8 + an arg-span overlap warning in /7.
- Python's `ast` module reports correct line/col positions for f-string
  *containers* but the internal positions of Arabic-bearing format
  specifiers are unreliable for surgical string-level reorder.
- Manual reorder of 111 callsites (60 of which are multi-line) carries
  high typo risk + ~60 Edit-tool round-trips with potential
  regression-introduction probability non-trivial.

**Resolution path (when revived):**
1. Build/locate an **Arabic-aware AST refactor utility** that handles
   JoinedStr (f-string) positions reliably across Unicode content.
   Candidate: `libcst` library (concrete syntax tree, preserves
   formatting + handles f-strings robustly). Not currently a project
   dependency.
2. Re-run the reorder transformation: swap args + rename `check` →
   `_check` across the 111 callsites.
3. Verify per-file counts (64/64 + 62/62) preserved.
4. Drop the file-local `check(name, cond)` adapter in /7 + /8.
5. Update this section to mark TD-1 resolved.

**Suggested deferral venues** (any of):
- **Sprint 2.22.y** (validation hardening) — natural fit because
  /7 + /8 are validation-related (verification_url + adjustment_ledger).
  Could pair with the larger validation refactoring.
- **A dedicated tooling Sprint** — adds `libcst` to `requirements.txt`,
  builds a reusable Arabic-aware refactor utility, applies it here
  + future test files.
- **Sprint 2.22.0a.1 / 2.22.0a.2** — single-purpose follow-up Sprint
  after 2.22.0a ships, when there's no production risk.

**Rule reference:** Operational_Rules #39 (deviation justification
protocol) — the 3-sentence justification appears in Sprint 2.22.0a/10's
commit message (`72f5972`).

-----

*Last updated: 2026-05-27 — Sprint 2.22.0a/10 establishment. TD-1 added
2026-05-27 PM as part of Sprint 2.22.0a/11 prep per Anas course-correction.*
