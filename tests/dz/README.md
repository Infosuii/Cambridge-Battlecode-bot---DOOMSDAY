# DZ mechanical correctness checks

These probes are separate from the production bot. They establish engine facts
and validate recovery paths; instrumented and synthetic games are not strength
comparisons. The current status and retained failures are in
`research/dz/CONFORMANCE.md` and `research/dz/HANDOFF.md`.

Use a fresh name for every run. The runner freezes candidate/opponent source,
binary, runner and (when relevant) replay-reader code before producing evidence.
Completed native diagnostics have real fault totals. Truncated ones mark them
unmeasured.

```powershell
python tools/dz.py host
python tools/dz.py conformance --name new-draft-suspension --fixture draft-stale --maps 00collision 01big-world --diagnostic-rounds 2000
python tools/dz.py conformance --name new-tribute-passive --fixture tribute-passive --map-dir tests/dz/maps --maps prospector --diagnostic-rounds 2000
python tools/dz.py conformance --name new-capture-time --fixture capture-time --map-dir tests/dz/maps --maps prospector --diagnostic-rounds 2000
python tools/dz.py conformance --name new-camp-mods --fixture camp-mods --map-dir tests/dz/maps --maps camp-modifiers --diagnostic-rounds 2000 --set DZ_MONSTER=1 --set DZ_JUNGLE=1 --set DZ_DURABILITY=1
python tools/dz.py conformance --name new-prospector --fixture prospector --map-dir tests/dz/maps --maps prospector --diagnostic-rounds 2000
python tools/dz.py conformance --name new-linked --fixture linked --map-dir tests/dz/maps --maps isolated-monolith --diagnostic-rounds 2000
python tools/dz.py conformance --name new-missed-pick --fixture draft-miss --maps 00collision 01big-world --diagnostic-rounds 2000
python tools/dz.py conformance --name new-low-fuel --fixture low-fuel --maps 00collision 01big-world --diagnostic-rounds 2000
python tools/dz.py conformance --name new-clear --fixture clear --map-dir tests/dz/maps --maps isolated-wolf isolated-elk isolated-golem isolated-monolith cluster-line --diagnostic-rounds 2000
python -m unittest discover -s tests/dz -p test_measurements.py
python tools/dz_assertions.py
python tools/dz.py conformance --name new-core --fixture kernel --maps 00collision 01big-world --diagnostic-rounds 2000
python tools/dz.py conformance --name new-recovery --fixture recovery --map-dir tests/dz/maps --maps recovery-shop --diagnostic-rounds 140
python tools/dz.py conformance --name new-contest --fixture contest --fixture-opponent --map-dir tests/dz/maps --maps capture-contest --diagnostic-rounds 110
python tools/dz.py conformance --name new-hidden-death --fixture death --fixture-opponent --map-dir tests/dz/maps --maps isolated-monolith --diagnostic-rounds 130
```

The death probe uses Node 24 and the pinned official replay assets to compare
each SDK reading against native turn states. That reader is frozen in its
capsule. Ordinary builds, host tests and other probes use Python standard library
and the official CLI; the host test also needs a native C++20 compiler.

`uncaught` and `restart` intentionally cause one native fault per game; run to a
completed game (`--diagnostic-rounds 2000`). `kernel` and `module-stale` deliberately
exhaust fuel. `module-failure` injects contained exceptions. These candidates must
never be submitted or treated as release/strength evidence. Fault injection edits
only the frozen diagnostic copy, not `bots/dz/src`.

`maps/` contains tiny, official-MapBuilder-validated fixtures. They are excluded
from the 70-map competition pool and cannot be used by `smoke --map-dir`.

`linked` supports `--set DZ_ISSAC_DIES=1` to reverse the sacrificed linked body.
It uses the frozen native lifecycle reader. `draft-miss` supports
`--set DZ_SKIP_SECOND=1` to omit the second pick instead of the first. These
probes establish engine behavior; their lineups are not production draft plans.

`prospector` supports `DZ_PROSPECTOR=0` for its Power-item control,
`DZ_VESPER=1` for the gold-passive actor, and `DZ_WOLF_FIRST=1` to reverse
the last two awards. Use `--set` for these booleans. See
`research/dz/PROSPECTOR_REWARD_CONFORMANCE.md` for the supported scope and
the order-dependent gold rounding; these are not strategy match results.

`camp-mods` tests `DZ_MONSTER`, `DZ_JUNGLE` and `DZ_DURABILITY` in any boolean
combination. `DZ_MONSTER_FOCUS=1` uses the focus version for fractional basic
damage. The runner freezes the exact `basic_clear.h`. See
`research/dz/CAMP_MODIFIER_CONFORMANCE.md` for scope and measured tolerances.

`capture-time` selects the Capture emblem and enables physical-entry/progress
logging in the reward fixture. Use `--set DZ_CAPTURE_ITEM=0` for its Power-item
control. It verifies the 5/3 configured timers and the extra initialization
phase, not just a last-kill-to-reward gap; see CAPTURE_TIMING_CONFORMANCE.md.

`tribute-passive` compares the same bag before/after an item. `DZ_TRIBUTE=0`
selects its Power-item control; `DZ_SMALL_BAG=1` requests 7 gems and
`DZ_BIG_BAG=1` requests 21 instead of 14. For 98 use map `tribute-passive` with
`DZ_LARGE_BAG=1`; for 35 use `tribute-passive-mid` with `DZ_LARGE_BAG=1` and
`DZ_MID_BAG=1`. `DZ_OBSERVE_ONLY=1` deliberately leaves conformance unaccepted.
See TRIBUTE_PASSIVE_CONFORMANCE.md for timing and scope.

`draft-stale` intentionally exhausts one draft budget after a valid pick.
`--set DZ_DRAFT_BURN_SECOND=1` selects the ordinary second-turn budget instead
of the boosted first turn. It must preserve every intended pick/body and an
advancing draft round. These injected binaries are diagnostic only; see
DRAFT_SUSPENSION_CONFORMANCE.md.

`group-visibility` uses its same-named map and `--fixture-opponent` to test one
visible spawn among twelve members, including hidden capture. The
`group-visibility-first` variant makes the scripted enemy defeat that member
first, leaving hidden live members. See GROUP_VISIBILITY_CONFORMANCE.md.

`clear` freezes the exact production `basic_clear.h` into its diagnostic source.
Use `--set DZ_RANGED=1` for Vesper instead of Vendetta. This restricted primitive
is not used for production decisions; its scope and validation gaps are in
`research/dz/BASIC_CLEAR_VALIDATION.md`. `four-pick` is a separate kernel map for
the four-draft-picks / five-linked-bodies case. A full diagnostic needs 2000
rounds; zero rounds runs no turns and is rejected.

`priority` (CT-6) requires `--fixture-opponent`. Both teams run the priority
probe; the pinned replay reader `tools/dz_priority_audit.mjs` (frozen into each
run) compares native phase-14 turn order with both transcripts. Use
`--diagnostic-rounds 20` for a quick order check (faults unmeasured) or 2000 for
measured native faults. See PRIORITY_CONFORMANCE.md.
