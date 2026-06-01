# CHANGELOG v67 — Sprint 2.22.0a.15: Beta Instrumentation (prediction capture + feedback)

- **Engine:** `thammen-sprint2p22p0a15-eval-capture-feedback`
- **api/health:** `3.1.0-sprint2.22.0a.15`
- **Date:** 2026-06-01
- **Status:** BUILT + verified locally — **DORMANT** (flag-off + no-DB → no-op). **Presented for Gate-1 (Heroku push) — NOT yet deployed.** ACTIVATION is counsel-gated (PDPPL §8.1 + cross-border §8.2).
- **Brief:** `docs/BRIEF_instrumentation_v1.md` (Anas-signed, Rule #32). Decisions: **§8.3** UUID surrogate PK + redactable address; **§8.4** capture refusals; **§8.5** keep `2.22.0a.15`.
- **Type:** 🟢 Backend feature — additive, **NO valuation-logic change** (not Gate-2 on methodology). The captured-data *policy* is Gate-2-adjacent (PDPPL) and gates ACTIVATION, not this build.

### Files changed
| File | Change |
|---|---|
| `instrumentation.py` | **NEW** — dormant capture/feedback module (Postgres target, lazy `psycopg2`) |
| `api.py` | +defensive import guard (`_INSTR_OK`); +capture call before `return` in both `/api/evaluate*` handlers; +`FeedbackRequest` model + `POST /api/feedback` |
| `evaluate_unified.py` | `ENGINE_VERSION` + `SPRINT_TAG` → `2.22.0a.15` (`/api/health` auto-derives) |
| `requirements.txt` | +`psycopg2-binary` (installed for activation; unused while dormant) |
| `test_sprint_2p22p0a15_eval_capture_feedback.py` | **NEW** — 27 isolated checks (H1/H2/H3 + §3/§8.3/§8.4) |

## 1. Why
Beta **gate 4** (measured accuracy) + **gate 3** (PDPPL-in-practice) both need a durable record of *what the engine predicted* vs *what actually happened*. Recon (2026-06-01) measured: **nothing is persisted today** — the handler logs only the *input* address to stdout/Heroku logs (ephemeral); the output (value/method/tier/MUC) and `valuation_id` are returned-and-forgotten; no feedback channel exists. This sprint adds the foundation, **dormant**, so it ships safely *before* the counsel-gated activation.

## 2. What this patch does (additive)
- **`instrumentation.py`**: `capture_prediction(result, inputs)` + `capture_feedback(payload)` — each a guarded **no-op unless `is_active()`** (`EVAL_CAPTURE_ENABLED` truthy **AND** `DATABASE_URL` set). Pure record builders map the engine `result` → the data-minimized §3 field set. Postgres I/O only (`psycopg2` lazy-imported inside `_connect`). Any failure is logged + **swallowed** — never raises into the evaluate path; **never mutates `result`**.
- **`api.py` seam**: both unified-branch returns get `if _INSTR_OK: _instr.capture_prediction(result, {zone,street,building})` immediately before `return _attach_freshness(result)`. New `POST /api/feedback` (`FeedbackRequest`, `extra='forbid'` per #31) → `capture_feedback`; dormant → validates + `200 {"status":"accepted","stored":false}` without storing.
- **Field set (§3, data-minimized):** prediction `{id (UUID PK), valuation_id, zone, street, building, value, range_low, range_high, method, tier, muc, ts}`; feedback `{id, valuation_id, outcome, transacted_price?, note?, ts}`. **IP not stored.** `valuation_id` + address kept separate from the UUID `id` (§8.3 — independently redactable). **Refusals captured** (§8.4): `value=None`, `method=insufficient_data`.
  - Mapping: `value←valuation.amount`, `range←valuation.low/high`, `method←valuation.method`, `tier←accuracy.tier`, `muc←material_uncertainty.level`, `valuation_id←` top-level `valuation_id` (None on refusals; UUID `id` is the PK regardless).

## 3. Dormancy / safety
- Default production env (no `EVAL_CAPTURE_ENABLED`, no `DATABASE_URL`) → `is_active()=False` → capture is a **complete no-op** (returns False without touching `_connect`). **Zero data footprint.**
- `psycopg2-binary` is lazy-imported → unused while dormant; the module imports cleanly without it.
- The Heroku Postgres add-on is **NOT provisioned** (counsel-gated, §8.2). `DATABASE_URL` absent → dormant even if the flag were on.

## 4. Verification — empirical (local; no push)
- **py_compile**: `api.py`, `evaluate_unified.py`, `instrumentation.py` → OK.
- **Isolated** `test_sprint_2p22p0a15_eval_capture_feedback.py`: **27/27 PASS**.
  - **H1** (active + fake DB): exactly ONE `prediction` INSERT (12 params incl. value + valuation_id); `result` dict **byte-identical** after capture (no mutation).
  - **H2**: feedback keyed on `valuation_id` (+own UUID `id`); **real** `api.FeedbackRequest` rejects an extra field (`extra_forbidden`) + missing `valuation_id`; forced `_connect` failure → swallowed → returns False (no raise).
  - **H3** (dormancy): no-flag/no-DB · flag-on/no-DB · DB/flag-off → `is_active` False, zero writes, `_connect` **never called**.
  - **§8.4** refusal mapped defensively; **§3** record has EXACTLY the 12 fields, no IP.
- **DoD matrix**: aggregator **392/392** · security **15/15** · surface-honesty **45/45** · broad **58/58** files (was 57; +1 = this test). All green.
- **Route check**: `/api/feedback` registered on `app.routes` alongside the existing `/api/*` routes.
- **Byte-identical (4 anchors)**: guaranteed by construction — capture is read-only + dormant-by-default no-op (H1.6 + H3). The **live** 4-anchor byte-identical smoke (`56/565/21`, `54/541/6`, `55/296/13`, `52/903/90`) is the **post-deploy** step (Rule #52), to run after the Gate-1 push.

## 5. Deployment (Gate-1 — pending explicit consent; NOT executed)
```
git subtree push --prefix "deploy v2" heroku master      (after Anas "go")
git push origin master                                   (backup mirror, Rule #43)
```
Ships **dormant** (no behavior change; only the `engine_version` label → a15). No add-on, no flag set.
Post-deploy (Rule #52): `/api/health` = a15; 4-anchor smoke byte-identical; `POST /api/feedback` → `200 {"accepted", stored:false}`; logs show no capture writes (dormant).

## 6. Activation (LATER — counsel-gated, NOT this sprint)
1. PDPPL policy signed (§8.1 — fields / retention / consent / deletion).
2. Cross-border ruling (§8.2): Heroku Postgres (US/EU) cleared, **OR** a Qatar/GCC-region Postgres provisioned (same schema; the Heroku add-on then off the table).
3. Provision DB → set `DATABASE_URL` → set `EVAL_CAPTURE_ENABLED=true`. Capture goes live (and `/api/feedback` starts persisting).

## 7. What's NOT in this patch
- **NO** valuation-logic / methodology change (MUC / VPGA-10 / VPS surface untouched).
- **NO** UI / `index.html` (the user-facing feedback prompt is Sprint 2; zero mobile-390×844 risk).
- **NO** add-on provisioned; **NO** real data collected (dormant).
- **NOT** A7 (separate quick-win).
- The v2 fallback path (`_UNIFIED_OK=False`; dead in prod) is **not** instrumented.
- Land/PIN evals store null `zone/street/building` (the signed §3 field set is `zone/street/building`; `pin` is not in scope this sprint).
