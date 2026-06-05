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
| Q13 | **data.gov.qa licence terms for the MoJ dataset** | Confirmed 2026-06-05: licence = **CC BY 4.0** (publisher = Ministry of Justice; verified via the OpenDataSoft catalog API — `weekly-real-estates-sales-bulletin`, the dataset the engine ingests; CC BY is portal-wide). **Commercial reuse · derivatives · redistribution all permitted;** sole obligation = attribution + no-endorsement. | **VERIFIED** — attribution applied 2026-06-05 (Sprint 2.22.0a.25 / Heroku v164: verbatim CC BY 4.0 source credit + licence link in the results footer). Non-lawyer reading of a standard licence; revisit before paid (existing posture). | ✅ VERIFIED |
| Q14 | **Aqarat licensing** | Free beta is **defensible** (free + invited + research + «تقدير لا تقييم» + gov precedent), **but the catch-all gives no guaranteed safe harbour.** No paid access until licensed. | **Send the direct Aqarat enquiry** to close the free-beta question; enter the licensing framework before monetizing. | OPEN→REGULATOR |

---

## D. Genuinely open items (not "decided by over-compliance")

1. **DB residency decision** (Q3/Q4) — Qatar/GCC vs Heroku US/EU. Choosing local moots the entire cross-border question.
2. **Activation engineering** (Q8 / R11) — Fernet round-trip verified on Heroku, short backup retention, backup-erasure runbook. Required before the capture flag is ever flipped.
3. ~~**MoJ open-data licence** (Q13)~~ — ✅ **CLOSED 2026-06-05**: licence = CC BY 4.0 (commercial + derivatives + redistribution permitted with attribution); attribution applied in Sprint 2.22.0a.25 (Heroku v164). No longer a monetization gate.
4. **Aqarat enquiry** (Q14) — the one external touch we keep: a crisp regulator question to certify the free beta, and the entry point for the licence we'll obtain before charging.
5. **Lightweight DPIA + AI-impact note** (Q10/Q11) — recommended documentation; cheap insurance.

---

## E. Risk-register entry

R13 (this decision) is recorded authoritatively in `RISK_REGISTER.md`. A paste-ready draft of the row previously lived here; it was removed to keep a single source of truth.

---

*Owner: Anas. Non-lawyer self-assessment. Revisit before flipping the capture flag and before any paid access.*
