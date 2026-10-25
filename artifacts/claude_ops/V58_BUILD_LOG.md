# v58 coordinated economy research

User brief: build from frozen v57 (platform56), reproduce a repeated coordinated farming loop, and submit only if
every strict v58 gate passes. No match groups will be queued. No holdout or fresh-map tuning. Baseline remains frozen.
The pre-existing untracked Claude experiment was preserved at artifacts/tmp/v58-claude-experiment, then v57 copied
to bots/v58 and the copied build cache removed after checking the absolute paths. No running bench was found.

## Protocol

Screen on 28 development maps, both sides, seeds1-4; confirm supported mechanisms on12seeds. Every run needs a zero
exit, exact coverage, both teams zero native faults, and measured fuel-outs/game. Use hierarchical Bayes and the
map-cluster bootstrap. Incomplete-loop non-inferiority: posterior mean >=-25, P(>-50)>=0.9. Retention: posterior
mean>=25, P(>0)>=0.95, plus its mechanism evidence. Release: mean>=50, P(>0)>=0.95, positive bootstrap lower bound,
>=53% wins over672games, both once-only holdouts >=50% wins and nonnegative margin, fuel<=2/game, clean independent
build identical to benchmark seed1 and exact source-only bundle. Proxy if an actual Claudus economy signature is reached.

## 0. Baseline and architecture contract

All V58 switches begin0. Confirm switch-off executable equals v57 before adding logic. Read the required findings,
audit, ladder analysis, fresh-map history, v57 changes, handoff and engine rules. Do not repeat forced draft, naive
global funnel, static draft plan or opening-only pack variants already rejected.

Implementation concern: champions have independent persistent Bot instances; a C++ static is not shared team memory.
Also all64shared bits are already allocated:42claims plus22sighting/event bits. The director must use an explicit
compatible protocol or locally cached plans with deterministic anchors; it cannot assume another champion's static
cache is visible or overwrite sightings silently. Check this before implementing the repeated loop.

Mechanism targets: team capture gold byR250>=900, elk-size captures>=3.5, carry share>=40%, carry Treasure<=R120,
deaths -30%, fuel<=2/game. Current-draft director tests cannot establish the Vesper-specific target until the coupled
draft/build exists. Every shortfall will be reported; local lineage wins do not prove beating Claudus.

## D1: shared repeated jobs + bounded routing, current draft

224games,seeds1-4:98wins,-38.8gems; bootstrap[-116.5,+60.4]; Bayesian mean-40.2,P(>0)=0.256. Does not meet incomplete-loop
non-inferiority (mean<-25). Both teams0native faults; fuel1.728versus1.612/game. Mechanism: team capture goldR250
616.6versus707.9 (target900missed); elk captures2.58versus2.78; hitters3.06versus2.76; first elk captureR62versusR76;
carry share37.3%versus26.4%; Treasure byR12030.4%versus18.8%; split captures4.73%versus1.34%; capture delay10.01versus8.94.
Deaths15.72versus15.78. The first-clear improvement does not produce the repeated income loop. Not accepted.

The funnel tool had placeholder stats for gold clusters, monoliths and golems. Corrected against SDK facts/rules;
all new candidate/control metrics use the corrected tool. Added an optionalR250 cutoff; default full-life behaviour
is preserved. Historical reports are unchanged. Raw analysis/extracted replays are kept under artifacts/local-only/v58.

## D2: lifecycle and observation repair

Preserve active captures across assignment changes; persist satellite jobs until completion; cache empty replans;
respect staging avoid timers; evaluate the crew using visible current stats, with conservative hidden-ally estimates;
use the existing selected-group readiness model instead of demanding every assigned helper before any attack.
Record the public physical roster after each draft pick, so hidden-ally fallback types cannot make different role lists.
The draft API only submits prefixes and its public buffer is a startup snapshot: preserve the current host prefix
with sdk_read_draft_memory before adding8roster bytes at1008. The first D2 build used a nonexistent offset-write API
and a translation-unit-local alias; it exited1 with0games and is invalid evidence. Corrected D2b gets a clean
preflight build before its224-game screen. No strategy result is attributed to the failed build.

D2b:103/224,-31.3; Bayesian-25.8,P(>0)=0.349: incomplete-loop mean misses-25. TeamR250gold678.8vs729.3,
elk captures3.06vs2.83, first elkR56vs79, carry share39.7%vs25.5%. Split captures worsened15.0%vs1.1%.
Fuel1.679vs1.580/game,0native faults both teams. Better first clears still do not produce the required loop.

## D3: full coupled draft and shopping

Meta draft only on maps with a reachable own-side2.4k-6.5kHP gold group; other maps retain ML drafting. Carry
reserves the first Treasure's shard budget before consumables, completes a damaged clear before a gold-only trip,
and uses a short home trip when it can finish Treasure. Public roster metadata is preserved correctly.
90/224,-58.8; Bayesian-95.1,P(>0)=0.054. Fuel2.500vs1.518/game,0faults. R250gold695.0vs752.8, elk3.00vs2.88,
carry share44.3%vs26.1%, Treasure byR12035.3%vs14.7%, split captures12.3%vs2.2%. Fails income, strength, fuel;
not accepted, despite reaching the carry-share target. No extra seeds were used to rescue this result.

## D4: physical handoff

Changing a clearer target can leave it on the previous reward region while it attacks the next group in range.
Explicitly step off the region when the carry is present.86/224,-42.9; Bayesian-70.6,P(>0)=0.154. R250gold721.2vs750.3,
carry share46.6%vs25.7%, splits10.2%vs2.5%; Treasure byR12037.1%vs17.0%; fuel2.268vs1.768/game.0faults. Still fails.

## D5: price team-rounds and release capable satellites

The first objective used elapsed clear/travel time without charging all assigned champions. Correct the objective
to crew*(travel+wait+clear)+one capture, compare2/3crews after the opening, encode that choice in the spare claim's
high bit (group index uses6bits; restrict director and supported draft to<=48groups). Satellites may solo a nearby
elk when the existing readiness model says they can.99/224,-4.0; Bayesian-22.0,P(>0)=0.375,P(>-50)=0.670: still
fails non-inferiority despite its point estimate. Gold722.9vs721.8, elk3.05vs2.79, carry42.9%vs26.7%, split8.2%vs1.7%,
Treasure byR12034.4%vs17.0%, fuel2.036vs1.411/game.0faults. No income target, proxy or accepted mechanism yet.

## D6–D14: full-loop revisions and action, survival, vision and lock screens

D6 elected one capture owner, including while the carry approaches, and preserved the carry's pending reward across
job broadcasts. Its raw margin was effectively zero, but its Bayesian mean was −22.1 and P(>−50)=0.662, below0.9.
It is not retained. R250 income735.7 versus707.3; elk-size captures2.99 versus2.72; carry share44.5% versus26.5%;
split captures3.65% versus1.37%. First elk median48 versus69; clear median32 versus39. Early first captures already
match Claudus's approximate median50; comparing our mean67 to their median50 would misdiagnose this. The missing
income is repeated throughput, not simply the opening. Deaths15.04 versus15.53; fuel2.094 versus1.415/game.

Carry timing needs two views. Across every D6 map the censored Treasure median was141, but among the160 games
with Vesper it was114.5;52.5% had Treasure by120. Vesper capture-gold share averaged45.5%. D13 Vesper median110,
share45.8%;55.6% by120. Thus the coupled carry can hit its timing and ownership targets without hitting total income.
Do not force the carry draft onto structurally unsupported maps merely to improve this conditional metric.

D7 tried early capture positioning while helpers could finish within3 rounds. It lost26.8 gems and had2.205
fuel-outs/game. Review found its destination check removed the current occupied tile before checking whether the
carry was already adjacent, allowing needless shuffling. The inactive source corrects that ordering and isolates
this experiment behind V58_PRECAP=0. That correction is not claimed as a measured gain.

A1 tried stationary camp/enemy casts before movement; D8 coupled it to D6. Both failed. A1's casts increased only
10.562→10.770 per100 alive rounds while basic attacks fell24.420→23.938. Ryth5.84 remains below8; Tavi10.36 was
already above9 in the baseline. A2 instead preserved a post-walk attack reset; D9 coupled it to D6. A3 preserved a
legal remaining basic attack after dash-only approach; D11 coupled it to D6. No version met acceptance. The existing
controller already uses many legal resets: these are narrow ordering opportunities, not evidence all attacks were
missing. The original A1 snapshot used ACT=1 for both stationary paths; later ACT bits1/2 split camp/enemy,4 is the
post-walk reset and8 the post-dash basic. Reconstruct exact snapshots rather than assuming historical bit semantics.

S1 tested visible local power and risk-sensitive banking; D10 coupled it to D6. S1 lost200.6 and D10 lost270.2 gems.
S1 reduced deaths12.69 versus13.38 (5.2%, short of30%) and40-gem bag deaths0.866 versus1.045, while attacks fell
21.51 versus23.79 per100 alive rounds. Avoiding a few deaths did not repay the lost pressure/income. The inactive
source also uses the existing flee-mode prefix for distress propagation; the measured S1 used the earlier prefix.
That diagnostic correction is not an accepted survival improvement. No blind threshold search followed.

D12 added a nearby parallel second clearing pair using its existing target claim, leaving the unused sixth claim
for the primary director job. It lost31.5 gems and consumed3.031 fuel-outs/game. A separate four-game MICLOG sample
measured157 director replans, max22,497 fuel,13 above15,000. D13 hoisted repeated crew masks, power sums and claim
occupancy out of the candidate loop. Its separate four-game diagnostic sample had157 replans, max13,367, none over
15,000. These logging builds alter trajectories and are excluded from strength evidence. Normal D13 improved to
−4.7 raw gems but still used2.487 fuel-outs/game and missed income. Cheap planning alone did not fix the loop.

V1 refreshed personal wards near objectives and banking routes. SDK3.0.5 permits one active personal ward, not two
simultaneous wards per champion. Placements increased142.01 versus84.34/game, but deaths rose16.79 versus14.68,
and margin was−63.4. Placement count does not establish useful coverage or a winning vision layer. Rejected.
L1 timed already-owned locks against visible enemy banking threats. Placements2.527 versus0.464/game; enemy
completed tribute latency3.833 rounds versus our3.844, enemy completion92.65% versus90.17%. Raw margin+4.4,
Bayes+6.6,P=.548; no measured benefit. Timing excludes pre-start waits and does not establish causal lock delay.

D14 directly tested a conflict with v57's main gain: the new director banned middle camps beforeR150. Mode3 removes
that ban and charges enemy-side distance instead. Final screen107/224,+5.3 raw gems; Bayes+12.1,P=.564;
map-cluster95%[−136.7,+163.5], P(>−50)=.775. Fuel1.790/game,0native faults both teams. R250gold677.7 versus722.9,
elk2.99 versus2.75, carry share44.7% versus25.9%, splits4.90% versus2.05%; first-capture median43. Vesper-only
Treasure median134,45.6% by120; overall censored median147. Deaths13.80 versus14.33 (3.7% fewer). Neither the
strength nor repeated-income target passed. Middle access changes outcomes but does not rescue this architecture.

## Decision and limits

Stop this round under the user's strict gate: **not submitted**. Twenty complete four-seed screens produced4480
games, plus eight diagnostic games excluded from strength and one invalid build. No complete screen passes
acceptance, clustered positive gain, or incomplete-loop non-inferiority. There is no accepted mechanism. All new
switches remain0. A clean copy of the final disabled source builds byte-identically to frozen v57; its release
manifest's per-file hashes still match. This is a research-equivalence check, not an active candidate release gate.
No12-seed confirmation, original holdout, fresh15-map pass, release bundle, upload or match group was performed.
No~1000-gold/40%-carry configuration was reached, so no Claudus proxy was created. Denial and carry hunting remain
unimplemented, per the instruction to try them after a working loop. Sprint3 notes were explicitly ignored at the
user's direction; SDK/CLI3.0.5 and engine1.0.3 were retained.

The evidence supports a remaining throughput/pressure problem: concentrating rewards and completing Treasure
can work while team income and map pressure fail. A second clearing pair did not solve it in these tests. The
best result is still uncertain, with large between-map variation. The results do not prove a path to rank25 or
beating Claudus. The user decides the next architecture after this failed gate.

Analysis is offline and omniscient only. Capture gold is inferred from snapshots; simultaneous kills/purchases can
obscure individual captures. Funnel hitters count basic attackers, missing spell-only contributors. Treasure not
completed by500 is censored at501; absent milestones are not dropped. Carry means Vesper if drafted, otherwise
the lowest actor-id slot. Vesper-only reports avoid conflating supported carry maps with fallback drafts. First-clear
and Treasure comparisons label medians explicitly. Whole-life death/fault/fuel counts come from native summaries;
large-bag losses and action density use the audited replay counters. None of these limitations changes the failed
strength gate. Development maps have extensive prior exposure;20 screens are not independent confirmation.

## Commands, identities and per-variant results

Every normal run used bench3 with the absolute snapshot, frozen v57 and a new absolute output prefix, seeds1–4.
All normal run exits were0; D2 exited1 with0games. No benchmark wrapper or frozen baseline was edited.
For each row below, the snapshot is artifacts/tmp/v58-<label>, and the output is artifacts/evaluations/v58-<label>.
The exact source hash, each file's hash/line endings, v57-relative patch, four built candidate hashes and four frozen
opponent hashes are in V58_EXPERIMENTS.json / V58_RESULTS.json. All21 snapshot patches, including invalid D2,
were reconstructed into new directories and verified file-for-file by tools/reproduce_v58.py.

`python tools/check_bench_run.py <prefix> --seeds 1,2,3,4 --json <validation.json>` checks exact coverage and native
faults on both teams. `bench_bayes.py` and `bench_compare.py` provide the saved hierarchical and clustered outputs;
no naive standard error was used to retain a mechanism. Incremental comparisons below use both prefixes.

Mechanism commands: `python tools/replay/v58_bench_mechanisms.py <prefix> <report.json>` for D1,D2b,D3–D6,D13,D14;
`v58_action_report.py` for A1,A2,A3,S1,V1; `v58_lock_report.py` for L1; `v58_director_profile.py` for diagnostic D12/D13.
Other combined variants failed their strength/fuel screen before an additional full replay mechanism audit; no
unmeasured target is claimed as passed. Raw replays and extracted intermediates remain local-only.

* **d1**: Repeated primary jobs and bounded capture routing; original draft.
* **d2b**: Capture lifecycle, visible crew readiness and public roster.
* **d3**: Coupled carry draft and Treasure shopping.
* **d4**: Physically release the carry capture region.
* **d5**: Price team-rounds and release capable satellites.
* **d6**: Elect one reward owner and preserve carry delivery.
* **d7**: Preposition ranged carry before the clear finishes.
* **a1**: Stationary camp and enemy damaging casts before movement.
* **d8**: D6 plus stationary casts.
* **a2**: Post-walk attack reset.
* **d9**: D6 plus post-walk attack reset.
* **s1**: Visible-power disengagement and risk-sensitive banking.
* **d10**: D6 plus disengagement and banking.
* **a3**: Use legal remaining basic attack after a dash.
* **d11**: D6 plus legal post-dash basic attack.
* **d12**: Parallel nearby second clearing pair.
* **v1**: Objective and banking-route personal wards.
* **l1**: Time existing altar-lock consumables against visible threats.
* **d13**: Hoist repeated crew and claim calculations out of candidate loop.
* **d14**: Allow middle camps with an enemy-side travel cost.


28 development maps Ã— both sides Ã— seeds1â€“4 =224 games per screen;20 screens =4480 games.
Every completed screen has exact coverage and zero native faults on both teams. D2 failed to build and is excluded.
Eight diagnostic games are excluded. All results use SDK3.0.5 / engine1.0.3; Sprint3 changes were not applied.

| Variant | Wins/224 | Raw gems | Bayes mean | P(>0) | Map-cluster95% | Fuel/game |
|---|---:|---:|---:|---:|---|---:|
| d1 | 98 | -38.8 | -40.2 | 0.256 | [-116.5, +60.4] | 1.728 |
| d2b | 103 | -31.3 | -25.8 | 0.349 | [-135.4, +69.9] | 1.679 |
| d3 | 90 | -58.8 | -95.1 | 0.054 | [-152.8, +41.7] | 2.500 |
| d4 | 86 | -42.9 | -70.6 | 0.154 | [-160.2, +94.7] | 2.268 |
| d5 | 99 | -4.0 | -22.0 | 0.375 | [-111.7, +119.1] | 2.036 |
| d6 | 100 | +0.0 | -22.1 | 0.383 | [-115.2, +131.2] | 2.094 |
| d7 | 93 | -26.8 | -63.0 | 0.178 | [-132.2, +101.1] | 2.205 |
| a1 | 106 | -32.7 | -42.4 | 0.203 | [-104.9, +35.1] | 2.290 |
| d8 | 89 | -95.6 | -113.0 | 0.041 | [-192.9, +15.9] | 2.304 |
| a2 | 111 | +7.2 | +9.7 | 0.569 | [-39.0, +49.8] | 1.942 |
| d9 | 96 | -46.7 | -61.5 | 0.185 | [-161.8, +79.1] | 2.478 |
| s1 | 79 | -200.6 | -250.7 | 0.000 | [-302.2, -104.2] | 1.906 |
| d10 | 59 | -270.2 | -315.1 | 0.000 | [-378.7, -157.0] | 1.897 |
| a3 | 113 | -6.4 | -7.9 | 0.443 | [-21.9, +6.3] | 1.741 |
| d11 | 101 | -6.7 | -27.2 | 0.352 | [-120.6, +125.3] | 2.094 |
| d12 | 97 | -31.5 | -53.6 | 0.209 | [-140.5, +90.3] | 3.031 |
| v1 | 93 | -63.4 | -88.3 | 0.049 | [-133.2, +7.4] | 1.741 |
| l1 | 113 | +4.4 | +6.6 | 0.548 | [-55.6, +52.2] | 1.781 |
| d13 | 100 | -4.7 | -13.5 | 0.429 | [-119.8, +132.8] | 2.487 |
| d14 | 107 | +5.3 | +12.1 | 0.564 | [-136.7, +163.5] | 1.790 |

No screen reaches mechanism acceptance (Bayes meanâ‰¥25, P(>0)â‰¥.95); none has a positive clustered lower bound.
No screen passes incomplete-loop non-inferiority. No12-seed confirmation or once-only holdout was justified.

## Incremental comparisons

These compare each revision with the prototype it modifies, using paired map/side/seed observations.

| Change vs base | Raw gain | Bayes mean | P(>0) | Map-cluster95% |
|---|---:|---:|---:|---|
| d2b vs d1 | +7.5 | -5.9 | 0.464 | [-102.4, +107.3] |
| d3 vs d2b | -27.6 | -30.0 | 0.326 | [-161.3, +111.0] |
| d4 vs d3 | +15.9 | -3.9 | 0.469 | [-100.8, +135.9] |
| d5 vs d4 | +38.9 | +30.8 | 0.721 | [-74.1, +159.2] |
| d6 vs d5 | +4.1 | +7.4 | 0.573 | [-69.7, +89.9] |
| d7 vs d6 | -26.9 | -13.8 | 0.328 | [-99.3, +37.9] |
| d8 vs d6 | -95.6 | -106.1 | 0.029 | [-189.5, -9.3] |
| d9 vs d6 | -46.8 | -40.5 | 0.161 | [-142.6, +48.9] |
| d10 vs d6 | -270.2 | -235.1 | 0.000 | [-370.2, -178.5] |
| d11 vs d6 | -6.7 | -0.4 | 0.415 | [-17.2, +0.0] |
| d12 vs d6 | -31.6 | -23.4 | 0.182 | [-88.5, +25.8] |
| d13 vs d12 | +26.9 | +0.9 | 0.565 | [-2.3, +61.1] |
| d14 vs d13 | +10.0 | +31.3 | 0.755 | [-91.8, +112.1] |

An incremental improvement inside a losing loop does not make the complete loop acceptable.

## Reproduction

Use `python tools/reproduce_v58.py <variant> <new repo-local directory>`; it verifies every source-file hash.
Then run `bash artifacts/claude_ops/bench3.sh "$PWD/<directory>" "$PWD/bots/v57" "$PWD/artifacts/evaluations/<new-prefix>" 1 2 3 4`.
Use the same pinned SDK/engine. Every normal run returned0; `check_bench_run.py` verifies exact224-game coverage and both fault counts.
Run `bench_bayes.py <prefix> --json <out>` and `bench_compare.py <prefix> [base-prefix] --json <out>`.
Use the optional replay-report tools listed in V58_BUILD_LOG.md for mechanism audits. Raw replays remain local-only.
