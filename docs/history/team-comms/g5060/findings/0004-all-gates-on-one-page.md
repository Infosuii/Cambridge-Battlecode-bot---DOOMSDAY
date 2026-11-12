# 0004: every R1 gate run on this machine, on one page (facts; 2 Nov 08:20 UTC)

All lines on the same 480 games (x2 + x2-s2, 70 ladder + 50 styled maps, both sides; no maze cell yet). Base x1
1746f2bb7fa3 = 257 wins, 339 fuel-outs, 10.84 deaths/game. Sorted by wins. Source: results/J003, J006-J010, RQ6.

## Pass R1 (wins ≥ base, no kind > 2 pts down, fuel-outs ≤ base, no faults)

| line | wins | fuel-outs | job |
|---|---|---|---|
| X1_SOAK64=1 | 267 (+10) | 327 (-12) | J007 |
| APEX_ESCORT=1 | 265 (+8) | 332 (-7) | RQ6 |
| A2_HIDEREC=1 | 264 (+7) | 333 (-6) | RQ6 |
| X1_SECURE=1 (MULT 1.5 / 3.0) | 261 (+4) | 338 / 337 | J003 |
| A2_BURST_HOLD=1 | 260 (+3) | 334 (-5) | RQ6 |
| X1_SECURE=1 MULT 6.0 | 259 (+2) | 337 (-2) | J003 |

## Win more but fail only on the fuel-out clause (findings/0001)

| line | wins | fuel-outs | job |
|---|---|---|---|
| X1_ANTIFEED=3 WIN=250 | **284 (+27)** | 342 (+3) | J006 |
| X1_PLAN=1 R100 plan 4 (turtle from R100) | **280 (+23)** | 348 (+9) | J009 |
| X1_PLAN=1 R150 plan 4 | 275 (+18) | 386 (+47) | J009 |
| X1_ANTIFEED=4 / 7 / 3 / 3 W100 / 5 | 271 / 270 / 268 / 268 / 265 | 348 / 350 / 347 / 349 / 356 | J006 |
| X1_PLAN=1 R150 plan 6 | 270 (+13) | 351 (+12) | J009 |
| A2_BURST2=1 | 270 (+13) | 359 (+20) | RQ6 |
| X1_ECON stage 0.5 | 268 (+11) | 342 (+3) | J010 |
| A2_TS_VIS=1 | 268 (+11) | 423 (+84) | RQ6 |
| X1_PRUNEFIX=1 (also styled -3 pts) | 268 (+11) | 365 (+26) | J007 |
| X1_ECON wait 2.0 / 1.5 | 266 / 265 | 382 / 358 | J010 |
| V58_LOCKS=1 | 265 (+8) | 358 (+19) | RQ6 |
| A2_DISENGAGE=1 | 264 (+7) | 344 (+5) | RQ6 |
| X1_ECON need 1.3 | 263 (+6) | 359 (+20) | J010 |
| X1_PLAN=1 R150 plan 3 | 263 (+6) | 345 (+6) | J009 |
| A2_BELIEF=1 | 262 (+5) | 349 (+10) | RQ6 |
| X1_PLAN=1 R150 plan 8 | 261 (+4) | 373 (+34) | RQ3 |
| X1_SIEGE_STRICT=1 | 258 (+1) | 361 (+22) | J007 |

## Lose wins

X1_HEARTFIX 257 (0), X1_TEAMWIN 256, X1_PLAN R0 plan 6 256, A2_THREAT 255, A2_RESETFIX 253, X1_BAGRISK 80 / 50 / 30
253 / 250 / 228, X1_FLEEDROP 15 251, A2_MAP_PROFILE 251, X1_PLAN R0 plan 4 250, APEX_STALE_BAG 246, V58_VISION 244,
A2_FIELDFIRST 244, X1_FLEEHOLD 4 239, X1_ALONE 232, X1_FLEEDROP 40 / 25 / 60 232 / 229 / 225, X1_FLEEHOLD 8 225,
A2_ASSESS 222 (5,214 fuel-outs), X1_FLEEHOLD 15 187. Dead paths (0 games changed): X1_HUNT_SOLO 3 / 5 (also under
plan 8).

## Proposals (PC decides)

- The two biggest gains (ANTIFEED 3/250 +27, plan 4 from R100 +23) both cut deaths (9.4 and 8.6 vs 10.8) and differ
  from the base by only 3 and 9 fuel-outs on 480 games. If the fuel clause is relaxed (findings/0001), they lead.
- Every pass and near-pass is a candidate for the joint search (R3). I can run any stack you post as a gate line now
  (5 min each), or a seed-2 confirmation (x2-s3 / other opponents) of the top lines.
