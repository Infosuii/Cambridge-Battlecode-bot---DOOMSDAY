# Neural vs algorithmic: a fair assessment

The question that matters is not "net vs v76's leftover fallback". It is "net vs the best algorithm we can design for
the same decision". For each active learned or tuned component, this document separates three things:
- **A**: the existing learned or tuned subsystem
- **B**: v76's existing deterministic fallback (what runs when A is compiled out)
- **C**: a deliberately designed algorithm (specified in DRAFT_AND_ECONOMY_DESIGN.md and
  COMBAT_AND_COORDINATION_DESIGN.md)

E-numbers refer to FINAL_DEEP_ANALYSIS.md.

## 1. What the existing evidence does and does not establish

- **Established, A vs B** (E4, E5): 140 paired games per opponent, seed 71, two opponents.
- **Not established:**
  - A vs C. C does not exist yet.
  - Any comparison on unseen maps. All ablations used the 70 pool maps, on which the per-map tables and knobs were
    tuned.
  - Any ladder effect.
- **Noise:** a contested 140-game paired SE is about 55–70 gems (E7). Effects under about 120 gems are not resolved by
  one opponent; two opponents pooled resolve about 85.

## 2. Component-by-component

### 2.1 Camp selection: A2_CAMPNET (A) vs score_groups (B) vs TEP (C)

| | A: campnet | B: score_groups alone | C: TEP (DRAFT_AND_ECONOMY_DESIGN §A.3) |
|---|---|---|---|
| What it decides | Re-ranks the top-K of B's candidates for one champion; an off-base pick holds ≤40 rounds | Greedy per champion: value/cost with claims, belief and contest divisors | Team assignment: crews, respawn arrival, follow-up, contest probability, single capturer, progress contract |
| Inputs | 18 features: log score ratio, distance, gems, gold, harmless, camp mix, enemy ≤6, ally ≤4, need, own HP/maxHP/strength, round, bag, taken multiplier, base flag | Same world state | Same, plus the ledger timers, ally claims as crews, EnemyBelief pressure, the validated ObjModel |
| Fuel | 567/turn (1.3%), eval on 2.6% of turns (E2, E3) | ≈32% of turn fuel ≈13k (E2) | Target ≤13k mean (replan 3–8k, check <1k) |
| Measured value vs B | −58 [−174, +48] proxy; −91 [−225, +41] v65; +0.7..+1.6 deaths when removed | baseline | none yet |
| Why it helps (hypothesis) | The 40-round commitment stops per-turn re-scoring churn; the residual learns contest and size effects B mis-weights | — | Models what campnet can only guess: crew size, timing, contest, team-level opportunity cost |
| Main risk | Learned on v76's own lineage and pool maps | — | v82 / v58 failure modes; mitigated by the model-first gate and progress contract |

**Verdict: undecided.** It stays in v76 and in every fallback build. In the B architecture, TEP *replaces*
score_groups and campnet when `OCC_TEP ≥ 2`; campnet cannot sit on top of TEP because its features are B's score.

**Decisive experiment:** V-E2 in VALIDATION_PLAN.md.
- TEP must be non-inferior to v76 *with campnet* on the idle gate.
- In the contested league it must beat v76 with campnet on R500 retention and margin.

If TEP is non-inferior uncontested but only ties contested, keep v76 farming with campnet and redirect effort to EE.

### 2.2 Draft: A2_MLDRAFT (A) vs table/preset fallback (B) vs utility optimiser (C)

| | A: ML draft | B: fallback chain | C: exhaustive utility optimiser (DRAFT_AND_ECONOMY_DESIGN §B.2) |
|---|---|---|---|
| Scope | Maps outside the V70 table (40 of 70 pool maps, all unseen maps) | Map-class lineups, presets | Same scope as A |
| Inputs | 16 map aggregates + pick state | Map class (team size, size, density) | Camp mix vs clear power, gap access, contest index, revealed enemy picks, role constraints |
| Measured value | Removed: −116 [−258, +25] proxy, −112 [−298, +79] v65 on changed-draft games (E5) | baseline | none yet |
| Generalisation evidence | Trained on pool maps; unseen-map value unknown | — | LOMO on the v70 league: coarse features recover +9..+17 of an in-sample +134 (E6). Richer features untested |

**Verdict: retain provisionally.** It is cheap (draft turn only) and directionally positive. It is the only component
that already generalises by features. Replace it only if C wins the LOMO-plus-fresh-league test (V-D1).

The V70 table and the V71 map knobs remain primary on pool maps:
- **V70 table:** league-selected and transferred to the ladder (E21).
- **V71 map knobs:** removing them costs −100 / −171 (E4).

### 2.3 Global tuned parameters: A2_LAB knob vector (not a network)

A 48-value vector from black-box search (knob_es), applied every turn.
- Removing it together with the map knobs costs −148 / −197 gems and +2.4..+2.8 deaths (E4).
- **Verdict: retain.**
- In the B architecture the new modules expose their own small parameter surface: about 8 EE scalars and about 6 TEP
  scalars. These are re-tuned with the same league protocol (E21) and held-out maps. The old knobs keep acting
  wherever v76 code still runs.

### 2.4 The active search verdict: `tactical_decide` (APEX_TS_DECIDE=1)

- **What it is.** A search-based fight/run verdict judged with learned exchange-rate weights. It is a learned
  evaluator inside a bounded search, and it costs 3% of fuel (E2).
- **Evidence.** It is active in v76 and overrides the base formula (E25). It has never been ablated separately. Full
  tactical *search* (APEX_TSEARCH) is decisively harmful (−366, 16 fuel-outs), but that is a different, unbounded
  path.
- **Verdict: undecided; replace in B.** EE (C) takes over this decision.
- **Experiment, before EE stage 2:** v76 with APEX_TS_DECIDE=0, idle (sanity check) plus a 2-opponent contested run.
  This tells us how much of v76's fight quality comes from tactical_decide, i.e. what EE stage 2 must at least
  reproduce.

### 2.5 Compiled-out learned components

A2_POLICY, A2_ASSESS, A2_ENEMY_NET, APEX_TS_LOCALNET, NOVA_LEARNER, A2_MOVENET, A2_TILENET, A2_MLPLAN.
- None is active, and each failed its own gate historically.
- **Verdict: remove from the new controller's active design.** Keep the source in the repository; deleting evidence is
  not allowed.

### 2.6 Full tactical search (APEX_TSEARCH)

−366 [−470, −263] proxy and −325 [−453, −204] v65, with 16 fuel-outs/game and +5 deaths (E27). **Verdict: remove.**
Any search in the new design is analytic and bounded (EE), with a fallback path.

## 3. Summary verdicts

| Component | Verdict | Evidence | Validation that would change it |
|---|---|---|---|
| A2_CAMPNET | Undecided → replaced by TEP if TEP passes | −58 / −91, n.s., consistent sign | V-E2: TEP vs v76 + campnet, idle and league |
| A2_MLDRAFT | Retain (provisional) | −116 / −112 on changed drafts, n.s. | V-D1: LOMO plus fresh-league comparison with draft C |
| V70 draft table | Retain | Ladder transfer (E21) | Re-select only with the league protocol if the controller changes (V-T1) |
| V71 map knobs | Retain (v76 paths) | −100 / −171 significant, in-sample | Held-out-map re-tune for new modules (V-T1) |
| A2_LAB knobs | Retain (v76 paths) | −148 / −197 with map knobs | — |
| tactical_decide (learned evaluator) | Undecided; replaced by EE | not ablated | V-C0: APEX_TS_DECIDE=0 ablation; EE stage-2 league |
| APEX_TSEARCH | Remove | −366 / −325, 16 fuel-outs | — |
| Compiled-out nets | Remove from design | inactive, historically rejected | — |

## 4. Why the recommended new architecture is algorithm-first, and where nets may still earn a place

1. **The decisions that matter most are structural, not perceptual.** Team objective selection, combat valuation with
   objectives, and crew stances each combine a few well-understood quantities: HP, damage, distance, timers, bags.
   The rules give these exactly. Analytic models are cheap, explainable, calibratable on recorded fights, and fail
   visibly.
2. **Our learned components have never generalised beyond the lineage and pool they were trained on.** Mimic got
   0/120 and v83 intent was −65 (E17), and the nets' measured value is small (E4).
3. **Debuggability matters with 14 days left.** A value per stance can be logged, inspected, and fitted with a handful
   of scalars.
4. **Where nets may still help:**
   - draft on unseen maps (2.2)
   - a residual *calibration* layer on top of EE's analytic value, trained on counterfactual outcomes from the engine
     lab or puppets. It would be allowed only after EE ships and only if its held-out Brier score beats the analytic
     model.
   This is an optional post-finals item.
