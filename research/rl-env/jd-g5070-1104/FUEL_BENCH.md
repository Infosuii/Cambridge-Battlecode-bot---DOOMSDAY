# FUEL_BENCH: v92 fuel profile and the stages that suspend (run g5070-1104, FEAT-002)

All numbers are in-game WASM fuel at official settings (cambc 4.0.0 / engine 2.0.0, no `--fuel-quantum`). Machine-
readable data: `fuel_bench.json` (`baseline`, `stages`) and `fuel_contract.json`. Tool:
`py tools/jd_g5070-1104/fuelbench.py {probe,bench,prof,triggers} --run <run>`. A unit turn whose used fuel is >= its
budget is a **suspension**. The turn ran out of fuel, and the champion loses its next round (the probe shows the
next turn two rounds later). Engine `fuelExhausted` events and the replay-trace rule agree (461 vs 462 on the dev
baseline).

## 1. Baseline per-turn fuel (v92, dev partition)

Run `base-v92-dev-01`: v92 vs x3inv, p65pack, public-khiri and v92 on the 90 dev maps, both sides, 720 games. The
source is replay fuel traces (`team-?.fuel`). The size bucket is the map's longer side.

| phase | size | unit turns | p50 | p95 | p99 | max | suspensions |
|---|---|---:|---:|---:|---:|---:|---:|
| draft first (10M) | <=40 | 216 | 90,164 | 103,785 | 104,101 | 104,101 | 0 |
| | 41-60 | 280 | 91,413 | 100,356 | 107,118 | 107,118 | 0 |
| | >60 | 224 | 95,970 | 110,786 | 116,405 | 116,405 | 0 |
| draft later (100k) | <=40 | 616 | 59,738 | 61,416 | 61,421 | 61,423 | 0 |
| | 41-60 | 816 | 58,361 | 61,388 | 61,395 | 61,414 | 0 |
| | >60 | 688 | 3,368 | 61,393 | 61,425 | 61,430 | 0 |
| first champion turn (200k) | <=40 | 892 | 94,579 | 129,730 | 135,745 | 136,498 | 0 |
| | 41-60 | 1,242 | 123,598 | 152,644 | 154,847 | 155,048 | 0 |
| | >60 | 1,064 | 161,037 | 196,270 | 200,000 | 200,000 | **48** |
| ordinary (100k) | <=40 | 987,483 | 31,889 | 61,597 | 74,071 | 96,859 | 0 |
| | 41-60 | 1,249,113 | 42,042 | 67,097 | 78,094 | 100,000 | 8 |
| | >60 | 927,417 | 55,437 | 76,923 | 85,179 | 100,000 | **406** |

**Baseline suspension count: 462 unit turns in 97 of 720 games.** It is not zero. By round: 0-99: 283, 100-199: 75,
200-299: 41, 300-399: 25, 400-499: 16, 500+: 22. By map: pool_1907 107, pf_pool_77041 96, pool_1111 75, pool_1119
55, pf_pool_77127 40, pf_pool_77031 30, pf_pool_77125 14, pf_pool_77082 10, pool_1116 8, pool_1118 6, and 3 or fewer
elsewhere. Top cells: every one of the 8 pf_pool_77041 games (98x98) suspends all 6 bodies on round 1 (48 = the
whole first-champion-turn count), then suspends again around round 13. The holdout baseline `base-v92-pool-01`
(reporting only) has 705 fuel-outs in 183 of 688 games. v92 self-play on the pool maps shows none, so self-play hides
the problem.

The draft is almost unused: v92 spends 57k-135k of the first draft turn's ~9.985M.

## 2. Stage profile (JD_FUELPROF build)

JD_FUELPROF (default 0) records `fuel_remaining()` at every existing `PROF_CHECK` checkpoint plus one new `claims`
checkpoint, and charges the fuel between consecutive checkpoints to the later one. Results are aggregated into
1k-fuel histograms per (checkpoint, phase): first turn / ordinary / contact (handle_enemies ran) / dead /
crossed-round. The histograms are printed in chunks (`JDPF` lines). A suspended turn's full trail is printed as a
`JDSUS` line on the next budget. Percentiles below are upper 1k-bin edges per checkpoint interval, aggregated by
stage. The first-turn `TURN` histogram saturates at 100k, so use section 1 for first turns.

Run `diag-fprof-04` (16 conf dev maps x v92/x3inv/p65pack x both sides; 96 cells):

| phase | stage | intervals | mean | p50 | p95 | p99 | max |
|---|---|---:|---:|---:|---:|---:|---:|
| ordinary | whole turn | 343,237 | 55,016 | 60k | 80k | 87k | 99,453 |
| ordinary | farm/route (score0, route0/1, farm0, farmsel, farmmove, c_*, s_*, sg_*, f_*) | 3,585,530 | 3,359 | 1k | 22k | 30k | 62,746 |
| ordinary | observe (refresh, w_vis/groups/hot/champs/ward/sight, world, sight, events) | 4,070,909 | 1,062 | 1k | 4k | 5k | 87,234 |
| ordinary | vision (wardrev, ambush) | 655,070 | 2,154 | 1k | 7k | 9k | 53,778 |
| ordinary | claims decode (read_shared, decode_claims, brain load) | 342,926 | 1,769 | 2k | 2k | 3k | 2,429 |
| ordinary | decide other | 327,960 | 756 | 1k | 5k | 13k | 37,051 |
| ordinary | shop | 328,475 | 124 | 1k | 1k | 4k | 6,659 |
| ordinary | tail (drop_ward, prewarm, prelock, priority) | 328,097 | 230 | 1k | 1k | 1k | 4,647 |
| ordinary | tail fields (build_fields) | 328,293 | 148 | 1k | 1k | 1k | 40,417 |
| contact | whole turn | 47,513 | 50,462 | 51k | 77k | 85k | 99,484 |
| contact | handle_enemies (e_*, enemies) | 415,048 | 1,815 | 1k | 9k | 28k | 48,932 |
| contact | farm/route | 187,513 | 3,300 | 1k | 21k | 28k | 51,818 |
| dead | whole turn | 17,442 | 6,661 | 5k | 32k | 44k | 57,167 |
| first turn | init (w.init) | 467 | 16,319 | 16k | 20k | 45k | 44,039 |
| first turn | build_fields | 468 | 20,921 | 16k | 50k | 50k | 49,917 |
| first turn | world init parts (boards, spawn_field, group_loop, tables) | 1,871 | 17,364 | 10k | 43k | 48k | 47,259 |

The individual checkpoints with the heaviest tails are farmsel (p99 47k, max 61k), sg_los (p99 61k), c_brk0
(p99 38k), route0 (p99 29k) and c_walked (p99 23k). On the 98x98 map pf_pool_77041 the first turn breaks down as
group_loop 58k, spawn_field 27k, init 20k, tables 12k, w_champs 11k, boards 8k, wardrev 6.5k and claims 6.5k.
After that, about 18k is left for the tail.

**Profiler perturbation** (profiled vs unprofiled v92 on the same 96 cells, replay traces): mean ordinary-turn fuel
59,474 vs 51,873 (+7.6k, +14.7%), p99 90,946 vs 86,335. Suspensions were **136 vs 148**, so the profiler adds no
suspensions. Two earlier profiler versions were rejected for perturbation. The first was built on A2_TEL with
unchunked printf dumps and had 32,618 fuel-outs. The second used chunked dumps without self-limiting and had 8,730.
The final version uses its own trail, aggregates in the next turn when the current turn is short of fuel, and
self-limits the dump at 25k remaining. The profiler is diagnostic only and is compiled out at JD_FUELPROF 0.

### Where suspended turns ran out (JDSUS trails, diag-fprof-06: probe4 maps incl. pf_pool_77041, 80 trails; the engine counted 164 fuelExhausted events, because a turn can suspend more than once)

| crossing interval | count | cause |
|---|---:|---|
| tail -> field | 24 | first champion turn: `build_fields` -> unguarded `prepare_field_order` with ~18k left; resumed on round 2's budget |
| support -> w_vis, support -> wardrev, w_groups -> w_hot | 17 + 5 + 10 | `ward_reveal` labelling a big bush cluster in one go (~72k; the A2_GOV_WARD gate covers only `ward_ahead`) |
| sg_ring -> sg_init (+ sg_los/sg_seeing) | 9 + 4 | siege line-of-sight opacity table built in one go (~65k on 98x98, 6.75 fuel per tile) |
| e_prefight/e_stand -> enemies | 7 | fight execution after the tactical decision (not governed in FEAT-002) |
| c_safe -> c_walked, w_vis -> w_groups | 2 + 2 | walk after a heavy farm selection; world update after a ward |

## 3. Governor (JD_GOV, runtime_budget.h)

`rb::Reserve{observe 20k, decide 25k, execute 20k, tail 6k}` (p99 of each phase's mandatory work, from section 2).
`rb::admit_optional(stage, worst)` admits optional work only if its worst case leaves the reservations of all later
phases (unsigned-safe, same rule as `fits`). `rb::turn_guard()` reports fuel below the tail reservation. The new
stages are kTactical, kRoute, kNN and kPlanCache (admission points for later FEATs) plus kFieldOrder, kSiegeInit and
kWardLabel. Wired bits:
- 1: order preparation only with room for a full field plus the tail reservation (fallback: wait for a turn with room).
- 2: opacity table built row by row with each row admitted, and used only once complete (fallback: the unfiltered
  siege ring).
- 4: resumable bush labelling with a 50k floor (existing X1_BUSHPRE; an unfinished cluster reads as unknown, so
  ward_reveal skips it this turn).

Nothing publishes a partial cache. Conformance results are in LEDGER.md.
