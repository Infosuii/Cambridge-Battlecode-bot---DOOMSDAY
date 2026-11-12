# Agent D report: strategy, draft, objective, role and value (Wave 2)

Runtime/model: inherited configured Codex session. The agent tool exposed no Opus 5.5 choice; exact
underlying session model id is not exposed to this worker. This was a real worker invocation. No
training, parameter fitting, submission, upload, browser/desktop use or external writes occurred.

## Implemented

- `bot/src/nn_strategy.h`: pure bounded candidate builders (F24): draft12, strategy6, objective8,
  role5; bounded value-signal transform. Candidate zero is teacher, deterministic masks, stable ids,
  finite clipping, and teacher-favouring priors. No SDK dependency in the pure builder layer.
- `bot/src/nn_strategy.cpp`: admission before features, SDK state extraction from existing Bot/World,
  `nnh::decide` calls, exact teacher fallback, 20-round role options with explicit reset, deterministic
  priority execution, per-round critic signal consumed by strategy and objective. Constant-initialised
  POD caches, bounded arrays, no heap allocation or shared-memory protocol change.
- `schemas/heads/{draft_pick,strategy,objective,role,value}.json`: complete features, normalisation,
  clipping, labels, contexts, semantics and lifecycle. Regenerated with `archive/agents/D/generate_schemas.py`.
- `python/nfs/heads/strategy.py`: float32 twins, mask/order/teacher labels, bounded critic transform.
- `tests/cpp/test_strategy_parity.cpp` and `tests/python/test_strategy_parity.py`: native parity harness
  and five synthetic tests. All temporary writes are under `artifacts/tmp/D2`.
- `archive/agents/D/INTEGRATION.md`: precise lead-owned source hooks and gated draft signature instructions.

## Verification actually run

```powershell
$env:PYTHONPATH="$PWD/python"
$env:PATH="C:/msys64/ucrt64/bin;"+$env:PATH
$env:TEMP="$PWD/artifacts/tmp"; $env:TMP=$env:TEMP
& 'C:/projects/cambridge battlecode/work/neural-gameplay/.venv/Scripts/python.exe' archive/agents/D/generate_schemas.py
& 'C:/projects/cambridge battlecode/work/neural-gameplay/.venv/Scripts/python.exe' -m unittest tests.python.test_strategy_parity -v
```

Result: **5/5 tests OK**, including 800 varied synthetic candidate fixtures (200/head) and 200 synthetic
value-signal fixtures with **bit-exact** C++/Python features/priors/masks/ids. Additional checks cover
teacher-first masks, empty sets, stable zero-residual ties, alternative permutation consistency,
schema widths and bounded critic output. No match data was fitted or used as synthetic evidence.

Follow-up unit resolution: `value.margin` is terminal submitted gem margin divided by1000, a fixed
model output unit separate from reward shaping's configurable margin scale. C++/Python bounded
signals apply `act(margin)` directly. The five synthetic tests were rerun after this change.

A scratch copy with NN_ANY_HEAD=1 passed native g++ C++20 `-fsyntax-only -Wno-attributes` against the
installed SDK. That checks glue syntax only, not Wasm instructions, fuel, SDK runtime legality or
integrated gameplay.

## Remaining verification / limits

Lead must apply hooks, regenerate synthetic untrained model exports against all completed schemas,
then rebuild official profiles and prove teacher_exact byte identity after each C++ integration.
At report time the official installed WASI compiler was permission-denied in the root session.
Therefore no new Wasm byte-identity, engine fuel, telemetry or smoke result is claimed by D.

Builder fuel reservations are provisional and must be replaced using engine measurements. The value
head is an auxiliary critic: its bounded signal affects combined strategy/objective; a value-only
profile has no standalone action policy. Team coordination uses existing camp claims and local roles;
it does not invent a larger blackboard. The inherited draft network remains separate and unchanged;
the emergency lineup fallback stays deterministic. All newly created heads are **untrained**.
