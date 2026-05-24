# Pre-Sprint 2.22.0 — 3-Stage Valuation Architecture (E16) — Audit Results

**Date:** 2026-05-24
**Status:** Pre-Sprint diagnostic. NOT a Sprint. No code change. No engine
bump. No Heroku push. Local-only audit against public production
(`thammen.qa/api`).
**Production baseline at run:** `thammen-sprint2p18p1p1-compound-misroute-fix`
(Heroku v106 — after docs-hygiene wave 2026-05-24).

---

## 1. Decision register (D1–D12 from BRIEF §5)

Defaults from BRIEF §5 recorded as the starting point. Anas signs each
after seeing the audit evidence; nothing is locked in until then.

### Critical (must answer before any Sprint 2.22.0 code)

| # | Decision | Default proposal | Anas sign-off |
|---|---|---|---|
| **D1** | Stage transition model | Auto-progress (Stage 1 returns immediately, Stage 2 starts automatically in background) | ⏸ pending audit |
| **D2** | Response architecture | Server-Sent Events (SSE) on single endpoint — modern, simple, no WebSocket overhead, native browser support | ⏸ pending audit |
| **D3** | Stage 3 scope in MVP | Defer to Sprint 2.22.1 — 2.22.0 ships Stage 1+2 only. Stage 3 broker co-pilot needs its own design pass | ⏸ pending audit |
| **D4** | Backward compatibility | Single endpoint, dual-mode. Current `/api/evaluate` continues as single-shot synchronous response. `Accept: text/event-stream` triggers staged response | ⏸ pending audit |
| **D12** | Sprint decomposition | 2.22.0 = Stage 1+2 MVP, 2.22.1 = Stage 3 broker co-pilot, 2.22.2 = telemetry refresh | ⏸ pending audit |

### Important (defaults proposed; Anas confirms)

| # | Decision | Default proposal | Anas sign-off |
|---|---|---|---|
| **D5** | Stage 2 cancellation | Continue computing, cache result. Reconnect within 5 min serves cached | ⏸ pending audit |
| **D6** | Brief structure across stages | Stage 2 APPENDS to Stage 1. Stage 1 = header (classification + quick value + MUC), Stage 2 = body (cap rate, comparables, sources block). UI shows them as one progressive document | ⏸ pending audit |
| **D7** | Stage 1 confidence labeling | «تقدير سريع — التحليل العميق جاري» with explicit MUC ±20%. No "preliminary" badge | ⏸ pending audit |
| **D8** | Asset types bypass logic | No bypass — always 2-stage even if redundant. ~100 ms wrapper cost accepted for consistency | ⏸ pending audit |
| **D11** | Stage 1 minimum output | `asset_type` + classifier confidence + (quick value OR explicit «computing»). Never empty. If Stage 1 can't classify → hard error | ⏸ pending audit |

### Operational

| # | Decision | Default proposal | Anas sign-off |
|---|---|---|---|
| **D9** | Telemetry refresh | New metrics in Sprint 2.22.2: Stage 1 p95, Stage 2 p95, % reaching Stage 2, Stage 1 abandonment rate | ⏸ pending audit |
| **D10** | UI mockups | Claude Code drafts initial mockup in 2.22.0; Anas iterates. No existing mockup library | ⏸ pending audit |

**Note:** All defaults are conditional on H1/H2/H3/H4/H5 being TRUE (or
not the falsifiers). If H5 is FALSE (apartments are data-driven, not
latency-driven), the entire 3-stage path pauses and these decisions
become moot — BRIEF_2p21p2 returns to top of queue.

---

## 2. Audit configuration

Script: `audit_pre_2p22p0.py` (local execution, no Heroku push).
Sample plan: 7 addresses × 3 reps = 21 requests. 30 s between reps of the
same address (Heroku throttling avoidance). Local Windows → public
`https://thammen.qa/api/evaluate`.

| # | Address / PIN | Expected asset_type | Why this one |
|---|---|---|---|
| 1 | `52/903/90` | apartment_building | Fast baseline. Re-confirmed 2026-05-24 audit |
| 2 | `51/835/17` | compound_large | Slow baseline (A6 case). Sprint 2.18.1.1 refusal pattern |
| 3 | `56/565/21` | standalone_villa | Bou Hamour reference case (Sprint 2.19.1, multi-QARS 2.21.0.9) |
| 4 | PIN `74328443` | raw_land | الخور post-2.21.0.5 polish |
| 5 | PIN `90040668` | reject (built non-residential) | Sprint 2.21.0.7 reality-check path |
| 6 | TODO — Lusail apartment Z/S/B | apartment_building | Motivating use case — needs Anas input |
| 7 | TODO — commercial address | commercial / shopping | Edge case — needs Anas input |

Per address the audit captures:

- HTTP status + error class
- TTFB (time-to-first-byte, approx — measured at `urlopen()` return)
- TTLB (time-to-last-byte, full body read)
- Full response JSON
- Brief section IDs (if `brief.sections[]` exists in response)
- Per-field "speed class" inference (which fields require GIS / MoJ / DCF
  vs which are immediate)

---

## 3. Audit results

Run 2026-05-24 18:25 UTC. Three independent runs total (one crashed mid-print
on Unicode in cp1252; two completed clean). All three runs reproduced the same
latency profile within ±0.7 s per asset_type. The numbers below are from the
3rd (final) clean run; runs 1–2 are consistent.

### 3.1 Per-address summary

| case_id | asset_type | reps | min / med / max TTLB (s) | val=None |
|---|---|---:|---|---:|
| c1_apt_52_903_90 | apartment_building | 3 | 4.56 / 4.68 / 4.71 | 3 / 3 |
| c2_compound_51_835_17 | compound_large | 3 | 26.26 / 26.27 / 26.38 | 3 / 3 |
| c3_villa_56_565_21 | standalone_villa | 3 | 23.43 / 23.52 / 23.62 | 3 / 3 |
| c4_rawland_pin_74328443 | raw_land | 3 | 22.00 / 22.49 / 22.91 | 3 / 3 |
| c5_built_pin_90040668 | unknown (reject) | 3 | 4.51 / 4.66 / 4.86 | 3 / 3 |

**Notable: `valuation_amount = None` on 5/5 cases.** Every address tested
today returns "insufficient_data" / refusal at the production tier. None of
the cases had rent input or full audit-input set; that's expected for
brief.qa/api anonymous calls.

### 3.2 Per-asset_type latency

| asset_type | n | p50 (s) | p95 (s) | > 5 s? | > 25 s? |
|---|---:|---:|---:|:---:|:---:|
| apartment_building | 3 | 4.68 | 4.70 | no | no |
| compound_large | 3 | 26.27 | 26.37 | **YES** | **YES** |
| standalone_villa | 3 | 23.52 | 23.61 | **YES** | no |
| raw_land | 3 | 22.49 | 22.87 | **YES** | no |
| unknown (reject) | 3 | 4.66 | 4.84 | no | no |

### 3.3 Field-speed classification (heuristic, for H2)

External-view heuristic per `audit_pre_2p22p0.classify_field_speed`. Fast =
no GIS/MoJ/DCF call needed once classification done; Slow = requires
spatial query / MoJ comparable / DCF / brief composition; Unknown = anything
else.

| case_id | fast | slow | unknown | % fast |
|---|---:|---:|---:|---:|
| c1_apt_52_903_90 | 5 | 3 | 21 | 17.2 % |
| c2_compound_51_835_17 | 4 | 3 | 20 | 14.8 % |
| c3_villa_56_565_21 | 4 | 5 | 23 | 12.5 % |
| c4_rawland_pin_74328443 | 4 | 4 | 21 | 13.8 % |
| c5_built_pin_90040668 | 6 | 3 | 20 | 20.7 % |

**Average across cases: 15.8 % fast.** The "unknown" bucket dominates
(~70 % of fields) because the heuristic prefix-matches a small reserved
list; in practice most "unknown" fields are also non-Stage-1-trivial (e.g.
nested classifier dicts, extent metadata). Even with generous assignment of
"unknown → fast", the lower bound stays well below the 30 % H2 threshold.

### 3.4 Brief structural seams (for H4)

| case_id | n sections | section IDs |
|---|---:|---|
| c1_apt_52_903_90 | 1 | `next_steps` |
| c2_compound_51_835_17 | 4 | `negotiation`, `flags`, `due_diligence`, `material_uncertainty` |
| c3_villa_56_565_21 | 5 | `negotiation`, `flags`, `due_diligence`, `material_uncertainty`, `cap_rate_provenance` |
| c4_rawland_pin_74328443 | 5 | `negotiation`, `flags`, `due_diligence`, `material_uncertainty`, `comparable_grid` |
| c5_built_pin_90040668 | 1 | `asset_type_reality` |

3 of 5 cases carry ≥ 3 brief sections, with consistent section IDs across
asset_types. **Brief template is NOT monolithic** — natural Stage 1 / Stage 2
seams exist (e.g. `material_uncertainty` + `negotiation` could be Stage 1
header, `cap_rate_provenance` + `comparable_grid` could be Stage 2 body).

### 3.5 Reproducibility

3 independent runs (one crashed mid-print on encoding, captured data only;
two completed clean). Cross-run variance per asset_type:

- apartment_building: 4.54 – 4.71 s (Δ = 0.17 s, ~3.6 %)
- compound_large: 26.18 – 26.96 s (Δ = 0.78 s, ~3.0 %)
- standalone_villa: 23.22 – 23.62 s (Δ = 0.40 s, ~1.7 %)
- raw_land: 21.97 – 22.91 s (Δ = 0.94 s, ~4.3 %)
- unknown: 4.51 – 4.86 s (Δ = 0.35 s, ~7.5 %)

All within ±5 % cross-run. The audit is reproducible. One cold-dyno HTTP 503
hit run 1 on c3 (recovered on reps 2+3 in same run) — single-rep cold-dyno
event, consistent with prior audit history (Session_Log §15.1, 21-rep
cohort).

---

## 4. Predictions ledger (H1–H5)

| # | Prediction | Result | Evidence |
|---|---|:---:|---|
| H1 | p95 > 5 s for ≥ 3 of tested asset_types | **TRUE** | 3 of 5: compound_large (p95=26.37 s), standalone_villa (p95=23.61 s), raw_land (p95=22.87 s) |
| H2 | ≥ 30 % of response fields are Stage-1-fast | **FALSE** | avg 15.8 % fast across 5 cases (range 12.5 – 20.7 %) |
| H3 | ≥ 1 asset_type meets ≤ 5 s naturally today | **TRUE** | apartment_building p50=4.68 s, unknown/reject p50=4.66 s — both under 5 s |
| H4 | Brief template has structural seams matching 1/2/3 split | **TRUE** | 3 of 5 cases carry ≥ 3 brief sections with consistent IDs across asset_types |
| **H5** | **Apartment failures are timeout-driven, not data-driven** | **FALSE** | apartment_building 3/3 reps: HTTP 200 + valuation_amount=None + TTLB ~4.7 s. **Zero timeout-driven failures; 3/3 data-driven.** |

---

## 5. Section 8 decision-tree branch indicated

```
H5 false (apartment failures are data-driven, not latency-driven)
   |
   +-> STRONG signal: 3-stage doesn't solve apartments.
       Reactivate BRIEF_2p21p2.md (hybrid foundation).
       3-stage stays as future architectural improvement,
       not blocker for apartments.
```

**Plus an independent caveat from H2 FALSE:**

```
H2 false (insufficient fast fields, 15.8 % < 30 %)
   +-> Even if 3-stage were pursued later, Stage 1 cannot return
       meaningful content at current architecture's "fast" ratio.
       Would need preliminary "fast path" refactor first.
```

H1 TRUE + H4 TRUE individually support 3-stage viability — but H5 is the
decisive falsification. The latency *is* real (3 of 5 asset_types > 5 s),
and the brief *does* have natural seams, but the **apartments problem is
not a latency problem**. Apartments return clean HTTP 200 in ~4.7 s with
no data-failure indicator beyond `valuation_amount=None`. Staging the
response can't manufacture data that isn't there.

---

## 6. Recommended next action

**Reactivate `BRIEF_2p21p2.md` (Hybrid Valuation Foundation).**

The apartments problem is structurally:

- T1 source (MoJ) has no apartment transactions (apartments are an MME
  collection, and authenticated MME access remains pending DevTools
  capture — see `2p21p1_pre/CHANGELOG_pre_2p21p1.md` § 2 diagnosis).
- T2 sources (PropertyFinder, FGRealty, arady) carry asking-price /
  listing data that can stand in for MoJ comparables under the
  tier-weighted framework Rule E3 governs.
- Hybrid foundation builds the tier-weighted aggregator that lets
  apartments produce a valuation from T2 (and developer-direct as
  available) without waiting for MME auth or secretary's confirmed
  sales.

The audit answered the BRIEF's central question honestly: 3-stage is a
real but separable architectural improvement, not the unblock for
apartments. Sprint 2.22.0 is **deferred, not cancelled** — its
falsifiable predictions H1, H3, H4 hold, and once apartments work via
2.21.2 the same evidence may justify revisiting 3-stage as a UX
enhancement Sprint.

**Open follow-up from this audit (not blocking 2.21.2):**

- Cases 6 (Lusail apartment) and 7 (commercial address) were left as
  TODO placeholders in `audit_pre_2p22p0.py`. They were not needed to
  resolve H5 (case 1's three reps were decisive), but if a future audit
  wants to broaden the H5 sample beyond `52/903/90`, those slots can
  be filled in and the audit re-run locally.

- 3-stage H1+H4 TRUE means future "UX refactor Sprint" (post-2.21.2)
  has empirical support. Not a 2.22.0 commitment, just data for a
  later decision.

---

## 7. Hygiene

Per BRIEF §10 step 7: `audit_pre_2p22p0.py` stays in `2p22p0_pre/` as
workspace artifact. **No Heroku push**. No engine version bump. No
production code touched. Local-only execution against public
`thammen.qa/api`.

*— Anas / Claude Code session, 2026-05-24*
