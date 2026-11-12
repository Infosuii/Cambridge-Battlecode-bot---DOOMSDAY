# Scenario walkthroughs, stress tests and failure modes

> **Carried forward into the DOOMSDAY Zero (clean-slate) package, 2026-10-28.**
> - "TEP" means DZ's economy planner, and "executors" means DZ's action scorer (ALGORITHM_SPECIFICATIONS §6).
> - v76 appears only as a benchmark and as the source of lessons. DZ reuses no v76 code.
> - Where this text mentions a v76 fallback path, DZ uses its own SafeMode (MASTER_ARCHITECTURE §3).


These are hypothetical design demonstrations, not tested performance. Numbers use engine stats and the formulas in
ALGORITHM_SPECIFICATIONS.md, with λ_gold ≈ 0.25 early and ρ̄ ≈ 0.45 GE per champion-round unless stated.

## Part A: walkthroughs

### W1. Normal economy opening (5 champions, medium map, no early contact)

1. **Observed state.**
   - Round 1. Lineup: Vesper, Vendetta, Heart, Marcella, Ryth.
   - Three elk-size groups and six gem clusters lie on our half. The opening schedule is in draft memory.
2. **Strategic objective.** FARM. Maximise R0–R120 GE income, and complete the first emblem by about R55.
3. **Candidates.**
   - Option 1: all five on the nearest elk group, E1 (d ≈ 9).
   - Option 2: 3 on E1, 1 on cluster circuit K, 1 on elk E2 (d ≈ 14).
   - Option 3: v76-like individual greedy.
4. **Evaluation.**
   - ObjModel: E1 with 3 champions takes T_clear ≈ 2400/185 ≈ 13 rounds. The 4th and 5th add DPS, but the marginal
     gain is smaller than their alternatives: Δteam(C+c) < ρ_alt(c), because a cluster runner earns about
     0.44 GE/round alone.
   - The opening prior ×1.3 favours the stored schedule, which is option 2.
5. **Chosen action.**
   - Vendetta, Heart and Ryth clear E1. Marcella joins and captures it: she is the gem-rich capturer and gets bank
     gold later.
   - Vesper runs clusters K1→K2→K3. The gear planner wants Prospector/Capture on the cluster runner; Vesper's +33% does
     not apply to clusters, so the runner role could equally be Ryth. TEP compares the two.
6. **Communication.** Claims: E1 ×3 (on-site codes), K1 ×1, E2 ×1. CAMP_EVENT when E1 is captured, carrying its
   respawn round.
7. **Follow-up.**
   - At the E1 capture, the follow-up lookahead sends the crew to E2.
   - Vendetta's kill-reset (camps too) is credited in DPS.
   - The first shopping happens on the next recall, or on a death.
8. **Failure and fallback.**
   - The schedule is dropped if E1 is contested (pressure > 0.5).
   - If ObjModel predictions miss by more than 30% (logged), TEP still works: assignments are re-solved every 8
     rounds and on events, and the contract releases stuck jobs.

### W2. Contested high-value camp (golem group, our 3 vs enemy 2 arriving)

1. **Observed.**
   - Our crew of 3 (Heart, Vendetta, Ryth, HP 70–90%) has the golem at 35% HP.
   - Two enemies (Vesper, Marcella) are seen at distance 9, moving in. Bag 20.
2. **Strategic objective.** Golem reward: 36 gems + 160 gold, about 76 GE. Progress 0.65, so V_obj ≈ 49 GE.
3. **Candidates.** FIGHT(Vesper), FIGHT(Marcella), HOLD(golem), DISENGAGE, RETREAT.
4. **Evaluation (EE).**
   - Join times: the enemies hit in 6–7 rounds (beyond H = 4) unless Vesper dashes, which gives about 4.
   - HOLD: the clear finishes in 1750/185 ≈ 9.5 rounds. The enemies arrive before capture, so the model plays τ = 1..4
     with the enemy joining at τ = 4.
   - Pessimistic variant: Vesper (45 str ranged) and Marcella (nuke 2×F) against our 3 with the golem still hitting us
     (120/round on one champion).
   - P_obj(HOLD) ≈ 0.6 (we have 3v2 locally). Lanchester S(us)/S(them) ≈ (2900·185)/(2200·110) ≈ 2.2.
   - V(HOLD) ≈ +0.6·49 − 0.3·DeathCost(Ryth ≈ 55) ≈ +13. V(FIGHT, Vesper) is similar but loses golem progress
     (camps sleep after 2 rounds). V(DISENGAGE) ≈ −49·0.65 (progress lost) ≈ −32.
5. **Chosen action.** HOLD. Keep clearing, with the free-action rule hitting enemies that enter range. The crew leader
   (Heart) writes CREW_STANCE = HOLD with the rally on the golem.
6. **Communication.** Distress is not needed (3v2). TEAM_MODE CONTEST(golem) is published, so a fourth ally within 15
   rounds gets a DEFEND objective if `ρ_defend > ρ_alt`.
7. **Follow-up.** Capture by the champion with the farthest next objective, if alive. Otherwise the new capturer is
   whoever is on the tiles.
8. **Failure and fallback.**
   - If a third enemy appears (S ratio drops to about 1.1), the pessimistic variant swings V(HOLD) negative. The
     margin rule m = 0.15·DeathCost delays the flip by about one round. DISENGAGE goes toward the safe side; the
     progress is lost.
   - Logged for calibration.

### W3. Unfavourable teamfight (our 2 vs their 4)

1. **Observed.** Our Vendetta (60% HP, bag 35) and Marcella are clearing a wolf. Four enemies emerge from a bush at
   distance 6.
2. **Objective.** The wolf is worth about 14 GE, progress 0.3.
3. **Candidates.** FIGHT ×2, HOLD, DISENGAGE, RETREAT.
4. **Evaluation.**
   - S ratio ≈ 0.4.
   - Pessimistic FIGHT: both die by τ = 3, so V ≈ −2·55 − 35 ≈ −145.
   - DISENGAGE toward the third ally 7 tiles away: the escape model gives about 2 pursuit rounds, P_die ≈ 0.3 for
     Vendetta. V ≈ −0.3·(55 + 35) − 4 ≈ −31.
   - RETREAT home is longer, P_die ≈ 0.45.
5. **Chosen.** DISENGAGE for both, as a crew stance. The free-action rule: Vendetta (melee) hits the adjacent enemy
   before moving if it is in range.
6. **Communication.** SIGHTING with distress and count 4. Our third champion's TEP gets DEFEND, but only if it can
   arrive before the predicted fight end. Otherwise the no-trickle rule stops it.
7. **Follow-up.** Regroup at the rally point; TEP replans. If two of ours die, TEAM_MODE becomes REGROUP.
8. **Failure.** If the bush ambush puts enemies adjacent at turn start, the personal override (P_die_next > 0.5) lets
   Vendetta dash away immediately.

### W4. Favourable teamfight (our 4 vs their 2, one enemy carrying 80 gems)

1. **Observed.** An enemy Vesper (bag 80, 55% HP) and Marcella are tributing near their altar. Our 4 are at
   distance 5–7.
2. **Objective.** KillValue(Vesper) ≈ 80 + 25 + 27 ≈ 132 GE. A tribute is not interrupted by damage, only by stun
   or death: 8 rounds remain for 80 gems.
3. **Candidates.** FIGHT(Vesper), FIGHT(Marcella), CONTINUE.
4. **Evaluation.** S ratio ≈ 3.5. Optimistic and pessimistic variants both kill Vesper by τ = 2–3, because our stuns
   interrupt the tribute (Marcella is immune). V(FIGHT, Vesper) ≈ +132 − 0.1·55.
5. **Chosen.**
   - FIGHT(Vesper), with stuns first (they cancel the tribute).
   - Our Marcella, Heart (dash landing stun) and Vendetta (reset on kill, then a follow-up on Marcella).
6. **Communication.** The leader (lowest slot) writes CREW_STANCE FIGHT, target index Vesper.
7. **Follow-up.** After the kill, re-evaluate FIGHT(Marcella). Then the bag-carrying killer's BANK hazard rule
   triggers at once, since pressure is high and an altar is near.
8. **Failure.** If an altar lock exists, we could also place our own lock to cancel the tribute when gold ≥ 10: the
   altar-lock executor is in the free-action list during ENDGAME or a carrier fight.

### W5. A champion carrying a valuable bag (Marcella, 140 gems, mid-game)

1. **Observed.** Bag 140. The altar is 12 tiles away, there is an enemy sighting 2 rounds old near the route, and HP
   is 80%.
2. **Objective.** Banking takes 12 + ceil(14) = 26 rounds, during which damage does not interrupt (stun-immune).
3. **Evaluation.**
   - Hazard: pressure 0.6 gives h ≈ 0.002·(1 + 3·0.6) ≈ 0.0056 per round.
   - T_next with no on-route altar: about 40 rounds of further farming.
   - `bag·h·T_next ≈ 140·0.0056·40 ≈ 31 GE`. `C_trip ≈ 12·0.45 − λ_gold·2·140 (Marcella) ≈ 5.4 − 70 < 0`.
   - So bank now. For Marcella banking is almost always profitable: +280 gold.
4. **Chosen.**
   - BANK. DEFEND_BANK mode, because bag ≥ 60 and there is pressure on the path, so the nearest crew-mate gets ESCORT.
   - Altar choice penalises pressure.
5. **Communication.** TEAM_MODE DEFEND_BANK, target altar.
6. **Follow-up.** After tributing, TEP reassigns. The gear planner may spend the 280 gold on the next spawn visit.
7. **Failure.** If an enemy lock is seen on the altar, choose the next altar. If a burst threat appears mid-tribute,
   EE compares RETREAT (the bag is kept, the tribute cancelled) with staying. Marcella can't be stunned, and death is
   the only risk, so stay unless P_die > 0.5.

### W6. Concentrated objective / unusual map (stampede-like sole gem group; guardians-like gated altar)

1. **Observed (sole gem group).** One 20-monster group holds about 90% of the map's gems (v76 has an `A2_SOLE_GEM`
   special case).
2. **Objective.**
   - ObjModel: crew DPS needed for a feasible clear without deaths (`D_taken` vs crew HP).
   - Gold farming elsewhere until the gear threshold makes it feasible.
3. **Candidates.** Farm gold clusters and wolves, or attempt the sole group.
4. **Evaluation.**
   - TEP's `Feasible` flag is false until crew HP × Jungle and DPS is sufficient. The gear planner values Jungle and
     Monster highly here, because cluster and wolf rates are low and the sole group's reward is enormous.
   - When feasible, CONTEST(g) mode puts the whole team on g. ρ for a 5-crew exceeds every alternative.
5. **Chosen.** Gold phase, then a whole-team cycle on the group, with capture rotation.
6. **Communication.** TEAM_MODE CONTEST(g).
7. **Follow-up.** Respawn arrival timing via ledger timers.
8. **Failure.** If the enemy holds the group, EE values HOLD/FIGHT at the region. If S is unfavourable, farm and wait.
   This is where a fixed special-case rule may still be better: DZ includes a sole-group rule (whole team once
   the crew is feasible) in its economy planner as a fallback if the feasibility model is wrong (V-M1 tests this).

**Gated altar** (02guardians: one altar reachable through gate-camp tiles).
- The BANK objective's altar path cost includes the gate groups. Clearing them becomes a prerequisite objective
  (value = bank access for the whole team).
- The ledger's altar-accessibility flag drives this.
- Known historical failure: A2_GATE_JOB's need = team_size deadlocked. **Never require the full team**; crew size
  comes from feasibility.

## Part B: stress tests and mitigations

| Stress case | Likely failure | Mitigation or experiment |
|---|---|---|
| Large map (100×100) early | Fields not built, so wrong distances and bad commitments | 1.3·cheb estimate flagged low-confidence: no assignment more than 30 tiles away until a field exists; fields for the top-25 groups first |
| Small map (30×30), constant contact | EE fires every turn; TEP starves | EE CONTINUE when no threat within the horizon; CONTEST mode; validate on compact maps where Mite was one-sided (0/7) |
| Unusual terrain (islands, holes) | Unreachable objectives; dash-only paths | A field marks them unreachable; the draft's mobility utility; no TP-crystal bridging (−345..−414 historically) |
| Unseen map configuration | Per-map tables absent | General defaults; kNN profile only if LOMO > 0; ObjModel is rule-derived |
| Concentrated camps | Feasibility mis-estimated | V-M1 includes multi-camp groups; keep DZ's sole-group fallback rule |
| Gated objectives | Deadlocks | No full-team requirement; contract release; gate as a prerequisite objective |
| Fast opponents (dash rushers) | Late threat detection | Join time counts dash (+2); bush phantoms through pressure; rush detection by style classifier |
| Heavy combat pressure | Income collapse | CONTEST/REGROUP modes; cluster runners kept away from pressure; P_ok lowers contested objectives |
| Different compositions (C&I, casters) | Model errors (linked fate, kiting) | C&I as one fate unit; ranged move-or-attack rule in micro; per-champion calibration terms |
| Low-health team | Repeated deaths | REGROUP mode; recall-and-heal is cheap (spawn heals 100%); pessimistic π after respawn |
| Unreachable objective | Wasted travel | The field says unreachable, so the objective is excluded; contract release |
| Sudden loss of vision | Stale belief | Reach ramp grows uncertainty; phantoms; never assume an enemy is absent |
| Banking unavailable (locks, gated) | Bags accumulate | Altar choice penalties; lock removal (5 hits) as an objective if the bag is large; DEFEND_BANK |
| Stale memory or claims | Duplicated jobs | Claim weight 0.5 when stale; on-site codes; CAMP_EVENT |
| Fuel exhaustion | Suspension mid-fight | Governor tiers; hard reserve; FALLBACK to DZ SafeMode; stale-turn guard after resumption |
| Repeated deaths | Snowball | Respawn re-entry rule; REGROUP; no trickle-in |
| Losing the early game | Over-aggression to catch up | Value is GE, not "catch up"; the race controller uses true T estimates; avoid all-in unless T_them is small |
| Unexpected strategies (perma-recall, turtling) | Exploitable heuristics | Channel-age rule for target worth; style classifier (optional); scripted style opponents in the league |
| EE miscalibration | Over-commitment | Offline Brier gate; shadow mode; LEAN tier uses the conservative mix |
| Protocol bug | Silent coordination failure | Encode/decode unit tests; claim codes unchanged; module error counters |

## Part C: comparison with historical failures, and what *materially* changed

A statement that a failure is "addressed" counts only if there is a **mechanism plus a gate that would catch a
repeat**.

| Historical failure | Root cause | What is materially different | Gate that would catch a repeat |
|---|---|---|---|
| v58 director (0/20 screens), A2_DPLAN −217 | Stale schedules; forced carry draft | Plans are advisory or re-solved every 8 rounds and on events; progress contracts; no forced draft | V-E2 idle non-inferiority before any contested run |
| v82 coalition scheduler (−89..−115 R100–R300 gold, uncontested) | Unvalidated travel and clear model; jobs held without progress | ObjModel must pass a replay accuracy gate first; contract release | V-M1 (offline), then V-E1 shadow disagreement review |
| v81 action sequences (−532, 12 games) | Immediate-damage objective; fuel overrun | Value includes deaths, kills, objective and tempo; analytic, ≤12k with governor; v76 executors kept | V-M2 Brier gate; G2 fuel gate |
| v83 learned intent (−65 vs proxy) | Imitation without value | No imitation; value-based stances | V-C1 |
| v84 fixed denial guards (−886) | Starved our own economy | Denial only as a valued objective; off by default | — |
| v85 rendezvous (−231) | No gear or bank follow-through; unbounded loops | Follow-up lookahead; BANK/SHOP objectives; budgets everywhere | V-E2 R500 metrics |
| v79 team fight (−24..−107) | Verdict layers added on top; long leave locks | Replaces the verdict stack; stances expire; TEP resumes immediately | V-C1/C2 league and puppets |
| Tactical search (−366) | Unbounded playouts, fuel | Analytic evaluation only | G2 |
| Funnel / meta draft / carry (−89..−141) | Copied surface choices | Single capturer only within the crew; draft re-selected by the league on the final controller | V-T1 |
| Seed- and lineage-overfit wins | Reused seeds; self-play only | Seed ledger 101–124; held-out maps; scripted style opponents; ladder duel before release | G5–G7 |

**What has *not* changed, and remains a risk.** We still cannot validate combat changes locally against true top-team
behaviour. The puppet harness, the scripted style opponents and the ladder duels reduce this risk but do not
remove it. That is why EE ships in stages, and why F + D is the fallback.
