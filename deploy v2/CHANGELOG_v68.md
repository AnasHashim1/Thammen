# CHANGELOG v68 — Sprint 2.22.0a.16: Pre-Activation Capture Privacy-Hardening (beta)

- **Engine:** `thammen-sprint2p22p0a16-precapture-privacy-hardening`
- **api/health:** `3.1.0-sprint2.22.0a.16`
- **Date:** 2026-06-01
- **Status:** BUILT + verified locally — capture **still DORMANT** (flag-off + no-op without `DATABASE_URL`). **Presented for Gate-1 (Heroku push) — NOT yet deployed.** ACTIVATION remains counsel-gated (§8.1 PDPPL + §8.2 cross-border + gate-11 security pass).
- **Source:** `docs/BRIEF_precapture_privacy_hardening.md` (Claude.ai-authored; Rule #32 SIGNED). Decisions D1 (disable `note`), D2 (180-day window), D3 (output label "تقدير سوقي آلي", PROVISIONAL). Recon → Claude.ai CONFIRM (Q1 rejected→UUID-FK; Q2–Q5 confirmed).
- **Type:** 🟢 Privacy hardening of the a15 dormant capture — additive/structural, **NO valuation-logic change**; D3 is an Arabic output-copy change (signed).

### Files changed
| File | Change |
|---|---|
| `instrumentation.py` | **rewritten** — UUID-only key; NO stored `valuation_id`; `zone` plaintext + `street_enc`/`building_enc` Fernet-encrypted (gated on `CAPTURE_ENC_KEY`); `created_at`+180d `expires_at`; feedback FK `prediction_id`; NO `note`; +`aggregate_and_purge_expired()` + `erase_prediction()` |
| `api.py` | capture seam returns the UUID → echoes `result['capture_id']` **in active mode only**; `FeedbackRequest` → `prediction_id` (drops `valuation_id` + `note`); feedback log line |
| `evaluate_unified.py` | `ENGINE_VERSION`/`SPRINT_TAG` → `2.22.0a.16` |
| `requirements.txt` | +`cryptography` (Fernet; lazy-imported, unused while dormant) |
| `index.html` | 4 OUTPUT-label spots `تقييم` → **`تقدير سوقي آلي`** (PROVISIONAL, D3) — top-bar, result-card header, estimate-block title, copy text |
| `test_sprint_2p22p0a16_precapture_hardening.py` | **NEW** — 26 isolated checks |
| `test_sprint_2p22p0a15_eval_capture_feedback.py` | **REMOVED** — superseded (the a15 schema it pinned no longer exists; a16 test is its successor) |

## 1. Why
Pre-activation privacy hardening of the dormant a15 capture, so the schema that goes live at activation is already minimized + de-identified. Recon (this sprint) confirmed the a15 dormant schema stored the address **twice** (the address-embedding `valuation_id` as a column **and** `zone/street/building` plaintext) and carried a free-text `note` + no retention.

## 2. What this patch does (signed design)
- **Q1 — de-embed (UUID-FK).** `id` (UUID) is the **sole** surrogate key + join target. The address-embedding `valuation_id` is **never stored** (it stays **display-only** in the API response, prod unchanged). In **active** mode `capture_prediction` RETURNS the UUID; the handler echoes it as `result['capture_id']`; feedback carries it back as `prediction_id` (FK → `prediction.id`). SHA-256(valuation_id) was **rejected** (low-entropy/enumerable → brute-forceable; not de-identification).
- **Q2 — address columns.** `zone` PLAINTEXT (coarse; for zone-aggregation). `street`+`building` **Fernet-encrypted**, separately droppable; encryption **gated on `CAPTURE_ENC_KEY`** → without a key the precise columns are **NULL (never plaintext)**. `transacted_price` plaintext during the window.
- **Q3 — retention (D2).** `created_at` + 180-day `expires_at`. Dormant `aggregate_and_purge_expired()` collapses expired per-record rows → **`prediction_zone_agg`** (zone-level distribution) and DROPS street/building + per-record transacted_price (feedback cascades). `erase_prediction(id)` = row-level data-subject erasure. **Backup erasure = activation runbook** (short PG backup retention) — app code can't reach PG backups.
- **Q4 — `note` removed (D1).** Dropped from the schema, `build_feedback_record`, and `api.FeedbackRequest` (with `extra='forbid'`, a `note` — or the now-removed `valuation_id` — yields **422**).
- **D3 — terminology.** 4 OUTPUT-label spots in `index.html` → "تقدير سوقي آلي" (PROVISIONAL — confirm exact Arabic next Arabic-surface pass). The `تثمين رسمي` disclaimer, scope-tier labels (`تقييم مشروط`), `signed_valuation`/`تقييم موقّع`, `Stage-5 تقييم`, and RICS VPS/IVS labels are **untouched** (the estimate-vs-certified-valuation framing is preserved).

## 3. Dormancy / safety (unchanged)
Default prod env (no flag, no `DATABASE_URL`, no `CAPTURE_ENC_KEY`) → `is_active()=False` → every capture/purge/erase entry point is a no-op; **zero data footprint**. `psycopg2` + `cryptography` are lazy-imported (dormant path needs neither). Capture reads `result` only, never mutates it, swallows all failures. **Active-mode-only** delta: the response gains `capture_id` (for the FK) — **dormant response byte-identical**.

## 4. Verification — empirical (local; no push)
- **py_compile**: api / evaluate_unified / instrumentation → OK. `node` absent (§11.3 precedent); the only JS change is a string-literal *content* edit (line 670) — syntactically safe; mobile 390×844 + render verified at Gate-1.
- **Isolated** `test_sprint_2p22p0a16…`: **26/26 PASS** — Q1 (UUID-only key, no valuation_id anywhere, capture returns UUID active/None dormant, no-mutation), Q2 (zone plaintext, street/building NULL without key; encrypt round-trip skipped locally — `cryptography` not installed, installs on Heroku), Q3 (created_at/expires_at; purge→`prediction_zone_agg` + DELETE; `erase_prediction` row DELETE), Q4 (real `api.FeedbackRequest` rejects `note` **and** `valuation_id` → `extra_forbidden`, requires `prediction_id`), §8.4 refusal, H3 dormancy (`_connect` never called).
- **DoD**: aggregator **392/392** · security **15/15** · surface-honesty **45/45** · broad **57/58** — the 1 = `test_sprint_2p22p0a7_geometric_determinism` (a **live-GIS flake** under broad-run load; **PASSES on direct re-run**, 0 mismatches; this sprint touches none of `geometric_factors`/zoning). Effectively green.

## 5. Deployment (Gate-1 — pending explicit consent; NOT executed)
```
git subtree push --prefix "deploy v2" heroku master      (after Anas "go")
git push origin master
```
Ships **dormant**; only the `engine_version` label → a16 + the `index.html` term change are user-visible. No add-on, no flag, no key.
Post-deploy (Rule #52, two-lane): `/api/health` = a16; **4-anchor byte-identical** (56/565/21, 54/541/6, 55/296/13, 52/903/90 — capture dormant); `POST /api/feedback {prediction_id, outcome}` → `200 {"accepted", stored:false}`; `note` or `valuation_id` → **422**; the result screen shows "تقدير سوقي آلي".

## 6. What's NOT in this patch (scope)
- **NO** activation / flag / `DATABASE_URL` / add-on / `CAPTURE_ENC_KEY`.
- **NO** gate-11 security baseline (rate-limit `/api/feedback`, etc. — lands WITH activation).
- **NO** consent/notice/privacy-flow workstream; **NO** valuation logic / methodology change.
- The `تقدير سوقي آلي` term is **PROVISIONAL** (D3) — final Arabic confirmed in the next Arabic-surface pass.
