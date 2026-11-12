# Z-plan first integrated pass (2026-10-31)

Selected release **5cf28cb7 is unchanged**: with every new flag at its default (0) the build is byte-identical
(`tools/dz.py build` → `5cf28cb74612…`). All new components are **unvalidated experiments behind `DZ_*` flags**. None
passed confirmation on a separate opponent, so none is promoted. No ladder, submission or activation. No old bot code
was read or copied; v76/v65 were opponents only, and v76 was also benchmarked as a candidate against idle (reference).

Setup on this PC: GCC 16.2 (WinLibs, via winget; MSYS2's installer failed here). GCC 16 adds a
`-Wmisleading-indentation` error in `duel.h`, so `tools/dz.py host` now passes `-Wno-misleading-indentation`
(no source change). Host tests and 54 Python tests pass; all earlier capsules verify.

## Diagnosis (stored release runs plus one new reference)

| | DZ vs v76 | DZ vs idle | v76 vs idle (`dz-ref-v76-idle-01`) |
|---|---|---|---|
| banked / opponent | 226 / 1028 | 920 | 1013 |
| deaths per game | 19.0 (15.7 to champions) | 4.5 (camps) | 0.9 |
| game length | 992 | 1334 | 914 |
| R500 banked | 130 | 332 | 412 |

- Contested: DZ 1.1 kills vs 15.7 deaths per game, 12.0k vs 22.3k champion damage, 2.0k vs 6.8k gold. First death
  median round 114. The 00ambush-A replay shows the typical death: a lone full-HP Vendetta (1000 max HP) meets v76's
  Ren (1300 max HP) at R204, trades evenly for eight rounds, then flees a same-speed chaser and dies at R221.
- Idle economy: by R500 both clear about the same number of camps (DZ 33, v76 37), but v76 averages 13.4 gems per
  collection vs DZ 8.8 and banks 26 gems per trip vs 13. A third of v76's R1000 gems come from groups DZ never
  collects. The gap concentrates on 01boss-battle, 02guardians, 02the-pack, 01islands, 01corridors,
  01concentrated-wealth, 02harvest, 00ribs and 01the-farm.
- 02the-pack: DZ sat on a Bank goal for 900+ rounds 4 tiles from an altar whose pocket is ringed by live camps; the
  8-neighbour gate test reported `gates=0`. That is what `DZ_RING_GATES` addresses.

## Components (all default 0)

| Plan step | Flag(s) | What it does |
|---|---|---|
| Z10 combat evaluation | `DZ_EE` (+`DZ_EE_NEAR` 3, `DZ_EE_SCAN` 10, `DZ_EE_MEMORY` 20) | Losing local fight: retreat once the enemy is within range+3, not only at reach; enemies within 10 enter the estimate; personal sightings (8 slots, 20 rounds) price nearby jobs ×0.33 like visible enemies. |
| Z10 | `DZ_EE_REGROUP` | A losing retreat heads for the nearest healthy ally within 12 instead of home. |
| Z9 conditional gear | `DZ_GEAR_SURVIVE` | Openers Jungle→Monster→Durability(health) (Heart/Ryth: Jungle→Durability→Monster, health), no Treasure. |
| Z9 | `DZ_GEAR_PROSPECT` | Third emblem is Prospector when the map has gem-paying cluster groups (`map_shop`). |
| Z9 | `DZ_GEAR_HEALTH` | Health-stat Jungle→Durability→Prospector for every body. |
| Z11 crews | `DZ_CREWS` (+`DZ_CREW_ALL`) | Slot pairs (0,1),(2,3): the follower adopts the leader's published group job; the leader prices pair damage. `DZ_CREW_ALL`: one whole-team crew. |
| Z6 objective/bank | `DZ_BANK_NEAR_MIN`, `DZ_BANK_BIG` | Near-altar bank needs ≥15 gems; ordinary trip bag 45. |
| Z14 map-aware | `DZ_RING_GATES` | Boot pass (resumable, budgeted): if the ally spawn cannot reach an altar's pocket with camp tiles blocked, every camp member bordering the pocket is a gate member. With every altar gated, bodies clear the weakest gate group the whole living team can survive (clear-risk model, all living allies' damage); otherwise the old fallback. |

## Results (140 cells each: 70 maps × 2 sides; paired against the stored selected-release runs)

vs v76 (baseline `dz-carrier-priority-v76-check-01`, banked 225.8):

| Run | Δ banked | SE | maps better/worse | deaths | wins |
|---|---|---|---|---|---|
| `dz-gsp-v76-01` survive+prospect | **+22.5** | 7.7 | 65/39 | 18.6 | 2 |
| `dz-gs-v76-01` survive | +12.7 | 6.2 | 55/44 | 18.5 | 1 |
| `dz-gp-v76-01` prospect | +0.6 | 4.2 | 29/19 | 19.1 | 1 |
| `dz-int1b-v76-01` gear+gates | +2.2 | 8.0 | 55/51 | 19.0 | 1 |
| `dz-int1c-v76-01` gear+EE | +1.4 | 11.4 | 65/66 | 15.7 | 0 |
| `dz-int1-v76-01` gear+EE+gates | −2.2 | 11.1 | 58/74 | 15.7 | 0 |
| `dz-bb-v76-01` bag 45 | −2.0 | 6.8 | 28/32 | 18.9 | 1 |
| `dz-gates4-v76-01` ring gates | −8.4 | 5.4 | 24/31 | 19.4 | 1 |
| `dz-rg-v76-01` regroup | −9.1 | 9.0 | 58/63 | 19.9 | 1 |
| `dz-ee1-v76-01` EE | −10.4 | 11.4 | 62/68 | 16.1 | 0 |
| `dz-ghp-v76-01` health gear | −19.3 | 9.0 | 51/72 | 17.3 | 0 |
| `dz-eerg-v76-01` EE+regroup | −21.5 | 10.9 | 50/78 | 17.7 | 0 |
| `dz-crew1-v76-01` pairs | −24.9 | 11.8 | 55/73 | 18.7 | 0 |
| `dz-bn-v76-01` near-bank ≥15 | −30.1 | 9.8 | 38/73 | 18.9 | 1 |
| `dz-crewall-v76-01` whole-team crew | −36.7 | 14.1 | 50/78 | 18.9 | 1 |

vs idle (baseline `dz-carrier-priority-idle-01`, banked 919.5): gsp +15.6 (SE 8.8), survive +22.9, int1 +10.2 (SE 15.5),
gates4 +6.5 (SE 5.3), bag 45 +13.7, prospect −7.7, near-bank +2.5, pairs −28.4, health gear −49.8, whole-team crew −77.8.

**Confirmation on a separate opponent (v65, baseline `dz-carrier-priority-v65-full-01`, banked 261.6):**
`dz-gsp-v65-confirm-01` **−6.9 (SE 9.6)**, `dz-int1-v65-confirm-01` −35.7 (SE 14.9). The v76 gear gain does not hold;
with ~15 variants screened on v76 it is consistent with selection noise. Nothing is promoted.

Faults 0 in every run. Fuel-outs 0 everywhere except the first ring-gate builds (`dz-gates1-*`, `dz-gates2-*`: 66,
all in boot rounds 11-20 on 01islands/02the-pack); the resumable boot pass (`dz-gates3+`) removed them. `dz-ref-v76-idle-01`
fails the runtime gate (v76's own 72 fuel-outs) and is kept only as a reference. Diagnostic trace runs
(`dz-diag-*`) distort fuel and play and are not strength evidence.

## What this means for the next agent

1. The contested gap is not a retreat-threshold problem. DZ loses even trades because v76 bodies have more max HP and
   3.5× the gold by mid-game; all retreat/regroup/crew variants left kills at about 1 per game. The next combat work
   should use real stat/ability state (the duel primitive in `duel.h`, abilities, focus) rather than more thresholds.
2. The economy gap is concentrated on about ten maps where DZ cannot reach or clear the high-value groups. Ring gates
   fix the detection on 02the-pack/01islands; 02guardians still needs a gate the survival model rejects, and
   01boss-battle needs the siege plan.
3. Screen against one opponent, confirm on another. Single-opponent screens in this pass swung by ±20 with SE ~10.

## Part 2 (same day): runtime plans, style opponents, gold weight, V-M2

All defaults 0; the default build is still byte-identical to 5cf28cb7.

- **Runtime per-map plans (Z14).** `DZ_PLAN_TABLE=1` makes every experiment flag a runtime bit (`plan.h`: `DZ_ON(X)`
  reads the table bit, `DZ_HAS(X)` compiles the code when the flag or the table is on). `map_plans.inc` rows are
  `{signature, draft (-1 = incumbent), bits}`, loaded once (`load_plan`) in draft and in play. `map_signatures.txt`
  lists all 70 signatures (from `dz-diag-signatures-01`; they match the incumbent draft table).
  `tools/dz_plan_select.py` picks per development map (holdout excluded) the config that beats the baseline by
  `--margin`, summed over opponents and sides, skipping configs with faults or fuel-outs on that map.
  Candidates: `z14_configs.json` (15 flag configs + draft variants 1-7 with and without gear). Screen: 26 of 58 runs
  done when paused; `tools/dz_z14_screen.sh` resumes it.
- **Z13 style opponents.** `DZ_STYLE` 1 rusher (hunts visible enemies, otherwise marches to the altar nearest the
  enemy spawn), 2 turtle (groups within 14 of home, leaves enemies within 8, never chases), 3 cluster farmer. They're
  generated by `tools/dz_styles.py` into git-ignored `bots/dzs-*`. Check runs `dz-z13-*-check-01`: 18 games, 0 faults.
- **Gold weight (Z12/Z6).** `DZ_OPENING_GOLD` (gold 0.5 per gem before R250), `DZ_GOLD_VALUE` (0.3 all game);
  default 0.1. Motivation: idle R100 gold DZ 180 vs v76 329, R500 1346 vs 2312.
- **V-M2 passes (Z10).** `tools/dz_contacts.mjs` + `dz_contacts_build.py`: 150,742 contact samples (team turns with an
  enemy within 8) from the 140 selected-release games vs v76, with true strength from each unit's perspective.
  `tools/dz_vm2.py`, game-grouped 5-fold CV: 4-round death Brier **0.0379** stat-aware vs **0.0398** HP-and-numbers
  baseline (Δ −0.0020, game-clustered CI below 0); DZ's current rule scores 0.644 (it calls 64% of contacts lost;
  6.5% die). Coefficients in `bots/dz/src/ee_model.h`; `DZ_EE2` retreats above P 0.15 (`DZ_EE2_BOLD` 0.30) and
  engages simulated wins below P 0.04, otherwise keeps working. Results: `research/dz/vm2-2026-10-31/RESULTS.json`.
  The contact dataset is regenerable: `python tools/dz_contacts_build.py dz-carrier-priority-v76-check-01 OUT`.

### Part 2 results (140 cells each)

| Run | Result |
|---|---|
| `dz-ee2-v76-01` / `dz-ee2-v65-01` | −6.7 (SE 12.0) / −21.2 (SE 13.4); deaths 19.0 → 20.8 vs v76. The better predictor used as a retreat threshold loses more bodies. Contested gate fails; off. |
| `dz-ee2b-v76-01` / `dz-ee2b-v65-01` | −6.6 (SE 12.0) / −34.5 (SE 15.0); fails |
| `dz-og-idle-01` (opening gold) | banked 926 (+6.7); R100 gold 180 → 223 (+24%), R250 gold 590 → 702, but R250 gems 176 → 155 and R500 357 → 340. V-E3 split; needs contested screens. |
| `dz-gv-idle-01` (gold 0.3) | banked 911; R100 gold +18%, R250 gems −6% |
| `dz-z13-rusher-01` / `-turtle-01` / `-farmer-01` | DZ wins 120 / 140 / 114 of 140, 0 faults and 0 fuel-outs on both sides in 420 games. **Z13 exit test passes.** |

## Part 3 (2026-10-31 night): exact Z14b table and its confirmation

Exact screening: every config ran as a uniform 70-row table under `DZ_PLAN_TABLE=1` from one frozen snapshot
(`z14b_source`), so a selected map replays the screened game exactly against v76/v65 (identical Wasm code
section, checked). Plan-table fuel fix: play computes the map signature from loaded camp tiles (the extra SDK
camp walk overran the boosted first turn on big maps). 30 configs incl. A1 team plans (home, hoard, fight, turtle).
Selection (`z14b_selection.json`, margin 100 on v76+v65): 55 of 56 development maps get a row; turtle 7, dvg7 6,
homedv1 5, then draft variants with and without gear.

Confirmation (never used to select; paired with the uniform-base table run vs the same opponent, 140 cells):

| Opponent | Δ banked all (SE) | Δ banked dev | Δ margin dev (SE) | deaths | fuel-outs |
|---|---|---|---|---|---|
| v74 | **+78.4 (15.3)** | +97.9 | +114.8 (27.4) | 17.8 vs 19.6 | 0 |
| v81hl (team's current best) | **+26.7 (11.2)** | +33.4 | +25.1 (19.0) | 17.9 vs 18.9 | 0 |

Holdout Δ is 0 by construction (holdout maps keep the base row), so G6 cannot judge a per-map table; it needs
generated maps (D5) or a geometric selector (C3 priority 7). G5 vs v74 passes the +50 bar; vs v81hl not yet.
Wins remain 0 (DZ ~300 banked vs ~1000). Candidate build: `--set DZ_PLAN_TABLE=1 --plan-rows z14b_table.inc --source z14b_source`.
