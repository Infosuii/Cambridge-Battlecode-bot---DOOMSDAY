# Validation plan: fair experiments, acceptance criteria and performance gates

**Nothing here has been run.** It is all for the implementation phase.

## 1. Instruments and their limits

| Instrument | Resolution | Limit | Use |
|---|---|---|---|
| Idle bench (bots/idle81, 70 maps × 2 sides) | Paired SD 20–180 (sharp) | Uncontested only | Mechanism gates (economy, timing, fuel) |
| Contested league: v65, v61, v58, proxy, v76 | 140 games: SE ≈ 55–70; 5 opponents: SE ≈ 27 | All our lineage; fight changes don't predict the ladder | Non-inferiority, retention, deaths |
| Scripted style opponents (T17): rusher, perma-recall turtle, cluster farmer | as the league | Approximations of styles, not the teams | Robustness to styles our lineage lacks (AlphaStar league lesson [B14]) |
| Puppet takeovers (deep-analysis harness; 12 byte-exact reproductions) | Exact state | ≤10-round horizon, enemies scripted | Scenario regressions (M1 and others) |
| Offline replay models | — | Observational | ObjModel and EE calibration gates |
| Ladder duel (top 12, 120 games) | ±54 gems | **Activates arms: user approval each time** | Final promotion |

The deep-analysis reserved set (165 games) **is spent** (deep REPORT.md) and cannot serve as a holdout.

## 2. Ground rules

- **Seeds.** 101–110 for development and selection; 111–120 for validation; **121–124 once-only release holdout**.
  Seeds 3 and 4 are reserved and must never be used. Record every use in `research/v86/SEED_LEDGER.md`.
- **Held-out maps** for new-module tuning: every 5th map of the sorted 70-map pool (14 maps). New scalars are never
  tuned on them.
- **Release holdout.** The frozen candidate and v76s on seeds 121–124 × all 70 maps × both sides × 5 opponents, run
  **once**. The plan, cell list and hash are recorded in `research/v86/HOLDOUT.md` *before* Day 1. Any tuning after
  the holdout invalidates it.
- **Pairing.** Same schedule, opponents and seeds; one flag differs. Tools: `research/v81/paired_strict.py`
  (provenance, faults, opponent hashes) and `tools/v67/c_paired.py` (map-cluster CIs).
- **Controls.** All flags 0 must equal v76's Wasm hash.
- **Report everything,** including failures and zeros, in `research/v86/RESULTS.md`.

## 3. Comparisons required

1. Frozen v76 (control).
2. v76 with selected components off: the existing ablations, plus V-C0 (`APEX_TS_DECIDE=0`, never ablated).
3. Deterministic subsystem replacements, one at a time:
   - TEP (vs v76 with campnet)
   - EE stage 2 and stage 3
   - gear planner
   - BANK rule
   - optional draft optimiser (vs ML draft, on non-table and held-out maps)
4. The complete OCC candidate vs v76 and vs v76s.
5. Simplified and search-assisted alternatives:
   - simplified: OCC-min (TEP2 + EE2)
   - search-assisted: no runtime search is planned (rejected on fuel evidence). Offline only, compare EE's stance
     choice with a slow exhaustive 4-round simulation on recorded scenes (an agreement rate). This tests whether the
     analytic approximation loses decisions that search would win.

## 4. Gates

| Gate | Test | Pass | Fail action |
|---|---|---|---|
| G0 | Byte identity | Wasm SHA equal to v76 | Fix the build |
| G1 | Offline model gates | V-M1, V-M2 thresholds | Fix the model; do not proceed |
| G2 | Fuel | p99 ≤ 88k, fuel-outs ≤ 0.6/game, 0 faults (idle + 2 contested opponents) | Budget fix |
| G3 | Idle mechanism (140 paired) | Module-specific (below) | Stop the module (no constant-tuning rescue) |
| G4 | Scenario suite | Puppet cases pass; no illegal actions; ≤2 stance flips per 4 rounds | Fix or stop |
| G5 | Contested league (5 lineage + 3 style opponents) × 140 games, seeds 101+ then 111+ | **Promote:** pooled Δmargin ≥ +50, lower 95% bound > −30, deaths not up, no opponent < −150. **Non-inferior:** Δ ≥ −30 | Reject (Δ < −75) or keep as non-inferior if it unblocks |
| G6 | Held-out maps | Δ on held-out ≥ 50% of the training-map Δ, and ≥ 0 | Revert to untuned scalars |
| G7 | Release holdout (once) | Candidate − v76s ≥ 0 with lower bound > −40 | Ship v76s |
| G8 | Ladder duel (approval only) | Candidate − same-day baseline arm ≥ +110 gems or +8 pp | Do not submit |

## 5. Component experiments and keep / revise / reject rules

| ID | Component | Metric(s) | Keep | Revise | Reject |
|---|---|---|---|---|---|
| V-A1 | M1 recall fix | Puppet case; league | Case passes, league Δ ≥ −30 | — | Case fails |
| V-C0 | APEX_TS_DECIDE=0 (measurement) | League Δ | Informs the EE stage-2 bar | — | — |
| V-M1 | ObjModel | Clear median \|err\| ≤ 20%, bias ≤ 10%; arrival ≤ 3 rounds; damage bias ≤ 20% | Pass | κ per type re-fit (once) | Fail twice: TEP uses the v76 value/cost instead |
| V-E1 | TEP shadow | Fuel G2; agreement rate; hand review of 5 maps | Pass | — | — |
| V-E2 | TEP farming | Idle R250 gems ≥ −2%, R500 ≥ 0, reach-1000 ≤ +10 rounds, R100 gold ≥ −3%; league retention (contested/idle collected) +5 pp; G5 | All | One diagnosed fix | Fails idle again |
| V-E3 | Opening | Idle R100 gold +10%, first elk capture ≤ R55, R250 non-inferior | All | — | R250 worse |
| V-E4 | Gear planner | Idle R250/R500 income ≥ fixed build; R250 equipment +10% | All | — | Income worse |
| V-E5 | BANK rule | Idle conversion ≥ v76 with income ≥ −2%; league bag loss down | All | η re-fit | Income worse |
| V-M2 | EE calibration | 4-round death Brier < v76 `in_danger` Brier; HP-loss MAE ≤ 25% | Pass | Re-fit scalars once | Fail: no EE stage ≥ 2 |
| V-C1 | EE stage 2 | G4; G2; G5 vs v76 and the V-C0 variant; deaths −0.5/game | Pass | — | Δ < −75 |
| V-C2 | EE stage 3 | As V-C1, plus step-away-without-hit share −5 pp (`tools/v67/c_engage.py`) | Pass | — | Worse than stage 2 |
| V-C3 | Crew stance | Split-engagement share down; deaths not up; G5 | Pass | — | Worse than EE3 |
| V-S9 | Unseen-map knob generalisation (offline LOMO) | Held-out gain CI > 0 | Use the kNN profile on unseen maps | — | Defaults only |
| V-D1 | Draft optimiser (optional) | Offline LOMO > ML net; then a fresh league on 40 non-table + 14 held-out maps | Pass both | — | Keep the ML draft |
| V-T1 | Scalar re-tune | G5 on seeds 111–120; G6 | Pass | — | Untuned defaults |
| V-L1 | Ladder duel | G8 | Promote | — | Ship the fallback |

## 6. Economy conversion and combat metrics (reported for every contested run)

- **Economy:** collected, banked, lost and carried gems at R100/250/500; conversion; equipment cost; first ≥20-gem
  receipt round; first purchase round; cluster captures.
- **Combat and survival:** deaths, dead champion-rounds, repeated-death rate, step-away-without-hit share,
  reversals, kill gold.
- **Fuel:** mean, p90, p99, fuel-outs; tier distribution (trace builds only).
