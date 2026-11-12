# Research

Every experiment, benchmark, ladder analysis and rejected idea, grouped by workstream. Reports are Markdown, and
measurements are JSON or TSV next to them.

| Folder | What's inside | Start with |
|---|---|---|
| [`versions/`](versions) | One folder per mainline version (v51–v81): plans, build logs, bench results (`results/`), kept experiments (`experiments/`) and rejected diffs (`rejected/`) | [`v58/V58_SPRINT3_RESULTS.md`](versions/v58/V58_SPRINT3_RESULTS.md) |
| [`x-series/`](x-series) | z-plan: map atlas, categories, portfolio, counter tables, anti-overfit study, ladder duels, x1 audit | [`x3/ANTI_OVERFIT.md`](x-series/x3/ANTI_OVERFIT.md), [`x3/MAP_IDEA_FINDINGS.md`](x-series/x3/MAP_IDEA_FINDINGS.md) |
| [`live-line/`](live-line) | Om's live line: the automated improvement loop, v113 integration, the v118 root-cause cycle, sw08 spawn recovery, live-safety analysis | [`v118-rootcause-20261109`](live-line/v118-rootcause-20261109) |
| [`rl-env/`](rl-env) | The RL environment and qualifier-week work, the v112 ladder diagnosis, the final hand-over, the recurrent PPO learner and belief design | [`rl_env_1104/HANDOVER_2026-11-09.md`](rl-env/rl_env_1104/HANDOVER_2026-11-09.md) |
| [`neural/`](neural) | The neural bot (nnq4 blend, RL checkpoints), findings E56–E76, the early policy-v2 behaviour-cloning runs | [`nnq4-blend/README.md`](neural/nnq4-blend/README.md) |
| [`doomsday-zero/`](doomsday-zero) | The clean-slate rewrite: plans, mechanics studies, model calibration, run results | [`dz/HANDOFF.md`](doomsday-zero/dz/HANDOFF.md) |
| [`gigabot/`](gigabot) | gigabot (gx) runs and its status reports | [`reports/FINAL_REPORT.md`](gigabot/reports/FINAL_REPORT.md) |
| [`botx3/`](botx3) | The team-economy line | [`botx3-20261102`](botx3/botx3-20261102) |
| [`analysis/`](analysis) | Studies outside any single version: top-team losses, deep game analysis, strategic audit, master plan, elite meta, maps, proxy and mimic opponents | [`top-losses-20261026`](analysis/top-losses-20261026) |

The headline results are collected in [docs/findings.md](../docs/findings.md).

Raw game-evidence archives (`evidence.zip`) were removed from the current tree to keep it small. They are still in the
git history: see [archive/REMOVED_FROM_TREE.tsv](../archive/REMOVED_FROM_TREE.tsv).
