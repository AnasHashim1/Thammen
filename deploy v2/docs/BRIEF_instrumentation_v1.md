# BRIEF — Beta Instrumentation: prediction capture + feedback (v1)

> **Status:** Claude.ai-formulated · **SIGN-READY FOR THE BUILD** (dormant code, safe to ship pre-counsel) · ACTIVATION gated on §8.1/§8.2 (counsel). Anas signs (Rule #32); CC implements + writes the canonical copy on sign.
> **Sprint (proposed):** `2.22.0a.15` · slug `eval-capture-feedback` · engine `thammen-sprint2p22p0a15-eval-capture-feedback` — *number/slug to confirm (§8.5); may warrant a new minor `2.22.1` as the first beta-feature sprint.*
> **Type:** 🟢 Backend feature — **additive, NO valuation-logic change** (not Gate-2 on methodology). BUT the captured-data **policy** is Gate-2-adjacent (PDPPL) — §8.
> **Track:** BETA — serves gate 4 (measured accuracy) + gate 3 (PDPPL-in-practice). Per `BETA_LAUNCH_PLAN_v1` §1 row "Beta instrumentation".
> **Governing:** `BETA_LAUNCH_PLAN_v1` §1/§3 · `LAUNCH_READINESS_GATES_v1` gates 3,4 · the **instrumentation Phase-1 recon (2026-06-01)** · Operational #31 (`extra='forbid'`), #36, backward-compat rule.

---

## §0 — Definition of Ready (recon-measured 2026-06-01)

| Fact | Value | Source (file:line) |
|---|---|---|
| Persistence today | **NONE** — handler logs only the *input* address to stdout/Heroku logs (ephemeral ~1500-line buffer); output stored nowhere | `api.py:928–983` |
| `valuation_id` | generated `THM-{ts}-{zone}{street}{building}`, live in prod, **returned-and-forgotten**; **embeds the address** | `evaluate_property.py:1892` |
| External store | none wired — no DB driver in requirements, no `DATABASE_URL` consumed, Redis off | `requirements.txt` / README |
| Ephemeral FS | local file/SQLite writes wiped on every dyno cycle → durable capture needs an external DB | recon §Q2 |
| Feedback hook | none — no `/api/feedback`; the `index.html` "feedback" hit is a code comment | recon §Q3 |
| Flag precedent | env-var flags exist (`HYBRID_APARTMENTS_ENABLED`, `T3_INVENTORY_ENABLED`), default-off → no new mechanism needed | recon flag-note |
| Seam | the two `api.py` handlers, after `result =`, before `return` — **NOT the engine** | recon §Q4 |

---

## §1 — Problem / why

The beta's strategic purpose is to close the two gates that can't be closed from a desk: **measured accuracy (gate 4)** and **PDPPL-in-practice (gate 3)**. Both require a durable record of what the engine predicted and what actually happened. Today there is none — predictions vanish, no feedback channel exists. Instrumentation is the foundation that makes the beta worth running; without it, a beta is just "people use the tool" and we learn nothing systematically.

---

## §2 — Scope (single-purpose)

**PRIMARY (this sprint):**
1. **Prediction capture** — on each successful `/api/evaluate` (+ `/details`), write one durable record. In the `api.py` seam, **try/except-isolated** so a capture failure can NEVER alter or break a valuation.
2. **Feedback endpoint** — `POST /api/feedback` (Pydantic, `extra='forbid'` per #31), writing one feedback record keyed on the prediction id.
3. **Store = Heroku Postgres (TYPE)** — the only option serving a queryable accuracy backtest *and* a deletable PDPPL record. *(Code targets Postgres; the add-on is NOT provisioned until counsel clears the location — §8.2.)*
4. **Dormant / safe-by-default** — capture + feedback gated behind a **feature flag (off by default**, reusing the env-var pattern) **AND no-op when `DATABASE_URL` is absent**. → the code ships to production **fully dormant (zero data footprint)** until BOTH the flag is on and a DB is provisioned. This is what lets the build proceed **in parallel** with the counsel track.

**Explicit NON-GOALS:**
- 🚫 **NO valuation-logic change** — capture reads only `result` fields + request inputs.
- 🚫 **NO UI / `index.html` change** — backend-only (the user-facing feedback prompt is Sprint 2; zero mobile-390×844 risk).
- 🚫 **NO activation / real-data collection** until the §8.1 PDPPL policy + §8.2 cross-border ruling are in place.
- 🚫 **NOT A7** (separate quick-win).
- 🚫 **NO raw IP storage** — §3.

---

## §3 — Design / mechanism

**Field set (data-minimized, pending counsel ratification — §8.1):**
- **prediction:** `{id, valuation_id, zone, street, building, value, range_low, range_high, method, tier, muc, ts}`
- **feedback:** `{id, valuation_id, outcome, transacted_price?, note?, ts}`
- **IP:** **NOT stored** — it serves rate-limiting, not accuracy. If dedup is ever needed: a salted hash, never raw.
- **Surrogate key (§8.3):** `valuation_id` embeds the address → it is *not* a privacy-safe surrogate. **Analyst lean: introduce a UUID `id` as the surrogate primary key, keep `valuation_id` + address as separate fields** so the address can be redacted independently of the join key.

**Seam** (`api.py`, both handlers — after `result =`, before `return`):
```python
result = evaluate_thammen(...)
if CAPTURE_ENABLED and db_available():        # flag-off OR no DATABASE_URL -> skip silently
    try:
        write_prediction(result, request_inputs)   # reads result fields only
    except Exception:
        log.warning("capture failed", exc_info=True)  # NEVER raises into the response
return result
```
**Backward-compat:** the write is fully isolated; old clients and the valuation path are untouched.

**Postgres:** +1 driver dep, +1 migration (`prediction` + `feedback` tables), +1 small connection/write module. No-op cleanly when `DATABASE_URL` is absent → deployable dormant.

---

## §5 — Hypotheses + Gate-2 stops

| # | Hypothesis | Measure |
|---|---|---|
| H1 | Flag-on + DB: each successful eval writes **exactly one** prediction record; the valuation output is **BYTE-IDENTICAL** to pre-instrumentation. | smoke the 4 anchors before/after → outputs identical + 1 record each. |
| H2 | `/api/feedback` writes one feedback record keyed on `valuation_id`; malformed body rejected (`extra='forbid'`); a forced write-failure does **not** 500 the evaluate path. | isolated tests: valid write · malformed reject · forced-failure → evaluate still 200. |
| H3 | Flag-off **or** `DATABASE_URL` absent → **zero** writes, **zero** behavior change (dormant). | flag-off / no-DB → no records, evaluate byte-identical. |

**Gate-2 STOP if:** any valuation output changes (capture leaked into valuation); a capture failure breaks an evaluate response (isolation failed); any field beyond the §3 minimized set is written; the IP is stored un-hashed; or a write occurs while flag-off/no-DB (dormancy breach).

---

## §6 — Regression anchors + expected

The standard four — **56/565/21, 54/541/6, 55/296/13, 52/903/90** — must return outputs **byte-identical to a14** (capture is additive). With flag-on + DB: one prediction record per successful eval (Abu/Marikh/house). Refusals (apt) captured per §8.4 (recommend yes, `method=insufficient_data`, no value). DoD regression green; py_compile; no `index.html` touch → no mobile re-check needed.

---

## §7 — Governance

No valuation-methodology change → **not Gate-2 on methodology**; the MUC / VPGA-10 / VPS surface is untouched. The captured record is **personal / quasi-personal data under PDPPL** → the data policy (§8.1) is the real gate, and it is counsel's. **Cross-border:** Heroku Postgres is US/EU → storing Qatari property/query data there is a cross-border transfer; counsel must clear the *location* (§8.2).

---

## §8 — Open decisions (PO + counsel) — these gate ACTIVATION, not the build

1. **PDPPL data policy** — fields / retention window / consent (beta-onboarding notice = the lawful basis) / deletion path. **Anas + counsel.** *Build proceeds dormant; activation waits on this.*
2. **Store LOCATION** — Heroku US/EU (cross-border, needs PDPPL clearance) vs a Qatar/GCC-region Postgres (different host; the Heroku add-on then off the table, same schema). **Counsel's cross-border ruling decides.**
3. **Surrogate key** — UUID surrogate + address as separate field (lean: yes, for redactability) vs keep `valuation_id` as the join key.
4. **Refusals captured?** — recommend **yes** (accuracy-relevant), `method=insufficient_data`, no value.
5. **Sprint number / slug** — confirm `2.22.0a.15` vs a new minor `2.22.1` (first beta-feature sprint).

---

*SIGN-READY FOR THE BUILD: the dormant code (flag-off + no-op-without-DB) is safe to ship pre-counsel and reversible. ACTIVATION gated on §8.1/§8.2. Claude.ai formulates; Anas signs (Rule #32); CC implements + writes the canonical brief copy on sign. §5 pre-Sprint audit = the 2026-06-01 instrumentation recon (this sprint adds no new valuation path, so no field/GIS audit applies).*
