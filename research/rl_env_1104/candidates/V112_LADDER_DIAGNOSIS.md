# v112 ladder diagnosis (2026-11-08)

**Data.**
- v112 (agentic-1108:auto_bank_arrive_learned, WASM 932030e0) went live at 05:23 UTC.
- Ranked games 05:25–16:20 UTC: 330 matches, 320 official summaries and 330 replay bundles downloaded.
- Decoded with the pinned engine-3 visualiser: `tools/replay3` and `tools/rl_env_1104/strategy/decode_ladder_replays.py`.
- Tools: `ladder_breakdown.py`, `ladder_deaths.py`, `ladder_idle.py`, `mode_idle.py`, `clear_capture.py`.

**Standing.** DOOMSDAY is rank 41, rating 2206. Win rate by live version (ranked):

| version | record | win rate |
|---|---|---|
| v108 | 109/215 | 50.7% |
| v109 | 342/675 | 50.7% |
| v111 | 902/1780 | 50.7% |
| v112 | 173/330 | 52.4% |

Mean opponent rating rose from 2064 to 2139 over that span.

v112 by opponent rating: 54/120 against teams rated 2150–2250, 119/210 against 2000–2150.

## Where the games are lost (exact gem accounting; 151 losses, 169 wins)

| | margin | production | fights | conversion | our deaths | their deaths | first death (us / them) |
|---|---|---|---|---|---|---|---|
| losses | -466 | **-311** | -112 | -32 | 12.4 | 6.7 | R676 / R1198 |
| losses vs 2150+ | -517 | -396 | -89 | -28 | 11.6 | 5.8 | R409 / R1077 |
| wins | +546 | +453 | +89 | +4 | 6.2 | 14.6 | R1308 / R850 |

- **Production** is the largest deficit in 96/151 losses (fights 41, conversion 13). Only 7 losses end with an unbanked bag of at least the deficit.
- **Early economy** decides it. In losses we clear as many or more camps early (5.3 vs 4.6 by R100), but earn 18% less gold (304 vs 359 by R100; 1052 vs 1257 by R300). In wins it is the reverse (374 vs 289). Final earned gold in losses vs 2150+: 4027 vs 6530.
- **Captures are smaller.** Gems per collection entry are about 11 for us vs about 16 for opponents, in both wins and losses. We take more, smaller captures.
- **Stealing** is not the issue: 1–4% of clears are collected by the other team.
- **Carrying** is not the issue: winners carry larger bags whichever side wins.

## How we die (122 decoded games)

| | us, losses | them, losses | us, wins | them, wins |
|---|---|---|---|---|
| champion deaths / game | 11.1 | 5.8 | 4.0 | 14.4 |
| burst share (>= 50% HP 3 rounds before death) | 0.52 | 0.38 | 0.38 | 0.55 |

- **Fuel** does not explain the deaths: only 10 of 892 deaths in losses came within 3 rounds of one of our fuel-outs. Most fuel-outs are early.
- **Prism** kills 6.1 of ours per loss game when present (27 games). It kills from a median of 5 tiles, 58% from beyond 4, with the victim at 62% HP. Stellar shows the same pattern.
- **Engine ability dump** (all designs): every spell reaches at most 4 tiles. So Prism's kills from beyond 4 tiles are move-then-cast. Prism also gains +1.5 focus per carried gem.
- **Our threat model** keeps only nuke size per design (`spell_kit`), not reach, and checks danger mostly within 4–5 tiles.

## Idle time (runs of >= 8 rounds with no move, attack, cast or channel)

| | us, losses | them, losses | us, wins | them, wins |
|---|---|---|---|---|
| idle rounds / game | 110 | 88 | 115 | 30 |

Examples:
- **04standing_stones:** a champion waits 50–60 rounds at full HP with the nearest camp 30+ tiles away.
- **00galaxy:** Ryth waits rounds 49–98 in the opening.
- **00vault:** Marcella stands with 428 gems for 42 rounds.

## Contested-capture stall (reproduced locally)

The v112 trace copy (`MD` and `CP` rows) on the stall maps (`v112-stall-trace-01`, `v112-capture-trace-01`) shows the following.

- The farm `capture` branch holds a reward region with no timeout and never reads `capture_state()`.
- The engine reports `contested` with the timer frozen at 5:
  - 00vault (v112 mirror): two to three of ours and two to four of theirs, about 1,900 turns per game.
  - 04lines: 3,443 turns, mostly with no enemy visible on the tiles.
- In 30 decoded ladder games, rewards sat available with nobody capturing for 14,468 group-rounds, including 131 runs of at least 20 rounds. Snapshots cannot separate abandoned from contested.

**Fix CL_CONTEST** (`tools/rl_env_1104/cl_patches.py contest`): push when we outnumber the visible enemies on the region; otherwise keep one anchor and release the rest; the anchor gives up after 36 turns; a bag of 40+ banks.

**Result:** neutral on a 32-map live-pool sample (`e3-v112-contest-01`, 512 games). Paired 0.000 [-0.035, +0.035], 136/256 each, 13 flips each way. The stall is real but rare on random maps.

## Next

Retrain the target network on the patched bot (Om's point: weights tuned to the old behaviour). Use the archived PPO trainer, ported to CPU (`artifacts/tmp/agentic_restore/cl_train.sh`), starting from v112's exact g12 checkpoint. The checkpoint export reproduces v112's `nn_weights.h` byte for byte.

## CL_WAITCAP (e3-v112-waitcap-01, 512 games, same 32-map live-pool panel)

**Mechanism.** Final targets that are respawns more than 20 rounds away are replaced by the v92 pick and avoided until 15 rounds before the respawn. The network's candidate set ignores the avoid list.

**Result.** Paired -0.023 [-0.090, +0.043] (130/256 vs 136/256), margin -22 per game. **Not a verified improvement; left out of the retrain bundle.**

## Retrain (in progress)

`cl1` is a CPU PPO run on base `cl112` (v112 + CL_CONTEST), starting from v112's exact g12 network (critic value_10).

| setting | value |
|---|---|
| league | v112 .20, nnfinal .15, v86h .10, x3inv .10, v111 .10, nnm4 .10, v92 .05, x1 .05, x3ctr .05, p65pack .10 |
| training maps | the 96 live-pool maps outside the 32-map evaluation panel (80%), generated pool maps (20%) |
| iterations | 16 x 192 games |
| checkpoint selection | 12 training-pool maps x 4 opponents x 2 sides, every 4 iterations |
| final judgement | the held-out 32-map panel and 21 generated holdout maps, paired against v112 |
