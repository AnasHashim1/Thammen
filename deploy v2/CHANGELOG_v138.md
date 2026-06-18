# CHANGELOG v138 — Sprint 2.22.0b.57 «تحصين الواجهة» (frontend hardening: esc/XSS insurance + gate fallback + null-guards)

> Engine `thammen-sprint2p22p0b57-frontend-hardening-esc` · SPRINT_TAG `2.22.0b.57` · api-health
> `3.1.0-sprint2.22.0b.57`. **🟢 FRONTEND-ONLY / VALUE-INVARIANT** — `index.html` only; engine = the 2
> version-string lines; `api.py` + the valuation engine UNTOUCHED.
> **Files changed:** `index.html` · `evaluate_unified.py` (2 version lines) · `test_sprint_2_22_0b57.py`
> (new) · `test_sprint_2_22_0b41.py` (R6 re-point) · this CHANGELOG. Date: 2026-06-18.

## 1. Why this matters

The PO asked for a comprehensive code + bug audit of the production site. Three parallel read-only audits
ran across the backend/API, the engine, and the frontend, and **every candidate was verified against the
actual code**. Conclusion: the codebase is mature and well-guarded — most of the scan's "critical" flags
were **false alarms** (the identity helpers ARE defined `index.html:902-905`; the deadline token can never
be `None` — `set()` always returns a Token; `_income_triangulation` can't fire on a 0 rent — truthiness
guard `evaluate_unified.py:5679`; the leadership gate can't crash on a `None` cost — guarded `:6434`;
rate-limiting / `extra='forbid'` / the `/verify` HMAC constant-time + `html.escape` / the dormant
capture+mailer gating / `_scrub_personal` isolation all verified clean). The PO chose the **value-invariant
frontend hardening** scope. This sprint adds defense-in-depth + small robustness to `index.html`.

**Honest framing:** the XSS surface is **not live-exploitable today** — every backend field injected into
`innerHTML` is either built from integer-validated inputs (`address` = `{zone}/{street}/{building}`, `pin`
— all Pydantic ints, can't carry markup), GIS-government data (`district` = Districts-layer ANAME), or
engine-authored. The `esc()` helper is **insurance**: it future-proofs any free-text field and defends
against a tampered/MITM'd API response (the layout-review's flagged "esc() insurance").

## 2. What this patch does (frontend, value-invariant)

**(1) An `esc()` HTML-escape helper** (added next to `fmt()`): escapes `& < > " '`. **Applied to the
plain-data fields injected into `innerHTML`** (19 sites): `d.address`, `d.district`, the asset-label
(`ASSET_AR[...]` / `d.asset_type_ar`), the keystone neighbour `source_area`, and the comparable-row area.
**The engine-authored `*_ar` NOTE/CLAUSE fields are LEFT AS-IS** (`condition_note_ar`, `leadership.note_ar`,
`muc_ar`/`_mucCardHtml`, `hbu_note_ar`, … — they deliberately carry intended HTML `<b>`/`<span dir=ltr>`/`<svg>`
and are trusted our-engine output; escaping them would break the display). The clipboard `lines.push` text
path is untouched (already plain-text, not innerHTML).

**(2) Inline-onclick coordinate coercion** — `openMapPicker('+Number(lat)+','+Number(lon)+')` (2 sites) so a
non-numeric coordinate can't break the attribute.

**(3) Gate `window._betaAck` fallback** — the pre-paint hide script now honors the in-memory fallback
(`…==='1'||window._betaAck`) for the rare sessionStorage-unavailable case.

**(4) Null-guard robustness** — `value_stack.cost.label_ar`/`sub_ar` wrapped with `||''` (the `.value` guard
existed but the paired strings weren't re-guarded → prevents a literal "undefined" rendering).

**`evaluate_unified.py`** — `ENGINE_VERSION`/`SPRINT_TAG` → b57 (the 2 lines only).

## 3. Value-invariance contract

The frontend never recomputes the headline (no `v.amount/low/high =`); `esc()` only changes how plain-DATA
fields are written, not any figure; `api.py` + engine untouched → the 5-fixture value-invariance gate is
byte-identical to v228 by construction. The b55 clusters + b56 trim are intact.

## 4. Verification — empirical evidence

- **Isolated** `test_sprint_2_22_0b57.py` — **29/29** (esc defined + escapes `<>&"'`; applied at the
  address/district/asset/area sites + the raw forms absent; the engine `*_ar` notes NOT esc-wrapped
  [formatting preserved]; the gate fallback; the `||''` guards; the coord coercion; value-invariance; b55/b56
  no-regression; engine-format).
- **R6 re-point (test-only):** `test_sprint_2_22_0b41.py` E3 (the keystone neighbour `source_area` render →
  `esc(g.source_area)`) — ALL PASS; intent (area-name + ×factor shown) preserved.
- **DoD** (`PYTHONIOENCODING=utf-8`): aggregator `run_sprint_2p22p0a_suite.py` **ALL COUNTS MATCH** · security
  `test_sprint_2p16p17_security.py` **15/15** · surface `test_sprint_2p22p0a3_surface_honesty.py` **45/45** ·
  broad walk `2p22p0_pre/run_regression_2p22p0a.py` **116/116 ALL GREEN** (115→116, +b57; 113.3s).
- **R14 live Chromium 390×844** (served `index.html` + real `.basket/f_marikh.json`): value **٢٬٤٠٠٬٠٠٠**
  byte-identical · the MUC clause keeps its intended HTML (`<strong>`/`<b>` rendered bold, NOT shown literal
  → the engine `*_ar` notes are NOT broken) · data fields not double-escaped · no overflow (scrollW 390) ·
  **0 console errors**. **XSS PROBE** — injected `<img src=x onerror="window.__xss=1">` into `d.district` /
  `d.address` / `d.asset_type_ar`, rendered the report: **`window.__xss` stayed undefined (no execution)**,
  the tag was neutralized to `&lt;img…` in the HTML (no live `<img>` element), the payload shows as inert
  text, and the legit address `54/541/6` still renders. The esc() insurance works end-to-end.

## 5. Deployment

```
cd /d "C:\Thammen"
git add "deploy v2/index.html" "deploy v2/evaluate_unified.py" "deploy v2/CHANGELOG_v138.md" "deploy v2/test_sprint_2_22_0b57.py" "deploy v2/test_sprint_2_22_0b41.py"
git commit -m "Sprint 2.22.0b.57: frontend hardening — esc() XSS insurance + gate fallback + null-guards (value-invariant)"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 6. Verification curl (post-deploy, browser-UA — Rule #61)

```
curl -s https://thammen.qa/api/health | findstr /C:"2.22.0b.57"
curl -s https://thammen.qa/ | findstr /C:"function esc("
```
Plus the live 5-fixture value-invariance gate (browser-UA POST): 54/541/6 2.4M cost_led · 56/647/6 3.8M
geo_full · 55/296/13 2.6M e25 · 56/565/21 2.4M matched · 52/903/90 refusal — all byte-identical to v228.

## 7. What's NOT in this patch (deferred, per the PO's scope choice)

- The engine **b11 `_cost_reanchor_down` low>high range inversion** (`evaluate_unified.py:6068-6069`, the
  documented §20.50 micro-bug, rare 54/788/10-class) — value-touching, deferred pending a Gate-2 sign-off.
- **A5** (`asset_type='unknown'` no explanation) + the income_led/b13-trim decomposition-recompute gap —
  known backlog.
- The broader esc() sweep to the engine-authored plain `*_ar` strings (`requires_user_input_ar`,
  `rent_source_ar`) — they're trusted engine output; left to keep the change surgical.
- The engine-emitted Arabic-string polish («مُخترَع», number-unification, grammar) — a separate engine-copy
  pass with its own value-byte-gate.
- **No engine / value / methodology change** — `api.py` + the engine untouched; value-invariant.
