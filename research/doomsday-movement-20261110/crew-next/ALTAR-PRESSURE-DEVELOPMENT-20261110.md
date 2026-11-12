# Second DOOMSDAY improvement pass

The user requested more effective 2v1 and 3v1 attacks, confident deposits near
enemies, protection for a followed carrier and a separate porting plan. The
finals pool is fully random. This pass uses a single agent and local matches.
The base is the last qualified v272DoomsdayFusion package, source digest
`e6713d28aa7c32904cacf9071057cab9849f2540e9a96a21f41bbf98656a915f`.
The separate plan is `BUILD-PLAN-ALTAR-PRESSURE-20261110.md`.

## Mechanisms

The old coordinated strike required three nearby allies in addition to the
actor and a target below 40% health. v296 lets one healthy teammate already in
range support a shot, or two teammates each one legal step from distinct
firing positions. A two-step projection is excluded from the new damage
estimate. The actor still passes the health and ready-burst checks, takes at
most one closing step, and preserves the old fog, camp, spawn and flank
exclusions.

v297 extracts the existing local altar and hostile-lock handling into
`submit_here`. Its short in-place window checks the real deposit duration
against basic attack arrival, ability range, cooldown and movement exclusions.
It gives an eligible submission priority before combat. The same initial
arm uses that forecast for active channels and retries. Recall retains the
original policy. New helper code does not depend on map names or IDs.

v298 lets a low-bag healthy champion take an in-range shot and available
targeted stun against a sole enemy approaching an allied carrier near the
altar. A carrier must be visibly submitting or have at least 30 gems. The
helper checks its own exposure, avoids camp fire and hostile spawn, and
does not chase.

## First paired factorial

Each arm used matching map bytes, side, seed, engine 3.0.0, opponent binary,
default fuel and draft. There were zero faults and no draft changes.

| Arm | Existing random set wins / 80 | New mixed-roster wins / 40 |
|---|---:|---:|
| v272 base | 49 | 27 |
| v296 supported strike | 49 | 29 |
| v297 altar windows and channel forecast | 53 | 30 |
| v298 escort | 58 | 32 |
| v299 strike and altar | 53 | 31 |
| v300 all three | 54 | 31 |

The new 10-map development seed is 261110303. It has five terrain and reward
families and 3, 4 and 5 picks per team. Its manifest SHA-256 is
`5a1737a0f0dce7f00218311ece85e26e8bfc295b9cd8377462291bb194910773`.
This is a synthetic stress distribution. It does not establish the finals
map frequency.

v296's 40-game action trace recorded ten additional supported strikes.
v300's 40-game mixed-roster trace recorded four strikes, three peels and
51 new short deposit starts. Forty-nine deposited the starting bag in the
expected completion window. The remaining two require replay inspection.
Trace and release results differ, so debug wins do not enter the score gate.

## Interaction investigation

The all-three arm lost four net cached-random wins relative to escort alone
and added champion deaths. Early replay comparisons found a first changed
projection on a 35-gem carrier in one escort win and on an 11-gem champion
with no loaded ally in another. These are outside the direct escort trigger
on the changed turn. The projection omits some command details and does not
rule out an earlier indirect effect. No fuel suspension occurred within
three rounds of those first differences. Their cause remains uncertain.

v301 and v302 separate strike plus escort from altar plus escort. v303
separates safe deposit starts from the replacement active-channel guard.
v304 moves the escort check inside actual contact after the existing
burst-kill check. It keeps the helper out of the empty-enemy farming path.
v305 combines that placement with supported strikes and short safe starts.
Its prediction helpers remain outside the large decision function.

v306 additionally repairs a specific gap in the old active guard. A visible
foe beyond basic range plus two was ignored, even when its mobility or spell
could reach before completion. The new forecast supplements that missing
reach case. The original near-contact cancellation remains in force.
This tests approaching-pursuer safety separately from replacing every
channel decision.

Detailed panel manifests and source receipts retain the standalone trials.

## Confirmation design

The reserved 60-map seed 261110301 was generated before candidate selection.
Its 3–5-pick version has manifest SHA-256
`549311439b0ec1ab834f1c0da73e396fd1a79ac9f26222f7d0e0ba781f2d70d0`.
There are 12 maps per family and 20 per team size. Geometry and native game
loading were checked without bot outcomes. Primary confirmation plays both
sides against ref_x1, John, Max and ref_hold_rush100. Random-map wins, banked
margin, gem losses, deaths and fuel determine selection. Published maps and
the old objective and movement checks provide regression evidence.

## Focused repairs and selection

| Arm | Existing random wins / 80 | New mixed-roster wins / 40 |
|---|---:|---:|
| v301 strike and original escort placement | 58 | 33 |
| v302 full forecast and original escort placement | 55 | 31 |
| v303 all three with start-only forecast | 54 | untested |
| v304 contact-scoped escort | 50 | 28 |
| v305 contact-scoped escort, strike and safe start | 56 | 29 |
| v306 adds the missing long-reach watch | 56 | 29 |

v303 separated channel starts from ongoing cancellation. Its cached late
champion drops were 2,811 versus v300's 3,057. v304 reduced the irrelevant
escort entry overhead, with less apparent score benefit than the original
placement. v305 restored the three intended mechanisms together and had
2,938 late champion drops versus the base's 3,618. v306 retained those wins
with 2,757 late champion drops and 628 total deaths versus 686 for the base.

The long-reach comparison changed two release games on the cached sample.
On Major Objectives against John B, the first change was at round 245.
The actor carried 57 gems with 660 HP. The incumbent banked at 254; the new
guard delayed the same 57-gem deposit to 287. Team champion drops in that
game fell from 283 to zero later. In the other changed game, champion drops
rose from 93 to 195. This verifies a changed channel decision and mixed
downstream consequences. It does not prove that the earlier cancel itself
rescued a doomed bag.

The final 40 debug conditions recorded three supported shots with one
nearby ally, three peels, 52 safe-start attempts and 49 timely completions.
There were two logged submission cancellations, one followed by banking
within 36 rounds and neither followed by champion-caused loss in 12 rounds.

The frozen v306 source was selected before exposing the 60-map confirmation.
Its freeze receipt is `altar-confirmation-freeze.json`.

## Independent confirmation

| Metric | v272 | v306 |
|---|---:|---:|
| Random-map wins / 480 | 368 | 372 |
| Published wins / 420 | 275 | 276 |
| Random all deaths | 1,861 | 1,920 |
| Random late champion drops | 8,378 | 8,614 |
| Random late large-camp gems | 102,696 | 107,619 |
| Random banked score margin | 89,987 | 91,091 |
| Random fuel suspensions | 918 | 947 |
| Published all deaths | 4,590 | 4,415 |
| Published late champion drops | 48,881 | 42,802 |

Every release comparison had zero faults and matching map bytes, seeds,
rosters and opponents. The fresh paired difference was +0.83 percentage
points with an 80% map-block interval of −0.83 to +2.50. This is a modest,
uncertain win-rate gain. Fresh deaths increased 3.2% and late champion
drops 2.8%. The four opponent score splits were 96–94 against x1, 88–83
against John, 90–92 against Max and 98–99 against rush100.

Homonoliths retained its round-428 median home capture. Islands had 197
trailing quiet pairs versus the original preservation reference's 6,577
and v272's 182. The preservation gate passed, and its 36 matches had zero
faults. The aggressive build has a small movement tradeoff on that check.

**Accepted for local testing — v306AltarPressureReach.** The intended
behavioural changes ran through normal entry points, the random result
was positive, and the existing preservation checks passed. The mortality,
loot-loss and uncertainty figures above remain part of the selection.

The supported-strike and contact-scoped escort components are
**Conditionally useful**. The broad replacement cancellation model is
**Retry required** because of its interactions. The original escort
placement is **Parked** for release selection because its early score
effects were harder to attribute. The separated start-only and full
factorial arms remain **Conditionally useful**.

## Verified delivery

The ZIP contains 44 source files, each byte-identical to the locally
compiled and tested source. Its CRC check passed. The compiled Wasm and
the separate plan accompany it.

- ZIP SHA-256 `cbdd638125acf5826a53f01813601ef92a7d43d289a35f684cfb1f5537995642`.
- Source SHA-256 `7f3dadb1d3876137ddd4606f340eb64f1fed67c9e4d6a70defa93c2c59a75d3e`.
- Release Wasm SHA-256 `9e335df552156d37ff5b3e0befafcbfe98c56d0a63004cab4335b20efefaab32`.

The delivery directory is
`C:\projects\cambridge battlecode\ladder-test-20261110\v306AltarPressureReach`.
The full selection receipt is
`C:\projects\cambridge battlecode\work\doomsday-movement-20261110\crew-next\v306AltarPressureReach-selected-build.json`.
