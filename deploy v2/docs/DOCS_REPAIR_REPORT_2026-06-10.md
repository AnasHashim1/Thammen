# DOCS REPAIR REPORT — 2026-06-10 (corpus-wide, docs-only)

> **Scope:** repair stale claims across the documentation corpus against the b13/v182 ground truth.
> **Type:** docs-only — **zero engine/frontend diffs · no Heroku release · `master == origin`.**
> **Owner:** Anas · **Lane:** CC. Pairs with `RISK_SUMMARY.md` (living) + Session_Log §20.45–§20.47 + `ISSUES_LOG.md` ISS-G03.

## 0 — Ground-truth handshake (#57, verified before editing)

| Check | Value |
|---|---|
| `/api/health` | `3.1.0-sprint2.22.0b.13` · engine `thammen-sprint2p22p0b13-cost-trim-convergent` · MoJ **161d** · qars healthy · reliable 6 |
| git HEAD (pre-repair) | `a24a83c` · branch `master` · `master == origin/master` (0/0) |
| Live truth applied | b11 (cost down-reanchor) · b12 (A15 HBU disclosure) · b13 (Lever-1 convergent-TRIM, user-age-gated, V001+25y→3.6M; D-1 0.31 ✅) · **Lever-2 UP-lift FALSIFIED → B-2** (E25) · CLOSED: R9/A16 (a18), A15 (b12) · open Medium = **A5 only** · **gate #6 DELETED** (ISS-G03) · binding decision = **D-3** (GT collection) |

## 1 — Classification table (file · hits · disposition · why)

### FIXED in place (live-layer)

| File | Stale hits | Disposition | Why |
|---|---|---|---|
| **CLAUDE.md** | (1) line-6 "Last update 2026-06-01 / a16" + trailing "§20.15"; (2) line-19 "Most recent state … §20.15 — current = a15/v154"; (3) line-57 "Engineering = ACTIVE … last shipped **b10**" (contradicts the line-54 Live=b13 bullet); (4) the historical snapshot code-block (118+, pinned a16/v155) | **FIXED (4 minimal-prefix edits + 1 banner)** | Lines 6/19/57 are *live* pointers that directly contradicted the already-correct line-54 «🧭 Live» bullet → re-pointed to b13/v182 + §20.45–47. The snapshot body (118+) and the b10→a19 cascade in line 57 are **frozen history** → ONE banner + a "_Frozen cascade_" flag instead of line-rewriting (rule b/d). |
| **docs/Project_Instructions.md** | §11 forward-block tail: "NEXT engineering = the §20.9 GATED slice [convergent-confirm + the **UP-lift**]"; "beta go-call [**gate #6**, Anas]"; "Ball = … beta go-call, gate #6"; priority-queue **row 6** "Cost-triangulation … POST-2.22.0b; BLOCKED" | **FIXED (2 edits)** | GATED slice ✅ SHIPPED b13; UP-lift DROPPED→B-2/E25; b12+b13 added to the shipped cascade; gate#6→**D-3** (ISS-G03, beta=parallel non-blocking track); row 6 → §20.9 partly-shipped (b11+b13). §18 bug table + "Open mediums = A5 only" were **already correct** (b12/PRE-STEP edits landed) → verified, left. |
| **docs/Custom_Instructions.md** | «تذكر الوضع الرشيق» recall: head "last shipped **b10/v180**"; tail "NEXT = the §20.9 GATED slice [… UP-lift …]"; "beta go-call [**gate #6**]"; "Ball = … beta go-call, gate #6" | **FIXED (2 edits — head + tail)** | Head → b13/v182 (+ b12 prior, b11 demoted to Prior); tail → §6 v2 / B-2 (under-anchor) / GT-collection (D-3); gate#6 deleted. The **frozen "Prior bN" cascade** between head and tail left intact (rule d). |
| **docs/LAUNCH_READINESS_GATES_v1.md** | gate 9 "A7 + open mediums (A5, **A15**)"; gate 6 "Condition model … designed, not built"; §0/line-17 "small invited cohort"; gate-4 framing | **FIXED (1 banner + 2 cell edits)** | ISS-G03 reconciliation banner (the #65a «gate #6 = beta cohort» is DELETED — *distinct* from this register's gate 6 = Condition model; R13 cover preserved; gate-4 reframe). gate 9 → A5 only (A7 ✅ a20, A15 ✅ b12); gate 6 → over-anchor half SHIPPED (b6→b11→b13), B-2 under-anchor half PARKED n≥20. "renumber nothing — strike + pointer" honored. |
| **docs/BETA_LAUNCH_PLAN_v1.md** | entire cohort-gated thesis (§0 "Cohort: small, invited"; §1 #6 "Cohort + access setup"; §3/§4 "the main thing gating beta-live"); §1 #3 "A7 fix … open bug" | **ANNOTATED (superseded-in-part banner)** | A v1-draft whose core thesis (cohort-gated beta) is wrong post-ISS-G03 → one prominent superseded banner (cohort framing OUT OF DATE; binding decision = **D-3**; A7 closed; kept for its gate-by-gate beta detail) rather than rewriting the draft. Pointer to ISS-G03 + RISK_SUMMARY. |
| **docs/RISK_REGISTER.md** (canonical ledger) | **R7** status cell ended at "the staged flow supplies it" (no shipped status); **R8** | **FIXED (R7 append) · R8 verified-left** | R7 += over-anchor half TREATED (b11 floor 1.9M→2.4M + b13 trim V001+25y→3.6M; D-1 0.31); under-anchor half → B-2 PARKED n≥20 (Lever-2 FALSIFIED, **E25**: premium-above-cost, not cost-reachable; needs `luxury_new` stratum). R8 has no "after A16" sequencing → left. |
| **docs/METHODOLOGY_DRC_qatar_v1.md** | §11 "🟡 GATE-TO-NEXT = convergent-confirm + the **up-lift**"; §11 closing "the UP-lift remain GATED-to-next" | **ANNOTATED (1-line superseded pointer above §11 SPLIT)** | The b11/b13 design source (frozen). The up-lift forward-claim is now FALSIFIED (E25) + the trim shipped (b13) + D-1 0.31 ✅ → one "superseded-by → §20.47 / E25" pointer above the SPLIT body (rule b), body left intact. |

### LEFT (frozen artifacts / correct-current / verified-no-contradiction)

| File | Hits | Disposition | Why |
|---|---|---|---|
| **docs/RISK_SUMMARY.md** | gate#6/GATED/Lever-2/D-1/D-3 | **LEFT — verified consistent** | Living layer, already maintained 2026-06-10 for b13 (§3: D-1 ✅; D-3 «لا بوّابة كوهورت — ISS-G03» as the binding decision; R7 row states the Lever-2/E25 falsification). No contradiction with the ground truth (esp. §3). |
| **docs/ISSUES_LOG.md** | gate#6 ×N, "live Marikh trace", GATED slice | **LEFT — frozen snapshot + the CORRECTION authority** | Banner-tagged "⚠️ point-in-time SNAPSHOT (2026-06-09)… NOT line-maintained". ISS-G03 *is* the authority that documents the gate #6 deletion + the "after-A16/live-Marikh-trace" removal. Editing it would corrupt the authority. |
| **docs/RISK_REGISTER_v2.md** | gate#6, cohort, "live Marikh trace" (D-4 errata) | **LEFT — frozen snapshot** | Banner-tagged "⚠️ point-in-time SNAPSHOT (2026-06-09, post-errata)". Already carries the D-4 errata + ISS-G03 references; internal R-F2 cohort-lever line is snapshot content. |
| **docs/Session_Log.md** | §20.13/§20.14 carried-forward "A16 = only Marikh lever (R9, own sprint after a live trace)" (2067/2126/4172) | **LEFT — frozen entries** | Session_Log entries are point-in-time records (rule b/d). The correction is recorded forward (a18 errata, ISS-G03); the old carried-forward notes were true at their date. |
| **docs/Empirical_Findings.md** | E24, E25, "GATED slice", "Lever 2" | **LEFT — correct-current** | E24 (system age = FLOOR) + E25 (premium-above-cost → under-anchor not cost-reachable) present and correctly cross-ref R7/R19/§20.27/§20.47. |
| **docs/DESIGN_2p2x_v4_owner_journey.md** | "decomposition", "B-2 مركونة n≥20" | **LEFT — correct-current** | "تفكيك" = the *analytical, not-verified, doesn't-raise-confidence* decomposition (the b2.2 lesson); B-2 parked n≥20. UX design unaffected by b13. |
| **docs/ROLES_AND_COMMS.md** | — | **LEFT — clean** | Stable conduct doc; no stale forward-tokens. |
| **docs/Operational_Rules.md** | — | **LEFT — clean** | Version-agnostic rules; no GATED/gate#6/last-shipped forward-claims. |
| **docs/METHODOLOGY_cost_triangulation_v1.md** | line-76 "مريخ alias A16" | **LEFT — frozen recon, harmless** | A "CC must re-run" recon caveat; A16 is CLOSED (a18) so the named normalization now exists → the caveat is moot, not dangerous. |
| **CHANGELOG_v94/95/96/85/…**, **BRIEF_\***, **PHASE0_\***, **PHASE1_\***, **MULTI_AI_\***, **DPIA / COMPLIANCE_SELF_CLEARANCE / Aqarat / 2p22p0_pre/** | gate#6, GATED slice, cohort, A16, Lever 2, "live Marikh trace" | **LEFT — frozen by definition** | CHANGELOGs / signed briefs / recon / pre-sprint logs are point-in-time artifacts; their framing was correct at authoring. Compliance docs' "cohort" refs concern privacy/activation triggers, not the deleted gate #6. |

## 2 — Sweep-token coverage (each token classified)

| Token | Where it lived | Action |
|---|---|---|
| `gate #6` / `beta go-call` / `كوهورت`/cohort | CLAUDE, PI, CI (live heads) → **fixed**; LAUNCH_GATES/BETA_PLAN → **banner**; ISSUES_LOG/RISK_REGISTER_v2/PHASE0/Session_Log/CHANGELOG → **frozen-left** | gate #6 = DELETED (ISS-G03); binding = D-3. All live refs now deletion/frozen-flagged. |
| `§20.9 GATED slice` / `GATED slice` / `Lever 2` / `UP-lift` | CLAUDE/PI/CI live tails → **fixed** (shipped b13 / UP-lift DROPPED, E25); METHODOLOGY_DRC §11 → **pointer**; Empirical E25 / RISK_SUMMARY → **correct-left**; CHANGELOG/PHASE0/BRIEF → **frozen-left** | GATED Lever-1 SHIPPED b13; Lever-2 falsified → B-2. |
| `A16` / `R9` / `live Marikh trace` | RISK_REGISTER R9 = ✅ CLOSED a18 (left); CLAUDE old-snapshot + Session_Log carried-forward = **frozen** (banner/left); ISSUES_LOG/RISK_REGISTER_v2 = the correction authority (left) | R9/A16 CLOSED a18; "live Marikh trace" step removed (already corrected at the authority layer). |
| `A15` / `Medium 3` / `open mediums` | PI §18 + "Open mediums = A5 only" already correct (verified-left); LAUNCH_GATES gate 9 → **fixed** | A15 ✅ CLOSED b12; open Medium = **A5 only**. |
| `D-1` / `0.27` / `n=2` | D-1 0.31 ✅ shipped (folded into edits); 0.27 = the *ordinary/default* floor (correct, byte-identical); n=2 = disclosed-as-indicative (correct) | No standalone fixes — all correct or folded. |
| `decomposition` / `bracket_n~1` / `exact-match` (area names) | DESIGN_2p2x_v4 "تفكيك" = correct analytical framing (left); `bracket_n~1` + "matches EXACTLY" = the R9 CLOSED *bug description* (left, correctly framed) | No stale forward-claims. |

## 3 — Commit list

| # | Commit | Files | Group |
|---|---|---|---|
| 1/3 | `241958a` | CLAUDE.md · Project_Instructions.md · Custom_Instructions.md | governance / lean-posture |
| 2/3 | `8fe0830` | LAUNCH_READINESS_GATES_v1.md · BETA_LAUNCH_PLAN_v1.md | launch / beta (ISS-G03) |
| 3/3 | `9dc6d57` | RISK_REGISTER.md · METHODOLOGY_DRC_qatar_v1.md | canonical ledger + DRC methodology |
| report | _(this commit)_ | DOCS_REPAIR_REPORT_2026-06-10.md | deliverable |

## 4 — DoD

- ✅ **Zero engine/frontend diffs** — `git diff --name-only` = 7 `.md` files only (CLAUDE.md + 6 docs); no `.py` / `index.html`.
- ✅ **No Heroku release** — docs-only; engine stays b13/v182.
- ✅ **`master == origin`** after the origin push.
- ✅ **Frozen artifacts preserved** — banner-tagged snapshots (ISSUES_LOG, RISK_REGISTER_v2), Session_Log entries, CHANGELOGs, briefs, PHASE0 recon = untouched; the two methodology/launch annotations are pointers/banners above frozen bodies, no history rewritten.
- ✅ **Counts derived from name-lists** (#58) — "Open mediums = A5 only" stands on the A15/A16-CLOSED list, not a free-standing number.

### Untracked scratch left in place (NOT committed)
`docs/RISK_REGISTER_R16_R22_rows.md` (already merged into RISK_REGISTER.md R16–R22), `docs/thammen_owner_flow_mockup.html`, `.b13_*.py` / `.b1*_*.py` / other dotfile recon scratch, and the parent-dir WhatsApp/villa-6 artifacts — all untracked, out of scope, left as-is.

---
*Docs-only repair. CC. Forward state = `RISK_SUMMARY.md` + Session_Log §20.45–§20.47; this report is itself a point-in-time snapshot of the 2026-06-10 repair pass.*
