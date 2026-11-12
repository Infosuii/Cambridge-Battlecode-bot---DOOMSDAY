# What we learned

> These findings describe historical experiments across several bot lines. For the final v306 comparison,
> confidence intervals, faults and fuel accounting, see [Results and evidence](RESULTS.md).
> For which systems are actually active in v306, see [the architecture](architecture.md).


The lessons that cost the most to learn, each with the measurement behind it. The longer write-ups are linked.

## 1. Compute is the real opponent

The bot runs at its 100k-fuel-per-turn limit, and the engine is deterministic.

- A change with identical behaviour that added a few instructions to a hot loop lost **70–98 over 168 games
  (−85 gems a game)**. The same no-op in a cold path played identical games.
- **Rule:** new logic runs once per call or once per turn, never per group or per camp.
- The best neural result needed 20M fuel per turn (about 59% vs v92). The version that fit the real limit
  reached 54.6%. Making the existing code cheaper was often worth more than new ideas.

→ [handoff.md §3](history/handoffs/handoff.md), [nnq4-blend](../research/neural/nnq4-blend/README.md)

## 2. Determinism makes single builds a single draw

- A do-nothing rebuild flips 4–7 of 172 local games, and a real behaviour change flips about 40%.
- An RL checkpoint looked like a +7.7-point gain (56.3% vs 48.6%). After adding tiny noise to the bot's own scores it
  scored *below* its starting point (44.5% vs 49.3%).
- **Rule:** compare bots with noise on their own scores, use map-clustered bootstrap intervals rather than per-game
  standard errors, and pre-register release gates.

→ [`tools/bench_compare.py`](../tools/bench_compare.py), [`tools/bench_bayes.py`](../tools/bench_bayes.py)

## 3. Local self-play did not predict the ladder

- `x3mf` was +30/516 locally and level with v92 on the ladder (+0.9% ± 6%).
- Counter tables scored +37 to +89 in sample and about 0 out of sample.
- Per-category portfolio choices scored −19 to −29 out of 688 on unseen maps.
- The only measurement that predicted the ladder was a **paired ladder duel**: the same opponents, pinned to the bot
  they ran before, played against the base and the candidate.

→ [`research/x-series/x3/ANTI_OVERFIT.md`](../research/x-series/x3/ANTI_OVERFIT.md),
[`tools/replay/duel_pipeline.py`](../tools/replay/duel_pipeline.py)

## 4. Losses are economic, and they start early

From 151 decoded v112 ladder losses (8 Nov):

- **Production** was the biggest deficit in 96 of the 151 losses. Fights were the biggest in 41, conversion in 13.
- By round 100 we had earned **18% less gold** in losses (304 vs 359). Top teams spend gold early.
- We died about twice as often: 11–12 deaths a game against about 6. Each death hands the killer the whole bag.
- A controlled snowball test: **+150 gold per champion at round 100 → 84.5% win rate** (control 53.5%).

→ [`V112_LADDER_DIAGNOSIS.md`](../research/rl-env/rl_env_1104/candidates/V112_LADDER_DIAGNOSIS.md)

## 5. Map-specific bugs are fast to find with a logging build

- **stampede:** one group holds every gem, and big-job calls never filled. 0/28 on the ladder before the fix, 6–0
  locally after it.
- **big_world / islands:** champions froze at camps behind two-tile hole moats. 0/26 and 3/25 on the ladder before the fix.
- **homonoliths:** home monolith groups were rejected because `need > team_size`. A 3-champion siege crew on spawn
  tiles (spawn heals fully every round) captured the home group in 18/18 test games, at a median of round 417
  against round 1,353 before.
- **Method:** reproduce with a logging build, look for champions whose position or mode never changes, find the code
  path, and fix it cheaply. Each of these took about an hour.

→ [`research/live-line/v118-rootcause-20261109`](../research/live-line/v118-rootcause-20261109)

## 6. Imitation alone did not work; a network beside the heuristics did

- Behaviour cloning on 7.3M top-team decisions produced a policy that scored 0 gems.
- Networks that only *override* a strong heuristic when clearly confident did work. The nnq4 blend changed v92's camp
  target only at a 2-logit margin, and 94% of its overrides kept the current target where v92 wanted to switch.
- How fresh the network's inputs were mattered more than its size: refreshing every turn scored 63.3%, every 4 turns
  47.6%. Larger networks (24×96, 32×128) gave no steady gain.

## 7. Parallel work needs a protocol

Up to five machines ran campaigns at once. What kept that usable:

- a git message board with jobs, leases and heartbeats;
- one owner for the live ladder version;
- an evidence record and a release record for every candidate.

The one serious incident came from uncoordinated uploads: in the early hours of 9 Nov the live version was uploaded,
cancelled, pinned and switched again by different people within about an hour.
