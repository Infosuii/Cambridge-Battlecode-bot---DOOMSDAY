# Validation plan: experiments needed to establish competitive strength

**None of these experiments have been run.** All of them are for the implementation phase, after user approval.
E-numbers refer to FINAL_DEEP_ANALYSIS.md.

## 1. Evaluation methodology audit

| Instrument | Strength | Limitation | Use it for |
|---|---|---|---|
| **Idle bench** (`bots/idle81`, 70 maps × 2 sides) | Paired SD 20–180, ~10× sharper than contested (E7). 140 games ≈1 minute | Measures uncontested mechanics only; our gap is contested (E10) | Mechanism gates: income, timing, fuel, regressions |
| **Contested league**: v65, v61, v58, proxy (`--per-team`), and v76 itself | Several styles, cheap (140 games ≈1 min), map-cluster CIs via `paired_strict.py` | All are our lineage (E20). Fight changes do not predict the ladder (E16). SD 620–830; winner flips in about half the games on small changes | Non-inferiority, economy and death metrics, catching regressions |
| **Proxy** | Top teams' drafts, items and perma-recall | v65 controller; predicts the ladder no better than self-play (E20) | One league member, not a judge |
| **Puppet takeover** (deep-analysis tools, E18) | Exact ladder states from real losses; byte-exact prefix | Enemies are scripted, so ≤10-round horizon. Only 12 cases reproduced. Examined set only | Scenario tests of decisions at specific moments |
| **Offline replay models** | No games needed; the full examined ladder set and local replays | Observational; confounded | Model calibration gates (ObjModel, EE) |
| **Ladder duel** (top-12, 120 games) | The actual target population; ±54 gem resolution (E16) | **Activates arms**: requires the user's explicit approval each time; quota | Final promotion decision only |

**Known pitfalls to avoid** (all have happened):
- reused seeds (v67 portfolio 220 → 137)
- duplicate schedule games
- in-sample per-map claims
- loss-conditioned correlations promoted to causes
- lifetime gold mistaken for income
- logging builds altering behaviour
- an invalid opponent with fuel-outs (mimic, public bots)

## 2. Ground rules

- **Seeds.** Seeds 1–22, 24, 41, 42 and 71 are used; 3 and 4 are reserved. The new program uses **101–124**:
  - 101–110 for development and selection
  - 111–120 for validation
  - 121–124 for final confirmation only

  Record every use in `research/<new-version>/SEED_LEDGER.md`.
- **Held-out maps for new-module tuning.** Every 5th map of the sorted 70-map pool (14 maps). New scalars (EE, TEP,
  λ) are tuned on the other 56 and judged on these 14. Per-map tables (V70 / V71) stay as they are and are not
  re-tuned on held-out maps.
- **Hands-off ladder set (165 games).** Untouched. The deep-analysis protocol governs any final frequency
  confirmation. This plan never uses it for development.
- **Paired comparison.** Same schedule, same opponents, same seeds; the candidate differs from its control in one
  flag. Use `research/v81/paired_strict.py` (provenance, both-team faults, opponent hashes) and `tools/v67/c_paired.py`
  map-cluster CIs.
- **Controls.** Every candidate's all-flags-zero build must match v76's Wasm hash (G0).

## 3. Gates

| Gate | What | Pass | Fail action |
|---|---|---|---|
| G0 | Byte identity: v86 with all OCC flags 0 | Wasm SHA-256 == v76 | Fix the build; nothing else runs |
| G1 | Offline model gates: ObjModel (V-M1), EE calibration (V-M2) | thresholds in V-M1 / V-M2 | Fix the model before writing decisions on it |
| G2 | Fuel: idle plus one contested opponent | p99 ≤ 88k, fuel-outs ≤ 0.6/game, no new bot faults | Budget fix; never benchmark strength on a failing build |
| G3 | Idle mechanism (140 paired vs the v76 control) | module-specific (V-E2, V-E3, V-E4) | Stop the module (the v82 rule) |
| G4 | Scenario suite (puppets plus synthetic) | V-C1 / V-C2 assertions | Fix or stop |
| G5 | Contested league: 5 opponents × 140 games, seeds 101+, then 111+ | **Promote:** pooled Δmargin ≥ +50 with lower 95% bound > −30, deaths not up. **Non-inferior:** Δ ≥ −30. **Reject:** Δ < −75 or any opponent < −150 | Reject, or keep as non-inferior if it unblocks a later module |
| G6 | Held-out maps (14 maps × 2 sides × 5 opponents) | Δ on held-out ≥ 50% of the training-map Δ, and ≥ 0 | Over-tuned: revert to untuned scalars |
| G7 | Ladder duel (user approval required) | candidate − same-day v76/v74 arm ≥ +110 gems (2 SE), or win rate +8 pp | Do not submit; keep the fallback |

Noise: pooled over 5 opponents (700 games) the SE is about 27 gems, so the +50 / −30 thresholds are ~2 SE apart.
Per opponent (140) the SE is 55–70.

## 4. Experiments (in dependency order)

### Track A: fallback and quick wins

- **V-A1: S7 recall guard (`OCC_FIX_RECALL`).**
  - Run the frozen deep-analysis diagnostic (`TAKEOVER_PLAN.json`, C004 R1669–1672) under its own decision rule.
    Pass = zero cancel+recall restart pairs while banking is disabled.
  - Then the G5 league for non-inferiority. A rare event, so expect no measurable gain.
- **V-C0: APEX_TS_DECIDE=0 ablation on v76.**
  - Idle sanity check plus 2 opponents.
  - Purpose: measure what the active search verdict contributes, i.e. the bar EE stage 2 must meet.
  - No promotion intended.
- **V-S9: unseen-map knob generalisation (offline, no games).**
  - LOMO on existing v71 knob-league runs, as in `scripts/lomo_draft.py`.
  - Pass = held-out mean gain 95% CI > 0.
- **V-S5 / V-S12 analyses (offline).**
  - Fraction of repeated deaths within 25 rounds of respawn while alone.
  - Fraction of deaths whose killer was first seen 2 or fewer rounds earlier.
  - Both decide whether S5's respawn rule and S12 target real deaths: proceed if >25%.

### Track B: OCC core

- **V-M1: ObjModel replay validation (G1).**
  - Extract per-capture travel, clear and damage from SA-IDLE-v76 replays (already on disk;
    `tools/replay/camp_clear.mjs`, `capture_funnel.mjs`).
  - Pass:
    - clear time median |error| ≤ 20%, bias ≤ 10%
    - arrival |error| ≤ 3 rounds for d ≤ 30
    - damage-taken bias ≤ 20%
    - capture 5–6 rounds in ≥ 90% of cases
- **V-E1: TEP shadow (OCC_TEP=1).**
  - Idle plus proxy.
  - Fuel gate G2.
  - Log TEP's choice vs v76's actual choice, and the agreement rate by phase. Disagreements are inspected by hand on
    5 maps.
- **V-E2: TEP owns farming (OCC_TEP=2) vs the v76 control *with campnet*.**
  - Idle gate G3:
    - R250 collected gems ≥ −2%
    - R500 collected gems ≥ 0
    - reach-1000 median ≤ +10 rounds
    - R100 gold ≥ −3%
  - Then G5 league and G6 held-out maps.
  - Additional contested metric: R500 retention = contested collected ÷ idle collected, same map and side. Target
    +5 pp.
  - **This is the decisive TEP-vs-campnet comparison** (NEURAL_VS_ALGORITHMIC §2.1).
- **V-M2: EE calibration (G1).** On recorded contact turns (local replays plus the examined ladder set), the offline
  Python EE must beat v76's `in_danger` flag on 4-round death Brier score, with HP-loss MAE ≤ 25% of the mean. Fit
  ≤8 scalars on the training maps only.
- **V-C1: EE stage 2 (verdict only).**
  - Scenario suite G4:
    - on the 12 reproduced games, all decision windows yield legal actions
    - no stance flip-flop more than 2 times in 4 rounds
    - recorded windows labelled "dive" by the deep-analysis cards must not choose FIGHT under the pessimistic
      variant
  - Then G2 and G5 against the V-C0 baseline and v76.
  - Success metric beyond margin: deaths/game −0.5 and split-engagement share down.
- **V-C2: EE stage 3** (stances, HOLD/AMBUSH, free-action rule): as V-C1, plus the step-away-without-hit share
  (`tools/v67/c_engage.py`) down by ≥ 5 pp locally.
- **V-C3: crew protocol (OCC_EE=4, OCC_CREW=1).** Beacon encode/decode unit test. League G5. Split-engagement share
  and dive deaths down. The no-crew build (EE=3) is the control.
- **V-E3: opening schedule (OCC_OPEN=1)**, only after V-E2 passes. Idle: R100 gold +10%, first elk-size capture
  ≤ R55, R250 non-inferior.
- **V-E4: shop tempo (OCC_TEP=3)**, only after V-E2 passes. Idle: R250 equipment +10%, R250 gems non-inferior.
- **V-T1: re-tune the OCC scalars with the v70/v71 league protocol** on the 56 training maps (seeds 101–110), then
  validate on seeds 111–120 and the held-out maps (G6).
- **V-D1: algorithmic draft (optional).**
  1. Offline LOMO on the v70 league with B.2 features from map files.
  2. If held-out gain > the ML-net-equivalent, run a fresh league of draft-C vs ML-draft on the 40 non-table maps
     plus the 14 held-out maps (seeds 111+).
- **V-L1: ladder duel (G7).**
  - Only with explicit user approval, because it submits and activates arms.
  - The arms are the final OCC candidate and a same-day baseline (v76s or the live version).
  - The CLI activation behaviour is documented in `research/v81/RESEARCH.md` (`ladder_duel.py run` activates).

## 5. Fair comparison of the new architecture with v76

- **Primary:** contested league (5 opponents) plus held-out maps, using paired fresh seeds. Report margin, win rate,
  deaths, R500 retention and R250 equipment.
- **Mechanism:** idle bench on the same maps and sides.
- **External validity:** puppet scenarios from real ladder losses, plus the ladder duel if approved.
- **Report every result**, including failures and zeros, in `research/<version>/RESULTS.md` with run prefixes. Never
  delete a run directory except an incomplete one belonging to the current experiment.
