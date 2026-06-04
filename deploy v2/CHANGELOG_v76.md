# CHANGELOG v76 — Sprint 2.22.0a.24 (beta-launch copy + consent entry gate)

**Engine:** `thammen-sprint2p22p0a24-beta-entry-gate` · **SPRINT_TAG** `2.22.0a.24` ·
**api/health** `3.1.0-sprint2.22.0a.24` · **Date:** 2026-06-05
**Files changed:** `index.html` (entry gate + Terms/Privacy modal + 3 links + CSS + JS),
`api.py` (address scrubbed from 2 INFO log lines — §4 / DPIA §5), `evaluate_unified.py`
(ENGINE_VERSION / SPRINT_TAG → a24), `docs/DPIA_AI_impact_beta_v1.md` (new), `CHANGELOG_v76.md`.
**Type:** content + small frontend + a DPIA doc. **NO engine / valuation-logic change — every
headline + B-1 `value_floor` byte-identical.** Gate-2 (user-facing copy) SIGNED by Anas (final);
Gate-1 (push) AUTHORIZED in the brief.

---

## 1. Why this matters
Thammen is going to a **free, invite-only, capture-DORMANT accuracy beta** (villas + land). Before a
user runs the tool we owe them an honest, up-front framing — what it is / is not, coverage, stated
limits, and their part — plus a reachable Terms & Privacy notice and a single affirmative consent. The
result surface already carries the not-certified disclaimer, the material-uncertainty banner, the
stale-data banner, and the B-1 land-floor/condition disclosure; this sprint adds the **pre-use**
onboarding + consent layer that complements (does not duplicate) them, and records a proportionate DPIA.

## 2. Context (additive, not a bug)
No defect. Pre-launch onboarding/consent did not exist; the tool opened straight to the form. The only
correctness finding surfaced during the §4 verify (see §3 below): the app was logging the property
**address** to the Heroku log stream, which is in tension with the signed notice's "we do not store the
address."

## 3. Root cause of the one code finding (§4 / DPIA §5 — body logging)
`api.py` logged the full address at INFO on both evaluate endpoints (`LOG_LEVEL` defaults to `INFO`):
- `evaluate_quick` (was api.py:943): `f"evaluate quick: {req.zone}/{req.street}/{req.building} from {ip}"`
- `evaluate_with_details` (was api.py:1007): `f"evaluate details: {req.zone}/{req.street}/{req.building} floors=… from {ip}"`
A property address is personal data of its owner; emitting it to logplex contradicts the beta privacy
notice ("the tool stores nothing… we do not store the address"). The brief §4 explicitly authorizes
"disable body logging / minimize retention" to back DPIA §5 — so the address was scrubbed from both
lines (client IP kept for ops/abuse; non-identifying building attributes kept on the details line).

## 4. What this patch does
**Frontend (`index.html`):**
- **Entry gate** (`#betaGate`, z-index 2000): onboarding framing (verbatim §1 — title, "ما هذا / ما ليس
  هذا / ماذا يغطّي / حدود نعرضها بصراحة / دورك", the "بالمتابعة تُقرّ…" line), the affirmation statement
  (verbatim §3) + a single **«أوافق وأكمل»** button, a link to the full Terms & Privacy, and a
  collapsible English summary. CSS `.bgate*`.
- **Session-only reveal:** `ackBeta()` sets `sessionStorage['thammen_beta_ack']='1'` (in-memory fallback
  if blocked) and hides the gate. A tiny **synchronous** inline script right after the gate markup hides
  it before paint for returning-within-session users. **No cookie, no server write, stores nothing.** New
  session → gate shows again.
- **Terms & Privacy modal** (`#termsModal`, z-index 2100): full verbatim §2 (7 Arabic sections + English
  mirror). Frontend-only — no server route. Reachable from the **entry gate + home screen + results
  footer** (3 links). `openTerms()` / `closeTerms()`.
- **Bidi:** Latin/number runs LRM-wrapped (`&lrm;`) per Rule #25 / a8; phone numbers and the
  "Heroku وCloudflare" infra token wrapped as `dir="ltr"` islands so they read in the signed order.
**Backend (`api.py`):** address removed from the two evaluate INFO log lines (§3). No behavior/output
change.
**Version (`evaluate_unified.py`):** ENGINE_VERSION / SPRINT_TAG → a24 (api/health auto-derives).
**Docs:** `docs/DPIA_AI_impact_beta_v1.md` committed verbatim from the brief §5.

## 5. Verification — empirical evidence
- **Ground-truth handshake (Rule #57):** pre-edit live = a23/v162, MoJ 155d stale, qars healthy,
  master==origin; security rate-limits `5/s,30/min,200/hr` key `cf-connecting-ip` (backs DPIA §5).
- **py_compile:** `api.py` + `evaluate_unified.py` OK.
- **R14 (real Chromium, `node` absent — a8/a17/a21 precedent):** whole-file inline JS parsed (all
  functions defined: `ackBeta`/`openTerms`/`closeTerms`/`go`/`fmt`), **0 console errors** across reloads.
  390×844: no horizontal overflow; gate card scrolls internally; Terms modal no overflow. Desktop
  1280×800: no overflow. Bidi measured: RICS/IVS + 2025 correct; "Heroku وCloudflare" reads L→R as one
  island; both phone spans render "+974 70177761" with `+` leftmost (LTR). Gate flow proven: ack → hidden
  + flag="1" + tool revealed; reload-with-flag → gate stays hidden; clear-flag + reload → gate reappears.
  Terms: 7 AR + 7 EN sections present.
- **DoD (PYTHONIOENCODING=utf-8):** aggregator **392/392** · security **15/15** · surface-honesty
  **45/45** · broad auto-walk **66/66** (205.6s, no flake). No new test file (presentation-only; the gate
  JS is covered by the Chromium R14 check, not the Python suite).
- **Post-deploy (filled at deploy):** /api/health = a24/v_N; 4 anchors byte-identical (zero value drift);
  stale-banner prominent; apartment-refusal (52/903/90) renders `message_ar` + `recommendation_ar`.

## 6. Deployment
```
cd /d "C:\Thammen\deploy v2"
git add index.html api.py evaluate_unified.py docs/DPIA_AI_impact_beta_v1.md CHANGELOG_v76.md
git commit -m "Sprint 2.22.0a.24 (beta entry gate): onboarding + consent + Terms/Privacy + DPIA; scrub address from logs (§4)"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 7. Verification curl (post-deploy)
```
curl -s "https://thammen.qa/api/health"
curl -s -X POST "https://thammen.qa/api/evaluate" -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124 Safari/537.36" -H "Content-Type: application/json" -d "{\"zone\":56,\"street\":565,\"building\":21}"
```
Expect: health version `…a24`; 56/565/21 = 2,400,000 (comparison_bracket, unchanged). Re-smoke
54/541/6 (5,400,000 comparison_thin), 55/296/13 (2,600,000), 52/903/90 (refusal) for zero drift.

## 8. What's NOT in this patch
- **No engine / valuation-logic change** — every headline + B-1 `value_floor` byte-identical; this is a
  presentation + privacy-doc sprint.
- **No capture activation** — capture stays DORMANT (a16); no DB, no `EVAL_CAPTURE_ENABLED`. The gate
  stores nothing server-side. Activation remains counsel-gated (R11).
- **No feedback UI** — Sprint 2 owns the in-app feedback prompt; for the beta, feedback flows to Anas's
  WhatsApp (per the notice). `/api/feedback` stays dormant.
- **No Terms backend route** — the notice is a frontend modal (stores nothing).
- **No Cloudflare/Heroku infra reconfig** — the app-side address log was scrubbed (in our control);
  Heroku router / Cloudflare do not persist POST bodies by default (router logs method+path only). If
  infra logging is ever added, revisit per DPIA §5.
- **No B-2** — the durable R7 built-type/condition fix (Stage-2 elicitation) remains next.
