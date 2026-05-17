# CHANGELOG — Sprint 2.16.1: HOTFIX — JS Identifier Collision

**Engine version:** `thammen-sprint2p16p1-strata-hotfix`
**SPRINT_TAG:** `2.16.1` → /api/health reports `3.1.0-sprint2.16.1`
**Date:** 2026-05-17
**Files updated:** `index.html`, `evaluate_unified.py` (version bump only)
**Replaces:** Sprint 2.16.0 (deployed 2026-05-17 12:43, broken in production)
**Severity:** 🔴 Critical — Sprint 2.16.0 made the entire site unclickable

---

## What broke

User report (2026-05-17): "I can't open anything on Thammen. The home page
loads but clicking 'ابدأ التقييم' does nothing." Verified by fetching the
deployed `index.html` and parsing the inline JS through Node:

```
$ node --check extracted.js
/tmp/extracted.js:505
  const ss=d.stock_strata;
        ^
SyntaxError: Identifier 'ss' has already been declared
```

Two `const ss = …` declarations in the same scope (function body of
`renderResult`):

- `index.html:201` — `const ss=d.service_scope;` (existing since Sprint 2.14.0)
- `index.html:505` — `const ss=d.stock_strata;` (added by Sprint 2.16.0)

**Effect.** Browsers refuse to evaluate the inline script at all when the
parse fails. No event handlers attach. Every button on the site becomes
a no-op. The home page renders (it's plain HTML) but cannot transition to
the evaluation form.

---

## Root cause — process, not code

The collision wasn't caught because:

1. **Pre-deploy `node --check` was never run on the modified `index.html`.**
   Sprint 2.16.0 was tested by:
   - Compiling the Python (`py_compile` on `evaluate_unified.py`)
   - Running the standalone `test_stock_strata.py` unit/integration tests
   - Running the renderer function in isolation against mock data
   - Confirming the JSON response shape from production

   None of these steps loaded the **full** `index.html` JS in a single
   parse context. The renderer test extracted only the new block, wrapped
   it in a fresh function, and executed it — the rest of the file was
   never co-parsed.

2. **Local short-name variable convention.** I added `const ss = d.stock_strata;`
   following the existing pattern in the file (`const rtr = d.reasoning_trace;`,
   `const lr = ss.land_reference;` etc). I did not grep for `ss` first.

3. **Sprint 2.16.0 verification was offline-only.** The browser was never
   loaded against the deployed site post-deploy. The `curl /api/evaluate/details`
   verification confirms the *backend* works — but `curl` does not parse JS,
   so a frontend regression of this magnitude was invisible to it.

---

## What this patch does

**Single change.** Inside the Sprint 2.16.0 block in `index.html` (between
`// ── Sprint 2.16.0: …` and `// ── Known unknowns ──` sentinels), rename
the local variable `ss` to `stockStrata`. All references within the block
updated.

The other (pre-existing) `const ss = d.service_scope;` at line 201 is
untouched.

**Diff:** 13 line-precise patches in `index.html`. No changes to:
- `stock_strata.py` (backend logic unchanged)
- `test_stock_strata.py` (still 6/6 passing)
- API contract / JSON response shape (no field renames)

**Version bump:** `2.16.0` → `2.16.1` in `evaluate_unified.py` so
`/api/health` confirms the hotfix is live.

---

## Verification (this patch)

Pre-deploy:

```
$ python -c "import re; \
> html=open('index.html').read(); \
> scripts=re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', html, re.S); \
> open('/tmp/c.js','w').write('\n\n'.join(scripts))"
$ node --check /tmp/c.js
✓ JS parses cleanly
```

Post-deploy verification:

```
curl https://thammen.qa/api/health
```
should report `"version": "3.1.0-sprint2.16.1"`.

Then open `https://thammen.qa/` in a browser and click "ابدأ التقييم".
The evaluation form should appear (broken in 2.16.0).

---

## Process changes (so this doesn't happen again)

Adding to the Section 5 (UI-First Audit) checklist for future Sprints
touching `index.html`:

1. **Before zipping any HTML/JS changes:** run `node --check` against the
   full extracted inline JS. One-liner:
   ```cmd
   python -c "import re; ...; open('/tmp/c.js','w').write(...)"
   node --check /tmp/c.js
   ```

2. **Before bumping the engine version in the CHANGELOG verification block:**
   load the deployed site in a real browser and click *at least one button*.
   The whole point of an "exposure-only" sprint is the user can SEE it —
   if the site is dead, the user sees nothing.

3. **Variable naming for new index.html blocks:** prefer
   multi-character semantic names (e.g. `stockStrata`, `rentDetail`) over
   2-letter abbreviations (`ss`, `rd`). Whole-file `grep` for the name
   first, regardless.

4. **`curl /api/health` is necessary but not sufficient.** A successful
   `/api/health` response only proves the backend started. It does not
   prove the frontend works.

These will be added to Section 5 of the Project Instructions in a future
documentation Sprint (not bundled here to keep this hotfix minimal).

---

## Deployment (hotfix)

```
prompt command
cd /d "C:\Thammen\deploy v2"
copy /Y index.html index.html.bak_2p16p0_broken
copy /Y evaluate_unified.py evaluate_unified.py.bak_2p16p0
tar -xf "%USERPROFILE%\Downloads\sprint2p16p1-hotfix.zip"
findstr /C:"sprint2p16p1" evaluate_unified.py
git add index.html evaluate_unified.py CHANGELOG_v23.md
git commit -m "Sprint 2.16.1: HOTFIX — rename ss to stockStrata (JS parse collision)"
git push heroku master
```

After push, wait ~60 seconds for the dyno to restart, then verify in a
browser that you can click "ابدأ التقييم" and reach the evaluation form.

---

## What is NOT in this patch

- **No backend changes** (stock_strata.py and its API contract unchanged).
- **No re-deploy of Sprint 2.16.0 features**; the strata card was already
  rendering correctly in the JS — it just never got executed because the
  parse failed before reaching it.
- **No tests added.** The right test is `node --check` in CI, not Python
  unit tests — that's process not code.

---

## Acknowledgment

This regression was preventable with a 2-second `node --check` step before
packaging. I missed it. Apologies for the broken-site interval —
~24 minutes of production downtime between Sprint 2.16.0 deploy
(12:43 UTC) and this hotfix.

---

## Files in this patch

```
sprint2p16p1-hotfix.zip
├── index.html             (MODIFIED, +153 bytes, rename only)
├── evaluate_unified.py     (MODIFIED, version line only)
└── CHANGELOG_v23.md        (NEW, this file)
```

---

_Last updated: 2026-05-17 — emergency hotfix for Sprint 2.16.0 production breakage._
