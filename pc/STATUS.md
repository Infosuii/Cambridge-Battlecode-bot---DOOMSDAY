# PC status (Rishik's PC, 8 threads), 2 Nov 2026 00:30

- x1 = `bots/x1` on `build/z-plan`, hash **1746f2bb7fa3** (fuel fix + camp watch on; all other X1_* switches off).
- Benchmark v88 = `bots/x2` (a9f1bbc43ef7), seed build `bots/x2-s2`. v86h 0fae1c17ee73, v86h-s2 a0d2aabd702a.
- x1 vs x2: ladder 68/140, styled 55/100.
- Working on: plan hook X1_PLAN (X1_PLAN_ROUND / X1_PLAN_ID, 8 plans). Builds with the hook off equal x1; checking
  that branch builds share one code section before posting the branch-farm job.
- Also here: ladder matches vs other teams and replay downloads for analysis (PC only).
- **Sweep 1d stopped here (2 Nov ~09:00).** Its finished runs (x1-sd-*), all x1e-* evals incl. x1e-cw-ladder-x2-01 and
  x1e-cw-unseen-x2-01, and research/x1/sweep1c_hashes.json are pushed on build/z-plan (msg 0001 answered). J002: go.
- New message: pc/msgs/0001 (read the whole repository).

| Job | State |
|---|---|
| J001 setup and reproduce | posted |
| J002 take over sweep 1d | **moved to g5070 as K003** (remainder returns to 5060) |
| J003 retry round 1 | posted |
| J004 maze maps | Rishik is asking Agent 2 to push maps_mazetest + maps_real200b; fallback: PC builds a maze-style set if none by 12:00 |
| J005 branch farm | running on 5060 |
| J009 whole-game plan gates (plan 4/6/3) | **posted, priority 1 right after J005** |
| J010 flee-drop + economy gates | **posted, after J009** |
| J006 anti-feeding gate | posted, after J010 |
| J007 audit fixes (6 switches) | **moved to g5070 as K002** |
| J008 bag-risk gate | posted, after J006 |

## PC quick screens for J007 (19 ladder maps vs x2, 38 games; base 17 wins, 326 deaths, 21 fuel-outs)

prunefix 21 (deaths 264), teamwin 20 (301), soak64 19 (330), heartfix 18 (323), siegestrict 17 (335), fleehold8 15
(304). No faults, no added fuel-outs. Screens catch bugs only: every line still gets the full J007 gate, and
fleehold keeps its 4 / 15 variants (retry protocol).

## 5070 Ti (g5070), 1.5-hour burst

| Job | State |
|---|---|
| K001 setup + reproduction | posted |
| K002 = J007 audit gates | posted |
| K003 = J002 sweep 1d remainder | posted (if time) |

## PC reading of J005 partial (01:16)

Plan 4 (turtle) is the strongest switch: net +20 @R150, +27 @R250, deaths -2, gold@R500 +29..39; plan 6 +17 @R150;
plan 8 (push) and 2 (hoard) are the weakest. x1 is over-aggressive vs v88. Next: J009 tests these as whole-game
settings; the PC investigates plan 4's extra fuel-outs.

## Later (low priority, after J009/J010/J006/J008 report)

Phase 4 design: research/x1/CBR_IM_ARCHITECTURE.md on build/z-plan. Your part later: J011 harvest map descriptors,
J012 case library from J005 rows + leave-one-map-out test. Not posted yet; keep the J005 rows (all columns).
