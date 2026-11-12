# Phase 0 tools

In `C:/dd/codex-20261104`: Python via `py`, Windows PowerShell, Git Bash at `C:/Program Files/Git/bin/bash.exe`. `py tools/configure_dev.py --cli tools/vendor/cambc.exe --python <python.exe> --native-cxx <python.exe>` generated the local paths/env; native-cxx is a placeholder and native C++ tasks are unavailable. Set `PYTHONPATH=<root>/python`, `PYTHONDONTWRITEBYTECODE=1`, local `TMP/TEMP`, and `NFS_REPLAY_ENGINE=2.0.0`. Avoid changing global settings.

| Tool | Check and limitation |
|---|---|
| Official CLI | 4.0.0; signed-in read-only submissions, ladder, matches, group show and quota succeeded. `build --release`, `run --release --json --statistics`, `view` succeeded. `match-groups create --help` confirms `--source-group`; never invoke create without lock. |
| `tools/dz.py smoke` | Help works; a real prebuilt smoke failed because this branch lacks `research/dz/SEED_LEDGER.md` (tracked on handover). Used CLI native statistics for the measured smoke and pool baseline; archived ledger untouched. |
| `tools/x1_gate.sh`, `tools/bench3.sh` | Git Bash syntax passed. Full historical gates not run. `bench_provenance.py` exposes functions, not a CLI; reject mixed fingerprint or engine provenance. |
| `tools/jd_g5070-1104/jdrun.py` | Pinned branch copy help passed; real runs need the correct worktree layout, frozen opponents and JD_EVAL. Historical output uses explicit candidate-then-base compact score cells. Never launch background/coordination code from historical work. |
| `tools/jd_g5070_resume_0715/reproduce.py` | Requires original package checksum and historical aliases. Reproduced equivalent official builds from earlier locally verified source archive twice; switches-off is identical to v92. |
| `tools/replay/ladder_duel.py`, `duel_pipeline.py` | Help passed. Plan C base group is still readable by `match-groups show`. Existing pipeline must be audited before live use; a successful read does not prove the platform still accepts it as pin source. |
| `tools/ladder/losses_recent.py`, `archetypes.py` | Help passed. `summary_profile.py` and `loss_study.py` fail importing missing `data/ladder/char_ids.json` on this checkout. |
| `tools/replay/*.mjs` | Syntax passed for winner_profile, death_context, camp_clear, contact_cohesion, focus_fire, hurt_contact, home_trips, map_state, decode_replays, crystal_divergence. `decode_replays.mjs` takes `--out` plus inputs, no standard help. `race_snapshot.mjs` missing. |
| Economy gap scripts | `early_fight.py`, `collect_gap.py`, `camp_control.py` present, no argparse. Inspect inputs and output paths before running so frozen evidence is not overwritten. |
| `tools/mapatlas/` | collect, categorise and portfolio_eval help passed. behaviour_check expects named DZ replay runs and its historical `replay_compare` helper. |
| Other | `x3_counter.py robust --help` passed. `tools/replay/ladder_ab.py` help passed. `mk_v92j.py` and `tools/platform_fetch.py` not found on this branch. `check_teacher_exact.py` blocked by missing torch; RL is out of this track. |

Read-only snapshot command arguments, saved in `artifacts/codex-p0` with args joined by hyphens, plus `.json`:

- `submissions list --json`
- `submissions list --before 86 --json`
- `ladder --page 1 --limit 100 --json`
- `matches list --team me --kind ranked --limit 100 --json`
- `matches list --team me --kind unranked --limit 100 --json`

Historical source pin: `r1shik/z-plan-handover` 33c16873, `johndoe/qualifier-builder-g5070-1104` 12c1804b, `johndoe/qualifier-builder-g5070-resume-0715` cb8d0105, `agent2-neural` 548694e1. Files under docs/codex and new research paths contain compact evidence only; no replay, ZIP, token, checkpoint or account settings are committed.
