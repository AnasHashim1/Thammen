# DPIA + Algorithmic-Impact Note — Thammen Free Beta (v1)
> Internal, non-lawyer record. Pairs with COMPLIANCE_SELF_CLEARANCE_beta_v1 (R13).
> Proportionate to a free, invite-only, capture-DORMANT beta. Revisit before capture activation,
> before any paid access, and on cohort growth beyond ~25.

## 1. Scope & purpose
Free, invite-only accuracy beta. Villas + land only. Capture DORMANT (a16). Purpose: validate estimate
accuracy and surface PDPPL in practice — nothing more.

## 2. Data inventory & flows
- Query input (zone/street/building [± plot area/rent]): a property address is personal data of its
  owner. Processed in-memory to compute an estimate; NOT stored by the app; not linked to the user.
- Output: returned to the user, not stored. valuation_id returned but not persisted (a16).
- Feedback: VOLUNTARY, user -> Anas via WhatsApp (+974 70177761). Controller = Anas. Accuracy use only.
- No accounts, no tracking/analytics cookies, no profiling.

## 3. Lawful basis
Explicit, informed, voluntary consent — via the invite (consent record: invite text + invited list +
date) and an affirmative entry click. No legitimate-interest reliance (Q6).

## 4. Necessity & proportionality
Minimal data; nothing stored; smallest viable cohort; honest framing throughout. Apartments gracefully
refused (not the beta's focus).

## 5. Risks & mitigations
- Re-identification of an owner via address -> address not stored, not linked -> residual near-zero.
- Cross-border PROCESSING (Heroku US/EU + Cloudflare) -> disclosed in the notice; nothing stored, so
  residency/SCC concern (Q3/Q4) does not bite for the beta.
- Infra request-body logging (addresses) -> VERIFY Cloudflare/Heroku do not persist POST bodies; if they
  do, disable body logging / minimize retention.
- Feedback-channel security (Anas's WhatsApp + user device) -> 2FA on Anas's account; delete-on-request.
- DoS on /api/evaluate and /api/feedback -> rate-limited (slowapi 5/s, 30/min, 200/hr + Cloudflare;
  confirmed live in /api/health). /api/feedback is dormant.
- Algorithmic harm (treating an estimate as a valuation) -> mitigations all LIVE: not-certified
  disclaimer, material-uncertainty banner, B-1 bidirectional land-floor/condition disclosure,
  stale-data banner, villas/land-only scope.

## 6. Known model limitations (algorithmic-impact)
- Condition / fit-out / age blindness (R7) — disclosed bidirectionally via B-1; durable fix = B-2.
- MoJ data ~5 months stale — disclosed via banner.
- Thin-cell dispersion — handled via honest-range / lowered tier / MUC.
- n<20: feedback MOTIVATES, does not CALIBRATE (discipline).

## 7. DPO
None at beta scale. No large-scale systematic monitoring, no special-category data at scale, nothing
stored; Anas (WhatsApp +974 70177761) is the single accountable controller/contact. Revisit at
activation/public.

## 8. Retention & breach
Retention: N/A (nothing stored) in the beta. At activation: 180-day auto-expiry + erasure runbook (R11)
— out of scope here. Breach: 72-hour notification posture; surface limited to transient processing +
the feedback channel.

## 9. Review triggers
Before flipping capture (activation) · before any paid access · on cohort growth beyond ~25.
