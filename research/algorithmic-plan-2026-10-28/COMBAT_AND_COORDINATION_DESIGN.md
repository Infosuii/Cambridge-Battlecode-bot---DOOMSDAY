# Combat decision authority, tactical algorithms and team coordination: detailed design

Status: a design, not implemented. E-numbers refer to FINAL_DEEP_ANALYSIS.md. Modules:
- M4 Engagement Evaluator (EE, flag `OCC_EE`)
- M5 Crew protocol (`OCC_CREW`)
- the survival rules folded into EE and TEP

## C.0 Requirements derived from the evidence

| Requirement | Why |
|---|---|
| R1. **One owner** of the fight/flee decision per champion per turn. No layer may overwrite another's verdict. | Five verdict writers over two booleans, last writer wins (E25). Every added layer was neutral or negative (E17). |
| R2. The decision values the **objective at stake** (camp progress, capture timer, bags, altar trip) alongside the fight outcome. | Retention 62–66% vs 93–96% (E10). The objective is absent from the current verdict (E25). |
| R3. **Crew-consistent stances** with hysteresis. | 28% step-away-without-hit, 2.6 reversals, split engagements 21.8% (E14). |
| R4. **Take free actions** while repositioning. | Same as R3. |
| R5. **Bounded analytic evaluation.** No rollout search, a fixed op budget, and fallback to the v76 path below the reserve. | tsearch −366 with 16 fuel-outs/game; v81 −532 (E27, E17). |
| R6. **Keep v76 executors** (flee pathing, kite, caster micro, gap-dash, position-and-attack) until individually beaten. | Tuned, load-bearing; the knob ablations show the combat stack's parameters matter (E4). |
| R7. **Calibrate** the model on recorded fights **before** it decides. | Learned exchange rates in tactical_decide and approximations in v81 were never checked against outcomes. |
| R8. Validate on **scenario replays and the ladder**, not local margin alone. | Local fight changes do not predict the ladder (E16). |

## C.1 Control flow inside a turn

```
if threat.present (visible enemy within 10, or EnemyBelief pressure at my position > θ_hidden):
    scene   = build_scene(me, allies≤10, enemies≤10, awake camps≤5)        // ≤ 1.5k fuel
    stances = candidate_stances(me, role, scene)                            // ≤ 6
    for s in stances: v[s] = evaluate(s, scene, objective)                  // analytic, ≤ 6k fuel total
    s* = choose_with_hysteresis(v, crew_stance, my_last_stance)
    if s* == CONTINUE: fall through to the objective executor (TEP role)
    else: execute(s*) via v76 executors; free-action rule; return
else:
    objective executor (TEP role)
```

**Early returns kept from v76**, run before EE because they are objective executors, not verdicts:
- `capture_stand`
- `camp_contact`
- `deny_capture`
- `bush_ambush`

Under OCC_EE each becomes a *stance option* instead: HOLD(capture) and AMBUSH. EE chooses among them with the same
value scale. In shadow mode (§C.6) the original order is kept and only logged.

## C.2 Scene and unit model

For each unit u in the scene:
- position, hp, max_hp
- shield (Varg / Heart self-shield, if visible)
- `dps_u` = strength. Ranged units must stand to hit. Heart's damage is multiplied by (1 + 0.5 · missing-HP fraction).
- `burst_u` = focus × spell multiplier, if a damaging spell is ready (cooldown ≤ 1; enemy cooldowns via
  `sdk_champion_cooldown`, as v76 does)
- `stun_u` = a ready stun with its range
- reach in τ rounds: `range_u + τ` (+2 at τ ≥ 1 if a dash is ready)
- `bag_u` in gems, and team

Champion-specific effects:
- C&I share one fate: a pair counts as one unit for death, with `hp = min(hp_C, hp_I)`.
- Marcella is stun-immune.
- Ren retaliates for 0.2 × focus when hit.
- Varg's splash adds strength to each other enemy adjacent to the target.

Hidden enemies: add `n_hidden = max(0, pressure(pos, 5) − n_visible_near)` phantom units at the average visible-enemy
stats, with weight 0.5. This mirrors v76's `kBelief` team-fight term.

## C.3 Candidate stances (≤6)

| Stance | Meaning | Executor (v76 reuse) |
|---|---|---|
| FIGHT(t) for the best 2 targets by v76's key `ttk/worth` | Commit to killing t with the crew | position_and_attack / gap-dash / cast_on_enemy / attack + reset; casters use caster_micro(engage = true) |
| HOLD(o) when on or near the objective | Stay on the capture or camp tiles; hit whatever enters range | capture_stand logic; attack/cast in place |
| KITE(t), ranged only | Keep spacing, shoot when safe | kite_step, kite-cast |
| DISENGAGE | Move toward the crew centroid or the objective's safe side, free hits first | regroup_from, retreat_from, flee-hit |
| RETREAT | Go home: walk, bush recall, or recall when safe | flee path, escape_or_stand, bush recall |
| CONTINUE | Enemy irrelevant within the horizon | the objective executor |

## C.4 Value model (gem-equivalents, horizon H = 4 rounds)

**Simulation.** Each stance runs a deterministic **focused exchange simulation** at most twice (an optimistic and a
pessimistic variant):

```
contact point x = t.pos (FIGHT), objective tile (HOLD), my pos (others)
join time:  τ_a = max(0, cheb(a, x) − range_a)  for allies in my crew or with FIGHT/HOLD stance messages (else ×0.5 weight)
            τ_e = max(0, cheb(e, x) − range_e − 2·dash_ready_e)  for enemies
for τ = 1..H:
    our_dmg   = Σ_{a joined} dps_a + Σ_{a joined, spell ready, first time} burst_a     (applied to our focus target)
    their_dmg = Σ_{e joined, not stunned} dps_e + bursts                               (applied to their focus target)
    our focus: FIGHT target t, then lowest EHP; their focus: lowest EHP ally in reach, ties → larger bag
    stuns: a ready stun of ours removes the highest-dps enemy's next τ; theirs likewise
    remove dead units (C&I pair dies together)
```

Variants:
- **Optimistic**: hidden phantoms ×0, enemy spells assumed on cooldown unless observed ready.
- **Pessimistic**: hidden phantoms ×1, enemy spells assumed ready.
- Combined value: `V = (1 − π)·V_opt + π·V_pess` with `π = 0.5 + 0.3·[my bag ≥ 40]`.

**Value of the outcome:**

```
DeathCost(u) = bag_u + λ_gold·100 + λ_tempo·60·ρ̄_u          // ρ̄_u = the unit's farming rate (GE/round) from TEP; λ_tempo ≈ 1
KillValue(e) = bag_e + λ_gold·100 + λ_tempo·60·ρ̄_enemy       // ρ̄_enemy from EnemyBelief (default: our median ρ̄)
V(s) = Σ_{e killed} KillValue(e) − Σ_{a killed} DeathCost(a)
     + V_obj · P_obj(s) − V_obj_lost(s)                       // objective term from TEP
     − ρ̄_me · rounds_lost(s)                                 // time diverted from the objective
```

The objective term:
- `V_obj = Reward(C,g) · progress`, from ObjModel; progress is the HP removed or the capture-timer fraction.
- `P_obj(s)` is the probability the objective completes under s: HOLD high if the simulation keeps our holders alive;
  DISENGAGE or RETREAT low (a capture resets when the region is empty or contested).
- `V_obj_lost` is progress forfeited: a capture timer resets, and camps heal or sleep after 2 rounds without an
  in-range champion.

RETREAT and DISENGAGE use an **escape model**:
- Pursuit rounds n = the rounds in which an enemy's reach covers my path to the safe point (ally cluster of ≥2 within
  3, or spawn). Count along the v76 flee-field path, with dashes.
- Damage taken `D = Σ_e dps_e · n_e + bursts`.
- `P_die = clip((D − hp)/σ_D + 0.5, 0, 1)`, with `σ_D = 0.25·D`.
- A ranged champion that is retreating cannot shoot (rules), so count no damage dealt.

**Decision.**
```
s* = argmax V(s)
hysteresis: if my last stance (or crew stance) was FIGHT/HOLD and is still feasible,
            switch to DISENGAGE/RETREAT only if V(new) > V(old) + m_commit,
            m_commit = 0.15·DeathCost(me)    [personal override: always switch if P_die_next_round(me) > 0.5]
            symmetric margin for re-engaging after DISENGAGE (prevents reversals, E14)
```

**Free-action rule (R4).** In every stance, before or after moving, take any legal basic attack or ready damaging
spell on an enemy in range that does not consume an allowance the stance needs this turn:
- melee may attack and then move
- ranged may shoot only if the stance does not need the move this turn
- spells that exclude walking are only cast if the stance does not move

This generalises NOVA_FLEE_HIT, which is melee-only today.

**Complexity.** The scene has ≤11 units. One simulation is O(H · n) with n ≤ 11, about 4 × 11 × ~30 ops ≈ 1.3k ops.
Six stances × 2 variants come to ≤16k ops, roughly 8–12k fuel including scene construction (fuel per op is about 0.5–1
in our wasm). Only on contact turns (≈7% of v76's fuel today, E2). A hard deadline applies: if fuel_remaining <
reserve + 15k on entry, return to the v76 `handle_enemies` path (compiled in).

## C.5 Calibration before deployment (R7)

1. **Dataset.** Contact situations from saved local replays (SA-P-base, SA-C-base and the v70 league runs) and the
   deep-analysis examined ladder replays. Use the examined set only; the hands-off set is untouched. Use the existing
   decoders: `tools/replay/fight_review.mjs`, `death_context.mjs`, `bench_contact.py`.
2. **Targets.** For each (unit, contact round): deaths within 4 rounds, HP change, objective completion.
3. **Check.** Run the analytic model offline (a Python port of §C.4). Compare predicted vs actual:
   - death Brier score must beat the base rate and the v76 `in_danger` flag as a predictor
   - HP-loss MAE ≤ 25% of the mean
4. **Fit.** Only the scalar parameters, about 8: π weights, λ_tempo, m_commit, the hidden-phantom weight, σ_D, the
   join-probability weight for non-crew allies, and θ_hidden. No neural model.
5. **Shadow mode** (in-game, behaviour unchanged). Log EE's choice next to v76's actual action every contact turn.
   Inspect the disagreement classes before enabling the module.

## C.6 Rollout stages for EE (each a separate flag value)

| `OCC_EE` | Behaviour | Gate |
|---|---|---|
| 0 | v76 byte-identical | binary hash equals v76 |
| 1 | shadow: compute and log only | fuel p99 ≤ 90k, fuel-outs ≤ 0.6/game, logging off in release |
| 2 | EE owns the **verdict only**: maps s* to v76's (winning, in_danger) flags; v76 executors and early returns unchanged | scenario suite + league non-inferiority |
| 3 | EE owns stances, including HOLD/AMBUSH replacing early returns, plus the free-action rule | scenario suite + league + deaths −1/game |
| 4 | Crew stances via M5 | as 3, plus the split-engagement metric |

Stage 2 is the narrowest replacement that tests R1 + R2 without touching execution. It is the first combat
experiment to run.

## C.7 Survival rules (inside EE and TEP, not a separate layer)

- **Bag-aware death cost.** DeathCost includes the bag, so carriers disengage earlier. Banking (DRAFT_AND_ECONOMY_DESIGN
  §A.4) triggers earlier under pressure.
- **Respawn re-entry** (targets D3 repeated deaths, E9).
  - For 25 rounds after a respawn, TEP adds a crew-join bonus and forbids solo objectives where pressure exceeds 0.3.
  - EE uses the pessimistic weight π = 0.8 for the respawned champion.
  - What differs from the rejected death-watchdog: it is a *bias inside objective choice and fight valuation*, not a
    freeze. The planner still farms safe objectives.
- **No late trickle-in.** A champion joins a fight only if `τ_join ≤ predicted fight end − 1`. Otherwise it continues
  its objective or regroups. This is the "dive deaths 5.1 vs 1.7" pattern (E15).
- **Lone-champion rule.** Folded into the join probability: no crew within 8 means FIGHT values carry no ally
  support, so lone fights win only on a clear margin.

## C.8 M5 Crew protocol (coordination)

### C.8.1 Shared-memory budget (E26)

All 64 bits are in use today: 6×7 claims plus a 22-bit beacon multiplexing a sighting or a camp event. The OCC
protocol keeps the claims unchanged and re-specifies the beacon as **2 type bits + 20 payload bits**:

| Type | Payload (20 bits) | Writer | Freshness |
|---|---|---|---|
| 00 SIGHTING | x 7, y 7, round mod 32 (5), distress 1 | any champion seeing an enemy | 4 rounds (as v76) |
| 01 CAMP_EVENT | group 7, respawn round mod 256 (8), spare 5 | capturer / observer | until consumed |
| 10 CREW_STANCE | leader slot 3, stance 3, target enemy index 3 (0–5, 7 = none), rally x/4 5, rally y/4 5, spare 1 | crew leader in contact | 2 rounds |
| 11 TEAM_MODE | mode 3 (FARM / CONTEST(g) / DEFEND_BANK / ENDGAME_RACE / REGROUP), target 7, round mod 64 (6), spare 4 | lowest-slot alive champion | 8 rounds |

Pre-emption priority: CREW_STANCE > fresh distress SIGHTING > TEAM_MODE > CAMP_EVENT > stale SIGHTING. A fresh
message is never overwritten by a lower-priority one; this keeps v76's rule that teammates' fresh sightings stay.

Enemy index = position in `bc::champions(team::enemy)` order (v76's `enemy_handles`). Reads and writes are whole-word
and happen within a single champion turn, so there are no races.

### C.8.2 Crews and leaders

- **Crew formation.** TEP's assignments: each claim carries a group id; champions whose claims share a group, or whose
  objectives are within 8 tiles, form a crew.
- **Leader.** The lowest slot among crew members within 8 of each other. With `set_priority` this can be made the
  first actor, so its stance is fresh for the others in the same round.
- **Stance adoption.** A member adopts the leader's CREW_STANCE unless its personal override fires (P_die_next > 0.5),
  or it is more than 8 tiles away (out of crew).
- **Disagreement.** A member's own EE result is used only to *raise* caution (FIGHT → DISENGAGE), never to dive alone.

### C.8.3 Reinforcement, protection, deadlock

- **Distress.** A distress SIGHTING turns into a DEFEND objective in TEP with value
  `Σ ally DeathCost · P_save(arrival)`. Champions whose own ρ and position make arrival in time join; others do not
  (the trickle rule).
- **Banking protection.** A carrier with bag ≥ B_protect (start 60, the v76 risk threshold) heading to an altar under
  path pressure > 0.4 gets an ESCORT role from the nearest crew-mate whose ρ loss is smallest.
- **Deadlock prevention.**
  - Crew size ≤ available-within-15-rounds; never "need = team_size". A2_GATE_JOB deadlocked exactly so.
  - The progress contract releases stuck jobs.
  - Waits are bounded by v76's stage timeout.
- **Reassignment.** Any TEP replan; crews dissolve when their objective completes or is released.

## C.9 Tactical micro and pathfinding

- Keep v76 primitives:
  - the SDK movement mask
  - `walk_toward` with bitboard goals
  - flee fields
  - `kite_step`, `caster_micro`, `position_and_attack`, gap-dash
- **Optional micro planner (concept S11).** A bounded enumerator of {move ∈ 9} × {attack target ∈ ≤3} × {spell ∈ ≤3
  options}, scored by the §C.4 immediate-damage terms plus position safety (enemy reach count). Budget ≤8k fuel with
  an anytime cut-off.
  - It must beat `caster_micro` in a scenario A/B before use.
  - v81's failure (immediate damage is not a sufficient objective) is why it scores position safety and stance
    consistency, not damage alone.
- **Pathfinding.**
  - Reuse v76's per-group distance fields, built incrementally under a per-turn budget (`build_fields`), plus the
    spawn and altar fields.
  - EE escape paths use the flee field. No new BFS in the hot path.

## C.10 Evidence summary for this design

| For | Against / risk |
|---|---|
| Fragmented, objective-blind verdicts (E25); fight-quality gaps (E14); deaths drive both outcomes (E11–E12, E9) | Fight changes never improved local results (E17); the knob-tuned stack is load-bearing (E4) |
| Analytic model fits the fuel budget; tsearch failed by fuel, not by concept (E27) | The analytic model may miscalibrate. Mitigated by the §C.5 offline gate and shadow mode |
| Puppet harness gives exact scenario replays (E18) | Puppets don't react, so the horizon is ≤10 rounds and only immediate outcomes are measurable |
| Crew stance attacks the reversal / split pattern directly | 20 payload bits limit stance detail; leader stale for one round if the leader acts last |
