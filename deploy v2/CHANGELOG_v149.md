# CHANGELOG v149 — Sprint 2.22.0b.68 «صدق إشعار الخصوصيّة» (privacy-notice truthfulness) — DEBUG T0-1

**Engine:** `thammen-sprint2p22p0b68-privacy-notice-truthful` · **SPRINT_TAG** `2.22.0b.68` · **Date:** 2026-06-25
**Files:** `index.html` (Terms §3/§6 AR+EN) · `docs/DPIA_AI_impact_beta_v1.md` (backing doc aligned) · `evaluate_unified.py` (2 version lines) · `test_sprint_2_22_0b68.py` (new) · `test_sprint_2_22_0b67.py` (1 R6 re-point) · `CHANGELOG_v149.md` · `docs/Session_Log.md`
**Class:** 🟢 FRONTEND + doc / **VALUE-INVARIANT** (Terms copy + the DPIA backing; engine = 2 version lines; no valuation change). Gate-2 (user-facing compliance copy) — PO delegated via «اكمل وافعل الأصوب» + the approved launch-readiness plan (T0-1). **Lawyer + linguist personas applied** (PO standing directive). The **last TIER-0 blocker**.

## 1. Why this matters
The live a24 Terms §3 (Your data) + §6 (Security) claimed, in AR + EN: «الأداة لا تُخزّن أي بيانات» / «The tool stores nothing … processed in-memory and discarded / not retained» / «we do not store the [address] or link it to you». That became **FALSE** the moment the operator report-copy went LIVE (b42.1): **every report — including the property ADDRESS + parcel data (PIN/district/GPS/estimate), with the Kahramaa utility account numbers SCRUBBED per b43 — is emailed to the operator's records (Resend + the operator inbox)**. A false «stores nothing» is the worst compliance posture (a misrepresentation), and the §20.74 note flagged the notice update as the open T0-1 item.

## 2. What this patch does
Rewrites Terms §3 + §6 (AR + EN) to be TRUTHFUL:
- **§3:** «نحتفظ بنسخة من تقرير تقييمك (تشمل عنوان العقار وبياناته العقاريّة: الرقم المساحيّ والمنطقة والموقع والتقدير) في سجلّات فريق ثمّن، لأغراض حفظ السجلّات وتحسين دقّة التقييم» + «لا نجمع بيانات تواصل شخصيّة (اسم/هاتف/بريد/رقم هويّة)، وتُزال أرقام حسابات الكهرباء والماء من النسخة المحفوظة» + cross-border hosting names **Resend** (`Heroku وCloudflare وResend`, in a `dir=ltr` island) + **the deletion right** on the retained copy («يمكنك طلب حذف نسخة تقريرك من سجلّاتنا … بمراسلة جهة التواصل»). EN mirror.
- **§6:** «سطح الخطر محدود بنسخة التقرير المحفوظة في سجلّاتنا وقناة ملاحظاتك؛ ولا نحتفظ ببيانات تواصل شخصيّة» + the **72-hour** breach commitment KEPT.
- **DPIA backing doc** (`docs/DPIA_AI_impact_beta_v1.md`) aligned: §2/§4/§5/§7/§8 now reflect the retained operator report-copy + the b43 scrub + the b50 email channel (the stale WhatsApp `70177761` dropped); the a15/a16 Postgres capture is noted as a SEPARATE, still-DORMANT mechanism.

**Does NOT** reapply the rejected heavy address-redaction (b43 keeps the address by PO decision — §20.74). **KEEPS** every real cover: «ليس تقييماً معتمداً» / NOT-certified, the free framing, «غير منتسبة لوزارة العدل», the affirmative-consent line, the disclaimer §5.

## 3. Persona review (PO standing directive)
- **Lawyer APPROVE:** a false «stores nothing» is the HIGHEST liability; making the notice truthful REDUCES exposure. The retained copy is the operator's OWN records (no third-party sharing), scrubbed of personal contact/account data (b43), with a deletion-on-request right + the 72h breach posture. No new claim, no weakened disclaimer. Non-blocking note: the cross-border residency/SCC question (Heroku/Cloudflare/Resend US/EU) is now explicitly a pre-wider-rollout / pre-activation review item (Tier-2, PO/counsel) — disclosed-not-resolved, acceptable for the invited beta.
- **Linguist APPROVE:** فصيح + register-consistent with the rest of the notice; the Latin hosting names are in a `dir=ltr` island (bidi-safe); the new AR sentences are pure-Arabic.

## 4. Scope boundary (Rule #38)
The **consent-gate** «stores nothing» strings (lines 453/847/851/899/3178 — the `sessionStorage` consent-flag mechanism) are UNTOUCHED: they describe a frontend-only consent flag, which genuinely stores nothing client-side. Only the DATA claims in Terms §3/§6 were false. The result/report screens are not touched.

## 5. Verification — empirical evidence
- isolated `test_sprint_2_22_0b68.py` **37/37** (the 8 false claims removed AR+EN; the truthful disclosure present AR+EN incl. Resend + scrub + deletion-right; the 72h breach kept; the real cover preserved; the consent-gate «stores nothing» mechanism preserved; the Latin tokens in a `dir=ltr` island + the new AR sentences pure-Arabic; the DPIA aligned — no «nothing stored», email channel, scrub noted).
- **1 R6/Lesson-2 re-point** (test-only): `test_sprint_2_22_0b67.py`'s exact-version pin `ENGINE_VERSION == b67` → a version-agnostic format check (the b67 landing is proven by the stable `Sprint 2.22.0b.67` comment marker) — the broad walk caught it on the b68 bump (the recurring no-exact-version-pins discipline; the b68 test's own pin was relaxed proactively).
- DoD: aggregator **395/395 MATCH** · security **16/16** · surface **45/45** · broad walk **124/124 ALL GREEN** (123→124, +b68). Copy siblings b50 32/32 · b54 44/44 · b56 30/30 · b58 27/27 green **WITHOUT re-point**.
- **R14 real-Chromium 390×844:** `openTerms()` renders the modal with the truthful §3/§6 (AR keep-copy + EN keep-copy + Resend + the deletion right + the b43 scrub), the false «stores nothing»/«not retained» claims ABSENT (AR+EN), the cover («ليس تقييماً معتمداً» / free / 72h) preserved, **no horizontal overflow** (docScrollW 390 == clientW 390, modalScrollW 390), **0 console errors/warnings**.
- Live smoke + served-HTML markers (see §20.97).

## 6. Deployment
```
git add "deploy v2/index.html" "deploy v2/docs/DPIA_AI_impact_beta_v1.md" "deploy v2/evaluate_unified.py" "deploy v2/test_sprint_2_22_0b68.py" "deploy v2/test_sprint_2_22_0b67.py" "deploy v2/CHANGELOG_v149.md" "deploy v2/docs/Session_Log.md"
git commit -m "Sprint 2.22.0b.68: privacy-notice truthfulness (T0-1) — disclose the retained operator report-copy; value-invariant"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 7. Verification curl (post-deploy)
```
curl -s https://thammen.qa/api/health   # → engine thammen-sprint2p22p0b68-privacy-notice-truthful
# served index.html: «نحتفظ بنسخة من تقرير تقييمك» present, «الأداة لا تُخزّن أي بيانات» absent,
# «We keep a copy of your valuation report» present, «The tool stores nothing» absent, Resend present.
# 5-fixture value byte-gate identical to v239 (copy-only; no engine change).
```

## 8. What's NOT in this patch
- The cross-border residency / SCC decision (Q3/Q4) — a Tier-2 PO/counsel item before wider rollout / capture activation (the notice now DISCLOSES the cross-border processing; the SCC posture is a separate decision).
- The a15/a16 Postgres capture — stays DORMANT; its activation has its own gate (R11).
- No valuation/method/UI change beyond the Terms copy + the DPIA doc.
