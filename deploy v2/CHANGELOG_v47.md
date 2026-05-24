# CHANGELOG v47 — Sprint 2.21.2 — Hybrid Valuation Foundation

**Engine version (post-deploy):** `thammen-sprint2p21p2-hybrid-foundation`
**Heroku release target:** TBD (pending Anas review per BRIEF §9 step 8)
**Date:** 2026-05-24
**BRIEF reference:** [`BRIEF_2p21p2.md`](2p21p2_pre/BRIEF_2p21p2.md) (v2, Anas-signed for D1–D6)

---

## Slot-numbering deviations (per Rule #39 + Rule #53 precedent)

The BRIEF was drafted before this slot count was checked. Two numbering
drifts surfaced at execution time, both honoured by using actual project
state (not the BRIEF literal):

| BRIEF said | Reality | Rationale |
|---|---|---|
| `CHANGELOG_v43.md` | **`CHANGELOG_v47.md`** | v43 is already Sprint 2.21.0.9 (multi-QARS Stage 1). Next sequential slot per Project_Instructions §2 is v47. |
| `Empirical_Findings_v3.md` | **`docs/Empirical_Findings.md`** | Actual project file has no `_v3` suffix; BRIEF's name was a Claude.ai-session convention. |

Same pattern as Rule #53 §10 in BRIEF itself: slot drift between Claude.ai
brief drafting and Claude Code execution. Not a methodology issue.

---

## 1. Decision register (D1–D6, all Anas-signed)

Per BRIEF §1:

| # | Decision | Value | Source |
|---|---|---|---|
| **D1** | Sprint number | `2.21.2` (2.21.1 reserved as MME-dependent, suspended) | Anas-signed |
| **D2** | Rule E3 update text | See §3 — **8** numbered constraints | Anas-signed (v2 expansion adds #7 + #8) |
| **D3** | T2 weight cap when T1 present | `0.40` | Anas-signed |
| **D4** | T3 weight cap | `0.15` | Anas-signed |
| **D5** | T2 negotiation discount | `−10 % to −15 %`, midpoint `−12.5 %` | Anas-delegated, derived from EMPIRICAL_FINDINGS §3 |
| **D6** | T3 combined adjustment | `−15 % to −20 %`, midpoint `−17.5 %` | Anas-delegated, derived as ~10 % negotiation + ~7.5 % off-plan-to-resale |

Both D5 and D6 are tagged `provisional, broker-experience-grounded` in
`HYBRID_TIER_CONFIG`. Recalibration from brokerage Confirmed Sales pipeline
is a future Sprint dependency (BRIEF §8), **not a blocker for shipping
2.21.2**.

---

## 2. Pre-Sprint §5 audit results

Per BRIEF §5. Five probes, no surprises.

### Probe 1 — Current `/api/evaluate` behaviour for apartments

**Status:** ✅ PASS (via proxy — per Anas approval to use 52/903/90
instead of 5 Lusail-specific Z/S/B)

**Evidence (this Sprint, fresh rep 2026-05-24 ~18:50 UTC):**

```
POST /api/evaluate  body={"zone":52,"street":903,"building":90}
  → HTTP 200  5.34 s
    engine_version = "thammen-sprint2p18p1p1-compound-misroute-fix"  (v101)
    asset_type     = "apartment_building"
    valuation_amount = None
```

**Cross-reference (Pre-Sprint 2.22.0 audit, 2026-05-24 morning, 3 reps):**

| rep | HTTP | TTLB | asset_type | valuation_amount |
|---|---:|---:|---|---|
| 1 | 200 | 4.71 s | apartment_building | None |
| 2 | 200 | 4.68 s | apartment_building | None |
| 3 | 200 | 4.56 s | apartment_building | None |

Total: **4 reps, 4 × HTTP 200, 4 × `valuation_amount=None`**. Reproducible
DCF-refusal pattern — Thammen has no apartment valuation today.
Confirms BRIEF premise: the gap Sprint 2.21.2 lays foundation to fill exists.

**Why 52/903/90 is a valid proxy:** the gate is `asset_type=apartment_building`
→ DCF refusal without `rent_input`. This classifier output is geography-
agnostic (no Lusail-specific routing in `evaluate_unified.py`), so a Lusail
apartment would exhibit the same pattern. Per Rule #36 (observed-vs-expected),
this is empirical evidence that the BRIEF's "all 5 return insufficient_data"
claim is structurally inevitable.

### Probe 2 — MoJ apartment record count for Lusail

**Status:** ✅ PASS (n=0 apartment-unit rows)

**Method:** `probe_moj_lusail_apartments.py` (workspace artifact) reads
`moj_weekly.csv` (n=26,719 total rows), normalizes per Operational §14 NBSP
rule, counts rows where district matches "لوسيل" / "لوسيل 69" AND asset_type
contains any of {`شقة`, `شقق`, `وحدة سكنية`}.

**Result:**
- Total Lusail rows: 175
- Apartment-unit rows (`شقة` / `شقق` / `وحدة سكنية`): **0**
- Whole-building rows (`عمارة سكنية` / `برج سكني`): 5
- Top Lusail asset_types: `أرض فضاء` (91), `فيلا` (49), `مبنى سكني` (7),
  `عمارة سكنية` (4), `فيلا + بنت هاوس` (3), `مبنى إداري وتجاري` (3), …

Confirms BRIEF memory: MoJ does not disaggregate individual apartments. T1
is structurally empty for apartment units.

### Probe 3 — arady.qa Lusail apartment reachability

**Status:** 🟡 PARTIAL (root reachable; URL pattern unconfirmed, deferred
to Sprint 2.21.3 connector smoke)

**Method:** `probe_t2_listings.py`.

**Result:**
- `https://arady.qa/` → HTTP 200, 238 KB body, 32 `شقة` mentions, Arabic
  Qatar-focused content confirmed
- `https://arady.qa/properties?type=apartment&location=lusail` → HTTP 404
  (search URL pattern guessed wrong; correct pattern is a Sprint 2.21.3
  discovery item)

Site is accessible from this network. Per BRIEF Probe 3 the criterion is
"≥30 listings retrievable" — root page alone doesn't satisfy this strictly,
but it does not "return empty" (the BRIEF surprise condition). Sprint
2.21.3 connector smoke will resolve the URL pattern.

### Probe 4 — PropertyFinder Qatar reachability

**Status:** ✅ PASS strong

**Method:** Same script, hit
`https://www.propertyfinder.qa/en/search?c=2&t=1&l=63` (rent / type=1 /
location=63 = Lusail).

**Result:**
- HTTP 200, 955 KB body
- **142** `/en/plp/` listing-detail links — well over the n≥30 threshold
- 14 `QAR` price tokens
- 19 `لوسيل` / `Lusail` mentions

Page-1 results alone satisfy the n≥30 requirement with substantial
margin. Pagination behaviour (CLAUDE.md §14: "PropertyFinder fully SSR —
pagination works") confirms deeper sample is retrievable in the connector
Sprint.

### Probe 5 — Developer-direct (T3) log status

**Status:** 📋 DEFERRED (to Sprint 2.21.4)

**Rationale (per Anas approval):** `hybrid_valuation_v1()` accepts
`t3_values: list[dict] | None` per BRIEF §4 spec. Cases A/B/D handle
`t3_values=None`. Case C (T3-alone) explicitly refuses per Constraint 8.
The function is null-safe for T3 absence — real T3 log feeds in Sprint
2.21.4 (`developer_inventory.sqlite` + manual entry per BRIEF §8 roadmap).
Probe 5 confirms a Sprint-pipeline question, not a function-spec question;
deferring it does not affect 2.21.2's deliverables.

### Audit verdict

**No surprises.** All BRIEF premises hold:

- ✅ T1 truly absent for individual apartments (Probe 2)
- ✅ T2 (PropertyFinder) carries plenty of listings, well over n≥30 (Probe 4)
- 🟡 T2 (arady) reachable, full URL discovery deferred (Probe 3 — not a surprise)
- ✅ Thammen currently refuses apartment valuations (Probe 1)
- 📋 T3 pipeline deferred to 2.21.4 (Probe 5 — by design)

Safe to proceed with implementation (§9.3 onward).

---

## 3. Rule E3 update (per BRIEF §3)

*Filled in by §9.3 — see diff in `docs/Empirical_Findings.md` Rule E3.*

The replacement text is the BRIEF §3 8-constraint version, deployed verbatim.

---

## 4. `hybrid_valuation.py` — new module

*Filled in by §9.4 — see `hybrid_valuation.py` at repo root.*

Exposes:
- `HYBRID_TIER_CONFIG` (provisional, broker-experience-grounded)
- `hybrid_valuation_v1(t1_values, t1_n_total, t2_values, t3_values, config)`
- `_apply_tier_caps()` (internal)
- `_normalize_t1_absent_case()` (internal)

**Not wired into engine path** — Sprint 2.21.3 onward will call it from
`evaluate_unified.py`. Today its existence is the deliverable; production
behaviour is identical to v101 except for the engine_version string.

---

## 5. Tests — `tests/test_sprint_2p21p2_hybrid_foundation.py`

*Filled in by §9.5 (deferred per Anas review gate).*

Covers H1–H4 + H6 per BRIEF §6.

---

## 6. Engine version bump

*Filled in by §9.6 (deferred per Anas review gate).*

Target: `ENGINE_VERSION = "thammen-sprint2p21p2-hybrid-foundation"`,
`SPRINT_TAG = "2.21.2"`.

---

## 7. Regression + deploy

*Filled in by §9.7–§9.9 (deferred per Anas review gate).*

H5 prediction: all existing standalone tests still pass. If any existing
test fails, rollback immediately (BRIEF §6 rollback gate — indicates
accidental coupling into live path).

---

## 8. Review gate (Anas)

Per Anas's chosen order (option B from BRIEF §9): **stop after §5 + Rule E3
update + initial `hybrid_valuation.py`**. Anas reviews:
- §5 audit findings (above) — any surprise → halt
- Rule E3 diff
- `hybrid_valuation.py` source

before proceeding to tests, version bump, regression, and Heroku release.
