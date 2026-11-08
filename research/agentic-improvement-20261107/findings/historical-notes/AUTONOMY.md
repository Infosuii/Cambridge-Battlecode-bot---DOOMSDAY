# Battlecode improvement routine

Updated 6 November 2026. Local development and replay collection are enabled.
Existing-bot unranked sampling is enabled; bot upload and activation are disabled. Original v111 and
x1 remain frozen. No candidate has established a substantial general upgrade.
See BOT_RESULTS.md and autonomy/data/mistake-review/REVIEW.md.

## Implemented loop

1. Read existing own ranked/unranked matches plus a bounded top-team sample.
   Retain metadata, native summaries, replays and engine identities.
2. Reconcile score exactly: camp collection, champion collection, actual losses
   and independently observed final bags must equal native submissions. Separate
   ranked/unranked and rating bands. Correlation remains diagnostic, not causal.
3. Select six incidents after accounting, prioritising known-policy failures,
   clean farming deficits and a labelled same-map win. Different opponents make
   that comparison observational, not a controlled counterfactual.
4. Decode with pinned official engine3 visualiser assets. Scores, rosters and
   final bags must match native summaries. Inspect backtracking, stationary
   periods and pre-death windows. Full-state information never becomes bot input.
5. Give a bounded analyst incidents, exact source and intervention memory. Bulk
   processing makes no AI calls. The signed-in analyst is capped at two calls/day
   with no paid API fallback or automatic account rotation. A $20 plan does not
   imply a particular remaining allowance.
6. Apply focused proposals in isolated copies. Test normal-fuel frozen releases
   on24 development maps against six styles, then preselect before60-map
   confirmation and44-map final validation. Historical exposure is acknowledged;
   these campaign partitions are not pristine team-unseen holdouts.
7. Decode actual local failures, preferring regressions where the matched baseline
   won. Carry that evidence, including confirmation failures, into focused repairs.
   Preserve Accepted/Retry required/Conditionally useful/Parked/Rejected labels.
   A failed first gate never automatically rejects a strategy.

Memory improves evidence available to future analysis. It does not retrain the
language model or guarantee rising ELO or diagnosis accuracy. A locally qualified
candidate is retained for review; official promotion remains disabled.

User resource preference: local laptop compute can be used heavily; signed-in
AI usage is limited. Reserve reasoning for strategy, tactics, traced errors and
experiment decisions. Bulk games, parsing and reports run locally. A no-AI
strategy review runs after three new completed confirmation results and feeds
the next analyst brief. The first review found14 distinct confirmation reports,
zero substantial-threshold hits;8 of11 matched positive-development searches
lost their positive gain on confirmation. These trials share map families and
are not independent statistical evidence. The search therefore prioritises
verified mechanisms/dependencies and preserves broad independent qualification.

## Controls

From C:\projects\cambridge battlecode\work\agentic-improvement:

```powershell
.\autonomy.ps1 -Action observe  # Read-only collection and deep replay review
.\autonomy.ps1 -Action start    # Also allow bounded AI proposals and local tests
.\autonomy.ps1 -Action status
.\autonomy.ps1 -Action stop
```

The hidden process checks every ten minutes and prevents sleep while active.
It does not install reboot startup. Status, receipts and logs are in autonomy/data.
Observe mode cannot reach editing, simulation or platform-mutation paths. Local
bot work in this chat is separate. Expired login produces needs-attention; use
normal official login without sharing passwords.

platform_enabled=true permits the requested existing-bot unranked sampling:
three five-game groups/day, quota reserve10 and one configured account. Each
creation checks the expected active version and avoids duplicate request tags.
deployment_enabled=false blocks upload and activation. Today6November already
used all three sample groups and both AI calls; bulk collection/review continues.

## Current evidence

At13:01 the refreshed end-to-end cycle decoded427 games, including310 of ours
and151 losses. The selected incident review covers farming, combat transfers,
monster deaths, final held gems, fuel and a clean farming deficit.
These are descriptive categories. Only15 games have locally pinned v111 version
provenance; historical own versions are otherwise unknown.

A replay-confirmed hidden-camp detour conflict made Cassi alternate between the
reveal approach and firing ring. A bounded commitment reduced374 backtracking
samples to19 and raised her camp gems51 to122 in a frozen release reproduction.
The team still lost. Its60-map confirmation was -1pp pooled,58/120 direct, zero
faults. The repair is conditionally useful and is not the default champion.

Extra logging matched the untouched debug bot in12/12 diagnostic games; debug
and release outcomes matched only7/12. Mechanism evidence and release strength
therefore remain separate. Teammate contributions are in TEAMMATE_REVIEW.md.
No teammate checkout/job changed and no repository messages were posted.

The ten-round retreat/join cooldown helped development but failed60-map
confirmation (-0.83pp,56/120 direct). A second focused repair is compiled and
awaits the current training job: suppress only the first two rounds after a
retreat. Existing diagnostic logs contain40 joins in that window,21 followed by
another retreat within three rounds, versus12/49 for delays3..9. This motivates
a test, not a claim that all reversals are wrong. Evidence and exact input hashes
are in autonomy/data/mistake-review/reengage-timing.json.

The native-probability training run completed16x256 games. Iteration12 remained
selected at58.3%,26/48 direct, versus54.9% for the initial checkpoint. Its frozen
44-map/nine-style release validation completed at13:24: +0.71pp pooled,
43/88 direct,90% map-cluster interval[-3.98,+5.54]pp. The three excluded styles
had zero pooled gain; rush alone regressed6.82pp. This is Retry required.

An independent capture audit checked all1,584 scheduled release cells, explicit
complete captures and zero own faults, unchanged map/Wasm hashes and one engine
build. Unknown fault counts now fail validation instead of becoming zero.
Six general regression replays and six rush regressions were decoded with native
parity checks. The two-round retreat repair passed development (+6.25pp,
29/48 direct); its frozen60-map confirmation is running. A separate compiled
base/retreat/learned/both experiment will test their interaction.

Later confirmation of learned+retreat also failed (-0.52pp,64/120direct over60
separate maps/nine styles). Its2,160 native captures and frozen artifacts audit
cleanly. The economy-preserving Ryth draft/role direction is Parked after focused
dependency attempts and actual failed replay review; no general gain.

At14:03 a win-objective training repair passed preflight and started32x256 local
games with8workers/GPU. It uses terminal team outcome with bounded telescoping
potential, a fresh critic and prior-round critic features. Original actor/roster/
temperature/native-probability checks remain. Training sources/maps are frozen;
24selection maps and60final maps are disjoint from training by exact bytes.
Normal-fuel final qualification uses nine styles. This is Retry required until
the independent release evidence proves improvement.

A release-only target-policy search is queued after that run. It learns48
target-head adjustments using paired actual compiled games, with no per-game AI
calls. Zero adjustment is byte-identical v111. It selects only population-mean
policies every4generations and qualifies a frozen winner on separate60maps/nine
styles. It will not run concurrently with the active training owner, and will
defer if that run meets the substantial threshold. Current results remain
unqualified; the original champion stays frozen.

Earlier operational history is preserved in
reference/autonomy-before-replay-review-20261106.md. Its old running/status and
preliminary results are superseded by this document and later evidence.
Controller controls now have separate stop domains. `autonomy.ps1 -Action stop`
requests only the controller to exit; independent local training/searches keep
running. `-Action reload` uses that same isolated marker, verifies the controller
runtime identity and waits for exit before starting another instance. The genuine
global `autonomy/STOP` still stops experiments; controller start never clears it.
This prevents a controller refresh from cancelling an unrelated frozen benchmark.

Before spending an AI call, the analyst now receives compiler-derived settings
from both active C++ translation units. The extractor strips all object/dependency
outputs before running the preprocessor, rejects indirect/plugin commands, checks
unchanged object/Wasm/source hashes and stores full provenance. Undefined macros
are distinct from definitions whose value is0. These settings describe compilation;
runtime inputs, call order and mutable knobs still require separate investigation.
Optional historical summaries can be reduced to fit the reasoning budget; core
incidents, source, current repair and compiler settings remain intact. Oversized
core evidence fails before reserving an AI call.



## Local compute expansion,6November2026

Main corrected retuning uses8native game workers. A separate lower-priority
8worker development league uses spare cores (~96%totalCPU measured). After its
5040games and strict replay/capture audit, checkpoint_transfer_queue.py tests
newly accepted training checkpoints:1680new games each on120maps/7styles/both
sides, reusing3360frozen original/parent controls. It requires initial league
completion, so these two extra jobs never run games together. No additional
model calls are needed per game. Each checkpoint and acceptance receipt is
frozen before its league; source/maps/CLI/SDK/currentbuild/both-team/runtime
and complete-schedule evidence stay audited. Failed replays decoded.40GBfree
storage reserve. STOP is honored. These processes keep the laptop awake.

These120maps are development: published60 overlaps native training; prior
synthetic60 was previously used. The separate primary24dev/new60final/44repeat
sets are excluded. Queue findings inform later focused repairs, never posthoc
current-final swapping or official activation. Service controller defers new
reasoning/trials during main OR extra/queued work; replay collection continues.
Read training/runs/corrected-strategy/runtime.json and autonomy/data/experiments/
extra-compute-transfer-league-20261106/runtime.json and checkpoint-transfer-
queue-20261106/runtime.json for actual status. Do not launch a duplicate owner
or edit frozen active sources. No official bot submission/publication/activation.


## Representative replacement actually started (2026-11-06T22:54:20.438795+00:00)

Old8+8tuning/league owners exited deliberately after repeated broad transfer failures. A single16worker representative_supervisor.py now owns local games. It keeps the corrected bank-arrival state repair, original/g12 NNalternatives and a frozen old contender, uses stratified48+48map batches/all9styles and54map development rollback. Source/hash/normal-fuel/currentbuild/both-team/runtime checks include exact native mapHash versus frozen input. Separate60newfinal+44publishedrepeat remain reserved; one final selection, no swaps. Working components and smaller gains stay distinct from the substantial goal.

The lower-priority representative_review_worker.py inspects every failed fresh proposal and both frozen final panels, with paired replay/context evidence and a fallback for shared defeats. It launches no games or model calls. Collector defers reasoning/trials during native OR replay-worker ownership.49tests pass. Actual runtime/evidence lives in training/runs/representative-corrected-v2. No official submission/publication/activation is authorized.
