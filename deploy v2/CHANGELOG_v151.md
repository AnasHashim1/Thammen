# CHANGELOG v151 — Sprint 2.22.0b.70 «وصوليّة النوافذ» (modal a11y) — Tier-1 hardening

**Engine:** `thammen-sprint2p22p0b70-modal-a11y` · **SPRINT_TAG** `2.22.0b.70` · **Date:** 2026-06-25
**Files:** `index.html` (scopeModal + termsModal role/aria + an Escape keydown handler) · `evaluate_unified.py` (2 version lines) · `test_sprint_2_22_0b70.py` (new) · `CHANGELOG_v151.md` · `docs/Session_Log.md`
**Class:** 🟢 FRONTEND-ONLY / **VALUE-INVARIANT** (additive HTML attributes + one keydown listener; engine = 2 version lines; no valuation change; the 5-fixture value byte-gate identical).

## 1. Why this matters
The two DISMISSABLE modals — `scopeModal` («نطاق الخدمة») and `termsModal` («الشروط وإشعار الخصوصية») — lacked `role="dialog"` / `aria-modal` / an accessible label, and could not be closed with the keyboard (Escape). That is a WCAG operability + screen-reader gap (a screen reader did not announce them as dialogs; a keyboard-only user could only close via the × button or a backdrop click).

## 2. What this patch does
- **scopeModal + termsModal:** add `role="dialog"` + `aria-modal="true"` + an Arabic `aria-label` (the modal title). Additive attributes — zero behavior change.
- **Escape-to-close:** one global `keydown` listener that, on `Escape`, closes ONLY the two dismissable modals (`closeScope()` / `closeTerms()` when each is open). The existing backdrop-click-to-close is preserved.
- **The betaGate consent dialog is intentionally NOT Escape-closable** (affirmative consent is required to proceed) — the Escape handler does not reference it; betaGate keeps its own dialog a11y from b46/b27 (untouched).

## 3. Verification — empirical evidence
- isolated `test_sprint_2_22_0b70.py` **15/15** (both modals role=dialog + aria-modal + aria-label; the Escape handler closes scope+terms; its executable body does NOT touch betaGate [exactly closeScope + closeTerms]; betaGate's own dialog a11y untouched; the backdrop-close preserved).
- DoD: aggregator **395/395 MATCH** · security **16/16** · surface **45/45** · broad walk **126/126 ALL GREEN** (125→126, +b70) — **ZERO re-points** (b27/gate tests unaffected by the additive attributes).
- **R14 real-Chromium 390×844:** scopeModal + termsModal report `role=dialog` / `aria-modal=true` / aria-label; `openScope()` → display flex → **Escape closes it** (display none); `openTerms()` → display flex → **Escape closes it**; **betaGate visible on load + STILL visible after Escape** (consent stays mandatory); no horizontal overflow (390==390); **0 console errors/warnings**.
- Live smoke + served-HTML markers (see §20.99).

## 4. Scope / deferrals (verify-first, documented)
b70 ships the high-value, low-risk core: dialog semantics + Escape. The fuller WCAG dialog pattern (a **focus-trap** — Tab cycles within the modal — + focus-restore-on-close) is DEFERRED to a Tier-3 a11y pass (it is the higher-complexity part; an invited beta is acceptable with role/aria-modal + Escape + backdrop-close). Also documented-deferred from the launch-readiness a11y tranche: the brown helper-text contrast (measured ~4.4:1 — marginal vs AA 4.5, and a brand-tint→grey tradeoff → a PO brand call); keyboard-nav role/tabindex on the custom tab/grid/toggle controls (higher-risk JS → Tier-3); the `.fr3` mobile media query (b49 already fixed the @390 overflow — non-issue).

## 5. Deployment
```
git add "deploy v2/index.html" "deploy v2/evaluate_unified.py" "deploy v2/test_sprint_2_22_0b70.py" "deploy v2/CHANGELOG_v151.md" "deploy v2/docs/Session_Log.md"
git commit -m "Sprint 2.22.0b.70: modal a11y (role/aria-modal/label + Escape on scope+terms); value-invariant"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 6. Verification curl (post-deploy)
```
curl -s https://thammen.qa/api/health   # → engine thammen-sprint2p22p0b70-modal-a11y
# served index.html: scopeModal + termsModal carry role="dialog" aria-modal="true"; the b70 Escape handler present.
# 5-fixture value byte-gate identical to v241 (frontend a11y only; no engine change).
```

## 7. What's NOT in this patch
- Focus-trap / focus-restore (the advanced dialog a11y) — Tier-3.
- The contrast / keyboard-nav / .fr3 items — deferred per §4.
- No valuation/method/copy change.
