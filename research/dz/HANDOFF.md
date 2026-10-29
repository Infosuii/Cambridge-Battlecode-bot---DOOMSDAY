# Continue DOOMSDAY Zero — 2026-10-29

## Latest steering and audit checkpoint (read first)

### Prospector / reward continuation after 59974a2

Production remains unchanged: exact low-fuel binary, 420-game receipt and clean
export still apply. New CT-13 controls pass ten complete native cells (all five
05 campaigns), zero faults/fuel-outs. Read PROSPECTOR_REWARD_CONFORMANCE.md.

Prospector boosts gold clusters too (20→25), omitted by the supplied reward
formula. With Vesper the tested boost is multiplicative (20→33 in this sequence).
Vesper's gold reward increments match cumulative fractional-bonus carry: after
an initial 240→319 award, gold20 then wolf40 give 26/54; reversed gives 53/27.
Do not floor each event independently or invent a hidden remainder. Gem bonuses
floor individually (7→8, 14→17). Current receipt scope excludes Golem/Monolith,
mixed/crew rewards, other stacking and death/respawn carry.

Earlier failed assumptions and weaker initial runs remain immutable evidence.
The final parser independently checks every reward using integer rational units.
Next fundamentals work: Monster/Jungle/Durability effects used in fixed shopping,
Tribute and remaining item modifiers, pending action/vision cases, then expanded
clear/arrival/damage calibration. Advanced modules and map-specific plans remain
deferred; the production bot still loses every contested v65 regression game.


### Linked-death and draft continuation after 8a0a51b

Production source remains unchanged and the 420-game/clean-export low-fuel
receipt still applies. New isolated conformance checks pass: four linked-death
cells and 12 first/second missed-pick cells across 3/4/5-pick maps. Read
LINKED_DRAFT_CONFORMANCE.md. Cassi/Issac die in one exact native event and return
at their respective champion turns after 60 rounds. Missing a draft pick fills
the remaining roster without resuming the guest for later draft rounds. An own
pick is not listed immediately; it is committed by the next draft turn.

Initial failed assumptions and weaker initial linked runs are retained. The new
reader also passes offline regression against all four previous hidden-death
replays. No map specialization or bot strategy change. Next fundamentals work:
controlled Prospector/item modifiers used by fixed shopping, remaining vision/
action cases, then expanded clear-model calibration. Full G0/V-M1/SafeMode and
competitive strength remain unfinished.


### Latest low-fuel and basic-clear checkpoint

- Restart checkpoint and clean export are pushed.
- `basic_clear.h` is an SDK-free work/single-duel primitive, not used for
  decisions. Read BASIC_CLEAR_VALIDATION.md. Full native melee/ranged 03
  campaigns pass 20 cells, zero faults/fuel-outs. 01 were truncated; melee 02
  accidentally ran zero turns and was rejected. All evidence is retained.
- `dz-core-four-pick-01` passes two complete native games: four picks/five
  bodies with C&I, exact one deliberate fuel-out each, zero faults.
- Low-fuel recovery now passes `dz-low-fuel-home-05`: all 16 bodies across four
  full native games enter below 5k fuel, clear their old claim, make one legal
  cached-home step and continue at R300; zero native/caught errors or fuel-outs.
  It preserves existing action history. Directions use fixed stack storage;
  diagnostics are deferred to the next fresh turn. This is not full SafeMode.
- Retained low-fuel failures: 01 mixed memory injection (harness bug); 02 spent
  budget on its own marker; 03 moved but sometimes could not clear its claim;
  04 passed the eligible 15 bodies but missed the fifth side-B large-map body,
  which was dead throughout the first window. 05 waits for its respawn.
- Fresh 420-game pool checks now pass: `dz-low-fuel-regression-idle-01`,
  `dz-low-fuel-regression-v65-release-01`, `dz-low-fuel-regression-v65-trace-01`.
  All have zero native faults/fuel-outs; trace has zero caught errors. Idle
  banked 903.54, collected 953.59, p99 53,220. Release v65 banked 185.99,
  collected 280.90, p99 52,358, 0/140 wins. Trace v65 banked 186.21 (diagnostic).
- Fresh restart/stale/module regression diagnostics all pass. Preserve exact
  intentional fault/exhaustion counts; never use injected binaries as releases.
- Current source matches the new frozen idle source; map-specific tuning stays
  deferred. See FOUNDATION_CHECKPOINT.json and LOW_FUEL_RECOVERY.md.
- Next work: remaining linked death/draft/action/item/vision conformance, then
  expanded clear/arrival/damage calibration. Full ObjModel/EE and full 5k
  SafeMode remain unfinished. The bot is still weak against v65.


### Restart-safe continuation checkpoint

The user said **continue** after the wakeup. c706ff3 is pushed; new work below is
now validated by 420 new full-pool games. Keep map-specific plans deferred.
FOUNDATION_CHECKPOINT.json records the current source and exact tested binary.

- Recovery: `dz-ct16-recovery-02` passes two controlled cells: base recall 5,
  Home recall 3, health purchase heals by maximum-health gain immediately,
  arrival precedes spawn healing, next spawn turn full-heals, recalling on spawn
  is accepted and starts a 3-tick channel with Home. `recovery-01` was a failed
  fixture that wrongly expected to escape a range-three wolf in one step.
- Hidden death: `dz-ct9-hidden-death-06` / `07-reverse` pass both sides, with an
  observer-order reversal. Hidden enemy alive/dead/respawn liveness reads work;
  hidden health reads reject 97. Offline official replay analysis checks every
  SDK observation against its actual champion-turn state. Actual respawn is 60
  rounds after death at the champion turn; another champion can first see it that
  round or the next. Earlier 01–03 wrongly assumed an observer delay always 60 or
  always 61; 04/05 had a reader phase/previous-event mix-up. Failures preserved.
  Bundled SDK exposes no champion respawn-timer wrapper/import; don't invent one.
- Contest: `dz-ct24-enemy-contest-02` passes: prior capture progress is confirmed
  by the scripted opponent, contest resets timer, prevents rewards, then leaving
  permits full reward and resumed progress. 01 missed an interleaved observation.
- Kernel: `dz-core-kernel-asserted-01` passes four completed native games, one
  deliberate fuel-out each, zero faults. CT-1 stable primitive samples, CT-2
  suspension, CT-3 budgets, CT-5 immediate shared writes, draft count and linked
  body count now have strict automatic assertions. Empty diagnostics cannot pass.
- **CT-4 research correction:** an uncaught exception restarts the guest; the
  champion stays alive. Local/static state resets, shared team memory persists.
  `dz-ct4-uncaught-03` passes four complete native games, exactly one deliberate
  fault each at round 50, boot at 51, fresh local counter, retained shared flag,
  and healthy round-100 execution. Fatal-turn stdout can be lost; native fault
  events are authoritative. 01 had 1,951 deliberate faults per cell under the
  incorrect permanent-inactivity hypothesis; 02 lost its unflushed marker.
- Production now loads its cheap roster and clears its own old shared claim
  before map initialization. `dz-production-restart-01` proved round-51 cleanup,
  but large-map cold startup exhausted an ordinary budget once. A new first-frame
  rule clears the claim then defers expensive map startup to a fresh turn when
  no boosted budget is available. `dz-production-restart-02` is the current test;
  `dz-restart-safe-idle-01` is the full 140-cell normal regression check.
- Trace now includes draft module exceptions. `tools/dz.py` aggregates repeated
  CT_CHECK names with AND so a later pass cannot hide an earlier failure. Hidden
  private-query denials are asserted. Twelve Python measurement tests pass.
  `tools/dz_assertions.py` audits all previously passing assertion transcripts.
- Death diagnostics optionally need Node 24 and pinned engine assets. Their
  replay reader and loader are frozen and hashed in each new capsule. Other
  experiments still use Python standard library plus the official CLI.

`dz-production-restart-02` now passes four complete games: exactly the one forced
round-50 fault, old claim cleared at 51, ordinary-budget startup deferred, zero
fuel-outs and healthy counters at 100. `dz-restart-safe-idle-01` passes all 140
cells: zero faults/fuel-outs, mean banked 903.34, fuel p99 53,054.
Both contested checks finished: `dz-restart-safe-v65-release-01` and
`dz-restart-safe-v65-trace-01`, 140 games each, zero native faults/fuel-outs;
the trace has zero caught errors. Release mean collected 280.65, banked 187.34,
fuel p99 52,234. All 140 contested release games are losses. The current bot is
still weak; these are runtime checks, not evidence of competitive strength.
The archive verifier now distinguishes extracted lifecycle payloads from match
bundles and checks that each extracted payload matches its authenticated bundle.
No map tuning has begun. Next: controlled basic-clear prediction/measurement,
remaining action/respawn/item conformance, then calibrated objective selection.

### Continuation at 04:07, 2026-10-29

The one-time wakeup fired; its automation was deleted after delivery. There is
no remaining scheduled continuation. A usage-related approval-review failure
previously prevented one local runtime command; after the reported reset it ran
successfully as `dz-module-boundaries-03-runtime` (eight stress cells, zero native
faults/fuel-outs/caught errors). No approval restriction was bypassed.

New work since published checkpoint 53e853e:

- CT-17 tribute/lock fixture passes eight assertions in four cells (`tribute-04`):
  interruption, retained gems, simultaneous team locks, automatic hit on submit,
  five hits, distance-three rejection, full transfer and exact duration.
- Module quarantine now covers observation, boot, shop, camp scan, memory,
  planner, executor, communication and fields after three contained exceptions.
  Memory/planner/executor failures use bounded recovery and clear old claims.
  Failed observation/boot yields; allocation construction still has catch/retry.
- `dz-module-isolation-02`: four completed diagnostic games, zero native faults/
  fuel-outs, exactly three injected exceptions per body and no further retries.
- `dz-module-stale-01`: four completed diagnostic games, exactly one intentional
  fuel-out per body (3/3/5/5), zero native faults and zero module/action errors.
  A deliberately thrown post-resumption error becomes a stale-turn abort, not a
  module failure. The exception path in module_work/Actuator now guards the round.
- Full `module-boundaries-02-idle` and `02-v65-trace` each pass 140 cells with zero
  native faults/fuel-outs; the trace has zero caught errors. Idle banked 901.09;
  contested trace is diagnostic and loses all cells. These include the module
  wrappers; `03-runtime` covers the subsequent stale-exception correction.
- CT-11 `targeting-03` and `targeting-04-reverse` each pass four cells. Damage
  follows the nearer champion after swapping positions. Equal-distance ties hit
  the lower handle after reversing draft order and changing the last attacker;
  neither champion type, original aggro nor last hit explains the result alone.
- New runs include a frozen runner snapshot/hash and both source-tree hashes.
  Completed diagnostics now report real native fault totals; truncated ones still
  mark them unmeasured. Fault injection changes only frozen diagnostic copies.
- `PORTABILITY_FUNDAMENTALS_VERIFIED.json` confirms clean source-only export of
  53e853e rebuilds to the exact tested default 07-control binary on this host.

Wolf/golem/monolith cadence now passes the stricter target-awake/in-range gate:
`wolf-cadence-02` (4 cells), `golem-cadence-04` (2), `monolith-isolated-01` (2).
The monolith map is a separate official-MapBuilder correctness fixture, never part
of strength testing. Earlier attempts exposed damage from outside champion vision.
Production channel checks now refuse hidden potentially damaging camps in range;
experimental camp observation marks them incomplete. Safety remains off.

Final current-source campaigns: `dz-foundation-checkpoint-idle` and
`dz-foundation-checkpoint-v65-trace`, each 140 cells, zero native faults/fuel-outs;
the trace has zero caught errors. Idle banked 902.91 / fuel p99 52,998; contested
trace p99 53,041, zero wins (diagnostic). `FOUNDATION_CHECKPOINT.json` records exact
source/binary identities. No calibrated clear/crew model or strong baseline yet.

The matching uninstrumented `dz-foundation-checkpoint-v65-release` also passes
140 cells with zero faults/fuel-outs: mean collected 282.29, banked 190.76, fuel
p99 52,114, zero wins. Both release campaigns use the exact same default Wasm
`9148f834cc3612ed5e68a3924b4b4e7de4da0684776d5a25df11e36b8b33a000`.
`PORTABILITY_CURRENT_VERIFIED.json` confirms source commit 5df59b6 rebuilds to that
same binary from a clean source-only export (same host, no machine config/cache).
5df59b6 is pushed; later metadata/evidence commits preserve the same bot source.

Next: remaining item/Home/hidden-death/contest fixtures, measured minimal recovery,
then clear/arrival/damage calibration and crew basics. Keep per-map plans deferred.
Eight Python measurement/gate tests and native host tests should pass.

The user explicitly deferred map-specific plans until fundamentals are solid.
Continue `FUNDAMENTALS_AUDIT.md`; no per-map tuning yet. G0 is incomplete and the
bot is weak. Starter numbers below are historical, not current-source results.

Latest frozen campaigns: `dz-fundamentals-07-{idle,v65}-{control,safety}`, each
140 games, all zero native faults/fuel-outs. Safety changes mean banked idle
902.94→917.39 and v65 191.14→187.04; deaths 14.88→7.07 and 18.35→14.76. Both
contested campaigns lose all games. Safety stays default OFF. Full-pool strict
trace audit `dz-fundamentals-08-v65-trace` passes 140 cells with zero native faults,
fuel-outs and printed caught action/module errors. It is diagnostic evidence only.

New fixtures: actions, camps, channels, visibility, capture, reset, fingerprint.
Select with `python tools/dz.py conformance --fixture NAME ...`; use fresh names.
Checks fail missing setup/assertions and unexpected errors. Six Python measurement
tests: `python -m unittest discover -s tests/dz -p test_measurements.py`.

Research correction: **elks attack every round**, not half-rate. CT-24 even/odd
splits and occupied respawn pass on 2/3/23-member groups. CT-26 resets cooldowns
but grants no second cast. CT-27 now pins 1,311 fields in `ENGINE_FINGERPRINT.json`,
checked on two maps/both sides. Remaining limits are explicit in `CONFORMANCE.md`.

Audit fixed action allowances, stunned recall, duplicate observations, camp
generations/dead members, long-group frontier, spawn yielding, cheap immediate
actions, bounded loops and shield/collateral policy. Two introduced regressions
were caught and corrected: repeated camp-interrupted recalls and contract renewal
on oscillation. Preserve failures; do not reintroduce unconditional step renewals.

No map-specific rules, submission, activation or ladder actions were added.

## Current authorization and branch

- Branch: `build/pure-algorithm-zero`, remote `origin`:
  `https://github.com/Infosuii/neural-networkk-battlecode.git`.
- User explicitly approved pushing this branch to that repository. Commit/push
  reviewable checkpoints. Build fresh algorithmic C++; **no old bot code in DZ**.
- User confirmed the existing 70-map pool is the target and authorized read-only
  top-team replay downloads. Do not assume approval for ladder games or activation.
- Never submit, activate, create match groups, or run `ladder_duel.py run` without
  separate authorization. The live bot is unchanged. v76 is the local comparator;
  final fallback selection remains the user's decision.
- Preserve this laptop's pre-existing `config/paths.json` edit and unrelated
  generated/untracked artifacts. Stage explicit paths, never `git add .`.

## What is built

Fresh `bots/dz/src/` implementation, using the official SDK and standard library:
kernel/Actuator/stale-turn guard, budgeted startup and fields, observation, camp
memory and contracts, claim codec, research-prior draft, fixed gear, nearest-group
farming/capture, basic banking and recovery, payload-based attack/reset/damage/CC/
shield spells, dynamic movement and ward placement. Detailed scope and omissions:
`bots/dz/README.md`.

**Advanced models remain disabled/unimplemented.** No auction, validated ObjModel,
EE, crew stance, optimized gear, opening rollout or per-map draft tables yet.
This is a tested walking skeleton. It is not a strong bot or a release candidate.

## Verified results and failures

- Host: 1,536 codec cases plus stale guard, contracts, ledger and bank-rule edge checks pass.
- Same frozen release source: `dz-pool-idle-02` 140 games, `dz-pool-v65-01` 140,
  `dz-v76-screen-01` 12; **0 faults, 0 fuel-outs**, worst pooled-run p99 64,076.
- Against idle: mean 917.1 banked; some maps win on the gold tiebreak.
- Against v65: **0/140 wins**, mean 182.0 banked. Against v76 screen: **0/12**.
- Major camp deaths on 00contest, 01starvation, 02guardians, 02the-pack and
  01shortcut. Models/crews/survival are essential, not optional polish.
- Read `RESULTS.md` for retained failed campaigns and `CONFORMANCE.md` for the
  exact observed/pending mechanics. G0/G1/parity/promotion/holdout are not passed.
- `python tools/dz.py verify` authenticates all completed experiment capsules.

## Next implementation milestone (do this before tuning)

1. Finish CT-11 camp cadence/targeting and CT-7 movement/spell allowances; CT-8/9
   visibility; CT-16/17 channels; CT-24–26 capture/credit/reset. Add automatic
   diagnostic transcript assertions and the complete canonical CT-27 fingerprint.
   Keep deliberate-fault/fuel-out tests isolated from candidates.
2. Extract objective arrival/clear/camp damage/capture data from the preserved
   **SA-IDLE-v76** replays. Build pure ObjModel and host tests, then perform V-M1
   offline (clear error <=20% median, bias <=10%, damage bias <=20%, arrival <=3 rounds).
   No previous bot implementation may be copied; measurements/evaluation tools are allowed.
3. Fix camp survival and add validated crew allocation/single capturer/cluster
   circuits behind explicit flags, one mechanism per experiment. Begin with the
   highest-death idle maps as correctness cases. Do not try to rescue an invalid
   model with threshold tuning.
4. Run idle non-inferiority and a matched v76-on-idle R250/R500 benchmark. Build
   the timeline extractor before claiming the idle parity gate; final totals alone
   cannot prove opening or income parity.
5. Only after conformance/model gates, add the auction, marginal gear and hazard
   banking, then threat/EE offline calibration and controlled contested experiments.

The full 21-file design is in `research/zero-bot-plan-2026-10-28/`; it was read
before implementation. It supersedes the on-v76 design, but is not infallible:
unchanged shared slots cannot prove age; parity/TTL alone cannot prove message
freshness; group >=112 must not alias group 111. See `DECISIONS.md`.
Also check `research/v81/RESEARCH.md`: the broad historical "step-away" metric was
corrected (46.6% vs 42.9%, not the advertised factor-of-two gap). Do not tune against
that invalid headline. The earlier deep-analysis reserved set is spent.

## Portable source/evidence and fresh-system commands

Read root `CONTINUE_HERE.md`. No venv, NumPy, credentials or machine config is
needed for `tools/dz.py`; it uses the vendored official CLI and root CMake/SDK.

```powershell
python tools/continuation_checkpoint.py verify
python tools/continuation_checkpoint.py restore --install-runtime
python tools/dz_support.py verify
python tools/dz_support.py restore
python tools/dz.py verify
python tools/dz.py host
python tools/dz.py build
python tools/dz.py smoke --name UNIQUE-IDLE-RUN --pool
python tools/dz.py smoke --name UNIQUE-V65-RUN --pool --opponent v65
```

- `continuation/checkpoint-2026-10-28/`: existing SHA-authenticated official Windows
  runtime and earlier research evidence. Git contains every part; no LFS download required.
- `research/dz/supporting/`: 61,643,106-byte archive in two <=40 MiB parts, 2,931 files:
  full SA-IDLE-v76 / SA-P-base / SA-C-base summaries/replays/build provenance, plus
  the deep-study research, next-bot brief and loss cases at 19109c4. SHA verified.
  Restore into repo-relative paths; no different file is overwritten. The deep-study
  snapshot restores under `research/dz/supporting/deep-19109c4/` to preserve history.
- `research/dz/runs/*/evidence.zip`: exact candidate and benchmark source, both Wasm,
  logs, full native summary and replay per schedule cell. Current source is not
  substituted into old experiments. ZIPs were fully CRC/content-hash verified.
- `PORTABILITY_VERIFIED.json`: a fresh source-only Git export (no local settings
  or prior bot build cache) rebuilt byte-for-byte to the tested Wasm hash. This was
  tested on the same Windows host using its installed official toolchain; it is
  not a claim of rerunning installation on a second physical machine.
- Replay decoding: Node 24, `NFS_REPLAY_ENGINE=2.0.0`; extract `replay.repl26a`
  from each bundle before decoding. The old camp-regeneration script hard-codes
  the previous laptop path; use a portable copy/import when running it elsewhere.
- Native tests: install C++20 g++ or set `DZ_CXX`. Official bot builds use the
  restored WASI SDK, independent of the native compiler.

## Evaluation discipline

Read `HOLDOUT.md` and `SEED_LEDGER.md` before experiments. Seeds 101–110 dev,
111–120 validation, 121–124 once-only frozen release holdout; 3/4 prohibited.
DZ v0 is deterministic and does not consume a seed. Do not relabel duplicate
identities as independent samples. Bug/geometry checks can use all maps; parameter
selection must respect the held-out-map partition. No new top-team download was
needed for this starter; existing data was enough.

## Checkpoint and continuation

53e853e was pushed and its remote HEAD verified. Verify newer commits and working
changes on resumption; use the latest audit above before the older starter list.
The initial starter binary (historical, not current) was
`c5486461a5f8704409f5cf9293a3ca20a49ba7f53152732ba20a068e2d2a9872`.
No scheduled wakeup remains; the requested one-time continuation has fired.
