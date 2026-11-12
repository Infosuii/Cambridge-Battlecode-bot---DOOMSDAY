# Discovery ablations

**MEASURED:** 1,280 official release games, no faults, engine 2.0.0. Each variant has 256 paired cells across the 16 verified JD heavy development maps, both sides, two own-score seeds (301/607, ±0.5%), and v92, x3inv, p65pack, public-khiri. The same noise was applied to the baseline and each variant. See [binary hashes, counts and opponent strata](ABLATIONS.json); per-cell summaries are under `artifacts/codex-p0/ablations-v2`.

| Change | Wins vs 193/256 | Paired delta (map-cluster 95% CI) | Fuel-outs vs 378 | Cells with increased fuel-outs |
|---|---:|---:|---:|---:|
| Lab and its forced dependencies off | 169 | −9.375 pp (−18.750, +1.562) | 347 | 32 |
| Active forced A3 options off | 193 | 0.000 pp (−2.734, +3.125) | 376 | 1 |
| Duo behavior off | 189 | −1.562 pp (−8.594, +6.250) | 277 | 18 |
| Tactical fight verdict search off | 175 | −7.031 pp (−12.500, −1.953) | 379 | 8 |

No arm had round-one suspensions. A lab-only change failed to compile: forced runtime, map and hybrid switches reference the namespace directly. The measured lab-off build additionally disables the required `A2_RTSW`, `A2_LADFIT`, `A2_HYB`, and `LADDER_TABLES` flags. It is a subsystem ablation, not an isolated estimate of learned weights, and regresses both v92 and x3inv by 15.625 pp. The duo switch is `NOVA_DUO=0`; changing only `NOVA_DUO_MAPS` from 1 to 0 would turn duo on for more maps, not disable it. Turning duo off gained 4.688 pp versus x3inv and lost 10.938 pp versus v92. The tactic ablation disables `APEX_TS_DECIDE`, since `APEX_TSEARCH` is already 0. It loses strength without a fuel benefit. No ablation qualifies for promotion or a ladder lock.

Run `py research/codex-ishan/ablate_dev.py prepare` in a fresh artifact directory with the exact frozen inputs, then build each project with the official CLI in release mode to its `bot.wasm` path and call the script with `run`. No holdout games were played.
