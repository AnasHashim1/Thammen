# CHANGELOG v158 — Sprint 2.22.0b.77 «بنية تعريب الإنجليزية» (EN localization infrastructure)

> Engine `thammen-sprint2p22p0b77-en-localization-infra` · SPRINT_TAG `2.22.0b.77` ·
> api-health `3.1.0-sprint2.22.0b.77`. **🟢 FRONTEND-ONLY / VALUE-INVARIANT** —
> `index.html` only + the 2 engine version-string lines; `api.py` + the valuation
> engine logic UNTOUCHED. Files: `index.html`, `evaluate_unified.py` (2 lines),
> `test_sprint_2_22_0b77.py` (new), `CHANGELOG_v158.md` (new).
> **First sprint of the EN-localization track — the PO's #1 remaining launch item.**

## 1. Why this matters

The PO's #1 remaining launch item is a full **English version** (the §20.107 handoff:
«حتى النسخة الانجليزية»). The DEF-UX5 recon (§20.69) already classified it a **Gate-2
project**: ~201 client-side AR string lines in `index.html` + ~520 backend `_ar` fields
lacking an `_en` twin + a toggle infra + a dir-flip CSS layer + dual-language R14. The
hard constraint (§20.107): **a partial EN = a mixed AR/EN UI = a deficiency → it is NOT
half-shippable.** So the EN must be built across several sprints but never SHOWN to a user
until the coverage is complete + the PO has reviewed the wording.

This sprint ships the **infrastructure only**, built **DARK** behind a feature flag
(`EN_ENABLED=false`), so:
- every intermediate sprint deploys **value-invariant** (the live site stays byte-identical
  Arabic — the toggle never mounts, `LANG` is forced `'ar'`, `fmt()` stays `ar-QA`);
- the **reveal sprint** simply flips `EN_ENABLED=true` once the EN coverage lands + the PO
  signs off on the wording — the one moment EN goes live.

## 2. Root cause / starting point

`index.html` had **no i18n layer**: a single `fmt()` hardcoded to `'ar-QA'`, `<html lang="ar"
dir="rtl">` fixed, every user-facing string a bare Arabic literal, and only **static** English
mirrors in three spots (`.bg-en` gate fold, `.tmodal-body .en` Terms, `.src-credit .en` source
credit). There was no `LANG` / `t()` / `pick()` / `setLang()` / locale switch.

## 3. What this patch does (the dormant scaffold)

`index.html` (one cohesive block + 2 surgical edits + a CSS scaffold):

- **Primitives** (after the `TIER_LABEL_AR` const, before `go()`):
  - `var EN_ENABLED=false;` — the reveal sprint flips this `true`.
  - `var LANG=(EN_ENABLED&&_langStored()==='en')?'en':'ar';` — **forces AR while dark**,
    ignoring any stored choice (so a user who once picked EN in a future build still gets a
    clean AR site today).
  - `t(ar,en)` — translate an inline literal pair; AR is the guaranteed fallback when no `en`.
  - `pick(o,base)` — pick `o.{base}_en` in EN (if present) else `o.{base}_ar` off a backend
    object; AR fallback.
  - `_loc()` — active Intl locale (`'en-US'` Western vs `'ar-QA'` Arabic-Indic digits).
- **`fmt()`** routed through `_loc()`: `…toLocaleString(_loc())` → **byte-identical** when
  `LANG==='ar'` (returns `'ar-QA'`), `'en-US'` digits in EN.
- **`setLang(l)`** — dark-period guard (`if(!EN_ENABLED&&l==='en')return;`) then flips `LANG`,
  persists to `localStorage`, sets `<html dir/lang>`, toggles `body.lang-en`, re-syncs the
  toggle labels, and re-renders the active result-family screen (`_rerenderForLang()`).
- **`_mountLangToggle()` / `_syncLangToggle()`** — a small language pill mounted into every
  `.tbar` (×6) + a home slot; **`if(!EN_ENABLED)return;`** → never mounts in the dark build.
- **`DOMContentLoaded`** — restores a stored choice **only when `EN_ENABLED`**; otherwise a
  no-op (stays AR, no toggle).
- **CSS scaffold** (before `</style>`): `body.lang-en{direction:ltr;text-align:left}` root
  override + `.lang-toggle` pill + `.home-lang` slot — **inert** (no element carries these
  classes in the AR-only build).

`evaluate_unified.py` = the 2 version-string lines only. `api.py` UNTOUCHED.

**No string wiring this sprint** — every string stays Arabic. The per-string `t()`/`pick()`
wiring lands in later sprints; the dir-flip CSS overrides land alongside each wired component.

## 4. Verification — empirical evidence

- **py_compile** `evaluate_unified.py` + `api.py` → OK.
- **node --check** N/A (node absent) → R14 Chromium is the JS-parse gate (0 console errors).
- **Isolated** `test_sprint_2_22_0b77.py` **23/23** (E14, reads the real files): the dark-period
  default (EN off, LANG forced AR, mount + restore both gated), the four primitives, `fmt`
  routed through `_loc()` (old hardcoded-`ar-QA` fmt def gone), `setLang` dir/lang/body flips,
  the CSS scaffold, and the value-invariance guards (locked hero label «التقييم السوقي»,
  forced-sale honesty, b72/b75 copy intact, the existing local `const t` un-collided, engine =
  b77 version lines only).
- **DoD**: aggregator `run_sprint_2p22p0a_suite.py` **395/395 MATCH** · security
  `test_sprint_2p16p17_security.py` **16/16** · surface `test_sprint_2p22p0a3_surface_honesty.py`
  **45/45** · broad walk `2p22p0_pre/run_regression_2p22p0a.py` **133/133 ALL GREEN**
  (132→133, **zero re-points** — the i18n is purely additive and the `fmt` def change is
  value-invariant).
- **R14 real-Chromium 390×844** (served `index.html`):
  - **AR default (production)** — `EN_ENABLED=false`, `LANG='ar'`, `<html dir>='rtl'`, body has
    no `lang-en`, **toggle count = 0 (DORMANT)**, `fmt(1234)='١٬٢٣٤'` (Arabic-Indic, unchanged),
    all 8 functions parsed, **no horizontal overflow** (docScrollW 390 == innerW 390),
    **0 console errors**.
  - **Forced EN (scaffold proof)** — `EN_ENABLED=true; _mountLangToggle(); setLang('en')` →
    `LANG='en'`, `dir='ltr'`, `lang='en'`, `body.lang-en` present, **7 toggles mount**
    (6 `.tbar` [form/refine/confirm/results/report/shortReport] + 1 home), `fmt(1234)='1,234'`,
    `t('أصل','Asset')='Asset'`, `pick(…)='Villa'`, no overflow.
  - **Revert + dark guard** — `setLang('ar')` reverts cleanly (rtl / Arabic-Indic / no
    `lang-en`); with `EN_ENABLED=false` again, `setLang('en')` is a **no-op** (stays AR/rtl).

## 5. Deployment

```
git -C "C:/Thammen" add "deploy v2/index.html" "deploy v2/evaluate_unified.py" "deploy v2/test_sprint_2_22_0b77.py" "deploy v2/CHANGELOG_v158.md"
git -C "C:/Thammen" commit -m "Sprint 2.22.0b.77: EN localization infrastructure (dormant i18n scaffold) …"
git -C "C:/Thammen" subtree push --prefix "deploy v2" heroku master
git -C "C:/Thammen" push origin master
```

## 6. Post-deploy verification curl

```
curl -s https://thammen.qa/api/health    # engine = thammen-sprint2p22p0b77-en-localization-infra
# 5-fixture VALUE byte-gate (browser-UA POST, Rule #61) must be byte-identical to v248:
#   54/541/6=2,400,000 cost_led · 56/647/6=3,800,000 geo_full · 55/296/13=2,600,000 e25_capped
#   56/565/21=2,400,000 matched · 52/903/90=refusal
# served HTML must carry: var EN_ENABLED=false · function t(ar,en) · function pick(o,base) · _loc()
#   and NO «.lang-toggle» element rendered (toggle dormant).
```

## 7. What's NOT in this patch (scope boundary, Rule #38)

- **No string wiring** — every UI string stays Arabic. The per-string `t()`/`pick()` wiring +
  the per-component `.lang-en` LTR overrides are later sprints (b78 backend `_en` coverage,
  b79 core-flow wiring, b80 reports wiring).
- **No visible toggle** — the language pill is built but dormant behind `EN_ENABLED=false`;
  the reveal sprint flips the flag (final EN sprint) once coverage + PO wording sign-off land.
- **No engine / methodology change** — value-invariant; the 5-fixture VALUE gate is untouched.

## 8. Next

- **b78** — backend `_en` coverage: author every missing `*_en` twin across `evaluate_unified.py`
  / `output_briefs.py` / `scope_of_service.py` / `refusal_templates.py` / `data_freshness.py` /
  `material_uncertainty.py` (the ~520 `_ar`-only fields); an isolated test asserts every
  user-facing `_ar` has an `_en`. Value-invariant (the AR default never reads `_en`).
- **b79** — wire the core flow (gate / home / form / `showConfirm` / `show` + scope modal) via
  `t()`/`pick()` + the `.lang-en` overrides.
- **b80** — wire the reports (`showReport` / `showShortReport`) — high-risk nested HTML; keep
  the LRM / `dir=ltr` numeric islands.
- **reveal** — flip `EN_ENABLED=true` once coverage is complete + the PO has reviewed the EN
  wording (the one sprint where EN goes live; full dual-language R14).
