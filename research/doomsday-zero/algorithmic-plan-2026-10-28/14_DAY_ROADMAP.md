# 14-day roadmap to finals (2026-10-29 → 2026-11-11)

Assumptions:
- Finals are about 14 days away. Day 14 is 2026-11-11; adjust if the date differs.
- One implementation agent, plus parallel sessions where modules are independent.
- Local games are cheap (140 in about 1 minute).
- Every submission or activation (ladder duels included) needs the user's explicit approval.

Gate IDs (G0–G7) and experiment IDs (V-*) refer to VALIDATION_PLAN.md.

## Dependency graph

```
 G0 scaffold (v86 = v76 copy + flags, byte identity)
   ├─► A-track: S7 recall fix (V-A1) ──► v76s fallback candidate (ready Day 2)
   ├─► offline analyses (V-S9, V-S5/S12, V-C0 ablation)            [parallel, no code dependency]
   ├─► M8 governor ─┐
   ├─► M1 ledger ───┼─► M2 ObjModel ─(V-M1 gate)─► M3 TEP shadow ─► TEP owns farming (V-E2) ─► SHOP/BANK (V-E4) ─► opening (V-E3)
   │                │                                                     │
   │                └─► EE offline port ─(V-M2 gate)─► EE shadow ─► EE stage 2 (V-C1) ─► stage 3 (V-C2) ─► crew (V-C3)
   │                                                                     ▲ needs V_obj from TEP (stub = v76 group value until TEP lands)
   └─► V-T1 league re-tune of OCC scalars (after the last module change) ─► G6 held-out ─► G7 ladder duel (approval)
```

Independent work that can run in parallel sessions (separate files, separate worktrees):
1. the EE offline Python port and calibration (V-M2)
2. ObjModel replay extraction and validation (V-M1)
3. A-track S7 fix plus the offline analyses

TEP and EE runtime code touch different hooks (`score_groups` vs `handle_enemies`). They can be developed in parallel
in separate files, but are merged and benchmarked in sequence.

## Day-by-day

| Day | Date | Build | Experiments / gates | Exit criterion |
|---|---|---|---|---|
| 1 | 10-29 | v86 scaffold: copy v76, add `occ_*` files as empty modules, all flags 0. `OCC_FIX_RECALL`. Seed ledger. Held-out map list. Trace build plumbing | G0 byte identity; V-A1 puppet diagnostic; start V-S9, V-S5/S12 offline; V-C0 ablation run | G0 passes; S7 diagnostic result recorded |
| 2 | 10-30 | M8 governor; M1 ledger in shadow (`OCC_LEDGER=1`); log v76's effective λ_gold per map | V-A1 league non-inferiority → **v76s fallback ready**; V-M1 data extraction; EE Python port begins | v76s packaged (not submitted); ledger fuel ≤2k p99 |
| 3 | 10-31 | M2 ObjModel (C++ and Python mirror) | **V-M1 gate**; EE calibration dataset built | ObjModel within thresholds, or model fixed |
| 4 | 11-01 | M3 TEP shadow (`OCC_TEP=1`) | V-E1 fuel and disagreement logs; **V-M2 EE calibration gate** | TEP shadow p99 ≤ 88k; EE beats `in_danger` on Brier |
| 5 | 11-02 | TEP owns farming (`OCC_TEP=2`): single capturer, progress contract | **V-E2 idle gate (G3)**, then league (G5) | TEP non-inferior idle, or diagnosed |
| 6 | 11-03 | EE shadow, then stage 2 (verdict only) | V-C1 scenarios (G4) and league (G5); fuel G2 | EE stage 2 non-inferior with deaths not up |
| 7 | 11-04 | Integration TEP2 + EE2; BANK hazard rule (`OCC_TEP=3` BANK part) | Combined league; retention metric | **Decision point D7** (below) |
| 8 | 11-05 | **Last major architecture change.** EE stage 3 (stances, free actions) and the crew protocol (if D7 = continue) | V-C2, V-C3 scenarios and league | Stage 3 / crew non-inferior, or reverted to stage 2 |
| 9 | 11-06 | SHOP tempo (V-E4) and opening (V-E3), *only if* ahead of schedule | Idle gates | Pass, or drop the optional items |
| 10 | 11-07 | V-T1 scalar re-tune on the 56 training maps (seeds 101–110) | League selection; G6 on held-out maps (seeds 111–120) | Tuned scalars pass G6, or untuned kept |
| 11 | 11-08 | Bug-fix only. Candidate packaging and release record draft | **Ask the user to approve a ladder duel (V-L1)**: OCC candidate vs same-day baseline | Duel run if approved |
| 12 | 11-09 | **Freeze the final candidate** (OCC or v76s). After this, only fixes for crashes, faults or fuel | Confirmation on seeds 121–124 (G5) | Frozen candidate and fallback both validated |
| 13 | 11-10 | Release dossier: hashes, flags, results, risks | Final ladder-duel readout if run | Recommendation to the user |
| 14 | 11-11 | — | **User decides on submission.** No agent submission | — |

## Decision point D7 (2026-11-04)

| State at D7 | Decision |
|---|---|
| TEP passes G3 and G5, **and** EE stage 2 passes G4 and G5 | Continue B: EE stage 3 + crew on Day 8 |
| Exactly one of TEP / EE passes | Keep the passing module, drop the other. Spend Day 8–9 on the passing module's stage and on A+ items (S9 knob rows, S7) |
| Neither passes | **Abandon B for finals.** Ship A+ (v76s + S7 + S9 if positive + league re-selection if any). Write the OCC post-mortem |
| Any fuel or fault regression unresolved | Fix it first; otherwise as "neither passes" |

**Investment triggers** (go further):
- TEP improves R500 retention ≥ +5 pp with league Δ ≥ +50.
- EE stage 2 cuts deaths ≥ 0.5/game with league Δ ≥ 0.
- Puppet scenarios show the stance logic fixing a recorded failure class.

**Abandonment triggers** (stop a module):
- It fails its offline model gate twice.
- It fails the idle mechanism gate after one diagnosed fix (the v82 rule).
- League Δ < −75.
- Fuel p99 > 95k that cannot be fixed within a day.

## Minimum correctness requirements, before any strength test

1. G0 byte identity at all flags 0.
2. Zero bot faults and no new exceptions in 280 games (idle + 1 contested).
3. Fuel gate G2.
4. Shared-word encode/decode round trip passes, and v76 claim codes are unchanged.
5. Each module's fallback path is exercised once: a forced-tier test build or a host test.
6. No logging in release builds. Trace builds are never used for strength or fuel-out claims.

## Parity with proven behaviour

- TEP stage 2 starts from v76's value weights (λ_gold = v76 effective per map) and keeps v76's capture, staging and
  avoid logic as executors. The only intended differences are crews, timing, contest and follow-up.
- EE stage 2 changes only the verdict. Executors, early-return owners and every knob stay the same.
- Stage 3 changes are separate flags, so any regression is attributable.

## Essential vs optional

| Essential (needed for an OCC candidate) | Optional (only if ahead of schedule) |
|---|---|
| G0 scaffold, governor, ledger | Opening schedule (S3) |
| ObjModel and its validation | Shop tempo (S6) |
| TEP stage 2 | Algorithmic draft (S8) |
| EE stage 2 (stage 3 if it passes by Day 8) | Crew protocol (S4), if EE stage 3 is late |
| S7 recall fix (in both tracks) | Ward control (S12), opponent modes (S10), micro planner (S11): post-finals |
| v76s fallback package | S9 unseen-map knobs (offline analysis is essential; adoption is optional) |
| V-T1 re-tune and held-out validation | |

## Keeping a reliable fallback

- **v76s** (v76 + S7 fix) is built and validated on Day 2 and kept frozen. Every OCC candidate is compared against
  it.
- The **live platform version is not changed by this roadmap.** Only the user activates or submits.
- Every OCC module is revertible by its flag. The Day-12 freeze picks the best validated flag set, or v76s.
- Frozen bots (`bots/v76` and earlier) and historical experiment records are never edited. All new work lives in
  `bots/v86` and `research/v86/`.
