# DOOMSDAY Zero: combined plan (Z plan + lab/v76 plan + all research), 2026-10-31

This is the working plan for the next agent. It merges four sources so that no idea is lost:

1. the **Z plan** (`research/zero-bot-plan-2026-10-28/`, 21 documents; steps Z0-Z15 with validation gates);
2. the **lab/v76 plan** run in parallel on branch `lab/box` of this repository (v74h → v75 → v76, branch farm,
   learned plan selection, overall-win-rate screening); read it with `git fetch origin lab/box`;
3. the **research review** of 24 papers (JueWu-SL, HMS, NaiveMCTS, Lanchester/Stanescu combat models, market
   allocation, DAgger/CQL/IQL, VIPER, CMA-ES/Hyperband, AlphaStar league, win prediction, potential fields), plus the
   lab kit, the team's FINDINGS and lab4 branching results;
4. **research/elite-meta-2026-10-29** (30 elite matches: 8 ranked priorities, experiments E1-E5, META_TO_ALGORITHM).

Rules that still bind: DZ contains no previous-bot code. Old bots are opponents, and lab ideas are re-implemented in
DZ's own code. Evaluation tools may be shared. No submission, activation or ladder matches. Preserve
`config/paths.json` and completed experiments. Fresh run names. Every new behaviour goes behind a `DZ_*` flag
(default 0, so the release stays byte-identical) until it passes its gate.

## 1. Where things stand (2026-10-31 15:30)

Selected release **5cf28cb7** (unchanged). Against v76 it banks 226 to 1028 and wins 1 of 140; against idle it
banks 920 and finishes at R1333 (v76: R914). Contested: 1.1 kills vs 15.7 deaths per game, 12k vs 22k champion
damage, 2.0k vs 6.8k gold. Economy: 8.8 vs 13.4 gems per collection; R100 gold 180 vs 329. The gap concentrates on
about ten maps (boss-battle, guardians, the-pack, islands, corridors, concentrated-wealth, harvest, ribs, the-farm).
Full diagnosis: `research/dz/z-integration-2026-10-31/README.md`.

### Z-step status and gates (VALIDATION_PLAN.md)

| Step | Built | Gate | Status / fallback |
|---|---|---|---|
| Z0 conformance | mostly | G0 | CT-1/7/8/9/11/13 partial |
| Z1-Z3, Z5 | done | - | done |
| Z4 draft | prior + 34-map table, variants 0-7 | per-map confirm | table incumbent; variants 1-7 screen half done (§3) |
| Z6 ObjModel | arithmetic, clear_risk; gold weight flags `DZ_OPENING_GOLD`, `DZ_GOLD_VALUE` | V-M1 | V-M1 open; gold flags screening (§3) |
| Z7 economy | heuristic (rate, survivability gate, leader crews, contracts) | V-E1 | auction not built → task A3 |
| Z8 action scorer | partial | G-P1 idle parity | R250 0.89x v76 idle; fails G-P1 |
| Z9 gear | `DZ_GEAR_SURVIVE/PROSPECT/HEALTH` | V-E4 | survive+prospect idle R250 = baseline, R500 +7 → V-E4 pass on idle; v65 confirm -6.9 (SE 9.6), not promoted |
| Z10 threat/EE | `DZ_EE`, `DZ_EE_REGROUP`, **`DZ_EE2` (V-M2 model)** | V-M2, contested league | **V-M2 PASSES** (Brier 0.0379 vs 0.0398, 140 games); threshold EE2 fails the league (−6.7 v76, −21.2 v65, deaths up) → B1 needs the enemy-side model and an expected-value rule |
| Z11 crews | `DZ_CREWS`, `DZ_CREW_ALL` | V-C3 | both fail (deaths not down, banked -25/-37) → fallback: no crew stance; market claims (A3) next |
| Z12 opening | `DZ_OPENING_GOLD` | V-E3 (R100 gold +10%, R250 not worse) | split: R100 gold +24% but R250 gems −12% (idle); screen contested next (A3) |
| Z13 style opponents | `DZ_STYLE`, `tools/dz_styles.py` (rusher, turtle, farmer) | legal games, 0 faults | **passes**: 420 games, 0 faults/fuel-outs; DZ wins 120/140/114 |
| Z14 league tuning | `DZ_PLAN_TABLE` runtime per-map bits + draft; `tools/dz_plan_select.py`; ring gates | G5/G6 | 26/58 screening runs done; resume with `tools/dz_z14_screen.sh` |
| Z15 hardening | 0 faults / 0 fuel-outs on release | G0-G7 | re-run on the final candidate |

## 2. Evidence: what is proven, what is null (do not repeat nulls)

Proven or strongly supported:
- **The engine is deterministic** per (binaries, map, side). Branches from one game are exact counterfactuals until
  the changed decision. Build-seed jitter (`NOVA_SEED`-style) is the only source of variation besides maps.
- **Early leads snowball**: one free kill at R100 raised the lab win rate 53.5% → 71%; +150 gold per champion → 84.5%.
  DZ's gold deficit (R100 180 vs v76 329) is therefore a first-order problem, not a detail.
- **Whole-team plan switches flip losses; single decisions don't compose** (lab4 `winsearch`/`cfexp`: 246 of 262
  losses winnable from an earlier position; the "home" plan flipped the most; fight-vs-run, bank-now and hold-bag
  single-decision branches were null or worse). Individual decisions are near locally optimal; gains need a change
  of *team plan*.
- **Per-map tables pay on known maps, generalists win on unseen maps**: ext (v71, per-map tables) beats v74 on the
  70 ladder maps (36/70), and v74 (home plan) beats ext on 400 random maps (61.1%). The ladder plays exactly the 70
  maps in `maps/local-benchmarks`.
- **lab/v76** (v74h + ext's draft table + map knobs, without ext's siege/island fixes) beat v74h 53.3% over 1,440
  games (lower bound ~51%) and v71 62.2% (57.5-66.7). The two "fixes" alone lost (46.7%). Composition matters more
  than any single fix.
- **Stat-aware death prediction beats HP-and-numbers** (V-M2 here). DZ's old fight rule called 64% of contacts lost
  while 6.5% ended in death: it retreated from fights it could take.
- **Selection noise is large**: single-opponent screens swing ±20 banked (SE ~10); best-of-K per map overfits.
  The lab found knob searches gain about +9 points by chance. Always confirm on an opponent not used to select.
- Top teams all draft **Heart of Ruin + Vesper Vale**; copying their draft without their play loses.
- Only the platform **duel set** (12 top teams × 2 groups × 5 games) has predicted the ladder; local suites screen
  regressions. Running it needs a submission, which is not authorised here. Ask the user only when a candidate
  passes G5/G6.

Null or negative (don't repeat as-is): knob searches (CMA-ES/SPSA over 48 knobs) that don't hold out; a Lanchester
*leave rule*; imitating top-team camp choice; packs/rushes/raids; shared-memory schemes; micro fight tweaks; a
contact fight evaluator *used as a rule* ("more of us wins" was as good); in DZ: pair or whole-team crews, bank
thresholds 15/45, health-first gear, retreat-to-allies, the threshold EE v1.

## 3. Runs in flight at pause (resume these first)

- **Z14 screen**: 32 of 58 runs remain (`research/dz/z-integration-2026-10-31/z14_configs.json`). Run
  `PY=python bash tools/dz_z14_screen.sh` (and a second copy with `REVERSE=1` to use 8 threads). On this PC, two
  interrupted raw folders (`artifacts/tmp/dz/dz-dv7-v76-01`, `dz-eerg-v65-z14-01`) must be deleted first; a fresh
  clone has none.
- Pause screens finished and are committed (EE2, EE2-bold, opening gold, gold value, three style pools).
  Still missing: opening-gold and gold-value **vs v76 and v65** (gold is v76's edge; run before A3 fitting).
- Then: `python tools/dz_plan_select.py --configs research/dz/z-integration-2026-10-31/z14_configs.json` (add EE2 and
  gold configs when screened; append the new bit names to `BITS` in plan.h order: ... `RING_GATES, OPENING_GOLD,
  GOLD_VALUE, EE2, EE2_BOLD`), build with `--set DZ_PLAN_TABLE=1`, and confirm against **v74** (never used for
  selection) plus idle and the three style opponents. G6: development-map gain vs holdout (every fifth map).

## 4. The task list (every idea, ordered; each is flag-gated with an exit test)

Priority A = expected large effect with supporting evidence; B = plausible; C = later or conditional.

### A. Team plans and the snowball (lab plan + lab4 evidence)

**A1. Native team plans in DZ (Z14/Z11).** Implement a DZ "team plan" layer: a small set of whole-team behaviour
modes, each a bundle of existing DZ terms:
- *home*: enemy-half groups priced ×0.3, engage aggression ×0.8 (lab v74's measured best generalist: 61% on unseen
  maps, deaths 10.8 → 6.9);
- *normal*;
- *hoard*: carry ×1.6 before banking;
- *fight*: engage threshold relaxed;
- *turtle*: own-half only, aggression ×0.65.

Define "enemy half" from the static map: the nearer spawn by home-field distance. Make the plan a runtime value
read each turn (like `plan_bits`), so a switch at round R changes nothing before R. Exit: each plan screened vs
v76 and v65; *home* expected to cut deaths (G5: deaths not up, Δ ≥ +50).

**A2. Branch farm and learned plan selection.** Port the lab tools as DZ *evaluation tools* (allowed):
`tools/lab/branch_farm.py`, `plan_model.py`, `branch_prefix.py`, `screen120.py` on `lab/box`. The method:
- Build per-branch binaries whose only difference is a volatile pair `(plan_round, plan_id)`, with non-zero
  initialisers so the code section and memory layout are identical. The lab's lesson: a constant 0 got folded
  and shifted the layout, and `PLAN_ROUND -1` changed the code. Verify with `branch_prefix.py` that every first
  divergence is at or after R.
- Play the baseline and 40 branches (8 switch rounds × 5 plans) per map/side/opponent. Baseline rows carry the
  position at each switch round (gems, carried, gold, kills, deaths, collected, earned, damage, per team).
- Fit `plan_model.py` (position → best plan, map-grouped CV, policy value against played results), then distil to
  a tiny table or tree (VIPER) for the bot.

Exit: CV policy gain > 0 with its interval above 0, then a G5 league check. The 5060 package (`pack5060.zip`,
v75-based) and box job 03 were set up for exactly this on the lab bot. Re-target them to DZ once A1 exists.

**A3. Gold and snowball (Z6/Z12).** `DZ_OPENING_GOLD` (gold 0.5 per gem before R250) and `DZ_GOLD_VALUE` (0.3 all
game) are built. Exit V-E3: R100 gold +10%, R250 not worse. Next, fit λ_gold properly, as the plan intends:
regress the final margin on R250/R500 gold from saved timelines across all runs, and set the weight from the fitted
marginal value of gold. Add kill-gold awareness: a near-certain kill (EE2 enemy-side estimate) is worth its bounty.

**A4. Per-map plans on the 70 known maps (Z14).** `DZ_PLAN_TABLE` exists. Finish the screen (§3), select on v76+v65
with margin ≥ 100 per map, confirm on v74 and the holdout. This is ext's proven lever, kept honest by confirmation.
Extend candidates to the A1 plans and to draft variants combined with plans.

### B. Combat, now that V-M2 passes (Z10)

**B1. EE2 in production.** `DZ_EE2` retreats only above P(death in 4) 0.15 (bold: 0.30) and engages won fights
below 0.04. Screen (§3). If it helps, add the *enemy-side* model: extract contacts for the opponent team
(`tools/dz_contacts.mjs ... 1`) and fit P(enemy dies in 4). Engage when the expected exchange is positive:
P(kill) × (kill gold + carried gems + tempo) − P(death) × (our value + respawn time). That is the multi-head value
the papers describe, built from calibrated parts.

**B2. Portfolio search over 3-5 scripts** (NaiveMCTS / Portfolio Greedy Search): fight, flee-to-home,
flee-to-ally, kite, focus-weakest. Score each with the cheap closed-form estimate (one `simulate_fight` costs
hundreds of fuel, not the 66k of a playout). Pick the best per contact turn. Exit: V-M2-style replay check of
chosen scripts, then G5.

**B3. Focus and ability use.** Target choice as a cheap attention-like score: bag, kill probability, threat
removed. Ability sequencing (reset→attack, Heart shield/missing-health, Vendetta camp-kill reset) from the duel
primitive (`duel.h`, conformance-verified). Elite-meta E5: change one carrier or sequence term at a time.

**B4. Heart + Vesper.** Every top team drafts them. Use draft variant 1 (Vesper/Heart core) with B1-B3 behaviour,
and test it as its own plan row.

### C. Economy and coordination (Z7, Z11, elite meta)

**C1. Market-based claims (Z7 auction / Z11).** Each body publishes a bid (its cost to its chosen group) in the
existing 6×7-bit claim slots; the cheapest bidder keeps the job, with ties broken by slot. No ML, low fuel. The
research says this fits best and fixes redundant jobs. Exit V-E1: idle income +10% vs the heuristic.

**C2. Big groups (the 9-map gap).** Price coalitions explicitly: who supplies damage, who stands on the region at
payout. Fix 02guardians (the gate the survival model rejects; it was clearable at 207) and the 01boss-battle siege.
Make `DZ_RING_GATES` cooperate with crews: crew only for gates and big groups, never for small ones. That was the
pair-crew failure.

**C3. Elite-meta priorities 1-8 and E1-E5**, each as an isolated flag:
- event-clock banking (start tribute before an imminent capture payout while on the region, if an altar is
  adjacent: E1);
- state-dependent delivery scheduler (E2; reject a global early-bank rule; protect Prism-like retained bags);
- item milestones from the next jobs (E3: Prospector only on qualifying cluster shares, Jungle when neutral damage
  forces recovery, Capture when waiting on regions, Tribute for long channels);
- protect repeatable production rather than reacting to death count (priority 5);
- geometric job features instead of map identity (priority 7: makes A4 transfer to unseen maps);
- fuel-freshness audit (priority 8).

**C4. Objective head (JueWu/HMS intent), conditional.** Imitating top-team camp choice was null, so train only on
*branch-best* labels from A2 (VIPER/Q-DAgger style), as a residual re-ranker over the scorer's top-K groups, with
scene balancing. C-priority: do it after A2 produces labels.

### D. Evaluation and tooling

- **D1. League (AlphaStar).** Judge against v76, v65, v74 and the three style bots, and later v71 and other repo
  bots. G5 requires no opponent below −150.
- **D2. Hyperband-style screens.** Run 20 dev maps first and promote survivors to the full pool. This cuts screen
  cost about 3×.
- **D3. Overall win rate with map-clustered bootstrap**, alongside banked margins (lab `screen120.py` reports both).
- **D4. Replay crawl of top-team engine-2 games** for B4/C4. It needs the user's platform login, so the user must
  log in themselves. Read-only downloads are authorised.
- **D5. Generated maps for generalisation** (`tools/mapgen` on branch `maps/generated-suite-120`, PR #1). Confirm
  that A4/A1 gains are not 70-map-specific.

## 5. Order of work for the next agent

1. Resume §3 runs → per-map table → confirm (v74, holdout, styles).
2. A1 team plans → A2 branch farm on DZ (this PC 8 threads; the 5070 Ti runner on `lab/box` can take jobs, see
   `docs/HANDOVER_5070TI.md` on that branch) → plan model → distilled selector.
3. B1 EE2 decision (and the enemy-side model) → B2 portfolio → B3/B4.
4. A3 λ_gold fit and kill-gold value; C1 market claims; C2 big groups; C3 elite experiments one at a time.
5. Combine the passing flags greedily, run a leave-one-out ablation, then G5/G6/G2 on the combined candidate,
   Z15 hardening, and G7 once. Report to the user; only they can authorise a submission or duel set.
