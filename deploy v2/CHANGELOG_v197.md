# CHANGELOG v197 — Sprint 2.22.0b.117 «إكمال إنجليزيّة ملاحظات التقرير» (EN completion for the always-visible report note bodies)

**Engine:** `thammen-sprint2p22p0b117-en-report-notes` · **SPRINT_TAG** `2.22.0b.117` · files: `evaluate_unified.py`, `material_uncertainty.py`, `en_localize.py`, `test_sprint_2_22_0b117.py` (new), `CHANGELOG_v197.md` (new).
**Class:** 🟢 **FRONTEND/ENGINE-COPY — VALUE-INVARIANT** (additive `_en` twins only; every `_ar` value + amount/low/high/method/rule untouched; the 5-fixture villa byte-gate byte-identical).

---

## 1. Why this matters

Since the b88 EN reveal (`EN_ENABLED=true`), a Qatari-market user who switches to English gets a mostly-English report — but three **always-visible, engine-authored note bodies** still fell back to Arabic, because the b78 `en_localize` catalog is a *fixed* Arabic→English map and cannot match dynamic notes that interpolate a live number or date:

1. **`material_uncertainty.muc_basis` + `muc_review_recommendation`** — the "why the estimate carries material uncertainty" line (interpolates the MoJ latest-record date + days-old) and its review recommendation.
2. **`accuracy.explanation`** — the confidence-tier line (interpolates the sample count `n`), across all reliability tiers.
3. The **very-stale `data_freshness` caveat** — a static string that simply had no catalog entry yet.

These are on the **default landing**, not behind a fold, so a mixed AR/EN result was the first thing an EN user saw.

## 2. Root cause

- `en_localize.attach_en` (b78) only adds `{base}_en` when the normalized `{base}_ar` value is a key in the fixed `CATALOG`. Dynamic notes (`… {date} … {days} …`, `… {n} …`) never match → no `_en` → `pick()` falls back to `_ar`.
- The very-stale freshness caveat is static, but its exact Arabic string was simply missing from the catalog.

## 3. What this patch does

- **`material_uncertainty.regime_muc()`** — emits `muc_basis_en` + `muc_review_recommendation_en` beside the existing `_ar` (faithful English; names the Ministry of Justice + the days-old freshness fact + the review triggers). The `_ar` values are unchanged.
- **`evaluate_unified.py`** — adds an `accuracy.explanation_en` beside **every** `explanation_ar` tier (6 tiers: reliable / indicative-thin / very-thin / insufficient / plus the wide-range indicative tier), each interpolating `{n}` like its Arabic sibling and preserving the honest caveats ("may deviate ±10-15%", "certified valuer", "No valuation was produced").
- **`en_localize.py`** — adds the very-stale freshness caveat to the CATALOG (static Arabic→English).
- **`evaluate_unified._enrich_material_uncertainty` — the merge fix (completes the 3rd family live):** the regime_muc merge changed from `if v is not None and k not in out` to `if v is not None and out.get(k) is None`. A caller's `None` slot for `muc_basis_en` (pre-existing in the merged `mu` on the valued main path) was **shadowing** regime_muc's authoritative value — so `muc_basis_en` was dropped live while `muc_review_recommendation_en` (absent, not None) threaded. Filling `None`/absent slots is the correct merge semantics and is strictly additive (a `None` disclosure field takes regime_muc's real value; never overwrites a non-None value). Display-only → value-invariant.

**Scope discipline (#38/§20.113):** only the always-visible dynamic note bodies. Deeper engine `_en` twins for folded/specialist-annex fields (consumption-recon-first) remain deferred (§20.113).

## 4. Verification — empirical

- **py_compile** `evaluate_unified.py` + `material_uncertainty.py` + `en_localize.py` — OK.
- **Isolated `test_sprint_2_22_0b117.py` — 15/15** (E14, reads the real files): regime_muc emits `muc_basis_en` + `muc_review_recommendation_en` (English + faithful) with the `_ar` unchanged; 6 `explanation_en` beside 6 `explanation_ar` (dynamic `{n}`, honest caveats); `en_localize.attach_en` adds the freshness caveat `_en` from the catalog + never clobbers an existing `_en`; version = b117.
- **The merge fix proven:** `_enrich` with a `muc_basis_en=None` shadow (the live condition) now emits `muc_basis_en` (was dropped by `k not in out`).
- **DoD:** aggregator **ALL COUNTS MATCH** · security **16/16** · surface honesty **45/45** · broad walk **ALL GREEN** (the merge change touches every `_enrich` caller — zero re-points; a `None` disclosure slot becoming regime_muc's authoritative value weakens no assertion).
- **Personas (standing PO directive):** lawyer APPROVE (the EN carries the AR disclosure faithfully — no new claim, no weakened «ليس تقييماً معتمداً»); linguist APPROVE (فصيح, register-consistent with the b78–b113 catalog).

## 5. Deployment

```
git push origin master
git subtree push --prefix "deploy v2" heroku master
```

## 6. Verification curl (post-deploy, browser-UA #61)

```
curl -s --compressed -A "Mozilla/5.0 … Chrome/122 Safari/537.36" -X POST https://thammen.qa/api/evaluate \
  -H "Content-Type: application/json" -d '{"zone":54,"street":541,"building":6,"audience":"owner"}'
# expect: valuation.amount = 2400000 (byte-identical) ·
#   material_uncertainty.muc_basis_en present · accuracy.explanation_en present
```

## 7. What's NOT in this patch

- No value/methodology change (display-only, additive `_en`). The 5-fixture villa byte-gate is byte-identical.
- Folded/specialist-annex engine `_en` residue (consumption-recon-first families, §20.113) + the apostrophe normalization — deferred.
- The b117 first deploy (Heroku, accuracy + freshness families live) is superseded by this redeploy which completes the muc_basis family.
