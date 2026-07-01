# CHANGELOG v169 — Sprint 2.22.0b.88 «كشف زرّ الإنجليزية» (EN reveal + result-family static-chrome completion)

**Engine:** `thammen-sprint2p22p0b88-en-reveal` · **SPRINT_TAG** `2.22.0b.88` · **api-health** `3.1.0-sprint2.22.0b.88`
**Files:** `index.html` (EN_ENABLED=true + result-family static chrome to data-en/t()/pick() + version-independent) · `evaluate_unified.py` (version bump only) · `test_sprint_2_22_0b88.py` (NEW)
**Class:** 🟢 FRONTEND-ONLY / **VALUE-INVARIANT** — AR is the default (`LANG='ar'` unless the user picks EN), every AR literal preserved (as the `data-en` element's content, or as the `t()`/`pick()` AR arg) → AR render byte-identical. `api.py` + the valuation engine UNTOUCHED. The 5-fixture value byte-gate is unaffected (display language only; no amount/method/rule touched).

## 1. Why this matters

The PO signed off the EN wording and asked for the reveal: **"i approve the wording for now, please i need to see the english button"** (2026-07-01). The b77 language-toggle infrastructure has been built DORMANT behind `EN_ENABLED=false` across b77→b87 (primitives → backend catalog → core flow → short report → full report → confirm → result screen → backend `_en` twins). b88 flips `EN_ENABLED=true` so the toggle goes live.

But b79 explicitly scoped its STATIC i18n to **gate / home / form ONLY**; the result-family screens' static wrapper chrome (nav buttons, the results disclaimer, the copy/print buttons, the scope-badge labels) was never given `data-en`/`t()`. Revealing the toggle on top of Arabic static chrome would ship a mixed AR/EN screen — the exact "partial EN = a deficiency" the b77 comment warns against. So b88 also completes that visible static chrome, so the revealed button lands on a genuinely English screen.

## 2. What this patch does

**The reveal (1 line):** `var EN_ENABLED=false;` → `var EN_ENABLED=true;`. This alone: `_mountLangToggle()` (guarded on EN_ENABLED) now mounts the `.lang-toggle` pill on the home header, the consent gate, and every working-screen top-bar; `setLang('en')` works; a stored 'en' choice is restored on load. **AR stays the default** — `LANG=(EN_ENABLED&&_langStored()==='en')?'en':'ar'` → a fresh user (no stored choice) gets AR, byte-identical.

**Result-family static chrome (b79's deferred remainder), AR preserved:**
- **Nav buttons** → `data-en` added, AR text kept as the element content (so `_applyStaticI18n` captures `data-ar0` and restores AR exactly): «→ تقييم جديد» ×2 (confirm+results) → "← New valuation"; «→ رجوع للنتيجة» ×2 (refine+report) → "← Back to result"; «→ التفاصيل الكاملة» (short) → "← Full details".
- **Results disclaimer (`.disc`)** → each Arabic advisory line wrapped in a `<span data-en>` (indicative / not an official valuation / recommend a certified valuer >QAR 5M) + the Terms link + the CC-BY intro line. The mandatory CC BY 4.0 `.src-credit` (a25) is already bilingual and untouched. EN mirrors established phrasing (the Terms modal + the b83 "not a certified valuation" hero line).
- **Copy / print buttons** → `t('نسخ النتيجة','Copy result')`, `t('طباعة / حفظ PDF','Print / save PDF')`.
- **Scope badge** → the 4 labels `t()`-wrapped («تحليل آلي»→"Automated analysis", «تقييم مشروط»→"Conditional valuation", «خارج النطاق»→"Out of scope", «غير مدعوم بعد»→"Not yet supported"); `ss.label_ar`→`pick(ss,'label')` and `ss.methodology_ar`→`pick(ss,'methodology')` (graceful AR now, EN when the backend twins land — b89+).

**Personas (PO standing directive).** Linguist: professional English, register-consistent with the b78–b87 catalog. Lawyer: the disclaimer carries every AR protection faithfully (indicative · not an official valuation · does not replace a certified valuer · certified-valuer recommendation >QAR 5M · CC BY 4.0), no weakened claim, no new disclaimer; the mandatory MoJ attribution is unchanged.

## 3. Honest residual (Rule #42) — carried to b89+

On reveal, EN mode renders **all chrome in English** (gate, home, form, top-bars, nav/copy/print buttons, scope badge, hero, range, MUC chip, evidence panel, "how we got", financing calculator) **plus** the b84–b87 note bodies English against the LIVE b87 engine (decomposition, strata, brief section titles, cost/scenario assumptions). The **deep engine-authored note BODIES still fall back to Arabic** (graceful `pick()` fallback) until their backend `_en` twins are authored — the b89+ list: the freshness subtitle (`data_freshness.py`), the MUC clause + basis (`material_uncertainty.py`), the methodology_note, service_scope `label`/`methodology`, the brief-content bullets (risks / questions-to-ask), reasoning_trace known-unknowns, income `cap_rate_label`/`rent_source`, tier-breakdown `role`/`source`, market-position `description`, rics-note. Area names («امريخ الجنوبي») + the brand («ثمّن») stay Arabic **by design** (proper nouns). So the reveal is a **mostly-English, honestly-partial** first release — accepted by the PO's "for now"; the residual is the next work.

## 4. Verification — empirical evidence

- Isolated `test_sprint_2_22_0b88.py` **34/34** — EN_ENABLED=true; AR-default init line intact; the b77 primitives/toggle infra intact; every nav button + the disclaimer + copy/print + the 4 scope labels wrapped with the AR preserved; `pick(ss,'label'/'methodology')`; the src-credit + b83 hero t() untouched.
- **R14 real-Chromium 390×844** (live preview, `.basket/f_marikh.json`): the "English"/"العربية" pill mounts on home + gate + all 6 top-bars; **AR is the default** (`dir=rtl`, "→ تقييم جديد", original disclaimer); clicking the pill flips to EN (`dir=ltr`, "Value your property in Qatar", "← New valuation", "Copy result", "Print / save PDF", "Automated analysis" badge, the English disclaimer); result/report/short-report/confirm all render in EN without error; **AR restores byte-identical** after clearing the stored choice; **no horizontal overflow** (390==390); **0 console errors** across the whole session.
- DoD: aggregator **ALL COUNTS MATCH** · security **16/16** · surface honesty **45/45** · broad walk **144/144 ALL GREEN** — **10 R6/Lesson-2 re-points** (b77–b83 flipped their `EN_ENABLED=false` dormancy pin → `=true`, the reveal being the whole point + the AR-default byte-identity they protect still holds; b29 short-report button + b36 scope label/methodology + a3 surface-honesty «تحليل آلي» pins allow the added `data-en`/`t()`/`pick()`; **zero value/security/methodology assertion weakened**).

## 5. Deployment

```
git push origin master
git -C "C:/Thammen" subtree push --prefix "deploy v2" heroku master
```

## 6. Verification curl (post-deploy)

```
curl --compressed -s https://thammen.qa/api/health    # engine = …b88
```
+ served `index.html` carries `var EN_ENABLED=true;` + the 5-fixture value byte-gate byte-identical to the b87 release (54/541/6 2,400,000 · 56/647/6 3,800,000 · 55/296/13 2,600,000 · 56/565/21 2,400,000 · 52/903/90 None).

## 7. What's NOT in this patch (carried forward, Rule #42) — b89+

The backend `_en` twins for the deep note bodies (§3 residual list) — each needs a per-field consumption-recon then an additive `*_en` twin (`data_freshness.py` subtitle/caveat first, since it's on the first frame). Then EN mode is fully English (bar the by-design Arabic proper nouns). The reveal is trivially reversible (flip `EN_ENABLED` back) and AR users are unaffected (AR default; EN is opt-in via the toggle).
