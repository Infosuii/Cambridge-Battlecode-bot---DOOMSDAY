# Battlecode development requirements

Do not submit, publish, or activate bots on the official ladder. Local development and testing are authorized.

## Mandatory failure investigation and retry protocol

Never reject a strategy or feature solely because its first benchmark is worse than baseline. Evaluate the potential of the correctly implemented strategy.

For failed experiments:
1. Verify compilation, effective configuration, activation, intended inputs and execution.
2. Inspect dependencies, conflicting heuristics, shared state and execution order.
3. Examine relevant failed-game replays. Separate strategic weaknesses from bugs, fuel exhaustion and indirect execution changes.
4. Where promising, make approximately 2–3 focused repair/tuning attempts, each motivated by an identifiable failure mechanism or plausible improvement. Do not run arbitrary configurations to rescue a weak idea.
5. Test plausible dependent systems together, preferably base/A/B/A+B with paired conditions.
6. Evaluate conditional benefits across maps, opponents and game states.

Use these outcome classifications in the development log:
- **Accepted:** demonstrated improvement with satisfactory reliability.
- **Retry required:** promising, with unresolved implementation, tuning, dependency or fuel issues.
- **Conditionally useful:** beneficial in identifiable situations, unsuitable as a universal default.
- **Parked:** insufficient evidence or diminishing returns; retain findings.
- **Rejected:** intended mechanism properly tested and reasonable repairs failed to demonstrate competitive value.

A failed benchmark gate is not itself a Rejected classification. Record evidence, mechanism, repair hypothesis, focused attempts, interactions, environmental scope and remaining uncertainty. Preserve frozen original x1 and reproducible results; do not overwrite another checkout's work.
