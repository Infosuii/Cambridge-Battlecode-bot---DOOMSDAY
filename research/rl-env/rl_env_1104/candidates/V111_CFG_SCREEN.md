# v111 single-switch screens (R1-owned per JOHNDOE #175)

**Base and setup.**
- Base: exact v111 (Ishan 53157d6f, WASM 0896a189).
- Maps and engine: 15 manifest development maps x A/B, engine 3 / cambc 5.0.0, release.
- Opponents: nnfinal 317e4ad9, v86h 0fae1c17, x3inv d762af61, v109 f3d919e9. That is 120 games per arm, paired against stock v111 on identical cells.

**What the bits are.** v111 picks a2stack cfg by draft size: 14377 for 3 or 5 picks, 12297 for 4. 14377 sets bits 1, 8, 32, 2048, 4096 and 8192. Each variant changes exactly one bit.

## e3-v111-need-01: bit 1 off (no forced lone camp attacks)

need 63/120 vs stock 71/120. Paired **-0.067 [-0.200, +0.050]**. It is worse vs v86h (15 vs 18) and x3inv (13 vs 18), the opponents it was aimed at. **Rejected.**

## e3-v111-cfgbits-01: 960 games, 0 failed

| variant | change | nnfinal | v86h | x3inv | v109 | all | paired vs stock |
|---|---|---|---|---|---|---|---|
| stock v111 | - | 16 | 18 | 18 | 19 | 71/120 | - |
| nomarcfun (6ade273a) | bit 8 off: no Marcella gold funnel / carry 40 / reward x1.5 | 20 | 17 | 20 | 20 | **77/120** | **+0.050 [-0.025, +0.125]** |
| nolatebru (b3a6184b) | bit 32 off: no late Bruiser items | 15 | 16 | 22 | 20 | 73/120 | +0.017 [-0.027, +0.063] |
| nocarry45 (01da95a1) | bit 8192 off: no 45-gem tribute cap | 18 | 20 | 16 | 16 | 70/120 | -0.008 [-0.083, +0.096] |
| nomarcagg (c2a360fa) | bit 2048 off: no Marcella aggression/hunt change | 15 | 13 | 19 | 16 | 63/120 | -0.067 [-0.133, +0.009] |
| sharegold (fdc65de3) | bit 4096 off: gold sharing restored | 15 | 15 | 13 | 16 | 59/120 | -0.100 [-0.212, +0.010] |
| topbuild (27b7b0d7) | bit 512 on: whole-team top-team item build | 11 | 17 | 13 | 14 | 55/120 | -0.133 [-0.257, -0.008] |
| topdraft (ab91a7d6) | bit 16384 on: top-15 teams' draft | 5 | 6 | 14 | 4 | 29/120 | -0.350 [-0.458, -0.250] |

**Reading.**
- Most existing bits look earned: turning off 2048 or 4096, or turning on 512 or 16384, hurts.
- nomarcfun is the best of seven arms. That is a multiple-comparison winner, so it is frozen as-is and confirmed on held-out maps (below) before it counts as a candidate.

## Held-out confirmation of nomarcfun (e3-v111-nomarcfun-holdout-01, 336 games, 0 failed)

21 generated holdout maps from f584c0ad, whose templates are not among the 15 development maps (12 template families; `manifests/genholdout_f584c0ad.json`). The four opponents are the same as above, both sides, release, engine 3.

| opponent | stock v111 | nomarcfun |
|---|---|---|
| nnfinal | 20/42 | 21/42 |
| v86h | 20/42 | 15/42 |
| x3inv | 32/42 | 29/42 |
| v109 | 24/42 | 19/42 |
| ALL | 96/168 | 84/168 |

Paired nomarcfun - v111: **-0.071 [-0.138, +0.006]** (12 families).

**Verdict: rejected.** The development gain (+0.050) was a seven-arm selection effect and reverses on held-out maps. Stock v111 remains the best verified build. None of the a2stack single-bit changes beats it.
