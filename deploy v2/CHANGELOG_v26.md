# CHANGELOG — Sprint 2.16.4: Mobile Form Field Clipping Fix

**Engine version:** `thammen-sprint2p16p4-mobile-form-clipping-fix`
**SPRINT_TAG:** `2.16.4` → /api/health reports `3.1.0-sprint2.16.4`
**Date:** 2026-05-17
**Files updated:** `index.html` (1 CSS line), `evaluate_unified.py` (version bump only)
**Builds on:** Sprint 2.16.3 (mobile header fix)
**Severity:** 🟠 High — silently hid 3 form inputs on mobile, breaking
                Sprint 2.16.0/2.16.2 entire workflows for mobile users

---

## Why this matters — a silent regression older than Sprint 2.16

User report (2026-05-17, iPhone, post-2.16.3 deploy): "still — the asking
price doesn't appear". The Sprint 2.16.3 header fix worked (screenshots
confirmed THAMMEN logo + "متصل" no longer overlap the banner on the home
page), but the user was pointing to a different issue: the optional
details form was missing its last 3 fields on mobile.

### What was hidden

When the "إضافة تفاصيل العقار" toggle opens, the form should reveal:

1. عدد الطوابق فوق الأرض
2. سرداب
3. عدد الملاحق
4. مجلس خارجي منفصل
5. حالة العقار
6. تقدير مساحة البناء الأرضي
7. عمر البناء التقديري
8. تشطيب فاخر
9. **السعر المطلوب** ← invisible on mobile
10. **الإيجار الشهري الحالي** ← invisible on mobile
11. **الإيجار الشهري المتوقع** ← invisible on mobile

The first 8 rendered fine. The user could see them and fill them. The last
3 were clipped, silently. The user clicked "ثمّن" without ever knowing
those inputs existed.

### Root cause (line 76 of index.html)

```css
.det.open { max-height: 600px; opacity: 1; padding-top: 16px }
```

This `max-height: 600px` was a hardcoded cap for the animated reveal.
Combined with `overflow: hidden` on `.det` and the mobile media query
at line 167:

```css
@media(max-width:600px) { .fr2 { grid-template-columns: 1fr } }
```

On desktop:
- `.fr2` = 2 columns
- 11 fields / 2 = ~6 rows × ~70px each = ~420px
- Fits comfortably under 600px ✓

On mobile:
- `.fr2` collapses to 1 column
- 11 fields × ~80px each = ~880px
- 600px max-height → **last ~280px (3 fields) hidden behind `overflow:hidden`**

The 3 hidden fields (`askingPrice`, `rentalIncome`, `potentialRental`)
are exactly the inputs that drive:

- **Sprint 2.16.0** subject_property classification (needs asking_price)
- **Sprint 2.16.2** stratum-aware negotiation (needs asking_price)
- **Income approach** with rental data (needs rentalIncome / potentialRental)

So this silent bug had been NEUTRALIZING all of Sprint 2.16.0/2.16.2's
user-facing value on mobile, for any user who tried the optional details.

### Why it took 4 sprints to notice

- All my testing was via `curl` (the inputs were SENT correctly when
  manually constructed; the form merely wasn't capturing them)
- The user tested on desktop initially (where the fields rendered fine)
- The mobile test that caught it was AFTER Sprint 2.16.3, when the user
  scrolled the optional-details form and noticed the gap

This bug is older than Sprint 2.16 — likely pre-existing since whatever
sprint introduced the toggleable details section. The fix is one line.

---

## What this patch does

```diff
-.det.open{max-height:600px;opacity:1;padding-top:16px}
+.det.open{max-height:1500px;opacity:1;padding-top:16px}
```

The new 1500px accommodates the worst case (mobile, single column, all 11
fields including any future additions). The transition animation is
unaffected — CSS interpolates max-height fine to any positive value.

Alternative considered: `max-height: none` would technically work but
disables the transition animation (CSS can't interpolate to/from `none`).
1500px keeps the smooth open/close while solving the clip.

---

## Verification — pre-deploy

```
$ python -c "...extract scripts..." && node --check /tmp/c.js
✓ JS OK

$ python -c "import py_compile; py_compile.compile('evaluate_unified.py')"
✓ Python OK
```

Manual visual check needed post-deploy: open optional details on iPhone
and confirm all 11 fields scroll into view.

---

## Deployment

```
prompt command
cd /d "C:\Thammen\deploy v2"
copy /Y index.html index.html.bak_2p16p3
copy /Y evaluate_unified.py evaluate_unified.py.bak_2p16p3
tar -xf "%USERPROFILE%\Downloads\sprint2p16p4-mobile-form-clip.zip"
findstr /C:"sprint2p16p4" evaluate_unified.py
git add index.html evaluate_unified.py CHANGELOG_v26.md
git commit -m "Sprint 2.16.4: mobile form clipping — hidden askingPrice/rental fields"
git push heroku master
```

## Post-deploy verification

```
curl https://thammen.qa/api/health
```
Should report `"version": "3.1.0-sprint2.16.4"`.

**Visual test (the key test):**
1. Open `https://thammen.qa/` on iPhone
2. Enter zone/street/building (any villa, e.g. 51/955/49)
3. Tap the "إضافة تفاصيل العقار" toggle to expand
4. Scroll down within that section
5. Confirm all 11 fields are visible, including:
   - السعر المطلوب (asking price)
   - الإيجار الشهري الحالي
   - الإيجار الشهري المتوقع

This unblocks Sprint 2.16.0 + 2.16.2 features for mobile users.

---

## What is NOT in this patch

- No backend changes (version bump only)
- No JS changes
- No new features — purely a CSS regression fix
- No changes to the toggle behavior itself

---

## Lessons (added to internal QA notes)

1. **CSS animations with fixed max-height are fragile.** They assume a
   layout that may not hold across viewports. Where possible, prefer
   `max-height: 100vh` or `max-height: none` (without transition).
2. **`overflow: hidden` is a silent failure mode.** Content disappears
   without any error. Pair `overflow:hidden` with explicit layout testing
   on small viewports.
3. **`curl` cannot catch form-rendering bugs.** Sprint 2.16.0 testing
   verified the backend accepted `asking_price` via curl — but the user
   couldn't actually input it on mobile. Future Sprints touching form
   features should include at least one mobile-viewport manual check
   (browser dev tools → device toolbar → 390×844 iPhone).

---

## Files in this patch

```
sprint2p16p4-mobile-form-clip.zip
├── index.html              (MODIFIED, 1 CSS value change)
├── evaluate_unified.py     (MODIFIED, version line only)
└── CHANGELOG_v26.md         (NEW, this file)
```

---

_Last updated: 2026-05-17 — mobile form clipping resolved, unblocking
Sprint 2.16.0/2.16.2 features on mobile._
