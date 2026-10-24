# Agent G: contract issues and requests

1. **`tools/nfs.py` shadows the `nfs` package (lead, everyone).** Scripts in `tools/` run with `tools/` as
   `sys.path[0]`, so `from nfs import export` in `tools/install_models.py` imported the CLI file and failed
   (`'nfs' is not a package`). Fixed inside `tools/nfs.py`: when it is imported as a module it loads the real
   `python/nfs` package and replaces itself in `sys.modules`. I verified that `install_models.py --help` and
   `tools/nfs.py --help` both work. Recommendation: rename the CLI to `tools/nfs_cli.py` (CONTRACTS row G) to remove
   the trap altogether.
2. **NFS1 layout differs from CONTRACTS 3.5 (B, lead).** B's `nn_log.h` (a) prefixes the turn-context payload with
   `u32 byte count`, and (b) appends a v1 decision trailer `u32 action_hash, u16 call, i16 net, f32 logit[K]`. My
   reference decoder implements B's layout. The PPO parity check also compares the logged C++ logits, not only
   logp. Please update CONTRACTS 3.5.
3. **`nfs.records` API (B).** It is not present yet. `records_dataset.decoder()` probes `decode_stdout`,
   `parse_stdout`, `decode_text`, `iter_records` and `decode_lines`, and normalises dicts, dataclasses and
   namedtuples. Please expose `decode_stdout(text) -> list[dict]` with keys `kind, version, schema_hash, round,
   champion, head, K, F, teacher, chosen, mode, reason, context, sampled, logp, prior, legal, id, feat` (+ `payload`
   for kinds 0/2, `net, logit, action_hash, call` for decisions), and `REASONS: dict[int, str]`. Until then the
   reason names are parsed from `bot/src/nn_head.h` `kReasonName`.
4. **`nfs.obs` API (C).** Needed: `encode_bytes(raw: bytes) -> np.ndarray[float32, kObsDim]` for a turn-context
   payload, plus `OBS_DIM` and `OBS_SCHEMA_HASH`. Probed names: `encode_bytes`, `encode_raw_bytes`, `encode_record`,
   or `RawTurn.from_bytes` + `encode`.
5. **Champion identity (B, C).** Records carry `champion_handle`. Rewards need the summary champion `id`. Current
   handling: identity if the handles are summary ids; otherwise sorted handles are mapped to sorted team ids
   (`order_assumed`, recorded in the manifest); otherwise team-level rewards are used. Request: log the summary
   champion id (or document that `champion` is that id).
6. **Commitments / forced steps (A, D, B).** `nn_head.h` has no "forced/committed" reason. PPO defaults to option
   semantics, which assume a committed choice (e.g. objective kept up to 40 rounds) logs ONE decision when the
   option starts and nothing while it is forced. If a hook calls `decide()` on forced turns, it must mark them (a
   reason code or a context bit) so they can be merged (`commitment_mode=option`) or masked
   (`exclude_forced`) via `PPOConfig.forced_reasons`.
7. **Profiles (B).** Requested: `teacher_record` (every head shadow, records on, no sampling) for teacher-label
   collection, and per-head training profiles (e.g. `training_objective`: objective active and sampled, others
   off/shadow) for the bounded first experiment. Record logging changes fuel; teacher-label runs must be compared
   with `teacher_exact` on the same cells.
8. **In-training model install (B).** `rl` exports each iteration with `nfs.export.export_model` into
   `<run>/exports/<name>` (never `models/`) and calls `install_models.py --profile training --src <copy> --model
   <dir>`. Please let `--model` accept an unregistered model directory, or add `--model-dir`.
9. **`PolicyNet.head_logits(..., context=None)` (B, lead).** B's signature has an optional `context`; CONTRACTS 4 does
   not. PPO and imitation pass the record's context code when the model accepts it (runtime semantics). Please add it
   to CONTRACTS 4.
10. **Engine helpers (lead).** (a) `run_match` trusts any folder with `summary.json` (same as H's issue 3). `collect`
    now uses content-addressed folder names (candidate/opponent sha prefixes) and refuses a folder whose `job.json`
    names a different game. (b) `--log-limit` is 1 MB by default; NFS1 records need more, so collection passes
    64 MB. Please confirm the CLI's per-team semantics. (c) The training configs use 8–12 workers for later
    training; the build-time cap of 4 (H issue 2) applies to evaluation now.
11. **Data reality (lead, D).** The local 21 October archives contain effectively no engine-1.0.3 entries (0 of
    4,760 sampled). No 1.0.3 gameplay labels or rewards can come from them. Draft analysis from them is 1.0.2-only
    and observational. All archive maps are the 40 local maps (reused benchmarks).
