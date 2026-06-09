# CHANGELOG v92 — Sprint 2.22.0b.10.1 (geometry building-area on the basis review)

**Engine:** `thammen-sprint2p22p0b10p1-geometry-basis-row` · **SPRINT_TAG** `2.22.0b.10.1` ·
api/health `3.1.0-sprint2.22.0b.10.1` · **2026-06-09**
**Files:** `index.html` (one row in `showConfirm`) · `evaluate_unified.py` (version bump only). **`api.py`
UNTOUCHED. DISPLAY-only / VALUE-INVARIANT.** Direct follow-up to b10 (v177) — closes a scoping gap Anas caught.

## 1. Why (Anas caught it)

b10 surfaced the auto-computed **max-buildable building footprint** on the full results card + the
`refineScreen` hint, but **NOT on Screen 2 (the confirm / basis review)** — the first screen the user sees,
where the rest of the auto-fetched basis (plot area, PIN, electricity, water, building-age floor) is shown.
So a user who just entered an address saw the **plot** area but **not** the **building** area, even though
the engine computes it automatically. Verified empirically: the response carries
`geometry.max_buildable_footprint_m2=311` for 54/541/6, but `showConfirm` rendered no building-area row.

## 2. What this patch does

`showConfirm` (`index.html`) now adds one basis row after the b9 `pbRows`, gated on
`geometry.max_buildable_footprint_m2 && _b2IsBuilding(asset_type)`:
> **مساحة البناء الأرضي (تقدير أقصى):** ≈ ٣١١ م² (من أبعاد القطعة 35×17.5 م) — عدّله لواقع مبناك في خطوة التحسين

Honest framing: labelled **تقدير أقصى** (an estimated CEILING from plot dims − setbacks), distinct from the
GIS-fact plot area / PIN, with «عدّله» pointing to the refine step (the user corrects DOWN). For
non-rectangular plots the dims clause is omitted (coverage-cap basis). **No value change** — the building
area is display-only (recon D1; the footprint→BUA→headline wiring is still the §20.9 cost-triangulation Gate-2).

## 3. Verification

- py_compile evaluate_unified.py OK. DoD aggregator **392** (ALL COUNTS MATCH — version-pin safe after the
  b10.1 bump). The broad Python suite + isolated b10 test are unaffected (index.html-only display change).
- **R14 real Chromium** (served index.html + real b10 payload): **confirm screen NOW shows the building-area
  row** «مساحة البناء الأرضي (تقدير أقصى) ≈ ٣١١ م² (من أبعاد القطعة 35×17.5 م) — عدّله…»; plot-area row still
  present; **0 console errors**; **390×844 no overflow** (docScrollW 390, cgMaxRight 370<390); all functions
  defined.

## 4. Deployment

```
cd /d "C:\Thammen\deploy v2"
git add index.html evaluate_unified.py CHANGELOG_v92.md
git commit -m "Sprint 2.22.0b.10.1: surface the auto building footprint on the confirm/basis review (Screen 2) — display-only, value-invariant"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 5. What's NOT in this patch

No value change; no new GIS; `api.py` untouched. The footprint→BUA→headline auto-wiring remains the §20.9
cost-triangulation Gate-2. Results-card presentation of the max-buildable (inside the «حسّن التقدير» card)
is unchanged from b10.
