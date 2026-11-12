# Executive recommendation

## Decision requested

Approve building **OCC (Objective–Crew–Combat)**:
- a hierarchical algorithmic controller (Architecture B)
- on v76's proven engine-facing infrastructure, in a new `bots/v86`
- with offline league-selected constants (D)
- with a confirmed-bug-fix fallback, "v76s", ready on Day 2

**Nothing has been implemented.** Implementation starts only on your approval.

## Why this architecture

1. **The deficit against top teams is a coupled loop, measured on both sides:**
   - **Opening and gear.** Intercontinental Fish has 483 gold at R100 against our 278, and 2929 equipment at R500
     against our 1440.
   - **Deaths.** Top teams die 2–5 times per game; we die 9–15. In losses we spend twice the champion-rounds dead.
   - **Retention under contest.** We keep 62–66% of our uncontested income; they keep 93–96%.
   - **Conversion.** We bank 56–86% of what we collect; they bank 88–95%.
   - Both economy and fights already diverge by R100 (36% / 34% of our losses).
2. **v76 cannot fix this by tuning.**
   - Its fight decision is five verdict writers over two booleans, objective-blind and per champion.
   - Its economy is per-champion greedy with 7-bit claims, and ignores the item economics it buys: Prospector gives
     +25% cluster gems (inferred from 9,196 capture events), and Capture makes captures 3 rounds.
   - Every earlier layer added on top lost.
3. **OCC replaces the decision layers with one value scale** (gem-equivalents, with time-dependent gold value and
   death cost) and single owners:
   - **TEP:** team objectives, crews, cluster circuits, banking as optimal stopping
   - **EE:** a stance portfolio evaluated by a Lanchester-style analytic model with commitment
   - **Crew protocol:** a typed 22-bit beacon
   - **Race controller**
   - **Gear planner**

   All are bounded by a fuel governor, and all fall back to v76 code per turn.
4. **External evidence supports the specific choices:**
   - Lanchester predictors beat simulation in RTS attack/retreat decisions and run 19–145× faster.
   - Portfolio-of-scripts search is the efficient form of combat search.
   - The best MOBA agent scripted items and abilities.
   - CBBA-style auctions tolerate inconsistent beliefs.
   - Banking is the burglar optimal-stopping problem.
   - Battlecode winners used simple scored micro, not deep search.
5. **The process is built against the recorded failure causes:**
   - model-first gates
   - progress contracts
   - replacement rather than layering
   - byte-identical controls
   - idle gates before contested runs
   - fresh seeds and held-out maps
   - a once-only release holdout

## Strongest alternative

**F + D:** v76 plus the M1 recall fix, robust targeting and league re-selection of tables. It is low-risk and uses
the only mechanism shown to transfer to the ladder (+142 for v74 over v67), but it does not touch the loop above.

It is preferable if:
- by **D7 (2026-11-04)** neither TEP nor EE passes its gates; or
- ladder duels cannot be approved and OCC's gains are combat-only.

## Biggest uncertainties

1. Whether the analytic combat model predicts 4-round outcomes better than v76's verdict. This is an offline test,
   Day 1–3.
2. Whether TEP's travel and clear model is accurate enough. Offline, Day 1–3. This is where v82 failed.
3. Whether local gains transfer to top teams. Combat changes never showed locally; puppets, style opponents and an
   approved ladder duel are the only checks.

## First implementation milestone (Day 1)

1. `bots/v86` scaffold with all flags 0, byte-identical to v76.
2. The M1 recall fix, with the deep analysis's warm puppet regression (baseline fails, candidate passes).
3. `research/v86/HOLDOUT.md` and `SEED_LEDGER.md` written before any experiment.
4. Offline ObjModel and EE calibration data extraction started.

## Risks before finals

| Risk | Likelihood | Mitigation |
|---|---|---|
| Core modules fail their gates (high base rate) | Medium-high | D7 switch; v76s fallback from Day 2 |
| Local gains don't transfer | Medium | Economy metrics; puppets; style opponents; ladder duel request on Day 11 |
| Fuel tail regressions | Medium | Governor tiers; p99 gate on every build |
| Over-tuning to the pool | Medium | 14 held-out maps; fresh seeds; once-only holdout |
| Scope creep | High | Last architecture change Day 8; optional items list |
| Accidental activation | Low | No submission or ladder duel without your written approval |

## Decisions only you can make

| ID | Decision | Why it matters |
|---|---|---|
| **Q1** | Are finals played on the current 70-map pool, or on new maps? | Decides the weight on per-map tables vs generalisation (draft optimiser, S9) |
| **Q2** | Will ladder duels be approved, and when? | They activate arms; they are the only judge of combat changes |
| **Q3** | Which platform version is live now? | Same-day baseline arm. Deep analysis: platform 69 = v75, activation not re-verified |
| **Q4** | Risk appetite at freeze when evidence is ambiguous | OCC vs v76s |

---

## Principal-engineer design review (Phase 10)

| Question | Answer | Where |
|---|---|---|
| Is every major algorithm mechanically valid? | Yes, given engine metadata at runtime. Docs and engine differ (Treasure 10%, Monster 15%, stats), so nothing is hard-coded from GameRules.md. Open engine questions ENG-1..5 have one-game diagnostics | GAME_MECHANICS §3–6, §11 |
| Is the architecture internally coherent? | One value scale (GE) is used by TEP, EE, BANK, gear and race. Every decision has one owner | MASTER §1–2 |
| Are decision priorities unambiguous? | The authority table plus the turn lifecycle order; EE pre-empts TEP only through an explicit stance | MASTER §2–4 |
| Are the inputs observable? | Yes: own vision, the shared word, SDK scores, engine metadata, the full map at draft. Hidden enemies are modelled as phantoms; no omniscience assumed | DATA §2, ALGO §9 |
| Can the protocol support the design? | Yes, within 64 bits: claims unchanged plus a typed beacon with pre-emption and freshness; sufficiency argued | DATA §4.3 |
| Do the algorithms fit the fuel limit? | Typical ≤48k, p99 ≤88k by construction, with governor tiers and hard reserve; to be confirmed by G2 | FUEL §2–4 |
| Is the true victory condition accounted for? | Race controller (time to 1000), ENDGAME_RACE mode, banking as stopping, tiebreak floor on λ_gold | ALGO §1, §4, §8 |
| Are economy and combat integrated? | EE values objective progress; TEP's P_ok uses combat strength; death cost uses economic tempo | ALGO §2–5 |
| Is economic performance under contest addressed? | P_ok, CONTEST/DEFEND modes, HOLD stance, cluster runners away from pressure, retention metric gate | ALGO §3, VALIDATION V-E2 |
| Can the system recover from bad decisions? | Progress contracts, hysteresis with a personal override, REGROUP mode, per-turn fallbacks, module self-disable | MASTER §4, §11 |
| Will it generalise to unseen maps? | Models are rule-derived; per-map tables are optional; S9 kNN only if LOMO > 0. **Not guaranteed**: held-out map gate | VALIDATION G6 |
| Are historical failure modes addressed? | Each has a material mechanism plus a gate that would catch a repeat | SCENARIOS Part C |
| Is it feasible before finals? | The core path (OCC-min) by Day 6 with 30% slack; D7 switch; fallback ready on Day 2 | FINALS_ROADMAP |
| Credible advantage over v76? | Plausible, not proven. It targets measured gaps with mechanisms the evidence ties to them; every claim is gated | this doc |
| Which claims need empirical validation? | ObjModel accuracy; EE calibration; TEP non-inferiority and retention; ladder transfer; the Prospector/Tribute/Capture semantics | VALIDATION §5, GAME_MECHANICS §11 |
| Can the next agent build without inventing design choices? | Module boundaries, data structures, formulas, defaults, gates and hooks are specified. Remaining choices are engineering only | IMPLEMENTATION_PLAN, DATA, ALGO |

**Revisions made during this review:**
1. Added the **gear planner** to the core. Item economics are measurably large (Sprint-3 package +136..+153), and
   Prospector/Capture are bought but unvalued.
2. Added **cluster circuits**, from the capture-bound mechanics.
3. Replaced the spent 165-game holdout with a **once-only seed-and-map release holdout** recorded before Day 1.
4. Added **scripted style opponents**, so the league is not only our lineage.
5. Removed runtime search entirely. The portfolio idea is kept with analytic evaluation.
