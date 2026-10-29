# Draft fuel suspension — 2026-10-29

The current production guard works during drafting. **No production change was
needed.** Native checks establish that `round_number()` advances between draft
turns, so the existing captured-round checks detect resumed stale draft work.

Twelve final full native games pass across three-, four- and five-pick maps,
both sides, with exactly one deliberate fuel-out per game and zero native faults
or caught action/module errors:

- `dz-draft-suspension-02`: first draft turn, 3/5 picks, four cells.
- `dz-draft-suspension-second-02`: second draft turn, 3/5 picks, four cells.
- `dz-draft-suspension-four-02`: first turn, four picks, two cells.
- `dz-draft-suspension-four-second-02`: second turn, four picks, two cells.

The frozen diagnostic requests a valid pick, logs and flushes its marker, then
burns the remaining draft budget until the committed prefix advances. Execution
resumes with the old local variables. The round changes **0→1** or **1→2**.
Every intended subsequent pick is still requested and every spawned body's type
matches the full fixed production lineup. Empty or incomplete transcripts cannot
pass. The initial `dz-draft-suspension-01` also passes four first-turn cases; the
final parser adds an explicit advancing-clock assertion.

The first turn uses the boosted 10M budget. Its stale optional publication meets
the Actuator guard. On the second turn the ordinary 100k budget is exhausted;
shared initialization already completed, so the footer round check preserves
the new turn. Both guard paths are exercised.

Keep this separate from the prior **yield-without-a-pick** experiment: yielding
without a first/second pick caused remaining-roster autofill in those cases.
Fuel suspension after a successful request resumes and preserves the intended
roster here. Neither result should be generalized to every possible draft fault.

Injection changes only a frozen copy. These binaries deliberately exhaust fuel
and must not become release or strength candidates. Uncaught draft exceptions,
misses at later positions and suspensions at other code points remain outside
this test. The baseline source/binary and its full-pool receipt remain unchanged.
