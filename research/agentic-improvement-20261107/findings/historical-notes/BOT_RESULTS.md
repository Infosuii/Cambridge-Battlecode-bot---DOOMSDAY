# Bot results — 6 November 2026

**No demonstrated stronger replacement for v111 yet.** Keep frozen v111 as the
reference. All new artifacts are local experiments, with no official upload or
activation. Original x1, other checkouts and archived checkpoints are unchanged.

## Replay-led investigation, 6 November12:10

The collector/deep-review loop is running again. At12:08 it had341 decoded games.
The11:59 score audit independently reconciled255 own games with zero accounting
failures: camp collection was the largest grouped shortfall in78/128 losses,
combat transfers33 and final held gems17. These are descriptive, not causal.

Native replay inspection and12 logged local reproductions found a real hidden
camp approach/reveal conflict. Cassi could step outside attack range on a terrain
detour, then the firing-ring approach pulled her back. Three focused variants
tested a wider reveal envelope, a bounded16-turn commitment and Cassi-only scope.
In a frozen Road of Riches vs p65pack release reproduction, commitment reduced
backtracking374->19 and increased Cassi camp gems51->122; all three versions lost.
The commitment's60-map confirmation was **-1.0pp**, map-cluster90%[-2.5,+0.67]pp,
**58/120 direct**, zero faults. **Conditionally useful**, not a general upgrade.
Six actual local loss replays, including changed wins, were decoded for retries.

All added diagnostic logging matched untouched debug in12/12 games. Debug and
release results matched only7/12, so mechanism logs are not strength evidence.
Competitive reports use frozen releases at normal fuel. Full data and source:
autonomy/data/experiments/replay-led-cassi-reveal-scope-20261106/ and
autonomy/data/mistake-review/repair-probes/.

Teammate review: exact Max gx source was -3.33pp/22of48direct on24 published maps;
John's exact pinned nnfinal artifact +2.5pp/23of48direct. Ishan's isolated bush
cache and guarded/large-component repairs did not establish a strength gain and
initially increased fuel exhaustion. Retained as references; none promoted.
Teammate replay-decoding/accounting methods were adapted and integrated instead.

The next analyst now receives real replay incidents, independent score accounting
and failed-local-game packets, including confirmation failures. Context is bounded
without additional model calls for collection/decoding. Thirteen evidence/action
tests pass. Original deployment prohibition remains enforced; existing-bot
unranked sampling stays within the previously authorised quota.

| Candidate | Separate confirmation | Direct against v111 | Outcome |
| --- | --- | --- | --- |
| Diverse-league checkpoint8 | +0.94pp, 320 paired cells; cluster90% [-5.63,+7.19]pp | 31/64 | Parked after focused calibration/displacement repairs |
| Lean combat-reset repair | +0.63pp, 320 paired cells; cluster90% [-1.56,+2.81]pp | 33/64 | Retry required; correctness mechanism observed, strength unproven |

Both confirmations use32 generated maps, six opponents and both sides under
normal engine3 fuel, CLI5/SDK5. All candidate fault counts are zero. Test map
bytes are excluded from this run's training/development sets; earlier teammate
exposure is unknown. Opponent versions are frozen own-family snapshots, so these
results do not establish ladder ELO or strength against the full public field.

## Reproducible artifacts

- `release/combat-reset/bot-source.zip` and `bot.wasm`: exactly the tested lean
  repair. Only bot.cpp/common.h change; v111 actor and draft remain unchanged.
- `release/diverse-league/`: frozen trained checkpoint8 source/Wasm; explicitly
  not a proven upgrade. Training:1,536 games/604,317 decisions/seven conditions.
- Every source ZIP file is compared with frozen source, and every Wasm checksum
  is checked against its benchmark manifest. Validation JSON and manifests sit
  next to the artifacts. Packaging scripts never upload or activate anything.
- Full summaries/replays/schedules/build receipts: `autonomy/data/benchmarks/`.
  Development records: `autonomy/data/experiments/`; training: `training/runs/`.

## Investigations and retries

The trained actor's large development gain (97/144 versus84/144) failed the
separate-map test. Several nnm4 win-to-loss flips increased champion deaths
without fuel increases. Tested original/new weights with a doubled override
margin and a half-displacement actor. None reliably improved the broad panel.

The reset experiment tests base/guard/refresh/both before two focused query-cost
repairs. Three diagnostic replay bundles expose34 stale cooldown values and25
dead-target cases. The eager queries were moved off ordinary attacks and out of
paths with no usable reset. The lean version still lacks a competitive margin.

Earlier route1 results were opponent/map dependent. An additional published-map
test was negative; route1 is **Conditionally useful**, not a universal release.
The independently refreshed teammate branch95b0952 also records a failed disjoint
route confirmation. Do not revive the old pooled win count as release evidence.

The next worthwhile work needs a new mechanism or richer state/reward evidence;
repeatedly selecting another checkpoint on these exposed cells is not confirmation.
No experiment is classified Rejected merely because its first benchmark failed.

6 November13:24: the faithful native-probability run completed4,096 games and
selected iteration12. Frozen44-map/nine-style release validation: +0.71pp pooled
(704 paired reference cells),90% map-cluster interval[-3.98,+5.54]pp,43/88 direct,
zero faults. Three styles excluded from training/selection give0pp pooled;
rush regresses6.82pp. Retry required; no substantial general upgrade.

Independent capture audit checks all1,584 exact scheduled games, explicit
complete native captures and integer fault counts, frozen Wasm/map hashes and
one engine3build. Actual general/rush regression replays are decoded. The
two-round retreat repair currently has +6.25pp development and29/48direct;
60-map confirmation is running. Compiled dependent-system and economic-roster
repairs remain unproven until their paired release comparisons finish.

6 November15:56: no substantial general upgrade established.

Team-win32:8,192training games, no learned checkpoint cleared selection.
Retained original v111, exact releaseWasm0896a189. Final60maps/nine styles,
2,160audited games:0pp,60/120direct,zero faults. This is baseline retention,
not an independent equal-strength finding for a learned checkpoint.

Heart passive: engine microtest confirms up to50%missing-health damage at
four wound levels. Fixed an unintended shared-helper interaction before wider
testing. Combat-only formula on60separate generated maps/nine styles:
+2.5ppreference,90%map-cluster interval[0,+5.208]pp,62/120direct,zero faults;
nnm4-3.333pp. All2,160scheduled captures independently audited. Retry required;
no promotion. Simulator+formula failed broader development. Four-map6/8direct
pilot must not be quoted as the broad result.

Major objectives: removing inherited6xpriority from newly admitted major groups
restores earlier captures on some maps. Four-map admission0pp/5of8direct;
admission+crew+6.25pp/4of8. Retry required. Crew/NN deadline interactions need
correct context. Immediate postcapture reward-loss fix unsupported by measured
20round follow-up in repaired large-collection events.

Actual optional budget guard is Parked:22/24native-identical on original,
no fuel reduction; combination24/24identical to Heart-only. NNavoidance is
Parked after universal-mask, reason-specific static-failure repair and documented
topology reproduction; all failed-game panels decoded, no competitive gain.
Neither was rejected solely from its first gate or merged into originals.

Release-only target-weight search is live,16generations planned. Generation2
mean improves its matched training fitness.554167->.570833, but no independent
selection yet (every4generations); incumbent remains v111. Training fitness is
not a strength result. All normal-fuel release games, no additional AI calls,
no official upload/activation. Current state: training/runs/release-es/state.json.

17:08: release search8/16. First24-map check+1.25pp/24of48direct;
second+0.417pp/20of48direct,zero faults. Neither selects a new incumbent.
Six failed maps decoded for each. Training gains and accepted ties have not
established independent strength. A frozen smaller-perturbation repair is queued
behind this run; it retains separate60-map/nine-style final and44-map replication.
The current search was recovered from exact state7after an unintended shared-stop
collision during controller reload; completed artifacts and frozen sources intact.
Controller stop/reload is now isolated and verified while the search stayed live.

## 6Nov2026 combat contracts and local qualification (18:17UTC)

Current engine verifies one spell/turn, even if both cooldowns initially0.
Original simulator violated this with damage/shield followed by dash/reset.
Isolated fix preserves a legal basic-reset-basic sequence. Real support_casts
also precedes C1 after cached cooldowns: current root model hadCD0 when engine
CD8/can_castfalse. Partial-root repair preserves spent spell budget now and
recovers future owner turns.48paired cells each: simple cast fix0pp/4of8direct,
Heart+cast+6.25pp/6of8;root repair-6.25pp/4of8,Heart+root+6.25pp/6of8.14failed
maps decoded,0faults. Retry required; four repairs frozen for queued24-map/
6-style selection,60new synthetic/nine-style confirmation and44published
replication. Strict schedule/hash/current-build and both-team zero-fault gates.

New60-map synthetic set uses official engine builder with frozen seed611611607,
five families12each. Independent actual tile/camp/path recount passes60/60;
10native initialization fixtures pass0fault/fuel. Exact hashes disjoint from
660current training and24/44selection/replication maps. It is a new stress
family distribution, not claimed ladder-frequency sampling. V1geometry-only
preflight preserved; no candidate scored on it. FinalV2manifest79a9730e.

Heart damaging dash125.4/radius1/stun1 verified against SDK and same-round
health. First dash/cast/fullkit factorial and repaired shield-priority/root
factorial did not establish competitive value.23failed maps decoded. Parked,
not Rejected; retain mechanic/dependency findings without arbitrary tuning.

Ranged rule engine proof: movement-exclusive Tavi spell176 plus basic45 works
in either same-round order,221damage total/0faults. Original ranged simulation
forbids basic after such a spell. Isolated correction/model controls underway;
no bot-strength claim yet. All32autonomy tests pass; analysis configuration
now includes actual neural bank gateBEH0, ruling out that inactive hypothesis.

Native search14/16,6strict training improvements but latest selection only
+1.667pp/25of48direct/0faults. No substantial repeatable upgrade yet. Scale
repair and combat qualification queued without changing current search.
No official submissions/publication/activation.

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
