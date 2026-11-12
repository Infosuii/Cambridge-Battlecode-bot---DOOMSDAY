# Resume prompt (paste into a new agent session)

Continue the DOOMSDAY Battlecode cycle from the v118 root-cause handoff. Read `v118-rootcause/FINDINGS.md` first, then `release-protocol.json`, `holdout-result.json` and `confirm-fresh-result.json`.

State: v117 (hp01) is the last recorded ladder version. The v118 candidate `v18HDR` = v117 + H (Homonoliths home siege) + D (relaxed bridge dash) + R (route veto of neural overrides). It fixes both targeted incidents in release builds, but the sealed holdout strength gate G4 failed (−4/720; a fresh 2,304-game report-only set came out at exactly 0). The package is `release/v18HDR`, marked not approved. Do not submit to the ladder without an explicit user decision. Recheck the active version (`cambc submissions list --json`, after the user runs `cambc login`) and teammate branches first.

Tooling (run from `v113-integration-20261108/`, Python 3.13 with numpy and torch 2.11.0+cu128):
- `python v118-rootcause/candidates.py`: rebuild H/D/R/N/O variants from hp01 (L and HDRL through `candidates.build(name, letters)`).
- `python v118-rootcause/dev_panel.py <label> hp01,<cands>`: paired development panel on the 88 dev maps (never the holdout).
- `python v118-rootcause/incident_checks.py`: release-build Homonoliths capture timing and Islands stall audit.
- `python v118-rootcause/activation.py <maps>`: debug activation counts of H/D/R.
- Trace scripts: `trace_objectives.py`, `crew_test.py`, `trace_outnumbered.py` + `outn_deaths.py`, `trace_islands*.py`, `map_census.py`.
- Training: `train_v118.py` (env vars in FINDINGS §5); `weights_arms.py` for the four-arm comparison.
- `qualify_v118.py <cand>` runs the sealed holdout. It has been opened once already; any new selection needs a fresh set.

Open next steps:
1. User decision: ship v18HDR as a targeted-fix release (expected gain only on Homonoliths/Islands, collateral about 0 on 2,304 fresh games) or keep v117. If shipping, use `deliver_cycle.py`-style receipts and pin/verify, and record the previous version.
2. Banking: trace the carrier decision in local race losses where the bag covered the deficit (53/372) before changing carry or endgame thresholds.
3. Swirl: needs an opponent that reproduces the upgraded-carry dive; the numbers gates are Parked.
4. Divergence noise: ≥2,000 paired games are needed to resolve about 1 pp. Consider deterministic-fuel-neutral gating if a future fix must be measured off-target.
