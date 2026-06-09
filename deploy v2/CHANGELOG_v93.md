# CHANGELOG v93 — Sprint 2.22.0b.10.2 (multi-QARS-aware geometry footprint)

**Engine:** `thammen-sprint2p22p0b10p2-multiqars-footprint` · **SPRINT_TAG** `2.22.0b.10.2` ·
api/health `3.1.0-sprint2.22.0b.10.2` · **2026-06-09**
**Files:** `evaluate_unified.py` (`_geometry_footprint` + `shared_effective_area` param + geometry block +
version) · `index.html` (confirm row + results card + fpHint — shared disclosure) ·
`test_sprint_2_22_0b10.py` (+7 multi-QARS). **`api.py` UNTOUCHED. DISPLAY-only / VALUE-INVARIANT.**
Direct follow-up — closes a footprint bug Anas caught on 56/565/21.

## 1. Why (Anas caught it)

**56/565/21** (Abu Hamour) is **PIN 56090294 — a 900 m² parcel SHARED by 2 villas** (multi-QARS: n=2,
`effective_per_villa=450`). b10 computed the geometry footprint on the **FULL** pdarea (900 → **528 m²**),
i.e. the footprint of **both villas combined**, when a single villa sits on ~450 m² → ~270 m². The **value**
side was already multi-QARS-aware (it brackets on the effective 450 → 400-600 → 2.4M, correct), but the
**footprint** side wasn't. So a user saw "528 m² ground footprint" for a single villa — ~2× too high.

## 2. What this patch does

`_geometry_footprint` gains an optional `shared_effective_area`. When set (the `effective_per_villa` of a 2+-
villa parcel, read from `ev.multi_qars` in the geometry block), the footprint is the **orientation-free
coverage cap on the share** (0.60 × 450 = **270**), method `coverage_cap_shared`, `plot_dims_m=None` (the
per-villa split shape is unknown — the cadastral polygon is the combined parcel), plus `effective_share_m2`
+ `n_share` for disclosure. The note + the 3 UI surfaces (confirm basis row, results card, `refineScreen`
hint) disclose «حصة الوحدة في قطعة مشتركة بين N وحدات». Single-plot villas are byte-unchanged (param
defaults to None). **Value-invariant** — the geometry surface is display-only (recon D1); `_suggested_fp`/
`_eff_fp`/`amount` untouched.

## 3. Verification

- py_compile OK. Isolated `test_sprint_2_22_0b10.py` **31/31** (24 + 7 multi-QARS: shared→cov_cap(450)=270,
  dims None, `effective_share_m2`/`n_share` surfaced, shared < full-plot footprint, share≥pdarea→normal,
  share None→normal). DoD aggregator **392** (version-pin safe). Broad walk: 79/79 (re-run; unaffected — the
  only logic touched is `_geometry_footprint`, covered by the isolated 31).
- **Local E2E (live GIS):** **56/565/21 → footprint 270 (coverage_cap_shared, share 450, n=2), amount
  2,400,000 byte-identical**; 54/541/6 → 311 (setback_envelope, single, unaffected); 56/647/6 → 391
  (coverage_cap, single); 55/296/13 → 630; 52/903/90 → refusal. **5 anchors value byte-identical.**
- **R14 real Chromium** (served index.html + 56/565/21 payload): confirm row «مساحة البناء الأرضي (تقدير أقصى)
  ≈ ٢٧٠ م² (حصة الوحدة في قطعة مشتركة بين 2 وحدات)»; results card «هذه القطعة مشتركة بين 2 وحدات؛ الحدّ الأقصى
  للبناء الأرضي لوحدتك ≈ ٢٧٠ م² (على الحصة الفعلية ≈ ٤٥٠ م²)»; **0 console errors**; **390×844 no overflow**
  (confirm + results).

## 4. Deployment

```
cd /d "C:\Thammen\deploy v2"
git add evaluate_unified.py index.html test_sprint_2_22_0b10.py CHANGELOG_v93.md
git commit -m "Sprint 2.22.0b.10.2: multi-QARS-aware geometry footprint (per-villa share, not whole parcel) - display-only, value-invariant"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 5. What's NOT in this patch

No value change; `api.py` untouched. The **value movement** Anas also wants (value responds to age /
condition / building area / penthouse) is the separate **§20.9 cost-triangulation Gate-2** (a Cost-Approach
value = land + depreciated building from BUA × rate × condition × age). The multi-QARS **substantiality
typical-BUA basis** (currently also on the full 900 m², over-stating one villa's typical → suppresses uplift)
is a related value-side fix folded into that §20.9 work, NOT here.
