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

## Top teams vs us (engine 3)

Sample: 40 recent ranked games between 2400+ teams (80 team-games), compared with v112's 320 games.

| | earned gold R100 | R300 | R600 | camps cleared by R300 | deaths/game |
|---|---|---|---|---|---|
| top teams | 395 | 1549 | 3467 | 19.9 | 10.5 |
| us (v112) | 341 | 1244 | 2660 | 16.3 | 9.1 |

Draft share (per team-game):

| champion | top teams | us |
|---|---|---|
| Cassi & Issac | 0.90 | 0.53 |
| Heart of Ruin | 0.81 | 0.77 |
| Vesper Vale | 0.57 | 0.09 |
| Prism | 0.44 | 0.00 |
| Willow | 0.42 | 0.07 |
| Marcella | 0.42 | 0.87 |
| Vendetta | 0.35 | 1.00 |
| Varg | 0.19 | 0.82 |

- **Our roster sits far from the engine-3 meta.** On our own ladder data, v112 plays Vesper (32 games) and Willow (25) much worse than our usual picks. A roster change therefore needs per-champion play work and a retrain, consistent with the local "top draft" switch scoring -0.35 without retraining.
- **Prism check (probe bot):** the engine-reported focus includes Prism's +1.5 per carried gem (90 base; 150.5 with 35 gems). Our threat model already uses it. Prism kills from 5 tiles are move-then-cast inside our 5-tile window, not a blind spot.
- **Spell reach:** the engine design dump shows every spell reaches at most 4 tiles.

## Final held-out panel (final-cl1-02)

**Setup.** 53 maps: 32 live-pool maps held out of all training plus 21 generated holdout maps. 6 opponents: v112, nnfinal, v86h, x3inv, x3mf2 and x3ctr3 (the last two never trained against), both sides, 636 games per candidate, paired with v112.

| candidate | score | paired vs v112 | family-balanced |
|---|---|---|---|
| v112 | 353/636 (55.5%) | - | - |
| cl1 iter 16 (PPO retrain on v112 + CL_CONTEST) | 331/636 (52.0%) | -0.035 [-0.082, +0.011] | -0.030 |
| CL_EARLYSHOP (shop at 90 gold before R300) | 365/636 (57.4%) | **+0.019 [-0.023, +0.066]** | +0.030 |

**cl1 retrain.** The checkpoint-selection panel showed noise around baseline (53.1 → 47.9 / 49.0 / 47.9 → 53.1%). On the held-out panel the retrain is slightly negative. Not shipped. This matches the team's earlier PPO runs (native-current +0.7pp, team-win: retry required).

**Early shopping.** Mildly positive; consistent with top-team spending (91/168 of team gold spent by R50, vs our 31/147). Proposed as v113. The upload is held for an explicit go-ahead.

## Per-map profiles for unrecognised maps (in progress)

- **The gap.** v112's LADDER_TABLES recognise 45 of the 128 live-pool maps by fingerprint (verified: 45 exact matches, no collisions). On those maps v112 wins 70/123 = 56.9% on the ladder; on the other 83 maps it wins 103/207 = 49.8%, against the same opponent ratings.
- **Selection run (profsel-01).** The 8 most-selected research/v71 profiles (nomid, gold, group, gems, mid, teamfight, softcaut, ranged), each applied only on unrecognised maps, against v112, nnfinal and v86h, both sides, paired with v112.
- **Table.** Maps switch only on a paired gain of at least 2 games with at most 1 lost cell (`train/profile_table.py`), as a fingerprint table (`cl_patches.newmap_table`).
- **Validation.** The table is then checked against different opponents.

## Per-map profile selection and independent validation

**Selection (profsel-01).** 83 unrecognised maps; opponents v112, nnfinal, v86h, both sides; 498 games per profile, paired with v112.

| profile (all 83 maps) | paired vs v112 |
|---|---|
| group | +0.004 |
| ranged | 0.000 |
| gold | -0.010 |
| softcaut | -0.014 |
| nomid | -0.016 |
| teamfight | -0.032 |
| mid | -0.074 |
| gems | -0.076 |

No global profile helps. Per-map tables (`profiles/profile_table_g{2,3}`):
- **Strict (gain >= 3 of 6 cells, <= 1 lost):** 16 maps switch (nomid 5, group 3, mid 3, gold 3, softcaut 1, gems 1); +51 games in-sample.
- **Loose (gain >= 2):** 38 maps switch; +95 games in-sample.

**Validation (tabval-01).** Same 83 maps; opponents never used in selection (x3inv, x3mf2, x3ctr3), both sides; 498 games per candidate.

| candidate | score | paired vs v112 |
|---|---|---|
| v112 | 286/498 | - |
| loose table | 289/498 | +0.006 [-0.040, +0.050] |
| strict table | 293/498 | +0.014 [-0.012, +0.040] (+7 on the 96 changed cells) |
| strict table + early shop | 300/498 | **+0.028 [-0.036, +0.090]** |

- **Strict table:** survives out of sample (+7 games where in-sample was +51), so it shrinks but stays positive. The loose table's extra maps are mostly noise.
- **Early shopping:** positive again on new maps with new opponents (about +1.4 on top of the table), consistent with +1.9 on the 53-map panel.

**Proposed v113** = v112 + CL_EARLYSHOP + CL_NEWMAP_TABLE (strict). Local WASM: 2c147d877d4d18f58fea9fdcf8b973daaf35678378a4abcd1e1e35390f13d804. Source: `artifacts/tmp/upload_v113/src` (41 files). The diff from v112 is the three defines, the table include, the table application and the early-shop cap.
