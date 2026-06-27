# CHANGELOG v159 — Sprint 2.22.0b.78 «كتالوج تعريب الخلفية» (EN backend catalog + post-pass)

> Engine `thammen-sprint2p22p0b78-en-backend-catalog` · SPRINT_TAG `2.22.0b.78` ·
> api-health `3.1.0-sprint2.22.0b.78`. **🟢 BACKEND-ADDITIVE / VALUE-INVARIANT** —
> the engine valuation logic + `index.html` are UNTOUCHED; a new `en_localize.py`
> module + an additive post-pass in `api.py` (the `_attach_freshness` seam + the
> `/api/scope` return) attach `{base}_en` siblings to cataloged `{base}_ar` strings.
> Files: `en_localize.py` (new), `api.py` (guarded import + 2 seams), `evaluate_unified.py`
> (2 version lines), `test_sprint_2_22_0b78.py` (new), `test_sprint_2_22_0b77.py` (R6
> re-point), `CHANGELOG_v159.md` (new). **Second sprint of the EN-localization track.**

## 1. Why this matters

b77 shipped the frontend i18n infrastructure (dormant). b78 ships the **backend EN
content**: an English twin for every user-facing Arabic string the result / confirm /
refusal / scope surfaces render, so that when the core flow is wired (b79) and the flag
is flipped (reveal), the result screen renders in English. The PO confirmed the load-bearing
terms (AskUserQuestion): product = **"Automated Market Valuation"**, the disclaimer =
**"not a certified valuation"** — those + the full termbase drive the wording.

## 2. Architecture (chosen after measuring the surface)

A live capture across diverse branches (cost_led / geo_full / e25 / matched / refusal /
unknown-refusal / compound / teardown / luxury / income / land / scope) catalogued the
rendered `_ar` surface: **~128 truly-constant strings** (fixed labels / clauses /
disclaimers / reasons / methodology / banners) + ~90 number-interpolated ones (notes /
source / assumptions with embedded amounts / n / % / days) + proper nouns (landmark /
district names).

- **Truly-constant strings → a centralized catalog** (`en_localize.CATALOG`, AR→EN) applied
  by a single **additive post-pass** `attach_en(result)`. The 8 engine modules stay
  **UNTOUCHED** (zero value-drift risk on the valuation logic); all the EN wording lives in
  one reviewable file. Keys are **LRM/zero-width-normalized** so they are robust against the
  engine's bidi-mark formatting; a live coverage test guards drift.
- **Number-interpolated strings → site-level `_en` twins** in a later slice (b80) — they
  have no `_en` here and fall back to `_ar` in EN mode until then.
- **Proper nouns** (landmark `name_ar`, `district_ar`) are intentionally not translated
  (fall back to `_ar`).

`attach_en` is **ADDITIVE-ONLY**: it never modifies an `_ar` or any value, and never clobbers
an existing engine-authored `_en` (e.g. the leadership/cost notes that already carry `_en`).
VALUE-INVARIANT by construction — amount/method/rule are not `_ar` fields, and the AR-default
frontend ignores the new `_en` keys.

## 3. What this patch does

- **`en_localize.py`** (new): `_norm()` (LRM/RLM/zero-width strip + whitespace collapse),
  `CATALOG` (135 entries, AR→EN, authored against the locked termbase — RICS clause numbers
  verbatim, "Ministry of Justice", "sales-comparison approach", "material uncertainty",
  "Standalone villa", the MUC clause, the RICS methodology note, the service-level statement,
  the refusal/disclaimer prose, the stratum labels/descriptions, …), and `attach_en(obj)`
  (recursive, best-effort, never raises).
- **`api.py`**: a guarded `from en_localize import attach_en` (`_EN_OK`, mirroring the
  `_MAIL_OK` discipline); `attach_en(result)` called inside `_attach_freshness` (the single
  seam both `/api/evaluate*` endpoints pass through); the `/api/scope` response wrapped with
  `attach_en`.
- **`evaluate_unified.py`** = the 2 version-string lines only.

The catalog was bootstrapped by a 5-agent translation Workflow (against the locked termbase)
for the result-screen prose, with the load-bearing legal/RICS strings + the labels authored
by hand; a build script normalizes the keys and a **live coverage test** drove completeness
to **0 constant misses**.

## 4. Verification

- **py_compile** `api.py` + `en_localize.py` + `evaluate_unified.py` → OK; `import api` OK
  (`_EN_OK=True`, the post-pass live).
- **Value-invariance unit** (production `attach_en` on a synthetic response): `attach_en`
  returns the same object; amount/low/high/method/rule UNCHANGED; every `_ar` value UNCHANGED;
  an existing `_en` is NEVER clobbered; plain values untouched; `_en` is ADDED only where
  cataloged (condition_note / label / reason); a non-cataloged `_ar` gets no `_en`.
- **Coverage** (live capture vs CATALOG): **128 constant covered, 93 correctly skipped
  (interpolated / proper-noun), 0 constant misses.**
- **Isolated** `test_sprint_2_22_0b78.py` **24/24** (the catalog + primitives, the additive
  value-invariance matrix, the LRM-robust keys, the load-bearing terms, the api.py wiring,
  the engine-version-only guard, the b77 infra intact).
- **DoD**: aggregator **395/395 MATCH** · security **16/16** · surface **45/45** · broad
  walk **134/134 ALL GREEN** (133→134; **1 R6/Lesson-2 re-point** — b77's test pinned its own
  exact `SPRINT_TAG = '2.22.0b.77'`, which the b78 bump breaks → relaxed to a version-agnostic
  format check; intent preserved, no assertion weakened).
- **R14 N/A by construction** — `index.html` is git-confirmed UNCHANGED (the b77 dormant
  toggle + AR rendering are byte-identical to v249); the §20.88 backend-only precedent. The
  live verification is the response gaining `_en` siblings + the 5-fixture VALUE gate.

## 5. Deployment

```
git -C "C:/Thammen" add deploy-v2-files ...
git -C "C:/Thammen" subtree push --prefix "deploy v2" heroku master
git -C "C:/Thammen" push origin master
```

## 6. Post-deploy verification

```
curl -s https://thammen.qa/api/health    # engine = thammen-sprint2p22p0b78-en-backend-catalog
# 5-fixture VALUE byte-gate (browser-UA POST) must be byte-identical to v248/v249:
#   54/541/6=2,400,000 cost_led · 56/647/6=3,800,000 geo_full · 55/296/13=2,600,000 e25_capped
#   56/565/21=2,400,000 matched · 52/903/90=refusal
# AND the response must now carry _en siblings, e.g. condition_note_en / label_en / reason_en.
```

## 7. What's NOT in this patch (scope boundary)

- **No string wiring** — the frontend still renders Arabic; the result screen's `pick()`
  calls land in b79. The catalog is dormant content (the response gains `_en`, unused by the
  AR-default frontend).
- **No interpolated twins** — the number-interpolated notes/source/assumptions get site-level
  `_en` twins in b80; for now they fall back to `_ar` in EN mode.
- **No engine / methodology change** — value-invariant; the 5-fixture VALUE gate is untouched.

## 8. Next

- **b79** — wire the core flow (gate / home / form / `showConfirm` / `show` + scope modal) via
  `t()` (inline EN literals for the static HTML) + `pick()` (the cataloged backend `_en`) + the
  per-component `.lang-en` LTR overrides. The reveal flag stays off.
- **b80** — the number-interpolated site `_en` twins + the reports (`showReport` /
  `showShortReport`).
- **reveal** — flip `EN_ENABLED=true` once coverage is complete + the PO has reviewed the EN
  wording (`en_localize.py` is the wording review surface).
