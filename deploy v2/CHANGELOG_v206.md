# CHANGELOG v206 — Sprint 2.22.0b.129 «التقرير المختصر اللين» (the lean short report, redesign v2 — the b128 lean destination in use)

Engine `thammen-sprint2p22p0b129-lean-short-report` · SPRINT_TAG `2.22.0b.129` · api-health `3.1.0-sprint2.22.0b.129`.
🟢 **FRONTEND-ONLY / VALUE-NEUTRAL** — `api.py` + the valuation engine UNTOUCHED (only the 2 version-string lines
in `evaluate_unified.py`); the amount is PRESENTED, never recomputed. The redesign-v2 program's short-report
lean slice (the counterpart to the b128 consolidated «الشروط والمنهجيّة» screen, which was built first as the
destination).

## 1. Files changed
- `index.html` — `showShortReport` (the owner story stays; the full terms/methodology route to b128 via a link;
  the 3 guards stay) + the redesign-v2 CSS (`.legalfull`, `.sr-terms`, `.thmr-basis`, `@media print` rules).
- `evaluate_unified.py` — SPRINT_TAG/ENGINE_VERSION → b129 (2 lines).
- `test_sprint_2_22_0b129.py` — new isolated test (E14, reads the real index.html).
- `test_sprint_2_22_0b128.py` — 1 R6/Lesson-2 re-point (exact-version pin `b128` → version-agnostic format check).

## 2. Why this matters
The PO's «منتج لين» decision (redesign-v2 plan): the short report was already visually lean (b90/b103 folded the
detail behind two `<details>`), but it still **carried** the full methodology/assumptions/cost-mechanism/
hierarchy/terms inline, and the basis-of-value + the «>5M → licensed valuer» compliance cover were not adjacent to
the number. The designer model (`ثمّن - التقرير المختصر.dc.html`) + `ANSWERS_to_claude_code.md` route that
detail to the one consolidated «الشروط والمنهجيّة» screen (b128) and keep only the 3 guards on the report.

## 3. What this patch does
- **GUARD 1 — basis of value (RICS VPS 2 / IVS 102) relocated ADJACENT to the number** (was §٩, far in the page-2
  fold; now a compact `.thmr-basis` line directly under the hero). Leader-agnostic (true for market/cost/income/
  land). It is the cover that stops the figure being read as a final price. Verbatim text (b106 R-1 preserved).
- **GUARD 3 — «>5M → licensed valuer»**, a conditional note near the number: `if(v.amount>5000000)` (ANSWERS Q1).
  Shows on land 7.1M / any villa >5M; NOT on the 2.4M/2.8M cases.
- **GUARD 2 — the FULL legal block prints ONLY** (`.legalfull`, `@media print{body.printing-short .legalfull{
  display:block}}`) — the printed PDF contract (ANSWERS Q17). On screen §٩ shows a compact line + a
  **«الشروط والمنهجيّة الكاملة ›» link → openTerms()** (the b128 destination). The verbatim full text stays in the
  DOM — nothing deleted.
- **«الشروط الكاملة ›» link** on the page-1 compressed legal line → openTerms() (b128) too.
- The owner story (§١ leader story + proof rows · §٢ three numbers · §٣ practical takeaway · §٤-٥ · scenarios §٦ ·
  investor §٧ · evidence §٨) is PRESERVED (folded, as before). Refusal path unchanged (early-return).
- Every new/moved string carries an EN twin (`t('عربي','English')`); EN stays live (b88).

## 4. Backend / schema
None. `api.py` untouched; `evaluate_unified.py` = 2 version lines only. Value-neutral by construction.

## 5. Verification — empirical evidence
- py_compile (evaluate_unified.py + api.py) OK; node --check on the 3 inline scripts OK (main script 3152 lines).
- Isolated `test_sprint_2_22_0b129.py` **23/23** (the 3 guards + the b128-destination link + value-neutrality +
  compliance preserved + the R-B leader-agnostic guard + EN twins).
- Sibling re-points/regression: `test_sprint_2_22_0b128.py` **45/45** (R6 version-pin → format); b106 **22/22**,
  b103, b94, b90, b25 **77/77** all green WITHOUT re-point (nothing deleted — moved text stays in SR).
- DoD: aggregator **ALL COUNTS MATCH** · security **16/16** · surface honesty **45/45** · broad walk
  **179 network-independent GREEN**; the only 2 non-passes (b114 latency, b116 gis-cache) are **live-GIS-flaky**
  (khazna «falling back to network»/timeout under parallel load) — both **PASS isolated** (16/16, 14/14); the
  frontend change touches no GIS/engine (R5 infra, not a regression).
- **R14 real-Chromium 390×844 on the 5 design fixtures** (cost 2.4M · income 2.8M · market 2.4M · land 7.1M ·
  refusal): value byte-identical (hero ٢٬٤٠٠٬٠٠٠/٢٬٨٠٠٬٠٠٠/٢٬٤٠٠٬٠٠٠/٧٬١٠٠٬٠٠٠); G1 basis present + leader-
  agnostic on the 4 valued; **G3 «>5M» visible ONLY on land 7.1M**, not the 2.4M/2.8M villas (R-B correct);
  G2 `.legalfull` present + display:none on screen + textContent carries IFRS 13/judicial/estates/tamper +
  (CSSOM) shown when printing + `.sr-screenonly` hidden when printing; terms link → openTerms() opens the b128
  modal (none→flex) carrying methodology + basis + cost + hierarchy + «>5M» + full terms; «ليس تقييماً معتمداً»
  on all 5; **0 console errors**; **no horizontal overflow** (scrollW 375 == clientW 375) on all 5.
- Personas (PO standing directive): lawyer APPROVE (each guard preserves the protection — the compact §٩ line
  keeps «ليس معتمداً + IFRS 13 + official-purposes», the full block rides the PDF, the b128 link carries the full
  terms one tap away; the >5M note raises defensibility); linguist APPROVE (فصحى, register-consistent with b128).

## 6. Deployment
`git push origin master` FIRST, then `git -C "C:/Thammen" subtree push --prefix "deploy v2" heroku master` (#43).

## 7. Verification curl (post-deploy, browser-UA #61)
`curl -s -A "Mozilla/5.0" https://thammen.qa/api/health` → `3.1.0-sprint2.22.0b.129`; the 5-fixture byte-gate
byte-identical to v292 (54/541/6=2.4M · 56/647/6=3.8M · 55/296/13=2.6M · 56/565/21=2.4M · 52/903/90=refusal);
served `/` carries `.thmr-basis` + `.legalfull` + `<a class="sr-terms" onclick="openTerms()">`.

## 8. What's NOT in this patch
The full report (`showReport`) leaning is a separate slice (next). The methodology/assumptions/cost/hierarchy
detail is NOT re-authored — it lives verbatim in the b128 consolidated screen; the report just links to it.
No value/method/rule change; no engine touch beyond the version lines.
