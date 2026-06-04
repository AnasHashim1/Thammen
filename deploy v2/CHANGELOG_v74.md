# CHANGELOG v74 — Sprint 2.22.0a.22 (B-1.1): multi-AI-validated framing tweaks

**Engine:** `thammen-sprint2p22p0a22-b1p1-framing-copy` · **SPRINT_TAG** `2.22.0a.22` ·
**api/health** `3.1.0-sprint2.22.0a.22` · **date** 2026-06-04
**Files changed:** `evaluate_unified.py` (4 note constants + 2 widened `method_label_ar` + version) ·
`test_sprint_2_22_0a21.py` (copy guards refreshed) · `test_sprint_2_22_0a22.py` (new, 15 checks) ·
`CHANGELOG_v74.md`
**Class:** copy-only — **VALUE-INVARIANT**; **RICS/IVS citation tokens UNCHANGED**. Signed B-1.1 (the
multi-AI D3 adjudication). Record: `docs/MULTI_AI_VALIDATION_BATCH_SprintB1.md`.

---

## 1. Why this matters
The B-1 (a21) D3 multi-AI round (GPT-5 + Gemini) was **FIRED & ADJUDICATED**, not passed-by-consensus:
both models wanted to renumber the four 2025-revised VPS citations back to their pre-2025 priors;
**Claude.ai primary-source verification (RICS/IVSC 2025) rejected the renumbering — the live citations are
correct, NO CHANGE.** What the round DID surface (and Anas accepted) = **three value-invariant framing
tweaks** that make the disclosure read as an *analytical decomposition*, not a second valuation basis.

## 2. Root cause (framing, not a defect)
a21's strings read "land **value**" / "implied building **value**" — which a non-expert can read as a
*determination* (a standalone land valuation) or a real building value. The honest framing: the land floor
is an **indicative component on a highest-and-best-use premise**, and the implied building is a
**computational contribution / mathematical allocation** — neither is a field-verified value.

## 3. What this patch does (copy-only)
- `LAND_FLOOR_NOTE_AR/EN` → "indicative land component … on a highest-and-best-use **premise**; not a
  standalone valuation of the land" / «مكوّن الأرض الاسترشادي … على أساس **افتراض** الاستخدام الأمثل؛ وليس
  تقييماً مستقلاً للأرض».
- `IMPLIED_BLDG_NOTE_AR/EN` → "implied building **contribution** (computational residual…) — a **mathematical
  allocation**, not field-verified" / «**مساهمة** البناء الضمنية … **تخصيص حسابي**، غير مُتحقَّق ميدانياً».
- Widened `method_label_ar` (both variants, `evaluate_unified.py:1058` + `:1071`) → «**منهج المقارنة
  بالمبيعات** (مجموعة موسَّعة جغرافياً)…» — names the recognised approach instead of «مقارنة بتوسيع
  جغرافي». (Rule #39: the signed string was given for the widened path; applied to BOTH widened variants
  [standard + «— شواهد محدودة» indicative] for label consistency; value-invariant.)
- **UNCHANGED:** the citation constants (`VPS 3/IVS 103`, `VPS 2/IVS 102`), the `land_anchored` note, the
  helper logic, the `~value~` 10k display-rounding, and **every headline value/range/method/tier/MUC**.
- `ENGINE_VERSION`/`SPRINT_TAG` → a22. `api.py` + `index.html` UNTOUCHED (strings render in the unchanged
  a17 `.rn` block; **R14 N/A by construction** — git-confirmed `index.html` 0-diff — plus a Chromium
  390×844 re-measure of the new longer strings, below).

## 4. Verification — empirical evidence
- **Isolated:** `test_sprint_2_22_0a22.py` **15/15** (citation tokens **byte-identical** + NO rejected
  renumbering leaked + new framing verbatim + old framing gone + value-invariance [no amount key, floor
  exact] + LRM + no-Latin + widened method_label new/old-gone); `test_sprint_2_22_0a21.py` **33/33** (copy
  guards refreshed to a22; all F1/F2/anchored/gate logic unchanged).
- **DoD matrix:** aggregator **392** · security **15/15** · surface-honesty **45/45** · broad auto-walk
  **65/65** (was 64; +1 a22 test; genuine clean pass).
- **R14 (executed):** `index.html` git-unchanged (0-diff) → JS syntax unchanged; the new (longer) strings
  render in the a21-proven unconstrained `.rn` block — real Chromium 390×844 re-measure: `scrollW==clientW`,
  no `overflowX`.
- **Live smoke v161 (browser-UA #61):** anchors byte-identical to a21 (2.4M/5.4M/2.6M/3.8M/refusal); the
  new wording + unchanged citations present; widened label updated.

## 5. Deployment
```
cd /d "C:\Thammen\deploy v2"
git add evaluate_unified.py test_sprint_2_22_0a21.py test_sprint_2_22_0a22.py CHANGELOG_v74.md
git commit -m "Sprint 2.22.0a.22 (B-1.1): multi-AI framing tweaks (value-invariant; citations unchanged)"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 6. Verification curl (post-deploy, browser-UA #61)
```
curl -s -X POST https://thammen.qa/api/evaluate -A "Mozilla/5.0 ... Chrome/120 Safari/537.36" ^
  -H "Content-Type: application/json" -d "{\"zone\":56,\"street\":647,\"building\":6}" > out.json
findstr /C:"مكوّن الأرض الاسترشادي" out.json
findstr /C:"VPS 3 / IVS 103" out.json
```

## 7. What's NOT in this patch
- The citation **numbers** (UNCHANGED by design — the models' renumbering was rejected by adjudication).
- Any **value/headline** change (byte-identical). Any condition **adjustment** or **Special Assumption**
  (→ B-2; B-1 keeps disclose-don't-assume). `stock_strata` a18-alignment (→ R15 §5 audit, separate).
- The verbatim GPT-5/Gemini transcript (appended by Anas to the validation record).
