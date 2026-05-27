# Sprint 2.22.0a.2 — Gate 3 report (Anas's visual review)

**Heroku release:** v135 (post Gate-2 hotfix)
**Engine version live:** `thammen-sprint2p22p0a2-arabic-surface-content-fixes`
**Date:** 2026-05-27
**Gate 2 smoke:** **5/5 anchors PASS** (re-run on v135)
**Heroku 5xx in last 100 logs:** 0
**Status:** Ready for Anas's visual verification

---

## Release history (this Sprint)

```
v132  Sprint 2.22.0a.1 (QARS envelope fallback) — baseline before this Sprint
v133  (deploy artifact between Sprints — config tweak, no engine change)
v134  Sprint 2.22.0a.2 INITIAL PUSH (commit bfc803d)
        Gate 2 smoke caught 2 misses → committed hotfix locally
v135  Sprint 2.22.0a.2 HOTFIX (commit 46b6a27) ← current
```

---

## Gate 2 smoke matrix (v135 — post-hotfix)

| Anchor       | asset_type        | refusal_trigger        | All checks |
|--------------|-------------------|------------------------|:----------:|
| 52/903/90    | apartment_building | comp_density_sparse    | ✓ PASS     |
| 56/565/21    | standalone_villa   | (none — full brief)    | ✓ PASS     |
| 69/255/75    | apartment_building | comp_density_sparse    | ✓ PASS     |
| 70/300/25    | unknown            | **classifier_failure** | ✓ PASS     |
| 51/835/17    | compound_large     | asset_scale_extreme    | ✓ PASS     |

### Pattern-by-pattern verification

| Pattern | Live behavior | Anchor evidence |
|---------|---------------|-----------------|
| **A** LRM bidi  | MUC banner Latin tokens wrapped | 56/565/21 muc_clause_ar |
| **B** classifier_failure | 70/300/25 routes correctly (was comp_density_sparse pre-Sprint) | 70/300/25 trigger_id=classifier_failure |
| **C1** geopolitical neutral | No war/Hormuz/displacement/collapse strings in any anchor | 4/4 anchors clean |
| **C2** internal-doc + stratification | No "Sprint 2.16.0" / "Project Instructions §3" / "الـ stratification" / "median المدمج" in user-visible output | 56/565/21 stock_strata block clean |
| **C3** شواهد taxonomy | reliable→شواهد كافية, indicative→شواهد محدودة renders on full brief | 56/565/21 (positive substring confirmed) |
| **C4** descriptive disclaimer | "ولا يُعتبر تقرير تثمين رسمي صادر عن مثمّن مرخّص" renders, old forms absent | 56/565/21 + 51/835/17 disclaimers clean |
| **C5** DELETE negotiation | 'negotiation' NOT in any brief.sections[].id; "لا تدفع أكثر..." gone | All anchors: section_ids do not contain 'negotiation' |
| **§9** precision | "قريبة في النوع والمساحة" renders, "مشابهة بنفس الحجم"/"الصفقات المشابهة" gone | 56/565/21 accuracy.explanation_ar |

---

## What Anas should visually check

Open https://thammen.qa on **a mobile device (390×844 viewport ideal)** and submit
each of these 5 anchors in sequence:

### 1. **56/565/21** (Bou Hamour villa — most visual surface)
Verify on the rendered brief:
- [ ] Header `⚠️ تحفظ مادي وفق RICS Red Book Global Standards (effective 31 January 2025)...`
      renders with Latin tokens **in correct left-to-right order** (Pattern A LRM working).
- [ ] In the MUC body, the cause-of-uncertainty paragraph reads
      `قيوداً جوهرية على شواهد السوق المتاحة، في ظل فجوة طويلة في تحديث بيانات وزارة العدل...`
      (C1 neutral — NO war / Hormuz / displacement).
- [ ] In the stock_strata section: badges read `شواهد كافية (n≥10)` / `شواهد محدودة (n=N)` (C3).
- [ ] In the stock_strata methodology: text reads `التصنيف بحسب الفئات في الأسفل شفافية إضافية` (C2 hotfix — NO `الـ stratification`).
- [ ] The accuracy section reads `🟢 شواهد كافية` for n≥20 cases (C3), explanation reads
      `...لعقارات قريبة في النوع والمساحة ضمن نفس المنطقة` (§9 precision).
- [ ] The disclaimer reads `ولا يُعتبر تقرير تثمين رسمي صادر عن مثمّن مرخّص وفق معايير RICS/IVS` (C4).
- [ ] **NO negotiation section** ("نطاق التفاوض المقترح" card should be absent) (C5).
- [ ] No `Sprint 2.16.0`, no `Project Instructions §3`, no `لا تدفع` imperatives anywhere visible.

### 2. **70/300/25** (asset_type=unknown — the Pattern B fix)
- [ ] Refusal message reads `لم نتمكّن من تحديد نوع العقار من البيانات الحكومية المتاحة. قد يكون العنوان غير مفهرس حالياً في قاعدة QARS...`
- [ ] Recommendation reads `تحقّق من بيانات العنوان أو تواصل معنا.`
- [ ] **NOT** the old `هذه المنطقة فيها أقل من 5 صفقات بيع مقارنة...` (which would be a Pattern B regression).

### 3. **51/835/17** (compound_large >= 15K — E20 boundary)
- [ ] Refusal message reads `حجم عقارك يتجاوز أي صفقة مقارنة في قاعدة بياناتنا...`
- [ ] Disclaimer = new descriptive-provenance form (C4 — same hotfix as 56/565/21).

### 4. **52/903/90** + **69/255/75** (apartment_building, sparse-data refusal)
- [ ] Refusal message reads the standard `هذه المنطقة فيها أقل من 5 صفقات بيع مقارنة...` (NOT classifier_failure — those are correct routes here).
- [ ] Disclaimer = new descriptive form.

### Cross-cutting bidi check (any anchor)
- [ ] At mobile width 390px, the MUC banner Latin tokens (`RICS`, `VPGA 10`, `VPS 6`, `IVS 106`,
      `effective 31 January 2025`) render **in original left-to-right order** inside the
      surrounding RTL Arabic text. If you see reversed digits or scrambled `61 SPV` etc.,
      Pattern A regressed.

---

## Rollback if needed

If Anas's visual review finds a regression:

```
heroku rollback v132    # back to Sprint 2.22.0a.1 (pre-Sprint 2.22.0a.2 baseline)
```

Or `heroku rollback v134` to go back to the initial 2.22.0a.2 push (before the
Gate 2 hotfix, if only the hotfix change is problematic).

---

## What's NOT verified in Gate 2 (Anas's job)

- **Mobile viewport 390×844 visual rendering** — programmatic smoke can confirm
  the strings are present but NOT that bidi rendering is correct on a real
  browser. This is the only Gate 1 checklist item left.
- **Methodology-level user comprehension** — whether the new C3 شواهد taxonomy
  is intuitive for non-expert Arabic readers. Multi-AI approved the wording,
  but real-user feedback is the test that matters.

---

## What's queued next (post-Anas-approval)

If Gate 3 passes:
- Session_Log.md gets a §17 entry for Sprint 2.22.0a.2 (next session task).
- Strategic items deferred to 2.23.x design Sprint per
  `docs/DESIGN_2p23_VALIDATOR_FEEDBACK.md`.

If Gate 3 surfaces issues:
- Either another hotfix cycle (small misses) OR rollback + restart as 2.22.0a.3
  (larger issues).

---

*Authored by Claude Code 2026-05-27 at Gate 2 post-hotfix completion.
Engine v135 live; awaiting Anas's mobile-device visual verification.*
