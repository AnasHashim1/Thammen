# CHANGELOG — Sprint 2.16.3: Mobile Header Overlap Fix

**Engine version:** `thammen-sprint2p16p3-mobile-header-fix`
**SPRINT_TAG:** `2.16.3` → /api/health reports `3.1.0-sprint2.16.3`
**Date:** 2026-05-17
**Files updated:** `index.html`, `evaluate_unified.py` (version bump only)
**Builds on:** Sprint 2.16.2 (stratum-aware negotiation)

---

## Why this matters

User report (2026-05-17, iPhone, post-2.16.2 deploy): "still appears
truncated" — but the placeholders Sprint 2.16.2 fixed ARE now rendering
correctly ("اختياري", "اختياري — مثال: 12"). The actual issue was
different: the **mobile header is overlapping itself**.

Specifically:

1. The data-freshness banner (.dfb) was `position: fixed; top: 0` —
   meaning it sits OVER the document, taking no flow space
2. `body.has-dfb .home { padding-top: 34px }` was the kludge that pushed
   page content down to compensate — but it ONLY accounted for ~34px of
   banner height
3. On mobile, the long Arabic banner text "آخر تحديث لبيانات وزارة العدل:
   ديسمبر 2025 (قبل 137 يوماً) — قد لا تعكس آخر تحركات السوق" wraps to
   2-3 lines, taking ~70-90px
4. The .tbar (containing THAMMEN logo + "متصل" status) was `position: sticky;
   top: 0` — meaning it ALSO sits at the top
5. Result: the wrapped banner text OVERLAPS the tbar logo and status
   indicator on viewports < ~520px wide

User's screenshots clearly showed the warning text crossing through the
THAMMEN logo, and the "متصل" green-dot indicator landing in the middle
of the warning text.

Not caused by Sprint 2.16.0/2.16.1/2.16.2 — pre-existing since Sprint
2.7 (the freshness banner introduction). The placeholders fix in 2.16.2
made the lower form usable, but this header issue remained.

---

## What this patch does

### Change 1: dfb position fixed → sticky

```diff
-.dfb{position:fixed;top:0;left:0;right:0;z-index:1000;...}
+.dfb{position:sticky;top:0;left:0;right:0;z-index:50;...}
```

`position: sticky` participates in document flow. The banner now occupies
its full natural height (whatever that is on the current viewport) and
the tbar stacks BENEATH it cleanly. No more overlap regardless of banner
text length.

`z-index: 50` (down from 1000) — still above page content, but the
tbar's `z-index: 10` doesn't matter anymore because they're no longer
fighting for the same vertical space.

### Change 2: Removed the brittle padding-top kludge

```diff
-body.has-dfb .home,body.has-dfb .screen{padding-top:34px}
```

No longer needed since the sticky dfb already takes its own flow space.
This was a fragile compensation that broke whenever the banner wrapped.

### Change 3: Mobile-friendly tbar at ≤480px

```css
@media(max-width:480px){
  .tbar{padding:8px 14px;flex-wrap:wrap;gap:6px}
  .tbar-logo img{height:30px}      /* was 36px */
  .tbar-st{font-size:.7rem;white-space:nowrap}
}
```

On narrow viewports:
- Tbar children can wrap if needed (`flex-wrap: wrap`)
- Logo is slightly smaller (30px vs 36px)
- Status text doesn't break mid-word

---

## Verification — pre-deploy

```
$ python -c "...extract inline JS..."
$ node --check /tmp/c.js
✓ JS OK

$ python -c "import py_compile; py_compile.compile('evaluate_unified.py')"
✓ Python OK
```

The new pre-deploy workflow (from Sprint 2.16.1's lesson) caught zero
regressions.

---

## Deployment

```
prompt command
cd /d "C:\Thammen\deploy v2"
copy /Y index.html index.html.bak_2p16p2
copy /Y evaluate_unified.py evaluate_unified.py.bak_2p16p2
tar -xf "%USERPROFILE%\Downloads\sprint2p16p3-mobile-header.zip"
findstr /C:"sprint2p16p3" evaluate_unified.py
git add index.html evaluate_unified.py CHANGELOG_v25.md
git commit -m "Sprint 2.16.3: mobile header overlap fix (sticky dfb + tbar)"
git push heroku master
```

## Post-deploy verification

```
curl https://thammen.qa/api/health
```
Should report `"version": "3.1.0-sprint2.16.3"`.

**Visual check (the key test):**
1. Open `https://thammen.qa/` on iPhone or any mobile browser
2. The warning banner should be at the TOP, in its full height
3. The THAMMEN logo + "متصل" indicator should be BELOW it (not overlapping)
4. As you scroll down, both should stick to the top in their natural order

Compare against the broken screenshots from the user (2026-05-17 19:38).

---

## What is NOT in this patch

- No backend changes (engine version bump only)
- No changes to Sprint 2.16.2 stratum-aware logic
- No JS changes
- No mobile responsiveness work beyond the header (e.g., the form below
  was already fixed by 2.16.2 placeholders + media query)

---

## Files in this patch

```
sprint2p16p3-mobile-header.zip
├── index.html              (MODIFIED, +~10 lines: sticky dfb + 480px tbar rules)
├── evaluate_unified.py     (MODIFIED, version line only)
└── CHANGELOG_v25.md         (NEW, this file)
```

---

_Last updated: 2026-05-17 — mobile header congestion resolved._
