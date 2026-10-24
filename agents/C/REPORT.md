# Agent C report: observations, entities, temporal and team state (wave 1)

Written by the lead. Agent C's wave-1 session was cancelled before it wrote a report. Everything below was checked by
the lead after the cancel. Model/runtime: Kiro CLI subagent, configured model claude-opus-5.5. No training.

## Delivered (files exist and are tested)
- **Schema:** `schemas/observation.json`, the canonical versioned schema. It has these sections: layout, normalisation,
  rows, coordinate_frame, size_classes, memory, belief, raw_turn, visibility_classes, self_global, ally_row, enemy_row.
  Layout is `[self_global | ally rows | ally mask | enemy rows | enemy mask]`; kObsDim = 563 and the schema hash is
  0xD341B69C.
- **Generator:** `tools/gen_schema.py` produces `bot/src/nn_schema.h` and `python/nfs/schema_gen.py`.
- **C++:** `bot/src/nn_obs.{h,cpp}` (POD RawTurn and pure encode) and `bot/src/nn_obs_glue.cpp` (`nnobs::capture` via
  `nn_obs_access`, reading already-computed Bot/World state).
- **Python:** `python/nfs/obs.py` (RawTurn pack/unpack and an identical encode) and `python/nfs/transforms.py`
  (canonical team-perspective transforms).
- **Tests:** `tests/cpp/obs_parity.cpp` and `tests/python/test_obs_{encode,parity,schema,synth,transforms}.py`.
- **Evidence and scripts:** `agents/C/evidence/build_checks.json` (code-section identity with heads off) and
  `agents/C/scripts/` (scratch probe).

## Verified
- `python -m unittest tests.python.test_obs_parity`: native C++ encode matches Python **bit-exactly** over randomized
  RawTurns, and native constants match the schema. It needs g++ on PATH; without it the test skips.
- The full Python suite passes (186 tests, including the obs schema, encode, transforms and synthetic tests).
- With every head off, the build including nn_obs*.cpp is byte-identical to the original. With heads on, capture and
  encode run in the engine in the dev_untrained, neutral and training profiles with 0 faults.

## Not done / open
- **No visibility audit:** `VISIBILITY.md` was not written. A per-feature legality review is still needed (live vs
  remembered-with-age, and the excluded hidden information). The schema's `visibility_classes` and per-feature fields are
  the starting point.
- **No engine fuel measurement** of capture+encode (deliverable 6), and no real RawTurn fixtures in
  `tests/fixtures/obs/`.
- **Team blackboard:** no proposal yet for intent/assignment encoding within `shared_memory_bytes`. The existing
  8-byte claim/sighting protocol is unchanged.
