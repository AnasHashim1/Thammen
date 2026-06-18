# CHANGELOG v140 — Sprint 2.22.0b.59 «حارس انعكاس النطاق» (range-inversion guard)

> Engine `thammen-sprint2p22p0b59-range-inversion-guard` · SPRINT_TAG `2.22.0b.59` ·
> api-health `3.1.0-sprint2.22.0b.59`. **🟢 BACKEND-ONLY / VALUE-INVARIANT** on all live
> traffic (`api.py` + `index.html` git-confirmed UNTOUCHED; the served range is a proven
> NO-OP on every current case → byte-identical to v230). 🔴 Gate-2 by class (it CAN change a
> displayed range — but only on a hypothetical inverted case that does not occur live).
> Files: `evaluate_unified.py` (+42/−2) + `test_sprint_2_22_0b59.py` (new).

## 1. Why this matters
The b57 audit (§20.86) + §20.50 flagged a "b11 `_cost_reanchor_down` low>high range
inversion" (observed pre-b20 on 54/788/10 + 55/1056/60). A served range where `low > high`
(or `amount` outside `[low, high]`) is a user-facing defect on a financial figure.

## 2. Root cause / recon (Rule #58 — measured wins; the premise was MOSTLY falsified)
- **The named function is DEAD CODE.** `_cost_reanchor_down` is not a function name; its real
  producer `_cost_triangulation` (`:6038`) has **zero call sites** — b20 RETIRED the
  branch-decider (`:4944-4946`: «the b11 `_cost_triangulation` branch-decider call is
  RETIRED … kept as a calculator»). The siblings `_old_stock_reanchor` (b16) are dead too.
  Fixing `:6068-6069` touches **no live path**.
- **The two documented cases are NOT inverted live.** Measured on v230 (browser-UA, #61):
  54/788/10 → cost_led 1.1M [1.1M…3.0M]; 55/1056/60 → cost_led 1.7M [1.7M…2.7M]. b20's
  `_leadership_gate` routes them through the **E25-safe** cost_led path (`low=cost_val<amount=high`).
- **All 8 live range-writing paths audited inversion-safe** (teardown · luxury-new ·
  income_led · cost_led · range_expansion · a9 elasticity). The ONLY theoretical residual:
  the geo_full low-raise (`:5157`) sets `low=cost_floor` without checking it against `high`
  — not observed (V001: cost 3.1M < high 3.8M).

## 3. What this patch does
A pure, idempotent final-pass helper `_clamp_valuation_range(valuation)` enforces
`low = min(low, amount)` and `high = max(high, amount)` → guarantees `low ≤ amount ≤ high`
(hence `low ≤ high`). Called as the FINAL pass over the settled range on **both** attach
points — the main path (`evaluate_thammen`, before scenarios + the report fingerprint) and
the fast/income path (`_build_fast_income_only_response`, before its fingerprint) — so a
range inversion can never reach a user, whichever path set the range (closes the `:5157`
residual + any future path). Acts ONLY when amount/low/high are all present + numeric
(bool excluded — `isinstance(True,int)` is True); refusals (`amount None`) untouched;
swallows errors → never breaks evaluate. **The headline `amount`/`method`/`rule` are never
changed; only `low`/`high` are clamped, and only when they violate the invariant.**

## 4. Verification — empirical
- py_compile OK · isolated `test_sprint_2_22_0b59.py` **23/23** (production helper exercised
  per E14/#40: no-op on valid · fix low>amount · fix high<amount · full-inversion → valid ·
  27-cell adversarial grid invariant · refusal/None/bool/non-dict safe · idempotent · only
  low/high touched · wiring on both attach points before the fingerprint · NO-OP on the 4
  valued fixtures · b11/b16 producers confirmed dead).
- DoD: aggregator `run_sprint_2p22p0a_suite.py` **395/395 MATCH** · security **15/15** ·
  surface honesty **45/45** · broad walk `run_regression_2p22p0a.py` **118/118 ALL GREEN**
  (117→118, **zero re-points**).
- **R14 N/A by construction** — `index.html` + `api.py` git-confirmed UNCHANGED; the served
  range is a proven NO-OP → renders identically to v230 (the §20.18 backend-only precedent).
- **Before/after (measured live v230, clamp applied to each captured triple → byte-identical):**

  | case | before (amount/low/high) | after (b59) | identical |
  |---|---|---|---|
  | 54/541/6 cost_led | 2.4M / 2.4M / 5.4M | same | ✅ |
  | 56/647/6 geo_full | 3.8M / 3.1M / 3.8M | same | ✅ |
  | 55/296/13 e25 | 2.6M / 2.0M / 2.6M | same | ✅ |
  | 56/565/21 matched | 2.4M / 2.2M / 2.6M | same | ✅ |
  | 52/903/90 refusal | None | untouched | ✅ |
  | 54/788/10 documented | 1.1M / 1.1M / 3.0M | same | ✅ |
  | 55/1056/60 documented | 1.7M / 1.7M / 2.7M | same | ✅ |

- **Persona review (PO directive — lawyer + linguist):** lawyer **APPROVE** (touches no
  disclaimer/honesty/CC-BY/consent; REDUCES exposure — an inverted range is a misleading
  defect; degenerate `low=high=amount` is safe + still under «ليس تقييماً معتمداً»; refusal
  preserved). linguist **APPROVE** (zero user-facing Arabic added/changed; only code
  comments; terminology «تقييم سوقيّ آليّ / النطاق التقديريّ / الوسيط» intact).

## 5. Deployment (HELD for the Gate-1 «go»)
```
git add "deploy v2/evaluate_unified.py" "deploy v2/test_sprint_2_22_0b59.py" "deploy v2/CHANGELOG_v140.md"
git commit -m "Sprint 2.22.0b.59: range-inversion guard — enforce low<=amount<=high (value-invariant)"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 6. Verification curl (post-deploy, browser-UA #61)
Confirm `/api/health` = b59, then re-probe the 5 fixtures + 54/788/10 + 55/1056/60 → values
byte-identical to v230, each satisfying `low ≤ amount ≤ high`.

## 7. What's NOT in this patch
- No deletion of the dead `_cost_triangulation`/`_old_stock_reanchor` functions (their b11/b13
  tests reference them → deletion is a test-touching refactor, deferred; harmless as-is).
- No `index.html`/`api.py` change; no new GIS; no copy/terminology change.
- The headline value/method/rule logic is untouched — this is a presentation-range invariant only.
