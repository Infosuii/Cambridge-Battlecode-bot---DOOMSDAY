# How the bot works

DOOMSDAY's ladder bot is a **hand-written C++ heuristic bot compiled to WebAssembly**, with small neural networks
in a few decision points. One codebase evolved from v48 to the final qualifier builds. This page walks through the
reference build, [`bots/mainline/v92`](../bots/mainline/v92/src), at about 17,000 lines. Later versions keep this
structure.

<p align="center"><img src="assets/architecture.svg" alt="Bot architecture: draft phase, per-turn priority cascade, neural modules, team radio, fuel discipline" width="100%"></p>

## The pieces

| Area | Where (v92) | What it does |
|---|---|---|
| Draft | `draft.cpp` | Picks champions from fixed lineups, per-map tables (`kNovaMapLineup`, ladder tables from v70) and a learned draft network (`A2_MLDRAFT`). It uses the 10× fuel of the first draft turn to analyse the map. |
| World model | `world.cpp`, `world.h` | Tracks tiles, camps, groups, altars, respawns and enemies. Builds **distance fields** with cheap host-side calls, because wasm loops are expensive. |
| Per-map profiles | `bot.cpp` (`V71_MAP_KNOBS`) | Recognises a pool map by fingerprint on the first turn and loads a tuned knob vector: aggression, bag size, hunting, retreat health and so on. |
| Camp choice | `score_groups`, `farm`, `route_search` | Scores every camp group by value, distance, danger and crew needed, then claims it through shared memory so champions don't collide. |
| Combat | `handle_enemies`, `tsearch.*`, `fight.cpp` | Fights, flees or regroups using Lanchester-style strength estimates. A bounded tactical search runs on whatever fuel is left in the turn. |
| Banking | `tribute_if_needed` | Decides when a bag is big enough to bank (`kTributeCarry`), and when a race lead means bank small and play safe. |
| Items | `shop`, `build_for` | Item plans per champion: stat shards, emblem milestones (Treasure first, Bruiser stacks), consumables. |
| Coordination | `write_claim`, `read_sighting`, `decode_claims` | Packs claims, sightings and respawn events into the **8 bytes** of shared memory. |
| Vision | `ward_ahead`, `ward_reveal` | Places wards ahead of routes and into bushes. |
| Race layer (switchable) | `play_turn` (`APEX_BRAIN`) | A learned win-probability model (73.6% held-out accuracy, 138k samples) switches posture between pressing, safe banking and contesting. |

## Neural components

All networks are tiny and quantised, because they must fit inside the 100k-fuel turn:

- **Draft net** (`A2_MLDRAFT`) and **camp net** (`A2_CAMPNET`, 321 parameters, about 3 hours of in-engine PPO),
  from the v48–v50 era.
- **Danger net** (`UB_DANGER`, v48) and an **item model**.
- **The nnq4 blend** (4 Nov, shipped as v106): a 16-bit student network re-scores camps inside `farm()`.
  It overrides v92's choice only when another camp scores more than 2 logits higher. Its slow part refreshes in stages
  on spare fuel. Against v92 it scored 54.6% ± 1.3 over 1,440 games. The blend (`A2_NN_ENS`, `A2_NN_LAZY`) stayed in
  the v112–v137 live line. See
  [`research/neural/nnq4-blend`](../research/neural/nnq4-blend/README.md).
- **ES-retuned weights** (Om's live line, v112): evolution-strategy tuning of the network weights on a 20-thread
  workstation. This was the build live at our peak ladder rank.

## Living inside the fuel budget

The bot runs at its fuel limit almost every turn, so the code follows strict rules:

1. New logic runs **once per call or once per turn**, never inside per-group or per-camp loops.
2. Expensive analysis is deferred: staged network refreshes, lazy distance fields, analysis spread over the draft turns.
3. Every change is measured as a whole build, because the engine is deterministic and any binary change can move later
   decisions.
4. Fuel-outs are tracked per game. A release must show zero faults and near-zero fuel-outs.

## Experimental systems built on the same code

| System | Where | Idea |
|---|---|---|
| Map atlas and portfolio | `bots/x-series/x3`, `research/x-series/x3` | About 25 map features computed by the bot itself, 7 map categories, and a 14-profile portfolio picked at round 3. Exact on 86/86 maps, but per-category choices did not transfer to unseen maps. |
| Counter tables | `bots/x-series/x3ctr*` | Opponent-specific tables. They looked strong in sample (+37 to +89) and came out about zero out of sample. |
| Team economy | `bots/botx3/` | Eleven versions of coordinated crews and shared economy, paused on 3 Nov. |
| gigabot (gx) | `bots/gigabot/` | Many single-mechanism increments, each with a matched control and a proof run. |
| DOOMSDAY Zero | `bots/doomsday-zero/` | A clean-slate C++20 rewrite with no old code or weights. It passed 292 release games with no faults and never reached strategy parity. |
| RL environment | `bots/rl-env/`, `research/rl-env/` | A recurrent PPO learner, a belief model, and a qualifier-week fix pipeline. |

## Building

The bots build with the official CLI, which bundles a wasi-sdk C++ toolchain:

```bash
cambc build bots/mainline/v92 --release --output v92.wasm
cambc run v92.wasm other.wasm --map maps/ladder-pool/<map>.map26a --release
```

The repository is a record of finished work. Scripts still use the paths from before the reorganisation (for example
`bots/v92`), and the platform has moved on to newer engines, so expect to adjust paths before rerunning anything.
