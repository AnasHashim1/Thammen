# Sprint 2.19.1 — Polish & Fixes for Cap Rate Calibration
## Brief for Claude Code

**Prepared by:** Claude (web session, 2026-05-20)
**Baseline:** Sprint 2.19 (CHANGELOG_v37, `thammen-sprint2p19p0-cap-rate-calibration`)
**Target:** Sprint 2.19.1 (`thammen-sprint2p19p1-polish-and-fixes`)
**Sprint type:** Polish + bug fixes + documentation hygiene. No new methodology.
**Expected scope:** ~6 fixes, ~200-300 LOC modifications, half a day of focused work.

---

## 1. Context

Sprint 2.19 deployed successfully on 2026-05-20 with one reliable cap rate (Al-Ebb villa 400-600 m² aging_stock @ 4.7%). A real user-facing report was generated for villa 56/565/21 (Bou Hamour 900 m²), and review of that PDF + the `/api/calibration` output surfaced **6 issues** worth fixing before Sprint 2.20 (Comparable Adjustments Grid).

These are all polish/hygiene items. **Production is safe.** No methodology violations. But they're accumulating and visible to users.

---

## 2. The 6 fixes (priority order)

### Fix #1 — Arabic labels for cap rate provenance fields 🟡

**Problem:** The new `cap_rate_provenance` block added to user-facing brief in Sprint 2.19 renders raw schema field names:

```
Source · Cap Rate Pct · Confidence · Body Ar
```

User sees English field names mixed into an Arabic report. The values themselves (`hardcoded`, `fallback`) are also untranslated technical strings.

**Fix:**
- Add Arabic labels for each field in `output_briefs.py`:
  - `Source` → **المصدر**
  - `Cap Rate Pct` → **نسبة الرسملة**
  - `Confidence` → **درجة الثقة**
  - `Body Ar` → drop the label entirely; render the body as a paragraph below the labeled fields (the Arabic text is self-explanatory)

- Translate the *values* too (this is Fix #2 below)

**Files:** `output_briefs.py`

**LOC estimate:** ~20

---

### Fix #2 — Translate confidence + source strings to Arabic 🟡

**Problem:** Same section shows `Source: hardcoded` and `Confidence: fallback`. These are accurate but jarring in Arabic context. User reads "fallback" as a technical word, not an explanation.

**Fix:** Translate at the rendering layer (keep SQLite + API JSON in English for machine consumption):

| Internal | Arabic display |
|---|---|
| `Source: calibrated` | **المصدر: مُعايَر من بيانات السوق** |
| `Source: hardcoded` | **المصدر: معدل افتراضي (غير مُعايَر)** |
| `Confidence: reliable` | **درجة الثقة: موثوقة** |
| `Confidence: indicative` | **درجة الثقة: إرشادية** |
| `Confidence: fallback` | **درجة الثقة: غير كافية — استُخدم معدل افتراضي** |

API JSON (`/api/calibration`, `/api/evaluate`) keeps English values for backward compatibility. **Only the user-facing brief renders translated.**

**Files:** `output_briefs.py`

**LOC estimate:** ~15

---

### Fix #3 — Villa hardcoded fallback rate investigation 🔴

**Problem:** Villa 56/565/21 (Bou Hamour) showed `Cap Rate Pct: 4.0`. Per the brief, the hardcoded mapping is villa=6.5%, land=4.0%. Either:

(a) **Intentional:** the system applies the 10-Year Rule logic — when a villa is valued primarily as land (building <20% of total), it uses the land cap rate. The Bou Hamour villa shows land=83%, building=17%, which fits this pattern.

(b) **Bug:** the hardcoded fallback maps all asset types to the land rate when no calibration exists, ignoring the explicit `villa → 6.5%` mapping.

**Investigation steps:**

1. Open `evaluate_unified.py`. Find the code path that selects the cap rate when `cap_rates.sqlite` has no matching row.
2. Trace: for `asset_type='villa'` with no calibration, what hardcoded value is selected? 4.0% or 6.5%?
3. If it's selecting 4.0% unconditionally → **bug**. Fix to use the asset-type-specific hardcoded value.
4. If it's selecting 4.0% based on land-dominance heuristic → **intentional**. Document this in the brief output, and update the explanation body text to explain to the user *why* 4% was used (10-Year Rule).

**Either way**, the user-facing brief should *explain the choice* clearly:

- If 6.5% used: "معدل الفيلات الافتراضي (غير معايَر)"
- If 4% used because of land-dominance: "البناء يساهم بأقل من 20% من القيمة — استُخدم معدل الأرض (4%) وفق قاعدة الـ 10 سنوات في قطر"

**Files:** `evaluate_unified.py` (investigation + possible fix), `output_briefs.py` (explanation text)

**LOC estimate:** ~30 if bug exists, ~10 if just documentation

---

### Fix #4 — Stratification gap for villa rows with no MoJ land median 🟡

**Problem:** Looking at `/api/calibration` output, some villa rows have `stock_class=null` even with large samples:

| District × Bracket | n_rent | stock_class | Confidence |
|---|---|---|---|
| Pearl 400-600 villa | 63 | **null** | fallback |
| Pearl 600-900 villa | 32 | **null** | fallback |
| Pearl 0-400 villa | 23 | **null** | fallback |
| Lqateefiya 400-600 villa | 45 | **null** | fallback |
| Lqateefiya 0-400 villa | 26 | **null** | fallback |
| Al-Ebb 400-600 villa | 35 | aging_stock ✅ | reliable |

Rule E4 (`Empirical_Findings.md` §2) requires stratification for villas before cap rate calibration. The null cases violate this — but they're correctly fallback, so production is safe today.

**The risk:** if Pearl 600-900 grows to n=50+ rentals AND we find MoJ land medians for Pearl, the row could promote to indicative/reliable while still missing stratification → silent Rule E4 violation.

**Probable cause:** Stratification requires `villa_per_m² / moj_land_median_per_m²` to compute the ratio. If Pearl has no MoJ land transactions (Pearl is reclaimed land, mostly apartments — very few raw land sales registered), stratification can't compute.

**Fix options (pick one):**

(a) **Hard guard:** if stratification fails (no land median), force `confidence='fallback'` regardless of rent sample size, and store reason in `notes` field: `stratification_unavailable: no_moj_land_median`. Production behavior unchanged, but the gap can never silently promote.

(b) **Proxy denominator:** use the municipality-level land median as fallback (e.g., Pearl falls back to Doha land median). Document this clearly in the row's `notes`. More inclusive but methodologically softer.

🟢 **Recommended: option (a)** — hard guard. Aligns with Rule E4. Safer.

**Files:** `cap_rate_calibrator.py`

**LOC estimate:** ~25

---

### Fix #5 — Outlier guard on rent/sqm values 🟡

**Problem:** `/api/calibration` shows some clearly impossible values that slipped past current validation:

| District × Bracket | rent/sqm (QAR/m²/month) | Plausible? |
|---|---|---|
| Pearl 1500+ villa | **0.67** | No (impossibly low) |
| معيذر 55 compound_small 0-400 | **183.33** | No (impossibly high) |
| الخريطيات compound_small 0-400 | **101.04** | Borderline (probably parsing error) |

These are all n=1 → fallback → no production impact. But they reveal a data quality gap. If we scale to larger samples, outliers like these will contaminate medians.

**Fix:** Add a sanity filter in `propertyfinder_client.py` *before* listings enter the calibration:

```python
RENT_PER_SQM_MIN = 5    # QAR/m²/month — absolute floor
RENT_PER_SQM_MAX = 200  # QAR/m²/month — absolute ceiling (Pearl penthouses ~150)

def is_plausible_listing(listing):
    rent_per_sqm = listing['monthly_rent'] / listing['size_sqm']
    if not (RENT_PER_SQM_MIN <= rent_per_sqm <= RENT_PER_SQM_MAX):
        return False
    return True
```

Log rejected listings to a counter (e.g., `outliers_rejected_total`) and surface it in `/api/calibration` for visibility.

**Files:** `propertyfinder_client.py`, `cap_rate_calibrator.py`

**LOC estimate:** ~30

---

### Fix #6 — Documentation hygiene 🟡

**Problem:** Sprint 2.19 created several new operational rules informally. The documentation didn't fully catch up.

**Tasks:**

1. **Verify `docs/Operational_Rules.md` contains all the rules created in Sprint 2.19:**
   - Rule #32 (no push without permission)
   - Rule #36 (CHANGELOG empirical numbers)
   - Rule #40 (two-layer tests)
   - Rule #43 (subtree push from repo root)
   
   If any missing, add them.

2. **Add Rule #44 — Subtree push divergence:**
   > After repeated `git subtree push`, synthetic commits diverge. Use `git subtree split --prefix "deploy v2" -b heroku-deploy-tmp` + `git push heroku heroku-deploy-tmp:master --force` + `git branch -D heroku-deploy-tmp`. Safe because Heroku is a deployment target, not a historical repo.

3. **Extend the Session Log** to cover 2026-05-20 (Sprint 2.19 deployment day). Either:
   - Append a new section to `__Session_Log___2026-05-17_to_19.md` and rename it to `__Session_Log___2026-05-17_to_20.md`
   - OR create `__Session_Log___2026-05-20.md` as a new file

   The session log should capture: Sprint 2.19 deployment, git divergence issue + Rule #44 discovery, denominator gating fix, Pearl 3.31% demotion, first reliable calibration cell (Al-Ebb).

4. **Update Project_Instructions.md §11** — add Sprint 2.19 + Sprint 2.19.1 (this one) to Completed Sprints table.

5. **Update Project_Instructions.md §18** — register A12 (stratification gap) + A13 (rent/sqm outliers) as bugs, then mark them resolved in this Sprint.

**Files:** `docs/Operational_Rules.md`, `docs/Session_Log*.md`, `docs/Project_Instructions.md`

**LOC estimate:** ~150 lines of markdown

---

## 3. Files modified summary

| File | Changes |
|---|---|
| `output_briefs.py` | Fixes #1, #2, #3 (display layer only) |
| `evaluate_unified.py` | Fix #3 (if bug) — bump ENGINE_VERSION + SPRINT_TAG |
| `cap_rate_calibrator.py` | Fixes #4, #5 |
| `propertyfinder_client.py` | Fix #5 (outlier filter) |
| `api.py` | Bump ENGINE_VERSION to `thammen-sprint2p19p1-polish-and-fixes` |
| `tests/test_cap_rate_calibrator.py` | Add tests for #4, #5 |
| `tests/test_output_briefs.py` | New file? Or add tests for Arabic label rendering |
| `CHANGELOG_v38.md` | New file documenting this Sprint |
| `docs/Operational_Rules.md` | Add Rule #44, verify #32/#36/#40/#43 present |
| `docs/Session_Log*.md` | Extend or new file for 2026-05-20 |
| `docs/Project_Instructions.md` | §11 + §18 updates |

**Total LOC estimate:** ~270 (code) + ~150 (docs)

---

## 4. Methodology constraints (still binding from Sprint 2.19)

Even though this is polish, the foundational rules still apply:

- 🔴 **Rule E1** — listings never adjust MoJ sale medians
- 🔴 **Rule E3 refined** — rentals calibrate cap rates only, not prices
- 🔴 **Rule E4** — villa stratification mandatory (Fix #4 enforces this)
- 🔴 **GIS districts authoritative** — never trust PropertyFinder location string

If any fix tempts you to bend these → STOP and re-read `docs/Empirical_Findings.md` §2.

---

## 5. Pre-deploy 6-item checklist (Project_Instructions §5)

1. `py_compile` on every modified Python file
2. `node --check` — N/A (no JS changes expected)
3. Mobile viewport test — verify new Arabic labels render correctly at 390×844
4. **140/140 regression tests pass** (current = 81 regression + 59 Sprint 2.19)
5. **≥6 new isolated tests** for this Sprint:
   - Test outlier filter rejects rent/sqm < 5 and > 200
   - Test stratification null guard forces fallback
   - Test Arabic label rendering for each confidence level
   - Test villa hardcoded fallback selects correct rate (6.5% expected unless 10-Year Rule applies)
   - Test rule #44 documented in Operational_Rules.md
   - Test outlier counter exposed in `/api/calibration`
6. Smoke test on 3 addresses post-deploy:
   - Al-Ebb 400-600 villa (still shows `calibrated` source with proper Arabic labels)
   - Bou Hamour 900 villa (now shows correct hardcoded rate + Arabic explanation)
   - Pearl 600-900 villa (still fallback, but stratification null is now documented in notes)

---

## 6. CHANGELOG_v38 required structure

Mirror v37 style. Required sections:

```markdown
# CHANGELOG v38 — Sprint 2.19.1: Polish & Fixes
Engine version: thammen-sprint2p19p1-polish-and-fixes
Date: 2026-05-XX
Files changed: [list]

## Why this matters
[Real user-facing report from 2026-05-20 surfaced 6 issues: English labels leaking into Arabic, unclear cap rate selection logic, stratification gap, outlier values. All non-blocking but accumulating.]

## What this patch does
### Display (output_briefs.py)
- Arabic labels for cap rate provenance fields (Fix #1)
- Translated confidence + source values (Fix #2)
- Clearer explanation of cap rate selection (Fix #3)

### Calibration (cap_rate_calibrator.py + propertyfinder_client.py)
- Outlier guard: reject rent/sqm outside [5, 200] QAR/m²/month (Fix #5)
- Hard guard: villa rows with no MoJ land median forced to fallback (Fix #4)

### Engine (evaluate_unified.py)
- [Fix #3 details if it was a bug, or just version bump if it was intentional]

## Verification — empirical evidence
[Re-run /api/calibration. Show: total cells before/after outlier filter. Show: new null-guard count. Show: Al-Ebb 400-600 still reliable @ 4.7%.]

## Deployment
git subtree split --prefix "deploy v2" -b heroku-deploy-tmp
git push heroku heroku-deploy-tmp:master --force
git branch -D heroku-deploy-tmp

## Verification curl
curl -s https://thammen.qa/api/health | findstr /C:"sprint2p19p1"
curl -s https://thammen.qa/api/calibration | findstr /C:"outliers_rejected"

## What's NOT in this patch
- Sprint 2.20 (Comparable Adjustments Grid) — separate
- Sprint 2.29 (MME apartments) — separate
- Heroku Scheduler decision — pending user input
- runtime.txt → .python-version migration — deferred to Sprint 2.19.2
- A6 latency optimization — deferred to Sprint 2.19.2
```

---

## 7. Authority delegation (no need to ask Anas)

You can decide independently:

- Arabic translation choices for confidence/source values (use my suggestions in Fix #2 as defaults; refine if better wording exists)
- Whether Fix #3 turns out to be bug or intentional — either path is acceptable, just document clearly
- Choice between Fix #4 option (a) vs (b) — recommended (a)
- Exact outlier thresholds in Fix #5 (5-200 QAR/m²/month is starting point; adjust based on observed distribution)
- Session log file structure (extend existing vs new file)

---

## 8. Return to Anas only if

- 🔴 You discover the 4% cap rate is a genuine bug AND fixing it changes Bou Hamour's valuation by >5% → flag before deploy
- 🔴 Outlier filter rejects more than 10% of all listings → flag, may indicate parsing problem
- 🔴 Operational rules conflict with what you find on disk (e.g., rule numbering already used differently) → ask for guidance
- 🟡 Any test fails after applying fixes → diagnose first, escalate if root cause unclear

---

## 9. Success criteria

Sprint 2.19.1 is done when:

1. 🟢 Real `/api/evaluate` response for Bou Hamour 56/565/21 shows **Arabic-only labels** in cap_rate_provenance section
2. 🟢 The 4% (or 6.5%) selection has a **clear Arabic explanation** in the body text
3. 🟢 `/api/calibration` shows `outliers_rejected_total` counter
4. 🟢 No villa row in calibration has `confidence='reliable'` or `'indicative'` with `stock_class=null` (Rule E4 enforced)
5. 🟢 CHANGELOG_v38 committed
6. 🟢 ENGINE_VERSION updated to `thammen-sprint2p19p1-polish-and-fixes`
7. 🟢 140/140 + ≥6 new tests passing
8. 🟢 Operational_Rules.md contains Rules #32, #36, #40, #43, #44
9. 🟢 Session Log extended to cover 2026-05-20
10. 🟢 A12 + A13 registered in Project_Instructions.md §18 and marked resolved in this Sprint

---

## 10. Deployment procedure (reminder — Rule #44)

From `C:\Thammen` (NOT `C:\Thammen\deploy v2`):

```
git subtree split --prefix "deploy v2" -b heroku-deploy-tmp
git push heroku heroku-deploy-tmp:master --force
git branch -D heroku-deploy-tmp
```

Wait ~60s for dyno restart. Verify with `curl -s https://thammen.qa/api/health`.

---

*End of brief. Total estimated build time: 4-5 hours. Test + deploy: 1 hour. Half-day Sprint.*
