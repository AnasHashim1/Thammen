# Sprint B — built-type / condition axis — CC PROPOSAL + handoff to Claude.ai

> **Status:** CC recon-backed **proposal**, NOT a signed brief. Sprint B is a **Gate-2**
> methodology sprint (changes user-facing valuation output) → needs **Claude.ai framing +
> multi-AI (Rule #54) + Anas sign-off** before any build. CC has done the empirical recon
> (live engine + the V001 ground-truth case); this packages it for the Claude.ai lane.
> **Authored:** CC, 2026-06-03 (after the Maamoura 56/647/6 real-buyer case). Live tip: a20 / Heroku v159.

---

## PART 1 — ملخص الجلسة (what we discussed)

1. **Shipped a20** (`thammen-sprint2p22p0a20-rics-compliant-status-label`, Heroku **v159**, CHANGELOG_v72):
   the **A7** honesty label — `rics_compliant_status_ar/en` = «بانتظار مراجعة مُقيِّم مُرخّص
   (المرحلة الخامسة)» next to the bool on every JSON surface. DISPLAY-ONLY, zero value drift,
   `api.py`/`index.html` untouched. DoD 392/15/45/63. **A7 → CLOSED.**
2. **Project-wide doc audit + cleanup:** fixed the wrong deploy command (`git push heroku master`
   → `git subtree push --prefix "deploy v2"`, Rule #43) in **all** active instruction docs
   (Custom/Project/CLAUDE); modernized the legacy claude.ai-chat delivery model → **two-lane**
   (briefs + direct edits + subtree push + DoD + docs-close); **deprecated** the stale
   `docs/claude_ai_upload/` bundle (frozen v91) → upload the canonical `docs/` directly.
3. **Git + personal-file hygiene:** tracked real untracked content (briefs, learnings, validation
   log, backtest), gitignored backup snapshots, removed junk, and cleaned the parent `C:\Thammen\`
   (deleted 12 redundant code archives + 22 regenerable dev-test valuation PDFs; preserved photos +
   the hand-named Izghawa report). App working tree = 0 untracked.
4. **Standing directive adopted (Anas):** on **reversible** matters, CC does **الأصوب** and proceeds —
   no opinion round-trips. Only the 2 hard gates (Heroku push consent, methodology/output sign-off)
   + true ambiguity warrant a question.
5. **The Maamoura case (56/647/6 = V001):** a real property Anas's aunt considered — **built 2001,
   652 m², travertine in/out, pool + jacuzzi, owner-engineer-built, structurally sound (independent
   buyer-side engineer, ~late May 2026), listed 4.8M→3.8M since ~2020, still UNSOLD ~5–6y**; buyers
   repeatedly offer **land value (~2.63M)**, owner refuses + redirects to an adjacent empty plot.
   We re-verified live (a20): engine returns **3.8M, comparison_widened, n=34** — i.e. it **matches
   the market-rejected sticky ask**. V001 updated with the new inspection + a20 re-verify.

## PART 1b — ما الذي تكسبه الحالة للمشروع (why it matters)

- **Canonical, multi-source-confirmed Sprint-B case** (no longer hypothetical): the engine
  **over-anchors old premium stock** by defaulting to the comp-pool median, which here = a
  5-year-rejected ask. Real buyer behaviour + a structural inspection + 5y price history back it.
- **Sharpens the gap into TWO distinct axes** the engine is blind to on the comparison path:
  - **(H-A) building AGE** → can't apply "old stock tends to clear toward land".
  - **(R7) CONDITION** → can't credit the premium that *partially offsets* the age discount.
  The two pull opposite ways; the engine sees neither → lands on the median.
- **Validates two shipped calls:** a8 de-ruling the "10-Year Rule" into a *tendency* (the
  premium-finish exception **H-C** is real), and the a17/a19 condition caveat.
- **Exposes a checkable bug:** a17/a19 `condition_note_ar` did **not** attach on this widened path
  for the textbook condition case (`condition_note=None`) — verify whether the a10 honest-range
  carries it or it slips through both.
- **Re-confirms the binding data dependency:** calibrating any age/condition adjustment needs
  **confirmed sales** (Sprint 2.16.16, deferred — no source). V001 is **GT-3 (asking, n=1)**;
  our discipline forbids deriving a rule from it. It **motivates**, it does not calibrate.
- **Beta relevance:** beta = villas + land; an old-premium-villa buyer is a core beta user. A bare
  "3.8M" misleads → raises Sprint B + old-stock honesty from "nice" to near beta-blocker.

---

## PART 2 — خطة العمل (work plan, staged per #50 / #38)

| Step | Class | What | Calibration needed? | Gate |
|---|---|---|---|---|
| **B-0** (fast-follow, tiny) | bug / honesty | Verify + fix the a17/a19 `condition_note` not attaching on the **widened** path (Maamoura exposed it). Confirm the dispersed-widened a10 honest-range carries the condition disclosure, or close the gap. | none | reversible (CC) |
| **B-1** (THIS brief — first shippable) | **Gate-2 presentation** | For villa comparison outputs where built-type/condition are **unassessed** (today: always), make the honest surface carry **(a)** the **land-value floor** as an explicit number, **(b)** an **honest range** (land floor → as-is comp median) instead of a lone point when age/condition are unknown, **(c)** an "**old stock tends to clear toward land; condition not assessed**" disclosure. Extends the a10/a14/a17/a19 honesty patterns. **No calibrated value change.** | **none** (presentation/disclosure) | Claude.ai framing + Anas sign-off |
| **B-2** (durable fix, deferred) | **Gate-2 methodology** | **Stage-2 elicitation** (2.22.0b Q&A): user supplies **built-type + condition (+ age)** → engine applies a **provisional, broker-experience-grounded** adjustment (like D5/D6), MUC-clad, that **narrows** the B-1 range. The real R7 fix. | provisional only; true calibration awaits confirmed sales | 2.22.0b UX + Claude.ai RICS framing + multi-AI (#54) + Anas sign-off |
| **B-data** (parallel/ongoing) | data | Confirmed-sale corpus (2.16.16) is the **only** path to calibrate B-2. If 56/647/6 ever sells, V001 → GT-2 = first real **H-A** test. | — | no viable source today (flag) |

**Sequencing recommendation:** B-0 now (CC, reversible) → **B-1 next** (the signed brief below; ships
to beta; in-discipline) → B-2 later (with 2.22.0b). Do **not** bundle (#38). Do **not** calibrate from
n=1 (#discipline).

---

## PART 3 — SPRINT BRIEF (proposal): **B-1 — old-stock / condition honest surfacing**

**One-line:** when a villa's built-type/condition/age are unassessed, **stop asserting a lone point**
that can equal a market-rejected ask — surface the **land floor + an honest range + the old-stock /
condition-unassessed disclosure** — *presentation only, no calibrated value change*.

### Why (the case)
56/647/6 (V001): engine point **3.8M = the 5-year-rejected ask**; real clearing signal is land
(~2.63M) + a modest ready-home premium. The lone point misleads a real buyer; the land component +
the spread + the disclosure are what the user actually needs (see `docs/learnings/LEARNING_2026-05-28_maamoura_old_premium.md` + `VALIDATION_LOG.md` V001).

### Discipline guards (must hold)
- **n=1 → no calibration, no new rule, no weight** derived from Maamoura. B-1 is **presentation/
  disclosure only**; any number it shows (land floor, comp median) is **already computed** by the
  engine — B-1 surfaces it, does not invent it.
- Ship with **MUC** (mandatory when condition/age unassessed). Tone = honest range, not a verdict
  (no BUY/SELL — `feedback_no_verdicts`).
- Backend + copy; if `index.html` is touched → node/mobile 390×844 (else R14 N/A-by-construction).

### §5 audit to run FIRST (Phase 0 — empirical, before any edit)
1. Does the **widened** path expose `land_value` / decomposition today? (a20 live run returned
   `decomposition.land_value=None` for 56/647/6, but v139 had ~2.63M — confirm where it lives now.)
2. What "old / condition-unassessed" **gate signal** is available without an age input? (E22: age
   is NOT auto-detected → an age-gated rule is inert. Options: gate on villa+comparison+no-Stage-2-
   input [≈ always today], or on dispersion, or surface land-floor for **all** villa comp outputs.)
3. Does B-0's `condition_note` actually fire / does a10 honest-range already carry condition copy?
4. **Incidence in the beta cohort:** how many villa lookups are old/condition-sensitive? (scope.)

### Decisions needed (Claude.ai to frame, Anas to sign — present options NEUTRALLY, Rule #59)
- **D1 — headline shape:** for unassessed villas, (a) keep the point + add land-floor as a secondary
  number; (b) replace the point with an **honest range** (land floor → as-is median); (c) **dual
  number** ("teardown/land value" vs "as-is ready"). *(CC leans (c) — it mirrors the buyer's real
  fork, which the owner's "adjacent plot" redirect literally reveals; but it's Claude.ai's framing.)*
- **D2 — gate definition** (from the §5 audit): what triggers the old-stock/condition surface.
- **D3 — RICS framing + copy:** VPS citation for a land-floor + "old stock toward land" disclosure;
  Arabic wording (LRM for any Latin). Pairs with the existing `rics_methodology_note`.
- **D4 — value invariance:** confirm B-1 changes **no** headline value (presentation only) — keeps
  it low-risk + Gate-2-light. *(CC strong recommend: yes, presentation-only.)*
- **D5 — multi-AI (#54):** is the "old stock clears toward land + premium-finish exception" framing
  an evolving-standard / framing question worth GPT-5 + Gemini? *(CC: yes — it's methodology framing.)*
- **D6 — B-1 ↔ B-2 boundary:** B-1 = disclose the spread (no input); B-2 = narrow it via Stage-2
  condition/built-type elicitation (provisional adjustment). Confirm the seam.

### Verification plan (DoD)
- py_compile; isolated test exercising the production surface (Rule #40/E14); DoD matrix
  (392/15/45/N); live smoke incl. **56/565/21** (clean bracket — must stay 2.4M), **54/541/6**
  (thin/widened), **52/903/90** (refusal), and **56/647/6** (the case — must now show land-floor +
  range + disclosure, value path unchanged unless D4 says otherwise).
- Confirm **zero value drift** on the anchors if D4 = presentation-only.

### Out of scope (explicit)
- Any calibrated condition/age **adjustment** (→ B-2). Any **age auto-detection** (separate).
  Land-path changes (villa-only). Confirmed-sales sourcing (→ 2.16.16, no source).

---

*CC proposal — pending Claude.ai methodology framing + multi-AI (#54) + Anas Gate-2 sign-off.
Source case: V001 (56/647/6) + `LEARNING_2026-05-28_maamoura_old_premium.md`. Discipline: n=1
motivates, never calibrates.*
