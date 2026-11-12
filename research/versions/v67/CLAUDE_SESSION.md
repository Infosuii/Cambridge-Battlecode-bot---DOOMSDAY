# Claude continuation, 2026-10-27 (after GPT's usage limit)

Goal unchanged: v67 ≥ 220/240 against unmodified v65 on the fixed schedule, **on seeds that were not used to pick it**.
Nothing in this session touched `bots/v67`, `bots/v65` or `bots/mimic`. All candidates are flat copies under
`artifacts/tmp/v67/c-*`; all runs are `artifacts/evaluations/v67/c*` (raw_run.py output, not appended to RESULTS.md).

## What is established

- GPT's frozen 220/240 portfolio is seed-overfit (137 on untouched 3/4 and 7/8). Its `NOVA_SEED` "seeds" are the
  bots' own RNG, so per-map policy choice from seeds 1/2 fits noise.
- The honest baseline is the b06 source (`artifacts/tmp/v67/c-b06`): 137 (s1/2), 123 (s9/10), 119 (s11/12),
  125 (s13/14). Seed-pair noise is about ±10 wins. **Compare variants only against a same-seed baseline.**
- GPT's last "real" fix, persistent bush entry (p59b, 145 on s1/2), scored 121 on s9/10: not a gain.
- Pooled over 7 comparable runs (`tools/v67/c_cells.py`): 26 games/240 sit in structurally lost (map, side) cells,
  40 structurally won, **174 are seed coin-flips**. 220 needs real strength in the mirror, not per-map fixes.
- Snowball (`c_snowball.py`): the side ahead in gold at R250 wins 75%, at R600 82%.
- Deaths (`c_death_batch.py`, `c_death_modes.py` with `APEX_DEATHLOG=1`): ~15 per team per game, 12.5 gems each;
  **75% of our deaths happen in mode `flee`**, 83% below 30% HP, 71% with an enemy within 2, 54% no ally within 4.
- Per champion (`c_by_type.py`): Vendetta decides games (6.8 kills / 1.9 deaths in our wins vs 3.2 / 4.2 in losses).
- 02guardians: one altar, reachable only through two gate-camp tiles; the side that holds the gate wins. Map
  control, not a bug.

## Variant results (all vs v65, 240 games, zero faults)

| Run | Change | Seeds | Wins | Same-seed base |
|---|---|---|---:|---:|
| c04 / c05b | LABK24 alive weight −1.5 / +1.5 | 11/12 | 126 / 122 | 119 |
| c06b / c07 | LABK30 decide margin −0.6 / +1.0 | 11/12 | 125 / 126 | 119 |
| c10 | APEX_STAND=7 (stand when caught) | 13/14 | **57** | 125 |
| c11 | APEX_STAND2=3 (melee caught) | 13/14 | **61** | 125 |
| c12 | both | 13/14 | **49** | 125 |
| c13 / c15 | A2_TEAMFIGHT=2 / NOVA_FIGHT2=4 (regroup flee) | 13/14 | 99 / 99 | 125 |
| c14 | APEX_ESCAPE_SEARCH=1 | 13/14 | 121 (fuel 544) | 125 |
| c16 | A2_TEAMFIGHT=3 | 13/14 | 107 | 125 |
| c17 | A2_ASSESS=1 | 13/14 | 84 (fuel 3106) | 125 |
| c18 / c19 | APEX_PAIR=1 until R300 / all game | 13/14 | 118 / 116 | 125 |
| c20/21/23 | APEX_DANGER_TTD 9 / 13 / 4.5 | 13/14 | 125 ×3, identical to base: the macro has no effect | 125 |
| c22 | APEX_DANGER_HP 0.35 | 13/14 | 132 | 125 |
| c24 / c25 | new C67_CARRY_FOCUS 1 / 3 (target enemy Vendetta) | 13/14 | 127 / 128 | 125 |

| c26/c27 | base / combo1 (carry 3 + DANGER_HP 0.35) | 15/16 | 124 / **143** | — |
| c28 / c29 | LABK22 melee aggression −1.2 / +1.2 | 15/16 | 113 / 107 | 124 |
| c30-c33 | base / combo1 / combo2 (carry 6) / combo3 (carry 3 + DANGER_HP 0.45) | 17/18 | 106 / 124 / 122 / **134** | — |
| c34-c39 | base / combo3 / DANGER_HP .55 / .65 / combo3+THREAT_RETREAT .55 / combo3+TRIBUTE_CARRY 40 | 19/20 | 121 / 111 / 118 / 121 / 123 / 118 | — |

Pooled over three seed pairs the survival tweaks (carry focus, earlier low-HP flee) are worth roughly +5..+10
wins, not the ~+95 needed; paired-difference noise between seed pairs is ±15. Note: `kDangerTtd` and
`kTributeCarry` are rescaled every turn by the baked A2_KNOBS (bot.cpp ~6578), so their macros are inert.

Standing (c10-c12) shows the fight layer has big leverage: our deaths 15.2→20.5, theirs 15.2→11.0, a ~5-death swing
worth ~70 wins. Every existing switch of the v65 toolbox tested so far is at or below its tuned default.

## Tools added (tools/v67)

`c_trace.py` (one traced game, any side/seed), `c_variant.py` (copy + macro/knob overrides), `c_batch.py` (parallel
raw runs), `c_compare.py`, `c_cells.py`, `c_banking.py`, `c_deaths.py`, `c_snowball.py`, `c_summary.py`,
`c_by_type.py`, `c_death_context.mjs` + `c_death_batch.py` (engine-2 replays; needs NFS_REPLAY_ENGINE=2.0.0, set by
the batch script), `c_death_modes.py`. `tools/proxy/local_duel.py` now tolerates two runs caching the same wasm.
