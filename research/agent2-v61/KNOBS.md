# Lab knobs (bot k64, `v4/bots/k64`)

Every tunable value a black-box search can move, by slot of `lab::knobs` (`src/lab.h`, `kKnobs = 160`).
The host (`agent2/lab/host.js`) writes a knob vector into an A2_LAB build before the game; a shipped build bakes one
in with `A2_KNOBS` (`src/common.h`). **Every knob is a no-op at 0**: a multiplier is `x *= exp(s k)`, a threshold moves by
an additive step of a sensible size. Slots 0-44 are read every turn or at their use; slots 64-142 are read once per
game by `kx_init` (`src/bot.cpp`) into the `kx` namespace (`src/common.h`) and cost a few multiplications a turn.

Champion groups (slots 64-84, 113-118): 0 Vendetta, 1 Vesper Vale, 2 Marcella, 3 Varg, 4 Heart of Ruin, 5 Ren,
6 other (Cassi, Issac, Ryth, Tavi, Prism, Stellar, Willow). Our draft (340 real games) picks Vendetta 99%, Vesper 73%,
Marcella 69%, Varg 68%, Heart of Ruin 37%, Ren 27%, C&I 17%, Ryth 16%, Tavi 9%, Prism 3%, Stellar/Willow never.

## Rotation blocks (`agent2/lab/knob_rot.js`, `ES_BLOCK`)

| block | slots | contents | start |
|---|---|---|---|
| A | 0-23 | base settings, targeting, melee/ranged aggression | `knobs_m62_g9.txt` |
| B | 24-44 | fight search, banking, economy, misc | `knobs_m62_g9.txt` |
| F | 64-88 | fights by champion group | 0 |
| C | 89-112 | camps | 0 |
| K | 113-128 | banking | 0 |
| S | 129-142 | shopping and wards | 0 |

## Slots 0-47 (before k64; v57-m62 lab builds)

| slot | meaning | formula (k = knob) |
|---|---|---|
| 0 | fight aggression (`tune::kAggression`) | × exp(0.3k) |
| 1 | go-home health share (`kRetreatHp`) | + 0.1k, clamp 0.05-0.95 |
| 2 | danger time-to-die (`kDangerTtd`) | × exp(0.3k) |
| 3 | danger health share (`kDangerHp`) | + 0.05k, clamp 0-0.9 |
| 4 | bag before banking (`kTributeCarry`) | × exp(0.3k), min 8 |
| 5 | hunt range (`kHuntRange`) | + 3k tiles |
| 6 | hunt health share (`kHuntHp`) | + 0.1k, clamp 0.1-1 |
| 7 | chase range (`kChaseRange`) | + 2k tiles |
| 8 | gold weight (`kGoldWeight`) | × exp(0.4k) |
| 9 | respawn wait weight (`kWaitWeight`) | × exp(0.4k) |
| 10 | health pool a solo camp fight may use (`kNeedPool`) | × exp(0.3k) |
| 11 | cohesion (`kCohesion`) | + 0.05k, min 0 |
| 12 | shop gold (`kShopGold`) | + 30k, min 30 |
| 13 | hunt gem cap (`kHuntGems`) | + 5k |
| 14 | camp staging timeout (`kStageTimeout`) | + 3k rounds, min 1 |
| 15 | hunting on/off (`kHunt`) | k > 1 on, k < -1 off |
| 16 | target worth of carried gems | + gems / 30 × (exp(0.5k) - 1) |
| 17 | target worth of enemy damage | × exp(0.3k × dps / 100) |
| 18 | target worth of wounds | × (1 + 0.5k × missing health share) |
| 19 | target worth of a stunned enemy | × exp(0.4k) |
| 20 | extra walk to a target | time-to-kill + 0.5k per tile past range |
| 21 | target worth of Cassi / Issac | × exp(0.3k) |
| 22 | melee aggression | × exp(0.3k) |
| 23 | ranged aggression | × exp(0.3k) |
| 24 | fight search: value of a life | × exp(0.3k) |
| 25 | fight search: value of health | × exp(0.3k) |
| 26 | fight search: threat at the horizon | × exp(0.3k) |
| 27 | fight search: value of carried gems | × exp(0.3k) |
| 28 | fight search: enemy flee health | + 0.1k, clamp 0.02-0.9 |
| 29 | fight search: ally flee health | + 0.1k, clamp 0.02-0.9 |
| 30 | fight / run decide margin (gems) | + k, min 0 |
| 31 | fight search horizon (rounds) | + round(k), min 1 |
| 32 | caster micro risk | × exp(0.3k) |
| 33 | Marcella bag | × exp(0.3k) |
| 34 | Prism bag | × exp(0.3k) |
| 35 | Vesper counts as poorer (camp rewards go to her) | items - 3k |
| 36 | tribute any bag within this distance (`kTributeNearDist`) | + 2k |
| 37 | end-game banking score (`kEndBank`) | + 150k |
| 38 | cohesion distance | + 2k |
| 39 | ward-ahead spacing | + 2k |
| 40 | middle-camp value | × exp(0.3k) |
| 41 | team-fight engage (strength ratio) | k > 0: engage at 3 / (1 + k); off at k ≤ 0 |
| 42 | altar prelock | k > 0: on, once the enemy banked 600 - 300k |
| 43 | early aggression (round < 250) | × exp(0.3k) |
| 44 | early hunt range (round < 250) | + 3k |
| 45-47 | unused | - |
| 48-63 | reserved: opening schedule (other session, `v4/bots/p63*`) | - |

## Slots 64-142 (k64 expansion)

### Block F: fights by champion group (64-88)

| slot | meaning | formula |
|---|---|---|
| 64-70 | aggression of group 0-6 (`kAggression`, each turn after the brain profile) | × exp(0.3k) |
| 71-77 | danger time-to-die of group 0-6 (`kDangerTtd`: flee when we would die sooner) | × exp(0.3k) |
| 78-84 | fight-verdict bias of group 0-6 (`tactical_decide`: fight value before the margin test) | + k gems |
| 85 | threat retreat: go home below this health share while enemies are near (`kThreatRetreat` 0.4) | + 0.05k |
| 86 | carrier risk: the fight margin multiplier for bags of 25+ (1.4) and 60+ (2.0) | 1 + (r - 1) × exp(0.3k) |
| 87 | outnumbered rule: radius in which enemies are counted (8) | + 2k, clamp 3-14 |
| 88 | target worth of an enemy channelling a tribute (+2) or recalling (+0.5) | × exp(0.3k) |

### Block C: camps (89-112)

| slot | meaning | formula |
|---|---|---|
| 89 | distance (approach steps) in a job's cost | × exp(0.3k) |
| 90 | value of harmless groups (gem / gold clusters) | × exp(0.3k) |
| 91 | value of groups with elks | × exp(0.3k) |
| 92 | value of groups with wolves | × exp(0.3k) |
| 93 | value of groups with a golem or monolith | × exp(0.3k) |
| 94 | value of a finished group waiting for its capture | × exp(0.3k) |
| 95 | value of groups of 40+ gems | × exp(0.3k) |
| 96 | value of groups an enemy was seen at in the last 15 rounds (contested) | × exp(0.3k) |
| 97 | value of groups on the enemy side (their spawn > 4 steps nearer) | × exp(0.3k) |
| 98 | value of groups on our side (our spawn > 4 steps nearer) | × exp(0.3k) |
| 99 | stickiness to the current target (1.52) | × exp(0.3k) |
| 100 | score of a job that still needs helpers (`UB_JOB_INIT` 0.7) | × exp(0.3k) |
| 101 | score of a siege from range (0.8) | × exp(0.3k) |
| 102 | crew size: health each helper adds to a camp fight (0.7 max health) | × exp(0.3k) |
| 103 | value of a solo job a lower slot claimed (0.15) | × exp(0.3k) |
| 104 | camp net: weight of the bot's own score (`A2_CN_SHARP` 4) | × exp(0.3k) |
| 105 | camp net: bonus for the bot's own pick (`A2_CN_BASE` 1) | + 0.5k |
| 106 | big-job multiplier (`NOVA_BIGJOB_MULT` 6) | × exp(0.3k) |
| 107 | duo: buddy's camp counts within this distance (`NOVA_DUO_DIST` 14) | + 2k |
| 108 | staging wait when teammates answered (`V54_STAGE_HELPED` 20 rounds) | + 3k, min 1 |
| 109 | camp-fight back-off: leave below incoming × 3 + 10% health | × exp(0.3k) on the 3 |
| 110 | fixed overhead per job (4 turns, with the capture time) | + 2k, min -3 |
| 111 | early gold weight multiplier (`UB_GOLD_MULT` 4 before round 250) | × exp(0.3k) |
| 112 | after a camp back-off, head home below this health share (0.45) | + 0.05k |

Value multipliers 90-98 also scale the pruning bound (`best_case`), so a boosted group is never pruned unseen.

### Block K: banking (113-128)

| slot | meaning | formula |
|---|---|---|
| 113-118 | bag before banking of Vendetta, Vesper, Varg, Heart of Ruin, Ren, other (Marcella and Prism: slots 33-34) | × exp(0.3k) |
| 119 | bag before round 200 | × exp(0.3k) |
| 120 | bag from round 600 | × exp(0.3k) |
| 121 | bag while our banked lead is 100+ | × exp(0.3k) |
| 122 | bag while 100+ behind | × exp(0.3k) |
| 123 | threatened bank: bag that banks with an enemy within 6 (20) | × exp(0.3k) |
| 124 | threatened bank: altar distance (8) | + 2k |
| 125 | safe banking route: age of the enemy sightings it avoids (10 rounds) | + 3k, min 1 |
| 126 | rhythm banking (`APEX_BANK_RATIO`, off): bank 20+ when distance × r ≤ bag | k > 0: r = 4 / k; off at k ≤ 0 |
| 127 | bank while the target respawns: slack over the altar trip (2) | + 3k |
| 128 | end-game banking distance (20) | + 5k |

### Block S: shopping and wards (129-142)

| slot | meaning | formula |
|---|---|---|
| 129 | shop gold before round 250 (`kShopGold`) | + 30k, min 30 |
| 130 | shop gold from round 600 | + 30k, min 30 |
| 131 | walk home instead of recalling within this distance (`kShopWalkDist` 7) | + 2k |
| 132 | shop while the target respawns: gold needed (90) | × exp(0.3k) |
| 133 | shop while the target respawns: slack over the home trip (4) | + 3k |
| 134 | teleport crystal: turns a hop must save (`V54_TP_GAIN` 8) | + 3k, min 1 |
| 135 | gold needed to buy an altar lock (10) | max(10, 10 exp(0.7k)) |
| 136 | leave the spawn at this health share (1.0) | min(1, 1 - 0.05k) |
| 137 | finish-before-shopping deferral (`V58_FINISH_RESET`, 10 rounds) | + 5k, min 0 |
| 138 | recall only with no enemy within 6 (sightings within 5) | + 2k |
| 139 | recall to travel (`APEX_RECALL_TRAVEL`, off): target this much nearer home than us | k > 0: max(1, 24 - 8k) + 5 steps; off at k ≤ 0 |
| 140 | ward-ahead placement: weight of closeness to the target group (4 per tile) | × exp(0.3k) |
| 141 | wards at captures, tributes and sieges (`APEX_WARDS`, off) | k > 0: on, spacing 10 + 3k |
| 142 | pre-emptive bush ward: sightings within 8 tiles | + 2k |

## Parity

With slots 64-159 at 0, k64 plays exactly as m62_c1 (`agent2/EXPERIMENTS.md` E63: 0 of 100 paired games differ,
mirror margin 0): multipliers are exactly 1, offsets exactly 0, and the reordered float expressions are exact for these
values. A wiring sweep (each knob +1, 20 games) changed games for 71 of 79 knobs; the rest act only in rare situations
(88, 106, 116, 117, 123, 137, 140).

## Tools

- `agent2/lab/knob_rot.js`: evolution-strategies search of one block (`ES_BLOCK=64-88`), other knobs fixed.
- `agent2/lab/knob_val.js`: paired validation of knob vectors on the same games (`VAL_ENTRIES`, `VAL_SETS`);
  `VAL_SWEEP=a-b:v` moves one knob at a time (wiring check).
- `agent2/lab/rot_all.js`: the whole rotation (search, held-out check, keep or revert per block) with a 2 GB free-RAM
  watchdog; resumable. `agent2/lab/rot_pick.js`: averaging / merging / deciding by hand.
