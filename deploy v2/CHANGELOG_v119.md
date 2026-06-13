# CHANGELOG v119 — Sprint 2.22.0b.36 «رفض الشقق فوريّ صادق» (DEF-UX3)

**Engine:** `thammen-sprint2p22p0b36-honest-apt-refusal` · **SPRINT_TAG** `2.22.0b.36` · **api/health** `3.1.0-sprint2.22.0b.36`
**Date:** 2026-06-13 · **Heroku target:** v207 (deploy-on-consent)
**Files changed:** `index.html` (2 frontend surfaces in `show()`) · `evaluate_unified.py` (the 2 version-string lines) · `test_sprint_2_22_0b36.py` (new) · `test_sprint_2_22_0b35.py` (1 R6/Lesson-2 re-point) · `CHANGELOG_v119.md`
**Type:** 🟢 FRONTEND-ONLY / VALUE-INVARIANT · Gate-2 (user-facing copy/scope) SIGNED in-session (scope = apartment+tower; remove the rent CTA) · `api.py` UNTOUCHED.

---

## 1. Why this matters

The apartment refusal screen was **misleading** for 8/10 of the persona LIVE review (`ISSUES_LOG §4ب`). Live (52/903/90 → `apartment_building`, amount `None`, `method=insufficient_data`) it presented **two false-promise surfaces**:
- the scope badge «⚠️ تقييم مشروط — عمارة شقق · منهج الدخل (Income Approach)» + «**يتطلب: الإيجار السنوي الإجمالي**»;
- the centered card «التقييم يحتاج بيانات إضافية» + a big button «**→ أدخل: الإيجار السنوي الإجمالي**» that deep-links (`goForm('rentalIncome')`) into the income flow.

Both imply that *adding rent yields a real, trustworthy valuation*. But the apartment **income product is the DEFERRED «بوابة بيانات الأنواع» (أ)** — there are **no MoJ per-unit comparables** (وزارة العدل لا تسجّل وحدات الشقق فردياً), the cap rate is a hardcoded «نموذجية», and the GAI/value_stack work is unshipped. So the honest stance is: **apartments aren't supported yet — ثمّن للفلل والأراضي فقط حالياً.**

## 2. Root cause (code)

`index.html` `show()`:
- **Surface 1** (scope badge): `if(ss.requires_user_input_ar&&!hasValuation) alerts+='…<strong>يتطلب:</strong> '+ss.requires_user_input_ar` (the `limited` tier renders «تقييم مشروط · منهج الدخل · يتطلب الإيجار» for any income type, apartments included).
- **Surface 2** (insufficient-data box): `var ctaText=ssReq?('→ أدخل: '+ssReq):…; flat+='<button class="insuf-cta" onclick="goForm(\''+focusTarget+'\')">'+ctaText+'</button>'` — an **unconditional** income deep-link on every income-type refusal.

The engine scope (`scope_of_service.py`) correctly marks `apartment_building` / `tower` as `tier='limited'` (income); the **UI framing** is what over-promised.

## 3. Recon reshape (ISSUES_LOG §4ب-2 spec was partly infeasible — the §20.26 pattern)

The signed DEF-UX3 spec had three parts; measured feasibility:

| spec part | verdict |
|---|---|
| (2) رسالة «للفلل والأراضي فقط» | ✅ **the achievable core** — reframe the two surfaces honestly. |
| (1) «كشف النوع client-side قبل الـAPI» | ⛔ **infeasible** — the asset type comes from server-side QARS classification; the 1-field identification (E17) gives the client no way to know «apartment» before the API responds. The refusal already returns in one round-trip (instant). |
| (3) «تعطيل الأنواع غير المدعومة في التبويب» | ⛔ **no asset-type tab exists** (the only tabs are address/PIN, both 1-field) → belongs to the deferred «بوابة الأنواع» (ج) types-tab/coming-soon cards. |

**Signed forks (in-session, recommended option taken):** scope = **apartment_building + tower** (the income-only types whose product is the deferred gate; compound_large = the methodologically-correct Income path per E20, palace = Cost → **unchanged**); the «→ أدخل: الإيجار» CTA → **suppressed** (don't advertise the deferred income product). **The income COMPUTATION + the refine rent inputs are UNTOUCHED — «بوابة الأنواع» (أ) owns them.**

## 4. What this patch does

**`index.html` `show()` — gated on a single predicate** `var _ux3NotReady=(d.asset_type==='apartment_building'||d.asset_type==='tower')&&!hasValuation;` (+ `var _ux3Noun=(d.asset_type==='tower')?'الأبراج':'الشقق';`):
- **Surface 1 (scope badge):** when `_ux3NotReady` → bad-styled badge «🚧 غير مدعوم بعد — {label}», the methodology line («منهج الدخل») is **dropped**, the «يتطلب: الإيجار» line is **dropped**, and a short honest sub renders: «ثمّن يدعم **الفلل والأراضي** فقط حالياً.» (the original `else` branch — «يتطلب» + `ss.disclaimer_ar` — is preserved verbatim for every other type).
- **Surface 2 (insufficient-data box):** when `_ux3NotReady` → icon 🚧, header «{الشقق|الأبراج} غير مدعومة بعد — للفلل والأراضي فقط», body «وزارة العدل لا تسجّل وحدات {الشقق|الأبراج} فردياً بشكل قابل للمقارنة، فلا نُصدر لها تقديراً موثوقاً بعد. نعمل على دعم هذا النوع لاحقاً.», and the income **CTA button is suppressed** (`if(!_ux3NotReady){…goForm…}`). The classification-facts card (address/district/type/area/map) is **kept**.
- Other refusals (compound_large keeps «→ أدخل: الإيجار السنوي الإجمالي للمجمع», palace, unknown) are **byte-identical**.

**Backend:** `evaluate_unified.py` = ENGINE_VERSION / SPRINT_TAG → b36 only. `api.py` UNTOUCHED. `scope_of_service.py` UNTOUCHED (apartment stays `tier='limited'` — the engine income product is not changed; we reframe the UI only).

**Value-invariance (by construction):** both surfaces gate on `!hasValuation`; the with-value income case (a power user supplies rent → `income_approach_only`) is byte-identical. The supported anchors (villas/lands) never enter the `_ux3NotReady` branch. No `v.amount/low/high` mutation.

## 5. Verification — empirical evidence

- **Isolated** `test_sprint_2_22_0b36.py` **22/22** (reads the REAL index.html — E14: the predicate apartment+tower&&!hasValuation; `_ux3Noun`; badge reframed 🚧/«غير مدعوم بعد»; «منهج الدخل» + «يتطلب» dropped/moved-to-else; honest copy; insuf header/why type-aware; the goForm CTA gated behind `if(!_ux3NotReady)`; compound_large NOT folded; value-invariance `&&!hasValuation`; `scope_of_service` apartment still `tier='limited'`; income artifacts intact).
- **R6/Lesson-2 re-point:** `test_sprint_2_22_0b35.py`'s exact b35 version pin → version-agnostic format check (the recurring «no exact version pins» rule); **b35 = 17/17**.
- **DoD:** aggregator `run_sprint_2p22p0a_suite.py` **392 ALL COUNTS MATCH** · security `test_sprint_2p16p17_security.py` **15/15** · `test_sprint_2p22p0a3_surface_honesty.py` **45/45** · broad walk `2p22p0_pre/run_regression_2p22p0a.py` **104/104 ALL GREEN** (103→104, 217s, 0 failed) · py_compile (evaluate_unified.py + api.py) OK.
- **R14 real-Chromium 390×844** (fresh b36 code loaded; live 52/903/90 payload): **apartment (buyer)** → honest badge «غير مدعوم بعد» + «للفلل والأراضي فقط» + «لا تسجّل وحدات» + «نعمل على دعم هذا النوع لاحقاً»; «يتطلب» **absent**; «منهج الدخل» **absent**; `insuf-cta` buttons **= []** (income CTA removed); no overflow (scrollW 390 == clientW 390) · **tower** (synthetic) → «الأبراج غير مدعومة» + CTA removed · **compound_large CONTROL** → UNCHANGED (keeps «يتطلب» + «منهج الدخل» + «→ أدخل: الإيجار السنوي الإجمالي للمجمع») · **0 console errors/warnings**.

## 6. Deployment

```
cd /d "C:\Thammen\deploy v2"
git add index.html evaluate_unified.py test_sprint_2_22_0b36.py test_sprint_2_22_0b35.py CHANGELOG_v119.md
git commit -m "Sprint 2.22.0b.36 (DEF-UX3): honest apartment/tower refusal — drop the misleading «يتطلب الإيجار» CTA"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 7. Verification curl (post-deploy — Rule #61 browser-UA POST)

```
curl -s https://thammen.qa/api/health   # → engine …b36-honest-apt-refusal
curl -s -A "Mozilla/5.0 … Chrome/120 Safari/537.36" -X POST https://thammen.qa/api/evaluate -H "Content-Type: application/json" -d "{\"zone\":52,\"street\":903,\"building\":90}"
# → asset_type apartment_building, amount None (refusal UNCHANGED — the served index.html carries the honest framing + _ux3NotReady)
```
Post-deploy: the 5-anchor value byte-gate (امريخ 2.4M cost-led · V001 3.8M · المعراض 2.6M · أبو هامور 2.4M matched · شقق refusal) must be byte-identical to v206 (frontend-only).

## 8. What's NOT in this patch (scope boundary)

- **NO change to the income computation / scope tiers** — apartments-with-rent still compute `income_approach_only` (8.5M via the tower pair); the value_stack/leadership/GAI work = the deferred **«بوابة بيانات الأنواع»** (أ/ب).
- **NO client-side pre-API asset detection** (infeasible, §3) and **NO asset-type tab** (deferred to «بوابة الأنواع» (ج)).
- compound_large + palace refusals are intentionally **unchanged** (their rent CTA is methodologically honest — E20 / Cost Approach).
- The honest card fires only on the refusal (`!hasValuation`); the with-value income path is the deferred gate's territory.
