# Trajectory contract `rlenv-1` (task rl-env-collector-1104)

Code: `tools/rl_env_1104/contract.py` (stdlib only; numpy optional for loading). Tests:
`python tools/rl_env_1104/test_contract.py` (8 tests). Engine facts behind each rule: `API_AUDIT.md`.

## Import and call interface

```python
import sys; sys.path.insert(0, "tools/rl_env_1104")
import contract as C

C.CONTRACT_VERSION                  # "rlenv-1"
C.LAYOUTS[4].nf                     # 556 (layout 2: 500); .offset("c"), .width("c"), .count("c"), .self_id_index
C.ACTION_SCHEMAS["target11-v1"].n   # 11: camp-group pointer over the c block, 10 = far

for man, cols in C.iter_shards("runs/<run_ns>", layout=4, split="train"):   # validates each shard; raises on mixing
    X   = cols["x_fresh"]        # int16 [N, 556]  this decision's fresh features
    Z   = cols["x_stale"]        # int16 [N, 556]  slow-part summary in force (has_stale[N] says if present)
    m   = cols["mask"]           # uint8 [N, 11]
    a   = cols["action"]         # int16 [N]
    lp  = cols["logp"]           # float32 [N], NaN where has_logp == 0
    w   = cols["weight"]         # float32 [N]  inclusion weight (1/KEEP subsampling of unchanged rows)
    ...
    man["selected_episodes"]     # present when split= is given: indices into man["episodes"]

man, cols = C.load_shard("runs/<run_ns>/shard_00000")       # one shard; use_numpy=False -> flat stdlib arrays
errors = C.validate(man, cols)                                # [] when valid

w = C.ShardWriter("runs/<run_ns>", base_manifest, max_rows=50_000)
w.done_keys()                     # episode keys already written (resume)
w.add_episode(meta, rows)         # rows: column -> flat list, row-major for 2-D columns
w.flush()                         # atomic: writes shard_XXXXX.tmp then renames
```

## Columns (one row = one logged decision of one body)

| column | dtype | shape | meaning |
|---|---|---|---|
| `x_fresh` | int16 | [N, NF] | features captured this decision (Agent 2 NRL X) |
| `x_stale` | int16 | [N, NF] | summary features in force (NRZ X); zeros if `has_stale`=0 |
| `has_stale` | uint8 | [N] | |
| `feat_round`, `stale_round`, `act_round` | int32 | [N] | capture round, summary round (-1 unknown), action round; `stale ≤ feat ≤ act` |
| `episode` | uint32 | [N] | index into `manifest.episodes` |
| `body_id` | int32 | [N] | engine champion id; must equal `x_fresh[:, self_id_index]` |
| `slot` | int8 | [N] | team slot 0..5 |
| `mask` | uint8 | [N, A] | legal actions; the sampled action must be legal |
| `action` | int16 | [N] | sampled/chosen index |
| `teacher_action` | int16 | [N] | v92's own choice (Agent 2 `bs`), -1 none |
| `executed` | int16 | [N] | action actually applied, -1 unknown |
| `logp` / `has_logp` | float32 / uint8 | [N] | behaviour log-prob; NaN exactly when absent (v92 traces: absent, never invented) |
| `weight` | float32 | [N] | inclusion weight > 0 |
| `changed`, `reset` | uint8 | [N] | target changed; first decision after start/respawn (reset GRU) |
| `reward` | float32 | [N] | reward from this decision to the body's next logged one (`reward_spec`) |
| `dt_rounds` | int32 | [N] | rounds to the next logged decision (discount `gamma**dt`) |
| `terminated` / `truncated` | uint8 | [N] | only on a body's **last** row of an episode, never both; death is not terminal |
| `h0` | float32 | [N, H] | recurrent state before the decision; only when `hidden_size` > 0 |

## Manifest (`shard.json`)

`contract_version`, `layout`, `action_schema`, `hidden_size`, `reward_spec`, `run_ns`, `rows`, `created_utc`,
`columns{name: {dtype, shape}}`, `policy{name, wasm_sha256, build: release|debug, flags[], source_commit}`,
`engine{cambc, engine, engine_build_hash}`, plus collector fields (`fuel_quantum`, `log_limit`). `episodes[]`: `key`,
`map_file`, `map_hash`, `opponent{name, wasm_sha256}`, `side`, `seed`, `status` (terminated | truncated |
truncated_log | failed), `our_team`, `outcome`, `rounds_completed`, `split` (train | dev, by map hash, so both sides and
all opponents of a map stay together), `rows`.

## Rules for the learner

- **Subsampling:** Agent 2 logs every target change but only 1/`A2_NN_RL_KEEP` of unchanged decisions. Weight losses by
  `weight`, and compute returns over `dt_rounds` (rounds actually elapsed), not over row index.
- **Mixed-age observation:** a decision used `x_fresh` (this turn) plus `x_stale` (an earlier summary). Recompute the
  policy from exactly these two vectors; don't rebuild the summary from fresher data.
- **Privileged data:** the match summary/replay may feed `reward` and a critic input built separately; never
  `x_fresh`/`x_stale`.
- **Layouts:** one root per layout; `iter_shards` raises on a mismatch rather than skipping.
- **Terminal handling:** `terminated` → no bootstrap; `truncated` (round cap, timeout, log cut) → bootstrap from V.

## Next slices

1. `collect.py`: builds the bot (release + debug), runs `cambc run-batch` with a raised `--log-limit`, parses NRL/NRZ
   rows and the match summary into shards; v92-only traces get `has_logp=0`.
2. E0 tests on the real engine: visibility (no summary/replay values in actor columns), death/respawn vs terminal,
   deterministic replay, logged-vs-recomputed log-probs, release-vs-debug primitive-action and fuel traces.
