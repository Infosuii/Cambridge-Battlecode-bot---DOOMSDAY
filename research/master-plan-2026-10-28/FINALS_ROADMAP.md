# Finals roadmap: 14 days (Day 1 = 2026-10-29, Day 14 = 2026-11-11)

Assumptions:
- Finals are about 14 days away; adjust the dates if not.
- One implementation agent, with parallel sessions for the independent offline tasks (T2–T4, T17).
- Every submission, activation and ladder duel needs the user's explicit approval.

Task IDs refer to IMPLEMENTATION_PLAN.md; gates to VALIDATION_PLAN.md.

## Milestones

| # | Days | Subsystem | Functionality | Depends on | Effort | Correctness tests | Performance tests | Acceptance | Risk | Fallback |
|---|---|---|---|---|---|---|---|---|---|---|
| MS0 | 1 | Scaffold, fixes, holdout record | v86 copy, flags, M1 fix, robust targeting; `HOLDOUT.md` and `SEED_LEDGER.md` written | — | 1 d | G0; M1 puppet case (baseline fails, candidate passes) | — | G0 passes; M1 case passes | Low | — |
| MS1 | 1–3 (parallel) | Offline models | ObjModel and EE Python ports; extraction; V-M1, V-M2; λ_gold regression; V-S9; death analyses | data on disk | 3 d (parallel) | Port unit tests | — | V-M1 and V-M2 pass, or models fixed | Medium | If EE fails V-M2, no EE stage ≥ 2 (combat stays v76) |
| MS2 | 2 | Fallback v76s | M1 fix + robust targeting; league non-inferiority | MS0 | 0.5 d | Faults 0 | G2 | G5 non-inferior | Low | Frozen v76 |
| MS3 | 2–3 | Governor, ledger, protocol | M8, M1, M5 codec, race (shadow) | MS0 | 1.5 d | Host tests; codec round-trip | G2 with shadow on | p99 ≤ 88k | Medium | Flags off |
| MS4 | 4 | TEP shadow | Assignments logged | MS1 (ObjModel), MS3 | 1 d | Assignment sanity on 5 maps | G2 | Fuel ok; disagreement review done | Medium | Flag off |
| MS5 | 5 | TEP farming | OCC_TEP=2 with CLUSTER_RUN and single capturer | MS4 | 1 d | Idle mechanism G3 | G2 | V-E2 idle pass, then G5 non-inferior | **High** | Keep v76 farming |
| MS6 | 4–6 | EE stage 1–2 | Shadow, then verdict mapping | MS1 (EE), MS3 | 1.5 d | G4 puppet/scenario suite | G2 | V-C1 | **High** | Keep the v76 verdict |
| MS7 | 6 | Style opponents | T17 (evaluation only) | MS0 | 1 d (parallel) | They play legal games, 0 faults | — | Available for G5 | Low | Lineage league only |
| **D7** | **7 (11-04)** | **Decision point** | see below | MS5, MS6 | — | — | — | — | — | — |
| MS8 | 7–8 | BANK, race, gear | OCC_TEP=3, M10, OCC_GEAR | MS5 | 2 d | Idle V-E4, V-E5 | G2 | Gates pass | Medium | Flags off individually |
| MS9 | 8 (11-05) | EE stage 3 + crew | **Last major architecture change** | MS6 | 1.5 d | G4 | G2 | V-C2/V-C3 | High | Stay at EE stage 2 |
| MS10 | 9 | Optional | Opening schedule; draft optimiser (only if Q1 says unseen maps) | MS5 | 1 d | V-E3 / V-D1 | — | Gates | Medium | Drop |
| MS11 | 10 | Tuning (D process) | V-T1 scalars; lineup re-selection on the final controller | final flag set | 1.5 d | — | — | G5 on seeds 111–120; G6 | Medium | Untuned defaults |
| MS12 | 11 | Ladder evidence | **Request approval** for a ladder duel: OCC candidate vs same-day baseline | MS11 | — | — | — | G8 | — | — |
| MS13 | 12 (11-09) | **Freeze** | Release holdout G7, run once; release record | MS11/12 | 1 d | Faults 0 | G2 | G7 | — | v76s |
| MS14 | 13–14 | Release dossier | Hashes, flags, results, risks; user decides submission | MS13 | 1 d | — | — | — | — | — |

## Decision point D7 (2026-11-04)

| State | Action |
|---|---|
| TEP (V-E2) **and** EE stage 2 (V-C1) pass | Continue the full B plan (MS8–MS9) |
| Only TEP passes | Keep TEP; combat stays v76 (plus the M1 fix). Spend Day 8–9 on BANK, gear and race (economy track, locally measurable) |
| Only EE passes | Keep EE stage 2/3; farming stays v76 + campnet. Add gear and BANK only if their idle gates pass on v76 farming |
| Neither passes | **Abandon B for finals.** Ship F + D (v76s + league re-selection + S9 if positive). Write the OCC post-mortem |
| Unresolved fuel or fault regression | Treat as "neither passes" |

## Investment and abandonment triggers

- **Invest more:** TEP retention +5 pp with league Δ ≥ +50; EE deaths −0.5/game with Δ ≥ 0; puppet cases fixed.
- **Abandon a module:**
  - it fails its offline gate twice
  - it fails the idle gate after one diagnosed fix
  - league Δ < −75
  - unfixable fuel p99 > 95k

## Dates

| Date | Milestone |
|---|---|
| 2026-11-05 (Day 8) | Latest major architecture change |
| 2026-11-08 (Day 11) | Ladder duel request (user decision) |
| 2026-11-09 (Day 12) | Freeze the candidate; release holdout once |
| 2026-11-11 (Day 14) | Submission is the user's decision only |

## Reserved time

- Days 10–13 are reserved for tuning, competitive testing and hardening.
- No new modules after Day 8.
- Days 1–6 carry about 30% slack for the expected first-attempt failures.
