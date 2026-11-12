# botx3 development log — 2 November 2026

Local implementation and development screens only. No upload, submission, activation, or publication was performed. Original x1 source is frozen in `original-x1-source.zip`; both initial and final repair-off Wasm equal `1746f2bb7fa341530f41bd8c8c4896b35172783f35eacee8e4a4b6ac0ceea183`. The x1c1 parent rebuild equals `22e6067a423356e29e6738438f47b22d05b554767757717e58bf350392e16b13`. Production x1 source hashes remain unchanged.

## Baseline assessment

K004–K009 are complete in `../../../x1-comms/g5070/results/FINAL_SYNTHESIS.md`. Their broad evidence establishes no universal replacement for original x1. K009 x1c1-equivalent: 419/716 versus original x1 379/716 against x2 builds, but 378/720 versus original x1 406/720 on the v86h/v81hl robustness pool. BP lowers fuel but also loses strength on that robustness pool. Preserve original x1 as the primary competitive reference and BP as an engineering comparator. Neither is universally best.

The connected GitHub check found completed [K010](https://github.com/Infosuii/neural-networkk-battlecode/blob/comms/x1/pc/analysis/K010_pc.md), preserved in `K010_pc.snapshot.md`. It reports x1c1 177/358 against original x1 and 198/358 against v86h, with poor historical results against the top two opponents. Those historical ladder records are repeated map outcomes and different sampling dates, not fresh paired trials. K010 attributes late economic stalling to indefinite plan 4 as a hypothesis. No new ladder games were requested or played.

v92 source was fetched through connected GitHub. All 35 source files verify against recorded Git blob IDs after accounting only for line-ending/trailing-newline normalization (`v92-verified.json`). Its compiled Wasm hash is in `manifest.json`. Original x1 wins 7/12 against it here; this small selected sample cannot rank v92 universally. Remote branch heads were not fetched into Git because shell DNS was unavailable; source/results checks used connected GitHub and local refs.

## Implementations and diagnostics

`bots/botx3` is an isolated source copy. All new switches default off. X3_PLAN_END restores base strategic knobs at expiry, including the persistent hunt offset for plans 6/8. Separate native telemetry confirms plan 4 starts at R150 and expires at R500.

X3_COVER_SAFE hides IDs belonging to an active partial bush flood and queries current enemy ward tiles before claiming hidden cover. The native synthetic paused-flood probe reproduces old partial ID 0, repaired unknown -1, and completed ID 0 in both versions, on all three acting champions. This verifies the repaired mechanism, not its natural-match frequency. The stale hidden-recall report does not apply to this source: `w.update(round)` already precedes the check, so no duplicate fix was added. Other visibility consumers and stack-overflow behavior remain unaudited.

Economic attempt 1 amortizes legal terrain bank distance and deposit time into camp candidate cost. Existing need/health checks, respawn knowledge, target persistence and shared-claim staffing remain the executors. It is a one-job delivery prototype, not a new team-wide optimizer. The later route search still uses its original cost model, a plausible interference mechanism.

Attempt 2 reuses the existing APEX_PLAN rolling-horizon camp/respawn/bank search instead, discounts carried gems rather than immediately usable gold, and considers all group members for bank distance. Attempt 3 admits optional search only above 50k fuel, limits first candidates to four and horizon to two jobs, and checks a 45k reserve inside scans. This addresses measured planner fuel exhaustion; nearest-member bank distance remains an optimistic abstraction for extended groups. Draft-time graph transfer and a new team scheduler have not been implemented.

Twelve host boundary/economic-model checks pass. Separate native activation diagnostics show actual candidate costs and planner decisions; instrumented builds are excluded from strength evidence. The final off build remains byte-identical after all edits.

## Paired development screen

Six already-inspected layouts: four official maps highlighted by K010, one styled generator map and one maze. Four opponents (x2, v86h, v81hl, v92), both sides: 48 cells per arm. Selection is deliberately diagnostic, not representative or untouched validation. Frozen source copies, compiler logs, injected Wasm, exact flags, map/opponent/CLI hashes, native replay bundles, receipts and raw summaries are retained. `analysis.json` includes exploratory map-cluster intervals; six correlated maps provide weak uncertainty estimates.

| Arm | Wins /48 | Fuel-outs | Mean collected | Mean banked | x2 / v86h / v81hl / v92 wins |
|---|---:|---:|---:|---:|---|
| off | 29 | 112 | 991.5 | 855.3 | 8 / 8 / 6 / 7 |
| parent | 25 | 114 | 1011.0 | 869.0 | 7 / 6 / 5 / 7 |
| end500 | 32 | 114 | 1028.5 | 910.9 | 10 / 8 / 6 / 8 |
| cycle | 23 | 128 | 957.9 | 830.2 | 7 / 5 / 5 / 6 |
| cover | 33 | 114 | 1051.0 | 919.8 | 11 / 9 / 6 / 7 |
| end500cycle | 23 | 115 | 969.9 | 828.8 | 6 / 7 / 3 / 7 |
| bp | 34 | 114 | 1046.8 | 920.2 | 11 / 9 / 7 / 7 |
| planner_control | 20 | 214 | 968.9 | 837.9 | 6 / 4 / 5 / 5 |
| planner_repair | 16 | 300 | 930.3 | 815.4 | 5 / 3 / 3 / 5 |
| planner_budget_v3 | 17 | 101 | 993.5 | 865.3 | 4 / 3 / 6 / 4 |
| end5000 | 27 | 114 | 1018.8 | 882.8 | 8 / 6 / 5 / 8 |

All 528 completed comparison cells have 0 own and 0 opponent faults. 68 cells reuse exact previous byte-identical conditions. BP controls were initially rerun before the cache lookup was generalized to all arms; those repeats are not counted as independent evidence. An interrupted admission-only planner build and its partial cells remain under `builds/planner_budget` / `games/planner_budget`, excluded from this completed matrix. No incomplete game is silently counted as a win or loss.

## Failed-game investigation and outcomes

Four native v92/gold-rush-side-A replays were decoded with the pinned engine 2.0.0 visualiser. Original x1: 11 deaths, 21 completed bank actions, 0 fuel-outs; delivery-cost attempt 1: 31 deaths, 13 completed bank actions, 0 fuel-outs. Final banked score falls 1047 → 159. This is a strategic/execution interaction failure, not fuel exhaustion in that replay. The audit does not by itself identify exactly which target decision caused the fights. Raw actor counts are in `replay-audit/behaviour.json`.

The cost model plus expiring plan combination scores 23/48, versus expiry alone 32/48; combination testing did not rescue this prototype. This is not a full four-arm factorial interaction estimate because the baseline configurations differ. No such estimate is claimed.

- **Retry required — cover repair:** source bug reproduced and repaired, but 33/48 versus BP 34/48 is no strength improvement. Need natural guard-trigger frequency, ward/cache scenarios and broader paired testing.
- **Parked — bank-cycle / rolling planner:** three mechanism-motivated implementations tested, plus unchanged planner control. Bounded search lowers measured fuel but does not establish competitive value. No further arbitrary parameter grid; next work must resolve route/executor consistency, forecasted service accuracy and economic staffing. This does not reject coordinated economic planning.
- **Retry required — expiry:** promising parent-relative screen, but adding a hook changes some pre-expiry games. Same-code never-expire control and prefix checks below are required before attributing wins to expiry.
- **Conditionally useful — bounded optional computation:** reduces planner fuel-outs versus unbounded repaired search; its worse wins prevent universal adoption.
- **Accepted:** no new strategic candidate. **Rejected:** none.

### Expiry causality control

{
  "comparison": {
    "wins_delta": 5,
    "exploratory_map_bootstrap95_pp": [
      2.083333333333333,
      18.75
    ],
    "maps": {
      "01starvation": 0,
      "01gold-rush": 0,
      "00great-wall": 2,
      "00rows": 1,
      "gen4_0005": 2,
      "pc_maze_00": 0
    }
  },
  "prefix": {
    "parent": {
      "100": 0,
      "250": 5,
      "500": 6
    },
    "end5000": {
      "100": 0,
      "250": 0,
      "500": 0
    },
    "same_wasm_code_section": true
  }
}

The never-expire control scores 27/48 versus expiry 32/48 (+5), with identical Wasm code sections and equal recorded R100/R250/R500 checkpoints in all 48 pairs. These checkpoint samples precede the resulting divergence and support an expiry effect better than the parent comparison. Full action/observation-prefix equality remains unchecked. The six-map exploratory interval excludes zero but is post-selection and provides no protected-family generalization evidence. Expiry remains Retry required pending broader validation.

## Generalization and next work

No genuinely untouched families were consumed. Therefore no new generalization claim or final acceptance is made. The new mechanisms use legal geometry/observations rather than map IDs, but the inherited bot still contains recognized-map tables. A map-independent whole bot has not been established.

Next: (1) native action-prefix comparison and broader official/styled/maze validation for expiry; (2) direct natural cover-trigger/ward coherence telemetry; (3) derive a coherent economic job/service model from legal replay projections and validate predictions before another planner search; (4) implement bounded shared team scheduling with explicit capture ownership and banking commitments; (5) freeze independently implemented map-generator families before selection, then run a once-only protected validation. Defer adaptive selectors until distinct strategies show reliable value.

The mandatory failure/retry protocol is persisted in the workspace `AGENTS.md` and the map-research evaluation protocol. Gate failure is never treated as feature rejection.
