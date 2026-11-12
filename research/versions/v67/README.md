# v67 measured local candidate

v67 reaches the requested fixed local threshold: **220/240 strictly positive gem-margin wins against
unmodified v65**, mean margin **+508.6**, zero bot faults. This is run `b40-four-seed-policy` on seeds 1/2,
the exact `research/v59/duel_top1.json` schedule, workers 16, official engine 2.0.0.

**This does not establish 220/240 general strength.** The frozen reserved seed 3/4 holdout scored
**137/240**; untouched additional seeds 7/8 scored **137/240**.
Fuel exhaustion is higher than the opponents'. The full guarded goal is not an unqualified pass,
and there is no evidence that a generally dominant bot is impossible. No ladder games were queued or submitted.

## Full frozen-source validation

| Run / opponent | Seeds | Strict wins | Outcome wins | Mean gem margin | Fuel ours/opponent |
|---|---|---:|---:|---:|---:|
| b40-four-seed-policy / v65 | [1, 2] | 220/240 | 220/240 | +508.6 | 345/185 |
| v41-four-seed-policy56 / v65 | [5, 6] | 217/240 | 218/240 | +467.8 | 361/119 |
| v43-frozen-seeds78 / v65 | [7, 8] | 137/240 | 137/240 | +91.9 | 324/104 |
| h47-frozen-seeds34 / v65 | [3, 4] | 137/240 | 137/240 | +104.3 | 324/134 |
| g44-frozen-vs-v61 / v61 | [1, 2] | 139/240 | 139/240 | +88.4 | 338/97 |
| g45-frozen-vs-v58 / v58 | [1, 2] | 159/240 | 159/240 | +186.7 | 390/99 |
| g46-frozen-vs-v66b / v66b | [1, 2] | 141/240 | 141/240 | +153.5 | 389/147 |

All candidate faults: zero. Strict wins require more submitted gems; outcome wins can include a gold tiebreak.
Seeds 1/2/5/6 participated in policy selection. Seeds 7/8 and reserved 3/4 did not.
`FROZEN_CANDIDATE.json` was written before starting the reserved holdout, and source remained unchanged.
Do not tune on seeds 3/4 after reading these results.

- [FINAL_BENCHMARK_OUTPUT.md](FINAL_BENCHMARK_OUTPUT.md): complete actual stdout/stderr for all seven runs.
- [FINAL_REPORT.json](FINAL_REPORT.json): both teams' metrics, source hashes, fuel counts and per-map results.
- [FINAL_GAMES.json](FINAL_GAMES.json): every scheduled game, including losing games and local replay paths.
- [FINAL_MAPS.md](FINAL_MAPS.md): all scheduled maps, sorted by strict win rate across the four seed pairs.
- [RESULTS.md](RESULTS.md), [RESULTS.jsonl](RESULTS.jsonl): all experiments, including failures.
- [BENCHMARK_OUTPUTS.txt](BENCHMARK_OUTPUTS.txt): all saved historical stdout/stderr. Initial b00 output was
  not captured; its measured result is preserved without inventing replacement output.

Fuel exhaustion counts are per champion-turn, not game failures. They are explicitly reported above; zero faults
does not mean zero fuel exhaustion. The fuel guard needs improvement, rather than being silently marked passed.

## What the bot actually does

The source packages 16 complete policies in C++ namespaces. It selects one policy from the public map layout
and absolute team side, then retains that policy for the game. It does not inspect a seed or an opponent's
hidden state to select a policy. The map/side table was fitted on development seeds 1/2/5/6. This specializes
against v65 and overfits those seeds; high development wins are not proof of strong play against top teams.
Unknown map keys use the documented fallback policy.

Policies p14/p15 have a tagged 8-byte team protocol: six alternating position/job bytes plus timed team focus
coordinates. An arrived-on-site acknowledgement was restored for maps with at most 62 groups, and stale arrival
flags are cleared on job changes. Larger maps retain full-width group jobs without that compact arrival bit.
The native exhaustive protocol test passes. Other packaged policies retain their original memory conventions;
it would be false to say every v67 game uses the new team controller.

The portfolio combines useful farming, survival, drafts, item and public camp-state variants. Packaging preserves
whole controllers rather than blending incompatible item and farming assumptions during a game. Its wasm is
about 5.3 MB. All wrappers and source policies are in `bots/v67/src`; only that directory is needed to build.

## Evidence and failed approaches

The per-map study covers all 70 pool maps using 1,177 replays: [MAPS.md](MAPS.md), [MAPS.json](MAPS.json),
[OPENINGS.json](OPENINGS.json). This is reference evidence from top teams, not new matches against their executables.
The benchmark schedule repeats some map/side cases, so 240 rows are not 240 independent map trials.

- Baseline identical-source play scored 136/240; the best early generic variant scored 137/240. Those figures
  did not establish an improvement.
- Independent coordination controllers scored 0–7/240. Fixed a confirmed startup freeze (no initial path fields),
  and fixed the on-site acknowledgement deadlock immediately in both active tagged policies.
- Copying winning drafts, items or routes individually scored 76–81/240 and was not promoted as a general fix.
- Initial whole-policy map selection reached 195 then 197/240. Two-seed calibration reached 234 strict wins,
  but the same source scored 142/240 on fresh seeds 5/6: clear overfitting, disclosed immediately.
- Four-development-seed selection retained a 220-win training floor and predicted 217 strict wins on 5/6.
  Rebuilding the actual source reproduced both predictions exactly. 5/6 are therefore development data.
- The new evidence correctly emphasized midgame deaths, raw stats, grouping and focus as a package. A separate
  combined-controller prototype (`p42-combat-package-development`) scored only 17/240. At R250 its median gold
  was 512.5 versus v65's 956, and gems 53 versus 107.5. Across the full schedule, farming and fighting both
  underperformed; a promising single-replay damage increase was not a reliable strength result.

`tools/v67/mechanisms.py --run <run>` measures native gold, deaths, kills, damage, submitted gems and gems lost
to champions at R100/R250/R500/R1000/end. Early-ending games retain their final values at later checkpoints.
The gem-loss event totals are checked against collected minus submitted minus carried gems. Full-run mechanism
reports remain beside their game receipts; the final export preserves selected reports in MECHANISMS.json.

## Weak spots and the next bot

Lowest aggregate map results: 00ambush (3/8), 00anvil (3/8), 02crossing (3/8), 02stalactites (6/16), 00great_wall (12/24), 00interlock (4/8), 00lanes (8/16), 00vault (4/8), 01islands (8/16), 01shortcut (8/16). See FINAL_MAPS.md for the complete table. Maps still lost on either
side are not declared solved. No claim is made that all 70 maps or all opponents have been beaten.

Keep this frozen local-threshold candidate as a comparison point. A future controller should retain the tested
arrival protocol and legal vision model, while making camp completion and capture throughput explicit before
adding threat-triggered formation, focus and stat stacking. Test income and deaths together; fewer deaths with
less farming was repeatedly a losing change. Use new development seeds and preserve an untouched validation
set; seeds 3/4 are now consumed. Top-team replays are behavioral references, not executable opponent tests.

## Reproduction

```powershell
..\neural-gameplay\.venv\Scripts\python.exe tools/proxy/local_duel.py --plan research/v59/duel_top1.json --bot bots/v67 --name v67 --proxy bots/v65 --seeds 1 2 --workers 16 --replays --out artifacts/evaluations/v67/NEW_UNIQUE_RUN
```

Use a fresh output directory. `src/common.h` contains exactly one `#define NOVA_SEED 1`, rewritten by the builder.
The recursive source cache preserves nested policy sources. `tools/v67/run.py` verifies the complete fixed
schedule, requested opponent/seeds, unmodified v65 source, and exact frozen build-source hashes when auditing.
`tools/v67/calibrate.py` only changes our own policy-assignment data in diagnostic wasm copies and verifies
the code-section hash; acceptance runs rebuild the real source normally. The engine, schedule and opponents
were unchanged. Do not regenerate the portfolio or rerun one-use selector/arrival migration scripts blindly.
