# ⚠️ DEPRECATED — STALE upload bundle (frozen 2026-05-22, Heroku v91)

**Do NOT upload from this folder.** The renamed copies here froze at Sprint
2.21.0.7.1 / Heroku **v91** and are now far behind production (current state:
see `CLAUDE.md` snapshot + `/api/health`). They are exactly the drift the
original staging note warned about ("regenerate from `docs/` or they drift") —
and they drifted ~30+ sprints.

## Current upload workflow (lean two-lane model)

Upload the **canonical `docs/` files directly** — **no renamed copies are
maintained here anymore**:

- `docs/Custom_Instructions.md`  ← lane-leading (Claude.ai reads this first)
- `docs/Project_Instructions.md`
- `docs/Session_Log.md`
- `docs/Empirical_Findings.md`
- `docs/Operational_Rules.md`
- `CLAUDE.md`

The `docs/` files are the **single source of truth** (Rule #58: live
engine / sprint / Heroku-vN = the CLAUDE.md snapshot + `/api/health`). The
three stale snapshots in this folder (`Project_Instructions_v5.md`,
`Empirical_Findings_v3.md`, `Session_Log_2026-05-17_to_22.md`) are retained
only as a 2026-05-22 historical marker and can be deleted.

---

*Original 2026-05-22 staging note (historical):* these were point-in-time
snapshots of the `docs/` files, renamed for manual upload to the Claude.ai
Project Knowledge store, covering through the Land Arc (Sprints 2.19 → 2.21.0.7.1,
Operational #45–#49, Empirical E8–E14, engine `…2p21p0p7p1`, Heroku v91).
