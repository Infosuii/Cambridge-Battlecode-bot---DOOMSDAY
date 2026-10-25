# Ladder bots (team DOOMSDAY)

Full submission sources of the heuristic bot lineage, one directory per version (`src/` is what `cambc submit` uploads).

| Version | Source | Notes |
|---|---|---|
| v48 | `C:\projects\cambridge battlecode\bot v48\danger20_engine103.zip` | heuristic, trained draft net (`A2_MLDRAFT`) and danger net (`UB_DANGER`) on |
| v50 | `C:\projects\cambridge battlecode\bot v50\bot.zip` | v48 lineage, draft net and camp net (`A2_CAMPNET`, about 3 hours of in-engine RL); no danger net |
| v51 | this repository | v50 plus the moated-island fix; submitted 2026-10-25 as bot version 51 (see `v51/CHANGES.md`) |

Build: `cambc build bots/v51 --release --output <file>.wasm`. Local head-to-head: `tools/bot_match.py`, `artifacts/claude_ops/bench28.sh`.
