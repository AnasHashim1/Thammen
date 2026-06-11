# CHANGELOG v105 — Sprint 2.22.0b.22: tower-pair fence (سياج زوج الأبراج)

**Engine:** `thammen-sprint2p22p0b22-tower-pair-fence` · **SPRINT_TAG:** `2.22.0b.22` · **Date:** 2026-06-11
**Files:** `evaluate_unified.py` (+helper, fenced call-site, 2 attach sites, version) · `index.html` (syncTowerPair + requires-line gate + disclosure chip) · `test_sprint_2_22_0b22.py` (new, 63 checks) · `test_sprint_2p16p10_tower_split.py` (stale sync-pin re-pointed) · `api.py` **UNTOUCHED**.
**Classification:** 🔴 micro Gate-2 (value-affecting ONLY on the previously-unguarded pair-on-non-tower inputs) — **SIGNED** (the PO contract enumeration, 2026-06-11); Gate-1 on explicit «go».

-----

## 1. Why this matters

Phase-0 (`docs/PHASE0_income_types_exposure.md` §4) measured the worst live back-door since b21: the Sprint 2.16.10 **(unit_count × avg_monthly_rent_per_unit)** pair — designed for towers/compounds — was multiplied into `rental_income` **for ANY asset type**. On villa 54/541/6 the pair (12×5,000) became a laundered «إيجار العقار الفعلي» → b6 `income_led` drove the headline to **11,200,000** against the signed **2,400,000 cost-led** (×4.7), with the b6 cost-ceiling rail inert (no footprint, §20.55) and the derivation provenance lost. A measured UI leak made it reachable with **zero typing**: the pair persisted across evaluations (apartment → villa) because `applyAssetToForm` only ran from the insufficient-data CTA and the payload builder sends the pair unconditionally.

## 2. Root cause

- `evaluate_unified.py` (pre-b22 :3818-3838): the derivation block ran before any asset gating — `if unit_count and avg_monthly_rent_per_unit: rental_income = _derived_total` regardless of `_qtype`. The documented §19 rule («if asset_type in TOWER_LIKE_TYPES …») never existed in code (doc-vs-code gap, #58 → RISK_REGISTER R20).
- `index.html`: `applyAssetToForm` called only from `goForm` (:610); no clearing of `#unitCount`/`#avgRentPerUnit` between evaluations; builder (:968) sends the pair whenever both fields hold values, visible or not.
- Stale qualifier: the scope banner's «يتطلب: …» line rendered unconditionally — still demanding the rent ABOVE a successful income valuation.

## 3. What this patch does

**Backend (`evaluate_unified.py`):**
- New pure `_derive_rent_from_unit_pair(qtype, unit_count, avg, rental_income)` + `_TOWER_PAIR_ASSETS = {tower, apartment_building, compound_large, compound_small, commercial_building}` + the verbatim disclosure constants. Tower-like + complete pair → derivation **byte-identical** to pre-b22 (same strings, same precedence over a bare rent). Non-tower (villa/house/land/unknown/None) + complete pair → the pair is **IGNORED**: `rental_income` is never overwritten (a bare rent proceeds exactly as a pair-less request — the b6 path untouched) and a `tower_pair_ignored` flag carries «**مدخل برجي على أصل غير برجي — تم تجاهله**» + the pair + the asset type. Incomplete pair → legacy behaviour byte-identical.
- **Membership note (#39):** `compound_small` IS in the allowlist — an address-entry large compound is quick-classified compound_small (subtype 2/3; the E20 extent promotion runs AFTER the DCF fork), so excluding it would have moved the contract's byte-identical compound behaviour. `commercial_building` kept per the literal §19 list (no classify branch emits it on this path today).
- Scope-safe init + two attach sites: the Gate-3 MoJ-thin fast route (`result['tower_pair_ignored']`) and the full-path output (`output['tower_pair_ignored']`).

**Frontend (`index.html`):**
- `syncTowerPair(assetType)` runs on EVERY `show()`: `applyAssetToForm` + **clears** the pair when the asset isn't tower-like → kills the cross-evaluation stale-leak vector.
- The «يتطلب: …» line renders only when `!hasValuation` (drops once the requirement is met; the scope banner itself stays).
- An ignored-pair disclosure chip (warn-bg, above the number) renders `tower_pair_ignored.note_ar` for API-direct/legacy payload cases.

## 4. Signed contract → measured outcome

| بند العقد | النتيجة |
|---|---|
| fixtures/bare paths byte-identical | villa bare = 2,400,000 cost-led [2.4M…5.4M] ≡ b20 fixture; bare requests never enter the fence |
| فيلا/بيت/أرض + الزوج ⇒ يُهمل + إفصاح، لا income_led | villa+pair = 2.4M cost-led byte == bare · no `income_led` · `user_inputs.rental_income=None` · verbatim note |
| b6 bare-rent path untouched | villa + pair + bare 9,000 → bare survives, `user_total` byte-identical |
| عمارة/برج + الزوج بايت-مطابق | 52/903/90 + 12×5,000 = **8,529,231** · NOI 554,400 @ 6.5% · provenance note byte-identical |
| مجمع كبير بايت-مطابق (وعد GAI سبرنت آخر) | 51/835/17 + 40×9,000: amount None · cross-check 44,352,000 @ 7.5% · `role_ar` unchanged |
| واجهة: مسح + sync + إسقاط «يتطلب» | R14 measured (below) |

## 5. Verification — empirical evidence

- **Isolated `test_sprint_2_22_0b22.py` 63/63** — production helper (E14): membership, byte-identity strings, ignore matrix, b6 preservation, fail-safe (None/unknown → ignore), wiring pins, index.html fence pins.
- **Local E2E (real engine, live GIS) 4/4 vs the live v190 captures:** villa+pair 2,400,000 byte == bare (door closed) · apt+pair 8,529,231 byte · compound+pair refusal byte (incl. `user_inputs.rental_income=360000`) · villa bare byte.
- **DoD:** aggregator **392 ALL COUNTS MATCH** · security **15/15** · surface-honesty **45/45** · broad walk **ALL GREEN** — the single first-run red was `test_sprint_2p16p10_tower_split.py`'s **sync pin on the replaced literal** `_rent_source = None` (behaviour 21/21 green) → re-pointed to the helper marker (R6/Lesson-2 class, test-only, Soft-Gate-3 flagged).
- **R14 real-Chromium 390×844:** apartment refusal shows «يتطلب:» → valued render drops it (banner stays) · villa-after-apartment: section hidden + pair CLEARED + zero-typing refine submit carries NO pair + headline ٢٬٤٠٠٬٠٠٠–٥٬٤٠٠٬٠٠٠ · the chip renders verbatim ONCE above the number (box 350<390) · no overflow (390==390) · **0 console errors**. (`preview_screenshot` tool timed out all session — §20.34 precedent; evidence = accessibility snapshots + DOM measurements.)

## 6. Deployment

```
cd /d "C:\Thammen"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 7. Verification curl (post-deploy)

```
curl -s https://thammen.qa/api/health | findstr 2.22.0b.22
curl -s -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36" -X POST https://thammen.qa/api/evaluate/details -H "Content-Type: application/json" -d "{\"zone\":54,\"street\":541,\"building\":6,\"unit_count\":12,\"avg_monthly_rent_per_unit\":5000}" > b22_v.json
findstr /C:"تم تجاهله" b22_v.json
findstr /C:"2400000" b22_v.json
```

## 8. What's NOT in this patch

- **The compound_large GAI promise** (address-entry large compound + the requested GAI still refuses — the DCF fork precedes the E20 promotion): its own signed Gate-2 (Phase-0 §6-ب-2).
- **value_stack/leadership for buildings** (b20 extension): separate methodology Gate-2.
- **The types-tab + coming-soon cards** (Phase-0 §6-أ-1): separate presentational slice.
- No change to b6 income_led for genuine bare rents, b4 levers, b11/b13/b16/b18/b20/b21 logic, or any bare-path output. `api.py` untouched (schema unchanged — the pair fields remain accepted; their effect is now asset-gated).
