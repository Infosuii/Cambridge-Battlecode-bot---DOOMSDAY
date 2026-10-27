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
