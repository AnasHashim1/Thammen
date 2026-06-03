# CHANGELOG v71 — Sprint 2.22.0a.19: Thin-path condition caveat (path-complete)

**Engine:** `thammen-sprint2p22p0a19-thin-path-condition-caveat` · api/health `3.1.0-sprint2.22.0a.19`
**Date:** 2026-06-03
**Files:** `evaluate_unified.py` (predicate broadening + ENGINE_VERSION/SPRINT_TAG + comments), `test_sprint_2_22_0a17.py` (1 stale case flipped), `test_sprint_2_22_0a19.py` (new, 22 checks), `.gitignore` (new — git hygiene, scratch families), `CHANGELOG_v71.md`, `docs/Session_Log.md` (§20.19)
**Type:** COPY-ONLY / honesty-additive — **NO valuation logic; every value byte-identical.** Extends the a17 condition caveat to be path-complete. `api.py` + `index.html` UNTOUCHED (backend-only; the render at `index.html:936` is method-agnostic — it keys on field presence, so the note auto-surfaces on the newly-covered paths).

---

## 1. Why this matters

Sprint 2.22.0a.17 attached a bidirectional **condition-not-assessed** caveat to villa/house valuations — but scoped it to the **clean `comparison_bracket`** point only. Sprint 2.22.0a.18 then moved Marikh (54/541/6) onto the **`comparison_thin`** path at ~5.4M (correct same-district pool). Result (verified live, browser-UA, this session): **Abu Hamour 56/565/21 (bracket) carries `valuation.condition_note_ar/en`; Marikh 54/541/6 (thin) does NOT** — the subject that most needs the disclosure (a worn/plain villa over-anchored by R7) was the one missing it.

Root of the gap: a17's comment claimed "thin already disclose[s]." That conflated the **thin SAMPLE-size caveat** (few comps → less reliable) with a **CONDITION disclosure** (we did not assess THIS property's renovation/wear). They are **orthogonal**. Condition-blindness (RISK_REGISTER **R7**, bidirectional) is **method-agnostic** — the engine never assesses subject condition on ANY path.

## 2. Root cause (in code)

`_condition_note_applies(primary, gate, asset_type, amount)` ([evaluate_unified.py](evaluate_unified.py)) gated on `primary.get('method') == 'comparison_bracket'`. So `comparison_thin`, `comparison_preliminary`, and **non-dispersed** `comparison_widened*` returned `False` → no condition note, even though none of those surfaces carries a condition disclosure.

The only surfaces that DO already disclose condition are the **dispersion-GATED** pools: the a14 dispersed-bracket and a10 dispersed-widened honest-range, whose text explicitly states *"built type and condition are not yet confirmed"* ([evaluate_unified.py:4869–4881](evaluate_unified.py:4869)). That disclosure fires exactly when `_stage1_dispersion_gate` returns `gated=True`.

## 3. What this patch does — broaden the method gate, keep the `gated` exclusion

One-constant change. Replace the single-method literal with the set of **value-bearing villa/house comparison surfaces**, and keep the existing `gate.get('gated')` exclusion — which now does the routing work:

```python
_CONDITION_NOTE_METHODS = (
    'comparison_bracket', 'comparison_thin', 'comparison_widened',
    'comparison_widened_indicative', 'comparison_preliminary',
)

def _condition_note_applies(primary, gate, asset_type, amount) -> bool:
    if not primary or primary.get('method') not in _CONDITION_NOTE_METHODS:
        return False
    if asset_type not in ('standalone_villa', 'house', 'villa'):
        return False
    if amount is None:
        return False
    if gate and gate.get('gated'):
        return False  # dispersed bracket (a14) / widened (a10) → honest-range already discloses condition
    return True        # clean bracket / thin / non-dispersed widened / preliminary → include
```

Because `_stage1_dispersion_gate` returns **`None` for thin/preliminary** (neither bracket nor widened), those reach the predicate with `gate=None` → the fail-safe-to-disclosure branch → note included. Dispersed bracket/widened still return `gated=True` → excluded → routed to their existing a14/a10 honest-range disclosure. **The note never duplicates an existing condition disclosure, and never appears twice on one surface.**

Net coverage (villa/house, amount present):

| Surface | a17 | a19 | Why |
|---|---|---|---|
| clean bracket (gate not gated) | note | note | unchanged |
| **thin** (gate None) | — | **note** | **the fix — Marikh 54/541/6** |
| preliminary (gate None) | — | note | path-complete |
| non-dispersed widened (gate not gated) | — | note | path-complete |
| dispersed bracket (a14, gated) | — | — | a14 honest-range already discloses condition |
| dispersed widened (a10, gated) | — | — | a10 honest-range already discloses condition |
| land / apartment / commercial / refusal | — | — | asset_type / no amount |

**Wording UNCHANGED** (`CONDITION_NOTE_AR/EN` byte-identical to a17; the note reads "...may sit above/below this point" — method-agnostic). **No new strings, no Rule #54 round** (same signed copy).

## 4. Verification — empirical evidence

- **py_compile:** `evaluate_unified.py` OK.
- **Isolated (Rule #40/E14 — imports the PRODUCTION predicate + method tuple):** `test_sprint_2_22_0a19.py` **22/22** (clean bracket invariant held; thin/preliminary/non-dispersed-widened → note; dispersed bracket+widened → excluded; land/apt/commercial/amount-None excluded; fail-safe gate-None/malformed → include; house/villa aliases; method-set sanity; verbatim AR/EN). `test_sprint_2_22_0a17.py` **15/15** (the single now-stale assertion — thin → PRESENT — updated; all other a17 invariants intact).
- **DoD matrix:** aggregator **392/392** · security **15/15** · surface-honesty **45/45** · broad **62/62** (genuine clean pass; was 61 at a18, +1 = `test_sprint_2_22_0a19.py`).
- **Local E2E (live GIS, production `evaluate_thammen`):**
  - Marikh 54/541/6 → standalone_villa, amount **5,400,000** (= a18, **unchanged**), `condition_note_ar` **PRESENT** ← the fix.
  - Abu Hamour 56/565/21 → standalone_villa, amount **2,400,000** (= a18, **unchanged**), note PRESENT (no regression).
  - 52/903/90 → apartment_building, amount None, note **absent** (refusal control).
- **Zero value drift:** the predicate only attaches `condition_note_ar/en`; it never reads/writes `amount`/`low`/`high`/`central_estimate`. Confirmed structurally (diff) + by the live E2E amounts above.
- **§5 UI-FIRST / R14:** `index.html` UNTOUCHED (git-confirmed) — the note render is method-agnostic, so it surfaces on the thin path automatically. Backend-only → `node --check` + mobile 390×844 are N/A **by construction** (no `index.html`/JS change).

## 5. Deployment

```
cd /d "C:\Thammen\deploy v2"
git add "deploy v2/evaluate_unified.py" "deploy v2/test_sprint_2_22_0a17.py" "deploy v2/test_sprint_2_22_0a19.py" "deploy v2/.gitignore" "deploy v2/CHANGELOG_v71.md" "deploy v2/docs/Session_Log.md"
git commit -m "Sprint 2.22.0a.19: thin-path condition caveat (path-complete)"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 6. Verification curl (post-deploy)

```
curl -s -A "Mozilla/5.0 ... Chrome/120 Safari/537.36" -X POST https://thammen.qa/api/evaluate -H "Content-Type: application/json" -d "{\"zone\":54,\"street\":541,\"building\":6}"
:: expect valuation.amount 5,400,000 (unchanged) + valuation.condition_note_ar PRESENT  ← thin path now caveated
curl -s -A "Mozilla/5.0 ... Chrome/120 Safari/537.36" -X POST https://thammen.qa/api/evaluate -H "Content-Type: application/json" -d "{\"zone\":56,\"street\":565,\"building\":21}"
:: expect 2,400,000 (unchanged) + condition_note_ar PRESENT (no regression)
curl -s ... https://thammen.qa/api/health   :: expect 3.1.0-sprint2.22.0a.19
```

## 7. What's NOT in this patch (Rule #42)

- **The durable R7 fix = Sprint B** (built-type/condition axis via 2.22.0b Stage-2 input). This caveat **discloses** condition-blindness; it does not **solve** it. Marikh's ~5.4M still over-anchors a plain/worn villa (defensible ~3.0–3.4M) — now disclosed on the thin path, fixed only by B.
- **No wording change / no new copy decision** — reuses the a17 verbatim strings (already signed). The «التقدير السوقي» output term remains PROVISIONAL.
- **`comparison_preliminary` (n<5)** is included for path-completeness but is rare in practice (already heavily accuracy-warned).
- **`.gitignore`** is a co-shipped git-hygiene item (regenerable per-sprint scratch families), not part of the engine change.
- **A7** (`rics_compliant` surfacing) — the queued next item; carries a copy sign-off.
