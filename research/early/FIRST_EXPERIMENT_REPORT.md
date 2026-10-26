# First bounded ROLE experiment — report (2026-10-24, Claude Opus 5.5 via Claude Code)

Repo `main` @ `5f8ecc3`, plus one uncommitted bug fix (below). CUDA interpreter from `config/paths.json`
(Python 3.12.14, torch 2.11.0+cu128, RTX 5070 Ti Laptop 12 GB, driver 616.92). cambc 3.0.5, engine 1.0.3, default fuel.
Nothing promoted, activated, submitted or pushed.

## 1. Existing data

**Summaries** (`match summaries 23102026`, full audit in `artifacts/datasets/summaries-23102026-audit/AUDIT.md`):
10 ZIPs, 245,607 unique matches (121,061 ranked, 124,546 unranked), 0 duplicates, all engine 1.0.3 in a 400-match
converted sample, ~95.5% outcome-eligible. They contain no observations, legal actions, chosen actions, logits or roles,
so they produce **0 rows** for any policy head. Usable later only for outcome/value/draft modelling.

**Replays** (`match summaries 23102026/math replays`, parts 1/2/5 complete, 3/4/6/7 downloading): `.repl26a`, about 24.5k
per part, ~160 KB each, same match IDs as the summaries. Undocumented binary format; no decoder exists in the repo,
SDK or CLI (`cambc view` only opens the visualiser). They probably hold full per-turn state, and that makes them the
only possible source of strong-player behaviour. Using them needs (a) a decoder, (b) exact reconstruction of each
team's fog-limited observation, (c) mapping each observed action onto our per-head candidate sets as imitation labels.
None of these exists yet. Not used in this experiment.

## 2. Collection (12 new games — the cap)

| Batch | Seed | Games | Faults | Invalid recs | Fuel exh. | Parity max err | PPO-eligible role rows | Result |
|---|---|---|---|---|---|---|---|---|
| 1 | 20261025 | 6 | 0 | 0 | 0 | 1.19e-7 | 588 | 0 W, 0 gems every game |
| 2 | 20261026 | 6 | 0 | 0 | 0 | 1.19e-7 | 586 | 0 W, 0 gems every game |

00rows, sides A/B, vs original/v47/first-hour. `prepare` → `artifacts/datasets/role-first`: train 980 eligible rows
(10 matches, 5 groups) and validation 194 (2 matches, 1 group), disjoint. `preflight` PASS. Imitation rows 0 (no teacher labels).

## 3. Fitting (CUDA)

- `artifacts/runs/role-first`: 8 updates / 2 epochs, then **stopped on the gate `evaluation_error`** because of a bug (section 5). Preserved.
- `artifacts/runs/role-first-r2` (same data, seed and limits, fresh dir, after the fix): **16 updates, 4 epochs, stop
  `epochs_complete`**, 63 s wall time including two in-fit evaluations. Epoch-2 actor/critic are bit-identical to run 1 (reproducible).
- PPO loss −0.0031 (flat), approx KL ≤ 1.0e-7 (gate 0.015), entropy 1.04–1.07 (gate 0.05), grad norm ≤ 0.04, critic
  loss 0.67 → 0.067. Only `heads.role.*` changed (max |ΔW| 1.4e-3).
- GPU: peak 25% util, 710 MiB, 47 °C (nvidia-smi at 500 ms). Total fitting time across both runs ≈ 35 s of optimisation.
- Note: the dataset's "validation" split is only a parity/leakage gate; no validation loss is computed by design.

## 4. Evaluation (deterministic argmax profile, 6 selection maps x 2 sides)

| Candidate | Opponent | W-L | Mean gem margin | Faults / fuel exh. |
|---|---|---|---|---|
| untrained | heuristic-v1 | 0-12 | −963 | 0 / 0 |
| role-first-r2 export | heuristic-v1 | 0-12 | −963 (identical games) | 0 / 0 |
| role-first-r2 export | untrained | 6-6 | 0 (all 0:0 at 2000 rounds, tiebreak) | 0 / 0 |

The trained head changes the argmax role in **0 of 1,174** recorded role states (max Δp 3e-4, median top-2 logit gap 0.016).
**No learning of playing strength was demonstrated.** This is the expected result, not a pipeline failure.

## 5. Engineering change

`python/nfs/policy/operations.py::compare` installed source copies under its `--out` directory, but `install_policy_v2`
only allows `artifacts/tmp`. So every in-fit evaluation (`artifacts/runs/...`) and every documented manual compare
(`artifacts/evaluations/...`) failed. Earlier verification only ran with out under `artifacts/tmp`, and the unit test
mocked `compare`. Fix: disposable sources are built in `artifacts/tmp/comparison_builds/<ns>`, recorded as
`plan.build_root`; Wasm, games and receipts stay in `--out`. Added a regression test that fails on the old code with
the real error. Suite: 288/288 pass (`research/early/logs/tests_after_compare_fix.log`). Revert: `git checkout -- python/nfs/policy/operations.py tests/python/test_policy_operations.py`.

## 6. Why nothing was learned (root cause)

1. Collection profiles set `NN_POLICY_V2 1` with the default `NN_POLICY_HEAD_MASK 510`, so **all eight untrained heads**
   control the bot. Movement, banking and combat are random, and the bot scores 0 gems in every game.
2. All returns are therefore losses (range −1.04 to −0.75, std 0.057). The only variance is discounting by round, so
   the advantage mostly says "later decisions look better". There is no information about which roles win.
3. A disabled head does not fall back to the heuristic teacher (`fallback()` ends the turn), so a "neural role + heuristic
   rest" profile does not exist without a C++ change.
4. With lr 1e-4, a 256-row batch, ~4 updates per epoch and a 1,056-parameter model, any run within these limits moves
   the weights by about 1e-3.

## 7. Recommendation — do NOT run the 2-hour session as role-only PPO

Two hours of the current loop would repeat steps 1–2 about 100 times on the same no-signal data, and GPU use would
stay near 0%. That would burn time without improving play. Recommended order:

1. **Teacher-annotation imitation (largest lever).** Record the heuristic teacher's choice for every head's candidate
   set in our own locally simulated games (unlimited, offline), then supervise all eight heads to reach heuristic-v1
   parity. This is the documented missing "teacher-annotation collection adapter". Data scales with games, so a
   2-hour GPU session becomes meaningful here.
2. **Hybrid collection profile** (per-head teacher fallback) for PPO after imitation, so games have non-zero, varying outcomes.
3. **Draft network retrain** from ~234k eligible 23-Oct summaries, using local map files for the 53-feature input.
   Observational, so confounded by team strength. Evaluate against the inherited draft net in games.
4. **Replays:** first build and validate a decoder on a sample. The `cambc view` web visualiser decodes `.repl26a`
   in the browser, so its JS bundle is the likeliest format reference. Finish the in-progress downloads, but hold
   off on downloading many more until a decoder works on a sample.
