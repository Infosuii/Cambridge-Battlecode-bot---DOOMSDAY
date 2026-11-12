This improvement round starts from v306AltarPressureReach. Its frozen source
digest is `7f3dadb1d3876137ddd4606f340eb64f1fed67c9e4d6a70defa93c2c59a75d3e`.
All development is local and uses one agent. The finals target is unseen
random maps with 3–5 picks per team.

The previous 480-condition random comparison added 59 deaths relative to
v272. Cassi and Issac accounted for 14 additional camp deaths each. Fresh
replay inspection found a Varg submitting 296 gems at (31,31) while taking
camp damage every round. From rounds 1549–1559 he remained in submission,
with no visible enemy champion, as health fell from 24% to 1.5%. He died at
round 1560 with the full bag. The channel guard counted enemy champions and
ignored camps. The input and frames are in `round3-windows/`.

Two additional source paths warranted investigation. Camp disengagement
could take one step and return to the same job the following turn. Also,
the bank walk could compute a route around enemy sightings, then discard
that avoidance and its altar targets during the generic movement retry.

The development panel uses 20 maps selected by a fixed generator-cycle
rule plus three failed-game incident maps. It has 138 paired conditions
against x1, John and Max on both sides. All comparisons verify map bytes,
match seed, full roster, engine 3.0.0, opponent binaries, release build and
default fuel.

| Arm | Wins / 138 | All deaths | Camp deaths | Late champion drops | Late large-camp gems |
|---|---:|---:|---:|---:|---:|
| v306 base | 107 | 738 | 247 | 3,898 | 39,845 |
| v307 committed camp exit | 103 | 787 | 252 | 3,006 | 37,868 |
| v308 preserve bank route safety | 105 | 751 | 268 | 3,304 | 37,356 |
| v309 exit and bank route | 103 | 779 | 249 | 2,529 | 35,803 |
| v310 camp-aware channels | 106 | 686 | 218 | 3,501 | 39,369 |
| v311 combined | 108 | 733 | 242 | 2,406 | 35,639 |

Every completed screen had zero bot faults and matching drafts. v309's
12-game trace recorded 249 exit steps and 23 safe detours. v311's trace
recorded 252 exit steps and 17 safe detours.

The first exit arm stays on a route until outside actual awake camp ranges,
with a six-round limit and released job claim. It could also withdraw from
a valid one-step tank rotation and skip useful work. **Retry required.**
The first bank arm preserves both the enemy avoidance mask and valid altar
targets when rerouting around live units. A temporary blockage can send
that dynamic route to a much farther altar. Its gem-loss benefit and
farming cost make it **Retry required**.

v310 adds actual awake camp damage to both recall and submission guards.
It checks a fresh channel before starting and removes dangerous camp
positions from the altar goals when the predicted channel would be
lethal. Shared duration logic preserves the existing Home-emblem recall
rule. In the two-sided Varg incident comparison, it won both games to
v306's one. Earlier decisions also changed, so this result does not
establish that the original 296-gem deposit was replayed and saved.
The broad solo arm reduced all deaths by 52 and camp deaths by 29, with
one fewer win. **Conditionally useful.**

The full first combination recovered the score to 108–107 and cut late
champion drops by 38%, with a 10.6% decline in large late camp gems.
Its outcome supports testing the dependencies together. **Retry required.**

The focused exit repair, v312, preserves the original one-step rotation.
It retains the committed route for deeper exits and releases it when a
healthy closer ally has already completed its turn and can hold camp
focus. Its claim and temporary job avoidance are applied only after an
actual committed exit begins. v313 bounds the bank detour to two extra
walking steps around a temporary obstruction. v314 combines these repairs
with the camp-aware channel guard.

The 60-map confirmation seed is 261110321. It was generated before any
candidate measurements, with 12 maps in each resource/terrain family and
20 maps for each team size. Its manifest SHA-256 is
`46966e0778f53b21017c402b1597a8b18a06d4f020202872b1eb3bd73765a1c9`.
The candidate is frozen before that confirmation. Selection requires
positive paired random-map score, zero faults, stable draft, acceptable
fuel and a demonstrated targeted improvement. Family and opponent
results, published regression evidence and movement/objective checks
remain part of the decision.


The v314 frozen confirmation underperformed: 355 versus 363 wins in 480
paired conditions, with 2,101 versus 2,017 deaths and 560 versus 462 camp
deaths. Its published regression was 249 versus 276 wins in 420 conditions.
The movement preservation passed (home median 428; Islands reversals 972
versus 1,573, stalls 1,455 versus 2,259), but that does not qualify a weaker
competitive build. **Retry required** for the interaction; no release.

Execution-order diagnosis found camp-safe routing evaluated before deciding
whether a bank trip was due, changing farming while no channel was intended.
v315 restricts that work to champions already at an altar. It scored 108
versus 107 on the 138-condition development set, 271 versus 276 on 420
published conditions. Published camp deaths fell 443 to 439, large late
camp gems 97,333 to 96,516. **Conditionally useful**, not a qualified default.

v316 further limited committed withdrawal to a lone long-range camp with
an affordable walking exit; it scored 105/138 and 248/420. The helper still
incurred work before rejecting ordinary short-range jobs. v317 moves this
rejection to the caller and restricts safe detours to unsafe camp channels
or unhealthy loaded carriers. It scored 104/138 and 265/420, all zero faults.
Its published late champion gem losses fell 42,802 to 39,884 but large camp
gems fell to 92,565. The broad committed-exit system is **Parked** after three
mechanism-driven repairs; targeted channel survival remains **Retry required**.
No source or results were discarded.

A second, independent teamwork defect was found in current source. The
P19_TRIP cleanup is not defined anywhere in the compiled source or build
configuration. Banking and healing champions therefore retain their camp
claims. Claim-count and on-site help calculations can count an absent ally.
v318 enables the existing mode-based cleanup and records TRIP_RELEASE in
debug builds; v319 combines it with v315 to test the dependency. Original
claims, idle code 127 and decode/write operations were checked. These are
new isolated builds, with source digests in round3-trip-inputs.json.

To separate the essential fatal-channel guard from trip planning, v320
retains the camp-aware channel checks but restores v306 tribute routing
and timing byte-for-byte. v321 combines that core fix with trip-claim release.
This is a dependency test motivated by the observed early planning changes,
not a search over arbitrary tuning values.

The second untouched 60-map confirmation set uses seed 261110323 and
manifest SHA-256 ac51d08d572772aa553c81908a47829c59435f8352e4e677212d3c831d44d458.
It is not a tuning set. Freeze the selected source before using it.


Trip cleanup verification: debug replays emitted 703 release events across
12 incident conditions (267 tribute, 429 home, 7 tribute-win), confirming
activation and the intended input modes. The first v318 arm scored 98
versus 107; with v315 safety, v319 scored 99. Deaths and late dropped gems
improved substantially but large-camp farming and early spending declined.
Source investigation found that cleanup erased target_group as well as
the shared claim. This bypassed crew_can_finish after short bank/heal trips
and discarded the existing target preference. **Retry required**.

Focused repair v322 releases the shared claim but retains local camp
intent. Its 138-condition result recovered to 108 versus 107: deaths 672
versus 738, camp deaths 217 versus 247, late champion drop 3,069 versus
3,898, r150 spending 51,500 versus 51,380, large late camp gems 38,807 versus
39,845. v325 combines this repair with the core channel guard.

The isolated v320 channel fix scores 108 versus 107 on development and
278 versus 276 on 420 published conditions. Early earned gold matches
baseline exactly in both panels, showing that restoring original tribute
routing removed the unrelated opening change. Published deaths fall
4,415 to 4,398, late champion drops 42,802 to 42,129, with large-camp gems
97,333 to 97,093. All zero faults and identical drafts. The 12-game debug
trace records 34 blocked unsafe starts and 14 channel cancellations, with
no blocked-start runs longer than two turns. These establish activation,
not a claim that each cancellation saved a life. **Conditionally useful**
until independent random-map qualification.

v323 changes only equal-score quiet travel ties, preferring the last
successful movement direction. It requires a consecutive turn and current
position equal to the previous destination; it cannot override shorter
routes, original central-path scoring, blocked tiles, or visible combat.
v324 combines this with v320. Original v306 and all failed sources remain
unchanged. Source identities are frozen before measurement.


Broader evidence for v322 and v325 did not generalise to published maps:
259 and 258 versus v306's 276 wins /420. Keeping local intent repaired the
first development failure, but fully clearing the shared claim still
changes crew continuity. A third focused repair, v329/v330, retains the
shared job and clears only its immediate on-site mark on a trip. These
score 106/107 versus 107 on development, and 269/273 versus 276 published.
Full claim release is **Parked**, not a qualified default. On-site cleanup
is **Conditionally useful** in source semantics, with no demonstrated
competitive improvement yet. v331 additionally removes channeling allies
from the physical count; it scores 106/138 and 242/420. **Retry required**.

The general heading preference v323/v324 scored 98/138 and 238/420, versus
107 and 276. The first projected replay position difference in a failed
open-economy condition occurs at round 8, actor 3: from (14,1) to (15,2)
versus (15,1). This confirms early route changes but does not by itself
prove a causal command or strategic loss mechanism; the replay projection
omits some actions and values. The focused v328 repair limits heading
preference to consecutive bank/home fields, preserving farming route ties.
It improves the first arm to 103/138 and 254/420, but increases published
deaths (4,562 versus 4,415) and late champion drops (50,239 versus 42,802).
The purely geometric tie preference is **Parked** after the combined and
trip-only comparisons; no competitive case justifies adding it now.

The initial readiness arms v326/v327 scored 104/101 development and
236/256 published. Source inspection found repeated state API queries in
a helper also used during job scoring. The world already obtains info.state
for each ally. v334 caches that field and consumes it without extra API
reads; v335 is a cache-only control, and v336 combines cached readiness with
the core channel guard. Activation and semantic versus fuel effects remain
under investigation. Fake-recall interference was considered, but default
FB_FLAGS is 10 (flag 4 off); it is not an established cause here.

v332/v333 attack an already-awake, visible, in-range camp during an otherwise
idle spawn-healing turn. The champion stays at spawn. The initial compile
caught that SDK attack returns void; this was repaired before any games and
both source identities are preserved in round3-spawn-inputs.json. Outcomes
remain pending. **Retry required** until measured.

The isolated v320 source was frozen before the second untouched 60-map
confirmation. It tied v306 359-359 /480, with zero faults and equal drafts.
Camp deaths fell 402 to 395, late champion drops 8,112 to 7,900, late large
camp gems fell 103,477 to 103,140. The 120 direct games against the exact
v306 binary tied 60-60. Its published score is +2 wins /420. The fresh
positive-win gate did not pass, so this is **Conditionally useful** as a
correctness repair, not an accepted stronger replacement. No package.

A subsequent unplayed 120-map pool adds random altar count and positions.
It has 24 maps per terrain/reward family, 40 per roster size, native integrity,
load and connectivity checks. Seed 261110341; final manifest SHA-256
 a85cc75e40b3502d311bbde0b88569f6353e0c0eaed202c565b47e815c502274.
Acceptance uses geometry only. The generator and all previous map sets are
retained. This broadens synthetic stress coverage without claiming a model
of the actual finals distribution.

A new source investigation found that ranged camp approach returns after
movement/basic/reset checks and omits a legal post-arrival camp spell.
v337 adds the compatible spell attempt and verifies the target after a kill
before preserving any follow-up attack. v338 tests that action with the
core camp-channel guard. Both are frozen before measurement in
round3-arrival-inputs.json. **Retry required** pending activation and results.

Latest user steering overrides the earlier time estimate: keep improving
until explicitly told to stop and package. Do not package a candidate now.
No official ladder actions are authorized or performed. No subagents.


Final timed selection: sources frozen at 2026-11-10T23:54:20.267155+00:00. No new bot code after benchmark request. v347 and v348 each won 93 versus 92 /120 on 20 unseen variable-altar maps, and 22-18 directly versus v306 /40. Both lost the fixed published subset 65 versus 68 /90. The guard-only and spawn variants tied fresh and direct games. All final matches had zero faults and matched seeds, maps, engine and drafts. v306 therefore remains the recommended release under the preregistered gates. The lethal-cast strategy is Conditionally useful on this small random panel, Retry required before a universal replacement; no Rejected classification from the failed gate alone. The user deadline prevented further repair/tuning. Source and compiled artifacts for experimental v348 are retained separately from the recommended v306. No official ladder actions.


The user requested an approximately 15-minute frozen benchmark and frequent
updates. The run executed 6,660 new local matches: 240 unseen variable-altar
maps x four references x both sides x three builds (5,760), 240 direct games
per candidate versus v306 (480), and the full 420-condition published pool
for v348. The fixed v306 and v320 published cohorts were reused with native
seed/map/engine/full-roster identity checks. All models remained byte-identical
before and after the run; all new matches had zero bot and opponent faults.

Random wins /1,920: v306 1,398; v320 1,395; v348 1,374. Direct scores:
v320 120-120, v348 124-116. Published wins /420: v306 276; v320 278;
v348 270. Correct map-cluster 97.5% intervals for paired random gain are
v320 -0.156 pp [-0.417, +0.104], v348 -1.250 pp [-2.708, +0.208].
The small direct v348 advantage is also inconclusive (95% interval versus
50% from -2.917 to +6.250 pp). No candidate demonstrated a reliable gain.
The recommendation remains the already-delivered v306; no bot was submitted.

An aggregation defect in the initial confidence summary used the last
candidate as the baseline in its lookup. Raw game totals and native identity
checks were unaffected. It was corrected to filter v306 rows before lookup,
then checked against exact score differences, 1,920 clean pairs, reference
split totals, and unchanged frozen binaries. The before-code and report
correction receipt are preserved alongside the corrected report. No games
were rerun or selected based on their outcomes during this correction.

v348 had 17 more camp deaths (1,481 versus 1,464), 473 more late champion
gems dropped (41,926 versus 41,453), and 3,494 fewer large late camp gems
(378,445 versus 381,939), despite 17 fewer total deaths. These are aggregated
associations, not a replay-proven mechanism. Its strategy remains Retry
required; failure of this gate is not a Rejected classification. The core
channel guard remains Conditionally useful as a correctness repair without
an established competitive score gain. No further bot development was part
of this benchmark-only request. Full evidence: long15-261110355-report.json
and long15-261110355-REPORT.md; frozen inputs and loss/gain replay paths are
retained for any later targeted repairs.


Medium uploaded-bot benchmark (11 November): unmodified ZIP SHA-256 7d9b610b0fd4e0fc40a6a50734c6a0670508d3b62ac6c2a14b32617c199079e0 imported as upload_7d9b610b, source/build label p98 verified in match logs. Frozen v306 and v348 played 100 fresh variable-altar maps and 30 published maps from both sides, 520 games total. v306 scored 104-96 random and 45-15 published; v348 103-97 and 44-16. Zero bot or opponent faults, all source/binary identities unchanged, matching seeds/maps/engine/full rosters verified across our builds. Fresh-map score intervals include 50%, so this comparison does not establish a reliable random-map advantage or justify replacing v306. This was benchmark-only; no code tuning, official ladder action or strategy rejection. Full identities, metrics and confidence ranges are in mediumzip-7d9b610b-261111401-report.json.
