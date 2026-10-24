# Agent B report: runtime, model format, budget, export, registry (wave 1)

Written by the lead. Agent B's wave-1 session was cancelled before it wrote a report. Everything below was checked by the
lead after the cancel. Model/runtime: Kiro CLI subagent, configured model claude-opus-5.5. No training.

## Delivered (files exist and are tested)
- **C++:** `bot/src/nn_rt.h` (kernels, bounded activation, masked argmax/log-softmax/sampling, SplitMix64 PRNG),
  `nn_model.h` (model descriptor, blob offsets, fnv1a64 segment checksums verified in `nnh::warmup()` on draft turns),
  `nn_head.{h,cpp}` (`nnh::decide/value/leaf/turn_start/idle/warmup`, reasons enum, per-turn context cache),
  `nn_budget.h` (`teacher_left`, `credit`, `admit`, `Meter`, per-head counters, `NNTEL` telemetry),
  `nn_log.h` (NFS1 records queued in turn, flushed by `nnh::idle()` from leftover fuel), and the generated
  `nn_registry.h`, `nn_config.h`, `nn_weights_*.h`. All of it is compiled out when `NN_ANY_HEAD==0`, and the default
  build is byte-identical to the original.
- **Python:** `python/nfs/models/` (PolicyNet, numpy reference twin, `untrained.py`), `export.py`, `registry.py`,
  `records.py`.
- **Tools:** `tools/gen_config.py`, `tools/install_models.py` (the single switch for profiles and models),
  `tools/run_cpp_tests.py`.
- **Profiles:** `configs/profiles/*.json` (release, teacher_exact, neutral_credit, neutral_real, dev_untrained,
  training, selftest). Model config: `configs/model/fs_v1.json`.
- **Registry:** `models/registry.json` lists fs_v1_untrained (zero residual) and fs_v1_dev (plumbing), both labelled
  synthetic and untrained, plus draft_net_original (inherited, trained, not re-exported).

## Lead fixes after the cancel (B was mid-refactor)
- `write_*` became `enqueue_*` in nn_head.cpp, and `nnh::idle()` was added.
- In training mode, `Result.net` is now the argmax.
- The test runner uses stub-schema test models.
- `models/budget.json` allowance was raised to 55000 and the admission log cost reduced. See HANDOFF.md.

## Verified
- `tools/run_cpp_tests.py` passes 11 targets, 451/451 checks. They cover:
  - kernel parity, record round trip (C++ → Python decoder);
  - the zero-residual path, which always returns the teacher choice;
  - shadow mode, which always executes the teacher;
  - active argmax, which matches the numpy reference;
  - training-record logits bit-exact against the reference, and sampled choices matching the PRNG twin with logp within 1e-6;
  - fallbacks: empty, teacher-illegal, NaN/Inf, bad prior, K too large, schema mismatch, bad checksum, NaN weights;
  - budget refusal and recovery;
  - the context cache and its invalidation;
  - the per-turn record bound;
  - selftest lines matching the reference.
- Official builds of every profile succeed. Smoke games vs the original had 0 faults and 0 bot errors
  (`evaluation/results/lead_profile_check*.json`).

## Not done / open
- **Budget not measured:** no engine fuel probe was run, so `models/budget.json` is provisional (coefficient model).
  Estimated cost: encoder ≈12.9k fuel, ≈919 per candidate (F=24, hidden 16), so a K=16 decision ≈30k. Measure it and
  probably shrink the default.
- **Telemetry format mismatch:** B prints `NNTEL` and H expects `NFT1`. Unify them.
- **Fuel-credit coverage:** neutral_credit does not yet credit teacher-capture, warmup or turn_start overhead, so it is
  not yet action-equivalent. See HANDOFF.md, finding 1.
