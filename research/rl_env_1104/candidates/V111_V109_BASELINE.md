# Stock v111 vs stock v109 baseline (JOHNDOE #167)

**Artifacts.**
- v111: Ishan source 53157d6f (bots/codex-live111-frozen, 40 files; archive 72e9a198). SDK5 release build 0896a189, matching Ishan.
- v109: exact f3d919e9.
- Opponents:
  - nnfinal: JOHNDOE's pinned Mac guest 317e4ad9 from 1345fed3, played as-is.
  - v86h: 0fae1c17.
  - x3inv: d762af61.

**Setup.** 15 manifest development maps x A/B, cambc 5.0.0 / engine 3.0.0, default seeds, release, normal budget. Run e3-v111-v109-base-02: 180 games, 0 failed, 0 faults.

Runner: `cambc run-batch` accepts only project directories, so when a .wasm guest is present, run_eval now plays game by game with `cambc run`, using the hashed release WASMs. An earlier attempt that rebuilt per game collided on build directories (7/180 failed); it is kept as e3-v111-v109-base-01-collided and is not used.

| opponent | v109 | v111 | paired v111 - v109 [family 95%] | flips +/- | fuel-outs v109 / v111 |
|---|---|---|---|---|---|
| nnfinal | 14/30 | 16/30 | +0.067 [-0.179, +0.312] | 8 / 6 | 96 / 146 |
| v86h | 18/30 | 18/30 | +0.000 [-0.179, +0.192] | 6 / 6 | 102 / 176 |
| x3inv | 17/30 | 18/30 | +0.033 [-0.167, +0.269] | 6 / 5 | 99 / 144 |
| ALL | 49/90 | 52/90 | **+0.033 [-0.089, +0.167]** (13 families) | 20 / 17 | 297 / 466 |

**Reading.**
- Strength: v111 is level with v109 on this panel, with a slight positive point estimate everywhere and no opponent showing a negative estimate.
- Fuel-outs: v111 runs out of fuel 57% more often (466 vs 297), consistent with Ishan's v111 safety baseline. v109 has full CLFS 1, while v111 compiles CLFS 9, which turns on only the slow-block estimates and the warm-up/rebuild margins. The fuel gap is therefore probably the missing parts (scoring margin and slower need decay) and/or v111's larger network, but that is not tested here.
- This is a stock-vs-stock strength comparison only. It does not tune anything or duplicate Ishan's runtime qualification.
