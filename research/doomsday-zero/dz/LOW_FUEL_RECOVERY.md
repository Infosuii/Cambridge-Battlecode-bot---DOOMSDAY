# Bounded low-fuel recovery — 2026-10-29

The normal action reserve requires more than 13,500 remaining fuel. It therefore
cannot perform the intended emergency action at 5,000 fuel. Production now has
an explicit emergency action budget for a small cached-home recovery path.

With a ready map cache and more than 2,800 fuel at entry, it clears its own soft
shared claim first, then tries at most eight fixed stack directions for one legal
step that reduces the cached home distance. It checks live movement restrictions,
occupancy and the captured round. The existing Actuator keeps its successful
move/cast history and error limit; changing budget does not reset either.
Channeling champions keep their channel. Without enough budget or a usable cache,
the path yields. It rebuilds no observations or fields and scans no groups/enemies.

This is **partial emergency recovery**, not the complete planned 5k SafeMode.
Banking, buying and productive farming under that cap remain future work. Moving
toward home is not a calibrated combat escape guarantee. Soft shared claims still
have no freshness lease.

## Native evidence

`dz-low-fuel-home-05` completes four diagnostic games on 00collision and
01big-world, both sides. All 16 champion bodies are forced below 5,000 fuel once,
only when alive with a legal improving move. One body was dead in the first test
window and is tested after respawning at R103; all others are tested at R50.

- Entry fuel: 4,811–4,838.
- Recovery uses 1,462–2,141 fuel; recorded remaining fuel: 2,677–3,368.
- Every body clears its claim and moves exactly one home-distance step.
- All continue through R300 with zero caught action/module errors, native faults
  or fuel-outs. Native summaries cover the full game.

Diagnostics store a compact record and format it on the next fresh turn. Printing
formatted diagnostics inside this small budget materially changed the experiment.

The failed attempts remain in immutable capsules: 01 accidentally also injected
the memory-failure fixture, caught by the gate; 02 consumed budget printing its
own force marker; 03 moved but sometimes could not clear the claim afterwards;
04 fixes the order and allocation but correctly fails the all-body requirement
because one body was dead through the short eligibility window. 05 tests it after
respawn without weakening the per-body action or budget assertions.

The changed action boundary also passes fresh forced-restart, post-suspension
exception and module-quarantine diagnostics (`dz-low-fuel-*-regression-01`). Only
their explicitly expected deliberate faults/exhaustions are allowed. The full
420-game idle/v65-release/v65-trace campaigns have zero faults/fuel-outs; the trace
has zero caught errors. Contested release still loses 140/140. This establishes
runtime behavior, not competitive strength or complete fundamentals.
