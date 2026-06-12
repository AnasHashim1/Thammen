# CHANGELOG v107 — Sprint 2.22.0b.24 «حزمة R13 النصية» (م0 — the R13 first-screens text bundle)

**Engine:** `thammen-sprint2p22p0b24-r13-first-screens-text` · **Date:** 2026-06-12
**Files:** `index.html` · `api.py` · `scope_of_service.py` · `data_freshness.py` · `evaluate_unified.py` (version strings ONLY) · `test_sprint_2_22_0b24.py` (new) · `test_scope_of_service.py` + `test_sprint_2_22_0b3.py` (pin re-points)
**Program:** م0 of «الواجهة والتقريران» (the signed multi-phase program; plan = `docs/PLAN_short_report_rollout_v1.1.md` — reconciled to Anas's original verbatim this session, صفر-أ). 🟢 **Presentational / VALUE-INVARIANT** — the engine diff is the 2 version-string lines; the 22-fixture byte-contract on amount/low/high/rule holds **by construction**.

## 1. Why this matters
The first screens over-claimed («تقييم» on the hero of a tool whose own Terms say it is NOT a تقييم معتمد — the R13 framing risk), hid the data recency until JS loaded, mislabeled the audience selector as «نوع التقرير» (implying different numbers per audience), and — worst — the confirm screen called EVERY central value «الوسيط» even when the b20 leadership gate had put the **DRC cost** (امريخ) or an **income figure** in the lead. One screen, one honest voice.

## 2. Root cause
- `index.html:382-383` hero said «تقييم عقارك / ابدأ التقييم»; `:384` static subtitle carried no recency.
- `:439-445` selector label «👤 نوع التقرير» + buyer default; «مالك» (the v4 journey's actual persona) absent; `api.py` `_AUDIENCE_ACCEPTED` rejected `owner` with 422.
- `showConfirm` (`:810`) printed the blind literal «الوسيط ≈» regardless of `valuation.leadership` (b20) — cost-led and income-led centrals are NOT medians.
- `scope_of_service.service_scope_summary()` iterated `.values()` over a dict carrying the Rule-#47 alias `raw_land → land` ⇒ the SAME AssetScope emitted twice ⇒ a duplicated «أرض سكنية» card + «4 فئات» count; the villa card used the colloquial «فلة مستقلة» vs the app-canonical «فيلا منفردة».

## 3. What this patch does
- **Home:** «تقدير عقارك في قطر» + «ابدأ التقدير»; static subtitle = the signed «بيانات وزارة العدل حتى ديسمبر 2025»; `data_freshness._render_subtitle` emits the same صيغة («حتى {الشهر}») so the dynamic refresh self-heals on a MoJ update.
- **Audience:** label → «👤 من أنت؟ (يحدّد طريقة العرض فقط — الرقم واحد للجميع)»; «مالك» 🔑 restored as the DEFAULT first option before مشتري/بائع/مستثمر/مثمّن; `let audience='owner'`; `api.py` accepts `owner`/`مالك` (the engine's `_normalize_audience` maps unknown→buyer ⇒ owner renders the default view with ZERO engine change; valuer keeps its v4 skip-to-results routing).
- **Confirm screen (leadership-aware):** the central-value label reads the b20 JSON — `leadership.leader==='cost'` → **«مرتكز التكلفة (أرض + بناء مُهلَك)»** + the dual evidence line «شواهد السوق: مطابق n={n} (<10) · جغرافي {n}/{disp} (>0.30)» (all from the broadcast incl. thresholds — zero JS arithmetic); `leader==='market'` → «الوسيط» (a true comparison median); income_led (detected via `income_triangulation.mode` — the method string stays `comparison_*` on income_led, measured at `evaluate_unified:4865`) and income-only/hybrid → the neutral «التقدير المركزي».
- **Scope window:** enumeration deduped by object identity (the #47 alias itself INTACT — `classify_asset_scope('raw_land')` unchanged) ⇒ «أرض سكنية» once, supported count back to 3; villa card → «فيلا منفردة».
- **Numbering (measured, #54):** the live surfaces ALREADY conform to the 2025 map (VPS 3/IVS 103 approaches · VPS 5/IVS 105 models · VPGA 10 MUC · VPS 6/IVS 106 reports · VPS 2/IVS 102 HBU); zero stale VPS 4/VPN 13 in live files (guarded by the standing a8/a22 tests + re-asserted in the b24 test). **No correct citation was removed** — see §8.

## 4. Backend / frontend / schema
Backend: `api.py` whitelist +2 values (boundary, additive); `scope_of_service.py` label + enumeration dedup (display listing); `data_freshness.py` subtitle string. **No value path touched.** Frontend: the 4 surfaces above. Schema: none (no new fields).

## 5. Verification — empirical evidence
- Isolated `test_sprint_2_22_0b24.py` **58/58** (real files/functions per E14: api `_check_audience('owner'/'مالك')` accept + bogus reject · engine `_normalize_audience('owner')=='buyer'` · scope dedup + alias-intact + count==3 · the JS label-decision mirror over 7 leadership shapes · LTR islands + escaped comparators).
- Pin re-points: `test_scope_of_service.py` («فلة»→«فيلا») + `test_sprint_2_22_0b3.py` (the blind «الوسيط ≈» literal → behavior markers; R6-class).
- DoD: aggregator **392/392 MATCH** · security **15/15** · surface-honesty **45/45** · broad walk **93/93 ALL GREEN** (92→93, +b24) · siblings re-run on the FINAL tree: b2p3 32/32 · b3 14/14 · b15 49/49 · b17 33/33 · b20 69/69 · b23 47/47 · scope 27/27.
- **R14 real-Chromium 390×844** (static serve + injected REAL-shaped payloads): hero/CTA/subtitle verbatim; «مالك» [SEL] first + `audience='owner'`; cost-led → «مرتكز التكلفة (أرض + بناء مُهلَك) ≈ ٢٬٤٠٠٬٠٠٠ ر.ق» + «شواهد السوق: مطابق n=3 (<10) · جغرافي 51/0.62 (>0.3)» (right-edge 353<390); matched → «الوسيط»; income_led REAL shape → «التقدير المركزي»; **0 console errors/warnings**; docScrollW 390==390 (no overflow). The R14 walk **CAUGHT a real defect** pre-ship: income_led keeps the `comparison_*` method string, so the method-fallback alone would have mislabeled it «الوسيط» → the `income_triangulation.mode` guard added + tested. (preview_screenshot timed out — the known §20.34 capture hiccup; DOM measurements = the evidence channel.)
- **Byte-contract:** structural — `git diff evaluate_unified.py` = the 2 version lines; nothing writes amount/low/high/method/rule. The live 4-fixture byte-smoke joins the **deferred smoke basket** (khazna R5 hang, measured again this session: primary timeout + legacy 500).

## 6. Deployment
```
git add <files>
git commit -m "Sprint 2.22.0b.24: R13 first-screens text bundle (m0)"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 7. Verification curl
```
curl -s https://thammen.qa/api/health | findstr "b24"
curl -s https://thammen.qa/ -A "Mozilla/5.0" | findstr /C:"تقدير عقارك في قطر" /C:"من أنت؟" /C:"مرتكز التكلفة"
```

## 8. What's NOT in this patch
- **No methodology/value change** — amount/low/high/method/rule untouched on every path (structural).
- **The literal «صفر VPS 3 وصفر IVS 105» reading is NOT executed** (#54 adjudication): the only live «VPS 3»/«IVS 105» occurrences are the **verified-correct 2025-map citations** (approaches/models — triple-confirmed primary-source, a8/§20.9, re-adjudicated a22 against the models' stale-2022 prior where VPS 3 meant *reports* and IVS 105 meant *approaches*). Stripping them would un-ship verified citations and break the standing a8/a22 guard tests. **Measured state: zero STALE numbering — the bullet's substance (live conformance to the 2025 map) is satisfied.** If the PO means literal removal, that is its own signed Gate-2 word.
- The results-screen/report «الوسيط» blind labels on cost-led = **م3** (the signed PDF-audit fixes) — not patched here (strict م0 scope = the confirm screen).
- Consent layers untouched (خارج الحصر — separate legal word).
- The beta gate + Terms copy untouched (a24 signed verbatim).
