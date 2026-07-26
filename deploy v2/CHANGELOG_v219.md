# CHANGELOG v219 — Sprint 2.22.0b.148 «الأحافير الإنجليزيّة المرئيّة»

**Engine:** `thammen-sprint2p22p0b148-visible-en-fossils` · **SPRINT_TAG** `2.22.0b.148`
**Class:** 🟢 BACKEND-COPY + frontend read-fixes / **VALUE-NEUTRAL**
**Files:** `en_localize.py` · `evaluate_unified.py` · `index.html` · `test_sprint_2_22_0b148.py`
`api.py` **UNTOUCHED** · the valuation logic **UNTOUCHED** (only the 2 version-string lines
in `evaluate_unified.py` are non-copy).

---

## 1. Why this matters

The §20.144 full-site review measured the live EN version and found Arabic text still
leaking on surfaces the b140→b146 EN track had not reached. b148 closes the **measured**
ones, plus one **Arabic-side** defect the same review surfaced.

The headline is **(A)**: on **every apartment/tower refusal**, the brief's «الخطوات
المقترحة» section rendered an **English heading over a fully Arabic body**. That is the
first — and often only — screen an English-speaking user of an unsupported asset type
sees.

---

## 2. Root cause (measured, per item)

| # | Symptom | Root cause |
|---|---|---|
| **A** 🔴 | Refusal `next_steps`: English title, Arabic body | `content.note_ar` is **interpolated** (address/area/asset label) → the constant CATALOG cannot cover it; `content.options_ar` is a **list under an `_ar`-suffixed key** → invisible to BOTH the scalar `_ar` rule (`isinstance(v, str)`) and the b142/b145 bare-key array rule. The frontend also read `c.options_ar` raw. |
| **B** 🟡 | Short report shows «37 معاملة، منها 28 خلال 24 شهراً» in EN | `valuation.window_used` is a **bare key** not listed in `_BARE_EN_KEYS`; read raw at `index.html`. Its shape was **already** covered by the b146 window-split template. |
| **C** 🟡 | «Overall trend: غير محدد» in EN | the b146 bare-key rule already emits `label_en`; the result-screen line read `esc(tr.label)` raw. |
| **D** 🟢 | Refine group numbers render ١٢٣ in EN | the three `.gnum` spans had no `data-en`. |
| **E** AR | «افتراضات: تشطيب **ordinary** …» | the `assumptions_ar` templates interpolated the **raw English enum** into Arabic copy (3 sites). |

---

## 3. What this patch does

### `en_localize.py`
- **`_ARR_AR_KEYS = ('options_ar',)`** — a new, *surgical* `_ar`-suffixed ARRAY rule:
  a list-of-strings under an `_ar` key gets an index-aligned `{base}_en` twin
  (unresolvable items fall back to the Arabic item; never clobbers an engine twin).
- **`_BARE_EN_KEYS += 'window_used'`** — the b146 window-split template already matches
  its shape, so listing the key **is** the whole fix.
- **CATALOG +6** — the refusal-body constants (the two classification options + the
  implied-rent note and its three constant steps).
- **`_TEMPLATES` +1** — the interpolated «أكّد أو انفِ … {rent} ر.ق/شهر؟» option.

### `evaluate_unified.py`
- **`ASSET_TYPE_EN`** — the EN twin of `ASSET_TYPE_AR` (wording locked to the frontend
  `ASSET_EN` map, b80). Used **only** to emit the interpolated `note_en`.
- **`note_en`** emitted beside the classification-refusal `note_ar` (same interpolations —
  the b144 engine-emit pattern for interpolated strings).
- **`COST_FINISH_LABEL_AR` + `_finish_label_ar()`** — the Arabic display label of the
  finish enum, used at the **3** `assumptions_ar` sites. The **EN twin keeps the English
  enum** (it reads correctly there); `COST_RCN_BY_FINISH` (the value driver) is untouched.

### `index.html`
- `pickArr` gains an `_ar`-suffixed fallback (`o[base]` is still tried first → the
  b142/b145 bare-key callers are byte-identical).
- 4 read swaps: `pickArr(c,'options')` · `pickBare(v,'window_used')` ·
  `esc(pickBare(tr,'label')||trLabel(tr.label))` · `data-en` on the 3 `.gnum` spans.

---

## 4. Value-neutrality

`api.py` git-confirmed untouched; no valuation field is read, written, or derived; the
edits are display copy + read swaps. Local E2E on the cost-led villa **54/541/6**:
`amount 2,400,000 / low 2,400,000 / high 5,400,000 / comparison_thin / cost_led` — byte-identical.

---

## 5. Verification

- **isolated `test_sprint_2_22_0b148.py` — 47/47** (real `attach_en` + real
  `evaluate_unified` maps + the real `index.html` reads; incl. the unresolvable-array
  no-fire guard, the never-clobber guard, and the b142 bare-key regression guard).
- **DoD:** aggregator **ALL COUNTS MATCH** · security **16/16** · surface honesty **45/45**
  · broad walk **200/200 ALL FILES GREEN** (199→200).
- **2 R6/Lesson-2 re-points** (test-only, **zero assertion weakened**): `b147` H3 (an exact
  version-tag pin → version-agnostic — the recurring Lesson-2) · `b91` trend-chart (the
  label literal → the bilingual read; the chart structure + the honest suppressed path
  unchanged).
- `python -m py_compile` OK · `node --check` OK on all 4 inline script blocks.
- **Local E2E (live GIS):** the refusal emits `note_en` («Address 52/903/90 sits on a plot
  of 467 m², classified as "Apartment building" …») + `options_en`; the matched fixture
  emits `window_used_en`.
- **R14 real-Chromium:** **AR** — refusal body fully Arabic, **0 English leak**, window
  «37 معاملة، منها 28 خلال 24 شهراً», hero **٢٬٤٠٠٬٠٠٠**. **EN** — refusal body fully
  English, **0 Arabic leak**, window «37 transactions, of which 28 within the last 24
  months», trend «Unspecified», gnum `data-en` 1/2/3, hero **2,400,000**. **AR restore**
  byte-identical. **0 console errors**, no horizontal overflow.
- **Personas:** lawyer **APPROVE** (procedural/descriptive copy; no claim or disclaimer
  added or weakened; an EN user can now read *why* the refusal happened and *what* to
  provide → raises transparency). Linguist **APPROVE** (فصحى; the finish labels reuse the
  shipped terminology verbatim — «فاخر» / «راقٍ»; the EN follows the b78 locked termbase).

---

## 6. Deployment

```
git push origin master
git -C "C:/Thammen" subtree push --prefix "deploy v2" heroku master
```

## 7. Post-deploy verification

```
curl -s --compressed -A "Mozilla/5.0 … Chrome/120.0 Safari/537.36" https://thammen.qa/api/health
```
Expect `3.1.0-sprint2.22.0b.148`; the 5-fixture value byte-gate identical to v311; the
refusal response carries `brief.sections[next_steps].content.note_en` + `options_en`, and
the matched fixture carries `valuation.window_used_en`.

---

## 8. What's NOT in this patch

- The **`polygon`** English word inside two `geometric_factors` `evidence_ar` strings —
  measured **not rendered** on the fixtures (gated-out low-confidence / no-polygon
  returns); left per the b139/b144 dead-field discipline, logged as carried-forward.
- The Terms modal's AR-above-EN ordering in EN mode (a signed-text ordering question — PO).
- The remaining **folded / specialist-annex** engine `_en` twins (§20.113 consumption-recon
  families) and the straight-vs-curly apostrophe normalization.
