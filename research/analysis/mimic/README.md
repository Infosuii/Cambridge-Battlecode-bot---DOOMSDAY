# Mimic: replay-trained opponent, 2026-10-27

Mimic is a new bot with its own observation, memory, objective selection, movement, target and spell code. It does
not use v65's executor. Its models imitate top-team replays; draft and item tables are shared with the earlier proxy.

**Status: working research prototype, still much weaker than the top teams.** The completed v9 run loses all
240 games against v65, by 913 gems on average. The real top teams beat v65 by 386. On the six existing ladder arms,
mimic's margin ordering agrees with 14/15 ladder pairs (self-play: 9/15), but this is a small, retrospective result,
not evidence that mimic is a reliable release gate. Nothing was submitted or activated.

## Architecture and data

`bots/mimic/src/core.cpp` and `core.h` contain the SDK-free observation, memory, candidate and feature code. The
same core is compiled into the runtime and `tools/mimic/kernel.cpp`, a WASI reactor driven by `extract.mjs`.
Features use only that champion's legal view, static map knowledge, past observations, and coarse allied positions
from the team's eight shared bytes. Observation and feature hashes are checked against actual local replays.

The models are conditional logits for objectives, moves, basic attacks and spells, plus logistic recall and tribute
decisions. Fits are hierarchical: pooled, then per hero for move/target/cast, then per team. Runtime action selection
first compares the summed probability of acting with doing nothing, then chooses the best acting candidate.
Recall uses a sampled per-turn hazard. Objective choices have a 0.5 logit commitment bonus and normally refresh
every third calm turn. Drafts, item milestones and the recall-cancellation habit come from the imitated team's table.

Training uses 1,177 engine-2 replays: 120 top-team games against v65 and approximately 1,050 top-versus-top games.
The replay corpus and binary rows remain local under `artifacts/local-only/`. Objective labels use the next event
within 60 rounds, with bank/home trips relabelled. These future events are labels, never observation features.
Entire matches are held out by match number modulo 10. The v9 feature widths are objective 65, move 36, target 19,
cast 24, recall 10 and tribute 6. Weights and provenance are in `weights.h` and `MODEL.json`.

## What the investigation found

1. **Recall cancellation froze five teams.** The runtime read action permissions while recalling, cancelled the
   recall, and cleared only the recalling flag. Movement, attack and cast permissions stayed false in that stale
   observation. Cancellation now happens before observing. The extractor also reads the post-cancel state for
   these turns; the old extractor incorrectly excluded about 400,000 movement and 817,000 spell examples. A focused
   NEETCoders reproduction on 00quadrants changed from zero gold/collected gems to 916 gold and 306 collected gems
   with the cancellation fix and otherwise unchanged v8 weights. Trace logging changes fuel use, so this is a bug
   reproduction, not a strength benchmark.
2. **Partially cleared groups had dead navigation roots.** Static fields target all spawn tiles, including dead
   monsters. Local objective distance now accounts for surviving visible or bush-hidden camps, preventing an
   apparent arrival outside the survivors' attack range.
3. **Empty groups and shared captures wasted time.** Known respawning groups are excluded until their return is
   within travel time plus five rounds. A visible reward is assigned to the nearest visible ally, with champion ID
   breaking ties. A champion already on its region keeps ownership; coarse remembered positions cannot claim it.
   Seven objective interactions describe availability, crew, redundant effort and capture coverage; four movement
   features describe capture holding, waiting and camp damage.
4. The old fuel probe formatted every stage and spent roughly 2.3k fuel per mark. It now records counters cheaply
   and formats after actions/shared-memory writes when budget permits. Explicit SIMD scoring is covered by tests.
5. Parity previously reconstructed ideal end-of-turn shared writes. Fuel suspension can delay the real write.
   Parity now replays each actual shared-memory read snapshot, retaining strict observation/memory/feature
   comparisons. Ordinary training still simulates uninterrupted shared writes from past turn-end positions.

## Training and parity

All 1,177 v9 replays extracted without errors. The dataset has 474,681 objective, 1,642,523 move, 2,500,427 target,
2,706,806 cast, 8,668,332 recall and 99,302 tribute rows. See `TRAINING.md` for held-out counts and losses.

| Decision | Held-out per-team accuracy | Rule/base-rate accuracy |
|---|---:|---:|
| Objective | 0.621 | 0.539 |
| Move | 0.683 | 0.463 |
| Target | 0.943 | 0.764 |
| Cast | 0.919 | 0.885 |
| Tribute | 0.715 | 0.487 |
| Recall | 0.988 | 0.988 |

Objective accuracy excludes unavailable/delegated labels: 72,800 labels were omitted, versus 51,068 in v6/v7.
The corrected cancellation state also changes the move/target/cast test populations. These accuracies are not
directly comparable across all revisions. Recall accuracy mostly reflects its low base rate.

Final parity: five pooled-policy maps plus two NEETCoders maps (`p12`, `p12-neet`), **39,288 observations and
memories, 37,867 complete-field decision hashes, 1,484 distance fields, zero mismatches**. Decision hashes before
all fields exist are explicitly skipped, since runtime then uses distance fallbacks. Core regressions pass in the
actual WASI/SIMD build and native C++; they cover partial clears, reward ownership, respawn exclusion, shared slots
and numerical scoring. See `PARITY.json`.

## Local results

The same 120-game map/side/team schedule is used throughout. Positive margins below mean v65 wins.

| Revision | Change | Games/seeds | v65 margin | Mimic wins |
|---|---|---:|---:|---:|
| v6 | Handoff baseline | 120 / 1 | +967.8 | 0 |
| v7 | Partial-clear pathing, coordination/threat features, SIMD | 120 / 1 | +987.4 | 0 |
| v8 | Capture ownership and respawn availability | 120 / 1 | +973.9 | 0 |
| v9 | Cancel before observing; restore excluded training rows | 240 / 2 | +912.6 | 0 |

The matched seed-1 improvement over v6 is 52.9 gems, SE 25.9 clustered by the 61 distinct maps (approximate 95%
interval 2 to 104 gems). This is modest and close to the uncertainty boundary. v9 has 83.1 fuel suspensions/game
versus 55.6 in v6; restoring actions increases work. Mimic's own native summaries report zero engine faults across
all 1,440 validation games (`NATIVE_CHECKS.json`); runtime still catches action errors. Fuel suspensions remain an unresolved limitation.

Opening economy comes from actor ledgers at round 250. Gold is capture income, per team per game. Clear, idle and
travel shares are fractions of living champion-rounds; full-game style gold is a separate earned-gold proxy.

| At round 250 | v8 mimic (120 games) | v9 mimic (240 games) | Real top teams vs v65 (120 games) |
|---|---:|---:|---:|
| Capture gold | 235.4 | 407.5 | 770.6 |
| Capture gems | 35.7 | 67.4 | 150.0 |
| Capture gold per 100 living turns | 24.1 | 45.5 | 71.0 |
| Clearing share | 0.105 | 0.204 | 0.202 |
| Idle on spawn | 0.357 | 0.096 | 0.037 |
| Idle off spawn | 0.237 | 0.102 | 0.121 |
| Travel share | 0.257 | 0.530 | 0.527 |

The populations differ by the second seed; this table is descriptive. It establishes that the severe freeze is
gone and that similar time allocation still produces much lower rewards. Full-game gold rises from 1,017 in v6
to 2,122 in v9, versus 6,773 for the real teams. Fighting remains the next bottleneck: v9 deaths 20.5/game versus
6.6 for top teams; back-off rate 0.217 versus 0.263, walk-in 0.349 versus 0.380. Low-health contact still ends in
death within five rounds about 64% of the time. See `ECONOMY.json`, `STYLE.md` and `LOCAL_RESULTS.json`.

Stable randomized objectives and forced departure from healthy spawn were explored on 24-game subsets before
the cancellation diagnosis. Their margin changes were small; neither rule is retained in the bot.

## Ladder-arm validation and limits

All six arms (v60, v61, v62c, v65, v66a, v66b) played 240 games each against the per-team v9 mimic. The existing
self-play control has one seed per arm. See `VALIDATION.md` and `VALIDATION.json` for every arm/team/pair.

| Opponent | Team difficulty r | Arm rank correlation | Pairs agreeing | Per-game r |
|---|---:|---:|---:|---:|
| Mimic v9, two seeds | +0.18 | +0.94 | 14/15 | -0.13 |
| Self-play v65, one seed | -0.44 | +0.43 | 9/15 | -0.01 |

The ordering is encouraging: v65 stays above v66a/v66b and v61, which self-play gets wrong. However, all six arms
win every local game, their local means span only 21 gems, most paired intervals overlap zero, and the ladder
itself decides only one of 15 pairs at two SE. Team and per-game difficulty are poorly reproduced. The comparison
is retrospective, uses unequal seed counts, and includes maps/teams and v65 replay evidence used in training.
Do not tune a release against these six arms or infer demonstrated superiority from the 14/15 count. A new
prospective set of bots and games is needed.

## Reproduce (PowerShell, from repository root)

```powershell
$mimicPython = '..\neural-gameplay\.venv\Scripts\python.exe'
& $mimicPython tools/mimic/test_core.py
& $mimicPython tools/mimic/build_kernel.py
$env:NFS_REPLAY_ENGINE = '2.0.0'
node --no-warnings tools/mimic/extract.mjs --index artifacts/local-only/proxy/replays/index.json --replays artifacts/local-only/proxy/replays --teams research/v59/duel_top1.json --out artifacts/local-only/mimic/rows-fresh --workers 12
& $mimicPython tools/mimic/train.py --rows artifacts/local-only/mimic/rows-fresh --out artifacts/tmp/mimic/weights-fresh.h --report artifacts/tmp/mimic/train-fresh.md
Copy-Item artifacts/tmp/mimic/weights-fresh.h bots/mimic/src/weights.h
& $mimicPython tools/mimic/parity.py --out artifacts/evaluations/mimic-parity/fresh
& $mimicPython tools/mimic/parity.py --team 4 --maps 00quadrants 01fracture --out artifacts/evaluations/mimic-parity/fresh-neet
& $mimicPython tools/proxy/local_duel.py --plan research/v59/duel_top1.json --bot bots/v65 --name v65 --proxy bots/mimic --per-team --seeds 1 2 --workers 12 --replays --out artifacts/evaluations/mimic-duel/fresh-v65
& $mimicPython tools/mimic/economy.py --index artifacts/evaluations/mimic-duel/fresh-v65/replays/index.json --replays artifacts/evaluations/mimic-duel/fresh-v65/replays --out artifacts/evaluations/mimic-economy/fresh
```

Use fresh output directories. Extraction refuses nonempty directories and exits nonzero on failed replays;
training rejects incompatible feature widths or failed extraction manifests. `trace.py --team 4 --out <fresh-dir>`
builds a decision trace; add `--fuel` for the lower-overhead budget probe. Trace output is written to `a.txt`/`b.txt`.
For validation, repeat `local_duel.py` for the other five arms and pass the six directories to
`tools/proxy/compare.py --ladder research/proxy/ladder_arms.json --run mimic=<comma-separated-dirs>`.

## Next work

1. Keep post-cancel permissions and the perma-team parity regression intact.
2. Reduce fuel suspensions, particularly objective-plus-move-plus-spell turns, without weakening observation parity.
3. Measure reward yield per clear and camp deaths. Clearing time now matches the reference; gold/gems do not.
   Test crew/route/reward ownership together, using opening ledgers and matched seeds.
4. Learn or implement a richer retreat/action-order policy, checked against low-health and outnumbered fight rows.
   More held-out accuracy from the current independent logits has not implied competitive strength.
5. Validate any next candidate on fresh opponents/variants rather than repeatedly selecting on these six arms.
