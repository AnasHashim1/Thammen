# Multi-AI Validation — Sprint B-1 (a21) D3 RICS/IVS Copy
Status: FIRED & ADJUDICATED (not passed-by-consensus)
Outcome: citations CONFIRMED CORRECT — NO CHANGE
Date: 2026-06-04 · Engine a21 / Heroku v160
Validators: GPT-5 + Gemini (independent, identical prompt) + Claude.ai primary-source adjudication

## 1. Scope validated
value_floor block + adjacent RICS surfaces on villa/house comparison outputs:
Sales-comparison approach (VPS 3 / IVS 103); land/HBU (VPS 2 / IVS 102); AVM/models
(VPS 5 / IVS 105); report/MUC (VPS 6 / IVS 106); VPGA 10; VPS 1 ToE; + the 3 disclosure
strings (land-floor note, implied-building note, condition caveat).

## 2. Validator verdicts
- GPT-5: PASS WITH FIXES. Hedged explicitly ("flag conservatively rather than assume");
  proposed replacing numeric citations with descriptive labels.
- Gemini: FAIL. Asserted "invented standard (VPS 6)", mischaracterised HBU, used pre-2025
  IVS numbering; proposed specific renumbered citations.
- DIAGNOSTIC: both AGREE with live copy on the two citations unchanged since 2022
  (VPGA 10, VPS 1) and DISAGREE on exactly the four RICS renumbered in 2025 → both reverted
  to the pre-2025 structure from training priors.

## 3. Adjudication vs RICS/IVSC 2025 primary sources
| Concept | Live (correct) | Model "fix" (rejected) | 2025 basis |
|---|---|---|---|
| Approach | VPS 3 / IVS 103 | VPS 5/IVS 105 or strip | RICS split old VPS 5 → VPS 3 (approaches+methods)+VPS 5 (models); IVSC moved old IVS 105→IVS 103 |
| Land/HBU | VPS 2 / IVS 102 | VPS 4 / IVS Framework | old VPS 4 (bases/assumptions)→VPS 2; IVS 102 = Bases of Value (holds premise/HBU) |
| AVM/models | VPS 5 / IVS 105 | IVS 104 / "no VPS" | VPS 5 Valuation models = new in 2025; IVS 105 = Models (IVS 104 = Data and Inputs) |
| Report/MUC | VPS 6 / IVS 106 | "VPS 6 doesn't exist" → VPS 3 | RICS: old VPS 3 (reports) IS NOW VPS 6 |
Sources: RICS red-book-global page (2022→2025 VPS mapping, verbatim); RICS Property Journal
(global-red-book-updates); IVSC/ICAEW/SAICA (IVS 2025 chapter list).

## 4. Decision
- Citations: NO CHANGE — live cites match the 2025 editions. Model fixes REJECTED (applying
  them mis-cites, e.g. VPS 5/IVS 105 for the approach = the *models* standard).
- Framing: 3 value-invariant tweaks ACCEPTED → B-1.1 (below). Citation numbers untouched.
- Condition stance: KEEP B-1 disclose-don't-assume; Special Assumption deferred to B-2.

## 5. Process learning → Operational Rule #54 refinement
For standards-NUMBERING questions on a freshly-revised standard, GPT/Gemini share a
stale-training blind spot; primary-source web verification GATES/TRUMPS the multi-AI pass
(inverted from the usual "models catch Claude's error" case). Run the web check first; treat
multi-AI as corroboration, not authority, on numbering.

## 6. Verbatim responses (appended by Anas)
### GPT-5
<paste>
### Gemini
<paste>
