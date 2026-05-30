# CHANGELOG v60 — Sprint 2.22.0a.8 · RICS / IVS Citation Correctness (2025 edition)

> **Engine:** `thammen-sprint2p22p0a8-rics-citation-2025` · **api/health:** `3.1.0-sprint2.22.0a.8`
> **Date:** 2026-05-30 · **Prior:** v59 (Sprint 2.22.0a.7, A14 closed, Heroku v146)
> **Type:** methodology + user-facing copy + comments — **entire sprint under 🔴 Hard Gate 2.**
> **Brief:** `BRIEF_2p22p0a8_rics_citation_2025.md` + `BRIEF_2p22p0a8_SIGNED_DECISIONS.md` (Anas-signed D1–D5).
> **Files:** `evaluate_unified.py`, `evaluate_v3.py`, `comparable_adjustments.py`,
> `hybrid_valuation.py`, `geometric_factors.py`, `scope_of_service.py`,
> `connectors/propertyfinder_apartments_t2_sales.py`, `index.html`,
> `test_sprint_2p22p0a8_rics_citation.py` (new).

-----

## 1. Why this matters (user-visible)

Two correctness gaps in how Thammen represents its RICS/IVS posture — the core value
proposition of an *auditable* AVM:

1. **The standard that governs AVMs was never cited.** The 2025 edition introduces a
   dedicated **valuation models** standard — **RICS VPS 5 / IVS 105** — which states in
   substance that *"no model without the valuer applying professional judgement, for
   example an automated valuation model (AVM), can produce an IVS-compliant valuation."*
   Thammen *is* an AVM; this is the regulatory bedrock of its staged lifecycle (Stage 5 =
   licensed-valuer sign-off). The citation chain (`VPGA 10 + VPS 6 + IVS 106`) omitted it.

2. **`VPS 4` was used as a method label — a mislabel.** Across the engine, the Sales
   Comparison approach / comparable adjustments / HBU were tagged `RICS VPS 4`. That is
   wrong under the 2025 edition (VPS 4 = *Inspections, investigations & records*) **and was
   already wrong under 2022** (approaches were VPS 5, never VPS 4). So this is a
   **pre-existing mislabel**, *not* edition drift (Decision D1).

## 2. Root cause

- **Pre-existing mislabel.** Method/approach content was tagged `VPS 4`. Approaches were
  **VPS 5 (2022) → VPS 3 (2025)**; they were never VPS 4 in any edition. Recon confirmed
  every live `VPS 4` site tagged an *approach/HBU/scope*, not "bases of value".
- **Models standard absent.** VPS 5 / IVS 105 (new in 2025) was simply not represented.
- **The "VPS 3" trap (context).** A single-AI pass had once cited `VPS 3` for *reports* —
  correct under 2022, wrong under 2025 (reports moved to **VPS 6 / IVS 106**). The existing
  `VPGA 10 + VPS 6 + IVS 106` chain was already correct; this sprint did not touch it.
- **Long-deferred "VPS 3 vs VPS 6" item — now CLOSED.** The 2.22.0a.4-era deferred question
  (a prior GPT-5 + Gemini pass had cited VPS 3 for reports) is resolved by this sprint's full
  VPS 1–6 verification: **reports = VPS 6 / IVS 106**, **approaches = VPS 3 / IVS 103** (both
  2025). No open VPS-numbering question remains.

**Numbering verified ✓** against IVSC + RICS primaries (both lanes, independently):

| 2025 | Title | was (2022) | | IVS 2025 | Title |
|---|---|---|---|---|---|
| VPS 1 | Terms of engagement / scope | VPS 1 | | IVS 102 | Bases of Value |
| VPS 2 | Bases of value | VPS 4 | | IVS 103 | Valuation Approaches |
| VPS 3 | **Approaches & methods** | VPS 5 | | IVS 104 | Data & Inputs (new) |
| VPS 4 | Inspections / records | VPS 2 | | **IVS 105** | **Valuation Models (new)** |
| **VPS 5** | **Valuation models (new)** | — | | IVS 106 | Documentation & Reporting |
| VPS 6 | Valuation reports | VPS 3 | | | |

## 3. What this patch does

### 3.1 Adds the models standard (item 1) — a NEW secondary surface
- New root fields `rics_methodology_note_ar` / `_en` in `_build_unified_output`
  (`evaluate_unified.py`), citing approach (**VPS 3 / IVS 103**) + the new models standard
  (**VPS 5 / IVS 105**) + MUC (**VPGA 10**) + report (**VPS 6 / IVS 106**), and the IVS 105
  AVM-not-standalone disclosure ("النموذج الآلي أداة مساعدة … دون مراجعة مُقيِّم مُرخّص (المرحلة الخامسة)").
- New **collapsible `<details>`** block in `index.html` renders it on a quiet secondary
  surface. **The 2.22.0a.4 universal bare `methodology_ar` line is untouched** (headline
  stays bare; "reduce, not add").
- This doubles as the **A7 disclosure** (why `rics_compliant=false` pre-inspection — see §3.4).

### 3.2 Remaps every stale citation to the 2025 edition (D2 + D5 — ALL labels)

| File · site | Tags | Before → After | Surface |
|---|---|---|---|
| `evaluate_unified.py:8/10` | approach | `RICS VPS 4` / `VPS 4 §7` → `RICS VPS 3` | docstring |
| `evaluate_unified.py:20` | approach | `per IVS 105` → `per IVS 103 — Valuation Approaches` | docstring |
| `evaluate_unified.py:354` | reliability | `VPS 4 reliability tiers` → `VPS 3` | comment |
| `evaluate_unified.py:957/961` | approach | `RICS VPS 4 [§7]` → `RICS VPS 3` | docstring |
| `evaluate_unified.py:979/991/1004` | approach | `(RICS VPS 4 [§7])` → `(‎RICS VPS 3 / IVS 103‎)` | **user-facing** `method_label_ar` |
| `evaluate_unified.py:1770/4663` | scope | `RICS VPS 2 scope` → `RICS VPS 1 …` | docstring/comment |
| `evaluate_unified.py:4437` | HBU | `RICS VPS 4 §3.4 — Highest and Best Use` → `RICS VPS 2 / IVS 102 — Highest and Best Use` | **user-facing** `rics_reference` |
| `evaluate_unified.py:4532` | approach | `RICS VPS 4 §7` → `‎RICS VPS 3 / IVS 103‎` | **user-facing** factor |
| `evaluate_unified.py:4547` | MUC | `RICS VPN 13` → `RICS VPGA 10` (typo) | comment |
| `evaluate_v3.py:7` | approach | `RICS VPS 4 §7` → `RICS VPS 3` | docstring |
| `comparable_adjustments.py:5` | approach | `RICS Red Book VPS 4 §7` → `RICS Red Book (effective 31 January 2025) VPS 3` | docstring |
| `hybrid_valuation.py:20` | approach | `RICS VPS 4` → `RICS VPS 3` | docstring |
| `geometric_factors.py:449` | HBU | `(RICS HBU — VPS 4 §3.4)` → `(‎RICS HBU — VPS 2 / IVS 102‎)` | **user-facing** |
| `scope_of_service.py:5/8` | scope | `RICS VPS 2` → `RICS VPS 1 (Terms of engagement / scope of work)` | docstring |
| `scope_of_service.py:72/76/83` | approach | `VPS 4 methodology` → `VPS 3 methodology` | comment + **user-facing** `SERVICE_LEVEL_AR/EN` |
| `connectors/propertyfinder_apartments_t2_sales.py:8` | approach | `RICS VPS 4 like-for-like` → `RICS VPS 3` | docstring |
| `index.html:273` | scope | `RICS VPS 2 Scope link` → `RICS VPS 1 Scope link` | comment |
| `index.html:1066` | HBU | `RICS VPS 4 §3.4` → `&lrm;RICS VPS 2 / IVS 102&lrm;` | **user-facing** HBU render |

**Sub-clause numbers (`§7`, `§3.4`) were DROPPED**, not re-pointed: they were unverified and
attached to the wrong (VPS 4) standard. Citing at the standard level (genus) is the honest
choice and matches D3's genus-fallback philosophy. *(Section-level citation is a future
copy-standard pass if ever wanted.)*

### 3.3 Edition label + RTL
- `RICS Red Book Global Standards 2024` (comment) → `(effective 31 January 2025)`.
- Every Latin standard code newly placed in **Arabic** copy is **LRM-wrapped** (`U+200E`)
  to prevent bidi reversal (Operational_Rules #25); the index.html summary uses `&lrm;`.

### 3.4 A7 (`rics_compliant` always false) — closed as not-a-bug (D4)
- Recon: `material_uncertainty.py:382` gates `rics_compliant` on `has_field_inspection`,
  which an AVM never has → `False` pre-inspection. Cross-referenced to the now-verified
  **IVS 105** principle, `False` for a standalone AVM is **correct by design**. **Flag logic
  unchanged.** The "why" is now disclosed in the new methodology note (§3.1).
- **Deferred (Rule #42 + #47):** rename/clarify the `rics_compliant` field so a consumer
  reads `false` as *"pending Stage-5 inspection"* not *"violates RICS"*. Its own later pass.

## 4. Verification — empirical evidence

- **py_compile:** all 7 modified Python files compile (`COMPILE_OK`).
- **Citation sweep:** `VPS 4` = **0 occurrences** across all live production files
  (remaining matches are backups, the `.live_index.html` probe snapshot, and a4's
  intentional *absence* assertions).
- **Isolated test** `test_sprint_2p22p0a8_rics_citation.py`: **43/43 PASS** — incl. a
  runtime exercise (`_build_unified_output` really returns the note; `methodology_ar` is
  still the bare line) per Rule #40 / E14.
- **Regression (DoD matrix):** aggregator **392/392** · security **15/15** · surface-honesty
  **45/45** · broad **51/51 files** (was 50 + this sprint's new test). **No valuation-number
  change** on any path (citation copy + comments only).
- **node --check:** node not installed locally (known — Session_Log §11.3); inline JS
  brace/paren balance verified by proxy; **desktop + mobile 390×844 render is the Gate-2
  browser step** (below).

## 5. Deployment (after Gate-2 string sign-off + Gate-1 "go")

```
cd /d "C:\Thammen\deploy v2"
git add evaluate_unified.py evaluate_v3.py comparable_adjustments.py hybrid_valuation.py geometric_factors.py scope_of_service.py connectors\propertyfinder_apartments_t2_sales.py index.html test_sprint_2p22p0a8_rics_citation.py CHANGELOG_v60.md
git commit -m "Sprint 2.22.0a.8: RICS/IVS 2025 citation correctness — add VPS 5/IVS 105 models standard, remap stale VPS 4/VPS 2 labels"
git subtree split --prefix "deploy v2" -b heroku-deploy-tmp
git push heroku heroku-deploy-tmp:master --force
git branch -D heroku-deploy-tmp
git push origin master
```

## 6. Verification curl (post-deploy)

```
curl -s https://thammen.qa/api/health
:: expect "engine_version":"thammen-sprint2p22p0a8-rics-citation-2025"

curl -s -X POST https://thammen.qa/api/evaluate -H "Content-Type: application/json" -d "{\"zone\":56,\"street\":565,\"building\":21}" > out.json
findstr /C:"rics_methodology_note_ar" out.json
findstr /C:"VPS 5" out.json
```

Post-deploy smoke (desktop + **mobile 390×844**): `52/903/90` (apt), `56/565/21` (villa),
`69/255/75` (hybrid) — citation strings render, LRM holds, **valuations unchanged vs v146**.

## 7. What's NOT in this patch (scope boundary)

- No valuation logic / tiering / MUC-magnitude / refusal changes; no schema removal (additive).
- **`rics_compliant` flag logic unchanged**; its field-rename is **deferred** (§3.4).
- The new note is added to the **main valuation output path** (`_build_unified_output`);
  refusal paths keep their own scope messaging — replicating the note there is a follow-up.
- Sub-clause (`§x.y`) citations dropped, not re-derived (genus-level only).
- Latin in non-citation methodology strings (GIS / MoJ / Cap Rate names) — separate
  copy-standard pass (already deferred).
- **HBU → VPS 2 / IVS 102 — RESOLVED (D3 closed).** Genus-level (no RICS sub-paragraph
  claim), **triple-confirmed**: Claude.ai primary-source (IVS 2025 → **IVS 102, Appendix
  A90**) + GPT-5 + Gemini all converged. All three flagged that the exact *RICS* paragraph
  is uncertain because the Red Book cross-references IVS — hence the genus-level citation,
  no sub-paragraph. The applied labels (`RICS VPS 2 / IVS 102 — Highest and Best Use`) are
  correct as shipped.
