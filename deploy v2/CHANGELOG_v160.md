# CHANGELOG v160 — Sprint 2.22.0b.79 «ربط المسار الأساسيّ بالإنجليزية» (EN core-flow wiring)

> Engine `thammen-sprint2p22p0b79-en-coreflow-wiring` · SPRINT_TAG `2.22.0b.79` ·
> api-health `3.1.0-sprint2.22.0b.79`. **🟢 FRONTEND-ONLY / VALUE-INVARIANT** — the EN render
> is DORMANT behind `EN_ENABLED` (b77); the AR default is byte-identical (the `data-en`
> attributes + `.lang-en` CSS are inert until the flag flips). `api.py` + the valuation engine
> UNTOUCHED. Files: `index.html` (the wiring + mechanism + CSS), `en_localize.py` (the b78 MUC
> wording fix riding with this deploy), `evaluate_unified.py` (2 version lines),
> `test_sprint_2_22_0b79.py` (new), + R6 re-points on b54/b56/b77/b78, `CHANGELOG_v160.md`.
> **Third sprint of the EN-localization track — the core flow now RENDERS English.**

## 1. Why this matters

b77 shipped the i18n infrastructure; b78 shipped the backend EN content (the catalog +
`attach_en`). b79 **wires the core flow to actually render English**: the consent gate, the
home landing, the property-entry form, the top-bars, and the scope modal. With the flag flipped
(reveal sprint), a user can switch to English and walk the entry flow end-to-end in English.
Built DORMANT behind `EN_ENABLED` so the live AR site is unchanged. The PO reviewed the b78
wording and signed off (with 2 MUC clarity fixes applied here).

## 2. What this patch does

**The static-swap mechanism (`_applyStaticI18n`)** — the entry screens are static HTML, so each
translatable element carries a `data-en` (innerHTML) / `data-en-ph` (placeholder). On a language
flip, `_applyStaticI18n()` captures the original Arabic ONCE (`data-ar0` / `data-arPh`) and swaps
to/from the English. `setLang` now calls `_applyStaticI18n()` + `chk()` (refresh the status bar)
+ `_rerenderForLang()`. The audience buttons wrap only their TEXT in a `data-en` span so the SVG
icons are preserved.

**Wired (data-en):** the gate (title / consent note / affirmation / "I agree and continue" / Terms
link — reusing the wording from the gate's existing `bg-en` English fold, which is hidden in EN
mode); the home (tag / sub / 3 trust steps / "Start the valuation" / the MoJ credit line); the form
(tabs / labels / placeholders / the audience selector / "Value it" / the entry titles); the 5
static top-bar titles.

**Wired (JS `t()`/`pick()`, NOT data-en — these are JS-rendered):** the scope modal (`openScope`
now uses `pick(s,'label')`/`pick(s,'reason')`/`pick(d,'service_level')` off the b78 `_en` siblings
+ `t()` for the section headers, with a **LANG-keyed cache** so it re-renders on a switch); the
status bar (`chk()` uses `t()`). The JS-driven `statusBar` / `dfSubtitle` / `scopeContent` are
intentionally **not** `data-en` (a swap would clobber their dynamic content).

**A gate language toggle** — `_mountLangToggle` now also mounts a pill into `#betaGate .bgate-head`,
so an English user can switch **before** passing the (first-frame) consent gate.

**`.lang-en` dir-flip** — scoped to the entry screens only (`#betaGate` / `.bgate` / `#homeScreen`
/ `#formScreen` → `direction:ltr`; the form inputs/labels/titles → `text-align:left`; the gate's
`bg-en` fold hidden; the scope modal inner div → LTR). The **result/report screens are NOT flipped**
(they keep RTL until b80 wires them — their explicit `.thmr{direction:rtl}` also keeps them RTL
under the body's lang-en).

**Hardened dark guard** — `setLang` now **coerces** a flag-off EN request to AR
(`if(!EN_ENABLED&&l==='en')l='ar';`) so the dormant state always lands on Arabic.

**b78 MUC wording fix (rides with this deploy):** in the MUC clause EN, "Scope of the reservation"
→ "Scope of the material uncertainty" (lawyer-lens RICS consistency) and "a thinness in the volume"
→ "a limited volume" (linguist-lens). The catalog is dormant content — no separate redeploy needed.

## 3. Verification

- **py_compile** OK; **R14 real-Chromium 390×844** (served `index.html`):
  - **AR default (production, dormant)** — `EN_ENABLED=false`, `LANG='ar'`, `<html dir>='rtl'`,
    **0 toggles mounted**, all gate/home/form text Arabic, 41 inert `data-en` attributes, **no
    overflow** (scrollW 390), **0 console errors**.
  - **Forced EN** — `EN_ENABLED=true; _mountLangToggle(); setLang('en')` → `<html dir>='ltr'`,
    `body.lang-en`, **8 toggles** (6 top-bars + home + gate), the gate ("Thammen — Automated Market
    Valuation…", "I agree and continue", `bg-en` hidden), home ("Value your property in Qatar",
    "Start the valuation"), form ("Zone no." / placeholder "e.g. 70" / "Villa/building (address)" /
    "Owner" / "Value it"), gateDir/formDir = ltr, no overflow, **0 console errors**.
  - **Round-trip** `setLang('ar')` restores Arabic exactly (innerHTML via `data-ar0`, placeholder via
    `data-arPh`, `bg-en` reappears); EN↔AR stable; the hardened guard coerces a flag-off EN to AR.
- **Isolated** `test_sprint_2_22_0b79.py` **19/19** (the mechanism, the gate/home/form/top-bar
  `data-en`, the gate toggle, the JS `t()`/`pick()` scope+status wiring, the JS-driven-not-data-en
  exclusion, the entry-only dir-flip, the value-invariance/AR-intact guards).
- **DoD**: aggregator **395/395 MATCH** · security **16/16** · surface **45/45** · broad walk
  **135/135 ALL GREEN** (134→135). **R6/Lesson-2 re-points (4):** b54 ×3 + b56 ×1 pinned the exact
  `<div class="htag/hsub/tbar-st">TEXT</div>` form, which the additive `data-en` attribute changed
  (the TEXT is preserved + the old «تقدير» forms still absent) → relaxed to be attribute-tolerant;
  b77 (the guard string) + b78 (its own version pin) re-pointed too. No assertion weakened.

## 4. Deployment

```
git -C "C:/Thammen" add <b79 files>
git -C "C:/Thammen" subtree push --prefix "deploy v2" heroku master
git -C "C:/Thammen" push origin master
```

## 5. Post-deploy verification

```
curl -s https://thammen.qa/api/health    # engine = thammen-sprint2p22p0b79-en-coreflow-wiring
# 5-fixture VALUE byte-gate (browser-UA POST) byte-identical to v248–v250.
# served HTML carries: data-en="Value your property in Qatar" · _applyStaticI18n · the gate-lang mount
#   · and NO .lang-toggle / lang-en rendered (the toggle stays dormant behind EN_ENABLED).
```

## 6. What's NOT in this patch

- **No reveal** — `EN_ENABLED` stays false; the toggle never mounts in production; the live AR site
  is byte-identical. The flag flips only after the result/report screens are wired (b80).
- **The result / confirm / report screens are NOT wired yet** — they render Arabic in EN mode and
  keep RTL; wiring `show()` / `showConfirm()` / `showReport()` / `showShortReport()` via `t()`/`pick()`
  + their `.lang-en` overrides is **b80** (it leverages the b78 catalog directly).
- **The freshness subtitle** (`dfSubtitle`) stays Arabic in EN mode (it's `subtitle_ar`,
  number-interpolated → a site `_en` in b80) — a minor secondary line.
- **No engine / methodology change** — value-invariant; the 5-fixture VALUE gate is untouched.

## 7. Next

- **b80** — wire `show()` / `showConfirm()` / `showReport()` / `showShortReport()` via `t()`/`pick()`
  (the result family + reports) + their `.lang-en` LTR overrides + the number-interpolated site `_en`
  twins (leadership/cost notes, source counts, freshness). Then the EN renders end-to-end.
- **reveal** — flip `EN_ENABLED=true` (full dual-language R14 across all screens).
