# Ladder bots (team DOOMSDAY)

Full submission sources of the heuristic bot lineage, one directory per version (`src/` is what `cambc submit` uploads).

| Version | Source | Notes |
|---|---|---|
| v48 | `C:\projects\cambridge battlecode\bot v48\danger20_engine103.zip` | heuristic, trained draft net (`A2_MLDRAFT`) and danger net (`UB_DANGER`) on |
| v50 | `C:\projects\cambridge battlecode\bot v50\bot.zip` | v48 lineage, draft net and camp net (`A2_CAMPNET`, about 3 hours of in-engine RL); no danger net |
| v51 | this repository | v50 plus the moated-island fix; submitted 2026-10-25 as bot version 51 (see `v51/CHANGES.md`) |
| v53 | this repository | frozen platform version53; see `v53/CHANGES.md` |
| v54 | this repository | frozen platform version54; coordinated economy and teleport logistics |
| v55 | this repository | submitted as platform version55 at2026-10-25 18:53:28UTC; completed camp missions, Heart camp strikes, legal mirrored drafts; evidence in `artifacts/claude_ops/V55_RELEASE.json` |
| v56 | this repository | v55 plus shop completion (`V56_SHOP_DONE`); never submitted |
| v57 | this repository | submitted as platform version 56 at 2026-10-25 21:25 UTC; v56 plus `UB_ENEMY_CAMP` 1.0 (contest the middle); evidence in `artifacts/claude_ops/V57_RELEASE.json` |
| v58 | this repository | Submitted as platform57 on2026-10-26; selected, compilation queued at last check.64.0% over672games vs v57; fuel0.999/game; both required holdouts pass; see `v58/CHANGES.md` and `artifacts/claude_ops/V58_RELEASE.json` |

Build: `cambc build bots/v51 --release --output <file>.wasm`. Local head-to-head: `tools/bot_match.py`, `artifacts/claude_ops/bench3.sh` (cached builds and verified complete runs). Compare candidates with `tools/bench_compare.py`; retain a mechanism only when its map-clustered 95% interval is above zero against its base.
