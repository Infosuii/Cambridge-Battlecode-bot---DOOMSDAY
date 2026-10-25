# Overnight report — 2026-10-25

Branch `claude/compare-fix-replay-decoder` (not pushed). Nothing promoted, activated or submitted. heuristic-v1,
references, SDK, maps and engine fuel are untouched.

## Headline

1. **Built:** a complete replay → behaviour-cloning → GPU training pipeline for 7 of the 8 policy heads, with exact
   checks at each stage.
2. **Learning:** the network clearly learns from strong players' replays (validation numbers below).
3. **Blocker:** the trained bot still scores 0 gems, and the cause is not the training. **The neural runtime cannot
   afford to run its own move head:** fuel admission refuses ~98% of move decisions, so champions almost never move.
   No amount of training fixes this. It needs a C++ performance or runtime change, which needs your decision.

## What was built (commits)

| Commit | What |
|---|---|
| `40f19ac` | `compare()` fix + regression test (288 tests pass) |
| `a35bbbf` | Replay decoder (official engine wasm from the cambc visualiser), parallel, compact `.npz` shards |
| `c73c36b` | BC pipeline: `bc_extract.mjs` (observation via the bot's own `Game_API_*` calls), `bc_dataset.py`, `policy_bc.py` |
| `b2acbb1` | + combat and engage heads; buffer-size bug fix |
| `2c3821f` | + strategy, objective, role and bank heads |

The 6 bot-internal inputs use hard-coded rules, as you asked: goal = own position 10 rounds later; role from behaviour;
hot_zone 0; claim code 127. Macro labels are hindsight rules (see the commit messages). `bc_dataset.py` refuses to
write unless sampled rows are **bit-identical** to `observation.encode` / `candidates.build` (5,000 rows checked). That
gate caught a real ordering bug on the objective head, which was fixed before training.

## Data

- Full-day decode (`artifacts/local-only/replays-20261023/`): COMPLETE: 245,607/245,607 replays, 0 failures, 15.8 GB of shards.
  Log: `decode.log` (last event `complete` at 02:14:19, parts 1–10; re-verified by the 03:41 resume task).
- BC pilot: 600 replays → 1.47M train rows (571 matches) + 65k validation rows (27 held-out matches).
  Extraction speed ~10 replays/s on 12 workers.

## Training results (pilot, validation = held-out matches, top-1 accuracy)

| Head | BC model | Majority | Uniform | Untrained |
|---|---|---|---|---|
| strategy | **79.6%** | 60.1% | 17.4% | 12.4% |
| objective | **63.9%** | 11.5% | 8.7% | 0.5% |
| role | **54.3%** | 37.8% | 32.6% | 37.8% |
| move | **50.6%** | 15.8% (hold 22.1%) | 12.0% | 21.9% |
| combat | **94.6%** | 69.9% (hold 78.8%) | 43.8% | 78.8% |
| bank | 59.6% | 59.6% | 26.8% | 24.2% |
| engage | 78.5% | 78.5% | 33.3% | 47.0% |

CUDA (RTX 5070 Ti), ~600k samples/s; a 60-epoch run takes about a minute. Bank and engage learn nothing beyond their
majority class: with 4-wide hidden layers (1,056 parameters in total, a size set by the fuel budget) the model has
little capacity. Shop is not yet extracted.

## Games (6 selection maps × 2 sides, deterministic argmax profile)

| Model | vs heuristic-v1 | vs untrained |
|---|---|---|
| untrained | 0–12, −963 gems | — |
| move-only BC | 0–12, −897 | 6–6 (0:0 tiebreaks) |
| engage+combat+move BC | 0–12, −980 | 6–6 |
| all 7 heads BC | 0–12, −947 | 6–6 |

0 faults and 0 fuel exhaustion in every game. Each of our champions dies once, early, then barely acts.

## The blocker: fuel admission refuses the move head

Telemetry from a recorded game (`direct_untrained` profile = trained model, telemetry on, no logging):

| Head | Starts | Direct (executed) | Fallback |
|---|---|---|---|
| move | 5,756 | **131 (2.3%)** | 5,625 |
| combat | 5,825 | 3,291 (56%) | 2,534 |
| strategy / role / shop | 742 / 191 / 272 | 100% | 0 |

The move and combat decisions are logged as `safety_override`, reason `budget` (admission refused). The same pattern
was already present with the untrained model in the first experiment (move 10% direct, combat 7%). That explains why
the untrained bot scored 0 gems as well.

Measured maximum costs per head (fuel): observation ~19k; move candidates 23k + decision 19k (total ~43k); combat
~40k; strategy/objective/role ~33–40k. The per-turn policy allowance is 82k of the engine's 100k. Observation + combat
+ move does not fit in one turn.

Isolated experiment (disposable copy, not production; `artifacts/claude_ops/experiments/budget_cap_experiment.py`):
capping the move/combat candidate bounds at 30k raised move admission to 12–18% on 00collision but only 0.2–4% on
00elkring. 0 fuel exhaustion, still 0 gems. The bounds are conservative, but **actual** per-head cost is the real
limit.

## Recommended next steps (need your decision)

1. **Fix runtime fuel efficiency (prerequisite for any neural strength).** Profile and cut the per-decision cost.
   For example: compute the observation once per turn and share it; cheaper candidate construction (reuse fields and
   world refresh); cheaper inference (19k fuel for a 1k-parameter model suggests overhead outside the maths). Target:
   observation + combat + move within ~70k. This is C++ in Codex's area and changes fuel-safety code, so I did not
   change production code.
2. **Or a hybrid runtime:** neural macro heads (cheap, periodic, already 100% admitted) driving the original
   heuristic's tactical movement and combat. That needs a per-head teacher fallback in C++.
3. Once the bot can move: run the full-day BC extraction (~4–5 h CPU, ~10 GB), train longer on the GPU (it is
   far from converged), add the shop head, filter to top-rated teams (ratings from the decoded shards; team A/B order in
   member names is unverified, so check it with prediction accuracy), then evaluate and move on to PPO/self-play.

## Leftovers

- Decode finished; no decode process running.
- Resume task `battlecode-night-resume` ran at 03:40. It only checked that the decode had finished and started no
  training, extraction or C++ work, as NIGHT_PLAN.md says. Fuel admission fixes were committed in `153f498` after this
  report was written. NEXT_STEPS.md has the current state: the combat_has_choice fix is still blocked by fuel
  exhaustion on 00quadrants.
- Untracked local outputs: `artifacts/runs/bc-*`, `artifacts/evaluations/bc-*`, `artifacts/tmp/*`, `artifacts/local-only/*`.
