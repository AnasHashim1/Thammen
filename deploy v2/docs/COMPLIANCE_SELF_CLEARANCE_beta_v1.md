# Thammen — Conservative Self-Clearance (Free Beta)

> **Replaces external legal counsel** for the free, invited beta, per Anas's decision of **2026-06-02**.
> This is an internal, non-lawyer compliance record. It is **not legal advice**. Its strategy is *over-compliance*: where a question is unresolved, Thammen adopts the **strictest** option so the safe side is the default. The two genuinely open items (Q13 open-data licence, Q14 Aqarat) are closed by a direct regulator enquiry, not by assumption.
> Posture: **FREE invite-only accuracy beta → validate the system → obtain Aqarat licence → only then monetize.** No paid access before licensing.

---

## A. Decision record (2026-06-02)

- **No external counsel** will be engaged for the free beta. Compliance is self-cleared conservatively.
- **No paid access** until the necessary Aqarat licence(s) are obtained; licensing is *deferred*, not skipped.
- The free beta is framed as **accuracy research among invited users**, with outputs labelled **«تقدير سوقي آلي، وليس تقييماً معتمداً»**.

## B. Regulatory finding that frames this (web research, 2026-06-02)

- **Real-estate valuation is a named, regulated activity.** Amiri Decision **No. 28 of 2023** (which established Aqarat) lists, among Aqarat's competencies (Art. 5(7)), approving the rules governing several real-estate professions **including real-estate valuation (التقييم العقاري)** — plus a broad catch-all *«وغيرها من الأنشطة العقارية»* (and other real-estate activities). Source: Al Meezan (Qatar Legal Portal).
- **The regime is tightening, not loosening.** Aqarat's Licensing director: valuers must now hold recognised qualifications within defined expertise levels; the old "a broker can also value without requirements" is **no longer acceptable** (The Peninsula, May 2026).
- **Government precedent for the framing exists.** Qatar's own e-gov runs a **free** "المثمّن العقاري" approximate-price tool, expressly disclaiming that the figure is the actual value — so *free + approximate + disclaimer* is established in Qatar (operated by the State, not a private licensee).
- **Not resolved by public sources:** whether a *private, automated, free* estimate tool falls inside the regulated "valuation" profession or the catch-all, and what licence category applies at monetization. → closed only by **asking Aqarat directly** (enquiry drafted separately).

---

## C. Conservative self-clearance checklist (Q1–Q14)

Status key: **DECIDED** = conservative stance adopted, action is documentation only · **ACTION** = a concrete to-do remains · **OPEN→REGULATOR** = only Aqarat/MCIT can give certainty.

| # | Question | Conservative decision adopted | Action / evidence | Status |
|---|----------|-------------------------------|-------------------|--------|
| Q1 | Is an address + valuation "personal data"? Invited-cohort identifiable? | **Treat every record as personal data** of the owner/occupant; assume the invited cohort is identifiable. Do not rely on "no name/IP/QID." | Privacy notice + consent written on this basis. | DECIDED |
| Q2 | UUID = anonymised or pseudonymised? | Treat as **pseudonymised** → full PDPPL obligations apply. | — | DECIDED |
| Q3 | Regulator approval before US/EU hosting? Consent enough? | **Avoid the question: host the capture DB in Qatar/GCC.** If overseas is ever retained: explicit consent + named jurisdiction + SCCs. | Decide DB residency (likely off Heroku common runtime, which is US/EU only). | ACTION |
| Q4 | Binding residency expectation / SCCs? | Assume a residency expectation **may** exist → Qatar/GCC residency is the safe default. | Same residency decision as Q3. | ACTION |
| Q5 | Must the privacy notice name the hosting jurisdiction? | **Yes** — name it explicitly. | Privacy-notice clause. | DECIDED |
| Q6 | Legitimate-interest vs explicit opt-in? | **Explicit, unbundled opt-in consent**, kept separate from the ToS. No legitimate-interest reliance. | Consent UI + record of consent. | DECIDED |
| Q7 | Special-nature data / free-text / price? | Free-text `note` **already removed (a16)**. Transacted price is optional and covered by the same explicit consent. | Confirm no free-text path remains. | DECIDED |
| Q8 | Residual re-identifiability + erasure scope? | **Strictest:** residual = personal data (do **not** claim zone+valuation is anonymised). On erasure, delete the **entire record** (not just street/building), reaching backups within the window. 180-day auto-expiry. | Gate-11 eng steps (R11): Fernet round-trip on Heroku · short PG backup retention · backup-erasure runbook. Needed **at activation**. | ACTION |
| Q9 | Breach timeline / channel / threshold? | Adopt the strictest posture: **72-hour** notification + documented breach-response procedure; notify NCSA/MCIT. | Write the breach-response procedure. | ACTION |
| Q10 | Register/notify? DPO? DPIA? | Prepare a **lightweight DPIA** for the AVM even if not strictly mandatory; no DPO at beta scale (document the reasoning). Registration: fold into the regulator enquiry. | Draft DPIA; add registration to the Aqarat/MCIT enquiry. | ACTION |
| Q11 | NCSA AI guidelines → algorithmic-impact assessment? | Review the NCSA AI guidelines; document a short algorithmic-impact note. | AI-impact note. | ACTION |
| Q12 | Are the 2021 MCIT/CDPD guidelines binding? | **Treat as if binding** (over-comply). | — | DECIDED |
| Q13 | **data.gov.qa licence terms for the MoJ dataset** | Do **not** assume commercial reuse is permitted. Confirm the exact licence (commercial reuse · derivatives · attribution format · redistribution). | **Verify the open-data licence** before monetization; apply attribution as required. *Independent of Aqarat — a separate gate to charging.* | ACTION |
| Q14 | **Aqarat licensing** | Free beta is **defensible** (free + invited + research + «تقدير لا تقييم» + gov precedent), **but the catch-all gives no guaranteed safe harbour.** No paid access until licensed. | **Send the direct Aqarat enquiry** to close the free-beta question; enter the licensing framework before monetizing. | OPEN→REGULATOR |

---

## D. Genuinely open items (not "decided by over-compliance")

1. **DB residency decision** (Q3/Q4) — Qatar/GCC vs Heroku US/EU. Choosing local moots the entire cross-border question.
2. **Activation engineering** (Q8 / R11) — Fernet round-trip verified on Heroku, short backup retention, backup-erasure runbook. Required before the capture flag is ever flipped.
3. **MoJ open-data licence** (Q13) — confirm commercial-reuse permission + attribution. A monetization gate *independent* of Aqarat.
4. **Aqarat enquiry** (Q14) — the one external touch we keep: a crisp regulator question to certify the free beta, and the entry point for the licence we'll obtain before charging.
5. **Lightweight DPIA + AI-impact note** (Q10/Q11) — recommended documentation; cheap insurance.

---

## E. Append to `RISK_REGISTER.md` (next ID = R13)

```
| **R13** | 🟠 | **Regulatory self-clearance without external counsel (free-beta decision, 2026-06-02).** Anas elected NOT to engage licensed counsel and to self-clear conservatively. التقييم العقاري is a *regulated activity* (Amiri Decision 28/2023 Art 5(7), Aqarat) with a broad catch-all, so operating even a FREE AVM on internal / AI-derived assumptions risks (a) being deemed an unlicensed regulated real-estate activity and (b) PDPPL non-compliance — neither *fully* curable by conservatism. | Web research 2026-06-02: Al Meezan confirms التقييم العقاري named among Aqarat-regulated professions + «وغيرها من الأنشطة العقارية» catch-all; Peninsula (May 2026) — Aqarat tightening valuer licensing ("broker-as-valuer no longer acceptable"); gov precedent — free "المثمّن العقاري" approximate-estimate tool with a "not necessarily the actual value" disclaimer. AVM-specific binary NOT in public sources. | **OPEN — accepted-with-mitigations.** (1) Beta is FREE, invite-only, accuracy-research, labelled «تقدير سوقي آلي، وليس تقييماً معتمداً»; NO paid access pre-licence. (2) PDPPL self-cleared conservatively — strict opt-in, all records treated as personal data, 180d retention, full erasure, documented security/breach, Qatar/GCC residency recommended (moots cross-border). (3) Aqarat licensing framework to be entered BEFORE monetization (confirmed required, not hypothetical). (4) Free-beta residual (does the catch-all reach a free automated tool?) closable only by a direct Aqarat enquiry — drafted, pending send. (5) MoJ open-data commercial-reuse licence = separate monetization gate (Q13). Checklist: `COMPLIANCE_SELF_CLEARANCE_beta_v1.md`. Honesty #10. |
```

---

*Owner: Anas. Non-lawyer self-assessment. Revisit before flipping the capture flag and before any paid access.*
