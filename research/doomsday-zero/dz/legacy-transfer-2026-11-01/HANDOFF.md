# PAUSED — DOOMSDAY Zero legacy decision transfers

Fresh clone: start at `../../../FRESH_LAPTOP.md`. The user subsequently authorised
repository pushes and a portability check, while gameplay stays paused. The
original request, later steering and all reference replays are now committed;
`tools/dz_restore_run.py` recreates every ignored path used below from Git
capsules. No old laptop or credentials are needed to recover the evidence.

Paused at the user's explicit request on 2026-11-01: no usage remains. Do not
resume gameplay work until the user resumes it. All already-started jobs ended;
no new matches or builds were started after the pause. This handoff is WIP,
not a release recommendation or a claim that the performance gap is closed.

## Start here

Workspace: `C:\projects\cambridge battlecode\work\neural-full-stack`.
The parent `C:\projects\cambridge battlecode` is not a Git repository.
Branch: `experiment/dz-lifecycle-repair-2026-11-01`.
Previous checkpoint: `c79c23fae7ad938302b92cf02e7bb4ad1cdd8270`.
The source at pause is candidate **24**, with experimental flags still zero by
default. Native screens enabled `DZ_ECONOMY_V2=1,DZ_LIFECYCLE=1` in frozen copies.
Read `../LEGACY_TRANSFER_ROADMAP.md`, this file, and `RUNS.json` first.
The preceding session is documented in `../productive-cycle-2026-11-01/README.md`.

**Known failing check to fix first after resume:** `tools/dz.py host` stopped
compiling `tests/dz/host/sequence_test.cpp:68`. The new prefix test uses
`auto prefix=search`, but `SequenceSearch` contains a deliberately noncopyable
`RouteSearch`. Construct a separate `SequenceSearch` and copy only the fields
the test needs (`stage,count,actors,roster,phases`); do not make RouteSearch
copyable. This is a test-fixture compile failure. Candidate24's Wasm built and
its native games completed. No fix was made after the user requested pause.

## User direction and scope

- Transfer the *decisions* that make v76 and peer bots strong, inside DZ's
  Goal/Memory/kernel/Actuator. Do not copy their architecture or learned weights.
- Prioritise opening tempo, first-job timing, missed resources, camp clearance,
  gold/equipment, drafting, survival and combat. The user identifies these as
  steps15–18/21 and says the reference is probably Z-plan. Exact numbering was
  not found in the checked-in Z0–Z15 plan or `origin/build/z-plan`; the named
  outcomes are now explicit in the roadmap. Do not spend another audit hunting
  the numbering before doing useful work.
- Accept productive gameplay/design risk. Implement coupled known repairs
  before testing. A losing package requires diagnosis and repair, not instant
  removal. Preserve 05/06/09/10 and every transfer package below.
- No Varg in any draft. Preferred core Vendetta/Marcella/Vesper, with Heart/Ryth
  and complementary map drafts allowed. The source retains the observed
  Vesper/Heart/Vendetta collision/packs prior and all unique/non-Varg assertions.
- Local development, checkpoints, replay reading and local tests authorised.
  No remote push/merge, online games, submission, activation or release changes.
- Preserve user `config/paths.json`, unrelated binaries, compile databases and
  untracked `bots/v81home`. No applicable AGENTS.md was found. No subagents were
  requested; do not delegate without authorisation.
- Fourteen reserved maps (every fifth lexically sorted of70) and seeds121–124
  remain reserved. Only collision/packs/corners development trajectories and a
  separate generated correctness fixture were used here. No new ladder fetches.

## Actual progress and limits

The user's celebrated **914 versus498 gems** is the exact six-cell total for
candidate15 versus candidate13, on collision/packs/corners A/B against the same
v76lab binary. The repair preserved30k fuel for resource selection/execution
after optional combat forecasting. Candidate13 had189 fuel-outs; candidate15
had zero. It is an observed screen improvement, not proof of general strength.
Candidate15 is retained; later opening repairs did not monotonically improve it.

| Untraced package | Collision A/B | Packs A/B | Corners A/B | Runtime |
| --- | --- | --- | --- | --- |
| 10, prior session | 80/26 | 56/56 | not in that capsule | zero faults/fuel-outs |
| 11, first transfer batch | 0/0 | 148/14 | 0/0 | zero |
| 13, detail-clock fix | 131/146 | 84/28 | 89/20 | 189 fuel-outs on corners |
| 15, execution budget | 89/175 | 204/100 | 326/20 | zero |
| 16, earlier startup | 121/103 | 56/28 | 142/91 | zero |
| 17, explicit first resource | 110/168 | 56/28 | 204/66 | zero |
| 18, finite post-resource team window | 127/168 | 124/56 | 157/69 | zero |
| 19, home-side equal-route choice | 231/66 | 102/100 | 225/64 | zero |
| 20, contested crew planning | 165/66 | 102/56 | 225/48 | zero |
| 21, useful staging | 231/66 | 84/56 | 225/66 | zero |
| 22, cheap raw roster | 315/62 | 84/36 | 225/66 | zero |
| 23, bounded search batches | 227/223 | 28/56 | 225/66 | zero |
| 24, priced first-phase offers | 227/223 | 84/84 | 225/66 | zero |

Every v76lab competitive cell still loses. Candidate24 totals909, approximately
candidate15's914, with a different distribution. **Do not call the fundamental
gap fixed, select a release, or treat the latest package as unambiguously best.**
Trace binaries behave differently because diagnostics consume real fuel; their
scores are diagnostics, not another independent competitive confirmation.
No current transfer package has yet been checked against v81hl.

A direct native correctness control *does* prove a missing resource class is
unblocked: `dz-transfer-large-resource-control-10` banks0/0 and collects0/0;
`dz-transfer-large-resource-23` banks1008/126 on the identical 72-member fixture,
with zero faults/fuel-outs. These idle-opponent fixture outcomes are not strength
claims. The native outcome field even assigns one win to the zero-score control;
use receipts, collection and banking rather than its nominal wins.

## Implemented source and why

1. `opening_cache.*`, `opening_catalog.h`, draft/kernel/static_world:
   versioned, dimension-checked public draft bytes cache the six camp designs.
   SDK4 already caches camp kind/spawn position; the initial redundant member
   copy was stopped in16. The generic catalog still contains a tested optional
   member section, currently emitted empty. This can be simplified later.
   Startup progresses through up to32 bounded stages instead of8, spends
   otherwise idle boot fuel, and may initialise memory/act on the same adequately
   funded turn. Actual packs-B first movement improved R5→R3 in15→16, and first
   basic R16→R12; earlier tempo alone did not improve later farming.
2. `lifecycle.cpp`: all cheap job bounds are ranked before exact prices. The
   first11 batch wrongly charged ranking against the16k exact-work clock, causing
   zero jobs examined on collision/corners. Fixed13. Early gold weight .20 fades
   to .12 byR400, a hand-authored experiment inspired by legacy item tempo.
3. `clear_risk.h`, `actions.cpp`: harmless groups no longer inherit the64-monster
   workspace exclusion. Work retains per-member rounding and a finite2,000-hit
   horizon. Damaging groups retain their supported limits. Large navigation-root
   sets are built locally and resume, then cross the SDK boundary once.
4. `draft.cpp`: preserve observed map lineups; repair general portfolio admission
   for all group sizes with exact identical-member multiplicities. Lifecycle
   alternatives are the five core picks and need10% model improvement over the
   prior. No learned policy imports. A retained variant6 linked-draft test on
   package19 banks collision136/168,packs56/92 and loses all4; not promoted or
   rejected as an idea. Shared fate/economic staffing still need proper work.
5. `safemode.cpp`, `engage.cpp`: optional combat forecasts keep30k for actual
   decisions/actions. The bounded fallback counts allies that can reach combat,
   checks voluntary engagement against in-range help, and can regroup toward a
   healthy ally without increasing observed enemy danger. Incomplete optional
   rollouts do not by themselves prove a losing singleton/crew fight.
6. `actions.cpp`: retain earlier in-range camp focus, kill resets and healthy
   damaging dashes. Refresh reset targets from bulk live camp tiles rather than
   many per-member SDK calls. Equal-score movement/dash routes prefer the home
   side rather than the first(-1,-1) direction that cut toward enemy resources.
7. `lifecycle.cpp`, `crew.*`, `main.cpp`, memory: first packs resource is an
   explicit finite opening, not a3x multiplier that could miss detailed pricing.
   After it, a30-round window stages toward the observed home-side wolf/elk job
   (SDK/native camp enum names differ; trust SDK design stats). Defers banking
   the first bag while forming a real crew. Followers accept real leases after
   finishing their current job. Cheap raw rosters use visible HP/basic strength,
   factor1 and no speculative kit/equipment credit. Actual accepted execution
   still reads its kit. Routine bank/shop triggers no longer tear down an active
   crew. Real losing contact and survival still interrupt it.
8. Crew search budget checks now batch8 local primitives; raw planning previously
   spent too much on repeated SDK bookkeeping. The full sequence still took
   ~15 rounds for its first priced phase, longer for all4. New24 permits a
   **Prefix** offer for one fully priced visit and its exit, while later phases
   continue in background. `complete` remains false for such an offer; it does
   not promise a group payout. Formation, lease consent and the existing attack
   agreement remain mandatory. If a following phase is not ready, the stored
   staging exit becomes the managed destination with firing disabled.
9. `gear.h`: a committed funded shop transaction keeps its quoted purchase;
   other lifecycle shopping retains the existing fixed/map build. Speculative
   gear pricing and bank-field work cannot take precedence over active raw work.

## Unfinished proof and highest-impact next work

1. Fix the noncopyable test fixture described above, then finish host checks.
   Before24, the24 pre-existing host suites passed and the new catalog/resource
   suite passed separately;58 Python tests passed. The last host run stops at
   sequence_test compilation, so do not report25 current suites green.
2. **Prove physical post-resource crew payoff.** Trace22 showed real count3
   rosters atR27+, but repeated Budget results. Trace23 got first complete phase
   atR43; roster changed byR52. In24's retained trace there are Budget lines
   throughR31, then a count2 restart atR52. No native CREW_COMMIT/CREW_ATTACK was
   found in the packs-B opening log. The new prefix path compiled and screened,
   but has not yet demonstrated its promised execution. Do not equate an offer
   or prefix quote with a clear/capture. Use a dedicated production fixture to
   isolate coordination, followed by the same small contested comparison.
3. Audit new prefix logic carefully: published count must mean all routes and
   prices are complete; actual roster/HP/gear must still match; stale future
   geometry must not authorise a strike. Return/escape routes need current
   neutral validation. The raw roster's current observed strength may vary with
   health on some champions; it is not a calibrated future lower bound. Avoid
   resetting resumed work merely for irrelevant state changes, while preserving
   actual safety. Source23's full-sequence policy and15's simpler policy remain
   exact alternatives for diagnosis, not reasons to remove24 after one attempt.
4. Compare actual first job/receipt/purchase, R100/R250 gold/spending, per-body
   collect→bank→purchase→return cycles, deaths and delivery. Native helper tools
   below already exist; do not restart the archive audit or broad70-map screen.
5. Once a material package is coherent and verified, compare its exact same
   binary against v81hl as well as v76lab. No current parity/strength claim.

## Evidence and tools

Every completed transfer run has immutable `research/dz/runs/<name>/`
`provenance.json`, `results.json`, `evidence.zip`. Exact source/builds and stdout
also remain under `artifacts/tmp/dz/<name>/`; source is `build/candidate/src`.
`RUNS.json` inventories every capsule, binary hash, per-cell result and source
location. `SOURCE_AT_PAUSE.json` hashes current source/tests/tools. These files
are generated during handoff; historical capsules are not rewritten.

Useful exact run names: `dz-transfer-package-11`, `dz-transfer-diagnostic-12`,
`dz-transfer-budget-repair-13`, `dz-transfer-corners-diagnostic-14`,
`dz-transfer-execution-budget-15`, `dz-transfer-opening-repair-16`,
`dz-transfer-opening-team-17`, `dz-transfer-post-resource-18`,
`dz-transfer-post-resource-trace-18`, `dz-transfer-home-approach-19`,
`dz-transfer-home-approach-trace-19`, `dz-transfer-linked-draft-19`,
`dz-transfer-contested-crew-20`, `dz-transfer-contested-crew-trace-20`,
`dz-transfer-crew-staging-21`, `dz-transfer-crew-staging-trace-21`,
`dz-transfer-raw-team-22`, `dz-transfer-raw-team-trace-22`,
`dz-transfer-search-repair-23`, `dz-transfer-search-trace-23`,
`dz-transfer-large-resource-23`, `dz-transfer-large-resource-control-10`,
`dz-transfer-first-phase-24`, `dz-transfer-first-phase-trace-24`.
Two attempted custom-map `smoke` commands were rejected before creating runs;
custom maps correctly use `scenario`, not `smoke`.

The correctness fixture and exact manifest are in `fixtures/`. Its generator is
`tools/dz_make_fixtures.mjs`, using the official engine MapBuilder. Source/raw
strong-team references remain in
`artifacts/local-only/dz-cycle-reference-2026-11-01/`; attribution is retained
in `../productive-cycle-2026-11-01/references.json`. No versions of elite bots
were publicly identified; public peer-source strength is not independently proven.

Python: `C:\Users\omdha\AppData\Local\Programs\Python\Python313\python.exe`.
Compiler: `C:\msys64\ucrt64\bin\g++.exe`.
Native CLI: `tools/vendor/cambc.exe`, SDK4/engine2. Runtime builds require the
normal approved escalation to the installed runtime. Describe local purpose;
do not ask the user again for already-authorised local testing.

After explicit resume, useful commands (PowerShell, from the repo):

```powershell
$py = 'C:\Users\omdha\AppData\Local\Programs\Python\Python313\python.exe'
& $py tools/dz.py host
& $py -m unittest discover -s tests/dz -p 'test_*.py'
& $py tools/dz.py verify --names <only-the-new-run-names>
& $py tools/dz_cycle_report.py --names dz-transfer-execution-budget-15 dz-transfer-first-phase-24 --output artifacts/tmp/dz-transfer-comparison.json
& $py tools/dz_extract_replay.py --run dz-transfer-first-phase-24 --map 00packs --side B --output artifacts/tmp/new-inner.repl26a
$env:NFS_REPLAY_ENGINE='2.0.0'
node --no-warnings tools/dz_reference_trace.mjs artifacts/tmp/new-inner.repl26a artifacts/tmp/new-trace.json
```

For new tests always use fresh names. Opening diagnostics should set
`--trace --set DZ_TRACE_FROM=1 --set DZ_TRACE_TO=100`; default trace range100–250
hid the opening behind a3k formatting allowance. Native event4 is movement,
5 basic attack,6 ability; event23 is a blocked move, not a dash. Per-body SDK
views are legal; full-world diagnostic scenes are offline evidence only.
