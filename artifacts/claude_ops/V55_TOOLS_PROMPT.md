# Task for GPT: switch to the new benchmark tools and retire the old ones

Repository `Infosuii/neural-networkk-battlecode`, branch `claude/compare-fix-replay-decoder`, checkout
`C:\projects\cambridge battlecode\work\neural-full-stack`. Pull first (`git pull --ff-only`); the new tools are in
commit `bcb8944`. Keep `config/paths.json` and your uncommitted v55 work untouched by this housekeeping.

## 1. Finish what is running, then switch

Do not edit `artifacts/claude_ops/bench2.sh` or `bench28.sh` while any bench is running: bash reads scripts
incrementally, and editing a running script corrupts that run. Let current runs finish. From then on start every
new bench with `bench3.sh`.

## 2. The new tools

**`artifacts/claude_ops/bench3.sh`** replaces `bench2.sh`. Same arguments, same environment variables
(`MAPS_OVERRIDE`, `HOLDOUT`, `PY`) and the same output layout (`<prefix>-seed<s>-s<k>/summary.json`,
`<prefix>-seed<s>.txt`), so every analysis tool works on it unchanged.
```bash
bash artifacts/claude_ops/bench3.sh "$R/bots/v55" "$R/bots/v54" "$R/artifacts/evaluations/<name>" 1 2 3 4 5 6 7 8 9 10 11 12
```
* Builds each (source tree, seed) once and caches it by content hash in `artifacts/tmp/wasm-cache`, so frozen
  opponents (v53, v54) and unchanged candidates are never rebuilt.
* Checks that every shard has 2 games per map, reruns failed shards (`RETRIES`, default 2) and **exits 1 with an
  INCOMPLETE message** instead of quietly reporting fewer games. Treat a non-zero exit as a failed run.
* Verified: identical per-game results to `bench2.sh`, so results from the two scripts can be paired.

**`tools/bench_compare.py`** replaces `tools/bench_paired.py`.
```bash
python tools/bench_compare.py <prefix A> <prefix B> [--maps a,b] [--json out.json]   # A - B on identical games
python tools/bench_compare.py <prefix>                                                # one run vs its opponent
```
* Pairs only identical (map, side, seed) games.
* The 95% interval is a **map-cluster bootstrap** (games on one map are strongly correlated). The naive per-game
  interval is printed only for contrast and must not be used for decisions.
* The verdict line says "better", "worse" or "not distinguishable from zero". Per-map deltas beyond the measured
  ±100-gem inert-change noise band are flagged.
* Calibration: v54 vs v53 over 12 seeds is +187.1 [+116, +266] (clearly better); the earlier teleport step
  (+38.5) and the 50%-readiness variant (+0.2) are not distinguishable from zero.

## 3. Rules from now on

* Report every candidate comparison with `bench_compare.py` intervals; call a mechanism retained only when its
  interval is above zero against the base it modifies (or explain why a neutral-but-necessary change is kept).
* A run that exits non-zero, has faults, or has fewer than 2 × maps × seeds games is not evidence.
* Keep using `tools/bench_maps.py` (per-side table), `tools/bench_deaths.py`, `tools/replay/ledger_bench.py` and
  the ladder pipeline (`tools/replay/run_life_tools.sh`, `life_report.py`); they read bench3 output unchanged.

## 4. Retire the old tools (after your runs have finished)

1. Check nothing still needs them: `git grep -n "bench2.sh\|bench28.sh\|bench_paired"`.
2. Update every live reference to the new tools: `ops/SETUP.md` (smoke test and "Where things are"), `ops/HANDOFF.md`
   §4 (gate commands), `bots/README.md`, `artifacts/claude_ops/V55_GPT_PROMPT.md` §6, the docstrings of
   `tools/bench_maps.py`, and the comment in `bench3.sh`. Leave historical records (old CHANGES files, build logs,
   `ops/PROMPT_V53.md`, `V54_CLAUDE_PROMPT.md`) as they are: they describe what was run at the time.
3. Delete with `git rm`: `artifacts/claude_ops/bench2.sh`, `artifacts/claude_ops/bench28.sh`,
   `tools/bench_paired.py`. Keep `tools/bench_summary.py` (bench3 uses it).
4. Smoke-test after the deletion: `MAPS_OVERRIDE="00rows" bash artifacts/claude_ops/bench3.sh "$R/bots/v54"
   "$R/bots/v53" "$R/artifacts/evaluations/smoke-b3" 1` must exit 0 with 2 games, and
   `python tools/bench_compare.py "$R/artifacts/evaluations/smoke-b3"` must print a record.
5. Commit with a message that lists what was removed and what replaces it, then push. Do not touch frozen bots,
   raw replays or credentials.

## 5. Then continue v55

Resume the v55 work in `artifacts/claude_ops/V55_GPT_PROMPT.md`, re-evaluating anything previously judged with the
naive standard error from `bench_paired.py` (for example E2's +7.3) with `bench_compare.py` before building on it.
