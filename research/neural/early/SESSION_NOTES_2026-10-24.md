# Claude session notes — 2026-10-24 23:40 (read-only pre-flight, no commands run)

Written by a cloud Claude session that had file access to this folder but no shell. Nothing was executed and nothing in the repository was changed apart from adding this file. Pick up the work from here in a Claude Code session that has terminal access.

## Verified by reading files

- Workspace `C:\projects\cambridge battlecode\work\neural-full-stack`, `.git/HEAD` -> `refs/heads/main` = `5f8ecc3c5f4318c815d12082bb3eb9f63f7002e9`. This matches the reference commit `5f8ecc3`. Uncommitted changes were NOT checked (that needs `git status`).
- The four handoff docs were read in full: HANDOFF.md, OPERATIONS_HANDOFF.md, STATUS.md, DEEPSEEK_TRAINING_PROMPT.md. TRAINING_LATER.md and ARCHITECTURE.md were also read.
- `config/paths.json`:
  - python = `C:/projects/cambridge battlecode/work/neural-gameplay/.venv/Scripts/python.exe`
  - cli = `C:/Users/omdha/Documents/Codex/2026-10-22/what/work/cambc.exe`
  - maps = `.../arena/maps`
  - expected: cambc 3.0.5, engine 1.0.3, fuel 100000
  - `historical` still points at the 21-Oct archives, not the 23-Oct folder.
- CUDA has NOT been re-verified this session. The previous evidence (RTX 5070 Ti Laptop, torch 2.11.0+cu128) is in `evaluation/results/operations_verified.json`.

## Match summaries 23102026 — what is known

- The folder holds 10 files, `summaries-2026-10-23-part1..10.zip`, about 824–829 MB each (about 8.3 GB in total). None were opened: each is over the 400 MB cloud transfer limit.
- The existing tooling (`python/nfs/data/archives.py`) defines the format. Members are `<kind>_<match>_<teamA>_vs_<teamB>.camstat` files, converted with `cambc summary`.
- A converted summary (see `data/audit_samples/*.json`) contains:
  - match metadata (engine version, seed, map hash, outcome, rounds)
  - roster and draft
  - per-champion end metrics
  - team and champion metric timelines
  - events
  - heatmaps
  - diagnostics
- It contains NO per-turn observations, NO legal-action sets, NO chosen actions and NO behaviour logits.
- Consequence: these summaries cannot produce ROLE-head PPO rows. `policy_train.prepare` needs NFS2 decision records from our own pinned export, and `preflight` requires exact behaviour logits/logp. Imitation mode also refuses, because there are no teacher labels. Converting them would mean fabricating actions, which is forbidden.
- Legitimate uses of the summaries:
  - observational draft/outcome analysis (`draft_observational_records`, `train-value --draft`)
  - opponent and meta statistics
  - possibly a future outcome/value model
- The audit still to run on the laptop should cover:
  - a central-directory pass over all 10 zips (member counts, kinds, duplicate match IDs within and across parts, and overlap with the 21-Oct archives)
  - a bounded `cambc summary` conversion sample per part, giving engine version, eligibility via `archives.classify` and a top-level key census confirming there are no action fields
- The audit can reuse `archives.build_index(...)`, but it must write to a NEW directory (e.g. `artifacts/datasets/summaries-23102026-audit/`).
- Do NOT use `tools/nfs.py index-archives` as is. It reads `paths.json['historical']` and overwrites `data/manifests/archive_index_v1.json` and `data/archive_sample_v1/`.

## First bounded cycle — exact recipe (OPERATIONS_HANDOFF.md), not yet run

1. Two collections with `tools/check_policy_v2.py --profile direct_sample_record --record-head role`, model `models/policy_v2_untrained`:
   - seeds 20261025 and 20261026
   - map 00rows, sides A B
   - opponents original v47 first-hour
   - 12 games in total
2. `policy_train.py prepare`, then `preflight`. Gates: at least 16 train and 4 validation eligible role rows, disjoint groups, exact logit parity.
3. `policy_train.py fit --head role --mode ppo --device cuda --minutes 5 --epochs 4 --evaluation-config configs/evaluation/policy_v2_regular.json --i-authorize-training`.

Notes from reading `python/nfs/policy/training.py` and `operations.py`:

- `fit` already freezes the encoder and other heads, enforces KL ≤ 0.015 and entropy ≥ 0.05, and checkpoints every epoch.
- In-fit evaluation runs every 2 epochs, at most twice. Each run is 8 games on 00collision and 00contest (selection maps) and is capped at min(120 s, time left before the 5-minute deadline). A timeout ends fit with `stop='evaluation_error'`. Expect this to be tight.
- Comparison games use the argmax `direct_evaluation` profile and are deterministic for a fixed wasm pair, map and side. Repeating the same map/side adds no information, so widen the evaluation across maps instead.
- `compare` allows up to 24 games: 2 opponents × 6 selection maps × 2 sides. Final-partition maps are refused.
- Selection maps: 00collision, 00contest, 00elkring, 00fragment, 00lost-world, 00quadrants, 01boss-battle, 01concentrated-wealth, 01corridors, 01gold-rush.
- Suggested post-fit evaluation, all on the same 6 selection maps:
  - untrained vs heuristic-v1, which is the starting point
  - trained export vs untrained plus heuristic-v1

## Two-hour session (section 13): one structural conflict to raise with the user

- `fit` hard-limits a run to 30 minutes and 4 epochs.
- PPO data must be on-policy: a new cycle must collect fresh games from the exact new export. Reusing old data with changed weights is rejected.
- So "2 hours of training" means repeated collect -> prepare -> preflight -> fit -> compare cycles driven by a supervisor. It cannot be one long fit.
- Data collection is CPU/engine-bound (cambc games), and the role head is tiny (a compact 1056-parameter model). GPU utilisation of 85–95% is not achievable without changing the design. Report this honestly rather than padding GPU load.
