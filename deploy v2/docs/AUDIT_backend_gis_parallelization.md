# §5 audit + design — backend GIS-chain parallelization (the ACTUAL-latency latency sprint)

**Status:** 🔎 **AUDIT + DESIGN (the «ابدأ» step). BUILD = a separate Gate-2 / determinism-gated sprint (next session).**
**Context:** b114 removed the compute hotspot (`_parse_date`); b115 covers perceived latency (skeleton). This closes the loop on **actual** latency: the ~7s of serial GIS network per heavy request.
**Discipline:** Rule #51 (audit-driven perf) + the Branch-B/§20.2–20.4 determinism lessons + Rule #60 (measure-gate for lever sequencing).

---

## 1. What's measured (this session, warm + live)
- Warm villa (caches hot): total ~9.5s, of which `urlopen` ~2.7s over **35 network calls** + geo pool (`_run_geo`/`build_reference_geo_v2`) ~1.3s + `build_reference` ~0.9s.
- **The live/cold reality is the ~35 serial network calls** — S4 land 14.3s, villa ~8s live (§20.119 smoke). The warm profile understates it because the per-property GIS is uncached on a real first request.
- **Already parallelized (do NOT redo):** `property_factors.analyze_property` (2.18.0, 5-way `ThreadPoolExecutor`) · `geometric_factors.analyze_geometric_factors` INTERNALLY (Branch-B lever 2, A14/v146 — cold villa 31s→14-16s).

## 2. The dependency graph (from Branch-B §20.2, needs a fresh live re-measure)
Three sequential top-level phases in the villa/land path:
- **A — valuation:** the multi-QARS `get_plot` rounds + `build_reference` → **the central value**. Serial (each QARS round depends on the prior).
- **B — `property_factors`:** ~1.65s, **already parallel**.
- **C — enrichment:** `geometric_factors` (the long pole, ~11 serial calls before lever-2) + `geo_v2` (the comparable pool) + landmarks.

**The crux (Branch-B §20.3):** phase C is largely **independent of A's result** — so C can OVERLAP A. **BUT `geo_v2` FEEDS the central value** (it's the widened/geo comparable pool), so reordering it is **determinism-critical**: its output must be proven **byte-identical** whether it runs before/after/concurrent with the rest.

## 3. The parallelization design (Branch-B "lever 1" revival — H_A-cleared, deferred)
Overlap the **independent** enrichment calls (`geometric_factors` + landmarks — pure display/disclosure factors that do NOT feed the central value) with the **valuation + geo_v2 chain**, via a top-level `ThreadPoolExecutor` in `evaluate_property`/`evaluate_unified`. Expected: cold ~14-16s → ~10-12s (overlap the ~4-9s enrichment behind the valuation).

**Two tiers, by determinism risk:**
- **Tier 1 (safe): overlap `geometric_factors` + landmarks ONLY** (they feed disclosure/upper-range, NOT the central value — Branch-B proved `geometric_factors`'s output is independent of the valuation, the H_A harness). geo_v2 stays where it is. Lower ceiling, near-zero determinism risk.
- **Tier 2 (higher ceiling, higher risk): also overlap `geo_v2`** — but geo_v2 feeds the value → a full H_det byte-identity proof across many properties is mandatory (the §20.4 lesson: a passing anchor set is INSUFFICIENT; must include HBU-positive + multi-QARS + geo-widened + e25 + refusal cases).

## 4. The mandatory gates (before ANY deploy)
1. **Fresh live tracer** — run the existing `audit_a6_latency.py` on the **Heroku dyno** (a probe deploy, Gate-1) to get the exact LIVE per-phase split + confirm the dependency graph on the production network (the warm local profile understates the serial network).
2. **H_det determinism harness** — prove the 5-fixture byte-gate + a broad property set (HBU-positive · multi-QARS · geo-widened · e25 · cost-led · income · land · refusal) are **byte-identical** serial-vs-parallel. The Branch-B `harness_branchB_determinism.py` + `harness_HA_zoning_equiv.py` are the starting point.
3. **Gate-2 sign-off** — overlapping anything on the central-value compute path is methodology-adjacent (HARD GATE 2). Present the H_det proof + the before/after latency table for the PO's signature.
4. **Gate-1 deploy** on green + a post-deploy live latency re-measure (Rule #51 step 3: actual vs predicted).

## 5. Recommendation
Ship **Tier 1** first (overlap `geometric_factors` + landmarks — the safe, H_A-cleared lever), measure the real gain, then decide on Tier 2 (geo_v2 overlap) only if the gain justifies the determinism-proof cost. This mirrors Rule #60 (ship the proven lower-risk lever first, gate the higher-risk one behind a binding measurement) — exactly how A14 was handled.

## 6. Why this is a separate sprint, not this session
It needs: a probe deploy (the live tracer) + a determinism harness across ~8 property classes + a Gate-2 sign-off + a post-deploy re-measure. That is a full audited Gate-2 cycle — not a bolt-on. The «ابدأ» deliverable is THIS audit + design; the build is the next focused session.
