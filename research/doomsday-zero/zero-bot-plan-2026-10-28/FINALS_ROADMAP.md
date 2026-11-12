# Finals roadmap: DOOMSDAY Zero (Day 1 = 2026-10-29, Day 14 = 2026-11-11)

**Honest framing.** A clean-slate bot starts below the existing bot in every executor detail. v76 is the result of 76
iterations. The schedule therefore has **parity gates** before any superiority claim, and two decision points.

My judgement, not a measurement: the probability that DZ is *stronger than v76 against the top teams* by Day 12 is
roughly 30–45%, highest if the conformance and calibration work lands by Day 4. The user should weigh this against
the fallback (the current live bot).

## Gates

Gate details are in VALIDATION_PLAN.md.
- **G-P1, idle parity (Day 6).** DZ's uncontested income R250/R500 is ≥ 100% of v76's on the 140-game idle bench, with
  0 faults and fuel-outs ≤ 0.3.
- **G-P2, contested parity (Day 9).** DZ vs the league (v65, v61, v58, proxy, v76, plus 3 style opponents): pooled
  margin vs v76's *own* results against the same league ≥ −30.
- **G-S, superiority (Day 11).** League Δ ≥ +50 with lower bound > −30 vs v76; puppet scenarios improved; then a
  ladder duel request.

## Day by day

| Day | Date | Work (parallel tracks in brackets) | Gate / exit |
|---|---|---|---|
| 1 | 10-29 | Z0 conformance diagnostics; Z1 kernel; build pipeline; `HOLDOUT.md`, `SEED_LEDGER.md` written [offline: λ_gold regression, ObjModel replay extraction] | CONFORMANCE.md v1; kernel runs games with 0 faults |
| 2 | 10-30 | Z2 StaticWorld/Observation; Z3 SafeMode; Z4 draft prior [Z6 ObjModel validation; EE dataset build] | **Walking skeleton** plays full games; fuel gate |
| 3 | 10-31 | Z5 memory and protocol; Z7 auction v1 (solo plus crews) [V-M1 done; V-M2 started; Z13 style opponents] | Codec tests; auction runs |
| 4 | 11-01 | Z7 clusters, contracts, bank rule; Z9 gear v1 | V-E1 idle ≥ 0.9× v76 at R250 |
| 5 | 11-02 | Z8 action scorer (travel, clear, capture, bank, shop, ward, spells) [V-M2 done] | Scenario checks |
| 6 | 11-03 | Z10 EE live; integration | **G-P1 idle parity** |
| 7 | 11-04 | Contested league v1; fixes | **Decision D7** (below) |
| 8 | 11-05 | Z11 crew and race; Z12 opening (if on schedule). **Last architecture change** | Module gates |
| 9 | 11-06 | Full league plus held-out maps; fixes | **G-P2 contested parity** |
| 10 | 11-07 | Z14 tuning: scalars and per-map draft rows (seeds 101–110), validation (111–120) | G5/G6 |
| 11 | 11-08 | Puppet and scenario regressions; **request ladder duel approval** (DZ vs live) | G-S; G8 if approved |
| 12 | 11-09 | **Freeze.** Release holdout run once (seeds 121–124). Conformance re-run on the current CLI | G7 |
| 13 | 11-10 | Release dossier: hashes, flags, results, risks | — |
| 14 | 11-11 | **User decides** DZ vs the live bot. No agent submission | — |

## Decision points

**D7 (11-04).**

| State | Action |
|---|---|
| Idle parity met, and contested league ≥ −150 vs v76's league result | Continue |
| Idle parity met, but contested < −150 | Continue only on combat (EE, crew); economy frozen. Re-check on Day 9 |
| Idle parity not met | Stop new features. Days 8–9 on economy and execution bugs. If G-P2 still fails on Day 9: finals with the live bot; DZ continues as post-finals work |

**D9 (11-06).** If G-P2 fails, the finals use the live bot.

**Engine-update contingency.** If a new cambc version ships at any point:
1. Re-run the conformance suite (half a day).
2. Re-run the idle bench.
3. Re-run the league subset.

DZ needs no code change for value changes (all runtime-read). Rule changes are handled as defects.

## Essential vs optional

| Essential | Optional |
|---|---|
| Kernel, SafeMode, StaticWorld, Observation | Opening planner |
| Memory, protocol | Style adaptation |
| ObjModel (validated), economy auction, bank rule | Ward planner refinements |
| Action scorer with spell policy | Respawn denial |
| EE (calibrated) | Teleport-crystal use |
| Gear planner v1 | Draft LOMO weights (use the prior plus per-map rows instead) |
| League tuning; holdout; conformance re-run on updates | — |
