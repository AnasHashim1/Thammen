# DESIGN NOTE — Stage / Authority Boundary

**Track:** 2.23.x output-mode architecture (organizing principle)
**Origin:** Rule #54 multi-AI validation of Sprint 2.22.0a.3 — GPT-5 adversarial critique
**Status:** Design input. Does NOT block 2.22.0a.3 (all forward-looking). For a dedicated strategic session before 2.23.x scoping.

---

## 1. The finding the textual honesty pass exposed

Sprint 2.22.0a.3 corrected *textual* over-claims (fabricated condition, MUC-vs-trend contradiction, "10-Year Rule," uncalibrated ±range). But a report's authority does not live in its text — it lives in its **form**. The following surfaces signal "valuation-grade output" pre-attentively, *before the user reads a single disclaimer*:

- The `🟢 شواهد كافية` confidence badge
- The decomposition: land/build split, cap-rate source, cost + income + market approaches
- A single exact QAR point estimate
- Per-year median structures + trend
- Clean, formal report formatting

**High-resolution decomposition implies confidence in the underlying evidence and calibration.** Resolving a value into components (land/build split, cap rate, three-approach reconciliation) signals "we have the resolution to do this" — a confidence the evidence may not support. The problem is not decomposition as such; *analytical* decomposition is legitimate. The problem is *unsupported* decomposition — fine-grained structure shown when the evidence cannot earn it. So textual humility layered over structural authority produces the real current failure mode:

> **Implied institutional standing.** The system never says "I am a valuer," but it *looks*, *behaves*, and *presents* like valuation work product. That is the surface most likely to attract regulatory or professional scrutiny — not blatant over-claim, but appearance-without-accountability.

This is a second axis of honesty the textual pass never touched: **structural / visual authority calibration.** The fix is not more disclaimers — it is the opposite: show *less structure and less numeric precision* when the evidence (and the stage) does not earn it.

---

## 2. The principle: authority signal must track stage + accountability

GPT-5's strategic conclusion was "don't imitate a valuation report with fewer disclaimers — build a different category (decision-support / market intelligence)." That premise (proximity to *valuation report* = liability + incumbent friction) holds **only for an unlicensed automated tool with no accountability behind it.**

It misses Thammen's structure. The 5-stage lifecycle terminates in **licensed-valuer Stage 5 sign-off** (and the Path A track toward holding that credential directly). The bridge from cheap automated estimation to *credentialed* valuation at volume **is the moat.** Retreating from valuation entirely would discard it.

So the correct reframe is not "retreat" — it is a **visible stage / accountability boundary:**

| Lifecycle stage | Accountability behind it | Authority register |
|---|---|---|
| 1–2 (quick AVM, interactive Q&A) | none — automated, unsigned | decision-support / evidence navigation |
| 3–4 (final estimate, broker field check) | partial — broker verification | qualified estimate, explicitly desktop |
| 5 (licensed-valuer sign-off) | full — professional, registered | formal signed-valuation standing, earned |

**The danger, stated precisely:** Stages 1–4 currently borrow the *appearance* of Stage 5 without its accountability. The liability is not that Thammen is *near* valuation — it is that the unsigned output looks like the signed one. The "we route to a real valuer at Stage 5" defense fails on perception/liability grounds if the unsigned estimate is visually indistinguishable from a signed report.

> **Design law:** the authority signal (visual + structural) must be honest about which stage the user is in. The unsigned estimate must *visibly* look less authoritative than the signed report.

This also makes accountability — not distance-from-valuation — the thing that gates authority. That resolves GPT-5's liability concern while preserving the strategy.

### 2b. Second coupled gradient: finality / reversibility

Authority is *how authoritative the output looks*. Finality is *how settled it feels*. They track the same stage axis but are distinct levers, and the second is as important psychologically.

- **Early stages (1–2) should optimise for exploration and reversibility** — outputs that feel adjustable, probabilistic, revisable, conversational. This is not a weakness to hide; it is the honest register for an unsigned estimate, and it maps directly onto the Stage 2 interactive Q&A surface (2.22.0b), which is *literally* a revisable, conversational recompute loop.
- **Stage 5 should feel finalised** — signed, frozen, attributable. Finality is earned at the point accountability attaches.

The failure mode to avoid is an *early-stage output that feels final*: a single frozen-looking QAR figure on a clean card reads as a conclusion, not an exploration, regardless of the wording around it. So the two gradients pair: dial authority **and** finality down together in early stages, up together only as accountability accrues.

**⚠️ CORRECTION (2026-06-05, measured — SUPERSEDES the 2026-05-28 "inert engine" claim below).** The
originally-cited "live evidence" was **wrong**, and is **retracted**. Re-tested live (a25 / Heroku v164,
browser-UA curl, Rule #61): the surface is **honest about interactivity — it is NOT inert.**
(1) The `عدّل المساحة (م²)` control sends **`override_land_area`** (not `area`), which **is accepted +
consumed** on both request models (`api.py:349/388` → `evaluate_unified.py:3324` `plot_area_override`):
56/565/21 **2.4M → 4.3M** at override 600 m² (`user_override_applied=true`). It is the shipped Sprint
2.21.0.9 multi-QARS override.
(2) The optional property-details form posts to **`/api/evaluate/details`** (not `/api/evaluate`), where
**every** field — floors / condition / building_age_years / is_luxury / footprint_m2 / basement / annexes /
asking / rental / unit-pair — is **declared (`EvaluateDetailsRequest` `api.py:373-406`) + consumed
(`api.py:1041-1046`)**: condition+floors+basement → **2.4M → 2.8M** (HTTP 200, no 422).
The 2026-05-28 test hit the **wrong endpoint** (`/api/evaluate`, which legitimately doesn't declare detail
fields) with the **wrong override name** (`area`, not `override_land_area`) → the "rejects every field / dead
field / completely inert engine" reading was an **artifact**, not the surface's behaviour. **So "entering
property details adjusts the estimate" is true today — there is NO interactivity over-claim to fix; the
`عدّل المساحة` field and the T2.5 "details may adjust" copy are honest.** The Stage-1 input-honesty sprint
that acted on this stale claim was **closed as premise-falsified** (CHANGELOG_v78 / Session_Log §20.26).
Full recon: `docs/PHASE0_B2_condition_recon.md`.

> **The real, separate finding** (recon §3): those inputs are **mis-calibrated**, not absent — only building
> SIZE (floors→BUA, +25%-capped, upward-only) moves the headline; condition / finish / age contribute zero →
> **R7 = calibration + missing-mechanism (Sprint B-2)**, not an interactivity gap.

**What SURVIVES (the valid theme — keep + route to Stage-2 design):** the finality/authority point above
(§2b paras 1–2) stands entirely on its own and is **unaffected** by the retraction. An early unsigned
estimate that **visually feels final/authoritative** — a single frozen QAR figure on a clean card reading as
a conclusion — is the genuine early-stage honesty gap. That is a **Stage-2 / 2.23.x VISUAL-calibration** item
(dial authority + finality *down* in early stages) → **routed to the Stage-2 design session**, NOT a copy or
field fix.

### 2c. Root principle: user-facing copy must be *derived from* engine truth, not *authored* alongside it

The deepest pattern behind every honesty gap this season is structural, not incidental. In the methodology-line case (Sprint 2.22.0a.4 Phase 0), the engine's **internal** comments were honest from the start of the architecture — `# Primary valuation (from comparison approach only)` and `# Cross-checks (explicitly labeled as such, NOT in valuation)`. The lie lived **only in the user-facing string** (`توفيق ثلاثي الطرق` — "three-way reconciliation"), which claimed a blending mechanism the code never had. The engineering truth was correct and documented; the presentation layer drifted away from it and stayed wrong for months.

This is the common root of the entire season's honesty findings — they are all the *same failure class*, presentation drifting from engine reality:

- **Fabricated condition** (`بحالة جيدة`) — engine had no condition input; copy asserted one.
- **`Mzad` in the source list** — engine excludes Mzad; copy listed it.
- **`توفيق ثلاثي الطرق`** — engine is single-approach; copy claimed three.
- ~~**Dead area field + T2.5 "details may adjust"** — engine accepts no such input~~ → **RETRACTED 2026-06-05 (measured):** the engine **does** accept + consume these inputs (`override_land_area` + the `/api/evaluate/details` fields). Ironically the *design-doc claim itself* drifted from engine truth (wrong endpoint + field name) — a §2c violation **by this note**, now corrected in §2b. The real gap is **calibration** (the inputs are mis-sized — only building SIZE moves the value), not a missing input → Sprint B-2.

**The principle:** user-facing copy describing *what the system did* must be **derived from the engine's actual behaviour at render time**, not written independently and maintained by hand. Hand-authored copy decays silently against an evolving engine — there is no test that fails when prose and behaviour diverge, so the gap is invisible until a user (or a ground-truth case) hits it. The structural fixes that follow from this: copy that asserts a method, an input, a data source, or a confidence level should read its claim from the same field the engine computes from (the T-method `reconciliation['status']`-aware string is the first instance of doing this right), and GONE-style sentinels should assert against the *rendered* surface, not source substrings (E14 appendix). Where copy genuinely cannot be derived, it must be the narrowest honest statement the engine can stand behind.

This principle outranks the authority/finality work in importance: authority calibration tunes *how much* the system presents; derive-don't-author governs whether what it presents is *true*.

---

## 3. Reframe of the 2.23.x output modes

The original framing was *audience* modes (Consumer Snapshot / Analyst View / Institutional Draft). The sharper organizing axis is the **stage/accountability gradient + evidence quality** — not merely who is looking.

The existing confidence-tier taxonomy already encodes this latent gradient: *indicative estimate → analytical range → broker-verified range → signed valuation.* **2.23.x should make the visual authority match the tier label** — today the label is humble but the visuals are not.

Per-mode design implications:

- **Consumer Snapshot (≈ Stage 1–2, exploratory):** lead with a *range*, not a point estimate; minimal or no decomposition; evidence-count forward ("based on N nearby transactions"); recalibrate or remove the binary high-confidence badge (e.g. `🟢 شواهد كافية`); no formal-method labels; presentation should feel adjustable/revisable rather than concluded.
- **Analyst View (≈ Stage 3):** decomposition available, but explicitly framed as exploratory desktop analysis.
- **Institutional Draft (≈ pre-Stage-5):** full detail, clearly marked *draft pending licensed sign-off.*
- **Signed (Stage 5):** full formal RICS/IVS framing, frozen and attributable — legitimate, because backed.

**Evidence-quality coupling (within any mode):** dial structure down when evidence is thin — same instinct as the queued GPT-B multi-factor suppression gate, applied to *structure*, not just the trend decimal. Thin evidence → fewer components shown, wider band, less precision.

---

## 4. Open strategic fork (Anas decision)

**Retreat-from-valuation (GPT-5's read) vs. enforce-visible-stage-boundary (recommended).** The latter preserves the moat and converts the liability into a gated-authority design problem. Interacts with Path A timing: as real Stage 5 sign-off capacity comes online, the boundary can move outward. Worth a dedicated session before 2.23.x scope is locked.

---

## 5. Linked / queued items (not this note, but same theme)

- **GPT-B multi-factor evidence-adequacy gate** — suppress on sample adequacy + inference confidence + district volatility, not just freshness/level. Pre-MoJ-refresh trigger. Same "structure tracks evidence" instinct.
- **`توفيق ثلاثي الطرق` methodology phrase** → RESOLVED into Sprint 2.22.0a.4 T-method. Phase 0 traced `_analyze_reconciliation`: it is a *status reporter*, not a blender — value is always Sales Comparison alone; cost/income only generate convergence commentary. So the phrase was misdescriptive (no reconciliation of the value, not three-way), IVS 105 anchor rejected, replaced with a derived "basis + check" string. First production instance of §2c (derive-don't-author).
- **Disclaimer bucket separation** (MUC reservation vs. non-formal-report provenance stay distinct) → 2.22.0a.4 T2.8.
- **Maamoura old-premium case** (`docs/learnings/LEARNING_2026-05-28_maamoura_old_premium.md`) — ground-truth case behind the §2b interactivity evidence and the H-A "building over-credit on old stock" hypothesis; feeds the GPT-B evidence gate and Confirmed Sales DB (2.16.16).

## 6. Non-goals

- Not a disclaimer-addition exercise — the inverse (reduce structural authority).
- Does not gate the 2.22.0a.3 push.

---

*2.23.x is now quadruple-validated for need: original GPT-5 strategic feedback (DESIGN_2p23_VALIDATOR_FEEDBACK.md) + the 2.22.0a3 GPT-5 critique (this note) + earlier Gemini overlap + the standing brief. Design requirement, not opinion.*
