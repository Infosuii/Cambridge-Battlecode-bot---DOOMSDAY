# Validation plan (DOOMSDAY Zero)

**Nothing here has been run.** It is all for the implementation phase.

## 1. Instruments

| Instrument | Use | Limit |
|---|---|---|
| Conformance diagnostics | Engine truth (ENGINE_CONFORMANCE_SUITE.md) | Local engine only (verified equal to the platform) |
| Host unit tests | Pure cores | No engine |
| Idle bench (`bots/idle81`, 70 maps × 2 sides) | Mechanism and parity; paired SD 20–180 | Uncontested |
| League: v65, v61, v58, proxy (`--per-team`), v76, plus 3 DZ style opponents | Contested strength; SE ≈ 27 over about 1,000 games | Mostly our lineage; style opponents add diversity |
| Offline replay models | ObjModel and EE calibration | Observational |
| Puppet warm cases | Exact ladder states (requires a takeover build) | ≤10 rounds; optional |
| Ladder duel (top 12, 120 games) | Final judge | **Activates arms: user approval each time** |

**The deep-analysis 165-game reserved set is spent** and must not be used as a holdout.

## 2. Ground rules

- **Seeds:** 101–110 for development and selection; 111–120 for validation; **121–124 once-only release holdout**.
  Seeds 3 and 4 are reserved and never used. Every use is ledgered in `research/dz/SEED_LEDGER.md`.
- **Held-out maps** for tuning: every 5th map of the sorted 70-map pool (14 maps).
- **Release holdout.** DZ-final and v76 on seeds 121–124 × 70 maps × 2 sides × the league, run once. The plan is
  recorded in `research/dz/HOLDOUT.md` before Day 1 experiments.
- **Pairing.** Same schedule, opponents and seeds. Use `paired_strict.py` and `c_paired.py` (map-clustered CIs).
- **Report everything** in `research/dz/RESULTS.md`, including failures.

## 3. Gates

| Gate | Test | Pass |
|---|---|---|
| G0 | Build and conformance | Builds with the official CLI; CONFORMANCE.md complete; fingerprint recorded |
| G1 | Offline models | V-M1 (ObjModel), V-M2 (EE) thresholds |
| G2 | Fuel and faults | p99 ≤ 85k, fuel-outs ≤ 0.3/game, 0 faults (idle + 2 contested opponents) |
| G-P1 | Idle parity | DZ R250 and R500 collected gems and gold ≥ v76 (paired, 140 games); reach-1000 median ≤ v76's |
| G-P2 | Contested parity | DZ's pooled league margin ≥ v76's pooled league margin − 30 (same schedule) |
| G5 | Promotion | League Δ ≥ +50, lower 95% bound > −30, no opponent < −150, deaths not up |
| G6 | Held-out maps | Δ on held-out maps ≥ 0 and ≥ 50% of the training-map Δ |
| G7 | Release holdout (once) | DZ − v76 ≥ 0 with lower bound > −40 |
| G8 | Ladder duel (approval) | DZ − same-day live arm ≥ +110 gems or +8 pp |

## 4. Component experiments (keep / revise / reject)

| ID | Component | Metric | Keep | Reject |
|---|---|---|---|---|
| V-M1 | ObjModel | Clear time median \|err\| ≤ 20%, bias ≤ 10%; arrival ≤ 3 rounds; damage bias ≤ 20% | pass | Fails twice: economy uses a simpler distance/value rule |
| V-M2 | EE model | 4-round death Brier below the HP-and-numbers logistic baseline | pass | No EE; SafeMode combat plus action-scorer FIGHT/RETREAT by S ratio |
| V-E1 | Auction vs SafeMode farming (inside DZ) | Idle income R250/R500 | ≥ +10% | worse |
| V-E2 | Clusters | Cluster captures, gems per runner-round | up, with income not down | — |
| V-E3 | Opening planner | R100 gold +10%, R250 non-inferior | pass | R250 worse |
| V-E4 | Gear planner vs fixed build | Idle R250/R500 income; equipment | ≥ | worse |
| V-E5 | Bank rule | Conversion up; income ≥ −2%; bag loss down (league) | pass | income worse |
| V-C1 | EE vs SafeMode combat | League Δ, deaths, step-away share | Δ ≥ 0, deaths down | Δ < −75 |
| V-C3 | Crew stance | Split-engagement share, deaths | down | worse |
| V-T1 | Scalar tuning | G5 on seeds 111–120, G6 | pass | Keep defaults |
| V-T2 | Per-map draft rows on DZ | League gain > 100 per map and no opponent < −250 (v70 rule), confirmed on fresh seeds | pass | Prior lineup |

## 5. Metrics reported for every contested run

- **Economy:** collected, banked, lost and carried gems at R100/250/500; conversion; equipment value; first ≥20-gem
  receipt round; first purchase round; cluster captures.
- **Combat and survival:** deaths, dead champion-rounds, repeated-death rate, step-away-without-hit share, reversals,
  kill gold.
- **Runtime:** fuel mean, p90, p99; fuel-outs; stale-turn aborts; module error counts; SafeMode share of turns.
