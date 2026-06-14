# CHANGELOG v125 — Sprint 2.22.0b.42 «نسخة-المُشغِّل بالبريد» (operator report-copy by email)

> **Engine:** `thammen-sprint2p22p0b42-report-copy-email` · **SPRINT_TAG** `2.22.0b.42` ·
> **api/health** `3.1.0-sprint2.22.0b.42` · **date** 2026-06-14
> **Files:** `report_mailer.py` (NEW) · `api.py` (import + 2 guarded seams) ·
> `evaluate_unified.py` (2 version lines) · `test_sprint_2_22_0b42.py` (NEW)
> **Type:** 🟢 ADDITIVE BACKEND / DORMANT-by-default / VALUE-INVARIANT (the evaluation
> response is byte-identical; the email is a post-response side-effect that never mutates
> `result`). **Decision (PO):** channel = **email (Resend)** · scope = **operator's own
> reports now** (test mode); beta-wide deferred behind the a24 notice update.

## 1. Why this matters
The PO asked for **a memory of every report + a copy delivered to him**. Today the system is
stateless: a report is generated, displayed, then forgotten — the address is processed
in-memory and NOT stored (a24/DPIA §5), and the dormant a15/a16 capture is a *minimized*
aggregate record, not the report and not delivered anywhere. There was no operator audit
trail and no "did the tool produce this?" record.

## 2. The design (why email, not a DB)
Heroku's filesystem is **ephemeral** — a runtime SQLite is wiped on every dyno restart (this
is why `developer_inventory.sqlite` is committed read-only). The durable alternatives are a
managed Postgres (the counsel-gated a15 path) **or** the operator's mailbox. For a one-person
operation at beta scale, **the inbox IS the memory** — durable, searchable by `report_ref`,
backed up by the mail provider — so **one mechanism gives both "a copy reaches me" AND "a
memory of every report"**, with zero database to run or back up.

## 3. What this patch does
**NEW `report_mailer.py`** — mirrors `instrumentation.py` discipline (gated, lazy, never
raises, pure builders + isolated I/O):
- `mail_enabled()` — opt-IN, OFF by default; True only when **`RESEND_API_KEY` AND
  `REPORT_COPY_EMAIL`** are set. Dormant ⇒ every entry point is a silent no-op ⇒ zero external
  data flow.
- `build_email(result, inputs)` — PURE (no env/network). Subject `[ثمن] {report_ref} —
  {address} — {value} ر.ق` (inbox search key = the ref). RTL HTML summary (ref · address ·
  asset · value range+median · leader/method · MUC · property-basis · date · engine · fp;
  Latin/number tokens in `dir=ltr` islands, Rule #25). The **FULL result JSON is attached**
  (base64) so the email is a complete archive (the visual report is reproducible on
  thammen.qa from the address + ref).
- `send_report_copy(result, inputs)` — guarded: dormant → `False`, no network, NO mutation of
  `result`; active → one POST to `https://api.resend.com/emails` via stdlib `urllib` (no new
  dependency); failures swallowed + logged.
- Default sender `onboarding@resend.dev` (Resend's test sender — delivers ONLY to the Resend
  account owner's own verified email → a **structural "my reports only"** until a domain is
  verified); overridable via `REPORT_COPY_FROM`.

**`api.py`** — `BackgroundTasks` imported; defensive `_MAIL_OK` import guard (mirrors
`_INSTR_OK`); both `/api/evaluate` + `/api/evaluate/details` (unified path) gain a
`background_tasks: BackgroundTasks` param and, right after the dormant capture seam, a guarded
`background_tasks.add_task(_mailer.send_report_copy, result, {...ids})`. Runs **after** the
response → **zero latency**; never touches the returned value. Fallback (v2) path unchanged.

**`evaluate_unified.py`** — 2 version-string lines (b41 → b42).

## 4. Governance (Rule #39 flag — the ONE honest caveat)
The live a24 notice tells the user the address is processed in-memory and **NOT stored**. Once
a copy is emailed, the address IS stored (operator inbox + mail provider). For the **operator's
own testing** (Anas valuing his own properties, pre-invited-beta): **zero third-party data, no
governance issue**. For **real beta users**: the a24 notice line MUST be updated to disclose the
operator copy (+ a PDPPL nod) **before** the invited beta opens. The flag is the on/off; the
notice update is the gate for beta-wide use. Registered on the launch-readiness gates.

## 5. Verification — empirical evidence (local, measured)
- `python -m py_compile` — **4/4 OK** (api, evaluate_unified, report_mailer, test).
- Isolated `test_sprint_2_22_0b42.py` — **36/36 PASS** (E14, exercises the production
  functions): dormant-gate matrix · pure `build_email` shape (recipient/from/subject-ref/
  html/JSON-attachment/slug-safe filename/from-override) · refusal + address fallbacks ·
  `send_report_copy` dormant→no-network / active→exactly-one-POST / failure-swallowed ·
  **value-invariance** (`result` unchanged by build+send) · api.py wiring (BackgroundTasks +
  2 guarded `_MAIL_OK` seams).
- DoD: aggregator `run_sprint_2p22p0a_suite.py` **392/392 MATCH** · security
  `test_sprint_2p16p17_security.py` **15/15** · surface `test_sprint_2p22p0a3_surface_honesty.py`
  **45/45** · broad `2p22p0_pre/run_regression_2p22p0a.py` **110/110 ALL GREEN** (109→110, the
  new test; 187.5s, no flake).
- `import api` loads cleanly with the change (**14 routes**); `api._MAIL_OK = True`;
  `report_mailer.mail_enabled()` = **False** by default → dormant, response byte-identical.
- (Note: fastapi/slowapi were absent in this local env → installed to run the security suite +
  prove the import; the security suite then passed 15/15.)

## 6. Deployment
```
git add report_mailer.py api.py evaluate_unified.py test_sprint_2_22_0b42.py CHANGELOG_v125.md
git commit -m "Sprint 2.22.0b.42 (report-copy email): operator memory of every report"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```
**To ENABLE (operator action, after deploy):**
```
heroku config:set RESEND_API_KEY=re_xxxxxxxx
heroku config:set REPORT_COPY_EMAIL=<your-Resend-account-email>
# optional, after verifying a domain in Resend:
# heroku config:set "REPORT_COPY_FROM=Thammen <reports@thammen.qa>"
```
Without these two vars the feature stays **dormant** (no email, response byte-identical to b41).

## 7. Verification curl (post-deploy)
```
curl -s https://thammen.qa/api/health   # version 3.1.0-sprint2.22.0b.42
# 5-anchor value byte-gate (browser-UA, Rule #61) must stay identical to v212:
#   54/541/6=2.4M cost-led · 56/647/6=3.8M geo · 55/296/13=2.6M · 56/565/21=2.4M · 52/903/90=refusal
# Then set the two config vars and run one evaluation -> a copy lands in the inbox,
# subject "[ثمن] TH-… — …", with the full result JSON attached.
```

## 8. What's NOT in this patch (scope boundary)
- **NOT** a Postgres/DB store (that is the counsel-gated a15 instrumentation, D-2). The inbox is
  the memory.
- **NOT** beta-wide — gated to the operator's own use until the a24 notice is updated (§4).
- **NOT** a frontend change (`index.html` untouched); **NOT** a methodology/value change (the
  response is byte-identical; the email is a side-effect).
- The fallback (v2) eval path is not wired (mirrors the capture seam — unified path only).
- No WhatsApp/dashboard channel (email was the chosen channel).
