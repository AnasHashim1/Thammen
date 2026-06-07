# PHASE0 — «النطاق كصدارة» (range-as-lead) — recon (read-only)

> **thin-flow step 2** (v4 owner-journey, §2b authority/finality dial-down). **NO engine change, no deploy.**
> Engine stays **2.22.0b.2.3 / Heroku v169** (byte-identical). Handshake (#57): `/api/health` =
> `3.1.0-sprint2.22.0b.2.3`, qars healthy, MoJ 158d, `master == origin` @ `a6796ff`. Measured live via
> browser-UA curl (Rule #61) + read of `index.html` / `evaluate_unified.py`.
>
> **Purpose:** feed the Claude.ai range-as-lead **brief** with code-measured facts BEFORE it is drafted —
> the same recon-reshapes-the-brief discipline that re-shaped b2 / b2.1 / b2.2 / b2.3 (§20.26/§20.29/§20.32).
> **This recon does NOT design or decide** — it surfaces the constraints; the design + copy stay **Gate-2**
> (Anas + Claude.ai), and one item below is a genuine framing fork that needs the signature.

---

## 0. The decision as it stands (snapshot)

CLAUDE.md #65a / Custom_Instructions: *step (2) = range-as-lead [§2b dial-down — **symmetric ± bar, NOT the
rejected land-to-median**]*. This recon tests that phrasing against the live data. **Headline finding: the
"symmetric ±" half is falsified by the engine's own ranges — see §1.** The "NOT land-to-median" half is
re-confirmed sound (see §4 value_floor interaction).

---

## 1. 🔴 Finding 1 — the range is **structurally ASYMMETRIC** on thin/widened paths (measured)

Live `/api/evaluate` (4 anchors, this session). `ASYM` = `(high−amount) − (amount−low)` as % of amount:

| PIN | method | tier | low | **amount (median)** | high | lower gap | upper gap | **ASYM** |
|---|---|---|---|---|---|---|---|---|
| 56/565/21 | comparison_bracket | high | 2,200,000 | **2,400,000** | 2,600,000 | 200,000 | 200,000 | **+0.0%** (symmetric) |
| 54/541/6 | comparison_thin | medium | 4,900,000 | **5,400,000** | 5,500,000 | 500,000 | 100,000 | **−7.4%** |
| 55/296/13 | comparison_thin | low | 2,000,000 | **2,600,000** | 2,600,000 | 600,000 | **0** | **−23.1%** |
| 52/903/90 | insufficient_data | — | None | None | None | — | — | refusal (no range) |

**Read this carefully:** on the clean bracket path the range IS symmetric (±200K). But on `comparison_thin`
the **median sits at or near the HIGH** — on 55/296/13 `amount == high` exactly (upper gap = 0), and the whole
range is a one-sided downside `[2.0M … 2.6M]`. This is **deliberate engine conservatism** (the thin/widened
estimate is capped at the median; the honest spread is downward).

**Implication for the brief (the fork):** a literal **"symmetric ± bar"** would, on 55/296/13, draw ±300K
around 2.6M = `2.3M – 2.9M` — **inventing a 2.9M upside the engine explicitly refuses** (it set high = 2.6M).
That is the same "unsupported / authority-overstate" failure family this whole arc exists to AVOID. So:

> **Recommendation (Gate-2 — Anas/Claude.ai sign):** render the **engine's ACTUAL low/high (lopsided allowed)**
> + a **median marker in its true position** (which may sit at the high edge on thin). Do **NOT** normalize to a
> symmetric ±. The visual can still be "a horizontal bar with a marker"; it just must not be forced symmetric.

This is precisely what `showConfirm` already does (§3) — so the safe design already exists and was R14-passed.

---

## 2. 🟢 Finding 2 — `range_is_headline` (a10/a14) is **set by the backend but NEVER consumed by the frontend**

`grep range_is_headline index.html` → **0 matches.** The a10 (widened) + a14 (dispersed-bracket) honest-range
work sets `range_is_headline=True` server-side, but `index.html` never reads it — `show()` renders the **point**
as the headline (`index.html:1189`, `.rv hl` 1.5rem) on **every** path, with the range demoted to a secondary
two-box `.rg` card (`:1190-1192`). So the backend's "the range is the honest headline" intent **does not reach
the screen**.

> **This is the gap range-as-lead closes.** It is therefore **not a new feature** — it is *wiring the existing,
> signed `range_is_headline` signal to the visual headline* + generalizing it. That framing (a) lowers risk,
> (b) ties step-2 to already-signed a10/a14 methodology, (c) gives a natural gate: lead with the range when
> `range_is_headline` (dispersed/widened) and/or as the new default — a scope question for the brief.

(Note: 54/541/6 is now `comparison_thin` post-a18, not `comparison_widened`, so it carries `range_is_headline:
None` — correct: thin is gated by the weak-sample caveat, not by a10/a14. The grep result is the load-bearing
fact: the field is unconsumed regardless of path.)

---

## 3. 🟢 Finding 3 — the approved prototype already ships: `showConfirm` (b2.3, `index.html:700-735`)

The confirmScreen (v169, R14-passed) **already renders the range-as-lead headline** we want, and already
solves Finding 1:

```
:705  <div class="cg-est"><div class="cg-lbl">تقدير مبدئي (نطاق)</div>
:706  if(v.low!=null && v.high!=null){
:707    cg-range = fmt(v.low)+' – '+fmt(v.high)+' ر.ق        ← range is the big headline
:708    if(v.amount!=null) cg-mid = 'الوسيط ≈ <b>'+fmt(v.amount)+'</b> ر.ق'   ← median as a muted marker
:710  } else { cg-range = fmt(v.amount) }                    ← graceful point fallback
:712  cg-sub = 'تقدير أوّليّ قابل للتغيّر…'
```

It uses the **raw (lopsided) low/high** + the median as a text marker — i.e. it does NOT force symmetry, exactly
the §1 recommendation. CSS classes `.cg-est / .cg-lbl / .cg-range / .cg-mid / .cg-unit / .cg-sub` exist and are
mobile-verified.

> **Recommendation:** the results card adopts the **showConfirm pattern** (range headline + muted median marker
> + point-fallback). Design effort drops from "invent a ± bar" to "apply the signed, shipped pattern to the
> results valuation card." If a graphical bar is wanted over the text range, it is an additive visual on top of
> the same low/high/median data.

---

## 4. Current results headline + the swap point (`show()`, `index.html:1177-1213`)

```
:1181  card «التقدير السوقي»
:1185  tier badge («نطاق تحليلي»)
:1189  ★ HEADLINE NOW = «القيمة التقديرية» fmt(v.amount), .rv hl 1.5rem      ← the POINT-as-lead
:1190  secondary .rg two-box: «الحد الأدنى» fmt(v.low) / «الحد الأعلى» fmt(v.high)
:1194  condition_note_ar (a17/a19)                — keep, under the range
:1196  value_floor block (B-1)                    — keep, SECONDARY (see below)
:1205  moj_sample_size
:1213  evidencePanelHtml (b2.2)                   — keep, unchanged
```

**The change is the 1189↔1190 swap** (range becomes the large headline, median a muted marker), nothing else
in the card.

**Critical interactions (for the brief):**
- **value_floor / B-1 (`:1196`)** stays a SECONDARY muted block under the range. This **confirms the "NOT
  land-to-median" half** of the decision: the lead is the **market range**, never the land floor. ✓ consistent.
- **evidence panel / b2.2 (`:1213`)** unchanged — range-as-lead touches only the headline, not the quality panel.
- **range_expansion (`:1361-1377`)** already prints *"النقطة المركزية محافظة (وسيط المقارنات)؛ الحد الأعلى
  يَتسع…"* — existing copy that **describes the asymmetry**. Fully consistent with showing the true (lopsided)
  range; the brief should reuse/echo this framing rather than contradict it.

---

## 5. Edge cases

- **Refusal (amount=None, e.g. 52/903/90):** `hasValuation=false` → the headline block (`:1189-1192`) never
  renders → range-as-lead is a no-op. ✓ no special handling.
- **thin median==high (55/296/13):** the median marker sits at the high edge; the bar is all-downside. The
  design MUST allow this (it is the honest picture) — see §1.
- **raw_land:** **NOT verified this session** — the test PIN (74328443) returned `asset_type/method/amount =
  None` (likely a stale/invalid PIN, not a code issue). Land carries an analytical range too and would inherit
  range-as-lead; **confirm on a valid land PIN before build** (Rule #36 — observed-vs-not-seen).

---

## 6. Net recommendation to the Claude.ai brief

1. **Re-frame step 2** from "symmetric ± bar" → **"lead with the engine's true range + median marker"**
   (the showConfirm pattern). The literal *symmetric* claim is falsified (§1) and would invent upside on thin.
2. **Wire `range_is_headline`** (already set by a10/a14) to the visual headline — frames step 2 as completing
   signed work, not new methodology (§2).
3. **Reuse the showConfirm prototype + `.cg-*` CSS** (R14-passed in v169) on the results valuation card; the
   only edit is the `:1189↔:1190` swap (§3/§4).
4. **Keep** value_floor secondary (confirms "NOT land-to-median"), evidence panel + condition note unchanged.
5. **Scope = frontend-only, value-invariant** (engine version-string bump only) — same class as b2.1/b2.2/b2.3
   (4 anchors byte-identical expected). `api.py` untouched.
6. **multi-AI (#54):** the genuine question for GPT-5/Gemini = *"how to lead with a range without implying false
   precision, and whether to keep the point visible as a central-estimate marker (RICS) or drop it"* — a
   **framing** call. NOT a standards-numbering question → no web-check-gating needed (contrast B-1 D3).
7. **One open fork for the signature:** show the median marker **always** (transparency / RICS central estimate)
   vs only-on-symmetric — recommend **always**, positioned truthfully (§1).

**Verification owed at build (per the arc):** isolated test (reads real `index.html`), DoD broad +1, **R14 real
Chromium** (390×844 — the bar + marker, thin all-downside case, refusal no-op), live 4-anchor byte-identical
smoke (#61), `/api/health` version bump only.

---

*Read-only recon. Engine UNCHANGED (a25-era invariant holds: v169 byte-identical). Scratch probes `.rl_*.json` /
`.rl_probe.py` are regenerable (gitignored-class, untracked). Ball: Claude.ai drafts the range-as-lead brief
using §6.*
