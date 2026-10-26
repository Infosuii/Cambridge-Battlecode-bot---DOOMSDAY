# Research log

Everything measured or decided about each bot version is in that version's folder. Each version folder has the same
layout:

| Path | Contents |
|---|---|
| `vNN/VNN_*.md`, `vNN/VNN_*.json` | Plans, build logs, analyses and the release record (`VNN_RELEASE.json`: source hashes, Wasm and bundle hashes, submission time). |
| `vNN/results/` | Bench outputs: per-seed text summaries plus `-bayes`, `-cluster` and `-validation` JSON from `tools/bench_bayes.py`, `tools/bench_compare.py` and `tools/check_bench_run.py`. |
| `vNN/experiments/` | Patches for experiments that were kept or are still open, relative to the previous frozen version. `tools/reproduce_v55.py` and `tools/reproduce_v58.py` rebuild them exactly. |
| `vNN/rejected/` | Diffs of ideas that lost, kept so nobody runs them again. |

| Version | What happened | Start with |
|---|---|---|
| v51 | Moated-island fix; submitted as platform 51 | `../bots/v51/CHANGES.md` |
| v52 | Sole-gem-camp rule; submitted as platform 52 | `v52/V52_PLAN.md` |
| v53 | Open-job scan hoist; submitted as platform 53. Loss and champion-life analyses | `v53/V53_LOSS_REPORT.md` |
| v54 | Crew jobs, item milestones, lead lock, teleports: +149 vs v53; submitted as platform 54 | `v54/V54_BUILD_LOG.md` |
| v55 | Completed camp missions, Heart farming strikes: +106 vs v54; submitted as platform 55 | `v55/V55_BUILD_LOG.md` |
| v56 | Shop completion; never submitted | `../bots/v56/CHANGES.md` |
| v57 | Contest the middle: +122 vs v55, +85 on the fresh holdout; submitted as platform 56. Sprint 3 loss review | `v57/V57_FRESH_MAPS.md`, `v57/V57_SPRINT3_LOSS_REVIEW.md` |
| v58 | Economy package (capture, collectors, Greed) on the Sprint 3 rules: 430/672, +153 vs v57; **submitted as platform 57** | `v58/V58_SPRINT3_RESULTS.md`, `v58/V58_RELEASE.json`, `../bots/v58/CHANGES.md` |

`early/` holds the 2026-10-24 neural-policy work: night run reports, training logs and fuel probes. `misc/` holds a
few results that belong to no single version and `SPRINT3_SDK_FACTS.json` (the Sprint 3 rule changes read from the
SDK).
