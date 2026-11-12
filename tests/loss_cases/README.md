# Real-loss decision regression cases

M1 comes from platform69 game1473a066-b6df-4410-a447-2b374428adc2 on02guardians.
The frozen source reproduces the complete game byte-for-byte. At the fixed warm
state, it cancels and restarts a carrier's recall while its own banking timer
forbids banking. The original fails the case; a bounded diagnostic guard passes.
See TAKEOVER_PLAN.json / TAKEOVER_RESULT.json for the predeclared test and limits.

Raw fixtures, generated puppet source and Wasm remain ignored under artifacts/.
First restore the selected replay/native pairs and run the input validation and
reproduction tools in tools/replay/puppet. Use engine2 and the official CLI at
default fuel. This runner accepts an unpacked raw replay, not its ZIP bundle.

```powershell
# Confirm the live-source baseline fails its case (expected failure is a successful check).
python tests/loss_cases/run_case.py --case tests/loss_cases/M1-recall-disabled-bank.json --replay artifacts/local-only/deep-2026-10-28/replays/examined/1473a066-b6df-4410-a447-2b374428adc2.repl26a --node <node.exe> --expect fail

# Confirm the predeclared diagnostic passes.
python tests/loss_cases/run_case.py --case tests/loss_cases/M1-recall-disabled-bank.json --replay artifacts/tmp/deep-repro/takeover-recall-v1/run/game-raw.repl26a --node <node.exe> --expect pass
```

A future candidate must preserve the original accepted inputs and states before
R1669, then take over with warm perception and memory. The runner rejects an
earlier divergence, an incomplete/too-short replay, or a change to the enemy's
accepted script within the assertion window. A full candidate match that changes the opening is not this
exact-state test; use a warm takeover build or harness. During the fixed assertion
window it may keep recalling, move away, or start a feasible bank, but must not
repeat the recorded cancel-and-restart inconsistency.

The assertion is about the decision, not a win. Enemy scripted actions cannot
react: interpret at most ten rounds and stop earlier on a rejected enemy action.
The recorded diagnostic's first enemy rejection isR1701, beyond the ten-round
window. Passing this case is necessary evidence for a proposed fix, not sufficient
evidence for release. Apply the development-map, clustered comparison, Bayesian
and one-time frozen-candidate holdout gates documented in docs/handoff.md.
