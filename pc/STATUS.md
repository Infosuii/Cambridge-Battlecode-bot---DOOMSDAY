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
| J002 take over sweep 1d | **go** |
| J003 retry round 1 | posted |
| J004 maze maps | asking Rishik for Agent 2's maps; PC builds a fallback set if none by 12:00 |
| J005 branch farm | running on 5060 |
| J006 anti-feeding gate | posted, priority 1 after J005 |
| J007 audit fixes (6 switches) | posted, after J006 |

## PC quick screens for J007 (19 ladder maps vs x2, 38 games; base 17 wins, 326 deaths, 21 fuel-outs)

prunefix 21 (deaths 264), teamwin 20 (301), soak64 19 (330), heartfix 18 (323), siegestrict 17 (335), fleehold8 15
(304). No faults, no added fuel-outs. Screens catch bugs only: every line still gets the full J007 gate, and
fleehold keeps its 4 / 15 variants (retry protocol).
