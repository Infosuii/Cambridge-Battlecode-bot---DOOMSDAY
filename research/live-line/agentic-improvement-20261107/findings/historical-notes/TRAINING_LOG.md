# Training development log — 6 November 2026

## v111 continuation setup

Original checkpoint10/header and actor/critic archive remain frozen. The initial
actor re-export is byte-identical to v111. PyTorch 2.11.0+cu128 reports sm_120
support and completes a real CUDA matrix operation on the RTX5070 Ti laptop GPU.
CLI5/engine3 source builds and complete local games are verified.

New workspace: training/. Normal platform fuel; stochastic target selection and
training logging occur in the existing debug-block mechanism. Opponents compile
before parallel games; no per-game shared-source builds. Initial optimizer is
fresh because the old run did not save it. New optimizer/RNG states are saved.

Protocol: 24-game pilot, policy-data checks and one update, then a bounded
ten-iteration run of 96 games/iteration. Development evaluations are stratified
by v111/nnm4/v92 and excluded from this run's training map bytes. These maps were
historically used, so they are not claimed as untouched final tests. No platform
mutations are performed by these scripts.

## Focused integration repairs

- Retry required: first pilot failed before simulation because Python -P removes
  the script directory from module search. Added the explicit local module path.
  Evidence retained in training/launch-history. Trainer now starts and exports.
- Retry required: 24 rollout games completed without runner failures, but the
  inherited reader expected the output path itself to be a ZIP. CLI5 uses a
  directory containing the replay ZIP. Added checked folder/file handling;
  inspected a failed-run game and recovered 297 NRL decision rows and 294 NRZ
  summary rows. Retrying the same pilot, not changing strategy parameters.
- Interrupted batch evidence is moved to a checked local attempt path before a
  retry. Original files, v111, other checkouts and previous attempts remain intact.

These are integration findings, not strategy rejections or evidence of a stronger
bot. The promotion/reliability question remains open after training.

## Pilot completed

Accepted (pipeline execution only): 24/24 rollout games completed; parsed 9,250
decisions (2,849 changed targets and 6,401 sampled keeps). GPU update produced
student_1.pt, value_1.pt and resume_1.pt with optimizer/RNG state. Measured
actor/trainer log-probability difference: median 0.0000397, p90 0.0481, maximum
2.2737. The small median/p90 pass the predeclared integration guard; the tail
remains a quantized-actor/training limitation to examine before promotion.

Pilot development score moved from 7/12 to 6/12; direct v111 result stayed 2/4.
This is not evidence of improvement or competitive rejection. It establishes
the engine3 rollout -> trace -> GPU update -> release evaluation path works.
The supervisor proceeded to the bounded ten-iteration run from frozen v111,
with the original critic and a fresh optimizer, independently of pilot weights.

## Broader opponent league repair

After the initial continuation failed broader confirmation, inspected opponent
regressions and retained the original actor/critic, reward, features and normal
fuel. Changed the training mixture to v111/nnm4/nnm4n1/v92/x1/x3ctr/p65pack.
Checkpoint selection penalizes a losing direct v111 score and any individual
opponent regression beyond 1/12; this rule was fixed before this run.

Completed eight updates, 1,536 rollout games and 604,317 parsed decisions in
training/runs/diverse-league. All batches passed finite-data and probability
parity guards. Median probability discrepancies were small; maximum discrepancies
remain a quantized actor limitation (iteration 8 maximum 11.91), not erased by
the median/p90 guard. Actual logged behavior probabilities feed PPO.

Selected checkpoint 8 by the predeclared development score: 97/144 (67.36%)
versus original v111 84/144 (58.33%), direct v111 15/24, with no opponent
regression on that development panel. This is selection evidence, not confirmation.
Only nn_weights.h differs in the candidate source.

Frozen confirmation uses 32 generated maps excluded by byte hash from this
run's 74 training and 12 development maps, six opponents and both sides.
Historical exposure by teammates is unknown. All 768 games use SDK5/CLI5,
engine3 and normal fuel. Final classification and results are saved separately
in autonomy/data/experiments/diverse-league-repair-20261106/record.json.

Confirmation did not pass: +0.9375pp over 320 matched opponent cells, map-cluster
90% interval [-5.625,+7.1875]pp; direct31/64; nnm4 regression12.5pp; zero faults.
Inspected win-to-loss flips: several show more champion deaths without more
fuel exhaustion. Parked after a doubled heuristic-preservation margin control,
its interaction with new weights, and half actor displacement all failed to
demonstrate competitive improvement on the now-exposed development cells.

## Combat reset repair and focused retries

Found the disabled dead-target guard and the stale Vendetta cooldown cache.
Tested base/guard/eager-refresh/both on12 maps, six opponents, both sides.
An isolated debug twin's three replay bundles show34 cooldown corrections and
25 dead-target cases (24 without a visible replacement target). These establish
runtime exposure, not competitive gain. Initial variants had mixed outcomes.

Investigated unconditional target-liveness queries even when no reset is ready,
and two live-cooldown queries after every Vendetta hit. Two focused repairs:
admit guard work only for ready resets; then retain a lazy Vendetta refresh only
after a dead target. Both score14/24 directly but remain negative pooled on dev.
Because the mechanism is verified and direct benefit promising, froze the lazy
repair for a separate32-map confirmation without lowering acceptance gates.

Confirmation:33/64 direct, +0.625pp over320 matched opponent cells, map-cluster90%
interval[-1.5625,+2.8125]pp, zero faults. No reliable strength gain established.
Classification Retry required; no ladder actions. Original weights unchanged.
Exact tested source/Wasm and explicit limitations are in release/combat-reset.


## Native-policy/current-map continuation, 6 November12:33

**Retry required; training in progress, no strength claim.** The previous turn
advanced the goal through verified replay mechanisms and failed independent
strength tests; it was progress, not a completed improvement.

The join cooldown candidate gained7.5pp on24 development maps, but60-map
confirmation was -0.83pp, cluster90%[-4.67,+3.17]pp,56/120direct, zero faults.
Six failed release replays were inspected. Keep the mechanism for focused
context-sensitive repairs; no first-gate rejection or promotion.

Before more RL compute, audited all71,439 retained rows from the old diverse
iteration8:1,798 had float/native logp error>0.25,74>1. The float trainer omitted
deployment's bounded Q11 preprocessing. On preselected worst-tail games, matching
that preparation reduced the two worst errors11.91->0.38 and6.74->0.43.

Added full native behaviour-logit records and complete stochastic-decision
logging (KEEP1). The first16-game preflight stopped on unmatched records. Replay
inspection found zero padding between guest output chunks: deleting padding
joined an NRL line to the next P message, silently dropping it in the legacy
parser. Preserving padding as line separators recovered all6,602 legacy sampled
records in those16 games. The failed artifacts remain preserved.

A fresh isolated preflight with complete logging passed49,546 decisions:
maximum native/logged logp discrepancy0.00001216, below0.0002. Four meaningful
policy/framing tests pass. No faults or chronology rows are silently filtered.
The current method uses exact native old-policy probabilities plus float-logit
differences as a differentiable update surrogate. This is not bit-exact inference
at updated quantized weights; independent native releases determine strength.

The main run uses16x256=4,096 games:80% on60 current published training maps,
20% generated training maps. Original reward, roster and architecture remain.
Selection uses24 other published maps every4 iterations. Frozen final evaluation
uses44 disjoint maps and nine opponent styles, three excluded from training and
selection. Historical team exposure is acknowledged. Source snapshots, RNG and
optimizer checkpoints, per-batch native/map hashes and full evidence persist in
training/runs/native-current and training/v4/bench_out/nc. Initial untrained
release is byte-identical to frozen v111. Original x1 and other checkouts stay
untouched. No subscription AI calls or official bot changes are part of this run.

6 November,13:10 update: iteration12 selected at58.3% on288 selection games,
26/48 direct, initial54.9%/24of48. Iteration8 regressed and was not selected.
Selection gains are not confirmation. Four more iterations and the frozen
44-map/nine-style native release comparison remain in the existing supervisor.

Audited potential critic timing leakage using16 complete preflight games,
49,546 decision records and179 own death events. All death counters change at
the native event round, but no death shares a round with that body's logged
farm decision. This proposed audit is inconclusive, not evidence of causal
features or proof of leakage. Do not change the running trainer on that basis.

Prepared and compiled focused retreat/join repair2 in an isolated release.
The failed ten-round guard may suppress later useful reinforcement; the new
guard covers only the observed two-round rebound window (40 joins,21 followed
by a retreat within3 rounds, versus12/49 at delays3..9). Original debug parity
is checked and stdout framing preserves NUL separators. Seven of12 diagnostic
games match release, so paired release games remain necessary. Classification:
Retry required, compiled, awaiting training completion before simulations.

6 November,13:18: all16x256 native-anchored rollout games completed. The last
batch validated727,676 decisions, max logp error0.00001335. Final selection and
the44-map/nine-style release evaluation are still running in the same supervisor.

Investigated the old Ryth draft's failed40-map confirmation from480 paired
native release cells. The roster swap was inactive in276 cells/23maps, with
identical score-accounting metrics. In204 cells/17maps it replaced Marcella:
all-opponent win delta -5.39pp, team earned-gold delta -245.6/game, mean team
camp collection +19.2, own submissions +2.4 and held gems +15.4. This is a
whole-intervention association, not proof that gold alone caused the losses.

Compiled a third focused siege attempt: retain Marcella and replace the twins
with Ryth only on the existing custom five-member draft path. Original/draft/
repaired role/both will be compared on published development plus the original
diagnostic maps. Actual native rosters are checked, including retained Marcella;
no inactive-map result will be treated as a mechanism test. Weights are byte-
identical to v111. Classification Retry required; release tests pending.

6 November,13:24 final native training result: iteration16 selection53.5%, so
iteration12 remains frozen as auto_native_current16. Final44maps/eight reference
styles plus v111:704 matched reference cells,+0.710pp,90% map-cluster interval
[-3.977,+5.540]pp;43/88 direct. Excluded three styles pooled0pp; rush -6.818pp.
Substantial pass false. Classification Retry required, no promotion.

Independent post-run audit verifies all1,584 scheduled cells, explicit complete
native captures, zero own faults for both candidates, one engine3build and all
frozen map/Wasm hashes. Fixed benchmark validation: missing/None/bool/negative
fault counts and partial captures cannot become a zero-fault strength result.
The existing16-test suite passed; the additional unknown-comparison test was
corrected to supply a complete row fixture and all4 capture tests pass.

Decoded6 general regressions and6 rush regressions. Several farming collapses
coincide with extra deaths despite no fuel increase (e.g. contest versus rush:
-1,200 camp gems,+31 deaths,-1 fuel event); other losses include unbanked bags.
These are paired intervention outcomes, not proof of a single causal mechanism.

The focused two-round retreat guard development result is +6.25pp,
90% interval[2.083,10.833]pp,29/48direct,zero faults; all five reference gains
nonnegative. Its60-map confirmation started13:26 and remains frozen. Compiled a
separate original/guard/learned/both factorial using the exact iteration12
header and the same guard. Their interaction is unmeasured; no assumed additive
gain. The economy-preserving Ryth factorial is also compiled, awaiting games.

6 November13:45 update: two-round guard60-map confirmation -1.833pp,
54/120direct,zero faults. Six actual regressions decoded. The learned+guard
factorial gave +9.167pp/33of48direct on development but failed60 separate maps
and nine styles: -0.521pp,90% interval[-4.063,+3.125]pp,64/120direct. All2,160
cells explicitly complete, zero own faults, frozen artifacts unchanged. Both
remain Retry required. This is further evidence of development selection
optimism, not a substantial bot upgrade.

The initial no-AI strategy review found14 distinct confirmation reports, zero
substantial threshold hits. Of11 matching development/confirmation pairs,
8 positive development results lost their gain; median drop4.167pp. These
are descriptive, non-independent trials. Review refreshes after3 new completed
confirmations and feeds compact analyst context. The background service was
gracefully reloaded at13:43 so this is active, not merely a saved plan. Prefer
local compute for bulk tests; reserve AI for strategy/tactics and traced errors.

Economy-preserving Ryth pilot: six eligible maps,144 release games; both draft
arms swap in all36cases and retain Marcella. Draft-only first common horizon
(up to600rounds): mean camp gems+9.11, gold-306.17, deaths-2.22, fuel events-6,
submissions+35.58, Ryth monster damage10,069. Combined-role gains are smaller
for early farming. Losing a twin body also loses passive gold; preserved
Marcella does not imply preserved team gold. Small direct result8/12 is only
a smoke result. Role-only has no Ryth in this pilot and identical early metrics;
later outcome changes cannot be credited to role activation. Native summaries
do not contain ability-use events; an initial guessed zero count was removed,
then the report regenerated from cached games with actual monster damage and
explicitly unknown cast activation. No new games were needed for that correction.

The34-map/six-opponent original/draft/repaired-role/both comparison started
13:45 (1,632 release cells), with actual roster/body-count strata and optional
preselected60-map confirmation. Frozen original x1/v111 and other checkouts
remain preserved. No official uploads, publications or activations.

6 November14:09 update: economy-preserving draft factorial34maps,1,632 release
cells: draft -0.588pp/36of68direct; repaired role -0.882pp/34of68; both -1.765pp/
33of68. New roster actually activates in156cells: all-opponent win delta0,
mean camp collection-23.17 and gold-155.59. On84 already-Ryth cells the role
loses4.76pp despite increased production. Six failed replays per arm decoded.
Classification Parked after original/admission/economy dependency attempts;
retain conditional findings, not Rejected. No-Ryth late effects remain indirect
execution effects, not evidence of role activation.

Major-objective reproduction: original/admission/selective crew/both on4maps,
96 release games,zero faults. Reference deltas -18.75/-6.25/-12.5pp, direct
4/8,5/8,4/8. Small reproduction only. Admission inherits the old sixfold value
bonus, not just feasibility. First500-round analysis does not support a uniform
early gold-collapse story: boss-battle admission gains162.5camp gems/1,148.5gold
and reduces camp deaths2.33; contest both gains615.8gold early but still fails
large captures later. An enemy-penalty hypothesis is inactive because effective
UB_ENEMY_CAMP=1.0. Do not tune it from comments. A focused second repair uses
cached tag1 for original dominant objectives,tag2 for newly admitted objectives;
only tag1 inherits6x value. Admission-only and admission+crew repairs compiled,
games deferred during training. Relevant failed releases are being decoded.

Win-objective repair launched14:02; preflight passed14:03. New reward is terminal
team outcome plus bounded telescoping team-score potential; gamma1/lambda.995,
equal action weighting. Potential and privileged critic features use the prior
native round (current native timeline values include later same-round events).
Fresh critic avoids carrying the old resource-utility target into a new objective.
Actor/roster/temperature/native anchoring/Q11 prep/learning rate/league/map mixture
remain unchanged. These reward/trace/critic changes form one corrected objective
system, not isolated strength attribution.

Five substantive objective tests and four native-probability/framing tests pass.
Preflight49,546decisions maxlogp error0.00001216. Initial untrained release is
byte-identical v111 and full selection repeats54.861%/24of48direct. First main
256-game batch validates693,879decisions,maxerror0.00001264;136seconds. Return/
outcome correlation+.59 is diagnostic, not strength; fresh critic EV-0.007.

Frozen plan32x256=8,192games, selection every8iterations on24maps. Final60maps
are exact-SHA-disjoint from660training maps and24selection maps; nine opponent
styles,normal fuel. Main uses8local workers and GPU. Source snapshots and all
plans are in training/runs/team-win. Do not modify its six frozen lab sources
during the run. Existing original x1/v111 and earlier run artifacts stay intact.
Supervisor session44749/PID13848 is running; no official platform deployment.

6 November14:42: team-win16/32 rounds complete (4,096games). Round8 raw51.04%
and20/48direct, round16 raw52.43% and21/48direct; penalized selection38.54%
and46.18%. Neither replaces initial54.861%/24of48. Planned run continues.
First256rollouts under both reward profiles have byte-identical native summaries
and matching map/opponent/side schedule, confirming unchanged starting execution.
All completed native logp checks pass. Relevant matrix clipping is1/17,968 in
both original and teamwin8; this rules out new widespread clipping, not all
quantization effects. No mutation of the frozen training sources.

A low-priority input-list logger was compiled with exact release-Wasm parity,
but its debug match diverged from the unchanged debug control. Saved failed
parity receipt and quarantined the trace.2,172 comparisons showed1unrepresented
heuristic target and0unrepresented overrides, so no supporting local evidence
for a far-target guard. Parked, not a release explanation. No such guard added.

Queued release-only target-policy search (session28033/PID16256). New zero
calibration is exact v111 Wasm. It will wait for the current actual owner,
defer on substantial success, and refuse ambiguous/failed/stopped predecessor
states.16generations,12antithetic directions,48target-only parameters. Every
fitness game is the actual compiled normal-fuel release; no debug sampling or
float-gradient surrogate.12training maps/generation,6styles, both sides, balanced
direct/reference fitness. Mean updates use a population direction and one
half-step repair; no best-mutation promotion. Evaluate only means every4rounds
on24selection maps. Separate60maps/nine styles for final.8game/2compileworkers,
no AI calls, full immutable plans/model/runtime/source receipts.21autonomy tests
pass. The compute guard allows only its owning process while deferring others.

6 November15:25: team-win32 completed8,192games. Native probability preflight
and every batch passed, frozen sources unchanged. None of four learned
selection checkpoints beat the initial penalty score54.8611%, so best.pt
remained initial and exported exact original v111 Wasm. Final60maps/9styles,
2,160audited release games:0gain,60/120direct,zero faults. Do not report this
as a learned candidate's independent equal-strength result. The selection
retained baseline. No additional identical PPO continuation; Retry required,
with release-only optimization queued to address deployed dynamics directly.

Heart mechanic investigation: four engine3same-round hit measurements at
health fractions.91,.64,.28,.10 match30*(1+.5missingHP), error<.000025.
KITFIX25 disables existing passive bit4.96release-cell original/sim/formula/
both reproduction showed no reference gain;12failed replays decoded.
Scope audit found my_dps(nullptr) shared by combat and farming priorities.
Focused repair moves own factor to three handle_enemies estimates, preserves
entire original my_dps, checks exact expected source.48newmatched releases:
formula0ppreference/6of8direct;both+6.25ppreference/6of8direct;zero faults.
Seven remaining failed replays decoded. Small pilot, no accepted upgrade.

End-turn logger is debug-control faithful but differs from release trajectory;
its high incomplete-search fraction is quarantined diagnostic evidence.
Do not infer actual released decision counts from it. Local isolated repair
qualification now precedes the long ES search:24dev/60generated/44published
replication, six dev/nine confirmation styles, both sides, frozen one selection.
No official upload or activation. Waiting ES process stopped only after exact
identity/wait/no-child checks; supervisor resumes unchanged search afterward
unless a substantial replicated result needs audit.

18:38UTC ranged result/analysis update:96paired local release games complete,
rule alone/+one-cast+6.25pp4/8direct;Heart combinations+12.5pp6/8direct,
zero faults. Every arm23/24whole-native controls unchanged and wins only the
same additional compass/rush case;14failed-map replays decoded. Sparse pilot
signal, NOT broad strength. Retry required; new24dev/60newsynthetic/44published
qualification queued after prior jobs, no existing final changed. Both new
60-map sets independently audited; each10native initialization controls pass.

Current public SDK catalog26abilities verifies cooldown8/stun1/shield5; no
patch warranted there. Analyzer now gets authenticated CLI/SDK-matched designs
rather than trusting old comments. Context57,317/60,000chars;34tests pass, no AI
call. C1cost/admission constraint identified for further measurement:3–4units
requires87.8kremaining, only12.2kearlier work at100k. No reserve/cost change and
no claim about actual released skip frequency. Main16generations finished;
separate60-map/nine-style native final underway on frozen g12 incumbent.

18:58UTC native-search final AUDITED:2160exact cells/60separate maps/nine styles,
+2.1875pp [+.2083,+4.2708]pp90%CI,63/120direct,zero faults BOTHteams. Exact
current engine build and frozen map/Wasm hashes verified; six failed maps fully
decoded. Retry required, no substantial upgrade. Smaller-scale repair20796 now
runs automatically;combat andranged frozen qualifications wait. Analysispacket
58,300/60,000chars includes actual bot/NN/tactical compiler settings and all26
public designs with SDK enum labels;34tests pass,zero new AIcalls. All original
sources and queued source pins preserved. No official bot actions.
