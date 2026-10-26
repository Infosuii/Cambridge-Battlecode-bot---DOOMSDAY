# Agent G report: offline data and later-training pipeline (Wave 1)

Model/runtime: this session's configured model (Claude Opus 5.5 via Kiro CLI). **No training was run.** Nothing
was written to `models/`. No games were played. Every learning step ran only inside unit tests on data labelled
`synthetic`.

## 1. What was built (all files are in my CONTRACTS row G)

| File | Purpose |
|---|---|
| `python/nfs/data/archives.py` | ZIP integrity checks (zero-byte, truncation via EOCD/central-directory/member bounds, CRC for the sample); stable match IDs from member names (`<kind>_<match>_<team>_vs_<team>.camstat`); cross-part de-duplication; bundle-level date proof (filename + platform listing); eligibility filters (date ≥ 2026-10-21, 1.0.1 excluded, 1.0.2 → `draft_observational`, 1.0.3 → `gameplay_1_0_3`, capture complete, rounds ≥ 50, decisive outcome, no bot fault, no 0:0 tiebreak, known champions, draft size); `rule_version`; `gameplay_label_records` refuses 1.0.2 without an explicit tested `EngineAdapter` and refuses 1.0.1 always; experiment-1 ID loader (read-only); cached SHA-256; manifest builder with explicit accounting. |
| `python/nfs/data/splits.py` | Deterministic grouped split (union-find over match id, series/group id, unordered team pair, determinism key = wasm pair + map; partition = SHA-256 bucket of the canonical component key; invariant check). Experiment-1 groups are never `final_eval`. Map- and opponent-generalisation splits by entity holdout (mixed records → `excluded_mixed`). Map provenance: local/previously inspected maps → `reused_benchmark`, never `fresh_holdout`. |
| `python/nfs/data/records_dataset.py` | NFS1 stdout + 1.0.3 summary → `Shard` (`inputs` / `targets` / `meta`, npz + manifest with schema hashes, source identities, counts). Uses B's `nfs.records` if importable, otherwise a reference decoder (B's actual `nn_log.h` layout, including the v1 trailer). Uses C's `nfs.obs` encoder if importable, else an injected one. SMDP interval rewards and returns per (champion, head) stream. Refuses non-1.0.3 summaries and schema-hash mismatches. |
| `python/nfs/train/rewards.py` | Objective-aligned reward split into separately logged, ablatable components: terminal (win/loss/tie from `match.outcome` + clipped margin), deposit, potential-based carry shaping (Φ = c·carried, Φ(terminal)=0), economy, death, damage, objective. Config validation (c ≤ w_submitted). SMDP `interval_rewards`; `series_from_summary` (verified: timeline `gems` = carried); `scale_report`. |
| `python/nfs/train/ppo.py` | PPO with runtime semantics: logits through `PolicyNet.head_logits` (prior + R·act(r/R), illegal −inf, call-site `context` passed); parity check of behaviour logp **and** logged C++ logits before any update; ratio mask (active ∧ sampled ∧ reason ok ∧ legal chosen ∧ finite ∧ observation present ∧ not forced); commitments `option` (merge forced steps with exact γ^τ) or `exclude_forced`; streams per (match, side, champion, head); GAE with variable gaps; clip, entropy, optional teacher-prior KL, grad clip, KL early stop, deadline; metrics: explained variance before/after, critic MAE, entropy, KL, clip fraction, grad norm, reward components, per-head action distribution / off-teacher rate, invalid-action, fallback, budget-skip, shadow, deterministic-active, missing-obs rates, reason counts (names parsed from `nn_head.h`). |
| `python/nfs/train/imitation.py` | Per-head masked cross-entropy to `targets.teacher` (runtime logits), optional value regression, per-head weights (0 = ablated), prior dropout, grouped train/validation guard, early stopping that restores the best state. |
| `python/nfs/train/value.py` | PPO `Critic`; `train_value` (PolicyNet.values win/margin; rows de-duplicated per turn); observational `DraftOutcomeModel` labelled `confounded`. |
| `python/nfs/train/checkpoint.py` | Atomic checkpoints (actor, critic, both optimizers, scheduler, RNG python/numpy/torch/cuda, schema hashes, league, provenance, games ledger, counters, `pairing_id`, parameter hashes). `RunClock` persists one absolute deadline. `GamesLedger` counts each match folder once. Resume refuses an actor-only selection unless `reset_critic_optimizer=True`, refuses schema mismatches and refuses corrupt hashes. |
| `python/nfs/train/league.py` | Pinned-SHA league: original (`reference`, minimum share), v47/first-hour/v50 (`historical_release`), frozen self (capped), draft proxies labelled "NOT a real top-team executable"; deterministic sampling with saved state; per-opponent `anti_regression`. |
| `python/nfs/train/collect.py` | Copies `bot/src`, installs a profile with B's `install_models.py --src … --receipt …`, builds with the official CLI, plans content-addressed jobs (job.json with both wasm SHA-256s, map, determinism key), runs `engine.run_jobs` with a configurable worker count, torch threads and a 64 MB log limit, accounts games in the ledger. |
| `python/nfs/train/auth.py`, `common.py` | `--i-authorize-training` + time-limit gate; deadlines, early stopping, partition guards. |
| `python/nfs/cli.py`, `tools/nfs.py` | Subcommands `inspect-data, index-archives, build-splits, collect, build-dataset, pretrain, train-value, rl, export, benchmark, promote`. `pretrain/train-value/rl` refuse without `--i-authorize-training` AND a time limit in (0, 1440) min. `collect` needs `--i-authorize-collection`, `--max-games` and a time limit. `promote` calls H's `nfs.evaluate.gate.evaluate_files` and refuses if it is absent; on PASS it writes a receipt and leaves the status change to B's registry tools. `tools/nfs.py` includes a guard so other `tools/*.py` scripts still import the real package (see CONTRACT_ISSUES 1). |
| `configs/train/*.json` | `first_experiment.json` (bounded: objective head only, 30 min, ≤ 480 games, 8 workers, H's 18 training maps, original ≥ 50 % of games; stop criteria listed), `rl_default`, `pretrain_default`, `value_default`, `collect_teacher`, `reward_default`. |
| `tests/python/_fakes.py` + `test_data_*.py`, `test_train_*.py` | Synthetic fixtures; the real B `PolicyNet` is used when it builds (it did), otherwise a contract fake. |
| `data/manifests/*`, `data/archive_sample_v1/`, `data/audit_samples/` | Bounded index outputs (section 3). |
| `archive/agents/G/DATA_AUDIT.md`, `CONTRACT_ISSUES.md` | Content audit; interface problems. |

### Design notes
- **Commitments:** the default is `option`. One logged decision covers the whole commitment. The interval reward is
  discounted round by round, and bootstrapping uses γ^τ (SMDP), so forced steps never enter the ratio. B's reason
  enum has no forced code, so this assumes hooks log only when an option starts (CONTRACT_ISSUES 6).
- **Deployed vs sampled:** PPO optimises the sampled training policy (only `sampled=1` rows enter the ratio). Records
  from deterministic argmax runs are logged and excluded. Evaluation must test the deployed argmax build with H's
  gate. The per-head off-teacher rate is reported for both kinds of data.
- **Reward scale:** γ = 0.9997 per round (0.9997^2000 ≈ 0.55), so the terminal objective still reaches early
  decisions. On an existing official 1.0.3 match (read-only fixture), per-champion discounted dense terms were
  0.10–0.27 against a win term of 0.63 seen from round 0. The terminal ±0.70 dominates, and the losing team's
  positive deposits do not outweigh it.
- **Experiment-1 data:** its 4,000 IDs are labelled `already_used_by_experiment_1`. They are excluded from the fresh
  sample and are never `final_eval`.

## 2. Commands run (bounded, non-learning)

```
python tools/nfs.py index-archives --sample-per-part 190 --consistency-checks 10 --workers 8   # 167 s, incl. SHA-256 of 4 × ~820 MB
python tools/nfs.py build-splits
python -m unittest discover -s tests/python -p "test_data_*.py"     # PYTHONPATH=python
python -m unittest discover -s tests/python -p "test_train_*.py"
```
Before indexing I checked that `neural-gameplay/historical-training/ingestion.lock` is absent and that no Python
ingestion process was running. The command itself refuses if the lock exists. A plumbing build of the `training`
profile (`collect.build_profile_bot`) into `artifacts/tmp` succeeded with the official CLI. At that time every head
was off because C's `nn_obs.h` was missing. `bot/src` was not modified. The scratch directory was deleted.

## 3. Bounded index numbers (`data/manifests/archive_index_v1.json`)

| Field | Value |
|---|---|
| archive_entries (4 admitted parts) | 93,606 (23,401 / 23,437 / 23,415 / 23,353) |
| unique_match_ids / duplicate_entries_dropped | 93,606 / 0 |
| zero-byte duplicate part 1 | skipped (`zero_byte_duplicate_part`) |
| sampled_entries | 800 (760 fresh = 190/part + 40 experiment-1 consistency) |
| CRC / conversion errors in the sample | 0 / 0 |
| engine versions, fresh sample | 1.0.2: 590, 1.0.1: 170, **1.0.3: 0** |
| accepted_independent_matches (fresh) | 571, all `draft_observational`; `accepted_gameplay_1_0_3` = 0 |
| rejected by reason (fresh) | engine_1.0.1_excluded 170, zero_score_tiebreak 15, too_few_rounds 2, bot_fault 2 |
| per_turn_observations / augmented_samples / epochs | 0 / 0 / 0 |
| experiment 1 | 4,000 IDs known, all found; 3,070 accepted, **all 1.0.2**; 920 × 1.0.1; 7 forfeits without a recorded version; 40/40 engine agreement on re-check |
| archive maps | 40 distinct, all equal to local arena maps → `reused_benchmark` |
| splits (`splits_v1.json`, 596 accepted rows) | grouped 498/50/48 (542 groups, largest 5, 1 exp-1 group moved out of final_eval); map 403/39/154 (9 held-out maps, all reused); opponent 283/4/23 + 286 mixed excluded |

Implication: the four local archives cannot supply engine-1.0.3 gameplay labels (95 % upper bound ≈ 59 entries in
total, from 0 of 4,753 sampled entries with a known version). The remaining unsampled entries are not "unused compatible games".

## 4. Test results

- `test_data_*.py`: **35 tests, OK.** Covers archives (16: zero-byte, truncated, not-zip, bad CRC, duplicate IDs
  across parts, wrong/unproven dates, listing mismatch, 1.0.1/1.0.2/1.0.3/unknown engines, 1.0.2 refusal and
  adapter rules, status/completeness/rounds/score/draft filters, experiment-1 labelling, sample cap, accounting
  fields, SHA cache, deterministic sample), splits (9) and records/shards (10).
- `test_train_*.py`: **47 tests, OK.** Covers rewards (10: bank-and-win > collect-then-die across configs; losing a
  bag nets exactly 0 shaping; telescoping on random trajectories and variable SMDP gaps; scale on a synthetic game
  and on a real 1.0.3 summary), PPO (9: runtime formula, logp + logit parity of B's real PolicyNet against B's
  bit-exact numpy C++ twin, mismatch detection, ratio mask, option merge, variable-gap GAE, stream separation,
  synthetic update + refusal, KL early stop), checkpoint (8: RNG + optimizer + scheduler round trip with bit-exact
  continuation, persisted deadline, ledger, actor-only refusal, pairing, schema/corrupt refusal),
  imitation/value (6: refusal, synthetic loss decrease, head ablation, grouped/final_eval guards, early stop,
  confounded draft model), and CLI/collect/league (14: refusal without flag or time limit, collect refusal, sample
  cap, promote refusal/gate verdict, export refusal, config parsing, content-addressed folders, ledger, league
  share/proxy label/state/frozen cap/anti-regression).
- Total: **82 / 82 pass** (torch 2.11.0+cu128, CUDA available; tests ran on CPU).

## 5. Verified vs not verified

Verified (by tool output): the archive integrity/date/engine findings above; the experiment-1 overlap; that the
filters and refusals behave as specified on synthetic zips; logp/logit parity of the PPO path against B's C++-twin
reference on synthetic weights; checkpoint resume reproducing the next optimizer step exactly; the official build
of a training-profile copy; that every parameter-updating command refuses without authorization.

Not verified:
- End to end on **real** NFS1 records: no engine run has produced records yet (C's encoder/`nfs.obs` and B's
  `nfs.records` were missing when this ran). The decoder follows B's `nn_log.h` source, not observed bot output.
- The `rl` loop glue (`cmd_rl`: export → install `--model <dir>` → collect → update → checkpoint) and `collect` with
  real games were not executed: running them would be training or self-play. `install_models.py --model <dir>`
  support is unconfirmed.
- The champion handle → summary id mapping (`order_assumed` fallback).
- Replay-based observation reconstruction (not implemented). CRCs of members outside the sample.
- That the samples represent all 93,606 entries (SHA-256 order of UUIDs; the parts appear to be UUID ranges).

## 6. Contract issues

See `archive/agents/G/CONTRACT_ISSUES.md`: the `tools/nfs.py` name clash (fixed by the guard; renaming recommended); the
NFS1 layout differing from CONTRACTS 3.5; the `nfs.records` / `nfs.obs` APIs; champion identity; marking forced
commitment steps; the `teacher_record` and per-head training profiles; `install_models --model <dir>`; `context` in
`head_logits`; engine folder trust and log limit; the absence of 1.0.3 entries in the archives.
