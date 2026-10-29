# Fundamentals log — 2026-10-29 (Claude session, continued)

Per-agent, round-by-round diagnosis drives each change. Every run below is a
140-game pool (70 maps × both sides) unless marked trace. Paired SE is the
standard error of the per-cell banked difference; ~10 gems on these pools, so
treat |delta| < 2 SE as noise. Comparisons are against the named base run.

## Tooling added

- Trace builds: `DZ_FIGHT` (enemy-visible turns, incl. enemy strength in reach),
  `DZ_TIME` (per-body time by activity every 250 rounds), `DZ_PLANNER_FUEL`,
  and a per-round goal/executor window for one body
  (`--set DZ_TRACE_SLOT=… DZ_TRACE_FROM=… DZ_TRACE_TO=…`).
- `tools/dz.py smoke --candidate-bot NAME`: benchmark an existing bot as the
  candidate (evaluation only; no code enters bots/dz). `bench-v65-idle-01`.

## Findings and changes, in order

| Step | Evidence | Change | Result |
|---|---|---|---|
| Contested deaths | v65 pool: 14.2 champion-kill deaths/game vs 0.3 kills; 111/119 traced deaths during Retreat | `fight.h` focus-fire simulator; Fight goal | `dz-fight-v65-01` (retreat at range+3): deaths −2.7 but banked −24.7 (SE 9.2); `-02` (retreat at reach only): −16.6 (SE 9.5) |
| Calibration | `dz-fight-trace-v65-02`: HP loss ≈ 0.76 × visible enemy strength in reach per round | none; enemy damage not underestimated | — |
| Executor bug | pre-move target only saw enemies already in range: a melee approach never hit | re-pick enemy in reach after moving | `dz-fight-v65-03`: kills 0.7→1.2/game, damage dealt +8% |
| Capture abandonment | `dz-window-idle-02`: Vesper released a capture one round before completion (6-round window vs 5+1 capture) | standing on own reward group is progress (bounded) | `dz-capture-idle-01`: neutral (rare) |
| Economy gap | `bench-v65-idle-01`: v65 vs idle 43/161/421 banked at R100/250/500, 1000 in 928 rounds; DZ 40/134/307; 65% of DZ body-turns are travel; v65 takes 7.7 vs 4.5 20–39-gem groups by R500 | — | — |
| Respawn waiting | champions walked 26 tiles past clusters about to respawn | price known respawns at max(travel, wait) | `dz-wait-idle-01/02` (60-round horizon): R100 halved; champions sat out full 50-round respawns of gold-only groups. `-03` (≤15 rounds, gem groups only): R250 +14.5, R500 +18.6 (80 better / 36 worse) |
| Draft | v65 Varg 38.9 camp dmg/round vs our Heart of Ruin 8.2 | Vendetta, Varg, Marcella/Vesper first | `dz-draft-idle-01` neutral (+10.6, SE 11.9); `dz-draft-v65-01` (all changes) **235.0 banked vs 200.3, +34.7 (SE 10.3)**, kills 1.6/game |

Retained failures: `dz-fight-v65-01/02`, `dz-wait-idle-01/02`, the 60-round
respawn horizon and spawn-tile exclusion for alive groups (blocked approaches).
