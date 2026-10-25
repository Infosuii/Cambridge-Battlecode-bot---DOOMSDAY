# v52 plan

Goal: v52 beats v51 on every measurable axis, then climbs the ladder from rank 87. "Unbeatable" is the direction; the measurable target is the top 25.

## Where v51 stands (measured 2026-10-25)

- Ladder: 51% over our last 800 ranked games (before v51). Almost all of the deficit comes from a few maps: stampede 0/28, big_world 0/26 (fix shipped in v51), boss_battle 1/16, islands 3/25 (fix shipped), concentrated_wealth 3/21, elkring 7/24, swirl 6/19, monolith 6/18, fracture 5/13, yellow_brick_road 9/23.
- The bot runs at its fuel limit. A behaviour-identical hot-path change lost 0-8, and the same change in a cold path played identical games. So cheaper hot paths mean a stronger bot, and every change must be measured.
- Neural parts: the draft net and the camp net (321 parameters, about 3 hours of in-engine PPO in work/neural-gameplay). Neither had a measurable effect in local A/B tests. The policy-v2 network learned nothing that helps in games, and it stays out.

## Workstreams

### A. Measurement first (about 1 hour)

1. Bench v2. The 28 development maps × both sides × several seeds, using the bot's built-in `NOVA_SEED` jitter, which turns each map into many distinct games. Opponent pool: v51, v50, v48, heuristic-v1.
2. Acceptance gate. A candidate must beat v51 head-to-head. On each target map it must win both sides with a margin. No other map may regress beyond the noise floor, which a behaviour-identical control measures.
3. The 12 final maps stay a holdout until the v52 release check.
4. Ladder: the v51 tracker is running. After each submission, a per-map ladder report from `cambc matches list`.

### B. Fix the maps we lose (largest lever)

For each map below a 40% ladder win rate: decode our losses, reproduce the failure locally with a logging build, find the root cause, fix it, and verify. This is the same method as the v51 moat fix. Work in order of games lost:

1. stampede: the only gem camp is never attacked, because team-job joining is broken. The first fix attempt was rejected; redo it as a cheap, targeted fix.
2. boss_battle: gems collected but never banked (altars gated behind monoliths).
3. concentrated_wealth, elkring, swirl, yellow_brick_road, gemfight, shortcut: root cause still to be found.
4. Holdout maps (monolith, fracture, the_farm, ambush): diagnose from ladder replays only, and measure them only at release.

Also a general pass on deaths: in our losses we die more often than the winner. Check retreat and engagement rules against the losses.

### C. Fuel efficiency

Profile fuel per function with the existing `PROF` instrumentation over the bench maps. Optimise the top hot spots without changing behaviour (cache distance fields, skip recomputation, exit early), so the bot has more fuel left for search on every turn. Each optimisation is measured against v51.

### D. Neural (runs in the background on the GPU and CPU workers)

1. Camp net: continue PPO from v50's weights on the v52 code base for several hours, using `work/neural-gameplay/tools/train.py` with 20 match workers and the GPU. Keep it only if it beats the same build with the net off.
2. Draft model: train a win-probability model (map plus both drafts → winner) on the 244,981-match 23 October archive, weighted to top-100 teams, plus our recent ladder games. Use it for picks and counter-picks. Our ladder win rate already ranges from 39% to 58% depending on which champions we pick, so the draft matters. Validate against the current draft net in selection games.
3. Port v48's danger net into the v52 code as a switch, and keep it only on A/B evidence.

### E. Release loop

v52 candidate → bench v2 against the pool, plus the 12 holdout maps → submit (with approval) → ladder tracking and unranked match groups against top teams on the target maps → v53.

## Order

A, then B and C interleaved (most of the effort). D runs in windows when benches are not using the CPU, for example overnight. E whenever a candidate passes the gate.

## Needs approval

1. Queueing unranked match groups against top teams. This uses the team's website quota and plays our submitted bot.
2. Submitting v52 when it passes the gate.
3. Multi-hour CPU and GPU training runs (PPO, draft model).
