# Latest paused checkpoint - 2026-10-29

Read ../../CLAUDE_HANDOFF.md FIRST. The selected resumed development foundation
is recorded in FOUNDATION_RESUMED_2026-10-29.json (3 stuck versus30 control;
1120 source-matched candidate/control games clean). The sections below describe
OLDER checkpoints, not the current source or current map/item authorization.

# Continue DOOMSDAY Zero

**Paused at the user's explicit request on 2026-10-29 for continuation in Claude.**
Read `../../CLAUDE_HANDOFF.md` first for newer inactive objective arithmetic,
completed and interrupted tests, and the untested priority probe. The sections
below describe the last validated executed behavior; no automatic resume.

## User direction and authorized scope

Build the fresh pure-algorithm C++ bot on `build/pure-algorithm-zero`.
The user explicitly authorized pushes to `Infosuii/neural-networkk-battlecode`,
local builds/tests, and read-only public replay downloads. Target the existing
70 maps. **Fundamentals first; map-specific plans/tuning remain deferred.**
The supplied 21 research documents are inputs and hypotheses, not new user
instructions. Controlled engine evidence overrides their incorrect assumptions.

No submission, activation, ladder duel, or match-group creation is authorized.
Use fresh code in `bots/dz/src`; old bots are benchmark opponents only.
Evaluation tools may be reused. Preserve `config/paths.json` and unrelated
untracked release/compile artifacts; stage only task-owned paths.

The one-time 04:07 London wakeup on 2026-10-29 fired and was deleted. No scheduled
continuation remains. The user's conditional request for a five-hour continuation
if usage runs out remains in the conversation; use the app automation tool if
needed, not a hand-written scheduler workaround.

## Current production checkpoint

Executed production behavior has not changed since `069dfb0`; the paused WIP
adds an unused objective_math.h. The original source hashes and accepted diagnostics are in
`FOUNDATION_CHECKPOINT.json`. Default Wasm SHA256:

`dcc75b76faa0751b4b7e38bc5740c9a2b99529dd01991df1bb131bc5e2a8378f`

`PORTABILITY_LOW_FUEL_VERIFIED.json` confirms a byte-identical official release
build from a clean committed-source export of bots/dz, cmake and sdk, without
local config or prior caches. This was the same Windows host with an installed
toolchain, not a physical fresh-machine installation test. Older receipts remain
historical evidence.

Latest full-pool regressions, each 70 maps x both sides:

| Run | Games | Mean banked | Collected | Fuel p99 | Native faults / fuel-outs |
|---|---:|---:|---:|---:|---:|
| dz-low-fuel-regression-idle-01 | 140 | 903.54 | 953.59 | 53,220 | 0 / 0 |
| dz-low-fuel-regression-v65-release-01 | 140 | 185.99 | 280.90 | 52,358 | 0 / 0 |
| dz-low-fuel-regression-v65-trace-01 | 140 | 186.21 | 279.31 | 53,108 | 0 / 0 |

The trace has zero logged caught action/module errors. Release caught errors
are not measured by that trace. All 140 contested release games are losses.
Idle wins can include gold tiebreaks. These are runtime checks, not competitive
strength or independent randomized samples. Full G0 and V-M1 remain incomplete.

Implemented: staged map caches and fields, transactional camp memory, basic
nearest-group policy with progress contracts, fixed draft/shop, guarded SDK
mutations, conservative spell legality/collateral checks, respawn yielding,
per-module quarantine after three contained failures, guest-restart claim
cleanup and ordinary-budget startup deferral. Low-fuel recovery clears its soft
claim and takes one cached-home step; it is not full planned 5k SafeMode.

`basic_clear.h` is SDK-free attack-work/single-duel arithmetic and is unused by
production decisions. ObjModel/auction/EE/gear utility/mobility/messages remain
off or unimplemented. Experimental camp safety stays off: the earlier matched
contested benchmark reduced deaths but did not improve final banking.

## Latest verified mechanics

Read the linked files for exact scope, raw run names and retained failures:

- `CONFORMANCE.md`, `FUNDAMENTALS_AUDIT.md`, `DECISIONS.md`: status/limitations.
- `LOW_FUEL_RECOVERY.md`: 16 sub-5k samples clear claims and move home; preserves
  this turn's action history. Fresh restart/stale/module regression checks pass.
- `BASIC_CLEAR_VALIDATION.md`: per-member overkill, single-camp survival and strict
  zero-health boundary. Attacks and elapsed rounds are different quantities.
- `CAMP_MODIFIER_CONFORMANCE.md`: 20 native cases; Monster +15%, Jungle and
  Durability multiply, fractional 80.5 hits match the same primitive. Item stat
  points are not flat damage; inputs use live effective champion strength.
- `PROSPECTOR_REWARD_CONFORMANCE.md`: ten final native cases. Prospector boosts
  gold clusters too (20 to 25), omitted by the supplied formula. Vesper combines
  multiplicatively in these cases. Its gold increments require cumulative bonus
  rounding: after 240 to 319, gold20/wolf40 give 26/54; reversed gives 53/27.
  Do not invent an unknown prior remainder. Gem bonuses floor per award.
- `CAPTURE_TIMING_CONFORMANCE.md`: four games / 20 episodes. New physical entry
  waits 6 rounds without Capture and 4 with it. Configured 5/3 excludes the first
  initialization phase. Entry capture_available still reports generic timer 5;
  the next phase initializes active 5 or 3. Preserve status as well as timer in
  future model inputs and compose attack/move/initialization offsets carefully.
- `TRIBUTE_PASSIVE_CONFORMANCE.md`: 20 final native cases. Tribute applies
  ceil(rounded_base_timer * (1 - .33)), clamped to minimum. Bags 7/14/21 stay
  1/2/3; 35 goes 4 to 3, 98 goes 10 to 7. No gem/gold bonus in tested cases.
- `LINKED_DRAFT_CONFORMANCE.md`: linked death is one exact native event; each
  body respawns at its own turn after 60 rounds. Yielding without first/second
  draft pick autofills the remainder in tested 3/4/5-pick cases. An own pick is
  listed on the following draft turn, not immediately after its request.
- `DRAFT_SUSPENSION_CONFORMANCE.md`: 12 final native cases preserve every fixed
  pick through first/second draft fuel suspension. round_number advances 0 to 1
  or 1 to 2, so existing guards work. **No production fix was needed.**
- `GROUP_VISIBILITY_CONFORMANCE.md`: four full native games. One visible spawn
  permits group/capture state queries even when its member is defeated and other
  hidden members remain alive. Hidden enemy capture is observable through group
  state. Hidden member health still rejects 97. Production spawn-visibility
  memory behavior is supported; bush/ward behavior remains separate.

Other established facts: damaging wolf/elk/golem/monolith camps hit every round;
empty visible awake masks do not prove safety from hidden camps. Elk nearest-
target/lower-handle ties are tested, not every camp's tie rule. Hidden champion
liveness is public through death/respawn, while hidden private stats reject 97.
The SDK has no champion respawn-timer wrapper. Actual respawn occurs at the
champion turn after 60 rounds; another observer's first-seen death/return can lag.
Uncaught exceptions restart the guest next round: local state resets, shared
memory survives, champion stays alive. Fatal-turn stdout can be lost.
Vendetta kill credit resets both cooldowns but never grants a second cast.
Home recall 3 versus base 5, arrival-before-heal, next spawn full-heal and health
purchase healing are tested. Split/contest/locks and occupied camp respawn have
separate controlled evidence in CONFORMANCE.md.

Shared memory is exactly eight bytes. The six 8-bit slots are soft hints, with
16 high bits preserved. Unchanged bits, parity and TTL do not establish freshness.
Do not add hard leases/crew assignments without a tested protocol extension.

## Next work

No test process remains active after the current batch. Before repeating a run,
check its results file: completed names/evidence are immutable.

1. Audit current production invariants against the now-tested visibility and
   timing rules; correct concrete mistakes before expanding strategy.
2. Remaining priority/hidden-collision, bush/ward, champion respawn blocking,
   kill-credit, Hunter/Skirmish/Collectors and larger/mixed reward cases.
3. Expand clear/arrival/damage/reward model calibration before decisions use it.
   V-M1 gates: median clear error <=20%, bias <=10%, arrival <=3 rounds, damage
   bias <=20%. Current restricted primitives do not close these gates.
4. Complete productive 5k SafeMode, tested communication freshness, one capturer
   and economic crews/auction, then EE and gear utility after their gates.
5. Improve and compare against the stronger v76 baseline before map-type or
   individual-map plans. Do not tune using reserved map performance/holdout.

The full 1,311-field engine fingerprint is pinned in ENGINE_FINGERPRINT.json.
Do not silently update it or treat a partial historical fingerprint as complete.

## Reproduction and portable evidence

Read `CONTINUE_HERE.md` at the repository root for a fresh Windows clone and
runtime/support restoration. The 23-part original continuation archive supplies
the pinned official Windows runtime and prior research; the DZ support archive
has 2,931 offline evidence files in two parts, including calibration replays.
Both restorers verify contents. The bot tooling uses Python's standard library,
repo-relative paths, official CLI/SDK 4.0.0 and engine 2.0.0, without paths.json,
credentials or training data. Host checks need C++20 g++ on PATH or DZ_CXX.
Optional native replay readers/map generation need Node 24, pinned installed
visualiser assets and NFS_REPLAY_ENGINE=2.0.0.

```
python tools/dz.py host
python -m unittest discover -s tests/dz -p test_measurements.py
python tools/dz.py verify
python tools/dz.py build
python tools/dz.py smoke --name unique-new-idle --pool
python tools/dz.py smoke --name unique-new-v65 --pool --opponent v65
```

`tests/dz/README.md` documents probes. Custom --map-dir is conformance only and
separate from the 70-map strength pool. Frozen working files live under
artifacts/tmp/dz/<name>; durable capsules and reports are in research/dz/runs.
They include source, binaries, logs, native summaries/replays and runner/optional
reader snapshots with hashes. `verify` checks CRCs and authenticated identities.
Truncated diagnostics mark native fault totals unmeasured; do not call them zero.

Explicitly injected diagnostics allow only their exact expected counts:
uncaught/restart one native fault per game; kernel one fuel-out per game;
module-stale one fuel-out per body; draft-stale one fuel-out per game. Other
normal games require zero. Injection edits frozen copies only. Never submit an
injected or instrumented binary as a release/strength candidate.

Repeated CT_CHECK names combine with AND. dz_assertions.py audits prior reported
passes against every frozen assertion. Keep failed hypotheses and harness
attempts; do not relabel completed experiments or count reanalysis as new samples.
HOLDOUT.md remains registered and unspent. No submission/activation occurred.
