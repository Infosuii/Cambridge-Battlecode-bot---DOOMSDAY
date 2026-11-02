# Retry protocol and retry queue (2026-11-01, user rule: "retry features before you reject")

No feature is rejected after one test. A single test can fail for reasons that are not the idea: one opponent build,
one map style, one parameter value, a trigger that never fires, or a piece that only helps when tuned together with
the rest (Agent 2's main finding: every v86h piece was neutral alone and +7 combined).

## Protocol: a feature is *rejected* only after all of R0-R3

| Step | What | Passes when |
|---|---|---|
| R0 fires | The build differs from the base (`tools/x1_flag_hashes.py`) **and** the behaviour triggers in games (telemetry count or changed-game count > 0) | Otherwise it is a dead path: fix the trigger, do not score it |
| R1 independent retest | Full gate: 70 ladder + 50 ladder-style + maze-style maps, both sides, vs v88 (`x2`) **and** its seed build `x2-s2` | Gain ≥ 0 on the total |
| R2 variants | At least two other parameter values (or a v2 that fixes the weakness the first test showed) | Any variant ≥ 0 |
| R3 combined | Included as a switch (and its knobs) in the joint structure + knob search (Phase 7) | The search keeps it on, or the final ablation shows a loss without it |

Status words: **kept** (passed the gate), **retry pending** (failed fewer than all of R1-R3), **dead path** (R0
failed; fix the trigger first), **rejected** (failed R1, R2 and R3). Until R3 has run, nothing is "rejected".

## Queue: every earlier rejection, reinstated

| # | Feature | First result | Retries still owed | Where |
|---|---|---|---|---|
| 1 | `X1_SECURE` kill-securing (mult 3.0) | -2/240 vs v86h only | R1 (x2, x2-s2, maze); R2 mult 1.5 / 6.0 and v2 (count every ally that can hit, release surplus attackers); R3 | 5060 retry round 1 |
| 2 | `X1_ALONE` regroup (ally 5, enemy 10) | -4/240 vs v86h only | R1; R2 ally 4 / 7 and enemy 8 / 12, and a cohesion variant (mild pull to allies only when enemies are near); R3 | 5060 round 1 |
| 3 | `X1_HUNT_SOLO` (3, 5) | 0 of 240 games changed | **dead path** in x1's default play (lone long hunts never happen). Retest under the early-contact plan, where hunting is common; then R1-R3 | after plan 1 |
| 4 | `X1_MASTERY` role-aware draft bias | -25..-59 margin vs v81hl (stats confounded by DZ games) | Recompute per-champion results from x1's own games vs v88; R2 bias 0.25 / 0.5; R1; R3 | 5060 round 2 |
| 5 | Nine sweep finalists stacked | -13 (greedy combos 71-76 vs 81) | R3 only: combined *with re-tuned knobs* in the joint search (stacking without re-tuning is not a test of the combination) | Phase 7 |
| 6 | Sweep stage-2 near-misses vs v81hl (flee-ally 80, snipe 79, pair 78, others) | not adopted | Sweep 1d vs v88 is R1; then R2/R3 | running |
| 7 | x2 merge (v86h structure into x1) | 53.5% vs 57.9% | Superseded by v88 = x2. Port v86h's four structural pieces (positioning, spacing, convergence, Lanchester override) into x1 **as separate switches**; R1 each; R3 together | PC day 1, 5060 gate |
| 8 | DZ line: altar locks, bold clears, focus fire, gold reweighting, early jobs | negative / neutral in DZ | Never tested in x1. Locks = `V58_LOCKS` (sweep 1d); focus fire = #1; gold weight = `UB_GOLD_MULT` / `APEX_GOLD_WEIGHT` knob variants; early jobs = plan variants. R1-R3 in x1 | sweep 1d, Phase 7 |
| 9 | DZ line: v81hl fight-or-run net (three threshold modes) | -24..-83 in DZ | x1 has it natively (`A2_ASSESS`, sweep 1d): R1 there; R2 threshold variants | sweep 1d |
| 10 | Agent 2: Lanchester model as the whole fight verdict | -6..-10 | Retry as a *plan-level* gate (enter or avoid early contact), not per-fight; R1; R3 | after plan 1 |
| 11 | Agent 2: rollout fight search (with/without paranoid weighting) | 17-27% vs v81 | Retry only with the arrival-time fight model as evaluator (idea bank #15); R1 | Phase 6 end |
| 12 | Agent 2: Heart of Ruin forced into the draft | 42-48% vs v81 | Retry as the early-contact plan's draft (QS2isLaw drafts Heart + Vendetta + Vesper); R2 with the HoR aggression knobs; R3 | after plan 1 |
| 13 | Agent 2: HoR aggression knobs | neutral in games | With #12 | after plan 1 |
| 14 | Agent 2: power play after a kill | measured only (first kill wins 50%) | Build it as a plan trigger (after a kill with bodies up, push denial / big bank for N rounds); R1-R3 | Phase 2 plan 3 |
| 15 | Agent 2: opponent stance rule | +9 vs stand-in, even vs v81 | Candidate input to the plan selector (Phase 4); R1 vs x2 and stand-in | Phase 4 |
| 16 | Agent 2: hunter pair | +2 in search | R1 in x1; R3 | 5060 round 2 |
| 17 | Agent 2: joint search trained on half the ladder | overfit (58% -> 47.6%) | Method, not a feature: rerun only with held-out maps of all three styles | Phase 7 |


## New features in the queue (2 Nov)

| # | Feature | Source | First result | Next |
|---|---|---|---|---|
| 18 | `X1_ANTIFEED` (K team deaths in W rounds -> team plays safe) | top-team games: 9/35 collapses (research/x1/TOP_TEAMS_2026-11-02.md) | quick screen K=3/5: 22+22 vs 17+19 | J006 (K 3/4/5/7, W 100/250) |
| 19b | `X1_FLEEDROP` 25 (drop the fled-from camp target) | audit F01 alt | quick screen 22 vs 17; **full gate vs x2 (PC): ladder 68 = 68, styled 41 vs 55** | R2: 15 / 40 / 60 in J010; R3 joint search |
| 19 | `X1_FLEEHOLD` (keep away from enemies seen within 8 for N rounds after a flee) | audit F01 (retreat/farm oscillation) | - | J007 (4/8/15) |
| 20 | `X1_TEAMWIN` (win-now counts the team's carried gems) | audit F03 (859 + 170 carried lost to 1083) | - | J007 |
| 21 | `X1_HEARTFIX` (fight forecast: Heart dash landing + missing-health damage) | audit B01 | - | J007 |
| 22 | `X1_SOAK64` (camp danger counts up to 64 members) | audit B02 | - | J007 |
| 23 | `X1_PRUNEFIX` (prune bound includes campwatch / dominant multipliers) | audit B03 | - | J007 |
| 24 | `X1_SIEGE_STRICT` (siege LOS cache used only when complete) | audit B04 | - | J007 |
| 25 | Throughput: waiting / staging while the enemy clears (dunes R431-471: 0 vs 177 collected) | audit F02 + top-team economy gap | - | knobs kWaitWeight, kStageTimeout, champions_needed in the joint search; plan 1/7 in the farm |
| 26 | Respawn-event ambiguity in the 8-byte protocol (mod 256 date read after 64 rounds) | audit H01 | - | fix as a switch if J005 rows show stale-event effects |

**Correction to the sweeps:** common.h's profile block sets many v81hl switches unconditionally (A2_KITFIX 25,
A2_BRIDGES 1, A2_APPROACHFIX 1, A2_ALTARFIX 3, ...). A sweep entry "same binary as x1" therefore means *dead code,
already on, or not overridable by --set*. The already-on ones are part of x1; the not-overridable ones (e.g.
A2_KITFIX bits) need a code switch to test, as X1_HEARTFIX does.

Fuel-fix versions 1-2 (no fuel gain) were superseded by version 3 (kept); they are not features and are not retried.

**Lesson (2 Nov):** the 38-game quick screen is a bug and fuel check only. X1_FLEEDROP 25 went 22 vs 17 there and
109 vs 123 on the full 240-game gate. No switch is ranked or dropped on quick-screen wins.

## Fuel-blocked features: fuel attempts (rule from Rishik, 2 Nov: 2-3 attempts to cut fuel, then rethink or abandon)

14 features gained wins in R1 but failed only on the fuel-out clause (anti-feed +27, plan 4 R100 +23, BURST2 +13,
stage 0.5 +11, prunefix +11, TS_VIS +11, wait 1.5/2.0 +8/+9, LOCKS +8, DISENGAGE +7, need 1.3 +6, BELIEF +5, plan 6
R150 +13, plan 4 R150 +18). x1 itself has 339 fuel-outs per 480 games, so a feature's +3..+20 is mostly game paths
reaching x1's own spikes.

| attempt | change | 8 hotspot maps vs x2 (16 games): fuel-outs / mean banked |
|---|---|---|
| - | x1 | 85 / 696 |
| 1 | `X1_BUSHPRE` labels bush clusters ahead of use (first-use labelling was 50-120k inside ward / ambush code) | 33-26 (floor 20) |
| 2 | on-demand labelling resumable too (`X1_BUSHPRE_LAZY`) | **26 / 862** (15 / 60) |
| 3 | `X1_SIEGEFUEL` siege LOS cache floor (a 49-camp group spent ~60k a turn) | 23 / 842 (55) |

Rounds 0-150 fuel-outs 64 -> 10. General fuel attempts stop here (3 done); J013 re-gates all 14 features on top of
BUSHPRE. A feature still failing on fuel there gets at most two attempts of its own, then a rethink or abandonment.

## Gate rule amendment (2 Nov, Rishik): fuel-outs on generated unseen maps count only slightly

Fuel-outs on generated maps whose realism is not checked against the official maps (maze set A/B) are reported but do
**not** fail a feature on their own. The fuel clause is judged on ladder + styled maps (the realism-screened suite);
a maze cell fails only on wins / deaths / gold, or if its fuel-outs rise by more than 25% *and* ladder/styled also
rise. Reason: on maze set A, 5 of 29 maps give 125 of x1's 165 fuel-outs (pc_maze_16: 71x71, 1-wide corridors, 34
groups per half, denser than any official map), so the count measures the generator's extremes. BUSHPRE on set A:
165 -> 157 (the maze fuel-outs have another cause; not chased until a map set is shown realistic).
