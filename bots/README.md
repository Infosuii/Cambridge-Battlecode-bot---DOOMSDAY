# Ladder bots (team DOOMSDAY)

Full submission sources of the heuristic bot lineage, one directory per version (`src/` is what `cambc submit` uploads).

| Version | Source | Notes |
|---|---|---|
| v48 | `C:\projects\cambridge battlecode\bot v48\danger20_engine103.zip` | heuristic, trained draft net (`A2_MLDRAFT`) and danger net (`UB_DANGER`) on |
| v50 | `C:\projects\cambridge battlecode\bot v50\bot.zip` | v48 lineage, draft net and camp net (`A2_CAMPNET`, about 3 hours of in-engine RL); no danger net |
| v51 | this repository | v50 plus the moated-island fix; submitted 2026-10-25 as bot version 51 (see `v51/CHANGES.md`) |
| v53 | this repository | frozen platform version53; see `v53/CHANGES.md` |
| v54 | this repository | frozen platform version54; coordinated economy and teleport logistics |
| v55 | this repository | submitted as platform version55 at2026-10-25 18:53:28UTC; completed camp missions, Heart camp strikes, legal mirrored drafts; evidence in `research/v55/V55_RELEASE.json` |
| v56 | this repository | v55 plus shop completion (`V56_SHOP_DONE`); never submitted |
| v57 | this repository | submitted as platform version 56 at 2026-10-25 21:25 UTC; v56 plus `UB_ENEMY_CAMP` 1.0 (contest the middle); evidence in `research/v57/V57_RELEASE.json` |
| v58 | this repository | Submitted as platform57 on2026-10-26; selected, compilation queued at last check.64.0% over672games vs v57; fuel0.999/game; both required holdouts pass; see `v58/CHANGES.md` and `research/v58/V58_RELEASE.json` |
| proxy | this repository | not a ladder bot: local stand-in for the top 12 (their per-map drafts, item milestones, recall trick, fitted fight knobs on v65's code); see `proxy/CHANGES.md` and `research/proxy/README.md` |
| mimic | this repository | new executor with replay-trained decisions; research only, never submitted. v9 loses 240/240 to v65, but matches 14/15 existing ladder-arm orderings; see `mimic/CHANGES.md` and `research/mimic/README.md` for limits |

Build: `cambc build bots/v51 --release --output <file>.wasm`. Local head-to-head: `tools/bot_match.py`, `tools/bench3.sh` (cached builds and verified complete runs). Compare candidates with `tools/bench_compare.py`; retain a mechanism only when its map-clustered 95% interval is above zero against its base.
