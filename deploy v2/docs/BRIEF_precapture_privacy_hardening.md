# BRIEF — Pre-Activation Capture Privacy-Hardening (beta)

> **Gate:** Rule #32 sign-ready. Scope = **dormant a15 capture schema + `index.html` terminology**. **NOT activation.** Origin + Heroku per routine; capture stays inert (no flag, no `DATABASE_URL`, no add-on).
> **Author:** Claude.ai (analyst lane). **Owner:** Anas (PO — Rule #32 sign-off). **Implementer:** Claude Code.
> **Provenance:** multi-AI legal triangulation (Claude/Gemini/GPT, `MULTI_AI_VALIDATION_BATCH_PDPPL_beta.md`) + the Claude-advisor pass on the counsel brief. These four changes **reduce data-protection risk regardless of how the open legal questions resolve** — and are cheaper to make while the capture is dormant than after activation.

## Why this matters

Activation of the a15 capture is gated on counsel (§8.1 PDPPL policy + §8.2 cross-border + the two written-sign-off items: **Q14 Aqarat**, **Q8 residual scope**). None of that blocks making the *dormant* capture privacy-sound now. This brief implements the design changes the three AI passes converged on, so that when counsel clears the gates the capture is already built to the defensible shape.

## Scope — 4 items

### 1. De-embed the address from `valuation_id` (storage schema)
- **Today:** `valuation_id = THM-{ts}-{zone}{street}{building}` (generated `evaluate_property.py:1892`); it **embeds the address**, and the dormant a15 prediction schema would persist it → the address is duplicated inside the join key, defeating the §8.3 UUID surrogate.
- **Change (dormant schema only):** the UUID `id` is the **sole** stored surrogate key. Persist the address (`zone`/`street`/`building`) as **one separately-redactable, encrypted column**. Do **not** persist the address-embedding `valuation_id` as a stored field — keep it only as the returned display string, or store a non-address hashed reference if a join is needed.
- **Recon:** confirm the `valuation_id` generation site + exactly how the dormant `instrumentation.py` schema references it.
- **Backward-compat:** the prod `valuation_id` **string in the API response is UNCHANGED** (display only). This touches only what the dormant store *would* persist.

### 2. Disable / hard-restrict the free-text `note` (schema + future UI)
- **Why:** unanimous across all three AIs + the advisor's [PRIORITY] read — free text can capture **special-nature** data (Article 16 → prior permission) and **third-party** data the user cannot consent for (the agent-valuing-a-non-owned-property case). Biggest single risk + largest erasure burden.
- **DECISION (Anas):** **(a) DISABLE the `note` field for beta** *[analyst lean — cleanest risk removal]*, or **(b) RESTRICT** to structured options + a hard warning ("do not enter names, IDs, phone numbers, or any information about other people").
- **Change:** per the decision — drop `note` from the dormant feedback schema (and the future feedback UI), or gate it behind the structured-constraint + warning.

### 3. Retention design — per-record during the consented window → aggregate residual (the Q8 implication)
- **Why:** the advisor's sharp point — a retained per-record `zone + value + timestamp` (especially `+ transacted price + date`) is **re-identifiable by cross-referencing the public MoJ dataset Thammen is built on** (price/zone/date can pin the specific villa/parcel → owner; higher risk for low-density villas/land). **Dropping street/building does NOT make the residual "anonymized / out of scope."** *(This is one of the two items the advisor flagged for written counsel sign-off — but the safer default is buildable regardless.)*
- **Design (preserves the capture's purpose):**
  - Per-record prediction/feedback rows are retained **only during the active, consented accuracy-measurement window** (legitimate purpose = measuring AVM accuracy vs. actuals; short retention, ~90–180d — see decision below). Per-record is *fine* here — it's the point of the capture.
  - **After the window**, residual-for-tuning is reduced to **zone-level aggregate distributions** — **not** per-record `zone+value(+price)` rows. The identifying columns are dropped at that point.
- **Implement (dormant):** schema carries `created_at` + a retention/expiry field; spec a (dormant) **aggregation+purge job** that post-window collapses per-record rows to zone-level aggregates and drops the identifying columns. The **erasure path must reach backups** and any legacy address-embedding IDs (per Q9).

### 4. UI terminology — "Automated Market Estimate" not "Valuation"
- **Why:** Aqarat-defensive (Q14). "Valuer/AVM provider" is **not** in Aqarat's enumerated licensing list (developers/brokers/agents/community/building managers), so the not-a-certified-valuation framing + "market estimate" terminology gives the best chance of staying outside the licensing perimeter. Cheap; worth doing regardless.
- **Change:** `index.html` user-facing surfaces — where the output is *labelled*, replace the "Valuation / تقييم" framing with **"Automated Market Estimate / تقدير سوقي آلي"** (NOT the methodology disclaimer line, NOT the RICS VPS/IVS labels — those are separate and stay). Keep the existing "decision-support, not a certified valuation" disclaimer.

## Out of scope (explicit)
- **NOT activation** — capture stays dormant; gated on §8.1/§8.2 + counsel-written **Q14** (Aqarat) and **Q8** (residual scope).
- **NOT the security baseline** (TLS / at-rest encryption / least-priv / audit logging / backups / processor DPA) — that lands **with activation** as gate 11.
- **NOT the third-party-owner consent handling** (Q1 new point) — routes to the **consent/notice + Sprint-2 UI** workstream, not this capture brief.
- **NOT the privacy notice / consent flow** — separate workstream (Gemini draft + counsel review).

## DoD
- `py_compile` on every modified `.py`; `node --check` on extracted inline JS if `index.html` JS is touched.
- Isolated tests for the schema changes + the dormant aggregation/purge spec (valid path · purge collapses to aggregate · erasure reaches the address column + legacy IDs).
- DoD regression green per the CLAUDE.md matrix; **4 anchors byte-identical** (capture still dormant → valuation outputs unchanged).
- `index.html` mobile **390×844** check for the terminology change.

## Decisions for Anas (Rule #32, before CC builds)
1. **Free-text `note`:** DISABLE for beta *(lean)* — or RESTRICT-with-warning?
2. **Retention window:** 90 days or 180 days for the per-record measurement window?
3. **Terminology Arabic wording:** "تقدير سوقي آلي" — or defer the exact Arabic to the Arabic-surface pass (keep English label change now)?

---

*Pre-activation hardening only. Activation remains counsel-gated. Pairs with `MULTI_AI_VALIDATION_BATCH_PDPPL_beta.md` and `Thammen_Counsel_Brief.docx`.*
