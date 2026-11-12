# Local testing audit: how close is self-play to the platform? (2026-10-28)

## What matches the platform exactly

| Check | Evidence | Result |
|---|---|---|
| Engine | `engineBuildHash` in 240 local summaries and 300 top-vs-top platform summaries (`tools/v67/c_engine_audit.py`) | identical: 2.0.0, `85aa7167…`, metric semantics 1 |
| Maps | `mapHash` of every map played locally against platform summaries of the same map (`tools/v67/c_map_audit.py`) | 61/61 identical; all 70 pool maps exist locally |
| Rules and fuel | `cambc run --release` at default fuel: the platform's mode (no debug blocks, no fuel-pause imports) | same CLI path as the platform |
| Our compiled bot | Our fuel-outs per game on the ladder (six top-12 duel arms, 720 games: 0.36-0.62) vs locally (0.58) (`tools/v67/c_ladder_parity.py`) | the platform's build of our source spends fuel like the local build |
| Determinism | Repeated slots (same wasm pair, map) give identical summaries; a cached game rerun from scratch is identical (`tools/v67/c_cache_check.py`) | deterministic |

## What was wrong with how we tested, and the fixes

1. **31% of every benchmark was duplicates.** `research/v59/duel_top1.json` has 240 seeded games but only 166
   distinct (map, side, seed) matches. The engine is deterministic, so the 74 repeats are copies that triple-weight a few
   maps and make results look more certain than they are. Example: the "+19 wins" combo on seeds 15/16 is +9 on distinct
   games, margin +67 with a 95% interval of [−58, +205]: not distinguishable from zero.
   **Fix:** `research/v68/pool_plan.json` (`tools/v67/c_pool_plan.py`): every pool map once from each side, 140 distinct
   games per seed.
2. **9 of the 70 pool maps were never played** (the plan was built from five-map ladder groups).
   **Fix:** the pool plan covers all 70. It immediately exposed a bug on `00vault` (below) that the old plan hid.
3. **We tested binaries we never ship.** Each seed rebuilt our bot with a different `NOVA_SEED`; the submitted source
   always has `NOVA_SEED 1`. **Fix:** `local_duel.py --bot-seed 1` builds our bot once, exactly as submitted, and the
   seeds vary only the opponent. `c_batch.py` uses this by default.
4. **Verdicts were read from raw win counts.** **Fix:** `tools/v67/c_paired.py` pairs candidate and baseline game by
   game, counts each distinct match once, and gives a 95% interval that resamples maps (games on one map correlate).
5. **Every match was recomputed.** **Fix:** a deterministic game cache in `python/nfs/engine.py` keyed by both wasm
   hashes, the map hash and the CLI hash (`NFS_GAME_CACHE=0` disables it). A rerun baseline or a mirror slot is free:
   280 mirror games took 25 seconds; three 560-game candidates took 3 minutes together, builds included.
6. Parallel runs crashed when two of them compiled the same opponent at once. **Fix:** `local_duel.build` keeps the
   copy another run cached first.

## A real bot bug the full pool found: the 00vault freeze

On `00vault` the siege target is a 49-camp group. The siege line-of-sight scan (`NOVA_SIEGE_LOS`, in `fight_camps`)
tests every ring tile (~109) against every camp each turn, overruns the 100k turn budget and suspends; the next turn
starts the same scan, so the champion never acts. v65 mirror, seed 1: Marcella 662 fuel-outs from round 532 to 2000;
up to 1,025 fuel-outs per game. The platform audit's Vault loss (two champions frozen from round 227) fits the same
pattern. Every version since v58 has it.

**Fix (`V68_SIEGE_FIX`, `tools/v67/c_siege_fix.py`; `bots/v68` = v65 + this fix):** the scan resumes next turn where it
stopped (it stops at 15k fuel left) and keeps its result until the group's live camps change. Where the scan fits in a
turn the ring is the same as before. A first version that stopped at 45k and cached partial rings for 40 rounds cut
scans short on other maps (01boss-battle −596, 01starfish −567 per game) and was replaced.

Full-pool check, v68 against v65 (560 distinct games, seeds 1/2/5/6, our bot as shipped): fuel-outs per game
2.9 → 0.6; `00vault` +156 gems per game; overall −12 gems per game, 95% CI [−32, +5], i.e. no change elsewhere.
A pool sweep (seeds 1, 2, 5-8) shows no other map with a freeze; `02the-pack` has 5-7 scattered overruns per game,
normal for a large map.

## The carry-economy candidates on the faithful test

Against v65, 560 distinct games each, compared with `bots/v66a` on the same games (`tools/v67/c_paired.py`):

| Candidate | Wins | Margin vs v66a per game (95% CI) | Gold per game vs v66a |
|---|---:|---:|---:|
| v66a | 284/560 | — | 5,723 |
| `bots/v68c` (v66a + v58 carry loop) | 196/560 | −176 [−262, −93] | −599 |
| `bots/v68cb` (+ one-emblem openings, Bruiser stacks) | 180/560 | −223 [−309, −143] | −870 |

The gold loss is economic, not just a fight-style artefact of playing ourselves, so these are not release candidates.

## What local play still cannot match

The opponent. Locally every opponent is our own lineage (v65 and older); the platform's top 12 farm about twice as
much, die a third as often and kill four times as often (`research/v66/RESULTS.md`). Proxies built from their drafts
and items did not predict the ladder better than self-play (`research/proxy/README.md`). Local runs are reliable for
bugs, fuel, faults and mechanisms (gold, deaths, carry income); strength against the top teams needs ladder duels.

## How to test now

```text
python tools/v67/c_batch.py --seeds 1 2 5 6 --workers 6 base=bots/v65 cand=bots/v68
python tools/v67/c_paired.py cand base
python tools/v67/c_carry.py cand base        # per-hero gold, deaths, early Bruiser
```

`tools/v67/raw_run.py` still refuses seeds 3/4 (GPT's reserved holdout for the dropped 220 target); use other seeds.
