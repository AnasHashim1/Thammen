# CHANGELOG v157 — Sprint 2.22.0b.76 «إتمام كنس الإيموجي» (complete the engine emoji sweep)

**Engine:** `thammen-sprint2p22p0b76-engine-emoji-complete` · **SPRINT_TAG** `2.22.0b.76` · **Date:** 2026-06-27
**Files:** `material_uncertainty.py` · `market_regime.py` · `geometric_factors.py` · `qatar_gis.py` · `evaluate_unified.py` (2 version lines) · `test_sprint_2_22_0b76.py` (new) · `CHANGELOG_v157.md` · `docs/Session_Log.md`
**Class:** 🟢 ENGINE COPY-ONLY / **VALUE-INVARIANT** (`index.html` + `api.py` UNTOUCHED; only display STRINGS change; the 5-fixture byte-gate identical to v246). Overnight queue #5 — completes b74.

## 1. Why this matters (honest correction to b74)
b74 swept emoji from `evaluate_unified.py` only and claimed it "completed the engine de-emoji" — **that was premature.** A measured live case-matrix (cost / geo / e25 / matched / apartment-refusal / land / unknown-refusal) found the remaining **user-facing-RESPONSE** emoji live: in **`material_uncertainty.py`** — the Material-Uncertainty banner (`⛔`/`⚠️`/`ℹ️`/`✅`) + the MUC clause (`⚠️`), AR+EN — which renders on **every valued result**. Plus three confirmed response-bound (rare-path) strings. This sprint finishes the PO's «لا اريد ايموجيز» / b48 "zero emoji" engine-side.

## 2. What this patch does
Stripped the leading/trailing emoji from the **response-bound** display strings (the level/message text is fully preserved — the MUC level reads from «تحفظ مادي جوهري/عالٍ/متوسط» / «مستوى اليقين جيد», not the glyph):
- **`material_uncertainty.py`** (10): the 4 banner levels (`⛔`/`⚠️`/`ℹ️`/`✅`) + the MUC clause (`⚠️`), AR + EN.
- **`market_regime.py`** (1): the data-recency note (`⚠️ آخر معاملة في وزارة العدل`).
- **`geometric_factors.py`** (2): the adjacency `evidence_ar` (`⚠`).
- **`qatar_gis.py`** (4): the land/asset reality-check messages (`⚠ هذه القطعة/الأرض`, `البناء: موجود ✓`).
- **NOT touched (measured non-response):** every `print()`/`__main__`/CLI/debug emoji (incl. `qatar_gis`'s 2 `print(f'⚠ {f}')` — preserved + asserted), and the **`/verify` ✓/✗ status page** (a standalone server-rendered tamper-check page; its ✓/✗ are semantic pass/fail glyphs — a separate concern flagged for a follow-up, not the main UI).

## 3. Verification
- isolated `test_sprint_2_22_0b76.py` **24/24** (E14: 0 `⚠️`/`⛔`/`ℹ️`/`✅` in material_uncertainty · the 4 level TEXTS + clause + EN twins preserved · market_regime/geometric/qatar_gis de-emoji'd · **the 2 qatar_gis `print(⚠)` lines PRESERVED** [count==2] · b75 منهج intact).
- DoD: aggregator **395 MATCH** · security **16/16** · surface honesty **45/45** (the MUC de-emoji didn't break the contract) · broad walk **132/132 ALL GREEN** (131→132).
- **R14 N/A by construction** — `index.html` UNCHANGED; the frontend renders the cleaner strings identically (b59/§20.88 precedent).
- Live: the 5-fixture byte-gate byte-identical + a **re-dump of the live case-matrix → 0 user-facing-response emoji** (the b74-measured leak closed).

## 4. Deployment
```
git subtree push --prefix "deploy v2" heroku master   # from C:/Thammen toplevel
git push origin master
```

## 5. What's NOT in this patch
- The `/verify` page ✓/✗ status glyphs (functional, standalone page) — flagged for a follow-up. The EN twins of these notices are already covered (the MUC EN banner/clause are de-emoji'd here too).
