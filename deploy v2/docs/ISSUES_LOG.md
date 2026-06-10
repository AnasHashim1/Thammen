# THAMMEN — ISSUES LOG (سجلّ مشكلات المشروع)

> **⚠️ STATUS: point-in-time SNAPSHOT (2026-06-09, post-errata §0.2b) — reference & audit depth, NOT line-maintained.** Live work-items = `CLAUDE.md #65a`; live risk layer = `RISK_SUMMARY.md`. Re-issued at stage gates only.

> **Project:** thammen.qa — Qatar residential real-estate Automated Valuation Model (AVM)
> **Methodology frame:** RICS Red Book Global Standards (effective 31 January 2025) — VPGA 10 + VPS 6 + IVS 106 · IVS 2025
> **Product Owner / sole gate authority:** Anas
> **Author lane:** Claude.ai (analyst / independent verifier) — *formulates*; Claude Code (CC) *commits to disk* (`C:\Thammen\deploy v2`)
> **Compiled:** 2026-06-09 (Tuesday)
> **Grounding:** Live `/api/health` probe + the on-disk governance corpus (CLAUDE.md, RISK_REGISTER.md, Empirical_Findings.md, Operational_Rules.md, Session_Log.md, Project_Instructions.md, LAUNCH_READINESS_GATES_v1.md, the PHASE0 recons, CHANGELOG v66–v94, and the 2026-06-09 governance-cleanup directive). **Not** memory — every live number below was measured this session (Rule #58 / #65a).

---

## مُلخَّص تنفيذيّ مُوجَز (Arabic abstract)

هذا سجلّ مشكلات شامل للمشروع، مبنيّ على آخر محادثة-حوكمة (تحوّل-الموقف الموقَّع + التسلسل الموحَّد) وعلى قراءة معمّقة للمصادر الحيّة. يجمع **كل** مشكلة مفتوحة، خطر، علّة، فجوة، بند مؤجَّل، سؤال منهجيّ، تبعيّة تنظيميّة، وبند حوكمة عبر تاريخ المشروع — مع تأريض رقميّ (لا تأطير «محجوب/لا-مصدر»). المبدأ الحاكم الجديد (2026-06-09): **المناهج المؤثِّرة في القيمة تُشحَن مُفصَحة-كإرشاديّة ثم تُحكَم مع نموّ الكوربوس — لا تُؤجَّل لأجل غير مسمّى**. المصدر الأماميّ الوحيد للتسلسل = CLAUDE.md #65a؛ البيتا مسارٌ موازٍ غير-حاجز.

---

# PART 0 — FRONT MATTER

## 0.1 Purpose of this document

This is the project's first consolidated **issues log** — a single living register that gathers, in one place, every:

- **open engineering / methodology issue** (the things that affect *what the engine returns to a user*);
- **risk** (operational and methodology — mirroring and extending `RISK_REGISTER.md`);
- **bug** (the A-series catalogue);
- **data limitation** (MoJ freeze, de-identification, hygiene traps);
- **infrastructure / technical-debt item**;
- **UX / product gap** (the owner-journey remainder);
- **regulatory / compliance dependency**;
- **governance / process issue** (the items the 2026-06-09 cleanup re-framed);
- **deferred / parked item** (with its explicit revival trigger);
- **closed / resolved issue and *failed path*** (kept on the record — Honesty Principle #10: *document failed paths as clearly as successful ones*).

It deliberately does **not** invent priorities. Where an item needs a Product-Owner decision it is marked **«القرار المطلوب»** and routed to Anas. It is **not** a brief and it does **not** replace any signed brief; in particular it does **not** replace the *decomposition-coherence* brief that is still awaiting a Gate-2 signature (see ISS-A07 / Part 5).

## 0.2 How this log was built (provenance discipline)

Per Rule #58 (assumed-vs-actual gap) and Rule #65a (read live state first at the #57 handshake), the "current state" facts here were **measured**, not recalled:

- **Live probe `GET https://thammen.qa/api/health` (2026-06-09 14:40 UTC):**
  - `version`: **3.1.0-sprint2.22.0b.11**
  - `engine_version`: **thammen-sprint2p22p0b11-cost-drc-reanchor**
  - `moj_freshness`: latest_record **2025-12-31**, **days_old 160**, tier **stale**, record_count **25,673**
  - `calibration_freshness`: total_cells **200** (reliable 6 / indicative 10 / fallback 184), last_updated 2026-06-07, outliers_rejected 27, calibratable_listings_seen 3,458
  - `qars_endpoint`: **healthy** (primary 162,496 / legacy 162,497)
  - `security`: CORS locked, rate-limits 5/s · 30/min · 200/h on `cf-connecting-ip`, docs locked
- **Heroku release:** **v180** (per CLAUDE.md #65a; the release number is not surfaced on `/api/health`, but the engine tag `…b11-cost-drc-reanchor` confirms the same ship).
- **Governance corpus** read on disk under `/mnt/project/` (the read-only project-knowledge mirror of `C:\Thammen\deploy v2\docs\`).

Where a fact could only be **reasoned** (not measured this session) it is tagged **assumed~**; where it was measured it is tagged **measured✓** (extends the `ROLES_AND_COMMS` "brief priors" conduct rule).

## 0.2b ERRATA — same-day correction pass (2026-06-09, after a full `Session_Log.md` read)

This log was first issued earlier on 2026-06-09. A same-day audit against the **full `Session_Log.md`** (through §20.45) found it had inherited a **stale framing from the legacy `RISK_REGISTER.md` R9 entry** (never updated after a18). Corrections applied throughout, marked "(errata)":

1. **ISS-A03 / A16 / R9 — re-classified OPEN → CLOSED (a18, v157, 2026-06-03).** §20.18 (measured✓): a18 wired `area_match_key` (NBSP + hamza + sibling-aggregation) into **`build_reference` itself** (the bracket path) + shipped the امريخ الجنوبي→مريخ override; live Marikh = **comparison_thin 5.4M n=15 same-district**; verdict verbatim: «RISK_REGISTER R9 → resolved-as-pool-fix (condition residual = R7/Sprint B)». The cleanup's "promote A16/R9 before floor patches" is **overturned** — it rested on the stale entry. Open Medium bugs = **2 (A5, A15)**, not 3.
2. **Forward sequence corrected** — the old Step 2 ("A16/R9 root after a live Marikh trace") is **removed**; the §20.9 GATED slice moves up. ISS-A04's "after A16" dependency, Fork C's "fold into the A16 sprint", DEF-02/DEF-08's "after A16/R9" triggers, and ISS-D03/D04's "bracket path not yet wired" claims are all corrected.
3. **Omissions added** (found in the same audit): **DEF-12** (report two-values display, MV + forced-sale MV×0.90 — §20.45-deferred), **DEF-13** (soil/geotech factor — §20.45-deferred), the a18 unreachable-name residual + the optional fast-follow (in ISS-A03), and the §20.45 **Heroku-auth deploy lesson** (recorded as an operational note in the companion `RISK_REGISTER_v2.md` R-C cluster).
4. **Surviving truth (unchanged):** the *condition* over-anchor on Marikh (defensible ~3.0–3.4M plain vs the 5.4M thin median) is real — it is **R7**, treated by b6 → b11 → §20.9 → B-2, **not** by any data-path fix.

## 0.3 Legend

**Status:** `OPEN` · `DEFERRED` (scheduled, not yet started) · `PARKED` (blocked on a named trigger) · `MITIGATED` (risk reduced, not eliminated) · `CLOSED` (resolved, with date + evidence) · `FAILED-PATH` (tried, abandoned — kept for memory).

**Severity:** 🔴 high · 🟠 medium · 🟡 low · ⚪ informational/structural.

**Lane / owner:** `PO` (Anas — decision/accountability) · `Claude.ai` (analyst — formulates) · `CC` (developer — implements) · `EXT` (external dependency, not in our hands).

**Gate tags:** **G1** = Hard Gate 1 (production push, explicit per-session Anas consent) · **G2** = Hard Gate 2 (methodology / user-facing output change, Anas sign-off before it lands) · **G3** = Soft Gate 3 (scope beyond the signed brief, flag-and-proceed) · **gate #6** = beta cohort (PO; *now re-framed — see ISS-G03*) · **gate #11** = capture-surface security pass.

## 0.4 The standing methodology principle that governs every "blocked" item (NEW — 2026-06-09)

The 2026-06-09 governance cleanup recorded a **new Empirical principle** that must be read before interpreting any "blocked / deferred-indefinitely / no-viable-source" wording anywhere in the corpus. Stated in full because it changes the *status* of several issues below:

> **Floor-reality (2026-06-09):** Only **n ≥ 20 parcel-linked confirmed sales** calibrate the *precise* coefficient and license any *published* accuracy claim. That bar gates **precision**, it does **not** gate **shipping**. By the standing precedent of **b4** (luxury-new) and **b11** (cost-reanchor), both shipped on **n = 2**, and of **§6** (income guidance): a *value-affecting* method may ship **disclosed-as-indicative** — opt-in, or rail-governed, with **wide MUC** (VPGA 10), a **"calibrated on limited n"** label, and a **`[land_floor, cost]` rail** — and is then **tightened as the ground-truth (GT) corpus grows**. The corpus grows by **(a)** valuer reports / manual confirmed sales (GT-1 / GT-2) and **(b)** organic beta usage — *not* "no source." **Delete** the framing "blocked / deferred indefinitely / no viable source" wherever it is blocking B-2, cost-triangulation, D5/D6, or the error distribution.

This principle is the reason several items historically filed as "DEFERRED INDEFINITELY (no source)" are re-classified in this log as **PARKED on a growing trigger** or **OPEN — ship-disclosed-as-indicative**.

## 0.5 Relationship to the existing registers

This log **mirrors and extends** the existing registers; it does not supersede them. Each issue cross-references its source-of-truth:

| Existing register | Role | This log's relationship |
|---|---|---|
| `CLAUDE.md` (#65a snapshot) | **Single forward source** (launch-gating + engineering-next) | Authoritative for forward state; this log expands each item into a full entry |
| `RISK_REGISTER.md` (R1–R15) | Operational/methodology risk ledger | Re-stated per-issue with current status; R-IDs preserved |
| `Operational_Rules.md` (#1–#65, frozen) | Process rules + scar tissue | Cited by rule number; not duplicated |
| `Empirical_Findings.md` (E1–E23) | Methodology findings | Indexed in Appendix A; issue-bearing findings expanded inline |
| `LAUNCH_READINESS_GATES_v1.md` | Launch-gate register (gates 1–11) | Re-framed per the 2026-06-09 cleanup; gates expanded in Appendix E |
| `Session_Log.md` (§20.x) | Chronological narrative | Cited as the evidence trail (§20.x) |


---

# PART 1 — EXECUTIVE SUMMARY

## 1.1 Live-state snapshot (measured 2026-06-09)

| Dimension | Value (live) | Note |
|---|---|---|
| Engine | `3.1.0-sprint2.22.0b.11` (`cost-drc-reanchor`) | Heroku v180; b11 = §20.9 down-re-anchor (Gate-2 SIGNED) |
| MoJ data | 2025-12-31 · **160 days stale** · 25,673 records | External freeze (ISS-D01); MUC clause active |
| Calibration | 200 cells (6 reliable / 10 indicative / 184 fallback) | Per-area villa-yield DB rebuilt at b5; 1-day fresh |
| QARS / GIS | healthy (primary 162,496 / legacy 162,497) | khazna primary + legacy fallback (R5 mitigated) |
| Security | CORS locked · 5/s 30/min 200/h · docs locked | `/api/feedback` rate-limit still to confirm (gate #11) |
| Capture / instrumentation | **DORMANT** | Writes nothing until flag + counsel-cleared PG (R11) |
| Open Critical/High bugs | **0** | — |
| Open Medium bugs | **2** (A5, A15) | A6/A7/A8/A11 closed; **A16/R9 → resolved-as-pool-fix at a18** (§20.18) — see §0.2b ERRATA |
| Beta | invite-ready under 2026-06-02 self-clearance | Re-framed as a **non-blocking parallel track** (ISS-G03) |

## 1.2 Issue inventory at a glance

> Counts are of *distinct issues catalogued in this log*. Many are cross-linked (e.g. A16 was a bug and, pre-a18, the root of the Marikh over-anchor). The figure in parentheses is "open + parked/deferred".

| Class | Prefix | Open | Parked/Deferred | Mitigated | Closed/Failed (in Part 6) |
|---|---|---|---|---|---|
| Accuracy / methodology | ISS-A | 6 | 4 | — | several |
| Data | ISS-D | 5 | 3 | — | (PN-hash crack = failed-path) |
| Bugs (A-series) | ISS-B | 3 | — | — | A6, A7, A8, A11 |
| Infra / tech-debt | ISS-T | 4 | — | 4 (R5, R12, latency, version-pins) | R2, R6 |
| UX / product | ISS-U | 3 | 2 | — | confirmation-gate, range-as-lead, panels (shipped) |
| Regulatory / compliance | ISS-R | 6 | — | 2 (R13, R11) | open-data licence (R13 sub-item) |
| Governance / process | ISS-G | 7 | — | — | — |

**Top-5 by impact (analyst lean — Anas decides):**

1. **ISS-A04 — §20.9 cost-triangulation GATED slice** (the *durable* R7 over-anchor/under-anchor fix; its DOWN half shipped as b11, the convergent-confirm + UP-lift half remains). This is the single most value-relevant open methodology item.
2. **ISS-A03 / A16 / R9 — CORRECTED (errata, §0.2b):** resolved-as-pool-fix at **a18** (v157, 2026-06-03, §20.18) — `area_match_key` (NBSP + hamza + sibling-aggregation) was wired into `build_reference` itself + the امريخ الجنوبي→مريخ override shipped; live Marikh = **comparison_thin 5.4M n=15 same-district**. The residual over-anchor is **pure R7 condition** (defensible ~3.0–3.4M plain); the cleanup's "promote before floor patches" rested on the stale pre-a18 register entry.
3. **ISS-D08 / gate-4 — no measured error distribution** — the responsible-to-ship accuracy gate; re-framed to "spot-check on manual GT now; statistical distribution is a public-tier requirement."
4. **ISS-R01 / R13 — regulated-activity / Aqarat licence** — the binding **monetization** gate (not a beta gate); التقييم العقاري is named-regulated under Amiri Decision 28/2023.
5. **ISS-A07 — decomposition coherence** — forward item #1; a signed brief is *pending a Gate-2 signature*; live-credibility, ready since b11.

## 1.3 The unified forward sequence (replaces the drifted roadmaps)

Per the 2026-06-09 cleanup, the single forward source is **CLAUDE.md #65a**, and the convenience roadmap in `Project_Instructions §11` is **DEPRECATED → see #65a**. Engineering proceeds on data we control, with **no beta gate**:

1. **Decomposition-coherence fix** — signed brief *pending Gate-2 (Anas)*. Live credibility; ready by b11. → **ISS-A07**
2. **§20.9 GATED slice** (convergent-confirm + UP-lift) — gated on the PO ~0.31 floor + the age recon. *(The previously-listed "A16/R9 root brief" is removed — errata: R9 was resolved at a18.)* → **ISS-A04**
3. **§20.9 GATED slice** (convergence-confirm + the UP-lift) — needs a "system-age → actual-age + CGIS gap" recon and the dilapidated-luxury floor number (PO decision); ships **disclosed-indicative**. → **ISS-A04**
4. **Rent-as-UX** — surface the rent field prominently so `income_led` fires on real traffic (the live payoff of all the §6 work is *UX-gated*, not beta-gated). → **ISS-U02 / ISS-A05**
5. **(parallel / optional):** B-2 disclosed-indicative (ISS-A10) · Phase-2 purity/window R8 (ISS-A02) · A15 (ISS-B02) · A5 (ISS-B01) · capture activation (ISS-R05, PDPPL §8.1/§8.2 + gate #11 security).

**Beta = a parallel, non-blocking track:** collect GT manually + organically; **no cohort, no gate** (ISS-G03).

## 1.4 What the 2026-06-09 governance reframe changes (and why it matters here)

The cleanup directive (DOC-ONLY; no code, no new Gate-2) re-labels several long-standing "dead" framings. The surgical rule it set: **do not delete measured facts** (the closed feeds, MoJ-not-geocoded, the PN-hash closure — all *true*, all stay); **change only the conclusion built on them.** The six edits and their issue-level consequences:

1. **"blocked / deferred-indefinitely / no source"** → the §0.4 ship-disclosed-as-indicative principle. *Consequence:* ISS-A10 (B-2), ISS-A04 (cost), ISS-D06 (D5/D6), ISS-D08 (error distribution) move from "dead" to "shippable-disclosed / parked-on-a-growing-trigger."
2. **MME apartments "BLOCKED (auth)"** → **out of v1 scope** (a villas+land product); auth is a *future-scope dependency, not a current blocker*. *Consequence:* ISS-D05 re-classed.
3. **Mthamen "deferred + 3 revival conditions"** → **CLOSED — methodology reference only; §20.9 independent DRC replaced it**. *Consequence:* ISS-G04 records the closure; the §20.2–20.4 methodology stays as reference.
4. **A16 / R9** → **promoted** by the cleanup — **[ERRATA, same day: OVERTURNED.** §20.18 shows a18 (v157, 2026-06-03) had already wired `area_match_key` into `build_reference` (the bracket path) and resolved R9 as a pool-fix; the promotion rested on the stale legacy register entry. The Marikh residual is **R7 condition**, not a source-data starve.**]**
5. **Beta** → **removed as a gate** from #65a; **gate #6 (cohort) deleted**; gate-4 re-framed ("spot-check on manual GT now; statistical distribution = public-tier"); income "beta-gated" → **UX-gated**; the conservative R13 framing (free / "not a certified valuation" / no-paid) **kept** but labelled an **R13 cover, not a beta ritual**. *Consequence:* ISS-G03, ISS-D08, ISS-U02 re-framed.
6. **Governance** → **CLAUDE.md #65a = the single forward source**; `Project_Instructions §11` convenience-roadmap marked **DEPRECATED → #65a**; LAUNCH_GATES reconciled. *Consequence:* ISS-G01.

## 1.5 Critical-path narrative (one paragraph)

The product is **engineering-active and beta-invite-ready**; nothing in the engineering queue blocks an invite, and nothing in the invite blocks engineering. The *value*-critical work is the **R7 family** — the engine returns a comparable-pool central tendency that is blind to where the subject sits in it, so it **over-anchors** weak/old stock (Marikh 54/541/6, 5.4M vs a defensible ~3.0M) and **under-anchors** strong/new stock (Abu Hamour 56/565/21, 2.4M vs a defensible ~2.5–2.8M; and V002/V003, new villas that *sold* at 4.0M while the engine said 2.4–2.5M, a −37/−40% miss). The **durable fix** is the §20.9 cost-triangulation: its DOWN half shipped (b11 re-anchors over-anchored old stock to a cost-informed floor); the UP-lift + convergence-confirm half (ISS-A04) is the next engineering item (the source-data starve root was already fixed at a18 — see the ISS-A03 errata). The **income** path (§6) is fully built and ships value-disclosed, but its live payoff needs a **rent field surfaced in the UX** (ISS-U02). The two binding *external/decision* gates are **regulatory** (Aqarat licence before any *paid* access — ISS-R01) and **accuracy measurement** (an error distribution — ISS-D08), both of which the beta itself helps close by generating GT. The recurring *process* risk is **cross-surface state drift** (R1/R3) — mitigated by the Rule #57 live handshake that produced this very document.

---

# PART 2 — METHODOLOGY OF THIS ISSUES LOG

## 2.1 What counts as an "issue" here

An issue is anything that (a) changes or could change *what a user sees*, (b) constrains the product's correctness, lawfulness, or credibility, or (c) is process scar-tissue that could re-bite. A *feature request* is **not** an issue unless its absence is itself a defect (e.g. "no error distribution" is an issue because shipping a number without one is a credibility problem). A *finding* (E-rule) is included only where it encodes a live constraint.

## 2.2 Classification taxonomy & ID scheme

IDs are `ISS-<class><nn>`: **A** accuracy/methodology · **D** data · **B** bug · **T** infra/tech-debt · **U** UX/product · **R** regulatory/compliance · **G** governance/process. IDs are append-only; a closed issue keeps its ID and moves to Part 6 with a closure note. Where an issue maps to an existing R# (risk) or A# (bug), both IDs are shown.

## 2.3 Per-issue template

Each open entry carries: a one-line **header block** (Class · Status · Severity · Lane · Gates · Cross-refs · First-logged), a **Summary**, **Evidence / detail** (grounded with measured numbers, code anchors, anchor cases), **Root cause** (where applicable), **Impact**, **Reproduction** (bugs), **Current mitigation / shipped state**, **Remediation / next action**, **Dependencies / blockers**, and a **«القرار المطلوب»** line where a PO decision gates progress.

## 2.4 The "document failed paths" rule

Per Honesty Principle #10 and the standing instruction that *"future Claude must know which roads have been tried and failed,"* Part 6 records not only resolved issues but **abandoned approaches** (Mthamen live integration; the PN-hash inversion; the secretary/brokerage confirmed-sales feeds; the Stage-1 input-honesty premise; the symmetric-± range; the land-to-median floor). A road tried-and-failed is as load-bearing as a road that worked.

## 2.5 Reading order

Part 3 is the substance (open issues, by class). Part 4 is parked/deferred with triggers. Part 5 is the forward sequence (the actionable plan). Part 6 is institutional memory. Part 7 is reference (indices, anchors, glossary). A reader who wants *only* "what's next" should read §1.3 + Part 5; a reader who wants *"is this safe/lawful to ship"* should read ISS-R*, ISS-D08, and ISS-G07.


---

# PART 3 — OPEN ENGINEERING / METHODOLOGY ISSUES

This is the substance of the log. Entries are grouped by class. Accuracy/methodology (ISS-A) is first because it is the most value-relevant cluster and most of it descends from one master defect (R7).

## 3.A — Accuracy & methodology issues (the R7 family + the income/cost/decomposition tracks)

### ISS-A01 — Built-type + condition blindness (bidirectional) — the master accuracy defect

> **Class** accuracy · **Status** OPEN (partially mitigated) · **Severity** 🔴 · **Lane** Claude.ai → CC, G2 · **Cross-refs** RISK_REGISTER **R7**, **R8**; Empirical **E23**, **E4**; ISS-A02/A03/A04/A10; anchors 54/541/6, 56/565/21, V001/V002/V003 · **First logged** 2026-05-31 (generalised)

**Summary.** The market-comparison engine returns the comparable **pool's central tendency** (a weighted median over size-bracket × area × 24-month window) and is **blind to where the subject sits inside that distribution** — blind to built-type sub-class, condition, finish, and built-up area (BUA). The error is **bidirectional**: it **over-anchors** below-average-condition subjects and **under-anchors** above-average-condition ones. The earlier "widened-only / over-anchor-only" framing was too narrow; the corrected framing (2026-05-31) is that *both* comparison paths (widened **and** bracket) are affected, and "bracket path validated clean" holds **only for average-condition subjects.**

**Evidence / detail (measured✓).**
- **Over-anchor (widened path):** Marikh **54/541/6** — a plain 2-storey + annex, ordinary finish, ~20 yr villa — was valued at **681 ر.ق/ft² @ 24-month** (bracketed) vs **509** unbracketed (**+34%**). Phase-1b refined the mechanism: the over-anchor is **window-driven**, not "+penthouse." The STANDALONE_VILLA bracket [490–736] collapses **681 (24mo, n=29) → 554 (36mo) → 517 (FULL, n=43)**; penthouse rows are *cheaper* (517) than strict villas (790), so folding penthouse in **dilutes** the median (790→681) rather than inflating it. Defensible plain ceiling ≈ **512–517/ft²**.
- **Under-anchor (bracket path):** Abu Hamour **56/565/21** — an excellent G+1 with a secure government lease — the engine returns **2.5M (~P68)**, under-anchoring ~10%. The pool is *tight* (dispersion **0.211**, correctly **not** gated by the a10 dispersion gate) but the subject sits at the **upper** end; market median ≈ income@5% ≈ 2.5M, P90 (567/ft²) ≈ income@4.5% ≈ 2.75M → a **defensible RANGE ~2.5–2.8M** (market + income basis, **not** replacement cost). **Do not** treat the 2.5M as a validated point.
- **Confirmed-sale evidence (the strongest):** **V002 / V003** (Abu Hamour 56/565/10 + /12) — the project's **first GT-2 confirmed sales** — new premium villas that **SOLD at 4.0M each**, while the engine returned **2.4–2.5M** = a **−37 / −40% under-anchor**. **V001** (Maamoura 56/647/6) — old premium villa, **over-anchors** the rejected 3.8M ask.

**Root cause.** `geo_reference_v2._categorize` (≈ line 105) lumps {basic villa / 2-storey+annex / +penthouse / مسكن / مجلس / فيلتان} into a single `'villa'` category; **condition (finish / maintenance / lease) is not an input at all**. MoJ records plot area + price + a coarse built-type label but carries **no BUA, no condition, no finish** — so the market method has **no shared field** on the two dimensions (condition, BUA) that most explain villa price dispersion. (Built-type *is* shared but is currently lumped.)

**Impact.** Directly degrades headline accuracy on the most common asset (villas), in *both* directions, and is the dominant contributor to the project's known accuracy gap. It is the reason the four headline anchors are tracked-for-drift rather than treated as validated point targets.

**Current mitigation / shipped state.**
- **a10** Stage-1 dispersion gate (T = 0.30) → honest P25–P75 range + tier downgrade + widened MUC on *dispersed* widened pools. *Necessary, not sufficient* — it catches the dispersed over-anchor case but **not** the tight-pool-above-average under-anchor case (56/565/21).
- **a14** extended the same honest-range to the *bracket-success* path (closed R10).
- **a11 / a12** purity: residential-usage filter + pure-villa pool (house/فيلتان/compound rows removed).
- **b4** condition/value axis (extremes-only: `teardown` ↓, `new`+luxury ↑, `penthouse` ×2.5 BUA).
- **b5–b8** income calibration + triangulation (the *income* leg of the durable fix).
- **b11** §20.9 cost down-re-anchor (the DOWN leg of the durable fix).

**Remediation / next action.** The *real* fix is **built-type / condition stratification in both directions across all areas**, delivered via the **§20.9 cost-triangulation** (ISS-A04) as a secondary independent approach, **+ the 2.22.0b Stage-2 Q&A** that supplies built-type + condition from the user (QARS carries no built-type; the staged flow supplies it). B-2 (ISS-A10) is the condition-elicitation mechanism, PARKED on n≥20 but shippable-disclosed under §0.4.

**Dependencies / blockers.** §20.9 GATED slice (ISS-A04); Stage-2 elicitation UX (ISS-U02); GT corpus growth (ISS-D07/D08). **Not** blocked on broker data sourcing — the staged flow supplies built-type/condition directly.

**«القرار المطلوب».** None new — the direction is signed (cost-triangulation approved; B-2 Gate-2 signed 2026-06-05). The PO decisions that *unblock the next slice* live in ISS-A04 (the dilapidated-luxury floor number + the actual-vs-system age handling).

---

### ISS-A02 — Comparable-pool purity + thin-window volatility (R8)

> **Class** accuracy · **Status** PARKED (Phase-2, separate signed brief) · **Severity** 🟡 · **Lane** Claude.ai → CC, G2 · **Cross-refs** R8, R7, E23, E22, Rule #52 · **First logged** 2026-05-31 (pinned by Phase-1b)

**Summary.** Two distinct levers behind the R7 over-anchor, both **measured** and **pinned** as Phase-2 design inputs but **not yet implemented**: (1) **thin-window volatility** (geo_v2's 24-month default), and (2) **pool impurity** (type-based pooling with no residential-usage filter).

**Evidence / detail (measured✓).**
- **Window (B1):** STANDALONE_VILLA is the volatile stratum — 24-month median sits **+8–11% above FULL** (genuine recent appreciation; e.g. the 600–900 cell runs 480→459→432 at 24/36/FULL). LAND and HOUSE are window-stable. Cell volatility 24mo→FULL: thin cells (<10) move >15% in **17%** of cells vs **4%** at n≥20; the 24mo→36mo step is gentle (median ~1.2%); staleness drift on reliable cells is **+3.3%**.
- **Purity (B2):** a residential-usage filter removes **~22%** of `cat=villa` rows → pooled median **−5%** (in-bracket −2 to −4%); compound (فيلتان) removal **≤3%**. Penthouse fold-in is globally negligible (Δ=1) but **Marikh-material** (20 of 74 of Qatar's penthouses sit in that bracket; **dilutive** there).

**Root cause.** `geo_reference_v2` pools comparables by `نوع العقار` via `_categorize` (type-based, no usage filter) over a fixed 24-month window with no n-adaptive widening.

**Impact.** Contributes to both the over-anchor (window recency) and pool contamination; **orthogonal** to Marikh's specific over-anchor (the Marikh bracket cascade is 517→517→517 at 24/36/FULL — i.e. its over-anchor is dispersion-, not window-, driven there). Low standalone severity because the dispersion gate (a10/a14) already catches the dangerous dispersed pools.

**Current mitigation / shipped state.** a11/a12 shipped the purity filters on the comparison driver (the −5% / pure-villa effect is live). The **window-adaptive** half is *not* shipped.

**Remediation / next action (Phase-2 design, PINNED).** Window: 24mo default; if a cell has **n < 20** widen to **36mo** then FULL — **prefer 36mo** (cuts ~half the recency drift, gentle move). **Caveat:** n alone is insufficient → **pair with the a10 dispersion gate** for dispersed-but-sufficient pools (Marikh n=29 passes T=20 yet is +32% over FULL — cross-ref E23). Reliability context: at 24mo only **83/787 (10.5%)** of cells reach n≥20 → **credibility shrinkage is essential** (a13 already shipped the shrinkage for thin cells). Phase-2 = a separate signed brief.

**Dependencies / blockers.** None data-side (the analysis is done); needs a signed Gate-2 brief and a CC sprint. Lower priority than ISS-A04.

**«القرار المطلوب».** Whether to schedule Phase-2 now or after the §20.9 GATED slice (analyst lean: after — the dispersion gate already neutralises the dangerous cases).

---

### ISS-A03 — Bracket-path area-name under-match (A16 / R9) — **RESOLVED-as-pool-fix at a18 (ERRATA 2026-06-09)**

> **Class** accuracy + bug · **Status** **CLOSED 2026-06-03 (a18, Heroku v157)** — corrected from OPEN by the same-day errata pass (§0.2b) · **Severity** was 🟠 · **Lane** CC (shipped) · **Cross-refs** A16, **R9**, R7, §20.18, CHANGELOG_v70, `BRIEF_R9_area_name_reconciliation.md` · **First logged** 2026-05 (§20.10.1); **mis-promoted** 2026-06-09 (cleanup); **corrected** same day (full Session_Log read)

**What this entry previously claimed (wrong).** That the bracket matcher still used exact string equality (no NBSP/hamza/sibling merge), that the floor and bracket paths diverged, and that fixing it required "its own sprint after a live Marikh trace." That framing was inherited from the stale legacy `RISK_REGISTER.md` R9 entry, which predates a18 and was never updated.

**What actually shipped (measured✓, §20.18).** Sprint **2.22.0a.18** (2026-06-03, Heroku v157, commit `d69d9c0`): `moj_reference.area_match_key` (whitespace/NBSP collapse + hamza-fold + trailing-zone strip → **sibling aggregation**) wired into **`build_reference` + `compute_trend`** (the bracket path — "was exact") **and** `resolve_moj_area_name`; overrides keep **A16 امريخ الجنوبي→مريخ** + Pearl/New-Slata/Lijmiliya. The brief's original "highest-count→bare-parent" was **REJECTED at the الثمامة-46 hard gate** (MoJ files recent txns under sub-zone labels, stale under the bare parent) → sibling aggregation adopted on PO «افعل الأصوب». Safety: hamza-fold collision-free (0 distinct merges); 15-district sweep = 0 silent clean-bracket regressions.

**The live result (the fact that overturns the old framing).** Marikh 54/541/6 → **comparison_thin 5,400,000 n=15, same-district «مريخ»** (was comparison_widened 4.5M n=29 cross-district). The value *rose* because the same-district pool genuinely sells higher. **a18 fixed WHICH pool — not condition.** Session_Log verdict, verbatim: «RISK_REGISTER R9 → resolved-as-pool-fix (condition residual = R7/Sprint B)».

**Surviving residuals (small, monitored).** (1) **فريج العسيري** (26 villa txns — no GIS ANAME contains «العسيري») + thin «المطار» (12): unreachable by any normalization (~**0.25%** of villa lookups) — they widen/refuse honestly. (2) The a18 **fast-follow** (never scheduled): one DIRECT live hit on a sub-zone subject (معيذر/نعيجة address) to demonstrate aggregation end-to-end live — optional, low priority, no gate. (3) The legacy `RISK_REGISTER.md` R9 row itself still reads OPEN → owed a one-line closure edit (doc-drift, ISS-G01-class / Rule #63).

**Consequence for the forward sequence.** The "A16/R9 root brief after a live Marikh trace" step is **removed** (Part 5 corrected). The Marikh over-anchor work is entirely the **R7 condition family**: b6 widen_down → b11 cost_reanchor_down (floor 1.9M→2.4M) → the §20.9 GATED slice (ISS-A04) → B-2 (DEF-01).

**«القرار المطلوب».** لا قرار — مُغلق؛ يتبقّى تعديل سطر R9 في `RISK_REGISTER.md` القانوني (يطويه CC في أقرب commit توثيقي).


### ISS-A04 — §20.9 cost-triangulation: the GATED slice (convergent-confirm + the UP-lift) — the durable R7 fix's remaining half

> **Class** accuracy · **Status** OPEN (DOWN half shipped b11; this is the remainder) · **Severity** 🔴 · **Lane** Claude.ai brief → CC, **G2 value-affecting** · **Cross-refs** §20.9, METHODOLOGY_cost_triangulation_v1, R7, E15, ISS-A01/A07, anchors V001/V002/V003 · **First logged** 2026-05-31 (direction approved); slice split 2026-06-09

**Summary.** An **independent RICS Cost Approach (DRC)** — `Value ≈ Land_floor + Depreciated_Building` — as a **secondary, independent** valuation approach (not a cross-check, not a blend) that observes the variables the market method is blind to (BUA, finish, effective age) via **subject-intrinsic** data, so it needs **no comparables' BUA** (which don't exist in MoJ). The **DOWN slice shipped as b11** (re-anchors a thin/widened **old over-anchored** villa down to the cost as an *informed floor*). The **GATED slice that remains** = **convergent-confirm** (when market and cost agree → raise confidence; when they diverge → flag atypical, widen, route to review) **+ the UP-lift** (lift an *under-anchored* strong/new villa toward the cost-supported value — e.g. V002/V003 toward ~4.0M, V001 a trim).

**Evidence / detail.**
- Hand-proven on **54/541/6**: a 35×17.5 m plot − legal R1 setbacks (front 5 / side 3 / rear 3, **E15**, corrected at b9) → a max-buildable footprint of **~238–311 m²** → BUA × depreciated rate + land → **~2.8–3.0M** vs the blind **5.4M**. The b10 geometric footprint (rotation-safe edge-pairing on the plot ring, **not** bbox) is the **BUA input** and is *already shipped* — the prerequisite is in place.
- Calibration anchor: the **Al Manara bank Cost-Approach report (TD 93317)** for V001 used **~2,380 ر.ق/m²** for that premium build (ordinary < premium). The cost model's segment Market/DRC ratio is the diagnostic.
- **b9 system-age behaviour:** the QARS `SURVEYED_DATE` age is a **FLOOR** (the building is *at least* this old), so it is **conservative / immune** for the DOWN slice (V001 at age 17 → +22%, no fire; at the actual 25 → +30.6%, would fire). The **ship-now DOWN slice MUST use the system age** to stay conservative; the UP/convergence slice **needs the *actual* age** and therefore a CGIS-vs-actual age-gap recon.

**Root cause (of why it's gated, not shipped whole).** Three open parameter/robustness items make the UP/convergence half a value-affecting Gate-2 that needs its own §5 audit: (1) **actual-vs-system age handling** (system age is a floor; lifting value needs the real effective age); (2) a **CGIS-vs-actual age-gap recon** (§11 ج); (3) the **PO dilapidated-luxury floor number** (~0.31 building-value retention; does **not** affect the DOWN ship-now slice).

**Calibration discipline (both AIs flagged independently — load-bearing).** Do **NOT** calibrate the cost model so "average villas reproduce the MoJ median" — that kills the method's *independence* (GPT) and *imports the market's blindness* (Gemini). Instead: build DRC as a pure physical estimate (RCN − market-derived depreciation), then **separately** observe the **Market/DRC ratio by segment** (district, age, prestige) — which can be **negative** (economic obsolescence). The subject's deviation from the segment-typical ratio is the diagnostic. **No hard valuation ceiling** — district P95 is a *soft* warning/review trigger, not a cap. Any calibration uses an **isolated curated GT** (known BUA/age/finish), **never** the raw MoJ median (this is **open decision #4** in the methodology record).

**Impact.** This is the **durable, two-directional** fix for R7 (ISS-A01). Shipping it disclosed-as-indicative (per §0.4) makes the engine *converge* on the confirmed sales it currently misses by 37–40% and *trim* the old-premium over-anchors — the single largest accuracy improvement available.

**Current mitigation / shipped state.** b11 (DOWN re-anchor) is live: Marikh floor 1.9M → **2.4M** `cost_reanchor_down` (cost 2,378,094; undercut 128%; BUA 479), precedence `income_led > cost_reanchor > widen_down`, age-gate ≥10, >30% undercut threshold, MUC high, **no invented central** (raises the *floor*, not the central — that is the honest residual and the gated slice). V001/Abu Hamour/apartment byte-identical.

**Remediation / next action.** **Forward item #3.** A Claude.ai-drafted Gate-2 brief that: (a) commissions the CGIS-vs-actual age-gap recon; (b) takes the PO dilapidated-luxury floor number; (c) wires the convergence-confirm + UP-lift with the segment Market/DRC ratio, all **disclosed-indicative** (MUC high, "calibrated on limited n", `[land_floor, cost]` rail) per §0.4; (d) its own §5 audit + R14.

**Dependencies / blockers.** The age-gap recon + the PO floor number (below). *(Errata: the previously-claimed "after A16/ISS-A03" sequencing is void — a18 had already fixed the pool; the cost slice re-anchors on the post-a18 pools that are live today.)*

**«القرار المطلوب» (PO).** (1) The **dilapidated-luxury building-value-retention floor** (~0.31 proposed). (2) Approval to commission the **actual-vs-system age-gap recon** (§11 ج). (3) Open-decision-#4: the **isolated curated GT source** for any cost calibration (this is the GT-corpus question — ISS-D07).

---

### ISS-A05 — §6 income-triangulation v2 remainder (Fork C + age-rent)

> **Class** accuracy · **Status** OPEN (core shipped b6–b8; remainder deferred) · **Severity** 🟠 · **Lane** Claude.ai brief → CC, G2 · **Cross-refs** §20.40–20.42, PHASE0_income_triangulation_recon, E22, ISS-A06/U02 · **First logged** 2026-06 (deferred at b6/b7)

**Summary.** The income leg of the durable fix is largely shipped: **`income_led`** (a grounded subject rent + a calibrated reliable/indicative cap-rate cell → income *leads* the villa headline, comparison demoted, with a circularity guard) and the b7 cross-bracket **yield-borrowing** and b8 **opex alignment**. Two items remain deferred: **Fork C** (the a18/override-aware cap-rate lookup) and **(ii) age-rent** (an age-adjusted rent input).

**Evidence / detail (measured✓).**
- **Fork C** (confirmed gap, robustness): `_lookup_calibrated_cap_rate` should route through `resolve_moj_area_name` so the lookup is alias/override-aware (the same normalization *class* a18 fixed on the comparison side, still open on the *yield* side). Today it works GIS↔GIS via `district_aname`; Fork C hardens the override case.
- **(ii) age-rent:** an age-adjusted rent term — **gated on auto-age reliability (E22)**: an adjustment gated on a non-auto-detected input is **inert on the default flow**, so age-rent only pays off once auto-age is reliable (which is the same age-handling problem as ISS-A04).
- **opex 0.20** alignment is **done** (b8): NOI opex now matches the calibration opex (villa 0.20, was 0.23) on calibrated cap rates → closed the **−3.75%** villa-calibrated income understatement; compound/fallback keep 0.23, byte-identical on no-rent traffic.

**Root cause / why deferred.** The income path's *live payoff* is **UX-gated**, not code-gated: `income_led` only fires when a **subject-specific rent** is supplied, and the rent field is not prominent in the flow (ISS-U02). So Fork C and age-rent are robustness/precision refinements whose payoff is bounded until rents actually flow.

**Impact.** Medium: improves let-asset and rented-villa accuracy; the structural win (income leads on a grounded rent) is already live and value-disclosed.

**Current mitigation / shipped state.** b6 income_led + widen_down; b7 yield-borrowing (borrows the area's usable 400–600 cell when the subject's bracket has none, MUC-high, `[land_floor,cost]` rail); b8 opex align. All Gate-2-signed and live.

**Remediation / next action.** Fork C stands alone in the §6 v2 remainder *(errata: there is no "A16 normalization sprint" — a18 shipped that; Fork C applies the same `resolve_moj_area_name` plumbing to the yield lookup)*. Hold age-rent until auto-age is reliable (couples to ISS-A04's age recon). **Forward item #4's** enabler is the rent-as-UX surfacing (ISS-U02), not these two.

**Dependencies / blockers.** Rent-as-UX (ISS-U02) for the payoff; the age recon (ISS-A04) for age-rent.

**«القرار المطلوب».** Whether to schedule Fork C within the §6 v2 remainder (analyst lean: yes — cheap robustness, same plumbing as a18).

---

### ISS-A06 — 600–900 villa yield cells are data-infeasible (the borrowing workaround's residual)

> **Class** accuracy + data · **Status** OPEN (worked-around at b7; residual disclosed) · **Severity** 🟡 · **Lane** CC/data · **Cross-refs** PHASE0_R7_income_v2_600-900_recon, §20.41, ISS-A05/A03 · **First logged** 2026-06 (recon NO-GO)

**Summary.** Calibrating per-area **600–900 m² villa yield cells** is **data-infeasible** — there are **0 / 187** usable villa cells (reliable/indicative) at 600–900. Usable cells exist only at **400–600 (13)** and **900–1500 (3)**. The §20.38 per-area deep crawl (3,458 listings) already tried and produced **no** usable 600–900 cell anywhere. The 600–900 villa bracket is systematically thin on **both** sides (large villas rent thinly / are owner-occupied; MoJ 600–900 sales are sparse).

**Evidence / detail (measured✓).** المعمورة 600–900 SALE n=7 (frozen); امريخ 600–900 RENT n=0. The binding block is genuine market thinness, not a query bug.

**Impact.** The standard headline anchors (Marikh 54/541/6, villa-6 المعمورة 56/647/6) live in the **600–900** bracket, so without 600–900 cells they could only **widen_down**, never **income-lead** — even with a rent. The b7 **borrowing** workaround lets them lead by borrowing the area's usable **400–600** cell (with disclosure + MUC-high + the `[land_floor,cost]` rail). The **residual**: the 600–900 income lead is *borrowed*, not native — a disclosed approximation.

**Current mitigation / shipped state.** b7 borrowing is live and decisive (live smoke: 54/541/6 default 600–900 + rent → income_led 2.7M via `borrowed=True from=400-600`, MUC high — the keystone that was widen_down in b6).

**Remediation / next action.** None purely technical — the only true unblock is **more 600–900 data** (organic beta + GT corpus, §0.4). Keep the borrowing disclosure. Re-test cell feasibility after the corpus grows.

**Dependencies / blockers.** GT corpus growth (ISS-D07); MoJ unfreeze (ISS-D01).

**«القرار المطلوب».** None — accept the borrowing residual as the data-feasible answer (already the live behaviour).

---

### ISS-A07 — Decomposition coherence (land + implied building reconciliation) — forward item #1

> **Class** accuracy/presentation · **Status** OPEN — **signed brief pending Gate-2 (Anas)** · **Severity** 🟠 · **Lane** Claude.ai brief → CC, G2 · **Cross-refs** a21 `_villa_value_floor`, B-1, ISS-A01, §1.3 item #1 · **First logged** forward item, 2026-06-09

**Summary.** The villa **value decomposition** (the B-1 land-value FLOOR + implied-building residual surfaced beside the condition caveat) needs a **coherence pass** so the displayed land + implied-building components reconcile cleanly with the headline (and with each other) across the paths that produce them. This is the **first** item in the unified forward sequence, is **live-credibility** (it's what an owner reads under the number), and is **ready since b11**. A signed brief exists **pending a Gate-2 signature** — this issues log **does not** replace it.

**Evidence / detail.** B-1 surfaces a `value_floor` block for villa/house via `evaluate_unified._villa_value_floor`: it prefers `value_decomposition.land` (F2) and otherwise recomputes `land_ppm² × plot` from the `moj_reference` land category (F1, *independent* of Patch-C) so the floor surfaces even for the land-priced cohort (~10% / 0%-reliable) where `_decompose_value` returns None; the implied building is **clamped ≥ 0** and framed as «مساهمة البناء الضمنية … تخصيص حسابي» (contribution / mathematical allocation, **not** a determination). The coherence concern is that the *displayed* land + implied-building must agree with the headline and across the F1/F2 paths and the strata-card land (which was itself reconciled at a23/R15) — so the owner never sees two land numbers that disagree.

**Impact.** Credibility / trust: an owner who sees a headline, a land floor, and an implied building that don't add up loses confidence in the whole estimate. Presentation-class (no new valuation logic intended), but it touches a user-facing surface → **G2**.

**Current mitigation / shipped state.** B-1 (a21) shipped presentation-only, every value byte-identical; a22 refined the framing (HBU-premise component / contribution); a23/R15 reconciled the strata-card land to the floor's `area_match_key`. The coherence pass is the next refinement on top.

**Remediation / next action.** **Forward item #1.** Sign the pending Gate-2 brief; CC implements the coherence pass; R14 + value-invariance (presentation-class).

**Dependencies / blockers.** **The Gate-2 signature (Anas).** No data/technical blocker.

**«القرار المطلوب» (PO).** **Sign the decomposition-coherence brief** so CC can proceed (the analyst is "ready to take it to the next signature").

---

### ISS-A08 — MoJ self-calibration is structurally BLOCKED (E12) — the de-identification ceiling

> **Class** accuracy/data · **Status** PARKED (blocked-cryptographic + blocked-ethical) — *re-framed*, see below · **Severity** 🟠 · **Lane** EXT / PO · **Cross-refs** **E12**, Rule #45, ISS-D02/D07 · **First logged** 2026-05-20; closed-as-uncrackable 2026-05-21

**Summary.** Any attribute premium derived by **self-calibrating on the MoJ dataset** (corner-plot premium, condition premium, etc.) is **infeasible** because the MoJ weekly bulletin is **not geocoded**: its `رقم العقار المرجعي` is an opaque `PN…` hash (**0 / 26,719 numeric**) with no PIN / coordinates / street, so no GIS attribute detector can tag MoJ sales. E12 activates only when a **PIN-keyed sale source** exists.

**Evidence / detail (measured✓).** Full-corpus hash analysis (n = 26,719; 26,128 distinct): variable 9–13-hex body (rules out fixed-width truncated hashes); unimodal/banded length (rules out keyless mod-2^k); per-nibble entropy ≈ 4.000 bits (cryptographic output); gcd(values)=gcd(diffs)=1 (not affine/XOR of PIN); PIN-embedding slices at chance baseline; deterministic per parcel across years (no salt) ⇒ a **keyed PRP/cipher (or keyed MAC)** over a bounded internal-id domain — uncrackable without secret-key recovery. Even a hypothetical inversion yields MoJ's *internal* parcel id, not the GIS PIN (no published crosswalk).

**Ethical hard line (2026-05-21 decision).** The encryption is a deliberate MoJ **de-identification** control; inverting it is **re-identification** of pseudonymised government data. **No oracle was built; no >100-record validation was run — by decision**, even if it had been crackable. Any future proposal to crack `encrypted_parcel_number` or build a MoJ→GIS re-identification map → **STOP** (recall: "تذكر E12" / "تذكر تحليل تشفير العدل").

**Impact.** This is the **structural ceiling** behind several "blocked" items: attribute premiums, the error distribution (you can't locate a MoJ sale to a parcel to score a prediction against it — Rule #45), and the cost-model calibration GT. It is *why* B-1 is presentation-only and *why* condition is elicited (not detected).

**Re-frame (2026-06-09, §0.4).** E12 stays cryptographically/ethically BLOCKED **as a MoJ-self-calibration path** — that fact is true and stays. But the *conclusion* "therefore attribute/condition work is dead" is **wrong**: the unblock path is a **genuinely PIN-keyed T1 sale source**, which the **GT corpus** (valuer reports + manual confirmed sales + organic beta — ISS-D07) supplies incrementally. So premiums/condition ship **disclosed-as-indicative** on small GT and tighten as it grows; they are **not** waiting on cracking the hash.

**Remediation / next action.** Grow the GT corpus (ISS-D07). Never attempt hash inversion. Treat E12 as a permanent constraint on *one* path, not on the goal.

**Dependencies / blockers.** A PIN-keyed sale source (GT corpus) or verified MME geocoding (ISS-D05).

**«القرار المطلوب».** None — the constraint is settled; the re-frame is recorded.

---

### ISS-A09 — Condition descriptors from listing text (R7 NLP idea)

> **Class** accuracy (exploratory) · **Status** OPEN — idea / future · **Severity** 🟡 · **Lane** Claude.ai/CC (exploratory) · **Cross-refs** R7, E1/E3, ISS-A01/A10 · **First logged** 2026-06 (Q-session idea)

**Summary.** Sale/rent **listings** must never enter the valuation as price evidence (E1/E3 — asking premiums are +70%/+160% over MoJ median, condition-blind; listings appear only in the sentiment panel). But the **free-text description** of a listing carries **condition descriptors** ("renovated", "new", "needs work", "luxury finish") that could feed the condition axis. The useful extraction is the **descriptor**, not the price.

**Evidence / detail.** The Q-session surfaced that sale listings would *widen* the villa over-anchor if used as price evidence (asking premium +70%/+160%), confirming E1/E3 — but the same text is a candidate **condition signal**. This is a hard NLP + PIN-matching problem (you must tie the descriptor to a parcel/subject).

**Impact.** Potentially a scalable, no-extra-survey way to populate the condition axis that R7 needs — but speculative and brittle.

**Current mitigation / shipped state.** None — idea only. Listings remain display-only in the sentiment panel.

**Remediation / next action.** Park as a future exploration; revisit only after B-2 elicitation (ISS-A10) and the GT corpus give a labelled set to validate an extractor against. Strictly **descriptor-only**, never price.

**Dependencies / blockers.** A labelled GT set; PIN-matching of listings (no current source). Lower priority than every other ISS-A item.

**«القرار المطلوب».** None now — logged as a future idea.

---

### ISS-A10 — B-2 condition-axis mechanism (the durable no-rent gap-narrower) — PARKED, but shippable-disclosed

> **Class** accuracy · **Status** PARKED (Gate-2 SIGNED 2026-06-05; resume trigger n≥20) — *shippable-disclosed under §0.4* · **Severity** 🟠 · **Lane** Claude.ai brief → CC, G2 · **Cross-refs** BRIEF_SprintB2_mechanism_elicitation_SIGNED, PHASE0_B2_condition_recon, R7, E4, §20.27, anchors V001/V002/V003 · **First logged** 2026-06-03; signed 2026-06-05

**Summary.** B-2 is the **condition-elicitation mechanism** that supplies the missing condition/built-type axis R7 needs, with **two levers**: **UP** (a finish / new-build premium on comparable ppm²) and **DOWN** (a 10-Year-Rule land re-anchor reusing the a21 `_villa_value_floor`). It is **Gate-2 SIGNED**, with the build **PARKED** on the resume trigger **Confirmed-Sales GT-2 corpus n≥20**. Under the §0.4 principle it is **shippable-disclosed-as-indicative now** (the precedent is b4/b11 shipping on n=2) — the n≥20 bar gates the *precise coefficient*, not shipping.

**Evidence / detail (measured✓, §5-audited).**
- **Fork#1 = MODERATE** (Lever-2 re-anchor): floor +0–10%, with a luxury-finish exception → floor +~20%, wide MUC.
- **Fork#2 = WAIT-for-n≥20** (the coefficient precision).
- **DECISIVE §5 finding:** the local `luxury_new` **E4 stratum is n=0 in BOTH motivating areas** → **Lever 1 must be corpus-calibrated (cross-area GT-2), NOT a per-area MoJ lookup**. **Lever 2 is data-ready** (land floor n=20–33).
- Framing Rule-#54 web-checked: VPS 2 / VPGA 10 / IVS 102 ✓; the stated condition = an **assumption + MVU**, **not** a Special Assumption (+IVS 104). The B-1 disclose-only approach was preferred over a Special Assumption (deferred to B-2).

**Root cause / why parked.** The *durable* condition fix needs labelled condition GT to calibrate the premium; only **V001/V002/V003** exist so far (n=3). Historically this read as "blocked"; under §0.4 it reads as "ship Lever-2 disclosed-indicative now (data-ready), ship Lever-1 corpus-calibrated as GT grows."

**Impact.** This is the **durable no-rent gap-narrower** — the mechanism that shrinks the R7 dispersion at *source* for the (majority) no-rent villa traffic, complementing the cost slice (ISS-A04). The bidirectional R7 is **measured + confirmed** by V002/V003 (−37/−40% under-anchor) and V001 (over-anchor).

**Current mitigation / shipped state.** Signed brief + recon committed; B-1 disclose-only already shipped; the a17/a19 condition caveat is **validated** by V002/V003. The MULTI_AI batch decision-record is committed (locked outcomes; only the optional raw GPT-5/Gemini transcript is pending an Anas paste).

**Remediation / next action.** Re-frame the resume trigger per §0.4: **ship Lever-2 (data-ready) disclosed-indicative** in a near-term sprint; **ship Lever-1 corpus-calibrated** as GT crosses each threshold. Couple to the Stage-2 elicitation UX (ISS-U02). Discipline: n<20 → *motivates*, ship-disclosed; n≥20 → *calibrates* the precise coefficient.

**Dependencies / blockers.** Stage-2 elicitation UX (ISS-U02) to *capture* condition; GT corpus (ISS-D07) to *calibrate* Lever-1. The cost slice (ISS-A04) is complementary.

**«القرار المطلوب» (PO).** Whether to **lift B-2 from PARKED to ship-Lever-2-disclosed-now** under §0.4 (analyst lean: yes for Lever-2, which is data-ready; keep Lever-1 corpus-calibrated as GT grows).


## 3.D — Data issues

### ISS-D01 — MoJ transaction data frozen (160 days stale) — external dependency

> **Class** data · **Status** OPEN (external, monitored) · **Severity** 🟠 · **Lane** EXT · **Cross-refs** **R4**, MUC clause, Sprint 2.7 banner, ISS-D08 · **First logged** active since 2026-02-28 (MUC); freeze since 2025-12-31

**Summary.** `data.gov.qa` last published the weekly real-estate sales bulletin on **2025-12-31**. Measured live this session: **160 days stale**, 25,673 records, tier **stale**. This is the **sole valuation evidence source** (T1) — the entire market-comparison engine rests on it — and it is **not self-serving** (no API push; adoption of any new drop is gated on a multi-factor sanity gate before it can replace the snapshot).

**Evidence / detail (measured✓).** `/api/health` moj_freshness: latest_record 2025-12-31, days_old 160, record_count 25,673. (The figure drifts upward daily; historical doc figures of "139d/150d/152d/155d" are *stale snapshots* — Rule #58, do not cite them as current.)

**Impact.** Every villa/land headline is computed on a 5-month-old window. The Material Uncertainty Clause (MUC) is active because of it. As the freeze lengthens, the 24-month window's recency assumption degrades; the dispersion gate (a10/a14) and the prefer-36mo Phase-2 design (ISS-A02) partly absorb this. It is a **public-credibility and liability** risk if the product is *marketed* without the staleness disclosure.

**Current mitigation / shipped state.** Transparent staleness **banner** (Sprint 2.7) + the MUC clause + **self-healing**: when the government resumes publishing, `/api/health` recomputes freshness and the multi-factor gate (schema / NBSP / volume) governs adoption — **no silent adoption** of a new drop.

**Remediation / next action.** Monitor `/api/health`. Do not adopt a new drop without the multi-factor gate. The MME apartment integration (ISS-D05), *if* it comes online, would be a *partial* alternative T1 channel (apartments only). There is no action that closes this in-hand — it is genuinely external.

**Dependencies / blockers.** Government resuming publication, or a verified alternative geocoded T1 source.

**«القرار المطلوب».** None — accept-and-disclose (the banner + MUC are the policy). At PUBLIC tier this becomes a harder gate (LAUNCH_GATES gate 2).

---

### ISS-D02 — MoJ records carry no PIN / are de-identified (the Rule #45 gap)

> **Class** data · **Status** OPEN (structural) · **Severity** 🟠 · **Lane** EXT · **Cross-refs** **E12**, Rule #45, ISS-A08/D08/D07 · **First logged** 2026-05-20 (Sprint 2.20 audit)

**Summary.** MoJ sales **cannot be located to a parcel**: the dataset has plot area + price + a coarse built-type label + an opaque `PN…` hash, but **no PIN, no coordinates, no street**. This is distinct from the *freeze* (ISS-D01) — it is a permanent *structure* of the published data. (The hash analysis and the ethical closure are in ISS-A08.)

**Impact.** This single fact cascades into the project's three biggest "blocked" framings: (1) **no attribute self-calibration** (E12 — can't tag a sale's parcel attributes); (2) **no rigorous error distribution** (ISS-D08 — can't score a prediction against the actual sale of *that* parcel — Rule #45); (3) **no cost-model GT from MoJ** (ISS-A04 — calibration needs known BUA/age/finish per parcel). It is the deepest data constraint in the system.

**Current mitigation / shipped state.** The engine works at the **area × bracket** level (medians), which does not need parcel keying. The GT corpus (ISS-D07) supplies the *small* parcel-keyed set that the median path cannot.

**Remediation / next action.** Grow the **GT corpus** (manual confirmed sales / valuer reports + organic beta — ISS-D07). Treat parcel-keying as something the corpus provides incrementally, **not** something to extract from MoJ.

**Dependencies / blockers.** The GT corpus; or verified MME geocoding (apartments only, ISS-D05).

**«القرار المطلوب».** None — structural; the path forward is the corpus.

---

### ISS-D03 — MoJ NBSP duplication (recurring data-hygiene trap)

> **Class** data · **Status** MITIGATED (must stay applied) · **Severity** 🟡 · **Lane** CC · **Cross-refs** Empirical §3 (NBSP), ISS-A03/D04, CSV gotchas · **First logged** early (data hygiene)

**Summary.** The same MoJ value appears in **two byte-forms** — with a non-breaking space (`\xa0`) and with a regular space (`\x20`). Examples: "أرض فضاء" appears as **8,499 rows (NBSP) + 5,656 rows (space)**; the column header "تاريخ التثبيت" itself contains an NBSP. **Direct string comparison loses roughly half the data.**

**Impact.** Any matcher that does not normalise whitespace silently halves its pool — which is exactly the failure mode that produced the (now-closed) ISS-A03 bracket starve. It is a **silent** correctness leak.

**Current mitigation / shipped state.** Normalise with `re.sub(r'\s+', ' ', s).strip()` **before any string comparison**. Since a18 this is applied via `normalize_area_name` inside `area_match_key` on **both** the floor and bracket paths (`build_reference` + `compute_trend`).

**Remediation / next action.** Keep the normalisation at **every** MoJ string comparison (a18 generalised it on the area-name paths). Add a test that asserts the NBSP and space forms of a known area resolve identically.

**Dependencies / blockers.** None — shipped (a18).

**«القرار المطلوب».** None — keep the normalisation (shipped at a18).

---

### ISS-D04 — MoJ area-name article-drop + alias reconciliation

> **Class** data · **Status** MITIGATED (a18 — both paths) · **Severity** 🟠 · **Lane** CC · **Cross-refs** **R9 / A16**, ISS-A03/D03, `area_match_key`, `resolve_moj_area_name`, the strict-GIS area rule · **First logged** 2026-05 (R9)

**Summary.** MoJ area names frequently **drop the definite article "ال"** (الدحيل → "دحيل"; الغرافة → "غرافة") and use variants/aliases (مريخ vs امريخ الجنوبي). Since a18 **both** the floor and bracket paths use `area_match_key` (sibling-aggregation + hamza-fold) — the historical divergence that produced ISS-A03 is **closed** (errata).

**Evidence / detail.** Marikh: `مريخ` (populated, 23+13 bracket rows) vs `امريخ الجنوبي` (n=0). المعمورة strata vs floor land medians differed +7% pre-a23 because of an analogous match-key gap (now reconciled at a23/R15). The **strict-GIS area rule** stands: `Vector/Districts/MapServer/0` is the **sole authoritative source** for area names; **no market aliases**; **zone number ≠ administrative district** — so any alias handling must be a *normalization of MoJ strings to the GIS-authoritative name*, not an invented alias table.

**Impact (historical).** Pool starvation (ISS-A03, closed a18), and divergent land medians across surfaces (the kind of incoherence ISS-A07 guards against).

**Current mitigation / shipped state.** Floor path and strata land are reconciled (a18 / a23). Bracket matcher is **not**. The cap-rate lookup is also not fully override-aware (ISS-A05 Fork C).

**Remediation / next action.** Shipped (a18). Remaining: Fork C (ISS-A05) applies the same plumbing on the yield side; the unreachable-name class (فريج العسيري 26 / «المطار» 12, ~0.25%) stays honestly widened/refused. **Never** invent market aliases — normalise MoJ strings toward the GIS name.

**Dependencies / blockers.** None — shipped (a18).

**«القرار المطلوب».** None — handled at a18; Fork C pending in §6 v2.

---

### ISS-D05 — Apartment / MME data gap — *re-framed: out of v1 scope*

> **Class** data · **Status** OUT-OF-V1-SCOPE (re-framed 2026-06-09; was "BLOCKED auth") · **Severity** 🟡 (for v1) · **Lane** EXT / future · **Cross-refs** LAUNCH_GATES gate 1, 2.21.1 pre-MME smoke, anchor 52/903/90, ISS-D01 · **First logged** 2026-05 (deferred); re-framed 2026-06-09

**Summary.** Apartments (Pearl, Lusail towers) return "insufficient data" because the MME apartment source requires an **authenticated session** that has not been captured. The 2026-06-09 cleanup re-framed this from **"BLOCKED (auth)"** to **"out of v1 scope (Thammen v1 is a villas + land product); MME auth is a future-scope dependency, not a current blocker."**

**Evidence / detail (measured✓).** 2.21.1 pre-MME smoke: Heroku *reaches* MME (P1 TRUE), but the JWT is an **anonymous Directus token (role=null)** → kpi29 returns `count:0` for all queries; rent paths (kpi30/31/32) verified **DEAD**. Sprint 2.21.1 deferred pending a DevTools capture of an authenticated session. The 2.22.0 audit proved **H5 FALSE**: apartment failures are a **DATA** problem, not latency — a 3-stage architecture does not solve apartments. Anchor **52/903/90** (apartment_building / اللقطة / 467 m²) → asset_type=unknown → **refusal** (correct, by-design for v1).

**Impact.** A large market segment is uncovered — a **PUBLIC/B2B** gate, **not** a beta gate (villas+land is the accepted v1 scope). For v1 the apartment refusal is *correct behaviour*, not a defect.

**Current mitigation / shipped state.** The engine **refuses** apartments cleanly (no false number) — this is the right v1 behaviour. The hybrid path (T2 PF Lusail + T3 Aryan) exists for *Lusail* apartments behind a flag, but is not the v1 product.

**Remediation / next action.** Future scope: a DevTools capture of an authenticated MME session + verified geocoding → an apartment T1 channel. **Not** on the v1 / beta path. **Never** propose reviving it without the gating discipline (Heroku smoke first, etc.).

**Dependencies / blockers.** An authenticated MME session capture (future).

**«القرار المطلوب».** None for v1 — apartments are explicitly out of scope; the refusal is correct.

---

### ISS-D06 — D5/D6 discount calibration is provisional indefinitely — *re-framed*

> **Class** data · **Status** MITIGATED (ships with MUC) — *re-framed 2026-06-09* · **Severity** 🟡 · **Lane** CC/data · **Cross-refs** §0.4, Empirical §3, ISS-D07, T3 weights · **First logged** 2026-05-24 (feeds closed)

**Summary.** The D5/D6 discount factors (the broker-experience-grounded adjustment factors) are **provisional, broker-experience-grounded**, and were historically labelled "remain so **indefinitely** — NO viable recalibration source" because both the secretary feed (closed 2026-05-24) and the brokerage (Gardenia, closed) are gone. The 2026-06-09 cleanup re-frames the *conclusion*: they **ship with the MUC clause** (not a blocker) and recalibrate as the GT corpus grows — they are **not** waiting on a dead source.

**Evidence / detail.** Empirical basis (interim): the §3 asking-premium ranges + documented broker negotiation experience. The closed feeds are a *true* fact (they stay on the record); the *blocking* conclusion is what the re-frame removes.

**Impact.** Low — the discounts ship disclosed (MUC), and they are adjustment factors, not the headline driver.

**Current mitigation / shipped state.** Discounts ship with the MUC clause. T3 (Aryan developer data) survives as an independent channel with a hard cap (0.15 × min(n,5)/5).

**Remediation / next action.** Recalibrate from the GT corpus (ISS-D07) as it grows. Keep the MUC. **Delete** the "indefinitely / no source" framing per §0.4.

**Dependencies / blockers.** GT corpus growth.

**«القرار المطلوب».** None — ship-with-MUC, recalibrate-as-GT-grows.

---

### ISS-D07 — Ground-truth (GT) corpus — *the unblock for everything calibration*

> **Class** data · **Status** OPEN — *growing channel* (re-framed from "Confirmed-Sales DB DROPPED / no source") · **Severity** 🟠 · **Lane** PO + organic · **Cross-refs** §0.4, 2.16.16, V001/V002/V003, ISS-A04/A08/A10/D08, GT-1/GT-2 · **First logged** 2026-05 (Confirmed Sales deferred); re-framed 2026-06-09

**Summary.** The **single most leveraged data item** in the project. Historically the "Confirmed Sales DB" (Sprint 2.16.16) was filed **DEFERRED INDEFINITELY — no viable source** after the secretary and brokerage feeds closed. The 2026-06-09 cleanup re-frames it: the corpus **grows** via **(a) valuer reports / manual confirmed sales (GT-1 / GT-2)** and **(b) organic beta usage** — it is **not** "no source." This is the resume trigger for B-2 (ISS-A10), the calibration GT for the cost model (ISS-A04, open-decision-#4), the unblock for D5/D6 (ISS-D06), and the seed of the error distribution (ISS-D08).

**Evidence / detail (measured✓).** The corpus already has its **first GT-2 entries**: **V001** (Maamoura 56/647/6, old premium), **V002/V003** (Abu Hamour 56/565/10+12, new premium, **sold 4.0M**, engine 2.4–2.5M = −37/−40%). These three *motivate* (n<20) but already **confirmed the bidirectional R7** empirically and **validated** the a17/a19 condition caveat. Aryan developer data survives as **T3** (an independent channel). The MoJ `PN…` hash is permanently closed as a PIN source (ISS-A08) — the corpus is the *only* PIN-keyed sale path.

**Impact.** Every calibration-blocked item (ISS-A04, A08, A10, D06, D08) unblocks *incrementally* as this corpus grows. Discipline (Rule, restated): **n < 20 → motivates (ship-disclosed); n ≥ 20 → calibrates the precise coefficient.**

**Current mitigation / shipped state.** GT-2 logging exists (`docs/validation/VALIDATION_LOG.md`). The beta (ISS-G03) is the organic channel.

**Remediation / next action.** **Treat corpus-growth as a standing PO activity** (collect valuer reports + manual sales) **plus** the organic beta. Re-test each calibration item as the corpus crosses thresholds. **Delete** the "DROPPED / no source" framing per §0.4.

**Dependencies / blockers.** PO effort (GT-1/GT-2 collection) + the beta running (ISS-G03). Not blocked on any dead feed.

**«القرار المطلوب» (PO).** Confirm the GT-corpus-growth posture (manual + organic) as the standing unblock, replacing the "dead source" framing.

---

### ISS-D08 — No measured error distribution (the accuracy-measurement gate) — *re-framed*

> **Class** data/validation · **Status** OPEN — *re-framed 2026-06-09* · **Severity** 🔴 (the responsible-to-ship gate) · **Lane** PO + V · **Cross-refs** **LAUNCH_GATES gate 4**, Rule #45, ISS-D02/D07, the 4 anchors · **First logged** launch-gate register

**Summary.** The product publishes a **number** but has **no measured error distribution** — accuracy is currently underwritten by **four value-invariant anchors + broker judgment**, not a statistical study. A rigorous study is itself constrained by the PIN-keyed-sale gap (Rule #45 / ISS-D02). The 2026-06-09 cleanup re-frames the gate: **"spot-check on the manual GT *now*; the statistical error distribution is a *public-tier* requirement"** — i.e. it does **not** block the invited beta, and the beta itself *generates* the data that closes it.

**Evidence / detail.** The four anchors are *stability guards* (byte-identical regression), **not** an accuracy distribution: 56/565/21 = 2.4M, 54/541/6 = 5.4M (over-anchor, tracked-for-drift), 55/296/13 = 2.6M (comparison_thin n=8, land-anchored), 52/903/90 = refusal. The only *accuracy* evidence is the three GT-2 confirmed sales (V001/V002/V003), which **disconfirm** point-accuracy on premium villas (−37/−40%) — itself a finding, not a distribution.

**Impact.** This is the **"responsible-to-ship" gate** for PUBLIC marketing. At BETA, expert spot-check + honest framing + the MUC may suffice, *and* the beta is the only realistic way to start closing it. At PUBLIC it is a hard requirement (an honestly published error band).

**Current mitigation / shipped state.** Honest framing throughout (range-as-lead, evidence-quality panel, "not a certified valuation"), the MUC clause, and the four stability anchors. No distribution yet.

**Remediation / next action.** (1) **Now:** spot-check predictions against the manual GT (V001/V002/V003 + each new GT-2). (2) **As the corpus grows:** compute and **publish an honest error band** before any PUBLIC marketing. (3) Couple to ISS-D07 (corpus growth) and the beta (ISS-G03).

**Dependencies / blockers.** The GT corpus (ISS-D07); the PIN-keyed-sale gap (ISS-D02) limits how fast a *MoJ-based* study could run — the corpus is the route.

**«القرار المطلوب» (PO).** Endorse the re-frame: spot-check-now (not a beta blocker); commit to publishing an error band before PUBLIC marketing.


## 3.B — Bugs (the A-series catalogue)

> Live bug counts (corrected by the errata pass §0.2b): **Critical 0 · High 0 · Medium 2** (A5, A15). A6 (latency), A7 (`rics_compliant` label), A8 (closed by 2.20), and A11 (Zoning/Subtype contradiction) are CLOSED — see Part 6. **A16 → resolved-as-pool-fix at a18** (§20.18); its corrected record is ISS-A03 (CLOSED).

### ISS-B01 — A5: `asset_type=unknown` residual (some addresses fail classification)

> **Class** bug · **Status** OPEN (medium) · **Severity** 🟠 · **Lane** CC · **Cross-refs** **A5**, R5, E7, Rule #11, anchor 52/903/90 · **First logged** Sprint 2.22.0a.1 era (§17)

**Summary.** Some address-tab evaluations resolve to **`asset_type=unknown`** (with `pin=None, qars=None`), which the engine surfaces as a scope badge / refusal rather than a valued result. This is the *residual* of the larger 2.22.0a.1 QARS-envelope outage (which was closed by the v132 hotfix); A5 tracks the remaining cases where classification legitimately fails or the GIS round-trip returns nothing usable.

**Evidence / detail (measured✓).** During the 2.22.0a.1 outage, **every** address `/api/evaluate` returned `asset_type=unknown, pin=None, qars=None` *silently* because khazna's `QARS_Point` returned an ArcGIS auth-error **envelope** (HTTP 200 carrying `{"error":{"code":503,…}}`) that callers read as an empty feature list — indistinguishable from a legitimate address-not-found. The v132 fix (the `_qars_query` primary→legacy fallback on both exceptions **and** envelopes) closed the *outage*; A5 is the remaining "genuinely unknown / unclassifiable" tail (e.g. 52/903/90 apartment → unknown is *correct* for v1; but A5 also covers cases that *should* classify but don't).

**Root cause.** A mix of: (a) addresses that QARS cannot resolve (sparse/edge parcels), and (b) the by-design refusal for out-of-scope types (apartments). The bug is the *conflation* — a user can't always tell "we don't cover this" from "we couldn't find it." (Cross-ref E7: QARS subtype can also be stale, requiring the Zoning cross-check — that path is A11-closed, but reinforces that classification is not single-source.)

**Impact.** Medium — affects coverage and the clarity of the "no result" message. Not a wrong *number* (it refuses rather than guesses), so it is a credibility/UX issue, not an accuracy one.

**Reproduction.** Submit an address whose parcel QARS cannot resolve → `asset_type=unknown`. (Use a known sparse-parcel address; do **not** use 52/903/90 for the "should-classify" case — that one is a correct apartment refusal.)

**Current mitigation / shipped state.** The v132 envelope-fallback (so an outage no longer *silently* unknown-s everything); the clean apartment refusal. The remaining tail is unhandled.

**Remediation / next action.** Small sprint: distinguish **"out of scope"** from **"could not resolve"** in the response/UI, and audit the residual unknown rate against a sample of real addresses (E14 — exercise the default flow). Low priority vs ISS-A*/ISS-R*. **Forward item #5 (parallel).**

**Dependencies / blockers.** None — self-contained.

**«القرار المطلوب».** None — schedule when convenient (parallel track).

---

### ISS-B02 — A15: HBU is silently dropped whenever the zoning hint is absent

> **Class** bug · **Status** OPEN (medium) · **Severity** 🟠 · **Lane** CC · **Cross-refs** **A15**, §20.5, ISS-A01 (HBU feeds decomposition) · **First logged** §20.5 (Sprint a-series)

**Summary.** The **Highest-and-Best-Use (HBU)** computation is **silently dropped whenever the zoning hint is absent** — i.e. when the engine cannot fetch/derive a zoning code for the parcel, the HBU step no-ops without a disclosure, so the result quietly lacks the HBU-premise component it would otherwise carry.

**Evidence / detail.** Logged at §20.5 as a Medium open bug + a determinism-test finding: "HBU is **silently dropped** whenever the zoning hint is absent — reachable" on the default flow. Because HBU underpins the B-1 land-floor premise («indicative land component on an HBU premise»), a silent drop means the decomposition (ISS-A07) can present a land floor whose HBU basis is missing — a coherence risk.

**Root cause.** The HBU branch is gated on a zoning hint that is not always populated; when absent, the code skips HBU rather than disclosing "HBU not determined for this parcel" (the same *inert-on-default* family as E22 — an output gated on a non-always-present input).

**Impact.** Medium — affects the HBU/decomposition surface (ISS-A07) and the honesty of the land-premise framing. Not a wrong headline (the comparison median is unaffected), but a **silent** omission, which is the part that matters for an audit trail.

**Reproduction.** Evaluate a villa/land parcel where the zoning hint is unavailable → observe the HBU component absent with no disclosure.

**Current mitigation / shipped state.** None direct. The B-1 framing (a21/a22) is careful elsewhere, but does not disclose the *silent HBU drop* specifically.

**Remediation / next action.** Make the drop **explicit**: when the zoning hint is absent, disclose "HBU premise not determined for this parcel" rather than silently omitting it. Naturally **folds into the decomposition-coherence fix (ISS-A07)** — both touch the land-premise surface. **Forward item #5 (parallel), or fold into #1.**

**Dependencies / blockers.** Best done with ISS-A07 (same surface).

**«القرار المطلوب».** Whether to fold A15 into the decomposition-coherence brief (analyst lean: yes — same surface, same audit-trail concern).

---

### ISS-B03 — A16: bracket-path area-name under-match (pointer) — **CLOSED at a18 (errata)**

> **Class** bug + accuracy · **Status** **CLOSED 2026-06-03 (a18, v157)** — corrected from "OPEN/promoted" by the errata pass (§0.2b) · **Severity** was 🟠 · **Lane** CC (shipped) · **Cross-refs** **A16 / R9 → full corrected record in ISS-A03**

**Summary.** A16 was the bracket-path area-name starve. It was **resolved-as-pool-fix at a18** (`area_match_key` wired into `build_reference` + the امريخ الجنوبي→مريخ override; §20.18). The open A-series mediums are therefore **A5 / A15** (two, not three). Residual: the unreachable-name class (~0.25%) + the optional a18 fast-follow live sub-zone demo — see ISS-A03.


## 3.T — Infrastructure & technical-debt issues

> Most of these are **MITIGATED** with documented scar tissue (an Operational rule was minted from each). They are kept open-in-spirit because the failure mode can recur, and a future session must know the guard exists.

### ISS-T01 — QARS / GIS Heroku reachability fragility (R5)

> **Class** infra · **Status** MITIGATED (monitor) · **Severity** 🟠 · **Lane** CC · **Cross-refs** **R5**, Rule #11, ISS-B01, §17 (2.22.0a.1) · **First logged** 2026-05-27

**Summary.** The primary QARS endpoint (khazna `QARS_Point`) has, from the Heroku AWS us-east-1 IP, returned an **ArcGIS auth-error envelope** (HTTP 200 carrying an error object) that a naive caller reads as an empty result — a *silent* envelope-as-empty failure that degraded address classification platform-wide until hot-fixed.

**Evidence / detail (measured✓).** 2026-05-27: `/api/health` qars_endpoint = degraded; every address `/api/evaluate` returned `asset_type=unknown` until the v132 envelope-fallback hotfix. Live now: qars **healthy** (primary 162,496 / legacy 162,497).

**Impact.** When it bites, it takes out the entire address tab (the villa/land path). High blast radius, low frequency.

**Current mitigation / shipped state.** `_qars_query()` does primary→legacy fallback on **both** Python exceptions **and** ArcGIS envelopes (Rule #11 defensive design); a new `_GISServerError` + `_arcgis_envelope_to_exception()`; three callsites refactored (`find_property`, `_qars_count_in_polygon`, `count_qars_within_polygon` — the last two previously had **no** fallback). `/api/health` exposes `qars_endpoint.status` for monitoring.

**Remediation / next action.** Monitor `/api/health`. If khazna tightens further, the legacy endpoint is the live fallback. **Never** treat a 200-with-envelope as success (the guard exists; keep it).

**Dependencies / blockers.** External (khazna ACLs on the AWS IP range).

**«القرار المطلوب».** None — monitor; the fallback is the policy.

---

### ISS-T02 — Heroku 30-second router timeout coupled to the serial GIS chain (E21)

> **Class** infra · **Status** MITIGATED (A14 closed the cold-503) · **Severity** 🟡 · **Lane** CC · **Cross-refs** **R2 (closed)**, **E21**, **E19**, Rule #51 · **First logged** A6 latency arc; E21 2026-05

**Summary.** The cold-latency penalty is coupled to the **serial GIS chain**, **not** dyno spin-up (E21). The heavy multi-QARS villa path once ran warm ≈21 s against the 30 s router wall → a cold first-try **503**. The fix was parallelisation, not bigger dynos.

**Evidence / detail (measured✓).** Was 503@31s cold (ref 56/565/21). Post-A14: 56/565/21 cold first-try **200@14.4s** (+200@15.0s ×2); 56/647/6 cold **200@15.9s** — all < 30 s, margin ~15 s, **zero 503**. The fix parallelised `geometric_factors` internals (Round0 polygon → Round1 ∥{corner road-probes, hbu, landmarks}), byte-identical output (H_det). E19: `max_workers = task count` for I/O-bound fan-out.

**Impact.** Low now (margin ~15 s). The constraint persists structurally: **all fetch operations must stay ≤10s** and any new serial GIS hop re-risks the wall.

**Current mitigation / shipped state.** A14 lever 2 (parallelised); lever 1 (overlap) deferred + H_A-cleared/ready if the margin ever regresses. Rule #52: latency sprints unmask methodology bugs (a recurring pattern — keep the content check post-deploy).

**Remediation / next action.** Keep new GIS work parallel (reuse already-fetched polygons — as b1/b10 did, "zero new GIS"). Watch the cold-latency margin on `/api/health` smoke.

**Dependencies / blockers.** None.

**«القرار المطلوب».** None — keep the parallel-I/O discipline.

---

### ISS-T03 — Cloudflare 1010 blocks urllib POST (R12)

> **Class** infra/tooling · **Status** MITIGATED · **Severity** 🟡 · **Lane** CC · **Cross-refs** **R12**, Rule **#61**, ISS-R06 · **First logged** 2026-06-01 (a15)

**Summary.** A bare `python-urllib` POST to `thammen.qa` is rejected at the Cloudflare edge with **error 1010** (bot signature), so a CC-side post-deploy POST smoke can be skipped or mis-read as a deploy failure.

**Evidence / detail (measured✓).** a15 post-deploy: urllib POST `/api/evaluate` + `/api/feedback` → **HTTP 403 "error code: 1010"** ×5; the *same* requests via **curl with a browser User-Agent passed**; GET `/api/health` was never blocked. (Cross-ref the same family: a browser User-Agent is required for `/api/evaluate` generally — Rule #61.)

**Impact.** Tooling only — could cause a false "deploy failed" read if a future script uses urllib for the POST smoke.

**Current mitigation / shipped state.** Rule **#61**: CC post-deploy POST smoke = **browser-UA curl, not urllib** + two-lane confirmation (CC + Anas). Fall back to the Anas/Claude.ai side if Cloudflare tightens to a JS challenge.

**Remediation / next action.** Keep using browser-UA curl for POST smokes. (Note: `curl` can *hang* on `data.gov.qa` — use `urllib` there; the two tools have opposite quirks on the two hosts — ISS-T08.)

**Dependencies / blockers.** External (Cloudflare WAF posture).

**«القرار المطلوب».** None.

---

### ISS-T04 — Cross-surface state divergence / memory-vs-disk drift (R1 + R3) — the operating-model risk

> **Class** governance/infra · **Status** MITIGATED (Rule #57/#58) — *structural, recurring* · **Severity** 🟠 · **Lane** all lanes · **Cross-refs** **R1**, **R3**, Rule **#57**, **#58**, **#43**, ISS-G06 · **First logged** 2026-05-30

**Summary.** Two coupled risks: **R1** — work done in one Claude surface (commits, deploys, decisions) is **invisible** to another that trusts a stale brief/memory → risk of re-doing, overwriting, or "losing" committed work; **R3** — CLAUDE.md / briefs / chat memory **drift** from the live code, git, and `/api/health` → numbers get *trusted* instead of *measured*.

**Evidence / detail (measured✓).** 2026-05-30: a forensic read-only pass was needed to confirm `0c81363`/`1711035` were real and that **origin was 98 commits behind production**. The same governance pass found MoJ "139d (doc) vs 150d (live)", "VPS 4 (docs) vs VPGA 10 + VPS 6 + IVS 106 (code)", "latest = 2.16.12 (4 sprints stale)", and a 49/49-vs-48/49 test delta. *This very issues-log compilation is an instance of the mitigation working* — every live number here was re-measured.

**Impact.** The single most dangerous *process* risk: it threatens work-loss and decisions made on stale numbers. It is **inherent** to the two-lane model (the lanes share no live context; Anas is the only router — ISS-G06).

**Current mitigation / shipped state.** Rule **#57** (session-start ground-truth handshake: `curl /api/health` + `git HEAD/reflog/origin-diff` before routing work — **live state outranks memory**); Rule **#58** (assumed-vs-actual gap: measured wins, the gap is logged in the RISK_REGISTER); backup-push part of the deploy ritual (Rule **#43** — `git push origin master` alongside the subtree push). Single-source critical numbers (the DoD count; `/api/health` version).

**Remediation / next action.** Keep the #57 handshake mandatory at every session start. Keep `/api/health` as the single source for version/freshness. Refresh the Claude.ai project-knowledge snapshot by re-uploading current `C:\Thammen` docs (only Anas can — ISS-G06).

**Dependencies / blockers.** None — discipline.

**«القرار المطلوب».** None — keep the handshake.

---

### ISS-T05 — Gate integrity: "verified" must mean EXECUTED, not reasoned (R14)

> **Class** process · **Status** MITIGATED (control adopted) · **Severity** 🟠 · **Lane** CC/Claude.ai · **Cross-refs** **R14**, **R14-the-rule** (real-Chromium), Rule #52 · **First logged** 2026-06-02 (a17)

**Summary.** A push-gate report once conflated **REASONED / WORKED-AROUND** with **EXECUTED**: a brief-mandatory pre-deploy check (mobile 390×844) was silently downgraded to post-deploy and *assumed* items were tagged as measured, and a DoD "59/59" was reported when the broad suite was 58/59 — so **the gate did not actually gate**.

**Evidence / detail (measured✓).** 2026-06-02 (a17): the report marked the mobile check "verified" via `.rn`-reuse *reasoning* + deferred the pixel-confirm to post-deploy ("a16 precedent"); reported "59/59" when broad was 58/59 (never a clean pass) + 1/1 isolated. Push to v156 proceeded on that report. **Outcome benign** — post-hoc real verification (headless render at 390×844: right-edge 374<390, no overflow; real JS parse: functions defined, 0 console errors) — but the gate didn't gate.

**Impact.** Audit integrity. A gate that can be satisfied by *reasoning* is not a gate. This is why "R14" became shorthand for **real-Chromium execution** of the mobile/JS checks in every subsequent sprint.

**Current mitigation / shipped state.** Control adopted: (a) "verified" in any push-gate report = **EXECUTED**, tag each item **done / worked-around / not-done**; (b) a brief-mandatory check that cannot run at gate-time **BLOCKS** the push (downgrading it = Anas's explicit waiver, never a Fast-lane substitution); (c) briefs authored without the codebase mark code-level claims "CC verify in recon." Every b-series sprint since reports a real-Chromium R14 line.

**Remediation / next action.** Keep the EXECUTED-not-reasoned discipline in every push-gate report. Keep the DoD count single-sourced (so "59/59 vs 58/59" can't recur).

**Dependencies / blockers.** None — discipline.

**«القرار المطلوب».** None.

---

### ISS-T06 — Brittle exact-version-pin tests (R6) — recurring anti-pattern

> **Class** tech-debt · **Status** MITIGATED (recurs) · **Severity** 🟡 · **Lane** CC · **Cross-refs** **R6**, Rule #58 · **First logged** 2026-05-30 (A14)

**Summary.** Test files that assert `ENGINE_VERSION == '<frozen tag>'` fail on **every** later sprint, producing a red regression unrelated to function. The pattern keeps **recurring** in new test files.

**Evidence / detail (measured✓).** `test_sprint_2p22p0a5_request_budget.py` (2 assertions) failed post-2.22.0a.6 bump → broad regression went 48/49; fixed by loosening to version-agnostic FORMAT checks against the live `ENGINE_VERSION`/`SPRINT_TAG` source → 50/50. **Recurred + fixed again** in a8 (`test_sprint_2p22p0a8_rics_citation.py`) during the a9 deploy-prep, and a b5 "Soft-Gate-3" repaired a stale 2.19.1 mock (R7 interface drift, latent red the skipped broad-walk never caught).

**Impact.** Low (cosmetic red), but it erodes trust in the regression signal and has masked at least one real interface drift (the b5 case).

**Current mitigation / shipped state.** New tests assert version **format**, not a frozen literal. The DoD broad-walk catches the latent reds (and at b11 the broad walk *caught and fixed* a real a2.p9 precision regression — «الصفقات المشابهة» → «القريبة في النوع والمساحة»).

**Remediation / next action.** **Never** assert a frozen `ENGINE_VERSION` literal in a new test. Keep running the **broad** DoD walk (not just the changed-sprint test) so latent reds + interface drift surface.

**Dependencies / blockers.** None — discipline.

**«القرار المطلوب».** None.

---

### ISS-T07 — Ephemeral filesystem: commit-before-deploy discipline

> **Class** infra/process · **Status** MITIGATED · **Severity** 🟡 · **Lane** CC · **Cross-refs** Rule #43, developer_inventory.sqlite note, ISS-G05 · **First logged** 2.21.4 (ephemeral-FS workflow)

**Summary.** Heroku's filesystem is **ephemeral** — anything written at runtime (e.g. a seeded SQLite) is lost on dyno cycle. Data artifacts (e.g. `developer_inventory.sqlite`, `cap_rates.sqlite`) must be **committed pre-deploy**, not generated on the dyno.

**Evidence / detail.** The 2.21.4 T3 inventory (17 cols, idempotent migration) was **committed pre-deploy per the ephemeral-FS workflow**; the b5 per-area `cap_rates.sqlite` was likewise a committed DB swap. Deploy is `git subtree push --prefix "deploy v2" heroku master` (Rule #43 — the app lives in the `deploy v2/` subdir; a plain `git push heroku master` is rejected by the buildpack).

**Impact.** Low if the discipline holds; a forgotten commit means a feature that works locally vanishes on the next dyno cycle.

**Current mitigation / shipped state.** Commit DB artifacts pre-deploy; idempotent migrations; the subtree-push deploy ritual + origin backup (Rule #43).

**Remediation / next action.** Keep committing data artifacts; never rely on runtime-written files persisting.

**Dependencies / blockers.** None.

**«القرار المطلوب».** None.

---

### ISS-T08 — MoJ CSV fetch quirks (curl hangs; urllib + utf-8-sig + NBSP)

> **Class** infra/tooling · **Status** MITIGATED · **Severity** 🟡 · **Lane** CC · **Cross-refs** ISS-D03, CSV gotchas, Rule #34 (file-based probes) · **First logged** early

**Summary.** Fetching the MoJ CSV from `data.gov.qa` has two traps: **`curl` hangs** on that host (use Python `urllib`); and the CSV is **`utf-8-sig`** encoded with **NBSP** contamination in values and headers (ISS-D03). This is the *opposite* tooling quirk from `thammen.qa`, where **urllib is Cloudflare-blocked** and curl works (ISS-T03).

**Evidence / detail.** `www.data.gov.qa` requires the `www.` prefix; CSV export via `urllib` (not curl); `utf-8-sig` encoding; NBSP normalisation mandatory (`re.sub(r'\s+',' ',v).strip()`). The two-host quirk pair: **data.gov.qa → urllib (curl hangs)**; **thammen.qa → curl browser-UA (urllib 1010-blocked)**.

**Impact.** Low — a known pair of gotchas; only bites a script that uses the wrong tool for the host.

**Current mitigation / shipped state.** Documented in the CSV-gotchas section + Operational rules; probes are file-based per Rule #34 (no inline `heroku run "python -c …"` — Windows cmd breaks on `&` in URLs); `smoke_<endpoint>.py` written as a standalone file.

**Remediation / next action.** Keep the host→tool mapping in mind. Keep probes file-based.

**Dependencies / blockers.** None.

**«القرار المطلوب».** None.


---

## 3.U — UX / Product issues

> These issues track the gap between the **shipped** owner journey and the **signed design** (`DESIGN_2p2x_v4_owner_journey.md`). The v4 design is a lean five-screen flow: **identify → confirm fetched data → improve → polished result → full report**. Three decisions are locked by Anas and frame everything below:
> 1. **Lean flow** — five screens, no detours; each screen earns its place.
> 2. **Number early, as a range that refines** — the figure appears as a band, not a hidden reveal at the end; it *narrows* as the owner adds detail. (This was the resolution of the §2b "range-as-lead" question. The rejected alternative — a *land-to-median* asymmetric band — is logged as a failed path in Part 6.)
> 3. **Condition = sensitivity only** — owner-supplied condition moves a *sensitivity readout*, never the headline confidence. This is the UI expression of the §2c structural rule "explanation does not raise confidence" and the B-1 "disclose-don't-assume" stance.
>
> Shipped coverage at the time of writing: screen 1 (identify) and screen 2 (confirm) are substantially shipped across b.2.1 (separate input screens), b.2.2 (four-component evidence-quality panel), b.2.3 (confirmation gate «تابِع بهذه البيانات»), and the b.3 polish. Screen 3 (improve) is **partial**. Screens 4 (polished result) and 5 (full report) are **pending** the decomposition-coherence fix (forward-sequence #1) landing first.

### ISS-U01 — Thinnest-flow remainder: screens 3–4–5 not yet built to v4 spec

> **Class** UX/product · **Status** OPEN · **Severity** 🟠 · **Lane** PO (vision) → CC (build) · **Gates** **Gate-2** (each screen's methodology/UX surface) · **Cross-refs** DESIGN_2p2x_v4, ISS-U02, ISS-U03, ISS-A07 · **First logged** DESIGN_2p2x v4 adoption

**Summary.** The five-screen owner journey is the agreed product spine, but only the first two screens are built out. **Screen 3 (improve)** exists in partial form (the inputs are separated and the confirmation gate is in place, but the "improve" interactions — condition sensitivity, rent surfacing — are not fully wired to their engine signals). **Screen 4 (polished result)** and **Screen 5 (full report)** are not yet built to spec, and are intentionally **blocked behind the decomposition-coherence fix** (ISS-A07 / forward-#1): a polished result that renders an *incoherent* land/building/total decomposition would harden a bug into the most prominent surface of the product.

**Evidence / detail (measured✓ / assumed~).**
- ✓ Screen 1–2 shipped: separate input screens (b.2.1); four-component evidence-quality panel — data completeness, comparables quality, market recency, building characterization, each rated strong/moderate/limited and **derived from engine fields (§2c), never hand-authored** (b.2.2); neutral confirmation gate «تابِع بهذه البيانات» — *proceed*, not *assert-correctness* (b.2.3).
- ✓ The number-as-range decision is locked (locked-decision #2) but the **range-as-lead headline** is itself a separate pending brief (see ISS-A07 note and Part 5 forward sequence), requiring Gate-2 + an R14 "verified=executed" UI audit. It is UI-only on fixed values.
- ~ Screens 4–5 content is specified at the design level (polished result = headline range + evidence panel + condition sensitivity + decomposition; full report = the methodology-grade document) but not yet implemented.

**Root cause.** Correct sequencing, not neglect: the polished result and report are *downstream* of (a) the decomposition being coherent and (b) the range-as-lead headline being signed. Building them first would mean rebuilding them after the upstream fixes.

**Impact.** The owner journey currently "tops out" at a confirmed-data screen plus a result that predates the v4 polish. For a free invite accuracy-beta this is acceptable (the beta measures the *engine*, not the chrome), but it is the main UX debt blocking a presentable v1.

**Current mitigation / shipped state.** Screens 1–2 + confirmation gate shipped; the result screen renders the existing (pre-v4-polish) output. Beta can run on this surface because beta is an **engine-accuracy** exercise, not a UX validation (see ISS-G03).

**Remediation / next action.** Sequence per Part 5: land **ISS-A07 (decomposition coherence)** → then the **range-as-lead headline brief** → then build **screen 4 (polished result)** carrying the coherent decomposition + condition sensitivity + range → then **screen 5 (full report)**. Each screen is its own Gate-2 + R14 UI audit (§5 UI-First: real props, GIS ground truth, live `/api/evaluate`, grep `index.html` to confirm the field renders, 390×844 mobile).

**Dependencies / blockers.** ISS-A07 (decomposition coherence) must land first. Range-as-lead headline brief must be signed (Gate-2).

**«القرار المطلوب».** يُمضى بتسلسل الشاشات بعد إصلاح التفكيك؟ (لا قرار جديد مطلوب الآن — الشاشات 4–5 محجوزة خلف forward-#1 بحكم التصميم.)

---

### ISS-U02 — Condition-sensitivity readout (screen 3) — present as a band, not a confidence lever

> **Class** UX/product · **Status** OPEN (design locked, build partial) · **Severity** 🟠 · **Lane** PO (vision) → CC (build) · **Gates** **Gate-2** · **Cross-refs** §2c, R7/ISS-A01, B-1, ISS-A10, locked-decision #3 · **First logged** DESIGN_2p2x v4

**Summary.** On the "improve" screen the owner can describe the property's **condition**. The locked decision is that condition moves a **sensitivity readout only** — it widens or shifts a *what-if band*, and it **does not raise the headline confidence/authority**. This is the UI face of the §2c rule (explanation does not raise confidence) and of B-1's bidirectional **disclose-don't-assume** stance: we *show* that condition could move value up or down, we do not silently *bake* a condition adjustment into a more confident-looking number.

**Evidence / detail (measured✓ / assumed~).**
- ✓ §2c structural rule: engineering moves value and raises evidence; **condition/explanation enrich understanding without raising confidence**; authority starts low and rises only with accountability at the final stage.
- ✓ B-1 shipped *bidirectional condition disclosure* as **disclose-only, not fix** (the engine discloses that condition is a live axis but does not assume a direction). The durable *fix* (an actual condition→value adjustment) is **B-2**, gated and disclosed-as-indicative (ISS-A10).
- ✓ R7 is **bidirectional**: under-anchors new/premium villas (~−37/−40% on the V002/V003 Abu Hamour sold-4.0M pair) and over-anchors older stock. A naïve "better condition → higher, more confident number" would deepen exactly the wrong half of R7.
- ~ The readout's exact visual (a ± band that breathes vs. a discrete better/worse toggle) is a design-surface decision still open.

**Root cause.** Condition is genuinely informative but **not yet calibrated to a value delta** (that is B-2, pending n≥20 — and even then it ships disclosed-as-indicative per §0.4). Until calibrated, the only honest UI is a *sensitivity* one.

**Impact.** Done right, this lets owners feel heard (their condition input *does* something visible) without manufacturing false precision. Done wrong (condition as a confidence lever) it would both violate §2c and amplify R7.

**Current mitigation / shipped state.** Inputs separated (b.2.1); the bidirectional **disclosure** exists (B-1). The sensitivity *readout* on screen 3 is the partial/pending piece.

**Remediation / next action.** Build screen 3's condition input to drive a **sensitivity band** (what-if), explicitly labelled as not changing confidence; keep the B-1 bidirectional disclosure copy. When **B-2** lands (disclosed-indicative), the band can be *anchored* by the calibrated delta but still presented as a range with a "calibrated on limited n" caveat (§0.4).

**Dependencies / blockers.** B-2 (ISS-A10) for an *anchored* band; until then, an *uncalibrated* sensitivity band. Gate-2 on the visual.

**«القرار المطلوب».** شكل القراءة في الشاشة 3: شريط ±-حسّاسيّة يتنفّس، أم مفتاح أفضل/أسوأ تقديريّ؟ (قرار سطح-تصميم محجوز لك.)

---

### ISS-U03 — Decomposition + report refinement (screens 4–5) — coherence is a precondition

> **Class** UX/product · **Status** OPEN · **Severity** 🟠 · **Lane** PO → CC · **Gates** **Gate-2** · **Cross-refs** ISS-A07 (decomposition coherence), ISS-A01 (R7), B-1 land-floor/HBU, RICS/IVS map (Appendix G) · **First logged** DESIGN_2p2x v4

**Summary.** The **polished result (screen 4)** is meant to carry the land/building/total **decomposition** and a condition sensitivity readout; the **full report (screen 5)** is the methodology-grade document an owner can keep. Both depend on the decomposition being **internally coherent** (ISS-A07): the land floor, the building contribution, the HBU logic, and the headline must not contradict each other. Refining these screens *before* the coherence fix would mean presenting a contradiction in the product's most authoritative surface.

**Evidence / detail (measured✓ / assumed~).**
- ✓ B-1 shipped land-floor / HBU decomposition + bidirectional condition disclosure. The §20.9 cost-triangulation **down-half shipped at b11** (re-anchors an over-anchored old villa toward a cost-informed floor — Marikh 1.9M→2.4M `cost_reanchor_down`, precedence `income_led > cost_reanchor > widen_down`). The **convergence + UP-lift** half is still pending and is part of the §20.9 gated slice (ISS-A04).
- ✓ The report is where RICS/IVS framing lives (Appendix G citation map). Authority **rises only at the final, accountable stage** — the report is that stage, so its claims must be exactly scoped (ISS-R03).
- ~ The decomposition-coherence defect (ISS-A07) is described as "live, credible, ready at b11" for a fix brief but the brief itself **awaits Gate-2** (the standing reminder from the 2026-06-09 cleanup).

**Root cause.** The polished result is the visual *summation* of the engine's structural story; it can only be as coherent as that story. The story is not yet coherent (A07), and one half of the cost-triangulation (UP-lift/convergence) is unshipped.

**Impact.** This is the screen that turns "a number" into "a defensible valuation." Its quality is the difference between a credible product and a calculator. But shipping it on top of an incoherent decomposition would be actively harmful.

**Current mitigation / shipped state.** The pre-v4 result screen renders today; B-1 decomposition + b11 down-half are live underneath.

**Remediation / next action.** Per Part 5: **A07 decomposition coherence** → §20.9 **convergence + UP-lift** gated slice (ISS-A04) → build **screen 4** carrying the coherent decomposition + sensitivity + range → build **screen 5** report with exactly-scoped RICS/IVS framing (ISS-R03). Each is Gate-2 + R14 UI audit.

**Dependencies / blockers.** ISS-A07; ISS-A04 (§20.9 UP-lift). Gate-2 per screen.

**«القرار المطلوب».** لا قرار جديد — الشاشتان محجوزتان خلف تماسُك التفكيك بحكم التصميم.

---

### ISS-U04 — Feedback / capture UI (Sprint-2) — not required for beta launch

> **Class** UX/product · **Status** DEFERRED (not a beta blocker) · **Severity** 🟡 · **Lane** PO → CC · **Gates** **gate #11** (capture security + data-residency + free-text handling), §8.1 PDPPL, §8.2 cross-border · **Cross-refs** ISS-R05, ISS-R06, R11, capture=DORMANT · **First logged** a15 instrumentation design

**Summary.** A feedback/capture surface (let owners flag "this is off," submit a known sale, etc.) is the mechanism that converts the beta from *opinion-gathering* into *error-measurement*. It is intentionally **not** a launch blocker: the beta can run with capture **dormant** and grow the ground-truth corpus via **manual** valuer-reports/sales (GT-1/GT-2) plus organic use. Turning capture *on* is gated by two PO decisions (data residency + free-text handling) and a security pass.

**Evidence / detail (measured✓ / assumed~).**
- ✓ Capture is **DORMANT** in the live `/api/health` (confirmed this session).
- ✓ a15 framing: two decisions owned by Anas before activation — **database residency** and **free-text field handling** (Gate #11) — plus a security pass. "Launching without = opinion-gathering; launching with = error measurement."
- ✓ The 2026-06-09 cleanup reframed the corpus-growth story: GT grows via **(a) manual valuer-reports/sales and (b) organic beta use** — *not* "no source." So capture being dormant does **not** block the beta; it only changes *how fast* GT accrues.
- ~ The exact feedback UI (inline "flag" vs. a post-result form vs. a submit-a-sale flow) is unspecified.

**Root cause.** Capture touches personal data and free text → it cannot be switched on until residency + free-text handling + at-rest security are decided (ISS-R05, ISS-R06). That is correctly upstream of building the UI.

**Impact.** Without capture, GT grows manually (slower but real). With capture (post-gate), the beta becomes a measurement instrument. Neither blocks launch.

**Current mitigation / shipped state.** Dormant. Manual GT path (valuer reports + curated sales) is the interim corpus engine.

**Remediation / next action.** Keep capture dormant through beta-start; in parallel, resolve **gate #11** (residency + free-text) + the **capture-surface security** items (ISS-R06) → then build the feedback UI as a Sprint-2 item.

**Dependencies / blockers.** gate #11 decisions (PO); ISS-R06 security; §8.1/§8.2.

**«القرار المطلوب».** قراران محجوزان لك قبل التفعيل: **مقرّ قاعدة البيانات (residency)** + **معالجة الحقل الحرّ** — ثمّ تمريرة أمن. (ليست حاجزاً للبيتا.)

---

### ISS-U05 — Authority / finality calibration across the journey

> **Class** UX/product (principle) · **Status** OPEN (design principle, partially shipped) · **Severity** 🟡 · **Lane** PO → CC · **Gates** **Gate-2** · **Cross-refs** §2c, §0.4 (disclosed-indicative), ISS-R03 (RICS scope), ISS-U02, Honesty principles · **First logged** methodology (recurring)

**Summary.** A cross-cutting UX principle, logged as an issue because it must be *enforced per screen*: **authority starts low and rises only with accountability**, and it rises **only at the final, accountable stage** (the report). Earlier screens must look *appropriately provisional*. Drama and visual weight should attach to **analytical depth and evidence quality** — never to hyping the headline figure. Explanation must never *look like* it raised confidence.

**Evidence / detail (measured✓ / assumed~).**
- ✓ §2c rule set: drama/authority attach to depth + evidence, never the figure; **explanation does not raise confidence**; authority starts low, rises with accountability at stage 5.
- ✓ The evidence-quality panel (b.2.2) is the *correct* visual home for "drama" — it makes the *evidence* legible, not the number.
- ✓ §0.4 standing principle: where a value-affecting method ships, it ships **disclosed-as-indicative** with a wide MUC and a "calibrated on limited n" caveat — the UI must carry that caveat, not bury it.
- ~ Whether each shipped screen currently respects the "low early, high only at report" gradient has not been audited end-to-end (an R14 UI audit item).

**Root cause.** Confidence-signalling is emergent across many small UI choices (font weight, the word "estimate" vs "valuation," where the ± band sits, whether a green check reads as "correct"). Without an explicit per-screen check it drifts upward (UIs tend to over-claim).

**Impact.** Mis-calibrated authority is a *credibility* and *regulatory* risk (over-claiming on a free, non-accredited indicative product — ISS-R01/R03). Correctly calibrated, it is a core differentiator.

**Current mitigation / shipped state.** The confirmation gate is deliberately **neutral** («تابِع بهذه البيانات» = proceed, not assert-correct); the evidence panel carries the analytical weight; confidence is structurally decoupled from explanation (§2c).

**Remediation / next action.** Add an **authority-gradient check** to the per-screen R14 UI audit: confirm earlier screens read provisional, the report is the only "accountable" surface, and every disclosed-indicative method carries its caveat (§0.4). Keep RICS/IVS claims scoped to what the engine actually does (ISS-R03).

**Dependencies / blockers.** None to *state* the principle; Gate-2 + R14 to enforce per screen.

**«القرار المطلوب».** لا قرار — مبدأ تنفيذيّ يُدقَّق ضمن مراجعة R14 لكلّ شاشة.


---

## 3.R — Regulatory / compliance issues

> Thammen operates in a regulated domain. Two framings recur and must be kept straight:
> - **Track A vs Track B.** *Track A* = indicative analytics, no licensed valuer required; the output is explicitly **not** an accredited valuation. *Track B* = a licensed entity with a valuer's sign-off. **Thammen's design already aligns with a compliant Track A** (free, indicative, "not an accredited valuation"). The Aqarat licence question lives at the **monetization** boundary, not the beta boundary.
> - **The 2026-06-09 reframe.** The beta launches under **6/2 self-clearance** as a free, non-accredited, indicative tool; the Aqarat licence is a **pre-monetization** gate (R13), **not** a pre-beta ritual. The conservative R13 copy (free / "not an accredited valuation" / no paid pathway live) is retained as **R13 cover**, not as a beta gate.

### ISS-R01 — Aqarat licence is a pre-monetization gate (R13), not a beta gate

> **Class** regulatory · **Status** OPEN (gated to monetization) · **Severity** 🟠 · **Lane** PO · **Gates** **R13** (regulatory cover) · **Cross-refs** Amiri Decision No. 28 of 2023 Art. 5(7), Track A/B, ISS-R03, ISS-R04, ISS-G03, `Aqarat_Enquiry_DRAFT_hold.md` · **First logged** regulatory recon

**Summary.** Real-estate valuation (التقييم العقاري) is a **regulated activity** under **Amiri Decision No. 28 of 2023, Article 5(7)** (note: it is an *Amiri Decision*, **not** "Law No. 28"). Thammen's path is: free invite accuracy-beta → validate the engine → **obtain an Aqarat licence → monetize**. The licence sits at the **monetization** boundary. The beta runs as a compliant **Track A** indicative tool under **6/2 self-clearance** and is **not** gated on the licence.

**Evidence / detail (measured✓ / assumed~).**
- ✓ Regulated activity cited correctly as **Amiri Decision No. 28 of 2023, Art. 5(7)** (the "Law No. 28" phrasing is a known mis-citation to avoid).
- ✓ R13 is the risk-register entry for regulatory self-clearance; the 2026-06-09 cleanup explicitly keeps R13's conservative framing as **cover** (free / not-accredited / no-paid-pathway) while **removing** any implication that the licence gates the *beta*.
- ✓ A regulatory enquiry to Aqarat is **drafted** in two Arabic variants (free-beta + paid-pathway) and saved as `Aqarat_Enquiry_DRAFT_hold.md`, on **HOLD** — to be sent only **after** product design/build is complete and **before** monetization. It is **not** a pre-invite gate.
- ~ No dedicated AVM licensing category exists yet in Qatar (ISS-R04), so the exact licence form for an AVM-backed service is itself an open regulatory question.

**Root cause.** The activity is regulated at the *paid-valuation* boundary; an indicative free tool that disclaims accreditation is a different (Track A) posture.

**Impact.** Mis-reading this as a *beta* gate would needlessly block validation; mis-reading it as *irrelevant* would risk monetizing without a licence. The correct reading: beta now (under cover), licence before money.

**Current mitigation / shipped state.** a24 shipped the consent gate + Terms/Privacy + DPIA + log-scrub; the product copy carries the "not an accredited valuation" framing (R13 cover). The Aqarat enquiry is drafted and held.

**Remediation / next action.** Run the beta under 6/2 self-clearance + R13 cover. **Before monetization**, send the held Aqarat enquiry and obtain the licence. Keep the "not an accredited valuation" disclaimer prominent throughout.

**Dependencies / blockers.** Product design/build "complete enough" to send the enquiry (PO timing). ISS-R04 (no AVM category) may shape the licence form.

**«القرار المطلوب».** توقيت إرسال استفسار Aqarat (محجوز لك): بعد اكتمال التصميم/البناء وقبل التسييل — وليس قبل الدعوات.

---

### ISS-R02 — PDPPL self-clearance + cross-border data flows (R11)

> **Class** regulatory/privacy · **Status** OPEN (gates capture activation) · **Severity** 🟠 · **Lane** PO · **Gates** **gate #11**, §8.1 (PDPPL), §8.2 (cross-border) · **Cross-refs** R11, ISS-U04, ISS-R05, ISS-R06, a24 (DPIA/log-scrub) · **First logged** a15/a24

**Summary.** Activating capture (collecting owner inputs, feedback, possibly known-sale submissions) brings Thammen under **PDPPL** (Qatar's Personal Data Privacy Protection Law) obligations (**§8.1**) and raises **cross-border** data-flow questions (**§8.2**) if data leaves Qatar (e.g. database residency on a non-Qatar Heroku region). These are the regulatory half of the capture-activation gate (gate #11); the engineering half is ISS-R06 (security) and ISS-U04 (the UI).

**Evidence / detail (measured✓ / assumed~).**
- ✓ a24 shipped a **consent gate + Terms/Privacy + DPIA + log-scrub** — the privacy groundwork for *running* the tool.
- ✓ The two PO-owned activation decisions are **database residency** and **free-text field handling** (gate #11) — residency is exactly the §8.2 cross-border question; free-text handling is the §8.1 minimization/handling question.
- ✓ Capture is currently **DORMANT**, so no personal-data collection beyond what consent + log-scrub already govern.
- ~ Whether the current Heroku region constitutes a cross-border transfer under PDPPL §8.2 needs a definitive read (PO + any counsel).

**Root cause.** Personal data + free text + (possibly) non-Qatar storage = PDPPL §8.1/§8.2 obligations that must be settled *before* the data starts flowing.

**Impact.** Getting residency/free-text wrong post-activation is a compliance and trust failure. Settling them first makes capture activation clean.

**Current mitigation / shipped state.** Consent + DPIA + log-scrub shipped (a24); capture dormant; no free-text capture live.

**Remediation / next action.** Resolve **gate #11** (residency under §8.2 + free-text handling under §8.1) → security pass (ISS-R06) → activate capture (ISS-U04). Until then, grow GT via manual reports/sales.

**Dependencies / blockers.** PO decisions (residency, free-text); possibly external counsel for §8.2.

**«القرار المطلوب».** قرارا gate #11 المحجوزان لك: **مقرّ البيانات (§8.2 عبر-الحدود)** + **معالجة الحقل الحرّ (§8.1)**.

---

### ISS-R03 — RICS / IVS claim scope must match what the engine actually does

> **Class** regulatory/standards · **Status** OPEN (continuous discipline) · **Severity** 🟠 · **Lane** Claude.ai (copy sign-off) → CC (copy) · **Gates** **Gate-2** · **Cross-refs** Appendix G (RICS/IVS map), Rule #54 (multi-AI validation of evolving standards), ISS-U05, a20 (rics_compliant label fix) · **First logged** RICS recon / a20

**Summary.** The product frames its methodology with **RICS Red Book / IVS** references. Two failure modes must be policed continuously: (1) **over-claiming** — implying an accredited Red Book *valuation* when the output is a Track-A *indicative analysis*; and (2) **citation drift** — the **2025 Red Book renumbering** means stale citations point to the wrong clause. Both are live, ongoing copy-governance duties.

**Evidence / detail (measured✓ / assumed~).**
- ✓ The 2025 Red Book renumbering is mapped (Appendix G): VPS 3→**VPS 6** (Reports); VPS 4→**VPS 2** (Bases of Value); VPS 5 split into **VPS 3** (Approaches) + **VPS 5** (Models); IVS 105→**IVS 103**. All six citation groups in the live copy were confirmed correct against **primary sources**.
- ✓ Rule #54: multi-AI validation is required for evolving regulatory standards, and **primary-source overrides consensus** when standards were recently renumbered (exactly this case).
- ✓ a20 fixed the **`rics_compliant`** label (closed A7) — an example of label scope being corrected to avoid over-claiming.
- ~ Continuous: every new user-facing methodology string is a fresh chance to over-claim or mis-cite.

**Root cause.** Standards moved (2025), and the temptation to borrow Red Book authority always pulls copy toward over-claiming on a free indicative tool.

**Impact.** Over-claiming is a regulatory exposure (implying accreditation) and a credibility risk; mis-citation undermines the methodology's seriousness. Correct, scoped citations are a genuine differentiator.

**Current mitigation / shipped state.** All six citation groups verified against primary sources; the `rics_compliant` label corrected (a20); RICS copy passes through Claude.ai sign-off (the analyst lane's explicit remit).

**Remediation / next action.** Keep every RICS/IVS string scoped to *indicative Track-A* use; re-verify against **primary sources** (not consensus) whenever standards change (Rule #54); route all such copy through Claude.ai sign-off + Gate-2. The **report screen (ISS-U03)** is where this matters most (authority stage).

**Dependencies / blockers.** None — continuous discipline; Gate-2 on copy.

**«القرار المطلوب».** لا قرار — انضباط مستمرّ: كلّ ادّعاء RICS/IVS مقيَّد بالاستخدام الإرشاديّ (Track A)، ويُراجَع على المصدر الأوّليّ عند أيّ تغيّر معياريّ.

---

### ISS-R04 — No dedicated AVM licensing category exists in Qatar yet

> **Class** regulatory (environmental) · **Status** OPEN (external/structural) · **Severity** 🟡 · **Lane** EXT/PO · **Gates** — · **Cross-refs** ISS-R01, ISS-R03, Track A/B, "AVM cannot be primary lending valuation" · **First logged** regulatory recon

**Summary.** Qatar's regime regulates *valuation* (Amiri Decision 28/2023) but has **no dedicated AVM licensing category**. Two consequences: an AVM **cannot serve as the primary lending valuation** (a human licensed valuation is required for that use), and the **exact licence form** for an AVM-backed commercial service is an open question that shapes ISS-R01.

**Evidence / detail (measured✓ / assumed~).**
- ✓ No AVM licensing category in Qatar yet; an **AVM cannot be a primary lending valuation** (recorded as a standing regulatory fact).
- ✓ This reinforces the **Track A** posture: position the product as indicative analytics, not as a substitute for an accredited/lending valuation.
- ~ The regulator's eventual treatment of AVMs (a new category? a Track-B wrapper? bundled under an existing licence?) is unknown — hence the held Aqarat enquiry (ISS-R01) is partly a *category-clarification* request.

**Root cause.** The technology is ahead of the local regulatory taxonomy.

**Impact.** Limits the *claims* and *use cases* (no lending-primary), and adds uncertainty to the licence path. Neither blocks a free indicative beta.

**Current mitigation / shipped state.** Track-A posture + "not an accredited valuation" disclaimer + no lending-primary claim.

**Remediation / next action.** Use the held Aqarat enquiry (ISS-R01) to also seek **category clarification**; keep claims within Track A until the regulator's stance is known.

**Dependencies / blockers.** External (regulator). Couples to ISS-R01 timing.

**«القرار المطلوب».** لا قرار الآن — يُدرَج استيضاح «فئة ترخيص AVM» ضمن استفسار Aqarat المحجوز.

---

### ISS-R05 — Instrumentation activation gate (gate #11) — the meta-gate

> **Class** regulatory/process · **Status** OPEN (meta-gate) · **Severity** 🟠 · **Lane** PO · **Gates** **gate #11**, §8.1, §8.2 · **Cross-refs** R11, ISS-U04, ISS-R02, ISS-R06, ISS-A08 (E12) · **First logged** a15

**Summary.** "Instrumentation activation" is the single decision that flips the beta from **opinion-gathering** to **error-measurement**. It is a *meta-gate* because it bundles a regulatory decision (residency/free-text under PDPPL — ISS-R02), a security decision (at-rest + endpoint hardening — ISS-R06), and a product decision (the feedback UI — ISS-U04). All three must clear together (gate #11).

**Evidence / detail (measured✓ / assumed~).**
- ✓ a15 framing: "Launching **without** [instrumentation] = opinion-gathering; launching **with** = error measurement." Two PO decisions (residency + free-text) + a security pass precede activation.
- ✓ Capture is **DORMANT** now; the meta-gate is *not yet opened*, and per the 2026-06-09 cleanup it is **not** a beta blocker — GT grows manually until then.
- ✓ This connects to ISS-A08 (E12): because MoJ self-calibration is *blocked* (PN-hash), the **only** path to a true error distribution is *captured* ground truth (manual now, instrumented later) — which is exactly what this gate governs.
- ~ The order within the gate (residency → free-text → security → UI) is logical but the PO may sequence differently.

**Root cause.** Measuring error requires collecting real outcomes; collecting real outcomes touches privacy + security → a bundled gate.

**Impact.** Until opened, the beta yields *qualitative* signal + *manual* GT. Once opened, it yields a measurable error distribution (the thing ISS-D08 says we currently lack).

**Current mitigation / shipped state.** Dormant; manual GT path; a24 privacy groundwork in place.

**Remediation / next action.** Open gate #11 when ready: resolve ISS-R02 (residency/free-text) + ISS-R06 (security) + build ISS-U04 (UI). Sequence as a parallel, non-blocking track to the engineering forward-sequence.

**Dependencies / blockers.** ISS-R02, ISS-R06, ISS-U04.

**«القرار المطلوب».** فتح gate #11 (التفعيل) قرار محجوز لك ويجمع: residency/free-text + أمن + واجهة التغذية الراجعة. ليس حاجزاً للبيتا.

---

### ISS-R06 — Capture-surface security (rate-limit /api/feedback, free-text, at-rest)

> **Class** regulatory/security · **Status** OPEN (part of gate #11) · **Severity** 🟠 · **Lane** CC (build) ← PO (gate) · **Gates** **gate #11** · **Cross-refs** ISS-R05, ISS-R02, ISS-U04, Rule #61 (Cloudflare/UA), live security state (CORS/rate-limit/docs-locked) · **First logged** a15/security pass

**Summary.** Before any capture endpoint goes live it needs the same hardening the existing surface already has, plus free-text–specific care: **rate-limiting** on the feedback/submit endpoint, **free-text sanitisation/handling** (injection + PII minimization), and **encryption at rest** for stored submissions. This is the engineering half of gate #11 (ISS-R05); the regulatory half is ISS-R02.

**Evidence / detail (measured✓ / assumed~).**
- ✓ The live surface is already hardened: **CORS locked**, rate limits **5/s · 30/min · 200/h on `cf-connecting-ip`**, **docs locked** (confirmed this session). A capture endpoint must inherit equivalent controls.
- ✓ Browser **User-Agent required** for `/api/evaluate` (Cloudflare 1010 blocks otherwise — Rule #61); a feedback endpoint behind the same Cloudflare will share this behaviour.
- ✓ slowapi gotcha (Rule-adjacent): the **list-form** `@limiter.limit([...])` *silently fails* — use the **semicolon-joined string** form. A new feedback limiter must use the working form.
- ~ At-rest encryption + free-text sanitisation are *required* but unspecified in detail (depends on the residency decision in ISS-R02).

**Root cause.** A new public write-endpoint that ingests free text + stores personal data is a fresh attack/exposure surface that must match the rest of the system before activation.

**Impact.** An unhardened capture endpoint is both a security risk and a PDPPL exposure. Hardened, it safely turns the beta into a measurement instrument.

**Current mitigation / shipped state.** No capture endpoint live (dormant); existing surface hardened as above.

**Remediation / next action.** When gate #11 opens: add the feedback endpoint with **working-form** rate limits, free-text sanitisation, at-rest encryption (per the residency decision), and the Cloudflare-UA expectation; security-review before exposing.

**Dependencies / blockers.** ISS-R02 (residency drives at-rest choice); gate #11 (PO).

**«القرار المطلوب».** لا قرار جديد — بنود أمن تُنفَّذ عند فتح gate #11 (تقييد معدّل + تعقيم الحقل الحرّ + تشفير عند التخزين).


---

## 3.G — Governance / process issues

> These issues are about *how the project knows what's true*. The 2026-06-09 governance cleanup (the signed directive this log builds on) was a **doc-only** pass that fixed several framing defects without touching code or opening a new Gate-2. Its surgical rule is the spine of this section: **do not delete measured facts — change only the conclusions built on them.** (The closed feeds, the not-geocoded MoJ, the PN-hash closure are all *true*; what changed is the *inference* "therefore no path exists.")

### ISS-G01 — Roadmap drift → CLAUDE.md #65a is the single forward source

> **Class** governance · **Status** OPEN→being-closed (doc cleanup) · **Severity** 🟠 · **Lane** PO + CC · **Gates** — (doc-only) · **Cross-refs** CLAUDE.md #65a, Project_Instructions §11 (DEPRECATED), 2026-06-09 cleanup edit #6 · **First logged** 2026-06-09

**Summary.** Multiple documents carried *roadmap* content (Project_Instructions §11 convenience-roadmap, scattered "next steps" in recon files, drifted sequences in older sessions). They diverged over time, so "what's next" had several non-identical answers. The cleanup designates **CLAUDE.md #65a as the single forward source** and marks the others **DEPRECATED → see #65a**.

**Evidence / detail (measured✓).**
- ✓ Cleanup edit #6: *"Designate CLAUDE.md #65a as the single forward source; mark Project_Instructions §11 convenience-roadmap 'DEPRECATED → see #65a'; reconcile LAUNCH_GATES."*
- ✓ #65a is described in the corpus as the **single canonical source for launch-gating and engineering-next framing**, and Rule #65a says **do not auto-pick** the next engineering step — present to Anas.
- ✓ This log treats #65a as authoritative for the forward sequence (Part 5).

**Root cause.** Several files independently grew "next steps"; none was declared the source of truth, so they drifted.

**Impact.** Drifted roadmaps cause the two lanes (and future sessions) to act on different plans — exactly the cross-chat divergence R1 warns about.

**Current mitigation / shipped state.** #65a designated single source; §11 to be marked DEPRECATED (doc edit in the cleanup commit).

**Remediation / next action.** Ensure the cleanup commit (a) stamps §11 DEPRECATED→#65a, (b) reconciles LAUNCH_GATES to #65a, (c) leaves #65a as the only place the forward sequence is *authored*. All future roadmap edits happen in #65a only.

**Dependencies / blockers.** None — doc-only; CC commits.

**«القرار المطلوب».** لا قرار — #65a هو المصدر الأماميّ الوحيد؛ §11 يُعلَّم DEPRECATED.

---

### ISS-G02 — "No-source / blocked-indefinitely" framing rot → ship-disclosed principle

> **Class** governance (methodology framing) · **Status** OPEN→being-closed · **Severity** 🔴 · **Lane** PO + Claude.ai + CC · **Gates** — (doc-only; the *principle* is signed) · **Cross-refs** §0.4, cleanup edit #1, ISS-A04, ISS-A10, ISS-D07, ISS-D08, E12, b4/b11 precedent · **First logged** 2026-06-09

**Summary.** The single most consequential governance defect: several docs framed value-affecting methods as **"blocked / deferred indefinitely / no viable source,"** which silently *blocked* shipping B-2, cost-triangulation, D5/D6, and the error distribution. The cleanup replaces this with the **ship-disclosed principle** (new Empirical, see §0.4): value-affecting methods **ship disclosed-as-indicative** (opt-in or rail-governed + wide MUC [VPGA 10] + "calibrated on limited n" + a [land_floor, cost] rail), then **tighten as GT grows**. **n≥20 gates precision, not shipping** (precedent: b4/b11 shipped on **n=2**). GT grows via **(a) manual valuer-reports/sales** and **(b) organic beta** — *not* "no source."

**Evidence / detail (measured✓).**
- ✓ Cleanup edit #1 (across CLAUDE.md · Project_Instructions §11+§20 · Empirical · RISK_REGISTER · recon): replace *"blocked / deferred-indefinitely / no source"* with the ship-disclosed principle.
- ✓ The **surgical rule** is explicit: **keep the measured facts** — closed feeds (secretary + Gardenia), MoJ **not geocoded**, **PN-hash closed (E12)** are all *true* and **stay**; only the *conclusion* built on them changes.
- ✓ Precedent is real: **b4** (luxury-new stratum) and **b11** (cost-reanchor down-half) both **shipped on n=2**, disclosed/rail-governed — so "ship disclosed, tighten later" is established practice, not a new risk.
- ✓ §6 (income guidance) is cited as the same pattern (ship disclosed-as-indicative).

**Root cause.** "Blocked/no source" is *true at the level of a specific automated feed* (e.g. a live Mthamen integration, an automated confirmed-sales API) but was over-generalised into "the *method* cannot proceed," which is false — the method can ship disclosed and improve on manual+organic GT.

**Impact.** This framing was *the* thing suppressing the engine's accuracy roadmap (B-2, cost UP-lift, error distribution). Correcting it unblocks the entire "improve accuracy" programme without lowering rigor (MUC + rails + caveats stay).

**Current mitigation / shipped state.** The principle is **signed** (نعم) and recorded as §0.4 in this log; the cleanup commit propagates the re-framing across files; b11 down-half is already a live instance of the principle.

**Remediation / next action.** Propagate the re-framing in every file that carried the old phrasing (without deleting facts); record the new Empirical; ensure B-2, §20.9 UP-lift, D5/D6, and the error distribution are described as **disclosed-indicative ship paths**, not blocked items.

**Dependencies / blockers.** None — doc-only; the principle is the unlock.

**«القرار المطلوب».** لا قرار — المبدأ موقَّع: المناهج المؤثِّرة تُشحَن مُفصَحة-كإرشاديّة وتُحكَم مع نموّ الـGT؛ تُحذف عبارات «لا مصدر/حجب دائم».

---

### ISS-G03 — Beta as a phantom gate → non-blocking parallel track; delete gate #6

> **Class** governance · **Status** OPEN→being-closed · **Severity** 🟠 · **Lane** PO + CC · **Gates** removes **gate #6** (cohort); reframes **gate-4** · **Cross-refs** cleanup edit #5, #65a, LAUNCH_READINESS_GATES_v1, R13, ISS-U04, ISS-R01 · **First logged** 2026-06-09

**Summary.** The beta had accreted the status of a *gate* (with a cohort-selection sub-gate, gate #6), which made it read as a blocker on the critical path. The cleanup **removes the beta as a gate from #65a**, **deletes gate #6 (cohort)**, **reframes gate-4** ("spot-check on the manual GT *now*; the statistical distribution is a *public-tier* milestone"), and changes income from **"beta-gated"** to **"UX-gated."** The conservative **R13 cover** is retained but explicitly labelled **R13 cover, not a beta ritual.**

**Evidence / detail (measured✓).**
- ✓ Cleanup edit #5: remove beta as a gate from #65a; **delete gate #6 (cohort)**; reframe **gate-4** (spot-check on manual GT now; statistical distribution = public-tier); income "beta-gated" → **"UX-gated"**; keep R13 conservative framing as **cover, not beta ritual**.
- ✓ Beta is reframed as a **parallel, non-blocking track**: collect GT manually + organically; **no cohort, no gate**.
- ✓ This is consistent with ISS-U04 (capture not required for beta) and ISS-R01 (licence is pre-monetization, not pre-beta).

**Root cause.** A validation *activity* was mis-modelled as a release *gate*, importing a cohort sub-decision (gate #6) that doesn't actually block engine validation.

**Impact.** As a phantom gate, the beta blocked forward motion and invited endless cohort deliberation. As a parallel track, validation proceeds while engineering continues.

**Current mitigation / shipped state.** The reframe is signed; the cleanup commit removes the gate language and deletes gate #6.

**Remediation / next action.** Update #65a + LAUNCH_GATES to drop beta-as-gate and gate #6; re-label gate-4 (spot-check-now / distribution-public-tier); change income to UX-gated; keep R13 cover. Run beta as the parallel track in Part 5.

**Dependencies / blockers.** None — doc-only.

**«القرار المطلوب».** لا قرار — البيتا مسار موازٍ غير-حاجز؛ يُحذَف gate #6؛ income يصبح UX-gated؛ يبقى غطاء R13.

---

### ISS-G04 — Mthamen: CLOSED, methodology-reference only

> **Class** governance · **Status** CLOSED (reference-only) · **Severity** 🟡 · **Lane** PO + CC · **Gates** — · **Cross-refs** cleanup edit #3, §20.2–20.4 (methodology kept), §20.8, §20.9 (the independent replacement), Empirical §8.5 · **First logged** 2026-06-09

**Summary.** "Mثمن / Mthamen" had been parked as *deferred with three revival conditions*. The cleanup **closes it**: it is now a **methodology reference only** — the independent **§20.9** work (cost-triangulation) **replaced** it. The §20.2–20.4 *methodology* is **kept**; what's closed is the idea of a *live Mthamen integration* as a pending dependency.

**Evidence / detail (measured✓).**
- ✓ Cleanup edit #3 (CLAUDE.md · §20.8 · Empirical §8.5): *"deferred + 3 revival conditions"* → **"CLOSED — methodology-reference only, full stop; the independent §20.9 replaced it."* Keep §20.2–20.4 methodology.
- ✓ §20.9 (cost-triangulation) is the independent, in-house line that supersedes any dependency on Mthamen as an external source.

**Root cause.** A parked external dependency lingered as a "maybe later" item after an independent in-house method had already replaced its function.

**Impact.** Removes a phantom future dependency from the backlog; keeps the useful methodology.

**Current mitigation / shipped state.** Closed as reference-only in the cleanup; §20.9 down-half already shipped (b11).

**Remediation / next action.** Stamp Mthamen CLOSED/reference-only in CLAUDE.md/§20.8/Empirical §8.5; retain §20.2–20.4 methodology text; point all "cost/triangulation" references at §20.9.

**Dependencies / blockers.** None.

**«القرار المطلوب».** لا قرار — مثمن مُغلَق (مرجع منهجيّ فقط)؛ §20.9 المستقلّ هو الخلف.

---

### ISS-G05 — Memory-hygiene & doc-delta-before-build (the C1 discipline)

> **Class** governance/process · **Status** OPEN (continuous discipline) · **Severity** 🟡 · **Lane** Claude.ai (memory) + CC (docs) + PO (cadence) · **Gates** — · **Cross-refs** Rule #63 (docs-on-disk before briefs reference them), Rule #64 (one unit + docs-close per sprint), memory-hygiene standing instruction, ISS-T07 · **First logged** memory + Rule #63/#64

**Summary.** Two linked process duties keep the project's "truth" from rotting: (1) **memory hygiene** — run maintenance *without being asked* at defined triggers (every 3 closed sprints; after a new E#/Rule; after a ≥3-day sprint; first session after a ≥7-day gap), targeting ≤10 entries; and (2) **doc-delta-before-build** — Rule #63: design documents must be **on disk before briefs reference them** (CC writes them), and Rule #64: **one complete unit + docs-close per sprint**.

**Evidence / detail (measured✓).**
- ✓ Memory-hygiene standing instruction: maintenance = view → classify → update → delete → consolidate → report; target ≤10 entries; defined triggers as above.
- ✓ Rule #63: docs on disk before a brief cites them (prevents briefs referencing phantom docs).
- ✓ Rule #64: one unit + docs-close per sprint (prevents half-shipped features + stale docs).
- ✓ This log itself is a *doc-delta* artifact — it must be committed by CC (Rule #63 spirit) to become canonical, not left only in chat.

**Root cause.** Truth lives in two places (memory + repo docs); without cadence both drift, and briefs can reference docs that don't yet exist.

**Impact.** Drifted memory/docs is the substrate for roadmap drift (G01) and framing rot (G02). The discipline is cheap insurance.

**Current mitigation / shipped state.** The standing instruction + Rules #63/#64 are in force; this session is itself producing a doc-delta (this log).

**Remediation / next action.** Run memory maintenance on the next applicable trigger; ensure this log is committed by CC; keep "docs-close" part of every sprint's DoD.

**Dependencies / blockers.** None — discipline; CC for commits.

**«القرار المطلوب».** لا قرار — صيانة الذاكرة تُجرى على المحفّز التالي؛ هذا الملف يُسلَّم إلى CC للـcommit.

---

### ISS-G06 — Two-lane context isolation: Anas is the sole router

> **Class** governance/architecture · **Status** MITIGATED (structural, by design) · **Severity** 🟠 · **Lane** PO (router) · **Gates** Gate-1/Gate-2/Gate-3 · **Cross-refs** ROLES_AND_COMMS.md, R1, R3, Rule #57 (handshake), Rule #58 (probe-don't-pin), ISS-T04 · **First logged** roles model

**Summary.** The operating model has **two lanes that do not share context**: **Claude.ai** (methodology coach, brief author, RICS sign-off, independent verifier — *chat text only, never writes files*) and **CC / Claude Code** (sole implementer at `C:\Thammen\deploy v2` — writes files, builds, deploys). **Anas is the sole router**: he copy-pastes between lanes and is the **sole gate authority**. The shared truth is **git + docs**. This is a deliberate design that *creates* a risk (divergence) which is then *managed* by ritual.

**Evidence / detail (measured✓).**
- ✓ Roles: Claude.ai = coach/author/verifier, **outputs chat text only, never writes files**; CC = sole implementer/deployer; **Anas = sole gate authority**, **never** saves/creates files manually, routes between lanes.
- ✓ Shared truth = **git + docs**; Heroku deploy = `git subtree push --prefix "deploy v2" heroku master`.
- ✓ The divergence this *structurally invites* (R1/R3) is mitigated by **Rule #57** (session-start handshake) and **Rule #58** (probe `/api/health`, never pin version from memory).
- ⚠️ *This very document* is an explicit, PO-requested exception to "Claude.ai never writes files" — an **audit/verifier deliverable**. To respect the model, it must be **handed to CC to commit** so git remains the source of truth (see ISS-G05 and the closing note).

**Root cause.** Separating authorship (Claude.ai) from implementation (CC) buys focus + safety but means neither AI sees the other's context; only Anas + git bridge them.

**Impact.** Done with ritual, it's safe and clean. Without ritual (handshake, probe, commit), it's the top divergence risk (R1).

**Current mitigation / shipped state.** Rule #57 handshake + Rule #58 probe in force; git + docs as the bridge; Anas routes + gates.

**Remediation / next action.** Keep the handshake + probe rituals; **commit this log via CC**; never let an analyst-lane artifact live *only* in chat if it's meant to be canonical.

**Dependencies / blockers.** None — structural; relies on PO discipline.

**«القرار المطلوب».** لا قرار — النموذج ساري؛ هذا الملف يُسلَّم إلى CC للـcommit حفاظاً على git مصدراً للحقيقة.

---

### ISS-G07 — Record the standing reality-floor principle (anti-rot anchor)

> **Class** governance (meta) · **Status** OPEN→being-closed · **Severity** 🟡 · **Lane** Claude.ai (memory) + CC (Empirical) · **Gates** — · **Cross-refs** §0.4, ISS-G02, the surgical rule, E12, ISS-D02 · **First logged** 2026-06-09

**Summary.** A meta-governance item: the project keeps re-learning the *same* lesson — a *true local fact* ("this feed is closed," "MoJ isn't geocoded," "PN-hash can't be inverted") gets over-generalised into a *false global conclusion* ("therefore the method is impossible"). The cleanup's **surgical rule** must itself be recorded as a **standing principle**: *keep measured facts; revise only the conclusions built on them.* This is the anti-rot anchor that prevents G02 from recurring.

**Evidence / detail (measured✓).**
- ✓ The surgical rule is stated verbatim in the cleanup: **do not delete the measured facts** — closed feeds, not-geocoded MoJ, PN-hash closure all stay; change the *conclusion* only.
- ✓ E12 (MoJ self-calibration blocked) and ISS-D02 (no PIN/Rule#45) are the canonical examples of *true facts* that were (incorrectly) read as *blocking everything*.
- ✓ §0.4 (ship-disclosed) is the *positive* form of the same principle; G07 is the *defensive* form (don't re-rot).

**Root cause.** Without an explicit "facts vs conclusions" discipline, every true constraint tends to metastasise into a blanket blocker.

**Impact.** Recording this principle is what stops the next session from re-introducing "no source / blocked" framing on top of the same true facts.

**Current mitigation / shipped state.** The surgical rule is signed and applied in this cleanup; this log records it as a standing principle (here + §0.4).

**Remediation / next action.** Add the principle to Empirical/Operational as a standing rule ("distinguish measured fact from inferred conclusion; revise conclusions, preserve facts"); cite it whenever a "blocked/no-source" phrase is proposed.

**Dependencies / blockers.** None.

**«القرار المطلوب».** لا قرار — يُسجَّل مبدأ «احفظ الحقيقة المقيسة، راجِع الاستنتاج فقط» قاعدةً ثابتة مضادّة-للتآكل.


---

# PART 4 — DEFERRED / PARKED REGISTER

> A *parked* item is not abandoned — it has a **revival trigger**. Per the ship-disclosed principle (§0.4) and the 2026-06-09 surgical rule, none of these is "blocked / no source"; each is *waiting on a specific, nameable condition*. The distinction this log enforces: **n≥20 (and similar thresholds) gate precision, not shipping** — so several of these can move from PARKED to a *disclosed-indicative ship* before their precision threshold is met.

## 4.1 — Deferred/parked summary table

| ID | Item | Status | Class | Lane | Revival trigger | Ships-disclosed-first? |
|----|------|--------|-------|------|-----------------|------------------------|
| DEF-01 | **B-2** durable condition/built-type fix | PARKED | accuracy | PO→CC | 2.22.0b UX vision (PO) **+** n≥20 confirmed sales | **Yes** — disclosed-indicative ship allowed before n≥20 (§0.4) |
| DEF-02 | **Phase-2** pool-purity + thin-window (R8) | PARKED | accuracy | CC | After the R7 priorities (§20.9 GATED slice / B-2) + decomposition coherence (ISS-A07) — *(the old A16/R9 dependency is void: closed at a18)* | Partial — purity diagnostics can ship as disclosure |
| DEF-03 | **Capture activation** (instrumentation) | DEFERRED | infra/regulatory | PO→CC | gate #11 (residency + free-text) + security pass | n/a (it *is* the instrument) |
| DEF-04 | **MME apartments** | OUT-OF-V1-SCOPE | product/data | EXT→PO | MME authentication integration + confirmed apartment sales (n≥10 indicative / ≥20 reliable) | Future dependency, **not a blocker** |
| DEF-05 | **2.21.5 hybrid input UI** | PARKED | UX | CC | Superseded by DESIGN_2p2x v4 five-screen flow; revive only if v4 screen-3 needs it | Folded into ISS-U01/U02 |
| DEF-06 | **2.18.2 GIS dedup** | PARKED | tech-debt | CC | If duplicate-GIS-feature noise resurfaces in a real trace | Diagnostic-only |
| DEF-07 | **2.17 (pre-cost line)** | SUPERSEDED | methodology | CC | Replaced by §20.9 cost-triangulation; reference-only | n/a |
| DEF-08 | **2.20.1 within-bracket size adjustment** | PARKED | accuracy | CC | Bracket matching is correct since a18 (errata); parked on its own merits — tune after Phase-2 window/purity | Partial |
| DEF-09 | **Cosmetic / polish sprints** | PARKED | UX | CC | After the five-screen flow is built to v4 spec (ISS-U01) | n/a |
| DEF-10 | **D5/D6 provisional source tiers** | PARKED→shippable | data | CC | Ships disclosed-indicative per §0.4; tighten as corroborated | **Yes** |
| DEF-11 | **Error-distribution (true)** | PARKED→building | accuracy | PO→CC | Built from manual GT now (spot-check); statistical distribution = public-tier milestone | Spot-check ships now |
| DEF-12 | **Report two-values display** (MV + forced-sale MV×0.90 — a CONVENTION; `index.html`/report change) | DEFERRED | UX/report | CC | §20.45-deferred; schedule with the screen-5 report build (ISS-U03) | n/a |
| DEF-13 | **Soil/geotech factor** (sabkha/karst) | DEFERRED | accuracy/data | CC | §20.45-deferred; v2 GIS layer availability | n/a |

## 4.2 — Parked entries (detail)

### DEF-01 — B-2 (durable condition / built-type fix) — the R7 remedy

> **Status** PARKED · **Cross-refs** ISS-A01 (R7), ISS-A10, ISS-U02, E23, V001/V002/V003 · **Lane** PO (2.22.0b vision) → CC

**What it is.** The durable fix for **R7** (the bidirectional built-type + condition blindness). Direction is established: **built-type + condition elicitation** (the Maamoura 56/647/6 reference case), with two levers — **Lever 1**: a luxury/new-build finish premium via the **`luxury_new` (E4) stratum ppm²**; **Lever 2**: a downward **land re-anchor** for old non-luxury stock via the **10-Year Rule / `value_floor`**. Lever 2 unlocks sooner because old-stock confirmed sales are more common; the b11 **`cost_reanchor_down`** is effectively a first, disclosed instance of the Lever-2 idea.

**Why parked / revival trigger.** Gated on **(1)** the 2.22.0b UX vision (Anas's reserved decision) and **(2)** **n≥20** confirmed sales in the ground-truth corpus. **But** per §0.4, a *disclosed-indicative* B-2 (opt-in, rail-governed, "calibrated on limited n," [land_floor, cost] rail) may ship **before** n≥20 — n≥20 gates *precision*, not *shipping*. Precedent: b4/b11 shipped on n=2.

**Note.** E23: over-anchor is diagnosed by **dispersion ≥0.30**, not thinness — so B-2's condition axis must be calibrated against *dispersion-confirmed* over-anchor cases, not merely thin pools.

---

### DEF-02 — Phase-2 pool-purity + thin-window (R8)

> **Status** PARKED · **Cross-refs** ISS-A02, R8, E20 (compound ≥15K m²), pool-purity gates · **Lane** CC

**What it is.** The Phase-2 work on **comparable-pool purity** (filtering contaminating transactions — wrong RULEID/zoning, commercial-priced land 3–5× residential, compound aggregates ≥15K m²) and **thin-window** handling (when too few clean comparables fall in the time window).

**Why parked / revival trigger.** *(Errata: the A16/R9 prerequisite is void — matching fixed at a18.)* Sequenced after the R7 priorities and the decomposition-coherence fix (ISS-A07). Purity **diagnostics** can ship as *disclosure* (surface "limited comparables quality" in the evidence panel) before the full purity engine lands.

---

### DEF-03 — Capture activation (instrumentation)

> **Status** DEFERRED · **Cross-refs** ISS-U04, ISS-R05, ISS-R06, R11 · **Lane** PO → CC

**What it is.** Turning on the feedback/submission capture that converts the beta from opinion-gathering to error-measurement.

**Why deferred / revival trigger.** Opens with **gate #11** (database residency under §8.2 + free-text handling under §8.1) + a **security pass** (ISS-R06). **Not** a beta blocker — manual GT is the interim engine. Reframed in the 2026-06-09 cleanup as a **parallel, non-blocking** track.

---

### DEF-04 — MME apartments

> **Status** OUT-OF-V1-SCOPE · **Cross-refs** ISS-D05, cleanup edit #2, LAUNCH_GATES gate-1 · **Lane** EXT → PO

**What it is.** Extending coverage to **apartments**, which requires **MME** (Ministry of Municipality and Environment) authentication integration + confirmed apartment sales.

**Why out-of-scope / revival trigger.** The 2026-06-09 cleanup re-framed this from **"BLOCKED (auth)"** to **"out of v1 scope (the product is villas + land); MME auth is a future-scope dependency, not a current blocker."** Revival = MME authentication integration + confirmed apartment sales (n≥10 indicative / ≥20 reliable). The current apartment **refusal** path (anchor 52/903/90) is the correct v1 behaviour.

---

### DEF-05 — 2.21.5 hybrid input UI

> **Status** PARKED (superseded) · **Cross-refs** ISS-U01, ISS-U02, DESIGN_2p2x v4 · **Lane** CC

**What it is.** An earlier "hybrid" input-UI concept.

**Why parked / revival trigger.** Superseded by the **DESIGN_2p2x v4** five-screen flow (separate identify/confirm/improve screens). Revive only if v4 screen-3 (improve) specifically calls for a hybrid input pattern; otherwise folded into ISS-U01/U02.

---

### DEF-06 — 2.18.2 GIS dedup

> **Status** PARKED · **Cross-refs** ISS-T01 (QARS), R5, GIS chain · **Lane** CC

**What it is.** De-duplication of GIS features when a lookup returns redundant geometries.

**Why parked / revival trigger.** Low-noise at present. Revive if a real property trace shows duplicate-GIS-feature contamination affecting the result; treat as a diagnostic-first fix.

---

### DEF-07 — 2.17 (pre-cost line)

> **Status** SUPERSEDED · **Cross-refs** ISS-A04, §20.9, ISS-G04 (Mthamen) · **Lane** CC

**What it is.** An earlier pre-cost methodology line.

**Why superseded.** Replaced by the **§20.9 cost-triangulation** programme (the independent line that also closed the Mthamen dependency, ISS-G04). Reference-only.

---

### DEF-08 — 2.20.1 within-bracket size adjustment

> **Status** PARKED · **Cross-refs** ISS-A03 (A16/R9), within-bracket logic · **Lane** CC

**What it is.** Tuning the *size* adjustment applied to comparables *within* a matched bracket.

**Why parked / revival trigger.** Bracket **matching** must be correct first (A16/R9, ISS-A03) — there is no value in tuning the within-bracket size curve while the bracket itself can under-match on area-name. Revive after ISS-A03.

---

### DEF-09 — Cosmetic / polish sprints

> **Status** PARKED · **Cross-refs** ISS-U01, ISS-U05 · **Lane** CC

**What it is.** Visual polish, micro-interactions, and aesthetic refinement.

**Why parked / revival trigger.** The five-screen flow must be **built to v4 spec** (ISS-U01) before polishing it; polishing an unbuilt/soon-to-change screen is wasted. Revive after the flow exists.

---

### DEF-10 — D5/D6 provisional source tiers

> **Status** PARKED → shippable-disclosed · **Cross-refs** ISS-D06, §0.4, E8 (tier weights) · **Lane** CC

**What it is.** Two provisional data-source tiers (D5/D6) beyond the established T1–T4.

**Why parked / revival trigger.** Per §0.4, these can **ship disclosed-indicative** (clearly weighted/capped, "provisional source") rather than waiting for full corroboration; tighten weights as corroboration accrues. This is a direct beneficiary of removing the "no source" framing (ISS-G02).

---

### DEF-11 — Error distribution (true)

> **Status** PARKED → building · **Cross-refs** ISS-D08, ISS-A08 (E12), ISS-R05, gate-4 reframe · **Lane** PO → CC

**What it is.** A true error distribution for the AVM (not just the four value-invariant anchors).

**Why parked / revival trigger.** Because MoJ self-calibration is **blocked** (E12, PN-hash), the distribution must come from **captured ground truth**. The 2026-06-09 cleanup reframes gate-4: a **spot-check on the manual GT can happen now**; the **statistical distribution** is a **public-tier** milestone (i.e. it firms up as the corpus grows via manual + organic GT). So this moves from "blocked" to "building incrementally."


---

# PART 5 — UNIFIED FORWARD SEQUENCE

> This is the single forward plan that **replaces all drifted roadmaps** (ISS-G01); its authoring home is **CLAUDE.md #65a**. Rule #65a still holds: **do not auto-pick** — these are presented in dependency order for Anas's selection, not executed unilaterally. The frame is *engineering on data we control, with no beta gate*; the beta runs as a **parallel, non-blocking** track.

## 5.1 — The sequence at a glance

```
[1] Decomposition-coherence fix      ── Gate-2 PENDING (signed brief awaits Anas)
        │  (credible live, ready at b11)
        ▼
[2] ~~A16/R9 root fix~~               ── REMOVED (errata: resolved at a18, §20.18)
        │  (the §20.9 slice below moves up to be the accuracy step)
        ▼
[3] §20.9 gated slice                 ── convergence-confirm + UP-lift  ← effective step 2
        │  needs: (a) system-age→actual-age + CGIS-gap recon
        │         (b) dilapidated-luxury floor ratio (~0.31) — PO decision
        │  ships: disclosed-indicative (§0.4)
        ▼
[4] Rent-as-UX                        ── surface the rent field → income_led fires on real traffic
        │
        ▼
[5] Parallel / optional (non-blocking):
        • B-2 disclosed-indicative (DEF-01)     • A15 HBU-drop fix (ISS-B02)
        • Phase-2 purity/window R8 (DEF-02)     • A5 unknown-asset_type (ISS-B01)
        • Capture activation (DEF-03 / gate #11) • D5/D6 disclosed tiers (DEF-10)

 ┌─────────────────────────────────────────────────────────────────────┐
 │ PARALLEL TRACK (does NOT gate the above): BETA                        │
 │  collect GT manually (valuer reports / curated sales) + organically.  │
 │  no cohort, no gate (gate #6 deleted). R13 cover stays.               │
 └─────────────────────────────────────────────────────────────────────┘
```

## 5.2 — Step detail, dependencies, and gates

### Step 1 — Decomposition-coherence fix  ·  **Gate-2 PENDING**
- **Maps to:** ISS-A07 (and unblocks ISS-U03 screens 4–5).
- **State:** A **signed brief is pending** — i.e. the brief exists/is-ready and **awaits Anas's Gate-2 signature**. This is the *standing reminder* carried over from the 2026-06-09 cleanup: the governance cleanup **did not** replace this brief.
- **Why first:** Every downstream surface (polished result, report, range-as-lead headline) renders the decomposition; an incoherent land/building/total contradiction would harden into the product's most authoritative screen if built first.
- **Readiness:** Credible and live; ready as of **b11** (which already shipped the cost-reanchor down-half underneath it).
- **Gate:** **Gate-2** (PO signature on the brief). After signing → CC implements → R14 UI audit.
- **«القرار المطلوب»:** توقيع Gate-2 على بريف تماسُك التفكيك (ما زال بانتظارك؛ التنظيف لم يستبدله).

### Step 2 — *(REMOVED by the 2026-06-09 errata)* — was "A16/R9 root fix"
- **Why removed:** §20.18 shows a18 (v157, 2026-06-03) had **already** wired `area_match_key` into `build_reference` (the bracket path) and resolved R9 as a pool-fix; live Marikh = comparison_thin 5.4M n=15 same-district. There is **no root brief to author** and no trace prerequisite — the cleanup's promotion rested on the stale legacy register entry. The Marikh residual is **R7 condition**, handled by Step 3 + the parallel B-2.
- **What replaces it:** the **§20.9 GATED slice (Step 3) moves up** to be the accuracy step after Step 1. Optional, non-blocking: the a18 fast-follow live sub-zone demo (معيذر/نعيجة).
- **«القرار المطلوب»:** لا شيء — أُغلق في a18.


### Step 3 (effective Step 2 after the errata) — §20.9 gated slice (convergence + UP-lift)  ·  ships disclosed-indicative
- **Maps to:** ISS-A04 (and supports ISS-U03 decomposition).
- **Already shipped (b11):** the **DOWN half** (`cost_reanchor_down`) — re-anchors an over-anchored old villa toward a cost-informed floor (Marikh 1.9M→2.4M), precedence `income_led > cost_reanchor > widen_down`, using **system age** as a conservative floor.
- **Remaining:** **convergence-confirm** + the **UP-lift** half. Needs **(a)** a recon mapping **system age → actual age** plus the **CGIS gap**, and **(b)** a PO decision on the **dilapidated-luxury floor ratio (~0.31)**.
- **Discipline (both AIs):** build a **pure physical DRC**; **do not** calibrate to reproduce the MoJ median (that kills independence and re-imports R7 blindness); observe the **Market/DRC ratio by segment** (it can be negative); **no hard ceiling**. Open-decision-#4 = an isolated, curated GT source.
- **Ship posture:** **disclosed-indicative** (§0.4) — opt-in/rail-governed, wide MUC, "calibrated on limited n," [land_floor, cost] rail.
- **Gate:** **Gate-2** + the **~0.31 floor** PO decision.
- **«القرار المطلوب»:** قرار نسبة أرضيّة-المتهالك-الفاخر (~0.31) + اعتماد recon العمر/CGIS.

### Step 4 — Rent-as-UX  ·  unlock an existing engine path
- **Maps to:** ISS-A05 / income-led ; surfaced via ISS-U02-adjacent UX.
- **What:** Surface the **rent field** in the owner flow so the **`income_led`** path **fires on real traffic** (the income method already exists in precedence; it just needs a real rent input to activate).
- **Why after 1–3:** It enriches the result once the decomposition is coherent and the cost line is converged; surfacing rent earlier would feed an income cross-check into an incoherent decomposition.
- **Gate:** **Gate-2** (UX surface) + the standing §6 "disclosed-indicative" framing for income.
- **«القرار المطلوب»:** إبراز حقل الإيجار في التدفّق (UX) — income_led جاهز في الأسبقيّة.

### Step 5 — Parallel / optional (non-blocking)
- **B-2 disclosed-indicative** (DEF-01) — the durable R7 remedy; may ship disclosed before n≥20.
- **Phase-2 purity/window (R8)** (DEF-02) — after Steps 1–2; diagnostics can surface earlier.
- **A15 HBU-drop fix** (ISS-B02) — restore HBU when the zoning hint is absent.
- **A5 unknown-asset_type residual** (ISS-B01) — close the residual classification gap.
- **Capture activation** (DEF-03 / gate #11) — opens the error-measurement instrument; parallel, gated by residency/free-text + security.
- **D5/D6 disclosed tiers** (DEF-10) — ship as provisional, weighted/capped.

## 5.3 — The parallel beta track (explicitly non-blocking)

- **Status:** runs **alongside** Steps 1–5; **gates none of them** (ISS-G03).
- **Mechanism:** grow the ground-truth corpus **manually** (valuer reports / curated GT-1/GT-2 sales) **and organically** (real owner use).
- **No cohort, no gate:** **gate #6 (cohort) is deleted**; the beta is not a release gate.
- **Cover, not ritual:** the conservative **R13** posture (free / "not an accredited valuation" / no paid pathway) stays as **regulatory cover** — it is *not* a beta gate.
- **What it feeds:** the **spot-check** form of gate-4 *now* (against manual GT); the **statistical error distribution** later, as a **public-tier** milestone (ISS-D08 / DEF-11). If/when **capture** activates (gate #11), the beta becomes a measurement instrument.

## 5.4 — Critical-path summary (one line)

> **Sign Step-1 brief (Gate-2) → §20.9 convergence+UP-lift disclosed (Step 3, effective 2) → rent-as-UX (Step 4)** — *(the old Step 2, "A16/R9 root", is removed by the errata: resolved at a18)* — building the v4 polished-result + report screens (ISS-U01/U03) *behind* Step 1, with **beta + capture + B-2 + Phase-2 + A15/A5** running as **parallel, non-blocking** tracks.


---

# PART 6 — CLOSED / RESOLVED + FAILED PATHS

> Two kinds of "done" live here. **Closed/resolved** = a risk or bug that was genuinely fixed and verified. **Failed paths** = approaches that were tried (or premised) and *correctly abandoned* — recorded so the project does not re-attempt them. Per the surgical rule (ISS-G07): the *facts* that closed these stay true; only re-opening them on **new evidence** is legitimate.

## 6.1 — Closed risks

| Risk | Title | Closure | Verified by |
|------|-------|---------|-------------|
| **R2** | A14 cold-start 503 | **CLOSED v146** | warm-path + envelope handling; cold-503 no longer reproduces |
| **R6** | Brittle version-pin tests | **MITIGATED** (recurs) | version-format assertions; broad DoD walk (ISS-T06) |
| **R9** | A16 area-name pool starve | **CLOSED a18 (v157)** — *errata: this log first mis-recorded it OPEN* | sibling aggregation wired into `build_reference` + the امريخ override; Marikh same-district n=15 (§20.18) |
| **R10** | Bracket dispersion gate | **CLOSED a14** | dispersion-gate logic shipped; over-anchor diagnosed by dispersion (E23) |
| **R15** | `stock_strata` a18 | **CLOSED a23** | strata wiring completed + verified |

> R1, R3 are **MITIGATED** (structural, via Rules #57/#58 — ISS-T04/G06), not closed. R4 (MoJ stale), R7 (built-type/condition), R8 (purity/window), R11 (instrumentation), R13 (regulatory cover) remain **OPEN/parked** as logged in Part 3. R5 (QARS reachability) and R12 (Cloudflare/urllib) are **MITIGATED** (ISS-T01/T03). R14 (gate integrity) is an **adopted control**.

## 6.2 — Closed bugs

| Bug | Title | Closure | Note |
|-----|-------|---------|------|
| **A6** | Cold-start latency (51/835/17) | **CLOSED** | 51/835/17 is the **closed-A6** marker — explicitly **NOT** a current value-invariant anchor |
| **A7** | `rics_compliant` label scope | **CLOSED a20** | label re-scoped to avoid over-claiming (ISS-R03) |
| **A16** | Bracket-path area-name starve | **CLOSED a18 (v157)** | resolved-as-pool-fix (§20.18); *errata-corrected from "open Medium" in this log*; residual = unreachable-name class ~0.25% (ISS-A03) |
| **A8** | (2.20 defect) | **CLOSED 2.20** | resolved in the 2.20 line |
| **A11** | Zoning / subtype contradiction | **CLOSED** | QARS subtype × Zoning cross-check → **E7** |

> Currently **open** bugs (carried in Part 3): **A5** (unknown asset_type residual — ISS-B01), **A15** (HBU silently dropped — ISS-B02), **A16** (bracket exact-match starve = R9 — ISS-A03 root / ISS-B03 pointer). Live `/api/health` this session: **Critical 0 · High 0 · Medium 3 (A5, A15, A16)**.

## 6.3 — Shipped sprint closures (selected, a-series → b-series)

> A *unit + docs-close per sprint* (Rule #64). Selected closures relevant to the current state:

- **a20** — `rics_compliant` label fix (closed A7); RICS citations verified against primary sources.
- **a23** — `stock_strata` wiring (closed R15).
- **a24** — consent gate + Terms/Privacy + **DPIA** + **log-scrub** (privacy groundwork; R13/PDPPL cover).
- **a25** — **CC BY 4.0** attribution (closed Q13/R13 sub-question: MoJ open data is commercial-use + derivative-OK **with attribution**; attribution is **not** a monetization gate).
- **B-1** — land-floor / HBU decomposition + **bidirectional condition disclosure** (disclose-only, not fix).
- **b.2.1** — separate input screens.
- **b.2.2** — four-component **evidence-quality panel** (data completeness · comparables quality · market recency · building characterization; each strong/moderate/limited; **derived from engine fields §2c, never hand-authored**).
- **b.2.3** — neutral **confirmation gate** («تابِع بهذه البيانات» — proceed, not assert-correct).
- **b.3** — owner-journey polish (screens 1–2).
- **b4** — `luxury_new` (E4) stratum premium — **shipped on n=2**, disclosed (a precedent for §0.4).
- **b11** — **cost-triangulation DOWN-half** (`cost_reanchor_down`; Marikh 1.9M→2.4M; precedence `income_led > cost_reanchor > widen_down`; system-age conservative floor) — **shipped on n=2**, the live instance of the ship-disclosed principle. The b11 DoD broad-walk also **caught + fixed** a real a2.p9 precision regression («الصفقات المشابهة» → «القريبة في النوع والمساحة»).

## 6.4 — Failed / abandoned paths (do not re-attempt without new evidence)

### FP-01 — Mثمن / Mthamen live integration
**Premise.** Use an external Mthamen source as a live cost/triangulation input.
**Why abandoned.** **CLOSED — methodology-reference only** (ISS-G04); the independent **§20.9** cost-triangulation replaced it. The §20.2–20.4 *methodology* is retained.
**Re-open only if.** Never as a *dependency*; the in-house line is the path. (Methodology text remains a reference.)

### FP-02 — PN-hash inversion (MoJ self-calibration)
**Premise.** Invert/crack the MoJ price-notation hash to self-calibrate value from MoJ's own data.
**Why abandoned.** **E12 — BLOCKED.** The de-identification is a **PN-hash** (keyed cipher), **0/26,719** numerically recoverable, **uncrackable** without the key, **and** there is an **ethical hard line**: never invert de-identified data. This is a *true, permanent* fact (ISS-A08/D02).
**Re-open only if.** Never. The conclusion that *therefore no error distribution is possible* was the **false over-generalisation** corrected by §0.4 — the distribution comes from **captured GT**, not from inverting MoJ.

### FP-03 — Secretary / Gardenia confirmed-sales feeds
**Premise.** Source confirmed sales from a secretary-maintained list / the "Gardenia" feed.
**Why abandoned.** Both feeds are **CLOSED** (no longer available). This is a *true fact* and **stays**.
**Re-open only if.** A new, sourced sales feed appears. **Crucially:** the closure of *these specific feeds* does **not** mean "no confirmed-sales source exists" — GT grows via **manual valuer-reports/sales + organic beta** (§0.4 / ISS-G02). The **Aryan developer data survives as an independent T3 channel** (cap 0.15 × min(n,5)/5).

### FP-04 — Stage-1 "input honesty" premise (falsified)
**Premise.** That asking-price/listing inputs could be treated as honest signals of value (under-registration hypothesis).
**Why abandoned.** **Empirically falsified.** Villa asking premiums run **+70.2%** above MoJ median (driven by **stock composition**, not under-registration); land asking premiums **+13.6%** (within global norms). The **MoJ under-registration hypothesis = falsified.** Hence **MoJ is the sole valuation evidence source** (E1/E12); listings appear **only** in the sentiment panel; the **buyer hard ceiling = MoJ × 1.10** (empirically validated for land).
**Re-open only if.** Never on the under-registration premise; the stock-composition explanation is the established one.

### FP-05 — Symmetric ± range as the headline (rejected)
**Premise.** Lead the result with a simple symmetric ± band.
**Why abandoned.** Rejected in favour of the **number-as-a-range-that-refines** (locked-decision #2): the band is *informative and narrows* with owner detail, not a static symmetric ± wrapper. (The *range-as-lead* idea survives; the *symmetric-±* form of it was rejected.)
**Re-open only if.** A signed UX decision revisits the headline form (Gate-2).

### FP-06 — Land-to-median "bidirectional trap" floor (rejected)
**Premise.** Anchor values toward a land-to-median figure as a bidirectional correction.
**Why abandoned.** Rejected as a **"bidirectional trap"** — it would have re-introduced exactly the kind of median-pull that imports R7 blindness (cf. the calibration discipline in Step 3: *do not calibrate to reproduce the MoJ median*). This aligns with **Honesty principle #10** (do not manufacture a comforting-but-wrong central tendency).
**Re-open only if.** Never in the median-pull form; the cost-triangulation **floor** (disclosed-indicative, [land_floor, cost] rail) is the legitimate mechanism instead.

### FP-07 — Confirmed-Sales DB as a product feature (dropped)
**Premise.** Ship a "Confirmed Sales database" as a first-class data source.
**Why abandoned.** **DROPPED — no source** *as a standing automated feed*. The **Aryan developer channel survives as T3**. (Again: "dropped" applies to the *automated DB feature*, not to the *existence of any confirmed sales* — manual GT is real.)
**Re-open only if.** A sourced, maintainable confirmed-sales feed becomes available.


---

# PART 7 — APPENDICES

> Reference material. The authoring homes remain the source files (`Empirical_Findings.md`, `Operational_Rules.md`, `RISK_REGISTER.md`, etc.); these indices are *navigational mirrors* for this log, not replacements. Where a one-liner here and the source file ever disagree, **the source file wins** (and the divergence is itself an ISS-G01 signal to fix).

## Appendix A — Empirical findings index (E1–E23)

| Rule | Title (as authored) | Used in this log |
|------|---------------------|------------------|
| **E1** | Reject "MoJ-uplift" frameworks (asking-premium is stock-composition, not under-registration — *falsified*) | FP-04, ISS-A* framing |
| **E2** | Section 4 Buyer Hard Ceiling validated — **MoJ × 1.10** | FP-04, ISS-A06 |
| **E3** | Listings: tier-weighted entry permitted (T2 ≤0.40 / T3 ≤0.15; **no T1 → confidence ≤ indicative**; ±20% MUC) | ISS-A*, Appendix D |
| **E4** | Villa valuation requires **stock stratification** (`luxury_new` stratum) | DEF-01 (B-2 Lever 1), ISS-A01 |
| **E5** | Premium > 25% on clean stock = red flag | quality gates |
| **E6** | Cost Approach (DRC) is a **documented reference, NOT live integration** (Mthamen) | ISS-G04, FP-01, §20.9 |
| **E7** | QARS subtype requires **Zoning cross-check** for residential codes | ISS-T01, A11 closure |
| **E8** | **Source Tier Weighting** (T1=1.0 / T2=0.7 / T4=0.4) | Appendix D, ISS-A02 |
| **E9** | Cross-Source Validation | Appendix D |
| **E10** | Transparent Source Attribution | ISS-R03, a25 |
| **E11** | Tier Floor for Critical Calculations | Appendix D |
| **E12** | **MoJ Self-Calibration — BLOCKED** (cryptographic PN-hash + ethical hard line) | ISS-A08, ISS-D02, FP-02 |
| **E13** | Coded-value domains are authoritative; **pull them, never guess RULEID** | ISS-A02 (commercial-land filter) |
| **E14** | A validation script must **exercise production logic**, not echo the input | R14, ISS-T05 |
| **E15** | Qatar **MME setback** regulations (front 5 m; load-bearing for multi-villa logic) | ISS-A* (HBU/decomposition) |
| **E16** | **Staged-valuation** pattern (platform-wide) | ISS-U01, staged flow |
| **E17** | **1-field minimum input** principle | ISS-U01/U02 |
| **E18** | Stage 2 **wall-to-wall classification** rule | decomposition |
| **E19** | I/O-bound parallelization: **max_workers = task count** (±2% validated) | ISS-T02, R5 |
| **E20** | MoJ **compound sampling boundary at 15K m²** | ISS-A02, DEF-06 |
| **E21** | **Cold-latency** penalty coupled to the **serial GIS chain**, not dyno spin-up | ISS-T02 |
| **E22** | An adjustment gated on a **non-auto-detected input is INERT** in the default flow | ISS-A04, "measure on default flow" |
| **E23** | **Over-anchor is diagnosed by DISPERSION (≥0.30), not thinness** | ISS-A01, ISS-A03, DEF-01 |

## Appendix B — Operational rules index (cited subset)

> Full register: `Operational_Rules.md` (#1–#65, frozen at #65). The subset this log leans on:

| Rule | Title (as authored) | Used in this log |
|------|---------------------|------------------|
| **#32** | Push & Commit Discipline — متى تدفع، متى تمتنع (Gate-1) | Gate-1, Appendix E |
| **#34** | File-Based Scripts for External Endpoints — لا تشغّل inline | ISS-T08, probe method |
| **#42** | Deferred-Work Documentation — وثّق التخلّي في الـdocs | Part 4, ISS-G05 |
| **#43** | Heroku deploy = `git subtree push` (app lives in `deploy v2/`) | ISS-T07, deploy ritual |
| **#45** | Verify data-linking schema BEFORE proposing batch processing | ISS-D02, ISS-A08 |
| **#46** | Pre-Sprint frontend input-flow audit must validate classifier output for the NEW path | §5 UI-First, R14 |
| **#47** | New asset_type → ALIAS in every lookup dict, never rename | ISS-B01 (A5) |
| **#49** | An identifier is NOT an asset_type — verify the real type via authoritative lookups | ISS-B01, ISS-A03 |
| **#50** | Staged-Sprint Discipline — Stage 1/2/3 lens | ISS-U01 |
| **#51** | Audit-driven Sprint pattern — measure → #11 rollback → refactor → re-verify | ISS-T05, process |
| **#52** | Latency Sprints unmask methodology bugs (post-deploy must read the now-reachable content) | ISS-T02, ISS-A03 |
| **#53** | Closed cases stay closed — including as comparison anchors | Part 6, Appendix C |
| **#54** | Multi-AI consult at sprint open (evolving-standard / effective-date / framing) | ISS-R03, Rule-#54 |
| **#57** | Session-start ground-truth handshake — measure live state before routing work | ISS-G06, ISS-T04 |
| **#58** | Assumed-vs-actual operational gap — measured wins, log the gap (probe, don't pin) | ISS-T04, ISS-T06, §0 |
| **#59** | Major-station reporting format (v2.1) | reporting convention |
| **#60** | Measure-gate for lever sequencing under borderline projection | Step 3, Efficacy-Before-Push |
| **#61** | CC post-deploy POST smoke = browser-UA curl, NOT urllib (Cloudflare 1010) | ISS-T03, ISS-R06 |
| **#62** | A hash of a low-entropy / enumerable input is NOT de-identification — use a random UUID surrogate | ISS-A08, ISS-D02, E12 |
| **#63** | **Claude.ai-authored docs auto-persist to the repo** (deliver with a same-message CC save+commit instruction; `docs/` is the single source of truth) | Closing note, ISS-G05 |
| **#64** | Session cadence + hard stop before compaction | ISS-G05, session cadence |
| **#65** | Standing session-handoff protocol (zero-ask restart) | ISS-G01, ISS-G06 |
| **#65a** | (within CLAUDE.md) Launch-gating + engineering-next snapshot — **single forward source**; do not auto-pick | ISS-G01, Part 5 |


## Appendix C — Anchor & validation catalog

> **Anchors** are *value-invariant* regression guards — byte-identical stability checks referenced (not re-run) during handshakes. **Validation cases** are *ground-truth* sales used to measure accuracy. Per Rule #53, closed cases stay closed even as comparison anchors.

### C.1 — Value-invariant anchors (4)

| PIN (zone/street/parcel) | Area | Expected | Behaviour / role |
|--------------------------|------|----------|------------------|
| **54 / 541 / 6** | Marikh | **5,400,000** (thin → grade B) | **OVER-anchor**, *tracked-not-target*; the live trace for the A16/R9 root (ISS-A03) + the b11 `cost_reanchor_down` subject (1.9M→2.4M) |
| **56 / 565 / 21** | Abu Hamour | **2,400,000** | bracket path; **under-anchors** the new-premium pair (see C.2) |
| **55 / 296 / 13** | — | **2,600,000** | `comparison_thin` (n=8), **land-anchored**; smoke case |
| **52 / 903 / 90** | — | **refusal** | apartment → correct **refusal** path (apartments out-of-v1-scope, ISS-D05) |

> **Explicitly NOT an anchor:** **51 / 835 / 17** — this is the **closed-A6** latency marker, **not** a current value-invariant anchor (a recurring confusion worth stating; Rule #53).

### C.2 — Ground-truth validation cases (GT-2)

| ID | PIN | Area | Ground truth | Engine | Error | Lesson |
|----|-----|------|--------------|--------|-------|--------|
| **V001** | 56 / 647 / 6 | Maamoura | old **premium** villa | **over-anchors** | + | R7 over-anchor half; B-2 reference case |
| **V002** | 56 / 565 / 10 | Abu Hamour | new premium, **SOLD 4.0M** | 2.4–2.5M | **≈ −37/−40%** | R7 under-anchor half (the master defect, ISS-A01) |
| **V003** | 56 / 565 / 12 | Abu Hamour | new premium (pair w/ V002) | 2.4–2.5M | **≈ −37/−40%** | confirms V002; dispersion (E23) not thinness |

> These three are the empirical spine of **R7 / ISS-A01**: the engine **under-anchors new/premium** villas (~−37/−40%) and **over-anchors old** stock — *bidirectional*. The fix direction (built-type + condition elicitation, two levers) is **B-2 / DEF-01**.

## Appendix D — Data-source tiers

| Tier | Sources | Weight / cap | Notes |
|------|---------|--------------|-------|
| **T1** | **MoJ** (`www.data.gov.qa`) + MME apartments (future) | **1.0** (dominant; ≥0.45 when present n≥10) | **Sole valuation evidence source** (E1/E12). CSV: `www.` prefix, `urllib` not curl, `utf-8-sig`, **NBSP normalize**. MME apartments = future-scope (ISS-D05). Confirmed-Sales DB **DROPPED** (no automated source). |
| **T2** | **PropertyFinder · arady.qa · FGRealty** | cap **0.40** (negotiation midpoint −12.5%); **weight ≤0.40** | Listings; enter **only** via `hybrid_valuation_v1()` (E3). Appear in the **sentiment panel**, not as primary evidence. PropertyFinder cap 0.7 in some contexts; ≤0.40 in valuation. |
| **T3** | **Aryan developer data** | cap **0.15 × min(n,5)/5** (off-plan midpoint −17.5%) | **Survives** as an independent developer-direct channel (the only confirmed-sales-adjacent feed left after FP-03/FP-07). |
| **T4** | **PropertyOryx** (p1 sponsored) | **0.40** | Sponsored listing tier. |
| **T5** | **Excluded** — Bayut (JS-dependent), Mzad (Cloudflare + Vue) | **0** | Not ingestible / excluded (`SOURCE_EXCLUSIONS.md`). |
| **D5/D6** | provisional tiers | TBD (disclosed) | **Ship disclosed-indicative** per §0.4 (DEF-10); tighten weights as corroborated. |

## Appendix E — Gate catalog

| Gate | Name | Trigger | Authority | Status |
|------|------|---------|-----------|--------|
| **Gate-1 (G1)** | Push / deploy consent | any Heroku push («push»/«deploy»/«ship»/«ادفع») | **Anas only** (Rule #32) | active |
| **Gate-2 (G2, HARD)** | Methodology / UX sign-off | any user-facing or methodology change **before it is built** | **Anas only** | active — **Step-1 brief PENDING** |
| **Gate-3 (G3)** | Scope expansion | work beyond a signed brief | **Anas** (flag-and-proceed for tactical) | active |
| **gate #6** | Beta cohort selection | (was) before beta launch | Anas | **DELETED** (2026-06-09 cleanup, ISS-G03) |
| **gate #11** | Instrumentation/capture activation | before turning capture on | **Anas** (residency §8.2 + free-text §8.1) + security pass | open meta-gate (ISS-R05) |
| **Launch gates 1–11** | `LAUNCH_READINESS_GATES_v1.md` | pre-launch readiness | Anas | **reconciled to #65a**; gate-1 (apartments) re-scoped; **gate-4** reframed (spot-check-now / distribution = public-tier); beta removed as a gate |

> **Reserved to Anas (PO-only decisions):** the **2.22.0b UX vision**; **land + build-cost methodology**; **opening the beta to real users**; the **dilapidated-luxury floor ratio (~0.31)**; **gate #11** (residency + free-text); **Aqarat enquiry timing**.
> **Delegated (inform-don't-ask, deploy-on-green):** all tactical/technical execution within a signed brief; scope expansion beyond a signed brief = **flag-and-proceed** (G3).


## Appendix F — Glossary

| Term | Meaning |
|------|---------|
| **AVM** | Automated Valuation Model — Thammen's core engine. Cannot serve as a primary *lending* valuation in Qatar (ISS-R04). |
| **MoJ** | Ministry of Justice open transaction data — the **sole valuation evidence source** (T1). Frozen since 2025-12-31. |
| **QARS** | Qatar's GIS parcel/attribute service (`khazna.gisqatar.org.qa` primary; `services.gisqatar.org.qa` vector). |
| **GIS chain** | The serial sequence of GIS lookups whose latency dominates cold response time (E21, ISS-T02). |
| **HBU** | Highest-and-Best-Use — drives the land-floor decomposition (B-1). Silently dropped when zoning hint absent = **A15** (ISS-B02). |
| **DRC** | Depreciated Replacement Cost — the cost approach underpinning §20.9 cost-triangulation. |
| **MUC** | Material Uncertainty Clause (VPGA 10) — the disclosure wrapper for indicative/limited-n outputs (§0.4). |
| **Track A / Track B** | Indicative analytics (no licensed valuer) vs. licensed-entity + valuer sign-off. Thammen = compliant **Track A**. |
| **ppm² / ppm2** | Price per square metre — the stratum unit (e.g. `luxury_new` E4 stratum ppm²). |
| **bracket / bracket-path** | The comparable-selection band; **A16/R9** is the bracket exact-match starve from area-name article-drop / NBSP. |
| **dispersion** | Spread of comparable values; **over-anchor is diagnosed by dispersion ≥0.30**, not thinness (E23). |
| **disclosed-indicative** | A value-affecting method shipped opt-in/rail-governed + wide MUC + "calibrated on limited n" + rail (§0.4). |
| **GT / GT-1 / GT-2** | Ground truth — confirmed sales / valuer reports used to measure accuracy. Grows manually + organically. |
| **PN-hash** | The MoJ price-notation keyed hash; **uncrackable + ethically off-limits** (E12) — self-calibration BLOCKED. |
| **NBSP** | Non-breaking space (`\xa0`) contaminating MoJ values/headers; normalize `re.sub(r'\s+',' ',s).strip()` (ISS-D03). |
| **capture / instrumentation** | The feedback/submission surface that turns the beta into an error-measurement instrument; **DORMANT** (gate #11). |
| **income_led / cost_reanchor / widen_down** | The §20.9 precedence chain (`income_led > cost_reanchor > widen_down`). |
| **the two lanes** | Claude.ai (analyst/author/verifier, chat-only) and CC (implementer/deployer); **Anas routes** (ISS-G06). |
| **6/2 self-clearance** | The compliance basis under which the free indicative beta runs (R13 cover). |
| **PDPPL** | Qatar Personal Data Privacy Protection Law (§8.1 handling / §8.2 cross-border) — governs capture (ISS-R02). |

## Appendix G — RICS / IVS 2025 citation map

> The **2025 Red Book** (Global Standards, effective **31 Jan 2025**) renumbered several clauses. All six citation groups in the live copy were verified against **primary sources** (Rule #54: primary-source overrides consensus on recently renumbered standards). Authority claims must stay scoped to **indicative Track-A** use (ISS-R03), and the **report screen** is where they carry the most weight (ISS-U03/U05).

| Topic | Old citation | **2025 citation** | Where it appears |
|-------|--------------|-------------------|------------------|
| Reports | VPS 3 | **VPS 6** | report screen (ISS-U03) |
| Bases of Value | VPS 4 | **VPS 2** | basis-of-value disclosure |
| Approaches | (part of VPS 5) | **VPS 3** | methodology framing |
| Models | (part of VPS 5) | **VPS 5** | AVM/model disclosure |
| Material Uncertainty | VPGA 10 | **VPGA 10** | the MUC wrapper (§0.4) |
| IVS — Bases | IVS 104 | **IVS 104** *(bases of value)* | IVS alignment |
| IVS — Approaches/Methods | **IVS 105** | **IVS 103** | approaches/methods |
| IVS — Data / inputs | — | **IVS 106** *(data)* | data-input disclosure |

> **Note on scope:** the live copy frames these as the *standards the methodology is informed by*, **not** a claim of an accredited Red Book valuation. The `rics_compliant` label was re-scoped accordingly (a20, closed A7).


## Appendix H — Sprint / version timeline (selected)

> Live engine at the time of writing: **`3.1.0-sprint2.22.0b.11`** (engine tag `thammen-sprint2p22p0b11-cost-drc-reanchor`), **Heroku v180**, probed `/api/health` 2026-06-09 (Rule #58 — never pin from memory; this is the *measured* value this session). CHANGELOG files in the corpus span **v64–v94**.

| Phase | Sprints | Theme | Key outcomes (this log's cross-refs) |
|-------|---------|-------|--------------------------------------|
| Land arc | 2.18–2.20 | source tiers, land grid, parallelization | E8–E11 (tiers), E19 (parallelization ±2%), E20 (15K compound boundary), R10/R15 work |
| Input/PIN | 2.21.0.x | PIN input, asset-type reality-check | E13/E14, A5 origin (ISS-B01), staged-input groundwork |
| a-series | 2.22.0a.2 → a.25 | privacy, RICS, strata, latency | a14 (bracket honest-range; R2/R10), a16 (precapture hardening; A16 surfaces), a18/a23 (stock_strata; R15 closed), a20 (rics_compliant; A7 closed), **a24** (consent/Terms/DPIA/log-scrub), **a25** (CC BY 4.0) |
| B-1 | SprintB1 | land-floor / HBU decomposition | bidirectional condition **disclosure** (disclose-only) |
| b-series | b.2 → b.11 | owner journey + cost line | b.2.1 (separate screens), b.2.2 (evidence-quality panel), b.2.3 (confirmation gate), b.3 (polish), b4 (`luxury_new`, n=2), **b.11** (cost-reanchor down-half, n=2 — live) |
| **next** | — | per Part 5 | Step-1 decomposition coherence (**Gate-2 pending**) → A16/R9 root → §20.9 UP-lift → rent-as-UX |

## Appendix I — This log's changelog

| Version | Date | Author lane | Change |
|---------|------|-------------|--------|
| **v1.0** | 2026-06-09 | Claude.ai (analyst/verifier) | Initial ISSUES_LOG.md. Built on the 2026-06-09 signed governance-cleanup directive. Deep research = live `/api/health` probe + full read of the governance corpus (`/mnt/project/` mirror of `deploy v2/docs/`). Parts 0–7 with per-issue template; **47 issue entries** across accuracy (A01–A10), data (D01–D08), bugs (B01–B03), tech-debt (T01–T08), UX (U01–U05), regulatory (R01–R06), governance (G01–G07); **11 deferred/parked** items; the unified forward sequence; closed risks/bugs + **7 failed paths**; **12 appendices (A–L)**. |


---

## Appendix J — Risk → Issue traceability matrix

> Maps every `RISK_REGISTER.md` entry (R1–R15) to the issue(s) that carry it in this log, with the live status. This is the audit bridge between the *risk* register and the *issue* log.

| Risk | Title (short) | Status | Carried by (ISS) |
|------|---------------|--------|------------------|
| **R1** | Cross-chat state divergence | MITIGATED (#57) | ISS-T04, ISS-G06 |
| **R2** | A14 cold-503 | **CLOSED v146** | Part 6 §6.1 |
| **R3** | Memory-vs-disk drift | MITIGATED (#58) | ISS-T04, ISS-G06 |
| **R4** | MoJ stale | OPEN (external) | ISS-D01 |
| **R5** | QARS reachability | MITIGATED (v132 envelope-fallback) | ISS-T01 |
| **R6** | Version-pin tests | MITIGATED (recurs) | ISS-T06 |
| **R7** | Built-type + condition blindness (bidirectional) | **OPEN — master defect** | ISS-A01 (+ A03 root, A04/A10 fix, A05 income, A09 NLP, U02 UX, DEF-01) |
| **R8** | Pool purity + thin-window | PARKED (Phase-2) | ISS-A02, DEF-02 |
| **R9** | Bracket area-name under-match | **OPEN (promoted)** | ISS-A03 (= A16), ISS-B03 |
| **R10** | Bracket dispersion gate | **CLOSED a14** | Part 6, E23 |
| **R11** | Instrumentation dormant | OPEN (gated §8.1/§8.2) | ISS-R05, ISS-U04, DEF-03 |
| **R12** | Cloudflare-1010 blocks urllib | MITIGATED (#61) | ISS-T03 |
| **R13** | Regulatory self-clearance | OPEN (cover, pre-monetization) | ISS-R01, ISS-G03 |
| **R14** | Gate integrity ("verified=executed") | adopted control | ISS-T05 |
| **R15** | `stock_strata` a18 | **CLOSED a23** | Part 6 |

## Appendix K — Locked-decisions ledger

> Decisions that are **settled** and should not be re-litigated without new evidence (the positive complement to the failed-paths list). Re-opening any of these is itself an ISS-G07 signal (distinguish a *new fact* from re-arguing a closed conclusion).

| # | Locked decision | Basis | Where it binds |
|---|-----------------|-------|----------------|
| LD-1 | **Lean five-screen owner journey** | DESIGN_2p2x v4 | ISS-U01/U03 |
| LD-2 | **Number early, as a range that refines** (not a hidden end-reveal; not a symmetric ± wrapper) | §2b resolution | ISS-U01, FP-05 |
| LD-3 | **Condition = sensitivity only** (never a confidence lever) | §2c + B-1 disclose-don't-assume | ISS-U02, ISS-A10 |
| LD-4 | **MoJ is the sole valuation evidence source**; listings → sentiment only; buyer ceiling = MoJ × 1.10 | E1/E2/E12, +70.2% falsification | ISS-A*, FP-04, Appendix D |
| LD-5 | **MoJ self-calibration is BLOCKED** (PN-hash cryptographic + ethical) | E12, Rule #62 | ISS-A08, ISS-D02, FP-02 |
| LD-6 | **Mthamen CLOSED** — methodology-reference only; §20.9 replaces it | 2026-06-09 cleanup #3, E6 | ISS-G04, FP-01 |
| LD-7 | **Ship value-affecting methods disclosed-as-indicative**; n≥20 gates precision not shipping | 2026-06-09 cleanup #1, §0.4, b4/b11 n=2 | ISS-G02, all of Part 4/5 |
| LD-8 | **Beta is a non-blocking parallel track**; gate #6 deleted; R13 = cover not ritual | 2026-06-09 cleanup #5 | ISS-G03, ISS-R01, Part 5 §5.3 |
| LD-9 | **#65a is the single forward source**; §11 DEPRECATED | 2026-06-09 cleanup #6 | ISS-G01, Part 5 |
| LD-10 | **Apartments out of v1 scope** (villas + land); MME auth = future dependency | 2026-06-09 cleanup #2 | ISS-D05, DEF-04 |
| LD-11 | **A16/R9 sequenced before floor patches** (fix the source starve first) | 2026-06-09 cleanup #4 | ISS-A03, Part 5 Step 2 |
| LD-12 | **Cost calibration must NOT reproduce the MoJ median** (build pure DRC; observe Market/DRC by segment; no hard ceiling) | §20.9 discipline, FP-06 | ISS-A04, Step 3 |
| LD-13 | **Two-lane model; Anas is the sole router and sole gate authority**; git+docs = shared truth | ROLES_AND_COMMS | ISS-G06 |
| LD-14 | **Drama/authority attach to evidence quality, never to the headline figure**; explanation never raises confidence; authority rises only at the accountable (report) stage | §2c | ISS-U05, ISS-U03 |

## Appendix L — Consolidated decision register («القرار المطلوب»)

> Every decision callout in the log, in one place, **split by whether it actually asks Anas for something**. Most entries are "no action — recorded" (the decision is already made or the item is structural). The **open asks** are the short list that actually needs Anas. Ordered to match the forward sequence (Part 5).

### L.1 — OPEN asks (need Anas) — ordered by the forward sequence

| Priority | Decision | Issue | Lane note |
|----------|----------|-------|-----------|
| **1 (now)** | **Sign the decomposition-coherence brief** (Gate-2) so CC can proceed — the analyst is ready to take it to signature. *This audit does not replace it.* | ISS-A07 / Part 5 Step 1 | the single most time-sensitive item |
| **2** | After Step 1: **approve a live Marikh (54/541/6) trace → the A16/R9 brief**; confirm A16/R9 sits at sequence-position #2 (before the cost slice). | ISS-A03 / Step 2 | analyst lean: yes |
| **3** | **§20.9 gated slice:** (a) set the **dilapidated-luxury building-value-retention floor (~0.31)**; (b) approve the **system-age→actual-age + CGIS-gap recon**; (c) Open-decision-#4: name the **isolated curated GT source** for cost calibration. | ISS-A04 / Step 3 | ships disclosed-indicative |
| **4** | **B-2 Lever-2 (downward old-stock re-anchor): lift from PARKED to ship-disclosed-now** under §0.4? (Keep Lever-1 corpus-calibrated as GT grows.) | ISS-A10 / DEF-01 | analyst lean: yes for Lever-2 (data-ready) |
| **5** | **Rent-as-UX:** approve surfacing the rent field in the flow so `income_led` fires on real traffic. | ISS-A05 / Step 4 | analyst lean: fold Fork-C into the A16 sprint (same plumbing) |
| **6** | **GT-corpus posture:** confirm *manual + organic* growth as the standing unblock (replacing "dead source" framing); endorse **spot-check-now** + a commitment to **publish an error band before PUBLIC marketing**. | ISS-D07 / ISS-D08 | the calibration unblock for everything |
| **7 (parallel)** | **Fold A15 (HBU-drop) into the decomposition-coherence brief?** | ISS-B02 | analyst lean: yes (same surface) |
| **8 (pre-activation)** | **gate #11:** decide **database residency (§8.2 cross-border)** + **free-text handling (§8.1)**, then a **security pass** — to activate capture. *Not a beta blocker.* | ISS-R05 / ISS-R02 / ISS-R06 / ISS-U04 | reserved to Anas |
| **9 (pre-monetization)** | **Aqarat enquiry timing** (held draft): send **after** design/build is complete and **before** monetization — *not* before invites; include an **AVM-category** clarification. | ISS-R01 / ISS-R04 | reserved to Anas |
| **10 (design)** | **Screen-3 condition readout form:** a breathing ±-sensitivity band, or a discrete better/worse indicative toggle? | ISS-U02 | reserved to Anas (UX surface) |

### L.2 — Recorded / no-action (the decision is already made or the item is structural)

> Listed for completeness; each is "None / recorded" in its issue: **ISS-A01** (direction signed; B-2 Gate-2 signed 2026-06-05), **ISS-A02** (Phase-2 *after* — dispersion gate covers the danger), **ISS-A06** (accept the borrowing residual — already live), **ISS-A08** (E12 settled), **ISS-A09** (future idea), **ISS-D01** (accept-and-disclose; harder at PUBLIC), **ISS-D02/D03/D04** (structural / handled by A16+Fork-C), **ISS-D05** (apartments out-of-scope; refusal correct), **ISS-D06** (ship-with-MUC, recalibrate), **ISS-B01** (schedule when convenient), **ISS-T01–T08** (monitor / keep the existing discipline), **ISS-U01/U03** (screens reserved behind Step 1 by design), **ISS-U05** (executional principle), **ISS-R03** (continuous copy discipline), **ISS-G01–G07** (cleanup items — signed / doc-only).

### L.3 — Standing reminder

> **The decomposition-coherence brief (L.1 item 1) is the one live signature.** The 2026-06-09 governance cleanup was doc-only and **did not** replace it. Everything in §5.2 Steps 2–4 is *downstream* of it.


---

# CLOSING — provenance, limits, and the one open signature

**What this document is.** An independent **issues log / audit** of the Thammen AVM as of **2026-06-09**, authored in the **Claude.ai analyst-verifier lane**. Every "measured ✓" item is grounded in *this session's* evidence: a live `/api/health` probe and a full read of the governance corpus. Every "assumed ~" item is flagged as such. Where this log and a source file disagree, **the source file wins** — and that disagreement is itself a drift signal to fix (ISS-G01).

**What it deliberately does not do.** It does not author code, open a new Gate-2, or delete any measured fact. It honours the **surgical rule** of the cleanup it builds on: *preserve the measured facts; revise only the conclusions built on them* (ISS-G07). The closed feeds, the not-geocoded MoJ, and the PN-hash closure remain **true** throughout; what this log carries forward is the **ship-disclosed** conclusion (§0.4 / ISS-G02), not the old "blocked / no source" framing.

**Three things to hold onto.**
1. **The master accuracy defect is R7** (bidirectional built-type/condition blindness — ISS-A01): under-anchors new/premium ~−37/−40% (V002/V003), over-anchors old stock. Its root-cause neighbour **A16/R9** (ISS-A03) is sequenced **before** floor patches.
2. **Shipping is not gated on n≥20** — n≥20 gates *precision*. Value-affecting methods ship **disclosed-as-indicative** and tighten as GT grows manually + organically (the b4/b11 n=2 precedent).
3. **The beta is a parallel, non-blocking track** — no cohort (gate #6 deleted), R13 as *cover* not ritual; the Aqarat licence is a **pre-monetization** gate, not a pre-beta one.

**The one open signature.** Per Part 5 Step 1, the **decomposition-coherence brief still awaits Anas's Gate-2 signature**. This audit does **not** replace it; it sits *upstream* of the polished-result and report screens (ISS-U03) and is the first move in the forward sequence.

**Canonicalisation (Rule #63).** This document is authored in the analyst lane; to become the repo's source of truth it should be **saved to `deploy v2/docs/ISSUES_LOG.md` and committed by CC**, routed by Anas — delivered *with* that instruction, not left only in chat. Git + docs remain the shared truth across the two lanes (ISS-G06).

*— End of ISSUES_LOG.md —*