# Agent 2 work from v61 onward (engine 2.0.0 / cambc 4.0.0)

Findings from the Agent 2 workspace after our v61 build. **This `v61` is Agent 2's own build and is not
`bots/v61` on other branches.** It is v57 plus the Prospector build, baked knobs and the lock guard, then a
black-box knob search (`EXPERIMENTS.md` E56–E57). The source is in [`../../bots/agent2-v61/v61/src`](../../bots/agent2-v61/v61/src).

## Headline results

| Item | Result |
|---|---|
| v61 vs the team's v60 dev (bot 5), real engine, 340 games (E57) | 55.0% ± 2.7 (unseen maps 53.5%, official 57.1%) |
| Lab vs real engine gap (E56) | Lab +21, real engine about +7: tuning against the training opponent plus a below-50 control inflated the lab figure |
| Everything tried after v61 (E58–E76) | No change beats v61 / m62 by more than noise in the lab against v61 and bot 5 |
| Platform match groups (E63, E67) | 20 distinct games, 0 wins |

## What was tried after v61 (all logged in `EXPERIMENTS.md`)

| Exp | Idea | Result |
|---|---|---|
| E58 | Merge bot 5 (v60 dev) with v61's knobs (m62) | 51.8 vs v61's 50.0: about nothing |
| E60 | Walking-distance fields on the 10M-fuel draft turn | Works in the real engine; generated maps too open |
| E61 | Specialist knob sets per map cluster + selector | Held-out 50.0 → 47.7: dropped |
| E62 | Team opening schedule from the draft fuel (`sched.h`) | Banked gems +11% by round 200, wins +1.5 (not clear) |
| E63 | 79 new knobs (slots 64–142), block rotation | Block F −1.5 ± 3.8: rotation ended |
| E63 / E67 | Platform loss analysis (`MATCH_ANALYSIS_E63.md`) | We buy no combat stats, die alone while fleeing (75% of deaths), place no altar locks |
| E64–E65 | Fixes from the match analysis (items, Vesper first, retreat, cohesion, bags, prelock) | None beats the control on 280 official games |
| E66 (precompute) | Draft precompute used all game (`A2_MP_LATE`, `bots/agent2-v61/p64`) + schedule knob search | 480 fresh games: 52.5 control, 51.7 / 52.4 tuned |
| E66 (squad) | Escape-distance retreat + squad farming | Deaths −27%, no more wins |
| E68 | Farm-speed knob search | Noise on held-out maps |
| E69 | Learned fight / flee / regroup from engine counterfactuals | Nothing learnable: the bot's own verdict is as good |
| E70 | Learned strategy switcher (RL over knob styles) | 51% vs 53.2% control |
| E71 | Altar raid (ward the enemy's banking altar, answer long tributes, lock-cancel) + carrier hunting (`A2_RAID`, `bots/agent2-v61/p65`) | Fires (ward in 16 of 20 official games, 15-22 lock cancels) but 48-55 vs control 57 |
| E72 | Next-camp choice: top teams vs us (conditional logit on 9,193 + 1,220 decisions), `A2_TOPFIX` | Top teams weigh gem size and respawn waits less; shifting either way loses (16-57 vs 57) |
| E73 | Exchange rates (one-off gifts / free kills), gold valuation, rush, flee / stand switches | +150 gold per champion at round 100 = 84.5 vs 53.5; one kill = 71.0; rush 37.5-48.5; stand-and-fight 25.5 |
| E74 | Opportunistic gang kills (`A2_GANG`), power-based early retreat (`A2_LANCH`) | Neutral (46-55.5) |
| E75 | 20 lost platform games decoded: winners farm 2x gems early, win early whole-team fights; packs / pairs / jackpot copies | Copies lose (9.8-46) |
| E76 | Farm first, then pack and attack (`A2_RUSH_FROM` etc.) | 7.0-32.5: packing costs at every stage |

## Why the lab stopped finding gains

- v61 and bot 5 play almost like our bot, so the lab measures a near-mirror. Changes aimed at the platform's
  stat-stacking, grouped opponents test neutral or negative here.
- Picking the best of many noisy candidates inflates its score (optimizer's curse): the best of 100 candidates on
  200 games shows about +9 points from noise alone. That explains "+5 to +29 in training, about 0 held out".

## Recommended next steps (from `MOBA_AI_TECHNIQUES.md`)

1. Stricter evaluation: common random numbers, held-out maps and seeds, a sequential test (SPRT).
2. Scripted ladder-style sparring bots (pack hunter, stat stacker, lock warden) so the lab can see platform losses.
3. Power-curve item build, ally-aware retreat and engagement, the altar-lock war — measured against those sparring
   bots and on the platform, not against v61 / bot 5 alone.
4. For beating v61 / bot 5 specifically: an exploiter knob search (at most about 20 knobs) with stricter testing.

## Files

| Path | Contents |
|---|---|
| `HANDOVER.md` | **Start here**: status, where everything is, how to build and test, what not to retry, next steps |
| `EXPERIMENTS.md` | The full Agent 2 experiment log (E1–E76) |
| `MATCH_ANALYSIS_E63.md` | Why the platform games were lost |
| `KNOBS.md` | Lab knob slots (0–142) and what each does |
| `FINDINGS.md`, `PLAN_v4.md`, `INTERFACES.md` | Engine 2.0.0 findings, plan and lab interfaces |
| `MOBA_AI_TECHNIQUES.md` | Research report: MOBA AI, competition bots, training methods, our code and strategy |
| `research-notes/` | The four research notes behind that report |
| `tools/` | Platform replay study (`platform_study.py`, `platform_farm.py`) and the next-camp model (`next_camp.py`) |
| `lab/` | Engine-lab scripts (Node host, head-to-head, knob searches, diagnostics). They expect the workspace layout `tools/viz/v2_0_0.wasm` and `v4/bots/<name>`. |
| `../../bots/agent2-v61/` | Sources: `v61` (best), `p64` (precompute all game, E66), `p65` (all dev switches + altar raid, E71), and `mkvar.py` (variant builder) |
