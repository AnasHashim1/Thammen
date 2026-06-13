# CHANGELOG v117 — Sprint 2.22.0b.34 (DEF-UX12): role-driven density (the study's «المفصل»)

**Engine:** `thammen-sprint2p22p0b34-role-driven-density` · **SPRINT_TAG** `2.22.0b.34` · api-health `3.1.0-sprint2.22.0b.34`
**Date:** 2026-06-13 · **Files changed:** `index.html` (the `_dense` flag + the «كيف وصلنا» open arg), `evaluate_unified.py` (the 2 version-string lines), `test_sprint_2_22_0b34.py` (new), + 5 sibling R6 re-points (`b15`/`b2p2`/`b31`/`b32`/`b33`, test-only)
**Class:** 🟢 FRONTEND-ONLY / VALUE-INVARIANT (`api.py` UNTOUCHED; value byte-identical across ALL roles — مبدأ b24 «الرقم واحد للجميع»).
**Gate-2:** signed by delegation (the study `docs/STUDY_persona_simplicity_and_entry_v1.md` §5 routes the density sprints as value-invariant; «Gate-2 applies only to UX17/UX18/B»). **Gate-1:** deploy-on-green (PO «CONTINUE»).

---

## 1. Why this matters

The study §1 names the role selector «من أنت؟» as **«المفصل»** — the hinge of the whole progressive-disclosure design. Today it is presentation-only (the engine normalizes owner→buyer for the brief), but it **does NOT drive the result screen's density**: a valuer or investor lands on the same folded view as a simple owner. The study's core rule: «من أنت؟» becomes the **default fold-state** — the simple owner stays minimal, the specialist «يولد بالكثافة مفتوحة».

## 2. Root cause + the recon finding (the «server field» was unneeded)

The study/`ISSUES_LOG §4ب-2` described DEF-UX12 as «🟡 frontend + **بثّ `audience` في الاستجابة** (تعديل خادم additive)». **Phase-0 recon falsified the server half** (the §20.26/§20.29 pattern): `evaluate_unified.py` ALREADY writes `'audience': audience` top-level on the main path (`_build_unified_output`) + every fast path; **live-confirmed on v204** (`POST {audience:investor}` → response `audience: investor`). So the additive server field is **unneeded** → **UX12 is FRONTEND-ONLY, `api.py` UNTOUCHED.** And the accordion helper `_acc(title, inner, open)` (b15) already takes an `open` arg — so the control surface existed too.

## 3. What this patch does (frontend, value-invariant)

In `show()`: a density flag derived from the broadcast `audience`, passed as the `open` arg to the b31 «كيف وصلنا لهذا الرقم؟» evidence accordion:
```js
const _dense=(function(a){return a==='investor'||a==='valuer';})(d.audience||'owner');
...
t2+=_acc('🔍 كيف وصلنا لهذا الرقم؟', how+evidencePanelHtml(d,acc), _dense);
```
- **investor / valuer** (the specialists in the 5-role selector) → the evidence accordion is **OPEN** by default («الأدلّة أولاً», study §1.3).
- **owner / buyer / seller** → it stays **FOLDED** (the b31 simple-owner default).
- Fallback `d.audience||'owner'` → folded if audience is somehow absent (safe default).

**Single-purpose (Rule #38):** only the «كيف وصلنا» accordion is density-driven this sprint; the other accordions (basic-info / report / full-details) stay folded for everyone (one click away). The per-role *delta content* (yield badge for the investor, per-component n row for the valuer — study §2) is a later slice (DEF-UX9 etc.). UX12 ships the **hinge** (the fold-state) that the rest branch from.

**Value-invariance (structural):** only the accordion's `open` attribute changes; `amount`/`low`/`high`/`method`/copy/tier-order are untouched. The DRC, leadership, and every note render identically — they're just open-vs-folded by role.

## 4. Backend / frontend / schema

- **Backend:** ENGINE_VERSION + SPRINT_TAG bump only. `api.py` UNTOUCHED. `audience` already broadcast (no new field).
- **Frontend:** the `_dense` flag (placed after `syncTowerPair` to keep the b22 fence-position pin intact) + the `open` arg on the «كيف وصلنا» accordion.
- **Schema:** none.

## 5. Verification — empirical evidence

- **py_compile** `evaluate_unified.py` OK.
- **Isolated** `test_sprint_2_22_0b34.py` **15/15** (reads the REAL index.html — E14: the `_dense` flag derived from `d.audience`; investor/valuer dense, owner/buyer/seller NOT; the `open` arg on «كيف وصلنا»; `_acc` still supports `open`; the recon premise `'audience': audience` in the engine; single-purpose [basic-info NOT density-forced]; no value mutation).
- **5 sibling R6 re-points (test-only):** `b31`/`b32`/`b15`/`b2p2` pinned the «كيف وصلنا» `_acc(...)` call as a literal ending `);` → re-pointed to drop the trailing `);` (b34 added the 3rd `open` arg); `b33` pinned `ENGINE_VERSION == b33` literally → format check (the project's «no exact version pins» rule). The `b22` fence-position pin (`syncTowerPair` within 800 chars of `show()` start) was preserved by placing `_dense` AFTER `syncTowerPair` (code, not a re-point). All green: b34 15/15 · b33 33/33 · b32 29/29 · b31 36/36 · b15 50/50 · b2p2 26/26 · b22 63/63.
- **DoD:** aggregator **392 ALL COUNTS MATCH** · security **15/15** · surface **45/45** · broad auto-walk **102/102 ALL GREEN** (101→102 with the new test).
- **R14 real-Chromium 390×844** (node absent → Chromium is the JS gate, EXECUTED) on the live امريخ cost-led fixture (`.basket/f_marikh.json`): the 5 roles rendered — **owner/buyer/seller → «كيف وصلنا» FOLDED · investor/valuer → OPEN** · **value byte-identical across ALL 5 roles** (amount 2,400,000 / low 2,400,000 / high 5,400,000) · with investor (open) **no horizontal overflow (docScrollW 390 == clientW 390, maxRight 370<390)** · howBody visible when open · **0 console errors/warnings**.
- **api.py untouched** — `git diff --name-only` = index.html + evaluate_unified.py + the 5 test files only.

## 6. Deployment

```
cd /d "C:\Thammen"
git -C "C:/Thammen" subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 7. Verification curl (post-deploy)

```
curl -s https://thammen.qa/api/health        # engine: thammen-sprint2p22p0b34-role-driven-density
curl -s https://thammen.qa/ | findstr /C:"_dense"   # density flag in the served HTML
# audience already broadcast (recon): POST {audience:investor} → response audience:investor
```
Plus the 5-anchor value byte-gate (browser-UA curl, #61) — value identical to v204 (frontend/value-invariant).

## 8. What's NOT in this patch

- The per-role **delta content** (study §2: yield badge for the investor, per-component evidence n for the valuer, financing calculator for the buyer = DEF-UX16, the heirs/bank compliance output = DEF-UX17) — each its own slice.
- Only the «كيف وصلنا» accordion is density-driven; the other accordions stay folded for everyone.
- The 5-role selector is unchanged (no new roles — heirs/lawyer/bank = DEF-UX17, Gate-2).
- **NEXT (study §5 sequence):** DEF-UX16 (buyer financing calculator, 🟢 frontend) · DEF-UX15 (autocomplete entry) · then the §4ب persona features (UX1 keystone comparables · UX3 apartment refusal · UX9 BUA/RCN).
