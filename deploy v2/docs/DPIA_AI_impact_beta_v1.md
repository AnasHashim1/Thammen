# DPIA + Algorithmic-Impact Note — Thammen Free Beta (v1)
> Internal, non-lawyer record. Pairs with COMPLIANCE_SELF_CLEARANCE_beta_v1 (R13).
> Proportionate to a free, invite-only, capture-DORMANT beta. Revisit before capture activation,
> before any paid access, and on cohort growth beyond ~25.

## 1. Scope & purpose
Free, invite-only accuracy beta. Villas + land only. Capture DORMANT (a16). Purpose: validate estimate
accuracy and surface PDPPL in practice — nothing more.

## 2. Data inventory & flows
- Query input (zone/street/building [± plot area/rent]): a property address is personal data of its
  owner. Processed to compute an estimate; a COPY of each report (address + parcel data: PIN / district /
  GPS / the estimate) is RETAINED in the OPERATOR's email records (Resend + the operator inbox) for
  record-keeping + accuracy (b42/b43). Not linked to a user identity (no account). The Kahramaa utility
  account numbers are SCRUBBED from the copy (b43); no personal contact data is collected.
- Output: returned to the user; the report copy is retained in operator records (as above). The
  a15/a16 Postgres capture stays DORMANT (no DB + flag off) — a separate mechanism from the operator email-copy.
- Feedback: VOLUNTARY, user -> Thammen team by EMAIL (info@thammen.qa, b50). Controller = Anas. Accuracy use only.
- No accounts, no tracking/analytics cookies, no profiling, no personal contact data collected.

## 3. Lawful basis
Explicit, informed, voluntary consent — via the invite (consent record: invite text + invited list +
date) and an affirmative entry click. No legitimate-interest reliance (Q6).

## 4. Necessity & proportionality
Minimal data; a single report copy retained in operator records (address + parcel data only; no personal
contact data; utility account numbers scrubbed); smallest viable cohort; honest framing throughout.
Apartments gracefully refused (not the beta's focus).

## 5. Risks & mitigations
- Re-identification of an owner via address -> the address IS retained in the operator's records, but is
  not linked to a user identity, carries no personal contact data, and is scrubbed of the utility account
  numbers (b43) -> residual low (operator-only, no third-party sharing).
- Cross-border PROCESSING + retention (Heroku US/EU + Cloudflare + Resend email) -> disclosed in the
  notice; for the invited beta it is the operator's OWN records only; residency/SCC (Q3/Q4) = a
  pre-wider-rollout / pre-activation review item.
- Infra request-body logging (addresses) -> the a24 §4 scrub keeps the address out of the app INFO logs;
  VERIFY Cloudflare/Heroku do not persist POST bodies.
- Feedback + record-copy channel security (info@thammen.qa + the operator inbox/Resend) -> 2FA on the
  operator email; delete-on-request.
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
None at beta scale. No large-scale systematic monitoring, no special-category data at scale; the only
retained record is the operator's own report copy (no personal contact data). Anas (info@thammen.qa) is
the single accountable controller/contact. Revisit at activation/public.

## 8. Retention & breach
Retention: each report copy lives in the operator's email records (Resend + inbox), deletion on request;
no automated user-facing datastore in the beta (the a15/a16 capture stays DORMANT). At activation:
180-day auto-expiry + erasure runbook (R11) — out of scope here. Breach: 72-hour notification posture;
surface = the retained report copy + the feedback channel.

## 9. Review triggers
Before flipping capture (activation) · before any paid access · on cohort growth beyond ~25.
