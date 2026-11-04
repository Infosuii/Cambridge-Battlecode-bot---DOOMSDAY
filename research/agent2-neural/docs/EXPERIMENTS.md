# Agent 2 experiment registry (local; mirrors Infosuii/battlecode-agent-36- #5)

Engine: `cambc 2.2.5`, engineBuildHash `d7e29ae3546357b011419c764204b7b9e2232bdb1b07868250c6b35d4c18d2a5`.
Toolchain: WASI SDK 33, Clang 22.1.0 (bundled with cambc).

## Builds

| Name | Source | Switches | Release wasm SHA-256 |
|---|---|---|---|
| `a2_v34base` | `bots/v34/src` copied verbatim (18/18 files hash-identical; archive `E6A958…FA605`) | as frozen | `ECAFAE4C4571D3A5401D356D03F5C336E6C9D7C5D6DD494AF463646622EAAE55` (identical to `bots/v34` build) |

## E1 — Baseline fuel exhaustion (registered 2026-10-19, before running)

- Hypothesis: v34 loses champion-turns to fuel exhaustion; reproduce the historical 2.5/game (local official) figure on
  the exact frozen build and characterise where.
- Schedule (fixed): `a2_v34base` vs itself on the 17 official maps, both sides (34 games); vs `sb_sparexp_b1` on the
  official maps, both sides (34 games); vs itself on the first 50 `maps_rdev` maps by name, both sides (100 games).
- Metrics: `fuelExhausted` entries per game and per 1,000 champion-turns (each team counted separately), games with at
  least one, rounds of the events, turns at exactly the budget in `team-*.fuel`, bot faults.
- No strength claim. Mirror games count both teams as v34 observations.
- Result: see FINDINGS.md section 2 (2.94 / 2.38 / 3.12 entries per v34 team-game).

## E2–E5 — Stage attribution and fixes (diagnostic builds; results in FINDINGS.md sections 3–5)

## E6 — Fuel package exhaustion (release builds `a2c_fix`, `a2c_gov`; same schedule as E1)

Entries per team-game, official mirror / vs sparexp / rdev mirror: v34 2.94 / 2.38 / 3.12; `a2c_fix` 0.29 / 0.47 / 0.55;
`a2c_gov` 0.41 / 0.41 / 0.06. `a2c_off` (all switches off) wasm = v34 wasm (`ecafae4c…`), byte-identical.

## E7 — Quick screen of the fuel package (registered before running)

- Candidate `a2c_gov` (A2_BUSH_FAST, A2_FAST_AMBUSH, A2_CMICRO_FAST, A2_GOV) vs `a2_v34base`.
- Schedule: all 200 `maps_rdev` maps, both sides (400 games); the 17 official maps, both sides (34 games).
- Primary: win rate and gem difference vs v34. Expected effect small (exhaustion is ~0.04% of champion-turns);
  the package is mainly an enabler for search coverage. Decision rule: keep the package if the screen is not clearly
  worse (win rate >= 47% on 400 unseen games) and the calibrated pool (E8) is not worse; it is not evidence of a gain.
- Result (vs v34; official 34 / unseen 400): fixes 19/34, 52.8% (+10,088 gems); fixes + strict ward gate (first
  `a2c_gov`) 12/34, 50.8%; after splitting: + walk cap 16/34, 53.0%; + lenient ward gate 19/34 (identical games to
  fixes), 53.0%; + both 16/34, 53.0% (+10,988). The strict ward gate (90k required) was replaced by a lenient one
  (worst-case labelling 70k + 6k tail) on mechanism grounds; prompted by this screen, so E8 decides.

## E8 — Calibrated pool for the fuel package (registered before running)

- Seeded builds (NOVA_SEED=k, k=1..8): `sb_a2base_c*` (all A2 switches off = v34 behaviour), `sb_a2fix_c*`
  (A2_BUSH_FAST, A2_FAST_AMBUSH, A2_CMICRO_FAST), `sb_a2gov_c*` (fixes + A2_GOV). Hashes in builds.tsv.
- Pool: farm, calm, v34c, sparexp, aggro, v30base, spartop (existing seeded builds), 17 official maps, both sides,
  seeds 1–8 (1,904 games per candidate). `tools/spar_pool.py`, scored with `tools/spar_compare.py a2base a2fix a2gov`.
- Seeds 1–4 and 5–8 reported separately (5–8 as the fresh check). Primary: weighted-pool paired change; secondary:
  deaths per game overall and vs sparexp; exhaustion entries. Keep rule: not worse than a2base on both halves.

## E9/E10 — Snapshot size, verdict authority, caster-micro tail, exact-result self-check (diagnostic builds)

- 4-unit relevance snapshot: verdict rate 39.3% -> 46.8% (official mirror); scene 6: 1% -> 36%, scene 7: 0 -> 21%.
  5-unit cap: verdicts at scene >= 5 collapse to ~3% (a 5-unit pair needs 78k at entry); rejected on measurement.
- The 4-unit snapshot raised post-search suspensions; cause: caster_micro scanned every camp per hot-zone tile
  (p99 ~33k even with one threat). A per-call camp filter (same camps, same order) cut it to p99 12–13k; suspensions
  with SNAP=4 back to 19 (mirror) / 25 (vs sparexp).
- A2_CHECK self-check (both paths computed in real games): 0 mismatches in ~132k caster-micro danger values,
  ~2.3k counter-ambush distances, ~15k bush-cluster labellings.

## E11 — Screens of the behaviour-changing switches (registered before running)

- All with the fuel package on (A2_BUSH_FAST, A2_FAST_AMBUSH, A2_CMICRO_FAST, A2_GOV), current source:
  `a2c_a2gov2` (package only), `a2c_a2s4` (+A2_SNAP=4), `a2c_a2s4a` (+A2_SNAP=4 +A2_TD_AUTH), `a2c_a2auth`
  (+A2_TD_AUTH), `a2c_a2fh` (+NOVA_FLEE_HIT). Each vs `a2_v34base`: 17 official maps x 2 sides, 200 maps_rdev x 2 sides.
- Screens only rank candidates for the pool (E12); no strength claim from them.

## E12 — Calibrated pool for snapshot, authority and flee-hit (registered before running)

- Seeded builds `sb_<name>_c1..8` (NOVA_SEED=k) of `a2gov2` (fuel package, current source; the ablation base),
  `a2s4`, `a2s4a`, `a2auth`, `a2fh` (each = a2gov2 + one change; a2s4a = + SNAP=4 + TD_AUTH).
- Stage 1: seeds 1–4 for all five (952 games each), scored against `a2gov2` with `pool_halves.py`, and against
  `a2base` for context. Stage 2: fresh seeds 5–8 only for candidates that are not worse than a2gov2 on seeds 1–4 by
  more than 1 SE; the decision uses seeds 5–8 (picks on 1–4 have shrunk 2–4 points on fresh seeds historically).
- Secondary: deaths per game overall and vs sparexp; for SNAP/AUTH the death change is the mechanism check.

### E8 results (vs `a2base` = v34 behaviour; 1,904 paired games each; points ± SE)

| Candidate | Seeds 1–4 | Seeds 5–8 | All | Deaths/game | Deaths vs sparexp |
|---|---|---|---|---|---|
| a2fix | +1.1 ± 1.6 | -2.8 ± 1.6 | -0.9 ± 1.1 | +0.01 | +0.10 |
| a2gov | +1.1 ± 1.9 | -1.4 ± 1.6 | -0.1 ± 1.2 | -0.02 | +0.30 |

Decision: the fuel package is strength-neutral; kept for runtime correctness (exhaustion -80–98%) and as the base for E12.

### E12 results (vs `a2gov2`; 1,904 paired games each)

| Candidate | Seeds 1–4 | Seeds 5–8 (fresh) | All | Deaths/game | Deaths vs sparexp |
|---|---|---|---|---|---|
| a2s4 (+SNAP=4) | +2.7 ± 2.1 | -2.1 ± 2.1 | +0.3 ± 1.5 | +0.01 ± 0.19 | -1.09 ± 0.63 |
| a2s4a (+SNAP=4 +TD_AUTH) | +1.5 ± 2.1 | +0.7 ± 2.1 | +1.1 ± 1.5 | -0.73 ± 0.19 | -2.67 ± 0.62 |
| a2auth (+TD_AUTH) | +0.6 ± 1.5 | -0.8 ± 1.6 | -0.1 ± 1.1 | -0.13 ± 0.10 | -0.36 ± 0.35 |
| a2fh (+FLEE_HIT) | 0.0 ± 1.6 | +2.1 ± 1.6 | +1.1 ± 1.1 | -0.31 ± 0.17 | -1.52 ± 0.66 |

(The first a2s4 seeds 5–8 batch failed silently with no games; it was rerun alone.)
SNAP alone shrank on fresh seeds (usual pattern). SNAP+AUTH cut deaths on both halves; AUTH alone does little,
so the authority rule matters once the snapshot omits units.

## E13 — Combined stack (registered after E12, before running)

`a2combo` = fuel package + A2_SNAP=4 + A2_TD_AUTH + NOVA_FLEE_HIT; pool seeds 1–8; exhaustion schedule; screen vs v34.

| Base | Seeds 1–4 | Seeds 5–8 | All | Deaths/game | Deaths vs sparexp |
|---|---|---|---|---|---|
| vs a2gov2 | +1.7 ± 2.1 | +2.2 ± 2.2 | +1.9 ± 1.5 | -0.83 ± 0.19 | -2.10 ± 0.65 |
| vs a2base (v34) | +2.3 ± 2.3 | +1.0 ± 2.3 | +1.7 ± 1.6 | -0.88 ± 0.19 | -1.67 ± 0.71 |

Exhaustion (entries per team-game, official mirror / vs sparexp / rdev): 0.18 / 0.53 / 0.08 (v34: 2.94 / 2.38 / 3.12).
Screen vs v34: unseen 217/400 (54.2%, gems +13,424); official 17/34 (kills 296–239).
Decision: recommended Agent 2 stack. Deaths -0.85/game (~4.5 SE, both halves); score change positive but not
significant (~1.2 SE). Leave-one-out: SNAP without AUTH is neutral; AUTH without SNAP is neutral; flee-hit adds a
small independent death reduction. Not yet tested: `maps_real` unseen pool, final holdout, ladder.

## E22 — Simulator validated against the real engine; vision added (A2_TS_VIS)

Engine lab (`agent2/lab/fight_lab.js` + `simharness.wasm`, the ts:: code compiled standalone). Fights of 1–3 per side
are teleported into open ground on dev maps with random health; each fighting champion's turn is chosen by the bot's
simulator from the engine's live state, played in the engine (`v0_0_3.wasm`, same engine as cambc 2.2.5), and the
engine's result compared with the simulator's prediction. Spells off (mechanics first).

What matches exactly: movement (0 refused moves in ~10k turns), basic damage = strength, Varg splash, Ren retaliation
(0.2 x focus), Cassi/Issac link, turn order. Small gap: the acting champion regains ~2–3 health at the end of its own
turn (not modelled). Large gap: **vision**. The engine refuses a basic attack on any target outside the attacker's
*own* vision (team vision does not count): 98–100% agreement with the bot's `World::vision_from` model (shadowcast
radius 8; walls and bushes opaque except the viewer's own 8-connected cluster; other clusters' bush tiles never seen).
The simulator assumed every in-range target is hittable: right for 66–75% of its attack choices in these setups.

`A2_TS_VIS` (tsearch.h/.cpp): a unit attacks or casts only on targets it sees — bush tile only from inside its own
cluster; beyond adjacency, no wall and no other cluster's bush on a 2d-sample segment (94–99% agreement with engine
vision); unseen targets are picked only when nothing else is. Off-build is byte-identical to v34 (`ecafae4c…`).

| Simulator (200 fights, 5 maps, ~5k turns) | Step mismatch | Refused attacks | Fight outcome agrees |
|---|---|---|---|
| vision off (v34/combo) | 21.0% | 852 | 174/200 |
| A2_TS_VIS | 4.5% | 30 | 194/200 |

Game results (a2c_vis = combo + A2_TS_VIS, vs a2c_combo): unseen 189/400 (47.2%, gems -12,080, kills 1432–1661);
official 15/34 (kills 202–301). Decision: stopped (clearly not better; ~14% fewer kills). Likely cause: the
approximate rule (94–99%) vetoes attacks the engine allows, including on enemies the snapshot already knows are
visible; a fix would trust live engine visibility at the root positions. A2_TS_VIS stays off.

E22b (a2c_vis2: same, but a pair of units still on their snapshot tiles always sees each other; the rule only judges
moved positions; off-build still `ecafae4c…`): unseen 188/400 (47.0%, gems -11,024, kills 1455–1578); official
12/34 (35.3%, gems -7,304). Same deficit, so the over-veto was not the cause. Stopped; A2_TS_VIS stays off. Reading:
a more faithful simulator does not make the current decision layer (fight/run thresholds, margins, tuned on the old
simulator's optimism) choose better; the thresholds would need refitting on the new model, or the gain is elsewhere.

E23 — verdict refit with A2_TS_VIS on (new knob A2_TS_FIGHT_BIAS added to the fight value; off-build `ecafae4c…`),
each vs a2c_combo on dev maps (SE ~3.5 pts at 200 games):

| Variant | Games | Wins | Gems | Kills |
|---|---|---|---|---|
| bias -4 (lean run) | 400 | 31.8% | -62,990 | 1280–1398 |
| bias -2 | 200 | 50.5% | -2,126 | 817–809 |
| margin 1.0 | 200 | 50.0% | -730 | 858–845 |
| bias +2 | 200 | 47.5% | -3,982 | 839–1043 |
| bias +4 (lean fight) | 200 | 41.0% | -13,684 | 845–1107 |

Decision: stopped. The best refits only tie the combo; vision in the playouts adds nothing the bot can use at
these thresholds. A2_TS_VIS stays off.

## E24 — Offline fight solving with the real engine (agent2/lab/solve_lab.js, solve_report.py)

934 real fight states (turn starts with an enemy within 4) sampled from 64 bench replays; each branched in the engine
(`Timeline_Branch` makes a replay state live) and played 3 rounds with the actor always fighting vs always running,
everyone else on the simulator policy (vision on, spells off); value = lives x 25 + 12 x health fraction (+ gems/10).
Engine prefers a side (|fight - run| > 2) in 12% of states. Where both decide (67), simulator verdict agrees 95.5%;
wrong side in 3/934; regret ~0.01 value per state. A linear correction on (simD, health, counts, distance, ranged) does
not hold out (coefficients flip between halves). Decision: nothing to distil — the fight/run verdict is not where
games are lost. Limits: spells off, 3 rounds, both sides on the simulator's own policy.

## E25 — Training environment: real bots inside the engine module (agent2/lab/host.js, es_host.js)

`host.js` runs cambc bot builds (`bot-injected.wasm`) inside `v0_0_3.wasm`: each SDK import is forwarded to the
engine's API under the instance's perspective (team, champion), buffers copied between memories, `yield` suspends
the instance with JSPI (Node 24). Fixes found on the way: draft/shared memory calls take a team index; the engine's
bitboard metadata leaves `board_bytes`/`field_bytes` zero (filled from the raw-size queries, else heap corruption);
`Cast(slot, unit*, position*, ok*)`, `PlaceWard(position*, ok*)`, `UseConsumable(id, position*, ok*)`.
Fidelity: deterministic; dev map 3 reproduces cambc (1000–808, round 344 vs 343); maps 1–2 differ because fuel is
not metered (no exhaustion, no low-fuel shortcuts). Speed ~0.25 s per full game per core (cambc ~1.5 s).
Lab build `A2_LAB=1` (off in shipped builds; off-build still `ecafae4c…`) makes the NOVA_LEARNER farm-score weights
host-writable (`lab_learner_w` export), so training needs no rebuild per candidate; zero weights reproduce the combo
game exactly.

Runs r1/r2 are void: the trainer started several games at once on one host per worker, and each game leaked ~6 MB
(bots suspended at game end are never freed), so 6 workers ran the PC out of memory (two crashes). Fixed: one game
at a time per worker, each worker recycled after 20 games, at most 4 workers, abort over 3 GB, abort if >5% of a
generation's games error, and a RAM watchdog (`run_guarded.ps1`, kills the run under 2 GB free). r3 peaked ~0.6 GB.

r3 (`es_host_r3.tsv`, 20 generations, 8 antithetic pairs, 12 random maps_rdev maps x 2 sides per evaluation): the
mean's fitness wandered between 33% and 62.5% wins with no trend (noise at 24 games is about ±10 points). Final
weights on held-out maps_dev, 50 maps x 2 sides in the host: 49/100 wins (49.0%), gem margin +8.7 per game.
Decision: stopped; no gain, so no cambc test. Re-weighting the camp score's features does not move results — the
same pattern as the earlier knob tuning (camp choice is not where the gap is).

## E26 — Fight turns against the engine's brute force (agent2/lab/duel_lab.js), value calibration (calib_lab.js)

Duel lab: the host drafts chosen types, plays to round 3, teleports 1v1 or 2v2 fighters into open ground at random
health (spells ready, others far away). The first fighter's turn is the bot's own, or forced through every move x
spell (slot, target, before/after the move, reset) x attack; the real bots then play 6 rounds; value = lives x 25 +
health fraction x 12 (ours minus theirs). Raw "best" is the top of ~50-100 chaotic outcomes, so it is re-scored
with the bot's own turn on 5 fresh variants (health jitter up to 3%, horizon 5-7): selection and scoring use
different outcomes.

| Luck-free (fresh variants) | Scenarios | Within 0.5 of best | Within 1.0 | Mean / median shortfall |
|---|---|---|---|---|
| 1v1 (seed 33) | 49 | 59% | 69% | 1.21 / 0.00 |
| 2v2 (seed 44) | 27 | 22% | 30% | 10.9 / 3.1 |

Raw (unscored-luck) 1v1 on 135 duels: 44% within 0.5; Tavi, Willow, Ren worst. 2v2 raw numbers are mostly luck
(single first-step differences of 55+ value). Real 1v1 misses: most are the bot casting and attacking while behind
on health where stepping out scores better (behind by >0.15: a passive turn best in 6/14; ahead: 3/12).
`A2_DISENGAGE` (lone duel, health fraction below the enemy's by A2_DIS_MARGIN = 0.15, no kill this turn: leave).

Value calibration: at a random round 60-300 one champion is killed / halved / given 20 gems; team gems (banked +
carried) 100 rounds later against the identical untouched game (349 states): death -91 ± 8 with an empty bag (flat
across rounds: 88 / 87 / 97), -177 ± 24 carrying 40+; half a health bar -21 ± 7 (full ≈ 42); +20 carried gems +12 ± 5.
The fight-or-run weights (NOVA_TD_*: life 8 -> 25, health bar 3, gem 0.75, in gems) undervalue lives 4-11x and health
~14x relative to gems; the life:health ratio (91:42) matches the duel lab's 25:12. Variant `a2c_cal`: life 90,
health 40, gem 0.75.

Same 60 duels (seed 33, 49 valid), luck-free: combo 59% within 0.5 (69% within 1.0, mean shortfall 1.21); a2c_dis
55% / 61% / 1.63 (worse even when behind: 2.12 vs 1.32); a2c_cal 67% / 78% / 1.35 (behind: 0.92); a2c_calv (+A2_TS_VIS)
59% / 73% / 1.03; a2c_calx (+action search) 47% / 61% / 2.71.
cambc vs a2c_combo, 200 games on maps_rdev: a2c_dis 79/200 (39.5%, gems -11,700) — the duel lab predicted it;
a2c_cal 103/200 (51.5%).
Final test (user-set) a2c_cal vs a2c_combo: held-out maps_test (105 maps x 2 sides) 101/210 (48.1%, gems -5,032,
kills 305–399); official 17 maps x 2 sides 8/34 (23.5%, gems -9,128, kills 191–316).
Decision: a2c_cal rejected — better isolated fight turns, but valuing lives at ~90 gems makes the bot fight and kill
far less, which loses the contested official maps. a2c_combo stays the best bot. The calibration measured a single
champion's life in isolation; the decision value of fighting also includes map control and denial the duel score and
the 100-round margin do not credit to the fight.

Middle calibration a2c_mid (life 40, health 15, gem 0.75), vs a2c_combo: official 17 maps x 2 sides 16/34 (47.1%,
gems -4,422, kills 194–288); held-out maps_test 105 x 2 sides 106/210 (50.5%, gems +1,564, kills 318–298). Level, not
better. Duel lab (first 18 shared duels): 44% within 0.5, in line with the combo. a2c_combo stays the best bot.
Why the duel-lab fixes do not show in games: close fights are a few percent of rounds; better isolated turns
(59 -> 67%) move results ~1 point, below the ±3.5 noise of 200 games; the duel score (6-round lives/health) is not the
game objective (fewer fights lose map control on the official maps); the bot's levers (thresholds, retreat routine,
weights) are blunter than the one-step answers the brute force finds; learned per-champion rules lacked data.

## E27 — Macro decisions branched in the engine (agent2/lab/macro_lab.js, macro_report.py)

Lab build hooks (`lab.h`, `A2_LAB` only; off-build still `ecafae4c…`): for one champion from a chosen round, at the
first turn the condition holds, (1) bar its current camp target for 20 rounds (calm, farming, health > 50%), (2) bank
a small bag (8-19 gems) now, (3) hold a 20+ bag for 30 rounds; each against its own record-only baseline (the host
is deterministic, so the games are identical up to that turn). Value: team gems (banked + carried) margin 150 rounds
after the intervention. 397 states on maps_rdev:

| Intervention | Margin change | Alt better / worse / same |
|---|---|---|
| Bar the current camp (take the next choice) | -8.6 ± 8.0 | 132 / 156 / 108 |
| Hold a 20+ bag 30 rounds | -1.1 ± 7.8 | 114 / 116 / 120 |
| Bank a small bag now | n = 1 (bags arrive in 24-gem steps; the condition almost never holds) | |

No split (distance to target, bag size, phase) shows a reliable gain; holding late (rounds 300+) -18.6 ± 12.5.
Reading: the bot's first and second camp choices are worth about the same, and bank timing within a 30-round window
does not move the margin — macro choices at this granularity are flat, which is why camp-score and banking tuning
never moved results. The largest measured lever remains deaths (-91 gems each, E26).

## E28 — Where a2c_combo loses against the pool; weights; search without fuel limits

Existing pool games (pb_a2combo, 1,904 on the official maps, 8 seeds): 60.3% (v34 base 57.9%). Weakest opponents
v34c 47.8%, sparexp 55.0%, spartop 55.3% (farm/calm/v30base/aggro 62-68%). Weakest maps lanes 50%, rows 47% (as in
v34). Regressions against v34 on the same pool: stampede 62.5% -> 51.8%, collision 68.8% -> 60.7% (gains: contest
51 -> 64%, packs 52 -> 63%). Per-switch pool runs: the stampede loss comes with the fuel package, the collision loss
(and the contest/packs gains) with A2_SNAP=4.
Stampede, 112 pool games each (8 seeds x 7 opponents x 2 sides): A2_BUSH_FAST alone 53.6% (+145), A2_FAST_AMBUSH
62.5%, A2_CMICRO_FAST 61.6%; BUSH_FAST with one bush behaviour off: hiding off (APEX_BUSH_HIDE=0) 58.9% (+172),
defence off 49.1%, ambush off 48.2%, ward reveal off 46.4%. Reading: same bush labels, but v34's slow labelling ran
out of fuel on stampede and so cut bush hiding short; fast labelling lets hiding run, which costs games there.
Weights: health bar = 0.45 x life (measured ratio) with the life ramp kept (a2c_hpr): 78/150 vs combo on maps_test
(52.0%, gems +1,098) — level.
Engine search per turn is not workable: a live-timeline branch costs ~62 ms and ~450 KB never freed (3,000 branches:
1.3 GB, 186 s). Stand-in: our own search with vision and full action search at 10x fuel (a2c_vx): 32/100 vs combo
(kills 211, deaths 449) — more search exploits the simulator's errors. Bush hiding off on the full pool
(a2nohide, 1,904 games): 61.2% (+143) vs combo 60.3% (+125); stampede 56.2%, sparexp 57.4%, spartop 58.8%.

## E29 — Simulator fidelity benchmark on real fights (fight_data.js, simharness2, bench_sim.js, behave_fit.py)

Data: 60 host games, a2c_combo vs v34c / sparexp / spartop / farm / aggro (fights.jsonl 40,466 turns; fights2.jsonl
with every champion and camps). Each logged turn: the full state of the champions (kits, cooldowns, buffs) and the
actor's real actions. simharness2 = the bot's ts:: code with full kits.
Mechanics (real actions applied in the simulator, 7,573 turns): health and deaths almost exact (44 health and 2 death
mismatches); spell damage = modifier x focus (measured ratio 0.96-1.0); cooldown counts are the same up to the
phase of the decrement; gaps: some casts the model cannot perform (Ren dash, some Cassi casts), Cassi's 20-health cast
cost, Varg splash from camp attacks.
Behaviour: the greedy playout policy predicts the real action class 35% of the time (holds where real bots move:
2,189; move direction right 39%; attack target right 95%). A learned 40-32-7 network on the real turns (type
one-hot included): 48.7% held-out class accuracy (most-common 24%), hit yes/no 80%.
Rollout, 3 rounds ahead on 3,000 real engaged fights (enemies within 3, someone loses 10%): deaths are the weak point —
greedy catches 132/487 real deaths (radius 8), 145/516 with radius 12 and camps (28%, 89 false alarms); the learned
policy 111/516 (64 false). A third of deaths have the killer outside 8 tiles 1-3 rounds before; 38% of victims had
more than half their health. Health error 7.0-7.1% (static 8.0%); positions are over-predicted (1.9-2.1 vs 1.5 tiles).

## E30 — Learned fight-or-run assessment from engine counterfactuals (fightcf_lab.js, assess_fit.py, A2_ASSESS)

Lab kinds 4 / 5 (lab.h, A2_LAB only): from a random round, at the first turn champion c (team A, lab build) has an
enemy within 4, force the fight / run verdict for 3 rounds; kind -4 records the bot's own verdict. Each state played
three ways against a pool opponent (v34c, sparexp, spartop, farm, aggro, combo); 1,468 usable of 2,000.
Deaths within 3 rounds: own verdict 1.3%, forced fight 3.2%, forced run 1.4%. Team gem margin 50 rounds later: fight
and run identical in 52%; a learned value model cannot predict the 50-round difference (held-out r = -0.02) — chaos.
Deaths are predictable from the start state: held-out AUC 0.81 (fighting), 0.95 (running).
3-round value (deaths 91 gems each side, health bar 42, from E26): run better 41%, fight better 4%, same 55%; mean per
decision: hindsight best +7.2, bot's own +4.5, always run +3.8, always fight -0.7. The 3-round value barely tracks the
50-round margin (r 0.075). A 42-24-1 network on the 3-round fight-minus-run value (4-fold held out, r 0.23):
switching only when |prediction| > 5 gives +5.05 against the bot's +4.47 (better in 3 of 4 folds).
A2_ASSESS (bot.cpp handle_enemies, assess_model.h): the bot computes the same features from what it sees and lets a
confident prediction (> A2_ASSESS_MARGIN = 5 gems) override fight/run. Off-build still ecafae4c.
a2c_assess vs a2c_combo: maps_test 100 x 2 sides 68/200 (34.0%, gems -24,424, kills 115–404); official 8/34 (23.5%,
gems -12,306, kills 94–347). Decision: rejected. The 3-round value favours running (run better 41% vs fight 4%), and
applied at every contact turn (training states were only the first contact turn) the bot keeps leaving fights and
gives up kills and ground. Any short-horizon lives/health score has this bias; the long-run value of fighting is what
the 50-round margin measures, and that is not learnable from ~1.5k chaotic samples.

## E31 — Learned in-fight move scorer (micro_lab.js, micro_fit.py)

micro_lab: duel_lab scenarios (70% 1v1, 30% 2v2, gap 1-3, health 30-100%), every option of the probe turn scored by
the engine (all options on one variant; each distinct executed action re-scored on a second variant, mean), with the
full start state. 338 labelled scenarios (the RAM watchdog stopped the run at 1.9 GB free; nothing crashed).
Scorer: 46 features the bot can compute (type, health, ranged, ready spells, enemies/allies, step distance change,
enemies that reach the new tile, enemies in reach, attack count and target health share, spell kind / target / order,
reset order), 46-32-1 network on value relative to the scenario's mean option. Held out (85 scenarios), shortfall
from the best option: bot's own turn mean 6.55 / median 1.25, within 0.5 of best 40%; model's pick 7.02 / 1.74, 38%;
average option 8.95. Decision: the scorer does not beat the bot's own moves at this data size; not wired in.

## E32 — In-fight move fixes tested in the duel lab (same 60 duels, seed 33, 49 valid; luck-free fresh variants)

| Bot | Within 0.5 | Within 1.0 | Mean shortfall | Behind on health (16) |
|---|---|---|---|---|
| combo (baseline) | 59% | 69% | 1.21 | 1.32 |
| a2c_ply1: one-turn lookahead (APEX_TSEARCH, APEX_TS_ROUNDS=0, A2_TS_VIS, A2_TS_FIGHTONLY) | 53% | 65% | 1.50 | 2.56 |
| a2c_bhold: A2_BURST_HOLD (Tavi/Willow/Ren/Vendetta, lone duel, behind: no burst) | 59% | 71% | 1.24 | 1.44 |
| a2c_cal (E26) | 67% | 78% | 1.35 | 0.92 |

A2_TS_FIGHTONLY: the tactical search only in turns the verdict fights (bot.cpp c1_acts). The one-turn lookahead
(my move, every other unit replies once, evaluate with the threat term) is worse than the hand micro. Burst-hold on
the 6 duels it applies to: best in 2/6 vs the combo's 3/6 (shortfall 2.12 vs 1.61) — without the burst the bot only
attacks, where the engine's better move was a step. Both rejected. Champion misplay analysis (1v1, losses of 2+):
Tavi 6/18, Willow 5/16, Ren 7/28, Vendetta 3/11 — mostly the burst combo where a single step scored better.
Richer move-scorer features (enemy spells ready, reach on the new tile, health race, damage that reaches the tile):
31% within 0.5 at 338 scenarios (bot 40%); more labels running.
Kite variant (A2_BURST_HOLD=2: a kite_step instead of the burst): 57% / 63% / 1.40, behind 1.14 — helps when behind,
hurts elsewhere. 2v2 (27 shared fights): combo 22% within 0.5 (shortfall 10.9), a2c_cal 26% (12.5), a2c_ply1 26% (14.4).

## E33 — Label reliability, simulator ranking, full-list search

Noise ceiling (noise.jsonl: 60 scenarios, every option on 4 independent variants): the best option on two variants
is within 0.5 of the best on the other two in 92%; rank correlation 0.90 (median 0.97); one option's score moves by
median 0.31. The labels are reliable: the bot's own turn (within 0.5 of best ~40%) really misses better moves.
Move scorers on 764 labels: physics scorer (exact damage/kills/stuns, worst plausible reply, fitted weights) 37%
(bot 39%); override-on-clear-gain 40%, shortfall 5.14 vs 5.67 (worse at 554 labels — not stable). Spatial model
(9x9 terrain + unit maps + option + physics, 373 inputs): 36% vs 39% — needs thousands more labels.
Simulator ranking (sim_rank.js: each labelled option applied in the bot's simulator, scored like the lab): best
settings — enemies commit (flee 0.2, no engagement check), our side flee 0.5 / engagement 1.0, 2 rounds, vision —
rank correlation 0.42 (ceiling 0.90); top pick within 0.5 44% vs the bot's 38% on 764 scenarios (shortfall 5.34 vs
5.80; 5.25 with only the orders the bot's search can express). Under these settings the simulator overvalues damage
dealt, stepping in and spell use, and undervalues stepping out.
In the bot (duel lab, same 49 duels): A2_TSFIX (tactical search with those settings, fight turns only) 51% / 55% /
2.43; A2_TSFULL (the labels' full candidate list via ts::gen_full, post-step and between-attack spells, no fuel
limit) 43% / 47% / 3.10 — both worse than the combo's 59% / 69% / 1.21. The offline gain does not survive the bot's
own snapshot (limited vision, cooldown estimates, acted flags) and a 0.4-correlated evaluator over 300+ candidates.
Decision: fight-move search and learned scorers stop here; all switches stay off (off-build ecafae4c).
Raising the simulator's agreement (764 labels, rank correlation with the engine; ceiling 0.90): one tuned greedy model
0.423; a 4-model opponent ensemble (commit / both careful / never flee / default) 0.423; ensemble plus the learned
behaviour network 0.421; an engine-calibrated linear evaluator on the simulated outcomes under all 5 models plus the
physics features (4-fold held out) 0.307 (raw ensemble on the same folds 0.401). The opponent model is not the
limit. Likely limit: the labels' 6-round continuation is played by the real bots, whose macro play (leaving to farm,
recalling, regrouping) a fight simulator does not represent.
Tested and rejected: fight-only continuation labels (MICRO_FIGHTONLY: every fighter's verdict forced to fight via
lab.h kind 4 for the whole continuation; host H.labCtlAll), 114 scenarios: agreement 0.373 (median 0.465), the same
as with the real bots' macro play. Forcing changed few option values (one smoke scenario 85/86 identical). The limit
is the simulator's fight model itself (rules over several turns and/or behaviour); next diagnostic would be replaying
the engine's recorded actions in the simulator to separate the two.

Replay diagnostic (replay_lab.js REPLAY_REC=1 trajectories, replay_sim.js): the simulator's rules are nearly exact -
95.2% of recorded turns reproduce exactly from the real state and real actions; replaying whole fights, 189/200 never
diverge by 25+ health and the final value error is 0.29. The disagreement is behaviour: the greedy playout policy picks
the real tile on 46-47% of turns, the real attack target 71-74%, the real spell slot 82%, all three 29%.
Learned tile model (behave2_fit.py, 9 tiles x 22 features + 18 context, 48 tanh units; A2_TILENET in ts::act, policy
team mask Policy::tile_net). The 2,000 recorded fights are only 873 unique (the host is deterministic; replayed
scenarios repeat exactly) - the first fit's 78.7% was train/test leakage. On unique fights, held out by fight: 59.3%
(always stay 42.4%, greedy ~47%); learning curve 56.0 / 57.4 / 59.3% at 1/4, 1/2, all training fights. The C++ port
matches the Python model (63.5% vs 61.6% on the same 200 fights; it plays 62.4% tile / 72.2% target / 84.0% slot /
41.4% all three vs greedy 47.2 / 70.9 / 81.5 / 29.1). Move-ranking agreement (764 labels, 2 rounds, vision): tuned
greedy 0.423; learned tiles both teams 0.368, ours only 0.371, enemies only 0.385; both at 1 round 0.386, 3 rounds
0.373. Better per-turn imitation lowers ranking agreement: the tuned greedy's flee/commit settings capture the
outcome-relevant behaviour better than a 59% tile imitator, whose errors compound over the playout. Decision: stop;
A2_TILENET off (default 0, parity unchanged).

Simulator agreement, continued (1v1 focus). Turn order: after the root move the playout let the root's ally act before
the next enemy; the engine alternates strictly (order_probe.js: A0 B0 A1 B1). A2_TS_ORDER (default 0) keeps an acted
unit's slot: 2v2 agreement 0.263 -> 0.278, all 0.423 -> 0.428. Sampled tile-model playouts (8 seeds, temp 0.5/1):
0.377 / 0.376 vs greedy 0.415 (train half) - rejected. Rank-scale correction on option features (rank_resid.py,
held out by half): +0.02 (1v1 0.49 -> ~0.51); it marks ranged-ends-adjacent and ends-in-own-range as overrated,
shield/dash underrated. Labels are reliable even for near-ties (fresh variants 0.92-0.96 in 1v1), so 1v1's 0.49 is
real disagreement. Sim vs labels by size: 1v1 0.488, 2v2 0.278.
Veto test (veto_rules.py, 531 1v1 positions, simulator value of the bot's own recorded move): keep the bot's move,
switch to the simulator's top option when it rates it better by more than T. T = 2: 10% of turns switched, of those
55% better / 26% worse; mean +0.30 gems per turn (95% CI -0.04..+0.69; halves -0.09 / +0.70); deaths 7.5% -> 6.8%.
T = 1: +0.33 (CI -0.09..+0.80), 24% switched. Always the simulator's top pick: worse than the bot (loss 3.19 vs 3.03).
Weak positive, not significant offline; would need an in-bot duel test.

## E35 — 1v1 behaviour fidelity (micro_lab.js MICRO_TRAJ, behave_swap.js, move_fit.py)

Engine ceiling: on 124 fresh 1v1 positions the engine's own 2-round option values rank like its 6-round values at
0.715 (median 0.81); the simulator reaches 0.488 against the 6-round labels. Horizon alignment (sim_rank.js --cut,
harness roll_cut: the last round ends after our own turn, as the labels do): vs 2-round labels 0.607 -> 0.650, vs
6-round 0.467 -> 0.488. Caveat: the labels' cut is an artefact of the label design, so this gain does not carry to games.
Swap analysis (276 1v1 positions, 2-round continuations recorded per option, replayed from the engine's post-move
state; real actions vs ts::act per unit/turn): all real 0.997 (rules exact); all policy 0.632; only our unit by policy
0.825; only the enemy 0.762; only turn 1 (the enemy's first reply) 0.809, turns 2-4 0.88-0.91. Enemy first reply,
real vs simulated: real steps away 27% (simulated 0.3%); spells agree 71%; hit-or-not agrees 71%.
Enemy flee/engagement grid (15 settings): nothing beats the always-commit setting (0.617-0.624 train half).
Learned movement intent (move_fit.py, closer/stay/side/away, 55 features, 26.5k turns): held-out 59.1% (majority 47.2%;
"away" recall 55.7%). In the playout (A2_MOVENET, team mask): enemy first reply 0.805 -> 0.819 but all-policy
0.647 -> 0.597 (held-out half). Class-score biases tuned for agreement on the train half (best: away -3, stay +1,
0.617 -> 0.636) are flat on the held-out half (0.629-0.651 vs 0.647). Same pattern as the tile model: per-turn
imitation gains compound into worse rankings. A2_MOVENET stays off.
Only real-rules fix for the bot: A2_TS_ORDER (engine turn alternation). Off-build still ecafae4c.
In the bot: a2ord (combo + A2_TS_ORDER) vs combo on the unseen-map pool (maps_real, 125 maps, one seed per map, 1,750 paired games): -0.2 +- 0.4 points, vs sparexp +0.4 +- 0.7, deaths/game -0.02 +- 0.02 (most games identical). Neutral; simulator-fidelity work stops here.

## E36 — Farming races (map_loss.py, solo_race.py, h2h.py)

Lanes, rows and expanse are farming races: 0.3-3.9 deaths a game (other maps 12.5), both teams finish near 1,000
banked gems, we are level on gems (coin flips 47-54%). Solo race vs the idle bot (rounds to 1,000, 3 race maps, 24
games each): farm 443, calm 444, v30base 446, combo 455, v34c 469, sparexp 486. Single changes on the combo: no item
build (APEX_BUILD=0) 444.8; gold weight 0.10 461.5; route depth 1, big-job off ~455; duo on official maps 483.8.
No item build on the official pool (1,904 paired): -7.5 +- 1.4 overall, expanse +34.8 +- 5.8 (53.6 -> 88.4%), fight
maps -10 to -31. A2_SPARSE_BUILD (default build when camp gems per tile < 0.25 AND tiles per champion >= 1,000; density
measured at turn one): fires on expanse and ambush; official head-to-head vs combo 75/136 = 55.1% +- 4.3.
Unseen maps (maps_real, 150 games each, head-to-head vs combo): a2best1 (combo + sparse build + bush hiding off)
48.7% +- 4.1; a2best2 (a2best1 with the v34 snapshot instead of SNAP=4) 46.0% +- 4.1. Neither beats the combo there.

## E37 — Draft and item build by map type on unseen maps (h2h.py, map_features.js, map_rule.py)

Options vs the combo (150 games each, 75 maps_real maps x 2 sides, head-to-head): farming item build everywhere
(rb0) 48.7% +- 4.1; ladder-meta lineup 19 on all unseen maps 50.7%; melee lineup 6 everywhere 36.0%; caster lineup 12
37.3%. The combo's unseen draft (lineup 2, melee lineup 6 on clustered maps) and top-team build are already the best of
these. Map features (agent2/lab/map_features.js: size, picks, groups, gems, density, room per pick, bush, blocked,
spread, ...; camp groups need Game_Runner_Init first) with single-threshold rules chosen on 50 maps and scored on 25
held out: rb0 -2.0, u19 +0.0, u6 -2.0, u12 -4.0 points. No map-type rule generalises at 2 games per map; nothing adopted.

## E38 — Death diagnosis and death what-ifs (real_deaths.py, death_lab.js)

Death context, combo pool games (68 each vs sparexp / v34c): we trade evenly (vs sparexp our 923 deaths, theirs 1,027);
Cassi+Issac 44% of our deaths; ~1/3 burst deaths (>= 80% health six turns before); 14-18% with no enemy within 6
(camps); 15% with no ally within 15. What-ifs (combo lab build vs sparexp, official maps, 138 deaths; the dying
champion runs / regroups / walks home / fights for 10-15 rounds starting 3 or 8 rounds before its death; team gem
margin 100 rounds after the death vs the untouched game): every response scores +2 to +21, including "fight", which
never avoids the death (+15.6 on average) — choosing moments just before a death selects bad futures, and any
perturbation regresses toward the mean. Against that control: home@8 avoids 72/138 deaths, +17.3 +- 10.6 overall
(+29.8 when the death is avoided, +3.8 when not); run@8 +9.4; regroup@8 +2.4. Avoiding a death by leaving early costs
about what the death costs: no response beats the control. Deaths against pool bots are not a cheap lever.

## E39 — Architecture changes (150 games each vs combo, maps_real, head-to-head)

A (decision layer): fight/run verdict by rules only, no simulator search (APEX_TS_DECIDE=0): 73/150 = 48.7% +- 4.1 —
the search verdict adds nothing measurable. B (strategy layer, A2_RACE): both teams' finish projected from the last 80
rounds' banking rate; projected lead >= 30 rounds -> safe (aggression x0.7, bank bags x0.6, retreat +10%, no hunting),
behind by 30 -> contest (aggression x1.35, x1.6 when the enemy is within 100 gems; hunting on): 68/150 = 45.3% +- 4.1.
Neither beats the combo.

## E40 — Exploit candidates against the combo (150 games each, maps_real head-to-head)

E1 carrier hunter (hunt range 14, while carrying < 60, down to 50% health, chase 9): 50.0% +- 4.1. E2 altar ambusher
(A2_AMBUSH: from round 60 one champion waits within 2 of the altar nearest the enemy spawn; fight / tribute-denial
logic when enemies appear): 36.7% +- 3.9. E3 counter-draft (unseen lineup 1, C&I+Stellar+Tavi): 44.0%. E4 early
pressure (brain class aggression x1.3, invade enemy-side groups): 34.7% +- 3.9. E5 calmer (class aggression x0.75):
44.0%. The combo's aggression sits at an optimum (both directions lose); exploiting it with hunting, ambushes,
pressure or a counter-lineup does not work. No candidate reached 55%, so no pool check.

## E41 — The ladder death gap and a two-turn burst check (A2_BURST2)

Decoded ladder games (real_deaths.py): v28 16 games, our deaths 317 vs theirs 139 (19.8 vs 8.7 a game); v26 13 games
120 vs 81. The pool is even (combo vs sparexp 923 vs 1,027), so pool and mirror tests cannot see this gap. 52% of our
ladder deaths start above 80% health six turns earlier (theirs 37%): two-turn bursts with stuns.
A2_BURST2: danger when two turns of hits from every enemy within range + 3, ready spells (cooldown <= 2) and an extra
round when a stun is ready within 5 exceed our health (C&I: the weaker body), unless allies within 3 at >= 50% health
outnumber the foes or this turn is a sure kill. Pool (11 maps_real maps, 154 games, paired with the combo):
+3.0 +- 2.8 points (+21 +- 20 local Elo), deaths -0.43 +- 0.19 a game (vs sparexp -0.86 +- 0.48). Head-to-head vs the
combo (150 games): 46.0% +- 4.1. Candidate for a ladder A/B (the only test that sees one-sided deaths).
A2_BURST2 vs combo, 100 more head-to-head games on the 50 maps_real maps not used before: 52/100 = 52.0% +- 5.0 (with the earlier 150: 121/250 = 48.4% +- 3.2).

## E42 — Big changes in order (150 games vs combo head-to-head on maps_real + 154-game pool check, paired)

Joint knob search (knob_es.js, lab knobs: 16 runtime settings after the brain layer; 32 maps x 2 sides x combo /
sparexp / farm, paired with the zero-knob games): averaged knobs -0.072 at generation 3, +0.025 at generation 6 (win
62.5% vs 61.5%); the run ended silently after generation 6 (builds were running alongside).
Change 3 (no fight-search verdict) = archA, 48.7%. Change 1 = no search + A2_BURST2 + A2_DANGERMAP (outside fights never
step into the two-turn kill zone unless allies outnumber): 47.3%, pool -1.1 +- 5.6, deaths -0.08 — worse than the burst
check alone. Change 2 (team brain = A2_PLAN team camp assignment + A2_TEAM=2 join + APEX_TFC focus): 16.7%, pool -30.0;
diagnosis (50 games each on the burst base): A2_PLAN 18% (with stickiness, A2_PLAN=2, 20%), join 54%, focus 44%. Solo
farming race: the plan takes 737 rounds to 1,000 against 577 without it — one group per champion and no multi-champion
jobs make it a much worse camp chooser than the scorer. Change 4: learned win probability (winprob_fit.py, logistic on
banked-gem timelines, 138k samples / 12k pool games, held-out accuracy 73.6%) driving the race posture (A2_RACE=2:
safe above P 0.8, contest below 0.25) on the burst base: 46.7% head-to-head, pool +5.2 +- 3.6 (+36 local Elo), deaths
-0.26 (vs sparexp -0.86). Best configuration so far: combo + A2_BURST2 + A2_RACE=2. Joint search resumed on it.
Joint search against the combo only (knob_es3: 64 maps_real maps x 2 sides, burst check + learned posture as base,
started from the first run's generation-6 knobs): baseline 42.2% vs the combo in the lab; averaged knobs 56.3% at
generation 3, 53.9% at 6, 48.4% at 9 (drifting; stopped). Generation-3 knobs baked into a build (lab.h A2_KNOBS; bot
g3 = combo + A2_BURST2 + A2_RACE=2 + knobs) vs the combo in cambc on the 61 maps_real maps the search never used:
65/122 = 53.3% +- 4.5. Knobs (best_knobs.txt): aggression x1.10, bag before banking x0.81, hunt range -1, chase -1,
wait weight x1.10, solo-camp health budget x0.89, shop gold +17, others near zero.
g3 vs the combo on maps_clean (75 maps x 2 sides, never used in the search): 84/150 = 56.0% +- 4.1; with the 61 fresh maps_real maps 149/272 = 54.8% +- 3.0. Smaller-step search started from the g3 knobs (knob_es4: sigma 0.25, lr 0.12, combo only, same 64 training maps).
knob_es4 (smaller steps from g3): averaged knobs 56.3% at generation 3 (fitness 0.186 vs 0.167 for g3), 54.7% at 6; paused at generation 8. Its generation-3 knobs saved to agent2/lab/best_knobs_es4_g3.txt (not yet tested in cambc). Best tested bot remains g3: 149/272 = 54.8% +- 3.0 vs the combo on unseen maps.

## E43 — Engine 3.0.2 (v3/ workspace): port, Heart of Ruin, new lineups, item build; vs the provided bot

New engine 3.0.2 / rules 9 (wolves 4 gems, elk/golem range 4, monolith 5, kill gold 100, locks 5 hits, ward recharge 10,
stat changes, Heart of Ruin, 35 official maps). Bot ported to v3/ (SDK compatible; spell table widened to 13 champions,
dash landing damage/stun counted). Versus the combo on the new engine: g3 37.9% official / 47.3% maps_real (old tuning
does not transfer). Striking dash (cast_on_enemy: Heart of Ruin lands its stun dash next to the target): L21 49.3 ->
57.1%. Lineups (all maps, dash): L24 60.0%, L23 52.9%. Camp-clearing build (APEX_BUILD=0): L24b0 67.9% official,
52.7% maps_real, 32.7% maps_clean; L21b0 56.0% maps_real; build only (combo lineups) 52.9 / 52.7 / 46.0%.
nb1 (build 0, L24 on the 17 recognised official maps, L21 elsewhere): 67.9% official, 56.0% maps_real, 38.0% maps_clean.
nb1 vs the provided bot (bot.zip = v34 + Agent 4's v36 draft: NOVA_V36_DRAFT=1, NOVA_MAPID_STRICT=0), new engine:
100 maps_real x 2 = 119/200 (59.5% +- 3.5; 3/4/5 picks 54/61/64%); 35 official maps x 3 = 67/105 (63.8% +- 4.7;
3/4/5 picks 78/71/58%; L21 on the unrecognised new official maps 52.4%, L24 on recognised 67-83%). Losses 0/3 on
eight, split, boss-battle, elk-arena, starvation.

## E44 — Engine 1.0.1 lab, lineup table, PPO policy, paper ideas (vs nb1)

Lab on the new engine (tools/viz/v1_0_1.wasm from the cambc 3.0.2 asset cache; ~1 s per game per worker; forced
drafts; draft ids = SDK champion_draft). Lineup table (draft_table.js, our bot both sides, forced lineups): 35 official
maps x 8 x 8 x 2 = 4,480 games: L24 61%, L21 59%, mix 55%, melee 51%, vesper 48%, L23 46%, meta 45%, caster 34%.
150 new-rule maps (tools/viz/mapmake3.js: engine 1.0.1 MapBuilder + golems; larger and sparser than the official pool):
120 done vs field meta/L21/L24/melee. Feature selectors (lineup_fit.py: 22 map features, ridge per lineup; simple
size/density/room/big-camp rules), 5-fold by map on 155 maps: none beats always L21 (57.5%; ridge ~57%, simple 55-57%).
PPO fight/run policy (A2_POLICY lab build; 24 features -> 32 -> fight/run/keep; ppo_lab.js: zero-sum team reward, win
bonus, GAE, clip 0.2, entropy 0.01, nb1/ext/self opponents, start = keep the bot's verdict): two-action version started
at 13% (neutral cases became fights); three-action version starts at nb1's level. 92 iterations x 96-128 games: greedy
vs nb1 46.7 -> 50 -> 60 -> 51.7 -> 56.7 -> 45 -> 53.3% (30 games each): flat, stopped.
Lab head-to-heads vs nb1 (lab_h2h.js; 75 new maps x 2 + 35 official x 2): always L21 50.0 / 51.4%; A2_HPVAL2 (logistic
death risk) 48.0 / 47.1%; A2_RACE=4 (aggression x (1 + 0.6 (P - 0.5))) 50.0 / 49.3%; NOVA_QUARTIC 53.0 / 49.3%.
Macro what-if expert iteration (exit_lab.js, a2c_mlab: 20 features recorded at the decision point; random map / round
60-800 / champion, nb1 70% + provided bot 30%; 6 replays per point: keep, forbid camp 25, bank 12, hold 30, regroup
12, home 15; gain = team margin (banked + carried + 40 per living champion) 150 rounds later minus keep's), 1,268 points
on 155 maps: always forbid -4.4 +- 2.4, bank -0.6 +- 2.4, hold -3.3 +- 2.7, regroup +0.1 +- 1.9, home -5.4 +- 2.7.
Ridge chooser per option (macro_fit.py, 5-fold grouped by map): best +0.1 +- 0.3 gems per decision (acts on 2%); acting
more often -1 to -3. The bot's macro choices are already locally optimal against these options; stopped.

## E45 (21 Oct) - kit audit under engine 1.0.1 + top-team lineup table
- Lineup table vs the real top-15 field (tmVarg / tmMarc / tmCI, nb1 play both sides, 35 official maps, 105 pairs x 2):
  L21 60.0% (+64), tmMarc 54.5, tmVesVen 51.9, tmVarg 51.7, L24 46.9, mix 46.4, melee 45.5, tmVesMarc 45.2,
  tmCI 43.8, vesper 41.0, L23 38.1, meta 33.6, caster 30.0. Our fallback L21 already beats the top-team lineups.
- Kit audit: wards (cooldown checked), altar locks (generic attack until gone), golems (generic) fine. Bugs found:
  tsearch kit_of table had 12 entries, Heart of Ruin = type 12 -> no shield / dash in the fight search for any HoR;
  no missing-health damage bonus; bot.cpp kBase (items_of) had old stats and no HoR (items_of(HoR) = 0).
- A2_KITFIX bitmask (common.h; 0 = nb1 replay-identical, checked): 1 HoR kit entry, 2 striking-dash landing in the
  search, 4 missing-health bonus, 8 new kBase. Built with v3/mk_kf.py (nb1 defines + extras). vs nb1, maps_test3:
  15: 46.5 | 1: 54.5/49.0 | 3: 44.3 | 4: 52.0 | 8: 55.0/56.0, seed2 50.7 (400) | 9: 54.5/52.5, seed2 54.6 (400) |
  5: 50.5 | 13: 53.5/53.0. Official 3/map: 8 44.8, 9 49.0, 13 47.6; seed2 2/map: 8 48.6, 9 42.1.
  -> bit 2 (dash landing) hurts; best 9 = +4 on unseen (800 games), -4 on official (175, 1 SE). Not packaged.

## E46 (21 Oct) - black-box knob search result + kit fix = new best candidate (knkf)
- knob_es2 run1 (40 gens, 8 pairs, 48 maps, vs nb1/ext + league): mean knobs on training games 55-63% (baseline 54.7),
  plateau from gen ~12. Fresh validation (lab_h2h H2H_KNOBS, a2c_klab vs sb_nb1_c1, maps_test3 200 x 2): zero knobs 51.7,
  g22 53.9, g30 59.0, avg(g22..32) 58.8; official 4/map: zero 53.6, g30 54.3, avg 53.9 (margin +60).
- Baked builds via v3/mk_kf.py: A2_LAB=1 + A2_KNOBS=avg22_32 (agent2/lab/knobs_avg22_32.txt) [+ A2_KITFIX=9].
  kn_c1 vs nb1: unseen 4/map 57.2% (800, +60), official 3/map 56.7%. knkf_c1: unseen 61.6% (800, +83), official
  61.0% (105, +160). knkf_c2 vs sb_nb1_c3: unseen 59.4% (400), official 63.6% (70). Gains stack.
- Real engine (cambc run-batch, 40 unseen maps x 2, seeds 1-2 spread): knkf vs nb1 62.5% (80). Packaged as v3/bots/nb2 (hash = knkf_c1) -> v3/submissions/nb2_engine3.zip.

## E47 (22 Oct) - map-conditioned black-box search (A2_CTX, knob_ctx.js) - running
Idea: settings as a smooth function of turn-one map features instead of one global vector (old evidence: the best item
build flips sign between map types; hand-made map rules failed on small data). Effective knob i = k[i] + sum_j
k[24 (1 + j) + i] * f_j, f = (team size, ln area, ln gem density, ln groups, monolith), normalised on the 185 training
maps (ctx_stats.js: MU 4.097 8.280 -2.156 2.794 0.400, SD 0.813 0.641 0.762 0.406 0.490; maps_test3 similar).
Parity: rebuilt nb2 replays knkf_c1 exactly; a2c_ctx (A2_LAB + KITFIX 9 + CTX 5) with nb2 knobs and zero slopes mirrors
nb2 (0 margin). Run 1: 144 knobs from nb2's, fresh 32 training maps per generation, vs nb2 (knkf_c1) + provided bot,
12 pairs, sigma 0.25, lr 0.10, 30 gens (knob_ctx_run1.tsv/.log).

## E48 (26 Oct) - cambc 4.0.0 / engine 2.0.0: setup, lab fix, v57 analysis
Workspace v4/ (cambc init . --yes; 70 official maps). Lab engine tools/viz/v2_0_0.wasm (asset cache 174924b1...).
host.js fix: Game_API_Champion_GetItems takes the capacity in BYTES on engine 2.0.0 (count 42 -> error 111 on every
inventory read, bots scored 0); now passes SZ.items (old engines unchanged: knkf vs nb1 replay identical). Lab vs real
cambc on 12 games: identical (v57 vs nb4 10/12 both). Maps: mapmake4.js (CLEAN=1 REAL=1) -> v4/maps_test4 (200, seed
99100000), v4/maps_new4 (150, seed 77700000). Bots v4/bots/{v57,nb4,nb2}_c{1,2}; variants with v4/mkvar.py.
4/map on maps_test4 (800) / official 4/map (280): v57 vs nb4 66.4% / 62.0%; v57 vs nb2 69.4 / 76.1; nb4 vs nb2 55.4 / 55.2.
v57 one-part-off vs v57 (400 unseen / 140 official): draft net off 41.5 / 45.7 (net worth ~+8); gold boost off 47.4 /
46.1; item milestones off 46.0 / 47.1; camp net off 52.1 / 55.4 but 45.0 on 100 fresh maps_new4 games (neutral overall);
TP off 52.3 / 49.3; hold, mobility draft, shop-done: 50.0 / ~50 (never fire or no effect).
Lineup table on 4.0.0 (lineup_v4.js: fixed lineup vs v57's own learned draft, v57 play both sides, 30 maps_test4 + 20
official x 2 sides = 100 games each): melee [2,9,3,0,8] 51.0, noHoR [2,9,0,6,1] 46, L21 45, vendHoR 45, vesTav 43,
vesVen 39, tmVesVen 38.5, mixB 37, prism 34, tavi 28, L24 27, casterB 25, tmMarc 24, tmVarg 20. No fixed lineup beats
the draft net; the old top-team core (HoR + Stellar + Ren) collapses after the patch (20-24%).

## E49 (26 Oct) - black-box search on 4.0.0 from v57 (running)
knob_ctx.js generalised (BOTS_DIR, ES_MAPDIRS; CTX_F=1 -> 48 plain knobs = v57's lab.h slots: 0-23 run-1 knobs, 24-32
fight-search weights / enemy flee / decide margin / horizon / cmicro risk, 35-42 Vesper items, tribute distance, end
bank, cohesion, ward distance, middle weight, team-fight engage, prelock). Lab bot v57_c1 (A2_LAB), opponent v57_c2,
start = v57's baked knobs (agent2/lab/knobs_v57_init.txt; centre plays even). Fresh 50 maps per generation from
v4/maps_new4 + 70 official (100 games per candidate), 12 pairs, sigma 0.25, lr 0.10, 30 gens -> knob_v4_run1.tsv/.log.
Held-out: v4/maps_test4.

## E50 (26 Oct) - patch notes check, self-play draft net, engine-read stats
Engine 2.0.0 designs match the 4.0.0 patch notes (Ren stun 1.1x, Tavi 1.6x, Ryth/Marcella/HoR growth cuts, Vesper 45
str, Cassi 100 focus, Willow 140, Varg 45); GameRules (10) is stale. Host: items now 84 counts (336 bytes); capacity
passed in counts. New emblem families 7-13 (tribute, capture, prospector, hunter, skirmish, greed, collectors).
Draft net self-play fine-tune (draft_data4.js random lineups, v57 both sides; 3,786 games before the RAM watchdog
stopped it; draft_fit4.py): val log-loss 0.676 -> 0.668; vs v57 100 games maps_test4: L2 1e-3 48%, L2 1e-2 50%. No gain.
v58 (A2_KITFIX 57: items_of base stats read from the engine design): 43% vs v57 (100). Not adopted.
Black-box search stopped at gen 5 (memory pressure with two jobs); restarted alone from the gen-5 knobs.

## E51 (26 Oct) - engine 2.0.0 glitch probes (agent2/lab/glitch_probe.js, altar_camps.js)
Harness: our team fully scripted (hooks.force), enemy idle, sandbox setup (gold, gems, teleport, damage), spectator reads.
- Tavi buy/sell: exact refunds (Treasure, Greed 25 -> +2625 hp on Tavi); no gold glitch.
- Tribute turns (from submit to banked) no emblem / Tribute emblem: 10:1/1, 20:2/2, 30:3/3, 31:4/3, 40:4/3, 45:5/4,
  60:6/5, 90:9/7. The emblem only helps bags >= 31.
- Growing bag: a 1-gem tribute (1 tick) banks the whole bag at completion (+80 sandbox gems mid-channel: 81 banked).
- Capture-bank: on a camp tile within 1 of an altar, start a tribute with a small bag on the capture's last turn ->
  the capture lands first and is banked in the same tick. shortcut 235-gem group: banked 6 rounds after the kill vs 30
  (24 turns of channel saved). 11/70 official maps have altar-side groups (boss-battle 400, shortcut 235x2, guardians
  200x2, starfish 118, yellow-brick-road 45x2, hooks 22x2, small elsewhere).
- Own altar lock cancels OUR teammate's tribute at that altar (40-gem channel lost). v57's prelock / try_lock_altar /
  deny lock do not check for an ally channelling there.
- Consumables: engine slot 1 is disabled (carry 0); the SDK maps altar_lock to slot 2 (not a bug). Crystal: range 3
  Chebyshev, altar landing forbidden.
- v58 A2_INSTABANK (capture-bank in the bot, bag cap A2_IB_MAXBAG 20, walks to the altar-side tile): fires 0-1 times
  a game; first version banked a 1,078-gem bag on boss-battle (no cap). On shortcut v57 never holds a finished capture
  near the altar (golem group rarely taken). 44 games on the 11 maps: 40.9% (first version). Not adopted.
- A2_LOCKGUARD (v58: prelock / try_lock_altar / deny lock skip an altar where a visible teammate is tributing):
  parity build lg0 vs v57 identical; lg vs v57 100 games maps_test4: 50/100, margin 0 = every game identical to v57's.
  The self-cancel never happens in v57's games (locks are placed where enemies bank, not where we do). Kept as a
  safety switch, no measured effect.
- Capture emblem (33-gem group, sandbox kill): none -> reward 6 rounds after the kill; holder from the start -> 4;
  holder starts with an ally then leaves after one turn -> 4 (the 3-turn timer is kept); ally starts, holder joins at
  timer 4 -> timer drops to 3, reward at 5 (rules say only "as the capture begins": engine deviation in our favour);
  holder joins at timer 3 -> no change (6). Engine behaviour: a holder on the region caps the timer at 3, never raises it.
- Hunter emblem on a Cassi & Issac kill: one reward (100 base, 150 with Hunter), both bodies die. As the rules say.
- Dead champion: buys items and altar locks anywhere; Tavi cannot sell while dead off spawn (rc 133). As the rules say.
- E49 result: the search stopped silently after 18 generations of run 2 (23 in total). Average of run-2 gens 9-18
  (agent2/lab/knobs_v4_avg9_18.txt; biggest moves k28 enemy flee 0 -> -0.71, k9 wait weight -0.12 -> 0.51, k12 shop gold
  0.07 -> 0.58, k38 cohesion dist 0 -> -0.49, k22 melee aggression -0.28 -> -0.77) vs v57's own knobs, same 100 games
  (v57_c1 vs v57_c2, maps_test4): maps 0-49 51% vs 45%, maps 50-99 55% vs 50% -> about +5.5 over 200 games.

## E52 (26 Oct) - emblem builds (item_v4.js) and v59
Builds via the lab build table vs v57 (same 100 games; control = v57's own build): unseen maps_test4 control 40.0:
capProspector 58.0, prospectorFirst 61.5, prosNoCap 56.0, capMonster 51.5, capCollectors 48.5, v57like 47.5,
capFirst 47.0, capNoTreasure 46.5, capHome 46.0, capSkirmish 45.0, capGreed 43.5, capTribute 42.0, treasureThenCap
39.5. Official (50 maps x 2) control 47.0: prosNoCap 56, prospectorFirst 52, capProspector 51, capProsMonster 51,
capMonster 49.5, v57like 45. With the 4.0.0 knobs (avg 9-18): prospectorFirst 63.5 unseen / 60.0 official.
v59 = v57 + A2_PROSBUILD (Prospector, Capture, Jungle, Durability, Bruiser 40/60; casters focus) + A2_KNOBS = avg 9-18
(48) + A2_LOCKGUARD (v4/bots/v59, submissions/v59_engine4.zip). vs v57, fresh: unseen maps 100-149 63.5% (+89),
official 60.0% (+129), seed 2 maps 150-199 66.0% (+97); real cambc 4.0.0, 100 games: 67/100.

## E53 (26 Oct) - real engine (cambc 4.0.0): v59 vs v57 (stopped) and v59 vs the team's v58 dev package (t58)
Same 390-game set: 250 fresh unseen maps (mapmake4 seed 99400000, one game each, sides alternating) + 70 official x 2.
v59 vs v57, stopped by the user at 288: 69.4% (unseen 181/250 = 72.4%, official 19/38).
v59 vs t58 (bot (4).zip = v58 dev: V58_ITEM_PLAN Prospector/Capture, capture footwork/stand, director, survive,
vision, locks, carry hunt, per-champion kits; v4/bots/t58), all 390: v59 44.9% (unseen 45.6%, official 43.6%;
as team A 48.7, team B 41.0; 5 picks 40.6). t58 is ~10 points stronger than v59. Official maps lost 0/2: 22.
Score: v59 175/390 (44.9%), t58 215/390.
Merging into t58 (lab, vs t58_c2, 100 games each; control = t58_c1): unseen control 42.5 -> + v59 knobs 47.0,
our Prospector-first table (V58_ITEM_PLAN 0) 35.5, table + knobs 50.5; official control 48.0 -> knobs 61.0,
table + knobs 52.0. Baked t59 = t58 + v59 knobs: lab fresh unseen 51.0 vs control 42.5. Real engine vs t58 (as sent):
48/100 and 50/100 (49% over 200) -> no real gain. Fuel is not the cause (fuel log: 0-4 overruns a game for both).
Their v58 stays best; v59's knobs were tuned against v57 and do not carry to t58 in the real engine.

## E54 (26 Oct) - black-box search from the team's v58 (t58), running
knob_ctx.js, LAB_BOT t58_c1 (A2_LAB), opponent t58_c2, start = t58's baked knobs (agent2/lab/knobs_t58_init.txt),
48 knobs, fresh 50 training maps per generation (100 games per candidate), 12 pairs, sigma 0.25, lr 0.10, 25 gens
-> knob_t58_run1.tsv/.log. Confirmation planned: lab 100 games on maps_test4 vs a same-games control, then 100+ real.

## E55 (26 Oct) - more engine probes (glitch_probe.js friendlyFire, rangedReset, wallCrystal, channels, campAggro)
- Friendly fire: basic attacks (rc 42) and damage spells (rc 30) on allies are refused: no gem transfer by team kill.
- Ranged move + attack: move, attack reset, attack works in one turn (attack then move refused). Legal (rules: resets
  restore the attack allowance). Vesper / Willow / Tavi every 8 turns.
- Teleport crystal onto a wall: "Forbidden landing tile" (crossing walls only).
- Channels: one tribute start per turn (rc 114 after a cancel); recall blocks other actions.
- Camp aggro: one hit on a sleeping wolf / elk camp whose nearest champion is an idle enemy -> the camp hits the enemy
  80 a turn for 7+ turns, never us (legal: camps attack the nearest champion; camp kills destroy carried gems).
  t60 = t58 + A2_CAMPPULL (spare attack on a sleeping camp whose nearest champion is a visible enemy): 44/100 vs
  control t58_c1 46/100 (same games vs t58_c2). Not adopted.
- The t58 search died after gen 1: RAM watchdog (lowest free 1.6 GB) while builds ran alongside; restarted alone.
  The earlier silent stops of long searches were probably the same cause.
- Stun timing (glitch_probe stunTiming): a one-round stun costs the victim exactly one turn whether it lands before or
  after the victim's turn in the round. No double stun.
- Random-action fuzzer (agent2/lab/glitch_fuzz.js: our team random moves / ground and unit casts / attacks / buys /
  sells / consumables / tributes / cancels / recalls every turn, v57 opposite, invariants: no champion on wall / hole /
  altar, health <= max, no unexplained gold or gem jumps): 20 games, ~19k successful actions (3,900 moves, 2,050
  casts, 1,170 buys, 320 consumables, 4,400 recalls): no violations.
E54 result: 25 generations (training-map centre win gens 16-25: 61, 60.5, 58, 62.5, 55, 57, 53, 55, 54.5, 54).
Average of gens 16-25 (agent2/lab/knobs_t58_avg16_25.txt; biggest moves k40 middle-camp weight 0 -> 0.63, k36 tribute
distance 0 -> -0.60, k11 cohesion 0.87 -> 0.39, k2 danger ttd 0.19 -> 0.61, k15 hunting 0.11 -> -0.31, k9 wait 0.29,
k27 search gem weight -0.39, k25 search hp weight 0.36). Lab vs t58_c2, same games: maps_test4 0-49 control 46 ->
67; 50-99 control 49 -> 62. Real engine v61 (= t58 + these knobs, v4/bots/v61, v4/submissions/v61_engine4.zip) vs t58
as sent: unseen maps_real250 56/100, official 58/100 -> 57% over 200.

## E56 (26 Oct) - why the lab showed +21 and the real engine +7 for v61
- Engine seed: Game_FromMapFileBytes' 4th argument (now H.seed / LAB_SEED in host.js) changes nothing (5 seeds, same
  game). No seed overfitting possible.
- Replaying the exact 100 real games (replay_real.js: same bots, maps, sides) in the lab: lab 57/100 vs real 56/100 in
  total, but the same winner in only 53/100 and game lengths differ: the lab is not an exact engine copy game by game
  (most likely fuel: the lab's fuel_remaining() always reports a full budget, so fuel-gated searches never stop
  early), yet the overall rate agrees.
- Same tuned settings vs different v58 seeds on maps_test4 0-49 (100 games each, control = v58's own settings):
  seed 2 (the search's training opponent) 46 -> 67; seed 1 (mirror) 50 -> 63; seed 3 (new) 54 -> 64.
  So: about +4 of the +21 is tuning to the training opponent, about +4 is the seed-2 control sitting below 50, and the
  rest (+10-13 lab vs +7 real) is within the noise of 100-game sets (the difference of two has SE ~7).
- Protocol fix: test against an opponent seed the search never played, with a mirror control, 200+ games.

## E57 (26 Oct) - v61 vs the team's v60 dev (bot (5).zip, v4/bots/b5), real engine, 340 games
bot (6).zip and bot (8).zip are file-identical to the v58 sent earlier (same build hash); not tested again.
200 fresh unseen maps (v4/maps_real200b, seed 99500000, one game each, sides alternating) + 70 official x 2:
v61 187/340 = 55.0% +- 2.7 (unseen 53.5%, official 57.1%; team A 55.9, team B 54.1; 3 picks 45.8, 4 picks 58.0,
5 picks 55.8). Official maps lost 0/2: 17.

## E58 (26 Oct) - merge of bot (5) (v60 dev) with v61's knobs, and a search against both
Lab, 200 games each (maps_test4 100 x 2) vs fresh seed-3 opponents: v61_c1 vs v61_c3 46.5 / vs b5_c3 53.5 (avg 50.0);
b5_c1 39.5 / 47.3 (43.4); m62_c1 (= b5 + v61 knobs) 48.0 / 55.5 (51.8). The merge adds ~nothing over v61.
Dormant feature screen (TEAMFIGHT, SURVIVE, DIRECTOR, ZONES, ROUTE, HUNT_CARRY, VISION, LOCKS, ...) dropped on the
user's word (team testing found them of little value).
Search: knob_ctx.js, LAB_BOT m62_c1, opponents v61_c2 + b5_c2 (seed 3 reserved for testing), start = v61 knobs,
25 maps x 2 sides x 2 opponents = 100 games per candidate, 12 pairs, 25 gens -> knob_m62_run1.tsv/.log.

## E59 (26 Oct) - engine reverse-engineering pass (agent2/engine_re/)
- Tools already on the PC: wasi-sdk llvm-objdump / llvm-strings (cambc's compiler). Engine v2_0_0.wasm: 408 exports,
  no name section (internal functions unnamed); 1,133 strings (strings_v2.txt): explicit vision / perspective checks.
- Fog-of-war audit (api_audit.js, our champion's perspective on 5 hidden enemies, 46 hidden camps, 12 groups): gems,
  gold, cooldowns, items, consumables, buffs, channel, priority, restrictions, wards, damage refused (97 / 105 / 112);
  identity, ability metadata (static design) and is_alive readable (documented; already used). Enemy-occupancy and
  camp boards contain only visible units; hidden camps unreadable; group state reads 0 (= unknown). No leak.
- Fuel: fuel_pause / fuel_resume / fuel_adjust are declared only under CAMBC_DEBUG; a release bot importing
  env::fuel_pause is trapped by cambc 4.0.0 ("bot was built in debug mode"). No way around the fuel budget.
- With E51 / E55 (rule probes, fuzzer): no engine bug found; usable mechanics remain capture-bank, the Capture-emblem
  timer cap, camp aggro, ranged move-reset-attack and failed-move bush scouting.

## E60 (26 Oct) - pathing benchmark (v4/bots/pathprobe: walking-distance fields on the first draft turn, real engine)
Draft turn 1 has ~10.0M fuel. One field: 3k-33k fuel; fields from every camp group: 96k-549k (1-6% of the turn).
Walking / straight-line distance to groups: ambush 1.32 (max 1.56), big-world 1.78 (3.20), islands 1.15 (38 of 46
groups unreachable on foot), cuts 2.40 (4.06; spawn-to-spawn walk 167 vs 57), lanes 0.99, boss-battle 1.11 (1.95);
generated unseen maps 0.98-1.00 (open). A2_DPLAN plans with straight-line distance (wrong on maze maps).
Methodology finding: mapmake4 maps are far more open than official maps -> weight tuning / tests toward official maps,
or add walls / corridors to the generator. Search knob_m62_run1 stopped after gen 8 (silent; session change or the
probe build); resumed from gen 8.

## E61 (26 Oct) - maze maps, specialist plans, map precompute (v4/bots/p63*, running)
- Walking features (agent2/lab/path_feats.js, engine distance field from each spawn): gem-weighted walk / straight-line
  ratio official median 1.27 (90th pct 2.52; cuts 2.81, big-world 1.89, ambush 1.36), mapmake4 maps all 1.00.
- Maze generator tools/viz/mapmake5.js MAZE=1 (walled rooms with doors, barrier bands with gaps, hole lakes; kept only if
  the spawns connect and the ratio is 1.15-3.2): v4/maps_maze (150, seed 55500000, train) and v4/maps_mazetest (100,
  seed 55800000, held out), ratio mean 1.32, max 2.58. Games run normally (0 errors).
- Clusters (agent2/lab/plan_clusters.py): 2 x large (area >= 4000) + maze (ratio >= 1.2); training maps per cluster
  100 / 56 / 141 / 73. One 48-knob search per cluster (plan_search.ps1, knob_ctx.js ES_MAPLIST, m62_c1 vs v61_c2 +
  b5_c2, from v61 knobs, 15 gens) -> plan_c<k>.tsv; selector A2_PLANSEL (p63, mappre.h cluster_of).
- Engine/SDK API audit (documented API only): the bot imports 85 of 154 host functions; it never reads enemy altar
  locks (a tribute at an enemy-locked altar becomes lock hits) -> A2_LOCKAWARE (p63L), test pending.
- A2_MAPPRE (src/mappre.h): first draft turn computes walking fields from both spawns and from every group (fdist reads;
  distance_field::get is a host call the lab does not forward), writes a summary at draft memory 600-991 ('M', version,
  cluster, n, rush, altar, 4 bytes per group); A2_DPLAN uses the walking matrix. host.js: LAB_DRAFT_FUEL (first draft
  turn budget, default 1M as before; 10M = cambc 4.0.0). Cluster and rush distance match path_feats.js exactly.
  Lab, 200 games each (25 maps_test4 + 25 maps_mazetest x 2 sides vs v61_c3 + b5_c3, LAB_DRAFT_FUEL 10M):
  control p63b 55.0%; p63m (precompute only) 55.0%, identical game by game; p63d (DPLAN straight) 49.5%;
  p63dw (DPLAN walking) 51.5% (mazes 58 vs control 56, open 45 vs 54). Walking beats straight-line planning by 2, but
  the opening planner still loses to none. Not adopted; the precompute stays as infrastructure (cluster for A2_PLANSEL).
- Precompute uses, same 200-game set (control 55.0): DPLAN walking own-half to round 100 (A2_DP_OWNHALF, A2_DP_UNTIL
  100) 46.0; with A2_DP_MULT 1.5 49.2; DPLAN on maze maps only (A2_DP_MAZEONLY) 56.0 (open maps = control, mazes +2);
  contested groups (enemy spawn nearer on foot) before round 150 x0.7 (A2_MP_CONTEST) 48.2, x1.3 50.5. Any change to
  m62's tuned group scoring or opening loses; none adopted (maze-only +1 is within noise). The precompute's payoff left
  to test: the plan selector (per-cluster knobs).
- 27 Oct, requested re-test (lab, vs v61_c3 + b5_c3, mirror control on the same games, 2 workers beside the search):
  100 games (13 official + 12 unused maze maps x 2 sides x 2 opponents): control p63b 45.0, p63dw (DPLAN walking)
  54.0, p63L (A2_LOCKAWARE) 45.0, p63all (DPLAN walking + MAPPRE + LOCKAWARE) 53.0.
  All 70 official maps x 2 sides x 2 opponents (280): control 50.5, p63dw 51.2, p63L 49.1 (games vs v61_c3 identical
  to the control: the lock path almost never fires).
  Pooled over the three sets (580 games): DPLAN walking 51.8 vs control 51.1 (+0.7); LOCKAWARE (380) 48.0 vs 49.1.
  Neither clearly wins -> no real-engine run; best bot unchanged (v61 / m62).

## E62 (27 Oct) - team opening schedule from the draft fuel (A2_SCHED, v4/bots/p63 src/sched.h)
- Real-engine fuel (A2_FUELPROBE, cuts): draft turn 1 9.99M; draft turns 2-5 (final pick included) 100k each; champion
  turn 1 185k, later 100k. So the schedule is searched on draft turn 1, before our lineup is known (slots get the
  average stats of the 12 champion designs).
- Model: walking distances from the A2_MAPPRE precompute (spawn + group-to-group, unreachable groups out), 1 tile a
  round, camp health/strength from the camp designs, crew 1-3 sized so each member takes <= 60% of its health, capture 5,
  group respawn timers, value = gems + 0.1 x gold, contested groups (enemy spawn nearer on foot) x 0.7. Search: up to 48
  randomised greedy rollouts + 1,500 local moves (swap, change group, change crew, drop, insert), fuel floor 2.5M.
  Output in the DPLAN step format; champions follow it (value x A2_DP_MULT), drop it while an enemy is within 6 or
  health < 50%. Knobs (lab.h now 56 slots; 48-54, 0 = defaults): horizon, follow, lateness, gold weight, contested
  penalty, max crew, rollout noise. Real engine: search stops at the floor (2.48M left on big-world and
  yellow-brick-road), no errors.
- Diagnostics (sched_diag.js, 65 games vs v61_c3, 35 official + 30 maze maps, round 200): banked gems 47.7 -> 59.8,
  carried gems + 0.1 gold 44.1 -> 41.7 (total +11%); champions follow their step on 60% of step turns.
- Lab wins vs v61_c3 + b5_c3, mirror control on the same games: 100 (13 official + 12 maze) 45.0 -> 53.0; 280 (70
  official) 50.5 -> 52.3; 200 (25 maps_test4 + 25 maze) 55.0 -> 52.8; pooled 580: 51.1 -> 52.6 (+1.5, not clear).
  Knob screen on the 280 official games (default 52.3): follow x2 45.2, follow x0.5 50.2, horizon 300 46.2, horizon 120
  49.1, lateness x2 53.6. Following harder or longer loses. Better early economy, no clear win -> no real-engine run.
  Next if pursued: add knobs 48-54 to a black-box run (knob_ctx.js needs NK 56) after the specialist searches.

## E63 (27 Oct) - k64: every part of the play tunable (79 new knobs), parity, block rotation (v4/bots/k64, running)
- k64 = m62_c1 + knob slots 64-142 (lab.h kKnobs 160; 48-63 left to the opening schedule; table in agent2/KNOBS.md).
  Read once per game into kx (common.h, kx_init in bot.cpp), a few multiplications a turn. Blocks: F 64-88 fights by
  champion group (aggression, danger time-to-die, fight-verdict bias for Vendetta / Vesper / Marcella / Varg / Heart of
  Ruin / Ren / other; threat retreat, carrier risk, outnumbered radius, channelling targets), C 89-112 camps (distance
  cost, group kinds, map side, contested, stickiness, help calls, crew size, camp net, big job, duo, staging, back-off,
  overhead, early gold), K 113-128 banking (bag by group, phase and score race, threatened banking, safe route, rhythm,
  bank while waiting, end-game distance), S 129-142 shopping and wards. Old slots: A 0-23, B 24-44.
- Parity: k64 vs m62_c1 mirror, 70 games (20 official + 15 maze x 2 sides): 50.0%, gem margin 0. Paired vs v61_c3 +
  b5_c3 (100 games): baked knobs and a written 160-knob vector both 0 games different from m62_c1.
- Wiring sweep (each new knob +1, 20 games vs v61_c3): 71 of 79 change games. Knobs 97-98 (map side) were dead: the
  enemy-spawn field was only built with the territory / numbers features on; now also when 97 or 98 is set (parity
  re-checked: 0 of 100 differ; 97-98 then change 20 of 20). No effect in 20 games, situational: 88 channelling targets,
  106 big job (dominant-group maps only), 116-117 Heart of Ruin / Ren bag, 123 threatened-bank bag, 137 finish-reset
  deferral, 140 ward-ahead aim.
- Start check (paired): g9 (paused knob_m62 search) vs v61's knobs: 25 maze test + 25 maps_test4 x 2 x 2 (200)
  -2.5 +- 4.2, official 70 x 2 x 2 (280) +2.3 +- 4.0: level. Blocks 0-47 start from g9 as planned, new blocks from 0.
- Rotation (agent2/lab/rot_all.js; knob_rot.js = knob_ctx.js with a block mask, knob_val.js = paired validation):
  per block 15 generations, 12 pairs, sigma 0.25, lr 0.10; per generation 10 official + 10 maze (maps_maze) + 5 open
  (maps_new4) maps x 2 sides vs v61_c2 + b5_c2 = 100 games per candidate. Candidate = mean of generations 8-15; kept
  only if it beats the block's start by >= 1 point on 200 held-out games (25 maze test + 25 maps_test4, fresh slice per
  block, vs v61_c3 + b5_c3, same games). maps_test4 150-199 and maps_real200b stay for the final checks.
- Block F (fights by champion group), stopped at 8 of 15 generations on the user's word (weak): training centre win
  50, 40, 54, 58, 57, 52, 50, 46 (no trend); biggest moves Marcella aggression -0.35, "other" danger ttd -0.29, threat
  retreat +0.20. Mean of gens 4-8 vs start, 200 held-out games (25 maze test + 25 maps_test4 vs v61_c3 + b5_c3):
  51.0 vs 52.5 (-1.5 +- 3.8) -> reverted (rot1_cur.txt unchanged).
- Rotation ended on the user's word after block F (blocks C, K, S, A, B never run). Best bot unchanged (v61 / m62);
  k64 (parity-exact with m62_c1, 79 extra knobs) and the tools stay for later use: resume with
  node agent2/lab/rot_all.js rot1 C,K,S,A,B 15 4 1.0 (F is marked DONE).
- E61 specialist plans, held-out check (27 Oct): knob set per cluster = average of search gens 8-15 (plan_c<k>_avg.txt),
  played by p63b through H2H_KNOBS against its own baked knobs on the same games, cluster test maps (clusters/c<k>_test,
  25 / 20 / 25 maps x 2 sides) vs v61_c3 + b5_c3: c0 small-open 49.0 -> 48.0 (100); c1 small-maze 46.2 -> 51.2 (80);
  c2 large-open 54.0 -> 44.5 (100); pooled 50.0 -> 47.7 (280). The per-cluster searches (vs v61_c2 + b5_c2, 25 training
  maps a generation) do not carry to held-out maps and fresh-seed opponents (as E56); c3 (large-maze) still running.
  Cluster 3 search stopped after 2 generations (plan_c3.tsv) on the user's rule "stop anything with no or weak results":
  the selector idea (A2_PLANSEL) is dropped; p63 keeps the switch off.

## E66 (27 Oct) - the draft precompute all game (A2_MP_LATE, v4/bots/p64 = p63sc + switch): no gain
- Champions now keep the draft summary's walking distances (mp_dA / mp_dE, bot.h). A2_MP_LATE bit 1: contested-middle
  test by walking distance; bit 2: territory / numbers-invade margins from turn one; bit 4: lab knobs 55-58 (55 blend of
  walking place into the middle test, 56 their-side groups x exp(-0.5k), 57 our-side x exp(0.3k), 58 scale from
  round 250). lab.h kKnobs 64.
- Parity: p64 (0) and p64k (4, knobs 0) replay p63sc exactly (100 games, 55.0%, same margins).
- Fixed switches, 100 games vs v61_c3 + b5_c3 (13 official + 12 maze maps): p63sc 55.0, bit 1 47.0, bit 1+2 with
  APEX_TERRITORY 0.8 51.0, bit 1+2 with NUMBERS_INVADE 2 44.0. Walking-distance middle loses (knob 40 was tuned on
  the straight-line middle).
- Search: knob_rot.js on p64k, block 48-58 (opening schedule + late precompute), 12 gens, v61_c2 + b5_c2, maps
  official 10 + maze 10 + new4 5 per gen (agent2/lab/p64k_rot.tsv / .log). Validate on c3 seeds.

## E63 (27 Oct) - platform match groups 02acbb16 / a6d76dcb / a9948bc0: 11 distinct games, 0 wins (agent2/MATCH_ANALYSIS_E63.md)
- Our bot (economy-first V59_ITEMS 2 build) buys 0 stat shards in 8 of 11 games; the opponent stacks Bruiser / Power
  (56-402 stat shards; their Vesper 19-26 Bruiser emblems). Power gap by round 200, then every fight is lost.
- Deaths us 5-41 (median 10) vs them 0-9; mostly alone / outnumbered, in our own third and the middle; we play spread
  (nearest ally 5-11.5 tiles vs their 3-8). Gems lost on death up to 270 a game; banked 0 on contest and road-of-riches.
- They keep altar locks on our altars 37-90% of the game on anvil / contest / breadcrumbs / reverse-spiral; we placed
  0 locks in all games. Fuel is not a cause: later turns use 23-59k of 100k, 3 turns at the cap in ~43,000.
- Item search (item_champ.js) paused after Ryth (best +1.9; all openings tested against our own economy-first family).

## E64 (27 Oct) - E63 fixes tested against v61_c3 + b5_c3 (lab, mirror control on the same games; fix_screen.sh)
Builds (from p63, A2_PLANSEL 0): p63it1 V59_ITEMS 1 (Treasure, Jungle, Bruiser hp, Durability, then Bruiser stacks),
p63it3 V59_ITEMS 3 (Prospector, Jungle, Durability, stacks), p63it4 V59_ITEMS 4 (new: Jungle only, stacks), p63vf
V60_VESPER_FIRST 1, p63ts APEX_DET_TS_BUDGET 85000; knob fixes on p63b: cohesion k11 +4 / k38 -1, retreat k1 +1.5 /
k0 -1, smaller bags k4 -1.5, prelock k42 +0.5.
100 games (13 official + 12 maze maps; control 45.0): Vesper first 53.0, retreat 50.0, items-1 48.5, search fuel 48.0,
prelock 46.0, cohesion 44.0, items-4 42.0, items-3 41.0, smaller bags 40.5. Mixes: V+R 49.0, V+T+R 49.0, V+I 42.0,
V+I+R 41.5, V+I+T+R 39.0, +prelock 38.0.
280 games (70 official maps; control 50.5): Vesper first 48.2, retreat 50.5, items-1 48.8, search fuel 51.2, V+R 40.0.
None beats the control against our own bot family; the 100-game gains were noise. The E63 losses come from a
stat-stacking, grouping, locking opponent that v61 / b5 do not resemble, so these tests cannot show whether the fixes
help against it (the sparring-bot step was skipped).

## E65 (27 Oct) - how the platform games were lost, and fixes against a stronger opponent
- Turn-by-turn (actions.js, g10 reverse-spiral/arena 4v3): champion damage traded is even to round 300 (2471/2468,
  3492/2868), then their stats run away and they out-damage us 2-17x. Each death = 60 rounds out + 100 gold + bag to
  them: g10's 41 deaths are ~2,460 champion-rounds (~40% of our time). Example deaths: Vendetta at 400 hp walks toward
  them and is poked by their ranged Vesper for 18 rounds without leaving or hitting back; Marcella stays 10 rounds in a
  bush 1-2 tiles from three enemies.
- All 11 games (bushdeath.js): our 184 deaths vs their 49; last 8 turns before our deaths: 34% dealt no champion
  damage, 26% moved <= 2 tiles, 18% were under 50% health 8 turns earlier, 12% sat in a bush.
- Lab mode log (A2_MODELOG, p63ml; mode_stats.js): the last mode before 75% of our deaths is "flee" (323 / 428 vs
  v61_c3, 221 / 367 vs op1). Flee deaths (295): flight starts at median 30% health (quartile 17%), median 1 enemy and 0
  allies within 5 (alone in 54%), median walk home 24 tiles, death after a median 5 turns of fleeing.
- Stand-ins: op1 (p63 + V59_ITEMS 1 + V60_VESPER_FIRST) loses to p63b 41.4% -> copying their build and draft does not
  reproduce them. H2H_BOOST (lab_h2h.js: opponent gets g sandbox gold a turn): +0.25 gold a turn turns 50% into ~18%
  either way round (symmetric); a small income edge decides these games.
- Fixes vs v61_c3 + b5_c3 boosted 0.25 (140 games, official 0-34; control 20.0): items-1 17.5, items-3 22.1, items-4 8.6,
  Vesper first 16.4, search fuel 17.9, retreat 13.6, retreat2 (k1 +3, k3 +2) 21.4, danger ttd 19.6, cohesion 21.4,
  smaller bags 22.9, prelock 22.9, A2_LOCKAWARE 19.3; stacks 14.3-16.1. Bags + prelock: 22.1 boosted / 56.1 plain
  (control 50.4) on maps 0-34, then 21.4 vs 26.4 boosted and 51.2 vs 53.2 plain on unseen games -> noise.
- Conclusion: no knob or switch-level change helps, with or without the income handicap. The losses come from the
  structure of play (champions farm alone far from home and run too late; an income edge snowballs) and need a design
  change, not a setting.
- Search result (12 gens, 81 min): knob 56 rose steadily to 0.58 (their-side groups x0.75), 58 +0.26 (stronger after
  round 250), schedule knobs 48/49 -0.23/-0.38, 50 +0.21; centre win 40-56% by map sample, no trend.
- Validation vs v61_c3 + b5_c3 (480 games: 25 maps_test4 + 25 maze test + 70 official, both sides): control (knobs 0 =
  p63sc) 52.5, final knobs 51.7, gens 9-12 average 52.4. No gain: the search drift was noise. No real-engine run;
  the draft precompute (opening and all game) is exhausted against our own bot family.

## E66 (27 Oct) - structural fix: escape-distance retreat + squad farming (A2_SQUAD, v4/bots/p63)
- Bit 1: in danger also while time to death < min(walk home, A2_SQ_CHASE 12) x A2_SQ_MARGIN (health < 90%). Bit 2: a
  group > A2_SQ_HOME (14) walking tiles from home with no teammate within A2_SQ_ALLY (8) of it (seen, or claiming a
  nearby group) is worth x A2_SQ_LONE (0.4). Existing switches also tried: APEX_PAIR 2, APEX_SQUADS 2, NOVA_DUO on all
  maps (NOVA_DUO_MAPS 0).
- Behaviour (mode log, 35 official games vs op1): our deaths 382 -> 279 (-27%), flee deaths 295 -> 208, wins 18 -> 23.
- Wins, same games, vs v61_c3 + b5_c3 boosted 0.25 gold a turn (official 0-34, 140; control 20.0): escape 15.0, squad
  18.6, both 20.4, pair 13.6, two squads 7.1, duo 25.0, mild both (x0.7 beyond 20 tiles) 21.1, mild escape (margin 0.7)
  19.3, duo + escape 18.6, duo + mild both 17.5. Plain (official 35-69 + 25 test4 + 25 maze, 340; control 53.2):
  escape 54.3, squad 47.1, both 44.1, duo 53.2, mild both 50.6, mild escape 55.6, duo + escape 54.3, duo + mild 50.6.
  Confirmation, boosted, unseen games (official 35-69 + maze 25-49, 240; control 22.1): duo 22.1, mild escape 17.9.
- Result: fewer deaths, no more wins: keeping champions near home or a teammate costs as much farming as it saves in
  deaths, against v61 / b5 with or without the income handicap. Not adopted. The lab stand-ins may not represent the
  platform opponent; a real test needs platform matches with the candidate (the user's submission).

## E67 (27 Oct) - two more platform match groups (204a14f3, e8437625): 9 new games, 0 wins (opponent B)
- Opponent B drafts Tavi / Vendetta / Marcella / Ryth (+ Vesper at 5); build Monster / Durability / Treasure / Jungle,
  then Bruiser (their Marcella focus 368-830, Ryth / Vendetta str 300-450). Deaths about even (us 2-17, them 1-21),
  but they out-farm us from round ~400: we often lead early (h08 341-154 at round 400, h01 78-0 at 100) and lose
  343-794 to 864-999. Our items: the same six-emblem economy opening; several champions end with no stat emblems.
- Road-of-riches (h04, and g09 vs opponent A): banked 0 until round 800 while carrying 113-192; no altar locks.
  Real-engine p63b vs v61_c3 on it banks normally (49 at round 200, 935 at the end) but carries 300-480-gem bags:
  the long spiral walk to the central altars makes carriers hold big bags, which the platform opponents kill.
- Both opponents: 2-4 emblems then Bruiser stats by round ~300; ours six economy emblems first. Power-curve build
  V59_ITEMS 5 (new: Monster, Durability, Jungle, then the stat stacks) and p64 (V59_ITEMS 5 + A2_SQUAD 1): boosted
  (official 0-34 + maze 25-49, 240; control 18.3) items5 17.5, p64 15.8; plain (340; control 53.2) items5 48.8, p64 48.1.
- Conclusion: the lab bench (our own bot family, with or without the gold handicap) cannot show gains against
  platform-style opponents; every change aimed at them tests neutral or negative here. Candidates packaged for
  platform match groups (not submitted): v4/submissions/p64_engine4.zip, p63sq3_engine4.zip (A2_SQUAD 3: deaths
  -27% in the lab), p63sq1_engine4.zip (A2_SQUAD 1).

## E68 (27 Oct) - turn use, solo farm benchmark, farm-speed search
- Turn use from replays (actions.js; live turns): vs opponent B us move 55% / stationary 37% / at spawn 4% / fighting
  champions 4%, dead 11% of champion-rounds; them 55 / 35 / 5 / 5, dead 8%. Vs opponent A we are dead 24% (them 6%).
  Opponent B does not use its turns better; it gets more per turn (stats -> faster camp kills) and survives fights.
- Solo farm benchmark (agent2/lab/farm_bench.js vs v4/bots/idle4, rounds to 1,000 banked, 70 official x 2): p63b 934,
  v61 920, b5 942, items-5 963, items-1 992, items-3 957 (economy emblems help solo farming in our bot). Never finished
  alone: reverse-spiral and shortcut (our team flees from the idle enemies standing on their nearby spawn: idle-bot
  artifact; vs v61 these maps finish in 1,358-1,540 rounds), stampede and elk-arena (long wait-respawn / stage).
  Held-out (60 test4 + 40 maze test): 1,088 rounds, 19 / 200 unfinished: maze-generator artifacts (maps with 14-28 gems,
  or only 4 single high-health camps -> "nofarm" at spawn all game).
- Farm-speed search (knob_ctx.js ES_SCORE=farm, p63b vs idle4, 188 maps, 15 gens, 50 games per candidate): candidate
  gains 1-7%; average of gens 8-15 (farm_s1_avg.txt): held-out farm 1,088 -> 1,075 rounds (noise); h2h plain 51.3
  (control 53.2, 340), boosted 17.9 (control 18.3, 240). Not adopted.
- Overall (E61-E68): no setting, switch, item plan or knob search beats m62 / v61 in our lab by more than noise; the
  bot is at a local optimum for its design, and the lab bench cannot see what beats the platform opponents.

## E69 (27 Oct) - learned fight / flee / regroup from engine counterfactuals (fight_cf4.js, fight_fit.py, fight_fit2.py)
- Bot side (v4/bots/p63): fight_features (24 inputs at a contact turn: own health / stats / bag, enemies and allies
  within 6 with health and damage, threat, time to death / kill, the bot's own verdict, walk home, round, sightings),
  recorded by lab kinds 4 / 5 into lab::fight_feat (export lab_fight_feat); A2_FIGHTNET (off) runs fight_net.h at
  contact turns and commits a predicted gain > A2_FN_MARGIN for A2_FN_LEN rounds (fight / run / regroup to the nearest
  ally). host.js: labCtl.team (intervene only on our team), H.fightRead.
- Data: p63fc (team 0) vs v61_c2 / b5_c2, half with the 0.25 gold handicap for them; from a random round the first
  contact turn (enemy within 4) is played 4 ways (own verdict, forced fight / run 5 rounds, regroup 5 rounds).
  Run 1: 2,542 rows, outcome 100 rounds; run 2: 2,000+ rows with outcomes at 10 / 25 / 50 / 100 rounds
  (fcf1_h100.jsonl, fcf2.jsonl). About 100 samples a minute on 5 workers, 81% usable.
- Mean change vs the bot's own verdict (100 rounds): fight +0.5 / -1.5, run -1.3 / -3.7, regroup -3.9 / -4.5 gems;
  hindsight-best per decision 4 (10 rounds), 10 (25), 15 (50), 28 (100). Held-out correlation of predicted vs real
  change, 5 folds by map, every horizon and action: -0.07 to +0.02 (deaths in 100 rounds: <= 0.14). Policies on held-out
  maps scored on the real 100-round change: -1.5 to +0.5 (+- 1-1.7) gems a decision at any threshold; win share +-0.009.
- Conclusion: from what a champion sees, the bot's own verdict is as good as forced fight / run / regroup; the large
  hindsight differences are chaotic divergence, not learnable decision quality (as E30). Not adopted.

## E70 (27 Oct) - learned strategy switcher (A2_MACRO, RL policy search; macro_es.js)
- Bot (v4/bots/p63, A2_MACRO, off): every A2_MACRO_EVERY (50) rounds each champion computes global features (bias,
  bank lead / 200, round / 1000, behind by 100+, large map, maze map; same for the whole team) and picks one of four
  48-knob styles (macro_presets.h: 0 = v61 knobs, 1 cautious, 2 aggressive, 3 farm-search knobs) by weights x features
  (lab::macro_w, export lab_macro_w; A2_MACRO_W bakes). Zero weights = style 0: parity with p63b exact (40 games, same
  margin). host.js H.macroW; lab_h2h.js H2H_MACROW.
- RL: evolution strategies over the 24 weights (macro_es.js: 10 antithetic pairs, sigma 0.5, lr 0.2, rank update),
  league v61_c2 / b5_c2 x plain / 0.25-gold handicap, 13 fresh training maps x 4 x 2 sides = 104 games per candidate,
  20 generations (90 min). Centre win per generation 23-43% with no trend; the policy drifted to "farm" almost
  everywhere (aggressive on large maps / when behind early).
- Held-out (fresh seed v61_c3 + b5_c3, same games): plain 340 (official 35-69 + test4 25 + maze 25): untrained 53.2,
  final 51.0, average of gens 11-20 51.2; boosted 240 (official 0-34 + maze 25-49): 18.3 / 17.1 / 18.3. No gain.
- Conclusion: switching between the existing styles by game state does not help; the styles are within noise of
  each other against these opponents (consistent with E64 / E68), so a selector over them has nothing to gain.

## E71 (27 Oct) - altar raid and carrier hunting (A2_RAID, v4/bots/p65 = p63 + A2_PLANSEL 0 + raid)
- A2_RAID bits: 1 the slot-0 champion wards the enemy's banking altar (the altar where enemy tributes were seen most,
  else the one nearest their spawn) when within A2_RAID_DETOUR 8 and keeps that ward all game (wards are permanent and
  personal); 2 a tribute of 40+ gems in sight with no other enemy within 6 goes to deny_tribute (hit the channeller,
  lock-cancel on our last turn, take its bag); 4 lock that altar when passing with a lock; 8 carrier hunt (bag 50+,
  not on its spawn, our numbers >= theirs near it, kill within 5 turns, risk < 70% of our health); 16 answer only with
  a lock in hand; 32 buy the lock before saving for items. Diagnostics: agent2/lab/raid_stats.js (A2_RAIDLOG).
- Parity: p65 (0) = p63b, 57.0 on the same 100 games (13 official + 12 maze vs v61_c3 + b5_c3).
- 100 games: ward + answer (3) 53, ward on any detour (3, detour 60) 48, + prelock (7) 54, carrier hunt (8) 54,
  3 + 8 55, lock-only answers + lock first (51) 50, + prelock (55) 51.
- The features fire: official maps (20 vs v61_c3) altar ward placed in 16-17 games, 1,100-1,800 enemy tributes of 40+
  seen, 160-420 answers, 15-22 lock cancels, carrier hunts 182; maze test maps rarely (ward in 4 of 15).
- Conclusion: denying v61 / b5 tributes and hunting their carriers costs more farming than it takes from them; no
  variant beats the control. Not adopted. (E40's permanent ambusher and carrier hunter lost the same way.)

## E72 (27 Oct) - next-camp choice: top teams vs us (tools/next_camp.py, agent2/lab/dec_lab.js; A2_TOPFIX in p65)
- Data: 9,193 next-camp decisions of top teams from 485 decoded ladder games (replays_db/dec, 17 maps with mapinfo)
  and 1,220 of p63b vs v61_c3 on the same 17 maps in the lab (dec_lab.js writes lab games in the decode format).
  Decision = after a capture, bank or respawn; label = the group captured next. Conditional logit over all groups:
  log walking distance, log gems, gold, respawn wait on arrival, side (walk margin), middle, allies / enemies within 5,
  a teammate nearer, bag x distance, hurt x enemies, round x side.
- Held-out top-1 (games split): top model 0.313 (nearest group 0.246, gems/distance/wait rule 0.238); ours 0.350.
- Coefficients top vs ours: dist -1.35 / -1.33, gems +0.75 / +1.25, gold -0.33 / -0.38, wait -0.84 / -1.30, side
  +0.53 / +0.65, mid +0.26 / +0.09, enemy5 -0.01 / -0.13. Top teams weigh gem size less and a respawn wait less.
- A2_TOPFIX: value x exp(K (-0.50 log(1 + gems) + 0.46 wait / 20 + 0.17 mid)), in the pruning bound too. 100 games vs
  v61_c3 + b5_c3 (control 57.0): K 0.5 43.5, 1 38.0, 1.5 16.0; K -0.25 57.0, -0.5 38.0, -1 36.0. Both directions lose:
  our camp choice is at the optimum against our own bot family. Not adopted.

## E73 (27 Oct) - what decides games: resource and kill exchange rates, gold valuation, rush, flee/stand (p63b / p65)
All on the same 200 games (25 official + 25 maze test maps x 2 sides, vs v61_c3 + b5_c3; p63b control 53.5).
- Gifts (lab_h2h.js H2H_GIFT=round:gold:gems, once to each of our champions): +150 gold at round 100 84.5, +300 gold
  97.5, +30 gems 67.0, +60 gems 74.5; at round 400: +150 gold 76.8, +30 gems 64.5. One gold is worth about 0.5-0.8
  gems in wins (camp choice uses 0.72 before round 250, then 0.18; 0.10 on unseen maps).
- Free kills (H2H_KILL=round:n, credited to us): 1 at round 100 71.0, 1 at round 300 67.2, 2 at round 100 80.5.
  The game snowballs hard on early resources: one kill or ~100 gold per champion early decides most games.
- Gold valuation (structural): early x4 until round 600 57.0, all game 47.2, early x6 56.5, official value on unseen
  maps 55.5 (all within noise except all-game, which loses). Gifts are free; in-game gold trades against gems.
- Item facts (SDK 4.0.0): every shard adds its stat whatever the family; Bruiser and Greed give 1.4x the stats per
  gold, Power 1.2x; passives: Treasure +10% gold, Prospector 0.25, Capture 3, Collectors 0.01, Tribute 0.33,
  Hunter 50, Skirmish 0.05, Monster +15% camp damage, Jungle -30% camp damage, Durability -10% damage.
- Opening rush (NOVA_RUSH_UNTIL, never tested on engine 2.0): 60 rounds 48.5, 100 42.5, 150 37.5. Probe
  (early_stats.js, 50 official games): rush60 raises enemy deaths by round 100 from 0.58 to 1.20 but our banked +
  carried gems fall from 44 to 18 and our stats lag: the farming lost outweighs the kills.
- Deaths (dec_lab, 34 games p63b vs v61_c3): about 12 per team per game, almost all with an enemy within 4, mostly
  after round 300; even between the teams.
- Flee / stand switches on engine 2.0: APEX_STAND2 3 (stand and fight when caught) 25.5, NOVA_FLEE_HIT 53.5,
  APEX_ESCAPE_SEARCH 55.5, all three 36.5. Fleeing is right; standing when caught is a disaster.

## E74 (27 Oct) - opportunistic gang kills and power-based early retreat (A2_GANG, A2_LANCH in p65)
Same 200 games as E73 (control 53.5). early_stats.js probes on 50 official games vs v61_c3.
- A2_GANG (an enemy within 6 with no other enemy seen within 7, off its spawn, a teammate within 5 of it, dead in <= 4
  turns, its damage < 60% of our health meanwhile -> attack it): probe unchanged from control through round 400
  (enemy deaths 0.60 / 1.28 / 3.14 at rounds 100 / 200 / 400 vs 0.58 / 1.32 / 3.40); 46-50% on the probe games
  (solo at <= 2.5 turns, reach 9: same). The situation is rare and the existing fight logic already takes it.
- Early deaths (A2_MODELOG, 70 games, rounds <= 200): 111 deaths, 89 while fleeing; 72 of those outnumbered when the
  flight began (2-4 enemies vs 0-2 allies), median flight start 32% health, 4 turns, 23 tiles from home. Our bot dies
  more early than v61 (0.88 vs 0.58 by round 100; 1.70 vs 1.32 by round 200) and banks less by round 200 (59 vs 74).
- A2_LANCH (leave at any health when the enemies' (health sum x damage sum) near us is k times ours): k 1.5 all game
  49.8, k 2 50.0, k 1.5 until round 300 53.5; NOVA_EARLY_SAFE_UNTIL 200 (flee when outnumbered by one) 55.5.
  Neutral: the bot's results barely move with its fight rules.

## E75 (27 Oct) - how the platform winners beat us (20 distinct lost games, rounds 0-300) and copying it
Tools: agent2/lab/platform_decode.js (replays -> per-round JSON in platform_matches/dec), tools/platform_study.py,
tools/platform_farm.py. Team 0 = us.
- Rounds 0-300 per game, us vs them: deaths 3.4 / 1.9, kills 1.9 / 3.4, kill gold 145 / 301, other gold 745 / 932,
  gems gained 134 / 262, banked at 100 / 200 / 300: 19 / 32 / 80 vs 49 / 106 / 191; strength sum at 300 260 / 306.
  Nearest teammate 6.3 / 4.8 tiles, a teammate within 3 42% / 59% of the time. Their items: Treasure + Jungle first,
  then Bruiser / Power; ours Prospector + Jungle + Durability.
- Farming: the same share of time at camps (49%), captures by round 100 3.0 / 3.2, by 300 9.4 / 12.2; gems per
  capture 11.6 / 19.6 (we split big groups between two champions; they take them alone).
- The decisive games: an early fight (rounds 19-75) where they arrive with 4-6 champions at full health against our
  1-4 (03-24610ae3: 6 vs 3, we lost 5, they 0; 01-609a1e2d: 5 vs 4 at a 343-gem group, then took it and banked 343
  by round 100; 03-ccd2c001: took 168 + 77 after an early kill). On ordinary maps both teams solo-farm 7-gem clusters
  at the same pace.
- Copies in p65, same 200 games as E73 (control 53.5, parity 53.5): A2_PACK (every champion works the leader's group)
  until round 100 46.0, 200 38.5, all game 9.8; pairs (A2_PACK 2) until 200 46.2, all game 22.8; pack + gang kills
  37.8; A2_JACKPOT (whole team on the map's biggest group early) 43.5, share 0.15 37.0, until 600 41.5. Probe of the
  200-round pack: our deaths by round 200 halve (0.86 vs 1.70) but banked falls 59 -> 36.
- Conclusion: against v61 / b5 (which spread out and contest little early), concentrating costs more farming than it
  saves. The platform winners' concentration pays against our platform bot; whether it pays against the ladder can
  only be measured there.

## E76 (27 Oct) - farm first, then pack and attack (A2_RUSH_FROM / A2_RUSH_LEAD / A2_RUSH_ITEMS, A2_PACK from a round; p65)
Same 200 games (control 53.5). The rush pack (leader marches to enemy-side camps within 20 of their spawn, followers
within 2, aggression x1.5) from a start round: 400-700 29.5, 600-900 25.8, 300-end 7.0, 500-end 10.0; from round 150
once a champion owns 15 shards' worth 16.5; from round 200 while 50+ banked gems ahead 32.5. Pack farming (every
champion on the leader's group) 400-700 31.5; pairs from 400 22.8.
- Packing costs at every stage of the game: capture rewards are split among the champions present, so team income
  scales with the number of camps worked at once, and v61 / b5 leave when outnumbered by two (APEX_OUTNUMBERED 2), so a
  pack gets few kills to make up for it. Not adopted.

## E77 (1 Nov) - the user's v81 (v74 HOME_SIDE + per-map ladder tables) in this workspace
- Source from v81_home_ladder_hybrid.zip -> v4/bots/v81 (A2_LAB build on v61's knobs; LADDER_TABLES 1, LADDER_HOME 1);
  builds with v4/cambc.exe. "cambc (7).exe" from Downloads is byte-identical to v4/cambc.exe (SHA-256 03ee5b8a...).
- Lab, 42 official maps (28-69) x 2 sides vs fresh-seed v61_c3 + b5_c3 (168 games): v81 110.5/168 = 65.8%
  (v61_c3 59/84 = 70.2%, gem margin +247; b5_c3 51.5/84 = 61.3%, +246). Clearly above every p63 variant (E61-E70).

## E78 (1 Nov) - GPU question and lab speed-up (agent2/lab/host.js)
- Hardware: RTX 5060 8 GB, Ryzen 5 5600XT (6 cores / 12 threads), 16 GB RAM.
- Where game time goes (lab, 1,000-round games): engine alone (idle vs idle) 20 ms a game; v81 vs v61_c3 456 ms.
  The engine is ~4% of a game: a GPU engine (even a full reimplementation) would save at most that; the rest is the
  two bots (wasm) and the host glue. GPU not useful for running games; only for training large networks.
- CPU profile (3 games): host.js 43% + 14.5% JS view creation; the hot spots were new DataView / Uint8Array views on
  every engine call (get m, get u8, b8) and subarray copies for 4-40-byte transfers (back, toE, outE).
- Fix (backup host.js.bak_e78): views cached and rebuilt only when a memory grows (detached buffer, length 0); copies
  of <= 64 bytes by a loop. Parity: 16 fixed games (v81 / b5_c3 / v61_c3 on 8 official maps) identical result and
  round count before and after. Time 9.3 s -> 7.4 s (views) -> 5.7 s (copies): 1.63x faster. Now wasm 50%, host 33%,
  other JS 15% (wasm-to-js transitions ~10% inherent).
- Worker scaling (36 games): 1 worker 19 s, 3 -> 8 s, 6 -> 5 s, 9 -> 5 s: saturates at the 6 physical cores (before
  the fix ~7 games/s; RAM, not CPU, usually limits workers to 3-5 while Chrome is open).

## E79 (1 Nov) - research read-through (World Models, Certicky 2018, Game AI Pro, ChatGPT plan, Reddit) applied to v81
- Read: World Models (Ha & Schmidhuber 2018), Certicky et al. 2018 (StarCraft strategy recognition), the Discord
  screenshot (2-ply combat search, breadcrumb pathing), the ChatGPT "MOBA bot" plan, the r/gamedev thread (layered
  stance systems, utility + hysteresis, Dijkstra/heat maps, advisors + executive), Game AI Pro chapters GAP3 14
  (scripts + game-tree search), 24 + 32 (Paragon objective graph / AI commander / one-step influence map / front line),
  25 (Lanchester combat prediction), 28 (MCTS pitfalls), 30 (hierarchical portfolio search), GAP2 30 (modular
  influence maps), GAP1 26 (tactical position selection).
- Mapping to v81: already present - threat zones and expected-enemy occupancy (influence maps), sticky targets
  (hysteresis), team claims / jobs (Paragon commander), score/race posture layer (A2_RACE, E39), learned win
  probability, skirmish simulator + tactical rollout search (tsearch, APEX_TSEARCH, off), branch-and-bound camp
  scoring (TPS-style evaluation order), learned residual nets (findings 21). Not present: opponent-strategy recognition.
- v4/bots/v85 = v81 + A2_STANCE (bot.cpp before FIRST_SAFE): each champion counts enemy champions seen deep in our
  half (place between spawn centres < 0.4, decayed 0.98/round). Bit 1 expand when none seen for 100 rounds
  (territory >= A2_ST_EXP_TERR); bit 2 defend when the decayed count > 8 (territory x 0.5, aggression x 1.15).
- Lab, official maps 28-69, vs v81 (84 games) / vs v61_c3 + b5_c3 (168 games; v81 = 65.8%):
  v85a (bit 1, 0.7) 46.4% / 66.4%; v85b (bit 2) 48.8% / 64.0%; v85c (both) 46.4% / 68.8%; v85d (bit 1, 1.0) 50.0% / 64.6%.
  All within noise. Not adopted.
- v85t1 / v85t2 = v81 + APEX_TSEARCH 1 (+ A2_TS_FIGHTONLY): 16.7% vs v81, 22.6% vs refs (lab fuel is unmetered, so
  the search always runs to its own caps). The rollout model still loses fights it predicts as wins (as findings 14).
- Conclusion: the literature's standard toolkit is already in v81; none of the untried pieces moves the lab pool.
  The measured gap (findings 20: early contact vs the dominant ladder teams) is not reproduced by any local opponent.

## E80 (1 Nov) - early-contact sparring stand-in (lab aura) and v81 variants against it
- agent2/lab/lab_h2h.js (backup .bak_e80): H2H_PROF=1 prints per-team gems held (banked + carried) and deaths at
  rounds 100-600; H2H_AURA=R:D[:from:until] - once a round each living champion of bot A takes D damage per living
  bot-B champion within Chebyshev R, credited to the nearest (kills pay B). Probes: Game_Sandbox_Buff kinds 0-2 return
  0 but change no Champion_Get stat; Sandbox_Damage rejects negative amounts (no heal). Champion_Get record: team,
  type, x, y (int32), hp, max hp, strength, focus (f32).
- Profiles (v81 view, official maps 28-69, 84 games; target = findings 20, v81 vs dominant ladder teams at r300:
  gems 117 / 230, deaths 2.4 / 1.3, ~10% wins):
  mirror v81_c2 177 / 195, 2.14 / 1.95, 47.6%; aggressive v81 copies (HOME_TERR 1.0-1.5, HOME_AGGR 1.0-1.4) die MORE
  than v81 (2.9-4.2 vs 2.4-3.0) - our fight engine cannot win early contact by being aggressive; gold boost 0.15-0.3
  wins games late (24-44%) but leaves the early profile unchanged.
  Aura 3:15 rounds 0-400 vs v81_c2 ("spar-15"): 154 / 218, 2.95 / 1.52, v81 wins 28.6% - the ladder shape.
- Screen vs spar-15 (184 games, maps 28-69 + maps_test4 0-49; v81 33.2%): FIRST_SAFE 34.2, DEATH_RETREAT 0.1 37.0,
  DEATH_TTD 1.3 35.9, HOME_AGGR 0.6 34.2, HOME_TERR 0.15 34.8, OUTNUMBERED 2 34.8 / 1 37.0, GT_SHOP 0.5 26.1,
  v85a 37.0, v85b 33.2, v85c 38.0, v85d 26.6, spA (no home side) 31.0.
- Fresh confirmation (maps_mazetest 0-99 + maps_test4 50-99):
  | bot | vs spar-15 (300) | vs v81 (300) | vs v61_c3 + b5_c3 (600) |
  | v81 | 36.8% | - | 50.2% |
  | v85a (A2_STANCE 1: expand when no enemy seen deep in our half for 100 rounds) | 45.8% | 49.7% | 53.8% |
  | v85c (A2_STANCE 3) | 46.2% | 46.8% | 50.8% |
  | e80o1 / e80dr | 36.2 / 37.2% | | |
- v85a: +9 points vs the stance-in (about 3 SE), neutral vs v81, +3.6 vs the references (about 1.8 SE). The aura has
  no real-engine equivalent, so the spar gain cannot be confirmed in cambc; whether spar-15 ranks bots like the
  ladder is untested (only one ladder profile to match). Not packaged.

## E81 (1 Nov) - Heart of Ruin, drill arena, fitted Lanchester, paranoid search, stacked candidates (bar: 56% vs v81)
- Test set "vs300" (agent2/lab/vs300.sh): maps_mazetest 0-99 + maps_test4 50-99, both sides, 300 games vs v81.
- HoR: v81 drafts it in 40-75% of games (lab_h2h H2H_PROF now logs types; H2H_DUMP writes per-game JSON).
  A2_HOR (draft.cpp, take HoR at our pick n): n=1 42.5%, n=2 47.5%, n=3 44.7% (200+100 games); + stance 43.8%.
  A2_KITFIX 29 / 31 (HoR missing-health bonus / striking dash in the fight model): 50.7 / 49.7% - those bits only
  act in the tactical search, which v81 has off.
- Drill arena (agent2/lab/drill_arena.js): both sides BOT to round R, all champions teleported into contact at the
  centre, candidate side's knobs changed from R (written into live instances - the host copies knobs only at
  instance creation), K=30 rounds, paired against the unchanged control. e81ar, 800 scenarios (maps_mazetest x
  R 120/200/300/450 x 2 sides): HoR knob 46 +2 (aggression x (1 + 0.5k x missing health)) k-d +0.033 +- 0.019,
  gem swing +1.4 +- 0.5; HoR 45 +1 +0.033 / +0.9 +- 0.6; aggression, danger ttd, cohesion, melee/ranged aggression
  within noise; danger hp, chase, HoR retreat no effect.
- Lanchester (agent2/lab/lanch_arena.js forced fights: random 1..n per side teleported 2 apart, lab intervention 4 on
  every instance for 20 rounds; 1,600 fights, 1,544 decided; lanch_fit.py): head count cv log-loss 0.522 / acc 75.6%;
  fitted per-type strengths n=1.0 0.445 / 82.5% (n 1.25 0.456, 1.5 0.467, 2.0 0.589): the linear law fits best.
  Model in v85/src/lanch_model.h; A2_LANCH2 overrides the fight verdict at P >= HI / <= LO.
- vs300 vs v81: A2_LANCH2 (0.75/0.25) 51.3%, (0.85/0.15) 51.0%; HoR knobs baked (A2_HORK 1, k45 +1, k46 +2) 51.7%,
  k46 only 49.0%; HoR + Lanchester 51.3%; + stance (e81all) 47.2%; HoR + stance (e81sh) 48.5%.
  Paranoid fight search (APEX_TSEARCH 1 + A2_TS_PARANOID 3 / 10): 26.5% (plain search 16.7%).
  vs spar-15 (v81 36.8%): e81all 40.5, e81sh 43.8, e81HRL 36.5. vs refs (v81 50.2%): e81all 50.5, e81sh 51.6.
- Opponent classifier: replays_db (517 ladder games) predates Heart of Ruin (no team fields type 12), so it cannot
  learn the current meta; platform_matches/dec has 25 current games - too few. Needs the current-engine replays.
- Nothing reaches the 56% bar; nothing packaged.

## E82 (1 Nov) - structural changes vs v81 (hunter pair, raider, positioning); knob search stopped
- Knob search (agent2/lab/knob_es48.js: ES over the 48 lab knobs incl. HoR 45-47, vs v81 on 400 training maps; e82s
  = v85 + A2_HORK) was stopped before generation 1 finished: structure first, knobs last on the winning structure.
- New switches in v85 (all default off): A2_PAIRHUNT (slots 0-1 converge on lone fresh enemy sightings off spawn,
  the nearer waits for its partner; rounds A2_PH_FROM-UNTIL, health A2_PH_HP, bag < A2_PH_GEMS), A2_RAID (slot
  team_size-1 values quiet enemy-side groups - no enemy for 30 rounds, belief map < 0.5 expected enemies within 8 - at
  A2_RD_MULT instead of the home discount), A2_TPS (position_and_attack for ranged champions too, the target counted,
  allies within 2 cover A2_TPS_ALLY of their strength). Note: v81 has APEX_POSITION 0 (exposure positioning off) and
  SPACING 0.
- vs v81, set A = vs300 (maps_mazetest 0-99 + maps_test4 50-99), set B = maps_test4 100-199 + maps_real200b 0-49:
  | variant | A | B |
  | s1a PAIRHUNT | 51.2 | 50.8 |
  | s1b PAIRHUNT range 16, all game | 49.5 | |
  | s1c PAIRHUNT hp 0.7 from 100 | 51.2 | 52.8 |
  | s2a RAID x1.0 / s2b x1.5 from 60 | 47.7 / 47.2 | |
  | s3a/b TPS without APEX_POSITION | 50.0 / 50.0 (no effect) | |
  | s3c APEX_POSITION | 49.3 | |
  | s3d POSITION + TPS / s3f ally 0.6 | 49.2 / 49.5 | |
  | s3g POSITION + SPACING | 51.3 | 44.3 |
  | s3e POSITION + TPS + SPACING (w 40) | 54.5 | 45.7 |
  | s3h / s3i SPACING_W 80 / 20 | 55.2 / 55.5 | 45.7 / 46.3 |
  | s13 s3e + s1c | 51.7 | 49.0 |
- Spacing (no ally adjacent when area-damage enemies are present) helps on maze maps (+5) and hurts on random/real
  maps (-5): map-type dependent, not a gain. Best overall: s1c hunter pair 52.0% over 600 games (+2, ~1.4 SE).
  Nothing reaches 56%; nothing packaged.

## E83 (1 Nov) - team commander: fitted Lanchester replaces v81's fight verdict, plus team convergence
- v85 A2_CMDR: bit 1 - the fight / flee verdict in handle_enemies (after every v81 rule, before the lab override) comes
  from lanch_model.h (us + allies within 7 at 25%+ health vs live enemies within 8): fight at P >= A2_CM_FIGHT, flee
  below A2_CM_FLEE (minus A2_CM_HYST while committed), flee under A2_CM_LOWHP health unless a sure kill, otherwise keep
  the commitment / v81's verdict. Bit 2 - a2_converge: go to an enemy (within 12, off its spawn) where an ally within 4
  is in contact and would lose (P < 0.6) but our healthy team within 12 would win (P >= A2_CM_CONV); bags < 40.
- vs v81, set A / set B (300 each): c1 verdict 0.55/0.40 46.5 / 40.5; c2 0.60/0.35 45.2 / 43.8; c3 verdict +
  convergence 47.0 / 41.3; c4 c3 + hunter pair 47.3 / 41.7; c5 c4 + HoR knobs 44.8 / 42.7.
- The Lanchester model predicts committed fights well (82.5%), but as the whole verdict it loses 6-10 points: v81's
  rules weigh what the model leaves out (spell cooldowns, distance and chase, bag value, flee success, camps).
- Conclusion of E79-E83: against v81 every add-on lands within +-2 and every replacement of a core v81 system loses.
  Best: s1c hunter pair 52.0% over 600 games. The 56% bar is not met; nothing packaged.

## E84 (1 Nov) - joint structure + knob search vs v81 (runtime structural switches) -> v86
- Why: E79-E83 add-ons were tested on v81's knobs; a structural change moves the best knob values, so structure and
  knobs were searched together. v85 A2_RTSW 1 compiles every E79-E83 structural change in and gates it at run time by
  lab knobs 48-63 (lab.h kKnobs 64; RTG / RTX / RTV macros in common.h): 48 stance expand, 49 stance defend, 50 hunter
  pair (51 range, 52 health), 53 raider (54 value), 55 melee positioning (APEX_POSITION path), 56 ranged positioning +
  ally cover, 57 spacing vs area damage, 58 commander verdict (59 threshold), 60 team convergence, 61 Lanchester
  override, 62 home territory scale, 63 HoR at our second pick. Parity: e84rt with every switch off (slots -0.5,
  parameters 0, HoR knobs 0) plays 40/40 games identical to v81.
- agent2/lab/knob_es48.js (ES_NK=64): antithetic ES, 16 pairs, 24 fresh training maps a generation from maps_new4 +
  maps_maze + maps_test4 100-199... note: test4 100-199 is also half of validation set B (see below), sigma 0.3,
  Adam lr 0.1; switches started at -0.15. Centre win vs v81 by 5-generation window: 50.4, 52.9, 52.7, 55.4, 50.4, 58.8.
  Centre at gen 30 (agent2/lab/e84_final.knobs): on = melee positioning +0.57, spacing +0.64, convergence +0.27,
  Lanchester override +0.30; off = commander verdict, ranged positioning, HoR draft, raider, hunter pair, stances.
  10 more generations (lr 0.07; e84b_es): windows 59.6 / 59.8 (plateau); centre keeps only positioning + spacing.
- Validation vs v81 (300 + 300 games):
  | centre | set A (mazetest + test4 50-99) | set B (test4 100-199 + real200b 0-49) | total |
  | gen 30 | 57.3% | 63.7% | 60.5% (363/600) |
  | gen 40 | 62.5% | 50.7% | 56.6% |
  Caveat: set B's test4 100-199 maps were in the training pool (24 of 400 sampled per generation); set A was never
  used in training: gen 30 is 57.3% there.
- v86 = v85 + A2_RTSW 1 + A2_KNOBS = the gen-30 centre (baked; identical to e84rt + knobs, 115/200 on mazetest).
  vs v61_c3 + b5_c3 (600): 53.1% (v81 50.2%).
- Clean maps (never in training or validation): v86 vs v81 maps_real200b 50-199 56.0% (300), maps_real250 58.3% (300);
  with set A: 515/900 = 57.2%. Official ladder maps (v4/maps, 140): 45.7% - LADDER_TABLES per-map knob sets were fitted
  to v81's knobs and clash with v86's.
- v86h = v86 + A2_HYB 1 (recognised ladder maps: v81's knobs, switches off, table on top): official maps 52.1% (90/140
  games identical to the v81 mirror: the tables recognise only part of the 70 maps), maps_real250 58.3%.
- NOT yet done: real-engine confirmation (manifest must sit in v4/ - paths resolve from the manifest's folder; use
  clean maps only: maps_mazetest, maps_real200b 50-199, maps_real250, official). Not packaged.
- Real engine (cambc run-batch --release, fuel metered; manifest v4/.m_e86h.txt, bench_out/e86h): v86h vs v81
  unseen maps (maps_mazetest 0-59 + maps_real200b 50-109, both sides) 137/240 = 57.1% +- 3.2; official ladder maps
  (70, one side each) 30/70 = 42.9% +- 5.9. All 310 games ran, 0 failed.
- Packaged: v4/submissions/v86h_engine4.zip (src/ only, like earlier zips; rebuilt from the zip = byte-identical
  bot.wasm). Not submitted. Caveat: worse than v81 on the current ladder map pool - the hybrid keeps v81's play only on
  maps the ladder tables recognise; the rest of the official maps get v86's knobs, which lose there.
- Real engine, official ladder maps, 210 more games (v4/.m_e86h2.txt, bench_out/e86h2: the 70 missing sides vs v81 +
  both sides vs v81_c2): 104/210 = 49.5%. All official games (280): vs v81 both sides 71/140 = 50.7%, vs v81_c2 63/140
  = 45.0%; total 134/280 = 47.9% +- 3.0. On the ladder pool v86h is about even with v81 (the first 70 at 42.9% were
  partly noise); its gain is on unseen maps (57.1% real, 57.2% lab).
- 50 more ladder-map games vs v81_c3 (NOVA_SEED 3; v4/.m_e86h3.txt, bench_out/e86h3, 25 maps x 2 sides): 27/50 = 54.0%
  (team A 17/25, team B 10/25). All real-engine ladder-map games: 161/330 = 48.8% +- 2.8 - even with v81.

## E85 (1 Nov) - ladder + unseen joint search; Khaos ideas; isolation switches coded
- Death contexts (lab_h2h H2H_PROF dctx; 100 v81 mirror games, 1,086 deaths): no ally within 5 51%, outnumbered by 2+
  29%, from >50% health 19%, before r300 19%, bag >= 30 4%. Kill momentum: first kill wins 50%, kill lead at r200 53%
  (32 games); after a kill the victim's team loses 0.63 more champions in 60 rounds vs 0.53 -> power-play dropped.
- Khaos (prominence-chan) changelog: camps never heal in engine 2.0.0 (camp_waste.js: 0% of 798k damage regained;
  8.4 damaged camps left alone 8+ rounds per game of ~146 camp kills) -> "finish partial camps" dropped. Camp_Get
  record: x, y, hp, max hp, strength (rc 98 = dead).
- Coded (v85, not yet tested): A2_ALONE alone alert (slot 64), A2_FOG gate (65), burst scale (66; NOVA_BURST_K is 1.0
  in v81, i.e. on); lab.h kKnobs 72; A2_HYB resets 48-71. knob_es48.js: ES_OFF (ladder half pool, half of every
  generation), per-pool centre win in the log, every generation's centre saved to OUT.hist.
- Search (e85_es, e84rt from the e84 gen-30 centre, ES_OFF=0: 12 even-index ladder maps + 12 unseen a generation,
  lr 0.07): centre by window ladder / unseen 45.8/60.4, 57.5/57.1, 56.7/61.2, 55.0/57.1, 54.6/54.2, last 5 ~52/52.
- Validation (val85.sh: held-out odd ladder half vs v81/c2/c3 = 210; clean unseen = 900):
  e85_final 47.6% / 55.7% (overfit to the 35 training ladder maps); e84_final with tables 52.9% / 57.2%;
  v86h 55.7% / 57.2%. All 70 ladder maps vs v81/c2/c3 (420): v86h 51.4%; v87 (A2_HYB 2: v81 knobs + tables but the
  structural switches kept on ladder maps) 49.0%.
- v86h stays the best: unseen +7, ladder about even (real engine 48.8% on 330 games).

## E86 (1 Nov) - v86h vs the user's x1 (real engine)
- x1 (Downloads/x1.zip -> v4/bots/x1): v81hl family; x1_config.h turns on A2_CAMPWATCH (camp watch) and X1_FAST_SIEGE
  (cached siege line-of-sight ring); bot.cpp, common.h, draft.cpp differ from v81.
- cambc run-batch --release (v4/.m_x1real.txt, bench_out/x1real), v86h vs x1, 290 games, 0 failed:
  unseen maps_real250 150-224 both sides 83/150 = 55.3% +- 4.1; official ladder maps (70 x 2) 61/140 = 43.6% +- 4.2;
  total 144/290 = 49.7%. x1 is clearly stronger than v86h on the ladder pool; v86h is ahead on unseen maps.
- 70 more ladder-map games vs x1_c2 (x1 with NOVA_SEED 2; v4/.m_x1real2.txt, bench_out/x1real2, one per map, sides
  alternating): v86h 37/70 = 52.9% +- 6.0 (team A 22/35, team B 15/35). All ladder-map games vs x1: 98/210 = 46.7% +- 3.4.

## E87 (1 Nov) - x1's features in v86h -> v88
- x1 = v81 + A2_CAMPWATCH 1 (existing v81 switch: contest enemy-farmed groups about to respawn when healthy with an
  ally by the group) + X1_FAST_SIEGE 1 (siege line-of-sight ring cached per camp; fuel only) + X1_MASTERY (draft
  override of Willow / Cassi & Issac; off in the zip). Lab (no fuel meter): x1 vs v81 x3 on the 70 ladder maps 49.8%,
  clean unseen 50.7% -> x1's real-engine edge over v86h on ladder maps comes from fuel, i.e. the fast siege.
- Ported X1_FAST_SIEGE into v85 (bot.cpp siege ring; default 0). v88 = v86h + A2_CAMPWATCH 1 + X1_FAST_SIEGE 1 (camp
  watch is compile-time, so it also stays on for ladder maps where the hybrid plays v81's knobs); v88c = v86h + camp
  watch; v88s = v86h + fast siege.
- Lab: v88c vs v81 x3 ladder 52.9% (v86h 51.4%), clean unseen 58.0% (v86h 57.2%); v88c vs x1 ladder 52.1%, real250
  60.3%.
- Real engine vs x1 (same 360 games as v86h's E86 runs; v4/.m_x1v88*.txt): ladder 106/210 = 50.5% +- 3.5 (v86h
  46.7%), unseen 83/150 = 55.3% (v86h 55.3%). v88 ties x1 on ladder maps and beats it on unseen maps: new best.
- Real engine vs v81 (same 570 games as v86h; v4/.m_e88*.txt): v88 unseen 136/240 = 56.7% +- 3.2 (v86h 57.1%), ladder
  maps 158/330 = 47.9% +- 2.7 (v86h 48.8%). Camp watch + fast siege help against x1 (ladder +3.8) but not against v81.
- Packaged: v4/submissions/v88_engine4.zip (src/ only; rebuilt from the zip = byte-identical bot.wasm). Not submitted.

## E88 (1-2 Nov) - ladder layer + joint search vs v81 and x1 -> v89
- v85 A2_HYB 3: on recognised ladder maps v81's knobs + the per-map table, then a ladder layer: slots 72-87 add to 16
  key knobs (0 1 2 3 4 5 8 9 10 11 12 22 23 43 45 46), slots 88-95 set 8 switches (55 57 60 61 64 65 50 49). lab.h
  kKnobs 96. e88rt = v85 + A2_RTSW 1 + A2_HYB 3 + A2_CAMPWATCH 1 + X1_FAST_SIEGE 1; with the v88 vector it plays 80/80
  games identical to v88.
- knob_es48.js: ES_OPP=a,b (opponent by map index), ES_OFF=-1 (all 70 ladder maps). Search e88_es: ES_NK 96, from
  v88 (new switches at -0.15), 12 ladder + 12 unseen maps a generation, v81 / x1 alternating, lr 0.07, 30 generations.
  Windows ladder / unseen: 49.6/56.3, 50.0/55.8, 55.4/50.0, 53.3/55.0, 59.6/60.0, ~54/48 (gens 26-29).
- val88.sh (never-played games: 70 ladder maps vs v81_c2 / v81_c3 / x1_c2 = 420; unseen vs v81 900; vs x1 real250 300):
  | v88 | 50.7 / 58.0 / 60.3 | gen 14 | 49.6 / 60.6 / 56.3 | gen 23 | 50.6 / 58.3 / 58.3 |
  | gen 25 | 52.0 / 59.1 / 59.7 | gen 30 | 58.8 / 57.8 / 57.5 |
  Gen 30 ladder layer: positioning on; unseen part keeps positioning, spacing, Lanchester override, defend stance.
- v89 = v85 + A2_RTSW 1 + A2_HYB 3 + camp watch + fast siege + A2_KNOBS = gen 30 (lab-identical to e88rt + knobs).
- Real engine (same 930 games as v88):
  | | vs v81 unseen (240) | vs v81 ladder (330) | vs x1 unseen (150) | vs x1 ladder (210) |
  | v89 | 57.9% | 51.2% | 62.7% | 52.4% |
  | v88 | 56.7% | 47.9% | 55.3% | 50.5% |
  Lab ladder +8 became +3.3 in the real engine (fuel is not metered in the lab).
- Packaged: v4/submissions/v89_engine4.zip (rebuilt from the zip = byte-identical bot.wasm). Not submitted.

## E89 (2 Nov) - lab fuel meter; per-map ladder re-fit
- Fuel meter: agent2/lab/fuel_instr.js rewrites a bot's wasm: an exported mutable i64 global lab_fuel, charged at the
  start of every straight-line segment (1 per operator; nop, drop, block, loop, end, else, return, unreachable,
  try_table free, as Wasmtime); below zero the bot calls its own env.yield, so the host suspends it until its next turn
  (the engine's fuel suspension). Decodes the MVP, 0xFC, SIMD (0xFD) and try_table opcodes. host.js (backup
  .bak_e89): LAB_FUEL=1 instruments at load, refills the budget each turn (draft turn 1 LAB_DRAFT_FUEL, other draft
  turns 100k, a champion's first turn 200k, then 100k), fuel_remaining() reads the counter, H.fuelOuts counts
  suspensions. v89: 568 functions, 15,292 meter points; metered games 1.0-1.7x slower. 02the-pack (the map x1's
  telemetry named): v89 11 / v81 23 suspended turns. SDK calls are charged nothing extra.
- Calibration: v89 on ladder maps, metered lab vs seed-3 builds 49.3%, vs v81/x1 engine seed 7 53.6%; real engine
  vs v81 51.2%, vs x1 52.4%; unmetered lab 53.9 / 59.3%. The meter closes most of the lab-to-real gap.
- LAB_SEED (engine random seed) barely changes games: not a source of independent validation games.
- Per-map fit: v85 A2_LADFIT (ladfit.h: fingerprints of all 70 ladder maps = width, height, camp groups, total gems,
  all unique; 24-value correction each on knobs 0 1 2 3 4 5 8 9 10 11 12 22 23 43 45 46 and switch slots 55 57 60 61 64
  65 50 49; lab knobs 96-119; kKnobs 120). agent2/lab/ladfit.js: per map (1+1) hill climbing, 6 of 24 coordinates
  x 0.5 N(0,1) a step, kept when >= +0.5 score on 8 deterministic games (v81, v81_c2, x1, x1_c2 x 2 sides), 20 steps.
  Unmetered fit (e89_fit.json): training 333.5 -> 506 / 560, 56 maps changed. v90 = v89 + A2_LADFIT + that table.
  Held out: vs v81_c3 + x1_c3 (280) unmetered v90 58.6% vs v89 53.9%; metered 50.5% vs 49.3%; vs v81/x1 seed 7
  metered 53.2% vs 53.6%. The unmetered fit's gain needs unlimited fuel -> rerun metered (e89m_fit).
- Fuel-meter fix (host.js): a bot runs unmetered outside its own turns (host calls to exports such as lab_knobs set
  lab_fuel to 1e15 after instantiation and at every yield; turn() then sets the real budget). Before it, metered runs
  with H.knobs crashed (SuspendError from lab_knobs). ladfit.js left a finished process alive once (stopped by hand).
- Metered per-map fit (e89m_fit.json, LAB_FUEL=1): training 297 -> 485 / 560, 64 maps changed. v91 = v89 + A2_LADFIT
  + that table (unseen maps unchanged: the fingerprints match only the 70 ladder maps).
- Metered held-out validation (val91.sh: 70 ladder maps x 2 sides vs v81_c3 / x1_c3 / v81_c4 / x1_c4, 560 games):
  v89 281/560 = 50.2% (46.4 / 52.1 / 50.7 / 51.4); v91 330/560 = 58.9% (57.9 / 57.9 / 55.7 / 64.3). +8.7, about 4 SE.
- Real engine (v4/.m_e91.txt, bench_out/e91_v91 / e91_v89; 70 ladder maps x 2 sides vs v81_c3 / x1_c3 / v81_c4 /
  x1_c4, 560 games each, 0 failed): v91 291/560 = 52.0% +- 2.1, v89 289/560 = 51.6%. The lab's +8.7 does not transfer.
- Game-by-game agreement, v89 vs v81_c3 on the same 140 pairings: metered lab and real engine name the same winner in
  80/140 (57%), unmetered lab 74/140 (53%) - barely above chance. Lab and real games diverge individually; only
  aggregate behaviour transfers. Seed builds (NOVA_SEED) and LAB_SEED give near-copies of the training games in the
  lab, so they do not validate a per-game fit. Per-map tables fitted on 8 lab games learn trajectories, not policy.
- v91 not packaged; v89 stays the best (v4/submissions/v89_engine4.zip).

## E90 (2 Nov) - real-engine per-map ladder fit -> v92
- Real engine is deterministic per pairing (12/12 games repeated exactly; match seed fixed) and fast: 560 games in
  about 2.7 minutes with 5 jobs (~200 games a minute), not 30 minutes as estimated.
- agent2/lab/real_fit.py: v4/bots/rf (v89 config + A2_LADFIT); each round one build whose ladfit.h gives every map
  its own tweak of its current best (6 of 24 coordinates x 0.5 N(0,1)); 8 real-engine games per map (v81, v81_c2,
  x1, x1_c2 x 2 sides); a map keeps the tweak at >= +0.5 wins; state in e90_state.json (copy e90_final_state.json).
  The process asks Windows to stay awake (SetThreadExecutionState). Stopped after round 15 (round 16 scored on a
  partial batch after the stop, 1 map kept). Training: 299 -> 473 / 560. Fresh candidates each round 286-319.
- Held-out real-engine check (70 ladder maps x 2 sides, 980 games; real_fit_held.py reran the final half after the
  stop left the first attempt with a half-built bot):
  | opponent | zero table (= v89) | final table |
  | v81_c3 | 69 | 84 | x1_c3 | 74 | 76 | v81_c4 | 69 | 79 | x1_c4 | 74 | 80 |
  | v86h | 82 | 91 | b5_c3 | 97 | 96 | v61_c3 | 85 | 91 |
  | total | 550/980 = 56.1% | 597/980 = 60.9% (+4.8, ~3 SE) |
  Against bots outside the fit's family (v86h, b5, v61): 264 -> 278 / 420 (+3.3).
- v92 = rf with the final table (v89 + A2_LADFIT + real-engine table; unseen maps identical to v89). Packaged:
  v4/submissions/v92_engine4.zip (rebuilt from the zip = byte-identical). Not submitted.

## E90b (2 Nov) - fight simulator fidelity measured
- v85 A2_TSLOG (lab): each turn with a visible enemy, the bot snapshots its fight model (ts_snapshot), rolls it one
  round with the search's own flee settings and prints "TSP" predictions; agent2/lab/tslog_run.js compares them with
  the engine state at the same bot's next turn. tslog = v92 config + A2_TSLOG; 40 metered games vs v81 (20 ladder
  maps x 2 sides), 182,338 unit predictions (agent2/lab/e90_tslog.json).
- Deaths in one round: actual 1,601, predicted 2,640, both 1,130 (enemy: actual 857 vs predicted 1,590).
- Health change when damage is predicted: ours predicted -249 vs actual -46; enemy -299 vs -64.
- By what actually happened (predicted / actual loss): units that lost < 5% - ours 241 / 6 (20,027 cases), enemy
  285 / 8 (20,870); lost 5-25% - ratio 1.7 / 2.1; lost > 25% (real fights) - ratio 1.0 (ours) / 1.2 (enemy).
- Conclusion: the damage mechanics are accurate; the error is engagement behaviour - in about two thirds of the
  cases the model expects a fight, none happens. Next: calibrate the rollout policy (flee / aggr per side) on these
  logs, or fit an engagement model, then retest the fight search (metered lab, then real engine vs v92).

## E91 (2 Nov) - fight simulator engagement calibration; fight search retested
- A2_TSLOG now logs the one-round prediction under 10 engagement settings (aggr per side, flee per side);
  agent2/lab/tslog_cal.js scores them. With LAB_FUEL=1 the 10 rollouts a turn starved the logging bot of fuel (it
  barely fought: 9 enemy deaths in 40 games), so the calibration ran unmetered (20 ladder maps x 2 sides vs v81):
  | setting (ours / theirs) | health error ours / enemy | deaths predicted / actual ours | enemy | F1 ours / enemy |
  | 0 / 0 = always fight (current) | 75.3 / 125.0 | 922 / 583 | 1312 / 734 | 0.505 / 0.529 |
  | 1.0 / 1.0 | 29.0 / 43.8 | 652 / 583 | 833 / 734 | 0.575 / 0.563 |
  | 0.5 / 0.5 | 26.2 / 39.4 | 582 / 583 | 715 / 734 | 0.570 / 0.562 |
  | 0.3 / 0.3 | 25.4 / 38.8 | 527 / 583 | 598 / 734 | 0.564 / 0.563 |
  Engagement factor 0.5 removes the bias (death counts match, health error -65%); which unit dies stays hard (F1 0.57).
- A2_TSCAL (tsearch.cpp, both search models' aggr = 0.5 / 0.5; the first attempt edited the lab-only A2_TSFULL branch).
  Metered lab vs v92 on 70 ladder maps x 2: search without calibration 25.7%, with 27.1%, + fight-only 27.1%.
  Profile vs v92 (35 maps x 2): metered deaths by r600 7.4 vs 4.7, gems 299 vs 374; unmetered deaths 11.7 vs 1.6,
  gems 238 vs 501, wins 4.3%. More search -> more deaths: the search acts in danger turns, where the model misses half
  the deaths. Fight search stays off; v92 remains the best bot.

## E93 (2 Nov) - v92's platform losses (9 match groups, 45 games) and economy fixes
- Data: the user's match-group zips -> scratchpad matches_e93 (we were team A in 7 groups, B in 2); decoded with
  agent2/lab/platform_decode.js; agent2/lab/e93_analyse.py. Record 11-34. Opponent lineups: HoR + Vendetta + Vesper
  (+ Marcella / Ryth) in 7 of 9 groups.
- Losses (34) vs the opponent: gems held r100 37 / 56 (deaths 0.53 / 0.53), r300 141 / 184, r600 311 / 440; strength
  r200 51 / 60, r600 72 / 102; unspent gold r100 135 / 89; items at the end 36 / 51. Wins: their deaths 3x ours.
- Items by r200 (losses, per game): us Prospector health 3.8 shards + 1.0 emblem, Jungle strength 1.7; them
  Prospector strength 1.8 + 0.6, Prospector health 1.4, Jungle health 0.9. v92's V58_ITEM_PLAN opens melee champions
  (not Vesper / Tavi) with Prospector health.
- Per champion by r300 (losses): their Marcella banks 76 gems and gains 445 gold (ours 14 / 242); their Vesper gains
  558 gold. Gems picked up by r100: their Marcella 31.5, ours 7.0. In our wins their Marcella banked 31.9.
- Switches in v85: A2_MFUNNEL (1 Marcella keeps / allies hand her capture rewards, like UB_GOLD_FUNNEL for Vesper;
  2 Marcella values reward-state groups x A2_MF_REWARD 1.5; 4 Marcella's bag x A2_MF_BAG 0.6), A2_PROSSTR (melee open
  with Prospector strength).
- Metered lab vs v92 (70 ladder maps x 2 + 50 maze-test x 2 = 240): funnel 41.9%, funnel + Prospector strength 51.7%,
  Prospector strength 47.7%, funnel + Vesper funnel 41.5%.
- Real engine, e93m2 (funnel + Prospector strength) vs v92 (v4/.m_e93m2.txt): ladder 75/140 = 53.6%, unseen
  maps_real250 150-224 x 2 70/150 = 46.7%, total 145/290 = 50.0%. Even with v92 in a mirror; not adopted on its own.

## E92 (2 Nov) - real-engine joint search (structure + knobs) from v92: no gain
- Candidate folders v4/bots/rjs00-24 (rjs_setup.py; A2_CANDS: cand.cpp copies row CAND_ID of cand_table.h into the
  knobs at start; full build 11 s, incremental 3 s; rjs00 with v92's vector = v92, 8/8 real games identical).
- agent2/lab/real_es.py: 25 candidates (12 antithetic pairs, sigma 0.3, Adam lr 0.07) over 96 slots, 12 ladder + 12
  unseen training maps a generation, both sides, opponents v81 / x1 / v92 by map; ~7 min a generation (1,200 real
  games). Stopped by the user's go-ahead after 26 generations (drifting). Centre by window: 53.3, 53.3, 52.5, 57.1,
  45.4% (gens 21-25). Optuna fANOVA / gradient t on gens 1-10 (agent2/lab/e92_importance.py): unused slots 69 / 71
  rank among the top -> importances are noise at ~48 games a candidate.
- Held-out (e92_held.py; ladder vs 7 held-out opponents 980 games, unseen vs v81 + x1 600 games):
  gen 18 54.1 / 54.5%; mean of gens 16-20 54.1 / 54.8%; gen 26 52.3 / 53.2%; v92 60.9 (E90) / 56.5%.
  Every centre is worse than v92, mostly on ladder maps (-6.8): v92's per-map table was fitted to v92's own knobs, so
  moving the knobs undoes it. v92 stays the best.
- Tools installed: optuna 5.0.0, scikit-learn 1.9.1, nevergrad 1.0.12, cmaes 0.13.1, smac 2.4.1 (no pyrfr: needs SWIG
  + MSVC), R irace 4.5.1 (R 4.6.1, user library).

## E94 (2 Nov) - meta sparring bot and Marcella carrier role (no gain)
- v85 A2_META_DRAFT (draft.cpp: Heart of Ruin, Vendetta, Vesper, Marcella, Ryth, Varg); A2_MFUNNEL bit 8 = carrier
  role (Marcella: value x (1 + A2_MC_GEMW 0.5 x gems / 50), no cohesion pull, aggression x A2_MC_AGGR 0.7, no hunting).
- spar_meta = v92 + meta draft + Marcella funnel (7) + Vesper funnel + Prospector strength: v92 beats it 146/240 =
  60.8% (real engine; ladder 61.4%, unseen 60.0%). Decoded (local run-batch replays are zip bundles: the replay is
  replay.repl26a inside): its Marcella banks 19.6 gems by r300 (top teams 76), Vesper gains 195 gold (top 558).
- Real engine vs v92 (70 ladder x 2 + 50 real250 x 2 = 240): spar_meta2 (+ carrier) 37.5%; v93c1 (v92 + funnel 15)
  49.6% (ladder 53.6, unseen 44.0); v93c2 (+ Prospector strength) 50.8% (52.9 / 48.0). With the carrier role Marcella
  banks 17-21 by r300 and makes 0.8-0.9 captures of 15+ gems (top teams 3.7).
- Platform losses, rounds 0-300 time profile: their Marcella near camps 58% / ours 53%, enemy within 4 15 / 15%, ally
  within 3 52 / 46%, dead 6 / 8%; Vendetta 55 / 55, 12 / 14, 49 / 42, 9 / 10. Same time use; they convert farming
  time into ~2x the captures (clear speed / routing / reward ownership), not a different role. v92 stays the best.

## E95 (2 Nov) - camp-clearing efficiency in the platform losses; duo farming on ladder maps (no gain)
- agent2/lab/e95_clear.py on the 45 platform games (decoded, captures = pickups of 15+ gems, rounds 0-300). Losses,
  us / them: captures a game 3.8 / 4.2, gems each 27.4 / 32.0 (group value 26.3 / 29.9), clear time mean 17.4 / 14.7,
  walk between captures mean 61.8 / 51.5, teammates within 3 at the capture 0.41 / 0.91. Gems gained r50 15 / 20,
  r100 38 / 57, r150 61 / 84 (first 15+ pickup median r74 / r68); in our wins both sides are even.
- v92 has NOVA_DUO 5 only off the official pool (NOVA_DUO_MAPS 1); its ladder drafts are HoR + Marcella / Varg /
  Vendetta (+ Cassi-Issac), so the melee-ranged duo pairs only Heart of Ruin. New bit 16 (v95d/e bot.cpp): same-kind
  buddies farm as a duo too, lower slot leading.
- Real engine vs v92 (70 ladder x 2 + maps_real250 150-199 x 2 = 240): v95a (duo 5 everywhere) 49.2%, v95b (13)
  46.2%, v95c (7) 51.2%, v95d (21) 47.5%, v95e (29) 42.5%. v95d decoded (agent2/lab/e95_local.py): teammates at the
  capture 0.34 vs v92's 0.36 - the duo does not make us farm in pairs at the captures. Not adopted.
- Where v92 loses on unseen maps (agent2/lab/e95_diag.py, map features agent2/lab/e95_feats.js): vs v81 / x1 on 550
  training maps (maps_real250 0-149, maps_test4 0-99, maps_new4, maps_maze; 2,200 games) 55.6 / 55.5%; by suite
  maze 55.0 / 53.7, new4 48.0 / 53.7, real250 59.7 / 55.3, test4 62.0 / 61.0. By feature tercile all 51-59%
  (gem density high third 51.2%, mid 58.6%): no map class worth switching on (< 1 point).

## E96 (2 Nov) - unseen-map knob layer (A2_ULAYER), real-engine search: on hold
- u96t = v92 + A2_ULAYER (ulayer.cpp / ulayer.h: additions to the 16 key knobs only on maps outside the 70-map
  ladder pool; 25 ladder maps use the unseen knobs + ladfit, so moving knobs 0-47 directly would disturb them).
  Zero layer = v92 (80/80 games identical); a test value changed only unseen games (ladder 40/40 identical).
- agent2/lab/real_es96.py (17 candidates, 64 unseen training maps x 2 sides vs v81 / x1 / v92 a generation). Gen 1:
  centre 55.5%, candidates mean 50.4%, best 57.0%. Put on hold by the user's rule (no prospect of +8); resumable
  (e96_state.json).

## E97 (2 Nov) - real-engine branching: consequences of one camp choice (no learnable gain)
- x97t = u96t + A2_RFORCE (rforce.cpp / rforce.h: per map fingerprint one forced decision - champion slot, first
  round, candidate rank by the bot's score; rank 0 = control). Lessons: (1) printf of floats in the deciding turn
  changed 16/18 control games (fuel); store at the decision, print integers after the turn's actions (rf_flush, only
  with 40k fuel left); (2) even a per-turn no-op call changed 8/80 games vs v92, so the base games come from x97b: the
  same code and table with the round past the game (branch-free trigger) - controls then 613/613 identical.
- agent2/lab/rforce.py: 120 maps (70 ladder + maps_test4 0-49) x v81 / x1 x 2 sides a round; 10 rounds, 4,277
  samples (e97_samples.jsonl). Taking the 2nd / 3rd / 4th candidate instead of v92's pick: win change -14.7 / -15.0
  / -11.5 points (se ~2.5); ~25% of games change result, nearly all for the worse.
- agent2/lab/e97_fit.py (ridge + gradient boosting on candidate-minus-default features x champion state, 5-fold by
  map): held-out correlation +0.02 (win) / -0.02 (gem lead at +200). No context where an alternative is better; v92's
  camp choice is locally near-optimal. Stopped after 10 rounds.

## E98 (2 Nov) - real-engine branching of whole-team strategy switches (no gain; on hold)
- x98t = v92 + A2_ULAYER + A2_RSWITCH (bot.cpp kMode: from round R every champion scales the per-turn settings the
  brain resets - aggression, carry, retreat, danger ttd, territory, cohesion, gold weight; branch-free, base x98b =
  same table with R past the game). agent2/lab/rswitch.py (120 maps x v81 / x1 x 2 sides a round, R uniform 20 to
  0.8 x game length), agent2/lab/e98_fit.py. 7 rounds, 3,360 samples (e98_samples.jsonl); controls all identical.
- Win change vs default, 6 rounds (2,880): aggressive -5.6, cautious -6.8, bank early 0.0, big bags -1.0, expand
  -6.0, home + together -2.6, gold focus -10.5, team fight -4.2 (se ~2.5). Before round 300 every switch loses (-3 to
  -20); after it bank early +4.0, big bags +3.4 (~1.5 se). Per-mode models of the change from the state at R (round,
  banked / gold lead, deaths, team size, map features), 5-fold by map: held-out gain per game -0.04 to +0.003. v92's
  default is at least as good as every switch in every state the data can separate; stopped (no prospect of +8).

## E99 (2 Nov) - team-structure styles: every grouping loses heavily
- v92 copies with grouping switches (A2_PAIRS new: slot % ceil(team / 2) squads; the rest existing), real engine vs
  v92 (70 ladder x 2 + maps_real250 150-199 x 2 = 240): pairs all game 12.9%; + reward sharing 11.7%; pairs until
  r300 29.6%; until r600 19.2%; pairs + sharing until r400 19.6%; two squads 11.2%; one pack until r300 21.7%; one
  pack all game 7.5%; casters + Issac pack (APEX_ROLE_SQUAD 1) 38.8%; last two slots paired (APEX_PAIR 2) 31.7%.
- Pairs decoded (20 ladder games): faster clears (11 vs 14 rounds) but half the parallel jobs and longer walks
  (95 vs 82): banked r200 35 vs 56, r600 168 vs 236; deaths r600 6.2 vs 4.5. v92's solo farming + help calls beats
  every fixed grouping by 11-42 points; the top teams' 0.91 helpers at captures is not reproduced by grouping.

## E101 (3 Nov) - the user's x3ctr: a counter table fitted against v92 itself
- x3ctr (Downloads/x3ctr.zip -> v4/bots/x3ctr) = v92 + X1_COUNTER (x1_counter.h: per map fingerprint and side, one
  of 30 variants = a team plan from round 0 (full map, hoard, fight harder, turtle, ...) or random knob deltas) +
  the X1_PLAN hook; every other x1 switch off. 89 rows: 73 on our 70 ladder map-sides, 16 on 14 "03-" maps that are
  not on disk (a newer pool; `cambc maps pull` needs a login).
- Real engine, 70 ladder maps x 2 sides (agent2/lab/e101_x3ctr.py, per-game rows in e101_games.tsv; report
  e101_report.py). v92 reproduced E90's held-out counts exactly (84 / 76 / 79 / 80 ...).
  | opponent | x3ctr | v92 |  | opponent | x3ctr | v92 |
  | v81_c3 | 82 | 84 |  | v86h | 82 | 91 |
  | x1_c3 | 74 | 76 |  | b5_c3 | 86 | 96 |
  | v81_c4 | 82 | 79 |  | v61_c3 | 85 | 91 |
  | x1_c4 | 76 | 80 |  | v81 / x1 (v92's fit opponents) | 97 / 92 | 116 / 119 |
  Held-out 567/980 = 57.9% vs v92 597/980 = 60.9% (-3.1); head-to-head x3ctr vs v92 139/140 (73/73 on its table
  rows, 66/67 on map-sides without one).
- Reading: the table was searched against v92. The engine replays a pairing exactly, so "the variant that beat v92
  here" memorises v92's games (and rows are needed only where the plain build lost). It does not transfer: -3 on
  held-out bots, -16 on v81 / x1 (its plans move v92 off its fitted per-map play). Same lesson as E91: a per-map fit
  on a few deterministic games learns trajectories. v92 stays the best bot.

## E102 (3 Nov) - Phase 1: top-team macro dataset from the platform replays
- Data: Downloads/replays-2026-10-25-part1..3.zip (74,447 replays, engine 1.0.3; file names carry kind, match id and
  both team ids: kind_match_teamA_vs_teamB, team A = team 0). Decoder engine v1_0_3.wasm from the visualiser cache
  (%LOCALAPPDATA%/cambc/assets/174924b1.../visualiser/assets; also has v1_0_2, v2_0_0). Selected 2,369 games: every
  ranked / tournament game of an Oct-19 top-20 team plus all 340 of ours. Current engine: the 14 match-group zips
  in Downloads (70 games, us = team A, v6x-v92 vs top teams).
- Tools: agent2/lab/p1_decode.js (per-round champion arrays, camp-group states, banked gems; per-map distance fields;
  9 games/s), p1_build.py (every 10 rounds per champion: 90 state features, decision dead / bank / fight / farm / walk,
  next farmed group as rank among the 5 nearest live groups, bank within 30), guard.py (RAM watchdog in Python:
  PowerShell scripts are blocked by the execution policy). Camp-group states read through the replay API are
  1 asleep / 2 under attack / 3 cleared in both engines (the SDK renumbers them on the bot side).
- Strength label: Oct-19 ranks are weak (top-20 vs lower 53%); Bradley-Terry from the dump's 2,142 ranked /
  tournament results (bt25.tsv): elite = 12 strongest with 30+ games; we are 37th.
- Gate (p1_gate.py, elite vs us, 508k samples, 5-fold by game): state only AUC 0.950, + decision 0.950, round +
  decision only 0.559. What separates the states: own max health / strength / gold 0.875, champion type 0.757,
  everything positional ~0.6. Taken alone this says "same choices in the same states" - but the decision label
  only carried the rank of the next group.
- Direct comparisons (current engine, same maps, us vs top teams; Oct-25 elite agrees):
  - per champion r600: their Marcella max health 2717 / ours 1687, gold 97 / 41; Vesper 2489 / 1250, str 194 / 117;
    Vendetta and Heart of Ruin even. Team banked r100 / 300 / 600: 29 / 136 / 369 vs 15 / 92 / 246.
  - picks: top teams take Vesper in ~80% of games (we: 4 of 45), Heart of Ruin, Marcella, Vendetta.
  - reward allocation r0-600 (p1_funnel.py): Marcella 38% of team captures, 41% of banking (ours 24 / 23);
    Vesper 30% captures, 41% of team gold (ours 20 / 20); Heart of Ruin 11% (ours 25); team captured +41%, banked
    +64%, gold +42%.
  - next-camp choice (p1_choice.py): top teams pick richer groups (Marcella 25 vs 18 gems, Vesper 23 vs 13), nearer
    (nearest live group 46-51% vs 39-42%; outside the 5 nearest 26-31% vs 34-41%) and where allies are (0.87-0.95 vs
    0.70-0.75 allies within 4) - for almost every champion type.
- Conclusion: there is a learnable macro difference, in camp choice (rich, near, with allies) and in who takes the
  rewards (Marcella / Vesper as the economy). Phase 2 goes ahead on both.

## E103 (3 Nov) - Phase 2: elite next-camp imitation as v92's macro layer (p2a, A2_BC)
- Model (agent2/lab/p2_bc2.py): per-candidate utility MLP (9 candidate + 21 own-state + 16 type inputs, 24 tanh
  units, no rank input), softmax over the 5 nearest live groups, Adam on 120k elite choices (Oct-25 dump). Held out by
  game: elite 73.1% top-1 (nearest 68.8%), log-lik -0.756; on our Oct-25 choices -0.850 vs a model of our own -0.791
  (a learnable difference); on top teams' current-engine choices (70 match-group games) 72.9% / -0.760 (transfers);
  our current-engine choices -0.778 (already closer to theirs than in October). Biggest gaps: Varg, Heart of Ruin,
  Ren, Issac, Vesper, Marcella; none for Vendetta.
- Bot: v4/bots/p2a = v92 + A2_BC (bc_net.h from p2_export.py, scaling folded in; checked against Python: utilities
  equal up to a constant). bc_utility adds A2_BC_BETA x utility to the camp net's logits (campnet_pick, among v92's
  8 best candidates when its pick changes). Features in the bot: walking distance (group field), gems, gold, under
  attack (damaged alive group), side (-group_margin), allies within 4 (seen) or claiming, enemies within 4, altar
  distance of the centre (nearest walkable neighbour: the bot's field blocks camp tiles; first build had 3.0 =
  unreachable there, 0.7% in training), big camps. A2_BC_SCOPE 1 unseen only / 2 ladder-table maps only.
- Fuel: v92's camp net never runs in normal play - campnet_pick needs kDetSafety + 18k (+25k for A2_BC) left and the
  bot arrives with less (debug counters A2_BC_DBG: entry == fuel skips in every game). The user asked to ignore fuel
  while designing: real engine `run-batch --fuel-quantum 1000000` for both sides (e95_run.py --fuel). Then the layer
  decides 30-66 times per champion-game and changes v92's pick in 5-18.
- e95_run.py fix: run-batch refuses to overwrite outputs, so a rerun silently re-read the previous run's JSONs; it now
  clears its folder first. (The first fuel-ignored screen was such a stale read.)
- Real engine, fuel ignored, vs v92 (70 ladder x 2 + 50 real250 x 2): beta 0.5 ladder 86/140 = 61.4%, unseen 41/100;
  beta 1 70/140, 41/100; beta 2 64/140, 27/100; beta 2 unseen-only 65/140, 27/100.
- Held-out ladder (7 held-out bots x 70 maps x 2 = 980 games each, fuel ignored, agent2/lab/held_run.py,
  e103_held_ladder.tsv): v92 552 (56.3%), beta 0.5 580 (59.2%, +2.9), beta 0.25 579 (59.1%, +2.8).
  Per opponent v92 / b0.5 / b0.25: v81_c3 76/80/81, x1_c3 74/81/83, v81_c4 78/71/74, x1_c4 75/76/72, v86h 68/77/78,
  b5_c3 94/100/98, v61_c3 87/95/93. (With fuel ignored v92 itself drops vs metered: v86h 68 vs 91 - its per-map
  table was fitted under real fuel.)
- Reading: imitation of the elite camp choice is a real but small gain on official maps (~+3, ~2 SE) and hurts on
  generated maps (-9; the model never saw them). Below the +8 gate: not packaged.
- E103b reward routing (A2_ECO_OWNER: a gem-rich capture reward goes to Marcella, a gold-rich one to Vesper, in
  poorer_ally_takes and the one-owner rule; else the poorest as before), fuel ignored, vs v92 (240 games):
  routing alone p2e0 52.9% (ladder 72/140, unseen 55/100); routing + A2_BC 0.5 p2e05 55.0% (ladder 90/140 = 64.3%,
  unseen 42/100). Best candidate so far; held-out check pending. Plan: agent2/plans/improvements_2026-11-03.md.
- E103c held-out check of p2e05 (fuel ignored, agent2/lab/held_run.py; e103_held_ladder.tsv, e103_held_unseen.tsv):
  | suite | v92 | p2b05 (imitation) | p2e05 (imitation + routing) |
  | ladder, 7 held-out bots (980) | 552 = 56.3% | 580 = 59.2% | 583 = 59.5% (+3.2) |
  | unseen, v81 + x1 (maps_mazetest 0-99 + maps_real200b 50-99 x 2 = 600) | 319 = 53.2% | 327 = 54.5% | 354 = 59.0% (+5.8) |
  p2e05 per opponent, ladder: v81_c3 80, x1_c3 77, v81_c4 75, x1_c4 82, v86h 75, b5_c3 96, v61_c3 98 /140;
  unseen: v81 179, x1 175 /300. Both suites 937/1580 = 59.3% vs v92 871/1580 = 55.1% (+4.2): consistent, below the
  +8 gate. Imitation carries the ladder gain, routing the unseen gain (the head-to-head screen's "imitation hurts on
  generated maps" was specific to v92 / maps_real250). Not packaged; under real fuel the imitation layer does not run
  yet (plan step B), routing is fuel-cheap.

## E104 (3 Nov) - p2 under real fuel, vs v92 and x3ctr; scoring multiplier; fuel value
- Fuel cost of A2_BC measured in metered games (A2_BC_DBG meters): features ~1,100 fuel per candidate computed ~5,000
  times per champion-game (every scored group, every call) = ~4.5k a turn; utility 17-20k per decision; v92's own camp
  net residual ~14k per decision. v92's camp net entry needs kDetSafety + 18k: it runs 17-57 times per champion-game on
  most maps, ~0-10 on fuel-tight ones (01islands).
- Optimised (v4/bots/p2a): features only for the <= 8 finalists of a real decision (bc_features; centre / altar distance
  cached per group), vectorisable utility (contiguous hidden loops, branch-free tanh) -> features ~4k + utility ~5.5k
  per decision (-96% / -70%); the A2_BC term has its own fuel check (A2_BC_FUEL 12000), v92's entry threshold unchanged
  (A2_CN_MIN 18000); A2_CN_FAST (branch-free residual tanh) did not reduce the residual's cost.
- Real fuel vs v92 (70 ladder x 2 + 50 real250 x 2): imitation 0.5 + routing 49.2% (ladder 54.3, unseen 42); beta 1
  47.1%; routing alone 50.0% exactly (70/140, 50/100 = mirror): A2_ECO_OWNER only acts when an economy champion and an
  ally both stand on a reward region with no enemy seen, which never changed a game - its fuel-ignored "gain" was fuel
  chaos (v92's searches size themselves by remaining fuel, so any code change perturbs them at 1M fuel too).
- vs v92 and x3ctr, real fuel (agent2/lab/e104_vs_*.tsv): ladder 140 / unseen (mazetest 0-99 + real200b 50-99) 300:
  | bot | v92 ladder | v92 unseen | x3ctr ladder | x3ctr unseen |
  | p2f05 (A2_BC 0.5) | 76 = 54.3% | 139 = 46.3% | 70 = 50.0% | 141 = 47.0% |
  | p2fl05 (ladder-table maps only) | 74 = 52.9% | 149 = 49.7% | 58 = 41.4% | 139 = 46.3% |
  | v92 | - | - | 1 = 0.7% | 146 = 48.7% |
  Any real change of play escapes x3ctr's memorised counter; vs v92 the gain is +3-4 on ladder, flat / negative unseen.
- A2_BCV (elite utility as a value multiplier in score_groups for the 4 nearest live groups, refreshed every 2 rounds):
  vs v92 (real fuel) weight 0.5 46.2%, 1.0 35.8%, 1.0 ladder-only 40.8%. Steering camp choice harder hurts (as E97).
- Fuel value probe (v4/bots/v92w + A2_WASTE: burn N fuel before each turn): waste 10k 43.8%, 20k 50.4% vs v92 (240
  each): no monotonic effect - v92's play is not fuel-limited enough for fuel savings to be a large lever.
- Conclusion: the macro imitation line gives at most +3-4 on ladder maps; neither scoring with it nor freeing fuel
  helps. v92 stays the best real-fuel bot.

## E105 (3 Nov) - game analysis from first principles; E96 resume aborted
- agent2/lab/rules_probe.js reads engine 2.0.0's champion designs (stats + growth), camp designs and item records
  (agent2/lab/rules_2_0_0.json). Camps unchanged from the rules file; champions: Vendetta str 70+6, Vesper 45+5
  (range 3), Marcella 45+4.5 / health 1200+100 / focus 60+14, Heart of Ruin 30+3, Ryth 45+4.5 / 1200+100, etc.
  Emblems add 5 shards of points + passive (Power 6, Greed 35 points, Bruiser 5 + 1 + 1); passive magnitudes:
  Monster 0.15, Durability 0.1, Treasure 0.1, Jungle 0.3, Home 0.5, Tribute 0.33, Capture 3, Prospector 0.25,
  Hunter 50, Skirmish 0.05, Collectors 0.01. (The settings record contains a double; fields after recall_time read
  shifted.)
- Analysis and build plan: agent2/plans/game_analysis_2026-11-03.md (camp economics per champion, snowball rate,
  death and fight math, MOBA strategy mapping, ranked levers, the economy-first pack design and a 6-step plan).
- E96 resume (real_es96.py, 3 Nov 02:51): generation 2 lost 1,681 of its games (21 s run; same stale-output /
  batch failure pattern) and its Adam step on that is now in e96_state.json - the process was stopped. Restore
  generation 1's centre from e96_es.hist before any resume.

## E106 (3 Nov) - step 1 of the game-analysis plan: economy core = the team's v58 director (fails its gate)
- The economy core already exists in v92's source, switched off: V58_DIRECTOR (1 primary jobs, 2 nearby parallel
  pair, 3 middle camps), V58_ROUTE (designated capturer), V58_CARRY_SHOP (carry Treasure), V58_DRAFT (Vesper / HoR /
  Vendetta / Ryth / Marcella / Tavi), V58_SURVIVE (disengage, bag discipline). The team's v58 notes
  (nn_push/docs/prompts/V58_GPT_PROMPT.md, nn_push/bots/v58/CHANGES.md): meta draft alone -89, + gold funnel -141,
  draft-turn plan -217, opening pack -52 (mechanically right, R250 gold unchanged); the forced-carry director "lost
  strength" and shipped off.
- Real fuel vs v92 (p2a variants, 240 games): ec1 director 2 + route 42.5% (ladder 45.0, unseen 39.0); ec2 + carry
  shop + carry draft 35.4% (40.0 / 29.0); ec3 + A2_ECO_OWNER 35.4% (identical: the owner rule still never fires);
  ec4 + V58_SURVIVE 27.9%.
- Gate (economy in the same games, ec2 team vs v92 team, 70 ladder games, rounds 0-600, p1_decode + p1_funnel):
  captured 389 vs 413, banked 288 vs 292, gold 2,032 vs 2,206; Marcella capture share 16.7% vs 17.7% (top teams
  38%), Vesper gold share 27.2% vs 20.3% (top 41%), Heart of Ruin capture share 27.4% vs 17.9% (top 11%). ec1:
  395 / 297 / 2,183 vs 423 / 299 / 2,285, shares unchanged. The economy does not move toward the top teams' loop;
  total income falls. Step 1 fails; per the plan's gates, not continued as built.

## E107 (3 Nov) - first-principles audit of our own bot (v92), not top-team games
- Correction: in replay decodes a camp group's state 2 lasts 7-9 rounds and ends at the payout: it is "monsters dead,
  capture running" (v92's GroupState::reward), state 1 = live monsters (attacked or not), 3 = respawning. So p1_build's
  "farm" label and the BC model's candidate feature 3 mean "capture phase". The bot side of A2_BC (bc_features)
  computed feature 3 as "alive and damaged": a feature mismatch - fix to (g.state == GroupState::reward) before any
  further A2_BC test.
- agent2/lab/e107_audit.py (time use), e107_walk.py (walking by purpose): v92's side of 70 ladder games (vs ec1, real
  fuel), rounds 0-600: walking 46.1%, attacking camps 19.3%, capturing 9.7%, dead 9.5%, waiting at respawning camps
  4.5%, fighting 4.4%, idle 2.7%, at spawn 2.1%, banking 1.7%. Unspent gold only 25-37 per champion (spent promptly);
  4.6 deaths per team by r600, mean bag 6.8 (32 gems lost a game).
- Walking: 50% of it ends attacking a camp (75 trips per team per game, mean 9 rounds), 11% fights, 11% ends waiting
  at a respawning camp, 10% idle, 7% banking, 7% captures. Walks to camps follow the shortest path (8.3 walked vs 8.7
  shortest): no detours. From a capture to the next attack: median 12, mean 22 rounds.
- Reading: productive time is 29%; the cost is distance between consecutive camps and early arrivals, i.e. the camp
  schedule (which camps, in what order, timed to respawns), not path quality, gold spending or bag losses.

## E108 (3 Nov) - farming schedule optimiser (no enemy): v92's farming is near the optimum it finds
- Ground truth: v92 vs v4/bots/idle4 on the 70 ladder maps (real engine, v4/bench_out/solo92): 65/70 reach 1,000
  banked, median 909 rounds (unfinished: reverse-spiral, rushbait-v2, stampede, elk-arena, shortcut, as in E68).
  Solo time use (e107_audit.py): walking 43.7%, attacking 25.2%, capturing 12.2%, waiting 7.6%.
- agent2/lab/econ_sim.py: round-by-round farming simulator on the real maps (decoded walking fields, camp health /
  damage / respawns, crews for big camps recruited by job calls, the group hitting its healthiest attacker, heal /
  shop trips with gold -> strength, banking trips), v92's lineup per map. Policies: greedy (v92-like value per
  champion-round) and rollout (one-step policy improvement: each of the 5 best greedy jobs simulated 150 rounds ahead
  with greedy, best taken). Calibration (greedy vs real v92 solo): 66/70 finish, median 988 vs 892 on 62 maps,
  correlation 0.73 across maps.
- Rollout vs greedy, 70 maps: median 1,000 -> 936 rounds (mean speed-up 10.0%), gems by round 600 503 -> 577;
  finishes 69/70. On maps 20-39: K8/H300 +10.7% (longer horizon no better); shopping at 90 gold instead of 150:
  greedy 985 -> 938, rollout 884; bags of 25 / 80: no gain.
- What rollout changes (1,270 overrides, maps 0-29): smaller crews (1.27 vs 1.60), smaller and quicker solo jobs
  (12 vs 21 gems, kill 10.5 vs 12.1 rounds) further away (21.6 vs 13.9 tiles): job calls pull teammates off their own
  work.
- Transfer to v92, real engine vs v92 (240 games): no job calls (APEX_INITIATE 0) 47.5% (ladder 40.7, unseen 57.0);
  shop at 75% (GT_SHOP 0.75) 49.2%; both 44.6%. No gain.
- Reading: real v92 (median 892-909) is already faster than the optimised schedule in the model (937): its farming is
  near what scheduling can give when alone. The economy gap to top teams is not solo farming efficiency; it comes
  from the contested game (enemy pressure, deaths, territory, camp contests) and champion strength (draft / items).

## E109 (3 Nov) - two-team contested-game model (first principles)
- agent2/lab/contest_sim.py (on econ_sim.py): both teams on the real map from their own spawns, shared camps; opposing
  champions at the same group fight (Lanchester: each side's summed damage on the other side's weakest member per
  round; a side retreats when its power, sum damage x sum health, is below RETREAT x the other's; retreating costs the
  weakest member PURSUIT rounds of the chasers' damage); a contest resets a running capture; an abandoned capture
  leaves the reward on the region; death = 60 rounds out, killer takes the bag + 100 gold; camp kills destroy the bag.
  Policy per team: territory (side, side_from), contest ratio, retreat ratio, bag, shop.
- Calibration (baseline vs itself, 70 ladder maps x 2 sides, v92's lineups): banked at r600 287 per team (real v92
  mirror-type games 292-299), game length ~1,370 (real ~1,200-1,700). Deaths: PURSUIT 3 / 6 / 10 -> 5.2 / 7.6 / 8.6 per
  team per game (real ~12; walking encounters are not modelled); PURSUIT 6 used.
- One-at-a-time variants vs the baseline (140 games each, se ~4): bag 20 56.4%, bag 80 30.7%, bag 150 30.0%; shop 90
  59.3%, shop 300 34.3%; retreat 0.5 61.4%, 0.65 57.9%, 1.0 50.7%, 1.3 30.7%; never contest 39.3%, contest 0.8-1.6
  48.6-50.7%; whole map from r0 53.6%, own half only 47.9%, deep own side only 5.0%; side_from 400 45.7%.
- Real-engine checks on v92 (v4/bots/v92b = v92 + GT_CARRY, a final multiplier on the bag after profiles and knobs;
  240 games vs v92): bag x0.5 52.5% (ladder 51.4, unseen 54.0), x0.33 46.2%, x0.5 + shop x0.75 48.3%. The model's
  economy levers (small bags, early shopping) do not give large real gains: v92 already shrinks bags under danger.
  The model's fight result (retreat later) contradicts E73 (standing when caught 25.5%): its fight model is too coarse
  to judge fight policy.
- Reading: the contested model reproduces the economy (banked gems, game length) and the structure (big bags and
  late shopping lose, never contesting loses, staying deep at home loses), and v92 already sits near those optima.

## E110 (3 Nov) - item value probe and real-engine build test (v92's build holds)
- glitch_probe.js prospectorEmblem (engine 2.0.0, sandbox: Marcella captures a 33-gem / 150-gold group alone): no
  emblem 33 gems + 150 gold; Prospector emblem 36 (+9%) + 155; Treasure 33 + 165 (+10% gold). Prospector multiplies
  capture gems (exact formula not determined; v92 stores prospector_bonus but uses it nowhere).
- v4/bots/v92c = v92 + A2_BUILD (default melee build variants in V58_ITEM_PLAN; Vesper / Tavi / Marcella / Heart /
  casters unchanged). Real engine vs v92 (240 games): 1 farm speed (Prospector str, Monster, Jungle, Capture,
  Durability) 46.2%; 2 early Capture 44.2%; 3 Greed early (Prospector, Greed str 25) 28.8%; 4 tempo (Prospector,
  Monster, Capture, then Greed) 34.2%. v92's Prospector-health / Jungle / Durability / Monster / Capture order beats
  every strength-first order: survival in fights is worth more than clear speed here; delayed Greed stats lose badly.
- Summary E101-E110: imitation layer, economy director, schedule optimiser, contested model levers, bag / shop sizes,
  fuel savings and item builds each move v92 by -20 to +4 points against our evaluation set. v92 is at a local optimum
  on every lever measurable locally.

## E111 (3 Nov) - self-play draft learning (real engine): the learned draft loses badly
- Exploration: v4/bots/v92r = v92 + A2_RDRAFT (a random lineup per seed / map fingerprint / team size, the same on
  both sides; everything else v92). agent2/lab/e111_draftgen.py: seeds 1-4 x 820 training maps (70 ladder + real250
  + test4 + new4 + maze) x 2 sides vs v92 = 6,560 games (e111_draft.tsv; lineups from the result JSON roster). Random
  lineups win 25-30% (ladder 16-25%): v92's lineups are far better than chance.
- agent2/lab/e111_feats.js: v92's 16 draft-net map features for 1,120 maps (both sides). agent2/lab/e111_fit.py:
  logistic win model (pick main effects + pick x map features + pair synergies + size + their picks as a control),
  5-fold by map: held-out log-loss 0.557 vs 0.578 base (C 0.01). Our bot's best picks: Vendetta, Varg, Ryth,
  Marcella, Ren, Vesper; worst: Willow, Heart of Ruin, Stellar. Favourite lineup Vesper / Vendetta / Marcella / Ren /
  Varg; the model predicted +11 points over v92's own lineups.
- v4/bots/v92l = v92 + A2_LDRAFT (the best-scoring lineup from the exported model, e111_ldraft.h, in the draft turn);
  real engine, held-out maps (unseen = mazetest 0-99 + real200b 50-99): ld1 (every map) vs v92 ladder 25.0%, unseen
  40.7%; vs x3ctr 25.0% / 39.3%; ld2 (maps without a ladder lineup only) vs v92 33.6% / 40.7%, vs x3ctr 11.4% / see
  e111_val.log. The predicted gain was badly optimistic: a model fitted on random lineups ranks good lineups poorly;
  v92's draft (platform-tuned net + per-map lineups; v70 covers only part of the ladder pool) is much better.

## E112 (3 Nov) - endgame race, shared intel, wards (items 5-7): no gain
- v4/bots/v93 = v92 + A2_ENDGAME (per turn: enemy within A2_EG_D 150 gems of winning and level or ahead -> deny:
  prelock altars we pass, buy an altar lock at spawn, hunt, aggression x1.3; we within 150 and ahead -> finish: bag
  <= 15, aggression x0.8, no hunting) + A2_INTEL (teams of <= 4 bodies: before a champion overwrites the one shared
  sighting, the previous fresh sighting of a different enemy moves into two spare claim slots; readers add both;
  spare slots decode as idle so they are never phantom claims). Wards via v92's switches V58_VISION (objective wards:
  altar when carrying, contested target camp, near enemies) + APEX_WARDS (wards at captures / tributes / sieges);
  v92 already wards bushes ahead (NOVA_WARD_AHEAD 6).
- Shared-memory layout (all 64 bits used): six 7-bit claim slots (targets, on-site, fight orders), one sighting
  (x, y, round), distress bit 62, camp-event bit 63.
- Real engine vs v92 (240 games): v93 all off 49.6%; endgame 47.1%; intel 51.2% (ladder 54.3, unseen 47.0); wards
  46.2%; all three 45.4%. No gain beyond noise.

## E113 (3 Nov) - top-team-style bot tuned as a whole (option 1): stopped, no gain
- agent2/lab/tt_setup.py: v4/bots/ttbase = v85 + the top-team structure (A2_META_DRAFT lineup Heart of Ruin / Vendetta /
  Vesper / Marcella / Ryth, A2_MFUNNEL 7, UB_GOLD_FUNNEL, A2_PROSSTR) on v92's base (A2_RTSW, A2_HYB 3, A2_CAMPWATCH,
  X1_FAST_SIEGE, A2_LADFIT + v92's ladfit.h) with A2_CANDS, 25 candidates tts00..tts24, all rows = v92's knobs.
- agent2/lab/tt_es.py (from real_es.py): real-engine ES over the 96 knobs, 25 candidates (12 antithetic pairs + centre),
  sigma 0.3, lr 0.07, ladder + unseen maps. Gen 1 vs v81/x1/v92 on 48 maps; from gen 2 vs x1/v92 on 32 maps (v81
  dropped to save time), ~1,600 games / 8.5 min per generation.
- Centre: gen 1 41.7% (old mix); gen 2 32.8%, gen 3 45.3%, gen 4 39.1% (vs x1/v92); best candidate 43.8-54.7%.
  No upward trend (noise about +-6 points per generation); the structure starts ~10 points behind v92 and the knob
  search does not close it. Stopped after gen 4 (efficiency rule). State in tt_state.json / tt_es.hist.
- Option 2 (neural macro self-play) not started (it was conditional on option 1 moving); option 3 (more compute per
  decision) skipped: no-fuel vs fuel self-play is flat, fuel-waste test flat, simulator depth-2 planner worse.

## E114 (3 Nov) - plan v3 step F fixes; B feasibility on the Oct-25 dump (engine 1.0.3)
- F: p2a / p2f05 bc_features feature 3 = (group state == reward), the training meaning (E107 mismatch); p2f05 rebuilt.
  e96_state.json restored to the generation-1 centre from e96_es.hist (Adam moments reset; bad gen-2 state kept in
  e96_state_bad_gen2.json).
- B1 (agent2/lab/b1_repeat.py, b1_ident.py; Bradley-Terry top 15 of bt25.tsv, 70 team-map-sides with 2+ games):
  - exact scripts: no. Same team, map, side and lineup: positions first differ at round 11 (median; quartiles 3 / 49),
    before first contact (<= 6 tiles, median round 32) in half the pairs (randomness or bot updates between games).
  - macro routes: yes, team-specific. Champions within 3 tiles of a same-team champion of another game: r20 0.94,
    r40 0.78, r60 0.68, r100 0.54, r150 0.41; different teams on the same map-side 0.53 / 0.34 / 0.27 / 0.27 / 0.27;
    different teams with the same lineup 0.36 (r40) / 0.23 (r60) / 0.19 (r100). Openings belong to the team, not the meta.
  - identification from the draft (most frequent team for the enemy's map + side + lineup, leave-one-out): 46% of
    top-15 sides (key unique to the team 36%); top teams share meta lineups. In-game identification would need the
    first sightings as well (contact median r32).
  - Reading: a per-team opening model is real (r40-100) but needs current-engine replays of the top teams (login), and
    the draft alone names the opponent only half the time. B is paused on data; C (offline positioning) goes first.

## E115 (3 Nov) - plan v3 step E: rules diff 1.0.3 -> 2.0.0; step C pilot (move labels on engine 2.0.0)
- rules_probe.js with the 1.0.3 engine (agent2/lab/rules_1_0_3.json) vs rules_2_0_0.json: balance changes only.
  Nerfs to the Oct top-team meta: Vesper strength 55 -> 45, Marcella strength / focus growth 5 / 15 -> 4.5 / 14, Heart
  of Ruin 3.5 / 12 -> 3 / 10, Ryth strength growth 5 -> 4.5. Buffs: Varg and Issac strength 40 -> 45, Cassi focus 70 ->
  100, Willow focus 120 -> 140, Stellar focus growth 7 -> 8.5, Prism health growth 60 -> 65, Ren ability 0 w1 0.75 ->
  1.1, Tavi ability 1 w1 1.4 -> 1.6. Items: emblem passives 1/3/5 0.10 -> 0.15, 19/21/23 0.20 -> 0.10 (the item table
  is 84 records in 2.0.0; E110 covers item values).
- E111 self-play pick effects (random lineup with vs without the pick, vs v92, 2.0.0): Vendetta +10.9, Varg +7.3,
  Marcella +6.7, Ren +5.8 (v92 picks it 6%), Vesper +3.3, Ryth +2.9, Cassi / Issac 0, Heart of Ruin -1.6 (v92 55%),
  Prism -2.4, Willow -8.8. Main effects do not compose into better lineups (E111 ld1 lost), so no new lever here.
- C pilot (micro_lab.js with DUEL_BOT=../v4/bots/v92, ENGWASM v2_0_0; duels teleported at round 3, 70% 1v1 / 30% 2v2):
  64 scenarios: v92's own probe turn shortfall from the engine's best option mean 6.9 / median 1.1, within 0.5 of best
  36%; the average option 6.8 - v92's duel move is no better than a random legal option. Label agreement between the
  two jittered variants: best option on one within 0.5 of the best on the other 84%. Throughput ~15 scenarios / min
  on 4 workers (~700 MB). 3,000-label run started (agent2/lab/c1_labels.jsonl, guard log c1_labels.guard.log).

## E116 (3 Nov) - neural bot (user's architecture): recorder, imitation of v92, first nn1 tests
- Design: agent2/plans/neural_bot_2026-11-03.md (entity encoders per type, mean+max pooling, trunk, heads behaviour /
  target pointer / step / attack pointer / cast / cast target pointer / cast timing / utility / shop; teacher encoder
  2x64 trunk 2x128, student 1x16 / 2x64; privileged critic for RL later). C label run (E115) stopped at 168 labels
  (CPU contention; the network's heads cover it).
- Data path: the real engine keeps each team's stdout in the replay bundle (team-a.stdout; --log-limit raises the
  1 MB cap), so the bot records its own features and actions at engine speed. v4/bots/nnrec (agent2/lab/nn_mkrec.py):
  v92 + nnrec.cpp features + every SDK action through wrapped imports in a bot-local copy of cambc.h (cambc_rec.h; the
  shared SDK untouched; imports.h cannot be included before cambc.h). nn_record.py (OUT/*.npz + replays), nn_labels.py
  (per-head labels: behaviour from v92's mode, target = v92's target_group as a camp-slot pointer, step from move_to,
  attack / cast targets from handles, position casts as direction classes), nn_model.py / nn_train.py (PyTorch 2.11
  cu128 on the RTX 5060), nn_export.py -> nn_weights.h, nn_infer.h (C++ forward; matches PyTorch to 0.01 on logits),
  nn_mkbot.py (v4/bots/NAME = v92 + A2_NN bits 1 target, 2 bank).
- Data 1: 1,242 games (every 4th map of maps / real250 / test4 / new4 / maze vs v92 / x1 / x3ctr, both sides), 1.73M
  rows, 428 features. Held-out (10% of maps) accuracy, teacher / student: behaviour 89.7 / 87.8, target 70.3 / 68.1,
  attack 95.7 / 95.0 (acted 90 / 88), cast 94 / 92 (acted 70 / 55), step on moved turns 45 / 35.
- Real engine vs v92, fuel ignored: nn1b (network banks) ladder 50.7%, unseen 47.0% = parity; nn1t (network picks the
  target group) 25.0 / 40.3; nn1 (both) 23.6 / 39.7. Target switching per turn without commitment (68% agreement)
  dithers. Real fuel: the float forward overruns most turns (fuel optimisation deferred, user's call).
- Data 2 (running): user's points - first-turn map analysis (every group's walking field built at once, fuel
  ignored: walking distance, side margin, altar and spawn distance per camp group, allies that reach it first) and
  memory (this champion's history: rounds since target change, target changes in 50 rounds, health 5 / 20 turns ago,
  movement over 10 turns, bag 20 turns ago, rounds since bank / contact / respawn; camp flag "current target").
  500 features; pipeline agent2/lab/nn_pipeline.sh.

## E117 (3 Nov) - neural bot: DAgger, pool-like maps, RL (PPO)
- DAgger for the target head (agent2/lab/nn_dagger.sh; nn2dag = recorder + network acting, rows keep v92's own choice
  from farm()): network target play vs v92 ladder 9.3% -> 27.9% -> 35.0% -> 45.0% (iterations 1-3; aggregated
  3.2M rows). nn3 (student, target + bank): ladder 43.6%, pool-test 54.7%. Teacher in the bot needs ~2M fuel a turn
  (--fuel-quantum 20000000; at 1M it overran and lost 0/140).
- Pool-like maps: tools/viz/mapmake6.js draws size / shape / symmetry / walls / holes / bush patches / altars / groups /
  walk-straight buckets from the 70 pool maps (agent2/lab/map_stats.js); v4/maps_pooltest (300, held out),
  v4/maps_pooltrain (600). The old unseen suites were 70-110 wide, scattered bushes, no holes, 6-12 altars, open.
- Throughput: 224 games/min (5 jobs) -> 252 (10 jobs) -> 295 (10 jobs, 600 rounds); CPU-bound.
- RL 1 (agent2/nn_rl1, PPO on the target head, per-game return): T=1.0 dithered (rollouts 15% vs v92); T=0.4,
  8 iterations flat in rollouts (53-58%), but held-out vs v92: iteration 8 ladder 42.1% (DAgger-3 41.4%), pool-test
  59.0% (54.0%).
- RL 2 fixes (agent2/lab/nn_rl.py): decisions logged only when farm() applies the choice; return = own value change
  (banked by this champion + carried) over 100 rounds / 30 + 0.5 x team banked-lead change / 60 + 0.3 x result;
  every target change + 10% of keep turns weighted x10; KL on the behaviour head (banking shares the trunk);
  800 games / iteration, lr 2e-4, 4 epochs; held-out deterministic eval vs v92 every 2 iterations (ladder 70 x 2 +
  pool-test 0-149 x 2), best kept. Pilot (2 iterations from RL-1 iteration 8): corr(return, result) +0.33, critic EV
  +0.04, behaviour KL 0.0004; eval ladder 70/140 = 50.0%, pool-test 182/300 = 60.7%, total 57.3% (DAgger-3 50.0%).
  Full run continuing; the best checkpoint is to be confirmed on pool-test 150-299 and vs x3ctr (selection bias).
- RL 2 continued: GAE (--gae) raised critic EV 0.05 -> 0.34; held-out evals iter 8 / 10: 55.5% / 54.8%; best stays
  iteration 6 (ladder 69/140, pool-test 185/300, 57.7%; agent2/nn_rl2/best.pt). Target-only RL plateaued ~55-58%.
- Macro policy RL prepared (not run yet): nnrec.cpp A2_NN_MACRO (behaviour options held until done, contact fight /
  flee verdict = A2_NN bit 4, out-of-contact options bit 8 via nn_option_out, NRB rows with gold / team kills / own
  deaths), nn_mkbot.py patches, agent2/lab/nn_rl3.py (joint PPO + GAE, league incl. v4/bots/p65pack = p65 + A2_PACK +
  A2_JACKPOT, nnsnap, ladder-weighted maps, iteration-0 eval). Unit tests pass; nnm_test compiles. Smoke test (2 games
  vs v92): logging works, but on 00contest the network banked 0 gems (lost 0-1000) and team kills read 0 in the other
  game - check count_enemy_deaths and the bank / farm options before the pilot.
- Best RL network (nn_rl2 iteration 6, bot nnbest = A2_NN 3 teacher, fuel 20M both sides) vs v92, fresh sets:
  249 new pool-like maps (mapmake6 seed 77001, v4/maps_poolfresh, never used in training or selection) 308/498 =
  61.8%; unseen mazetest 0-99 + real200b 50-199: 295/500 = 59.0%; official pool (70 x 2, earlier) 69/140 = 49.3%.
- Statistics JSON = per-round truth: championTimelines (gems, submittedGems, earnedGold, kills, assists, deaths, damage
  ...; run-length, one sample per round), teamTimelines (submittedGems), events. Bot champion handle = roster id.
  nn_rl3 now takes rewards from these timelines (the bot-side death / bank tracking counted channel gaps as deaths and
  missed banks) and gives the critic the full state (all champions' gems / banked / gold / kills / deaths).
- Macro "farm" option now keeps v92's go-home and banking triggers (smoke test: the network team banked 0 and died 48
  times on 00contest when farm skipped them).
- Macro policy ablation (best RL network, deterministic, vs v92; ladder 140 + pool-test 0-149 x 2): all parts
  (A2_NN 15) 40.2%; contact verdict only (7) ladder 26.4%, pool 46.3%; options only (11) ladder 45.0%, pool 54.3%;
  target + bank (3, reference) 57.7%. The forced fight / flee verdict (imitating v92's mode) is far worse than v92's
  own fight engine -> dropped; "farm" now = v92's whole default chain (skipping its hunt / converge cost ~6 points),
  the network forces only bank / home / regroup / hunt.
- Draft memory: the draft instance gets 100x fuel on its first turn and can submit draft memory (>= 1016 bytes; v92
  uses 6) that every champion reads after the draft - the place for a full first-turn map analysis.
- Macro starting point (deterministic, vs v92, ladder 140 + pool-test 300): options only, farm = v92's chain 47.3%;
  + logit bias -3 on hunt / home / regroup 49.5% (the bias moved probability onto bank: low-health "home" turns became
  forced bank trips); + bank only at v92's tribute step 50.7%; keep-5% scheme (abandoned: a forced option could never
  win the argmax). Final design: an RL-only option head (none / hunt / home / regroup / bank now; fresh head = zero
  weights + "none" bias 7, ~0.4% forced options per turn), banking stays the behaviour head's argmax at v92's tribute
  step. Baseline = the best bot exactly: ladder 69/140, pool-test 185/300, 57.7%.
- Version-3 features ready (not run): nnrec.cpp nn_feats_t<NC, AF> (500 = 10 camps / 12 ally fields; 828 = 24 camps +
  allies' claimed targets from shared memory), A2_NN_LAYOUT / A2_NNREC_LAYOUT, NN_LAYOUT for the Python side
  (labels regression identical on 3 games), agent2/lab/nn_v3.sh (the best RL network plays, version-3 features logged,
  labels = what the bot did).

## E118 (3 Nov) - where the ladder gap comes from; version-3 network; v92 official-map bug
- vs v92 (with its tables), real engine, fuel 20M both sides, ladder = 70 maps x 2 sides:
  new bot (best RL network, A2_NN 3) tables on 69/140 = 49.3%; all tables off (LADDER_TABLES 0, A2_LADFIT 0) 66/140 =
  47.1%, pool-test 184/300 = 61.3% (tables on: 61.7%); v92 without tables 67/140 = 47.9%. The per-map tables are worth
  ~2 points (noise; E89 measured ladfit at +0.4 in the real engine). They are not why the network only ties v92 on the
  ladder - the new bot does not need them.
- v92 bug: is_official_map() (old nova_map_id table, 17 maps) recognises 15 of the 70 current ladder maps, so v92 runs
  its unseen-map rules (NOVA_GOLD_UNSEEN gold weight 0.10, NOVA_DUO_MAPS) on 55 ladder maps. v4/bots/v92of
  (agent2/lab/mk_v92of.py: also accept the 70 ladfit fingerprints) vs v92: 82/140 = 58.6% (+8.6, ~2 SE). To validate.
- Version-3 network (agent2/lab/nn_v3.sh: 828 features = 24 camp groups + allies' claimed targets + ladder map id;
  1,074 games with the best RL network playing; teacher held-out target 97.6%, attack-acted 95.6%): in play ladder
  25/140 = 17.9%, pool-test 89/300 = 29.7%. C++ = PyTorch (0.009); the failure is compounding error (as nn2t before
  DAgger): the 97.6% is mostly "keep the current target". Needs DAgger with the RL network as the expert.
- E119 official-map fix validation (real fuel, ladder 70 x 2): v92of vs x1 57.9% (v92 85.0%), vs v81 57.9% (82.9%),
  vs b5_c3 67.9% (68.6%), vs x3ctr 34.3% (0.7%), vs v92 52.1%; network on the fixed base vs v92 48.6%. Rejected: v92's
  ladfit corrections were fitted against v81 / x1 on these exact maps (deterministic -> memorised), so any behaviour
  change loses ~25 points to them; vs held-out b5 no change. v81 / x1 results on ladder maps are inflated for v92.
- Ladder gap by map size (new bot without tables vs v92): official width <= 40 38% (50 games), 41-60 59% (58), > 60
  41% (32); pool-test 58 / 69 / 53%. Same shape, but official maps are 14-20 points harder at every size: v92 was
  developed on them; earlier RL used them in only 7.6% of games. nn_rl3 now trains 70% on ladder maps.

## E120 (3 Nov, 22:15) - candidate x3mf2 (team zip candidates_20261103) + fuel facts for the fuel fit
- Macro RL (nn_rl3) paused after iteration 2 (best: vs v92 ladder 77/140, pool-test 180/300, 58.4%); bot nnm_i2 =
  that checkpoint (identity check: 77/140 again). Resume: python -P agent2/lab/nn_rl3.py agent2/nn_rl3 agent2/nn_rl2/best.pt
  14 --games 800 --eval-every 2 (NOT the original command line, which starts with rm -rf agent2/nn_rl3).
- x3mf2 = x3 (v92 code + x1 configs) + per-map knob fits for competition maps (X1_MAPFIT) + per-map counter table
  (X1_COUNTER: the variant that beat a given opponent on each map) + fuel-scaled fight search (tsearch) + farm learner.
- nnm_i2 vs x3mf2 (fuel 20M): maps_poolfresh 0-124 x 2: 145/250 = 58.0%; unseen (mazetest 0-49 + real200b 50-124) x 2:
  149/250 = 59.6%. v92 vs x3mf2 (real fuel): pool 125/250, unseen 125/250 = 50.0% - and 247 of 250 maps give gem-for-gem
  identical games with sides swapped: off the official maps x3mf2 plays exactly like v92. Its value is only on the
  official maps (fits / counters), which this test did not cover.
- Real fuel (replay team-X.fuel: 13-byte header, then u64 LE; first 8 = [10M, 100k, 200k, 100k] x 2, then fuel used per
  unit turn): draft turn 10M (v92 uses 25k), first champion turn 200k, every later turn 100k, no sign of carry-over.
  v92 uses median 56k per turn (p10 25k, p90 71k, max 140k on first turns). Free per turn for the network: ~30-45k.
- Teacher (iteration 2) with A2_NN_FAST, fuel 20M (fuel_probe.py, A2_NN_FUEL): features 40.5k + network 1.09M per
  decision. At real fuel it hits the 100k cap on 92% of turns, prints nothing (no decision completes), loses 0/2; the
  engine does not count it as a bot fault (diagnostics.botFaults 0).
- Student (distilled from the iteration-2 teacher, 28,889 parameters; nn_distill 8 epochs on nn_labels_dag3): same argmax
  as the teacher on held-out maps: target 93.9%, behaviour 91.0%. At 20M fuel (vs v92, ladder 140 / pool-test 300 /
  fresh 498): teacher nnm_i2 77 / 180 / 306 (61.4%); A2_NN_FAST teacher nnf_t 58 / 169; FAST student nnf_s 61 / 170;
  network also in contact nnf_sc 59 / 170; keep decision in contact (A2_NN_CHOLD) nnf_sh 62 / 183 / 284 (57.0%).
  The FAST contact skip is not the cause; 77/140 was likely inflated by checkpoint selection on the same 140 games.
- Fuel profile (A2_NN_PROF, student, per decision): network 157k = trunk 55k + camp encoder 48k + rest; features 40k
  (camp features 31-44k). Input-major dense with zero skipping, SIMD pooling, exported transposed weights, cached
  per-group constants: network 83k, features 25k; same strength (nnf_sh2 fresh 284/498, as nnf_sh).
- Pipelined deployment (A2_NN_PIPE): the forward cut into 6 stages + features, run at the end of each turn while the
  fuel left covers the stage's worst cost (+1/8) plus A2_NN_RESERVE (5k, the user's 2-5k margin); published decisions
  expire after 8 rounds (v92 decides). Real fuel, 10 games: 0-1 overruns per game (A2_FUELLOG), 84-495 decisions per
  champion per game. Bugs fixed on the way: turn-boundary underflow of the cost estimate, the slog table fill (~60k)
  on first use (now lazy), and the bank gate (no decision in force = v92 never banked -> 0/10).
- Real-fuel pipeline v1 vs v92 (ladder 140 / fresh 498): control that never acts nnp0 59 / 245 (49.2%), targets + force-only
  bank nnp1 51 / 121 (24.3%), targets + full bank gate nnp2 44 / 95 (19.1%). NOT VALID as a measure of the idea: pf was not
  cleared between decisions, so absent enemies / allies stayed in the input as ghosts (fixed: std::fill before nn_feats).
  Rules (GameRules.md, Fuel): unused fuel does not carry over; a bot out of fuel is suspended and resumes next round.
- Staleness at 20M fuel, fresh features (vs v92, baseline nnf_sh3 every turn 284/498 = 57.0%, same score on the latest
  code): decide every 4, applied 3 late, nnf_e4 58/247 = 23.5% (partial: RAM watchdog; baseline on those games 57.1%);
  every 8, 6 late, nnf_e8 76/498 = 15.3%. Holding decisions costs > 30 points: the network has only played with fresh
  decisions, so a held target at a finished group (or a held bank gate) is a state it never trained on.
- Not used: the SDK's fuel_pause / fuel_resume (debug blocks). Free compute through them would be exploiting the platform.
- Partial held-out check, official maps, 20M fuel (job stopped on request; results kept in e120_held.tsv): vs b5_c3 nnm_i2 100/140
  = 71.4%, v92 94/140 = 67.1%, nnf_sh 85/140 = 60.7%; vs v61_c3 nnm_i2 93/140 = 66.4%. Correction to the note above: the
  student + A2_NN_FAST drop on official maps is 10.7 points against both v92 and b5_c3, so it is not all checkpoint-selection
  luck. A2_NN_FAST teacher nnf_t also fell (58/140), so the fast path looks responsible rather than the small network; cause open.
- Held-decision fixes, 20M fuel, maps_poolfresh 498 vs v92 (baseline every turn 284 = 57.0%). Every 4, 3 late: v92 banks nnv1 123
  (24.7%); drop targets that went to respawning, next choice (A2_NN_VALID) nnv2 162 (32.5%); both nnv3 182 (36.5%). Pipeline with the
  ghost bug fixed, features at END of turn, 1 turn late, nnp4 156 (31.3%): only one turn late yet below nnv3, so end-of-turn
  features hurt on top of staleness ("already acted" self values, world a round old). Real fuel, both fixes, TTL 30: nnp5 149 (29.9%).

## E121 (4 Nov) - what can stay fresh at low fuel
- 20M fuel, maps_poolfresh 498 vs v92, student, v92 banks: every-turn decisions nnb0 260 (52.2%, against 284 = 57.0% with the network's
  bank gate). Camps scored on fresh features every turn with the trunk summary z kept (A2_NN_ZEVERY / ZLAG): z every 4, 3 late, nnz4b
  241 (48.4%); every 8, 6 late, nnz8b 228 (45.8%). Held decisions with both fixes were 182 (36.5%), so fresh camp scoring keeps most of
  the value and z may refresh slowly. Event-driven (network only when the target finished or every 16 rounds, A2_NN_EVENT) nne16b
  153 (30.7%): continuous re-evaluation is the value.
- nn_tiny.py (offline, iteration-2 teacher, nn_labels_dag3, held-out maps): the teacher moves off its current target on 9.3% of rows; always
  keeping the target agrees 92.3% overall, 17.1% on those moves. Student (28k MACs) 94.0% / 51.3%. Tiny camp scorers without a trunk,
  770-13,456 MACs: 91.4-92.5% / 14.0-34.2%. So the tiny route fails for targets, and the student's 94% hides a weak spot on moves.
  Bank (teacher says bank on 4.4% of rows): student recalls 85.4%; tiny on global + self: linear 28.6%, hidden 8 67.0%, hidden 16 69.9%.
- Fresh camps with the summary's stale bank gate (z every 4, 3 late, 498 fresh, 20M): full gate nnz4n 224 (45.0%), force-only nnz4f 237 (47.6%),
  v92 banks nnz4b 241 (48.4%): under staleness v92 should bank. Distillation with moves + bank rows x4 (student_i2m, 12 epochs): moves 63.4%
  (was 51.3%), bank recall 93.3% (was 85.4%), target overall 93.5%.
- v92 fuel profile (APEX_PROFILE, 10 ladder games, real fuel): 39.6k per turn on average. farm 31.0k per call on 686 of 1,270 turns, of which
  score_groups 22.5k (including route_search 8.4k x 428 calls) and move 8.7k; world 12.3k; enemies 10.8k on 419 turns. On a farm turn where the
  network has already chosen, score_groups is wasted. A2_NN_SKIPSEL skips it; A2_NN_LIVE decides at the start of the turn with a fuel gate.
- First network bot inside real fuel (A2_NN_LIVE + A2_NN_SKIPSEL + A2_NN_VALID, student_i2m; nnl, with v92 at real fuel): fresh 245/498 = 49.2%,
  ladder 64/140 = 45.7% (never-acting control: 49.2% / 42.1%). 10-game log: full decision about 63k, camp-only about 25k, overruns 19-97 per team
  per game (about 0.5% of turns; plain v92 about 0.3%). Student deciding every turn at 20M: nns2 287/498 = 57.6%.
- Why the start-of-turn full decision failed: on overrunning turns it left v92 a median 4.9k, because the cost estimate decayed while unused, opened the
  gate, and the real cost (65-85k) went through it. 362 of 363 overruns were on that path. First turn: v92's own 100k before fields + the network's first run
  (about 100k) is over the 200k budget. Staged design (nnl6): camps at the start of the turn (about 28k), slow part in 4 stages at the end of the turn on what
  v92 left (about 7k / 12k / 22k / 15k), first turn left to v92 and the fields: 10 overruns in 46,581 turns (0.02%, v92 about 0.3%), a refresh every ~1.5
  calm turns, mean 32-60k per turn, first turns 100-170k. (Earlier designs at real fuel: nnl 49.2% fresh / 45.7% ladder; nnl5 45.4% / 32.9%, with first-turn overruns.)
- Bank control on the staged design at real fuel vs v92 (fresh 498 / ladder 140): network gate while the summary is fresh nnl7 260 (52.2%) / 67 (47.9%); force-only
  nnl7f 259 (52.0%) / 70 (50.0%); v92 banks nnl7b 278 (55.8%) / 67 (47.9%). First network bot to beat v92 at real fuel on fresh maps; official maps about even.
- nnl8 (staged, v92 banks, 2k margin, first summary on the first turn; 0.01% overruns, first turns about 185k): fresh 268/498 = 53.8%, ladder 65/140 = 46.4%, vs b5_c3 on
  the ladder maps 92/140 = 65.7% (v92 at real fuel earlier 68.6%). nnl7b and nnl8 are within noise on fresh maps: the real edge there is about 4-5 points; official maps about level or slightly behind.
- nn_rl4.py: PPO on the deployed student at real fuel, v92 only (user's choice), 70% official maps. Rollouts are debug builds: sampling and logging inside debug_block spend no fuel
  (--release: "debug_block is skipped and the fuel pause imports are not linked, as on the platform"). Smoke test: logged vs recomputed log-probability median 0.005, p90 0.15. Baseline check
  (nnq_eval): ladder 65/140 (same as nnl8), pool-test 163/300, total 51.8%.

## E122 (4 Nov) - using up to 99k a turn (the user's limit)
- Margin 1k. The slow part now runs at the start of the turn when it fits (a refresh under way first, then a whole new one, so the decision uses this turn's summary), the rest at the end of the turn.
- First try (nnm9): a refresh on nearly every calm turn (665 of 671), mean up to 88k, but 1/12 wins: the network starved v92. v92's fuel gates sit at 38-58k well above what the step costs; below them it skips work
  and then looks cheap (measured need 6-9k), so the network took more, down to v92's 9k walk gate. Fix: v92's fuel checks add back what the network spent this turn (nn_spent, a text replacement in nn_mkbot.py; field building keeps the true number);
  a 15k minimum stays for v92. Refresh on 70-80% of calm turns, overruns 0.5-0.7%.
- Deadlock found on pool_77012 (1 camp decision all game): an overrun set the cost estimate to about 86k and estimates only shrank on use. Overrun bumps are now capped (camps 45k, stages by kStageCeil), and the one-time setup runs in checked steps at the end of the first turns (nn_warm).
- 99k design at real fuel vs v92 (fresh 498 / ladder 140): network gate from same-turn summaries nnm12 261 (52.4%) / 59 (42.1%); v92 banks nnm12b 264 (53.0%) / 62 (44.3%); overruns about 0.7%. Against the end-of-turn design nnl8 268 (53.8%) / 65 (46.4%),
  nnl7b 278 (55.8%) / 67 (47.9%), overruns 0.01-0.02%. No measurable gain from fresher summaries or from spending more fuel: fuel is no longer the limit, the fresh camp scores carry most of the value. A2_NN_ZSTART=0 is the default.
- New base nnl9 (end-of-turn slow part, v92 banks, v92's fuel checks isolated, deadlock fixes): fresh 282/498 = 56.6%, ladder 62/140 = 44.3%. First real-fuel network bot clearly above v92 on fresh maps (best of 3 similar runs: 53.8 / 55.8 / 56.6).
- Draft-turn plan (A2_NN_DPLAN: mappre.h + sched.h from p65, 7.5M of the 10M draft fuel, plan's current step overrides the network unless an enemy is within 6 or health < 50%): nnl9q fresh 218/498 = 43.8%, ladder 53/140 = 37.9%; paired on fresh -64 wins of 498. Rejected in this form.

## E123 (4 Nov) - official-map gap: size, fast path, training data
- Official maps give only 140 deterministic games against v92, too few to compare bots. mk_v92j.py: v92jN = v92 + +-0.5% seeded noise on each group's farm score (redrawn every 16 rounds): independent games from what is
  still v92 (v92j1 vs v92 73/140 at 20M and at real fuel). Each cell below: 70 maps x 2 sides x (v92, v92j1, v92j2) = 420 games, SE 2.4. Report: e123_report.py; rows e123_official.tsv, e123_real.tsv, e123_fresh.tsv.
- 20M fuel, official 420 / fresh 498 vs v92: teacher normal path nnm_i2 53.8% (77, 75, 74 of 140) / 61.4%; teacher fast path + hold in contact nnf_th 49.0% / 55.8%; teacher fast path + network in contact nnf_tc 44.3% / 59.8%;
  student 16x64 normal path nns_n 46.4% / 57.4%; fast + hold nns2 45.7% / 57.6%; larger students (same recipe, same data, fast + hold): 24x96 nns24 48.1% / 60.0%, 32x128 nns32 45.7% / 57.8% (agreement on the teacher's moves 63.4% -> 67.0% -> 70.4%).
  Real fuel: nnl9 45.2% (62, 67, 61 of 140). So: the student's fast path costs nothing; larger students show no steady gain (24x96 +2.4 on both, within noise, 32x128 none).
- The student's distillation data (nn_labels_dag3) has only 54 of 1,074 games on official maps. nn_dag4.py: DAgger on the states the deployed student reaches at real fuel, 65% official; student scores as deployed (stale summary), teacher from this turn's features.
- nn_infer.h: the slow part now has 7 stages (trunk layer 0 in three parts, pointer vector apart), starting estimates scale with the matrix sizes, so larger students fit in turns. Not yet measured at real fuel.
- A2_NN_XF / NN_LAYOUT=4 (556 features, not yet tested): exact deaths and respawn countdown of both teams (sdk_champion_is_alive works without vision; global fields 16-21), draft-turn analysis per group (camp fields 22-26: value per round of a round trip, gems around the group, team plan steps, my plan order, rounds until my plan starts there); draft memory: plan at byte 8, 'X' block at byte 200. nn_xf_expand.py widens a student with zero weights on the new inputs. A2_DP_UNTIL -1 turns off the plan's direct effects.
- Teacher robustness: nnm_c (rebuild, same code) reproduces 77/140 exactly. Tiny noise on its own target logits (A2_NN_LJIT, width 0.1): nnm_j1 68 + 66, nnm_j2 71 + 77 of 140 x 2 = 50.4% (e123_jit.tsv), against 53.8% without noise.
- BUG (fast path, every real-fuel score before this line ran with it): slogi() read the nearest step of a table for |value| >= 4096. Off by up to 0.002 after the log, then multiplied by 1 / sd on the way in (sd floor 1e-3; some large features barely vary): bot vs PyTorch logits off by a mean of 0.18, up to 6.8 (normal path 0.0006). nnd_check.py found it, nnd_compare.py compares two builds per turn. Fixed: interpolated table (nn_infer.h, nn_export.py; old weight headers must be re-exported): now 0.00003, max 0.0002, and fast + normal builds play the same games (first-turn "field not ready" features aside, tie order in the camp sort is harmless).
- After the fix (official 420 / fresh 498 vs v92, e123_fix.tsv, e123_fix_f.tsv), 20M fuel: teacher fast path + network in contact nnf_tf 51.2% / 62.0%; student 16x64 fast + hold nns_f 49.8% / 57.0%; student 24x96 nns24f 47.1% / 63.3%. Real fuel, v92 banks, 7 stages: nnl10 45.2% / 55.6%.
- Bank control at real fuel after the fix (official 420 / fresh 498): network gate while the summary is at most 2 rounds old nnl10g 35.0% / 54.0%; force-only nnl10f 43.3% / 55.4%; v92 banks nnl10 45.2% / 55.6%.
- BLEND (A2_NN_ENS=a): v92's own target search runs; v92's choice stays unless the network's top group scores more than a logits higher than v92's choice (a group outside the 10 nearest counts at the "far" score). 20M fuel, student 16x64, fast + hold, network bank gate (official 420 / fresh 498 vs v92): a=0 (no blend) nns_f 49.8% / 57.0%; a=2 nne2 56.7% (83, 78, 77 of 140) / 63.5%; a=5 nne5 53.6% / 51.2%; a=10 nne10 52.6% / 52.8%. First design well above v92 on official maps too.
- nn_rl4.py: NN_ENS=a trains the blend (sampling moved to farm() in the rollouts, where v92's choice is known; rows log v92's slot); opponents v92, v92j1, v92j2; checks on official 420 + pool-test 300, score 65% official.
- More real-fuel tests (official 420 / fresh 498): held bank gate nnl10h 46.2% / 51.2%; 24x96 student nnl24 44.8% / 51.0%; 20M reference with v92 banking nns_b 47.4% / 56.4%. So banking is worth little, and a larger student loses at real fuel.
- Blend at real fuel, camps scored at the start of the turn nnle2: 44.3% / 44.8%. The gate (fuel >= scoring + v92's measured need) stays shut with v92's target search back: hold 979, camps 381 in a 2000-round game; overruns 0.69%. Fix: A2_NN_LAZY scores the camps inside farm(), after v92's own choice, on what is left (nn_lazy_score).
- Blend margins at 20M: a=1 nne1 55.7% / 61.4%; a=3 nne3 53.8% / 54.2%. a=1-2 is the plateau.
- First A2_NN_LAZY try nnlz2 at real fuel: 36.9% / 44.0%, overruns 0.02%, mean fuel only 44k: the scoring ran on about 1 turn in 4. A turn that also started a refresh (all features) pushed the cost estimate up, and the estimate only shrank when used: locked out, and stale scores then overrode v92's fresh choice. Fixes: scoring is camps only (the features behind a refresh are taken at the start of a calm turn), the estimate decays while unused, scores older than 2 rounds have no say (v92's choice stands).
- Blend + larger network, 20M: 24x96 nne24 52.9% / 61.0%; teacher nnet 52.6% / 58.8%: no gain over the small student's 56.7% / 63.5%.
- Blend at real fuel with the lock-out fixes nnlz3: official 49.0% (65, 71, 70 of 140), fresh 48.6%; overruns 0.30%, camps scored on 55-90% of farm calls. Official up from 45.2%, fresh down from 55.6%; both far below the blend at 20M.
- Where the blend loses between 20M and real fuel. nneb2 (every-turn network at the start of the turn, v92 banks, a=2, 20M): official 61.9% (88, 90, 82 of 140) / fresh 56.8%: best official score of any bot. nnlz3 (the real-fuel code) at 20M: 49.3% / 54.2%: so most of the loss is in the design (late summary, scoring moment), not the fuel. nn_livecheck.py: deployed scoring vs PyTorch: median 0.0000, p90 0.0000, p99 0.51.
- Late summary costs a lot (blend a=2, v92 banks, 20M, official 420): every turn nneb2 61.9%, + A2_NN_VALID nneb2v 63.3% (93, 87, 86 of 140); every 2 turns, 1 late nnz21 55.0%; every 4, 3 late nnz43 47.6%. A whole network every turn would be worth about 15 points on official maps over the staged design. Idea to test: NNUE-like: self + camps fresh every turn, trunk layer 0 updated by the inputs that changed, other blocks refreshed by stages (A2_NN_ZMASK simulates it).
  Fresh 498 for the same bots: nneb2 56.8%, nneb2v 56.2%, nnz21 51.4%, nnz43 57.4%: little sensitivity on fresh maps. Note the bank gate splits by map set: network gate nne2 56.7% official / 63.5% fresh, v92 banks nneb2 61.9% / 56.8%.
- Which blocks must be fresh (A2_NN_ZMASK; the others every 4 network turns, 3 late; blend a=2, v92 banks, A2_NN_VALID, 20M, official 420): self + camps nnm18 58.1%; + global nnm19 55.5%; + global + allies nnm23 60.7%; + global + enemies nnm27 63.8%; everything nneb2v 63.3%; camps only (summary every 4, 3 late) nnz43 47.6%. So self + camps carry most of it and fresh enemies may add more. Deployment A2_NN_NNUE: x of trunk layer 0 has one part per block and W x + b is kept (NNUE-style), so a block costs only its own columns; self + camps (+ enemies in view) every farm turn, others at the end of the turn by turns.
- A2_NN_NNUE first runs: nnu2 at real fuel: overruns 2.5%, scoring on 15-25% of farm calls: 36.4% vs v92 (stopped). Cost of a scoring: features 11.5k, camps 10k, self 6.3k, pooling + trunk inputs 6k, top 11.5k = 45k, on top of v92's 34k before its choice + 9k after. nnu3 (v92's search every 3 rounds A2_NN_SGCACHE=3, safety margin measured from what v92 spends after its choice): overruns 0.13%, scoring on 55-60% of farm calls, real fuel official 46.7% (61, 68, 67) / fresh 52.0%; at 20M 55.2% (77, 79, 76). But the search cache alone costs: full network every turn with it nnev3 53.8%, without nneb2v 63.3% (20M, official).
- Refinements at real fuel, official 420: search cache that re-runs after a target change + current target stays on no-score turns nnu4 47.4%; no cache + stays nnu5 38.6% (scoring too rare, target freezes).
- Smaller students, same recipe (20M, blend a=2, v92 banks, every turn; official 420 / fresh 498): 16x64 nneb2v 63.3% / 56.2%; 12x48 nns12x48 57.9% / 57.2% (moves agreement 57.1%); 8x32 nns8x32 53.3% / 59.2% (50.0%). Costs of a scoring: 45k, about 33k, about 24k.
- Fuel left at v92's target choice (nnfarm log): typically 50-70k, on big maps with many groups 30-50k. A scoring with small students is still about 38k (features 12k, camps 10k, self 5k, pool 3.5k, top 7k): real fuel, official 420: 12x48 nnu12 42.4%, 8x32 nnu8 40.0%: scoring on only 20-50% of turns. Next: two tiers: self + camps + rest of the network when it fits, else camps with the last pointer vector, else v92's choice.
- Two tiers nnt1 (16x64, no search cache) at real fuel: official 41.0% (62, 56, 54), overruns 1.1%, full tier about 25% of farm calls, camps tier about 55%. Worse than the stale-summary design nnlz3 49.0%.
- v92's search must stay fresh too (full network every turn, 20M, official 420): every turn nneb2v 63.3%; every 3 rounds, re-run after a target change nnev3b 54.8%; only when the target ends or changes nnh 48.8%.
- How much fuel would the fresh-scoring design need? nnf1 (A2_NN_NNUE, blend, no search cache) on a larger per-turn budget, both sides, official (v92, v92j1): 100k (nnt1) 41.0%, 130k 44.3%, 160k 55.0%, 250k 54.6%; 20M (with cache) 55.2%. Across real-fuel runs score falls with overruns: 2.5% -> 36.4, 1.1% -> 41.0, 0.7% -> 42-44, 0.3% -> 49.0, 0.13% (cap share 0.5%) -> 46.7.
- nnlz4 (stale-summary blend, 20k margin after the scoring, 4k at the end of the turn): official 46.0% (59, 69, 65) / fresh 56.8%. Against nnlz3 49.0% / 48.6% and nnl10 45.2% / 55.6%.
- Network only when v92 wants to change target or every k rounds (A2_NN_ENSEVERY, real fuel, official 420): k=2 nnk2 43.8%; k=4 nnk4 49.5% (68, 70, 70), cap share about 1%. As k grows this tends to v92 itself.
- A2_NN_XF checked in games (nnxd): enemy alive / dead / next return / sum, ally dead / next, per camp value per round, gems around, team plan steps, my plan order, rounds until my plan starts there; draft turn uses 7.54M of 10M; first champion turn 198k of 200k.
- Real-fuel summary so far (official 420 / fresh 498): nnl10 45.2 / 55.6; nnlz3 49.0 / 48.6; nnlz4 46.0 / 56.8; nnu3 46.7 / 52.0; nnk4 49.5 / not run. 20M blend with fresh everything 63.3 / 56.2 needs about 160k a turn or more. Long RL started on nnlz4 + A2_NN_XF (nn_rl5): NN_LAYOUT=4 NN_ENS=2 NN_LAZY=1.

## E124 (4 Nov) - checkpoints on held-out games; why scoring in farm() loses at 20M
- RL (nn_rl5, blend a=2, stale summary, A2_NN_XF, real fuel) stopped at iteration 8. Selection checks (official 420 vs v92, v92j1, v92j2 / pool-test 300): iter 0 46.9 / 52.0, 2 50.5 / 51.3, 4 53.6 / 48.3, 6 46.9 / 53.0. Held out, real fuel (official vs v92j3, v92j4, 280 games / fresh 498): nnc0 48.6 / 53.4, nnc2 49.3 / 53.6, nnc4 56.1 / 53.6, nnc6 45.7 / 50.8, nnc8 51.1 / 56.6. Then nnc4 on 50 random official maps x 2 vs v92j5: 57/100; 25 maze + 25 real-style unseen maps x 2 vs v92: 61/100 (e124_c4.py). nnc4 held-out official total 214/380 = 56.3% +- 2.5: first real-fuel network bot above v92 on official maps. Scores swing between iterations by more than noise: lower learning rate / more checks next time.
- 20M, official 420, all with blend a=2, v92 banks, A2_NN_VALID, LIVE build: A2_NN_NNUE with the fuel cuts nnd1 54.8%; + contact hold nnd4 56.7%; plain network at farm() nnd2 56.0%; + contact hold nnd3 51.4%. Against 61.9-63.3% for the plain network at the start of the turn (non-LIVE build). Pure-code difference to find: nnd_compare on nnda vs nndb.
- Fuel cuts as measured (nnd5log): features 10-10.6k (from 11.5k), camps 9.7-11k, self 4.4k (from 6.3k), pool + inputs 5.5-6k, top 10-12.7k: still 42k; overruns 1.0%, cap share 2-5%. Not enough: the 16-bit network is the next lever (8 lanes per instruction instead of 4).
- Discord ideas checked: memory.copy / memory.fill cost 10 fuel whatever the length (100 bytes or 100 KB; already on via -mbulk-memory-opt; platform builds from source with its own CMake, so no wasm-opt). v92 never sells; Tavi 2% of picks.
- What the blend's overrides are (nn_ens_why.py, 800 games at 20M, 205,742 override rows with both camps in view): 93.6% keep the current target against v92's wish to switch. Network's camp vs v92's, official: walking distance 8.3 vs 22.5, gems 29 vs 125, health left 2,061 vs 8,968, side margin 56 vs 39, allies near 0.69 vs 0.39. v92 wants to switch on 12.2% of turns; the blend stays on 63.1% of those (official 68.6%, generated 47.9%). Decision tree (nn_ens_rule.py, held-out maps, 74% vs 56% for the commoner answer): mainly stay unless the current target is respawning with more than about 28 rounds to go; v92's new pick on the enemy's side also says stay. Test: mk_v92stay.py (no fuel).
- Direct test of what a lost turn costs (mk_v92sk.py, v92 running out of fuel on 0.3% / 1% of turns, official 420 / fresh 498 vs v92): 0.3% 45.0% / 49.2%; 1% 53.6% / 48.0%. No measurable cost at these rates: the fall of score with overruns across runs was not caused by the lost turns themselves.
- Packaged nnc4: v4/submissions/nnc4_engine4.zip (not submitted). Findings pushed to the team repo branch agent2-neural (94237a9c, then every 17 minutes by gh_sync.py).
- Stay rule in plain v92, final (official 420 / fresh 498): stay unless respawning > 28 rounds v92s28 52.1% / 44.6%; unless respawning v92s0 51.0% / 46.2%; only against an enemy-side pick v92s28e 46.0% / 50.4%; soft stickiness 3.0 v92st3 50.0% / 49.6%. Rejected: the network chooses when to stay, a fixed rule does not.
- nnc4 package checks: built from the zip = same wasm as the tested bot (sha ca71b8404d0644c3); 20 games at real fuel: overruns 0.08%, turns at the cap 0.20% (max 0.70%), mean fuel 60k.
- The 8-point loss is the scoring moment, not the LIVE patches: plain network at the start of the turn in a LIVE build nnd6 62.9% (91, 86, 87 of 140), in farm() nnd2 56.0%, nnd3 51.4% (20M, official 420). Next: A2_NN_NNUE at the start of the turn, 16-bit (A2_NN_Q16; nn_q16_check.py: same blend decision on 99.78% of recorded rows, logits off by 0.04 on average).
- Same turn, same bot (nnfc, A2_NN_FCMP, 20M): features at the start of the turn vs at v92's target choice differ on 28.7% of farm turns, mostly the sighting entries of the enemy block; top camp differs on 0.60%, blend decision on 0.25%. So the decisions are nearly the same on a given state; 62.9% vs 51-56% may partly be which game line each build falls into. nnq1 (A2_NN_NNUE at the start of the turn, 16-bit): real fuel official 42.9% (overruns 3.3%, scoring on under half of the calm turns), 20M 54.6%. Scoring costs 34-38k: features 10-14k, camps 10k, self 3.6k, pool + inputs 3.3k, top 6.8k.
- CORRECTION: the "8-point loss from the scoring moment" was mostly noise. Deterministic games make each build one draw, and opponent noise (v92jN) does not fully fix that. With tiny noise on the bot's own target scores (A2_NN_LJIT, width 0.1; 20M, official vs v92, v92j1, 280 games each): start of turn nns1 59.3%, nns2 58.9%; in farm() nnf1 62.5%, nnf2 55.0%. Both about 59%. So the blend's real level at 20M is about 59% (not 63%), and scoring in farm() costs nothing. Tests now also need own-score noise.
- CORRECTION for nnc4: with own-score noise (A2_NN_LJIT width 0.1, real fuel, official vs v92, v92j3, 280 games each): nnc4 42.9%, 46.1% = 44.5%; its start nnc0 50.4%, 48.2% = 49.3%. The 56.3% on held-out noisy copies of v92 does not survive: most likely memorised lines against a near-deterministic opponent. Noisy copies of the opponent are not enough: own-score noise is needed in every check, and RL should select on it. nnc4_engine4.zip stays on disk but is not an improvement.

## E125 (4 Nov) - the blend inside the fuel
- A2_NN_LAZY + A2_NN_NNUE + A2_NN_Q16 (scoring in farm(), self + camps fresh, 16-bit), blend a=2, real fuel, official 420: nnq2 38.8% (65, 50, 48), overruns 0.47%, scoring on 30-85% of farm turns. nnq3 = nnq2 + A2_NN_SGAUTO (when the fuel cannot cover both, v92's search is skipped and its last pick stands, if still open): 50.2% (70, 71, 70), overruns 0.08%, turns at the cap 0.1-0.9%, scoring on 63-95% of farm turns (mostly 85-90%), mean fuel 55-77k. Scoring costs 36-38k: features 10k, camps 10k, self 3.4k, pool + inputs 3.2k, top 6.9k. First blend that fits; one draw so far.
- Retest on games no earlier test played (e125_c4.py, real fuel, no own-score noise; official: 70 maps x 2 vs new copies v92j6, v92j7, 10 maps x 2 vs v92j8; unseen: 75 maze + 75 real-style maps x 2 vs v92): nnc4 official 157/300 = 52.3%, unseen 148/300 = 49.3%; nnc0 (its start) official 149/300 = 49.7%, unseen 163/300 = 54.3%. Paired, nnc4 - nnc0: official +2.7 +- 3.9, unseen -5.0 +- 3.7. All nnc4 official without own-score noise since selection: 371/680 = 54.6%; with it 44.5% (560); unseen in all 209/400 = 52.3%. About level with v92 and with its start: no proven RL gain.
- Fitted blend nnq3, tests with own-score noise: official 48.6%, 49.6% = 49.1%; fresh (no noise) 49.6%, seed 1 47.6%. By size (noise runs): <= 40 54%, 41-60 54%, > 60 37%. Fuel is not why (e125_big.py): scoring on 91 / 85 / 84% of farm turns.
- Likely cause: distance fields. v92 builds them at the end of its turn only if the fuel left > the field's cost + 30-35k. On 100x100 a field costs about 43k. nnq3 on 00ambush (100x100): 1 of 12 built at round 100; nnc4: 0 of 12 at round 250; 00corners (71x71) nnq3 1 of 30 at round 100 (the count is per champion). Small maps: all by round 50. At 20M all are built on the first turn. So the network, and v92's own search, play the opening of big maps on straight-line distances. Test: margin 3k (mk_v92f.py for plain v92; A2_FIELD_MARGIN + A2_NN_FIELDS_FIRST for the blend).
- Field fix results (real fuel). Plain v92 + margin 3k v92f3: official 49.5% (74, 67, 67), fresh 52.2%. Fitted blend + margin 3k + no scoring until the fields are built nnq4: official 54.5% (77, 85, 67), fresh 55.0%; with own-score noise nnq4n1: official 56.2% (82, 76, 78). By size, official, noise run: <= 40 57%, 41-60 56%, > 60 55% (before: 54, 54, 37). First real-fuel gain that survives own-score noise.
