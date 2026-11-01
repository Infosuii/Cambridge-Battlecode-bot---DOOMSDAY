# 0001: read the whole repository for context (addendum to your starting prompt)

Before or alongside J001, read through the whole GitHub repository, every branch, for context. Read-only: check
other branches out in separate worktrees (`git worktree add ../ctx-<name> origin/<branch>`) or read with
`git show origin/<branch>:<path>`; never commit to them. What each branch holds:

| Branch | What is there |
|---|---|
| `build/z-plan` | **our line**: bots/x1, x2 (v88), v86h, v81hl and seed builds, tools/dz.py, research/x1 (plan, retry queue, synthesis, paper notes), research/dz (DZ bot history, runs), docs/x1_5060 |
| `main` | team baseline and the top-team replay study |
| `lab/box` | v72-v77 lab line: the plan-switch hook (v76p), tools/lab/branch_farm.py, branch_prefix.py, plan_model.py, research/v72 status. **Reuse these for the branch farm.** |
| `agent2/v61-findings` | Agent 2's E72-E76 findings and platform study tools (Agent 2 later built v86h / v88) |
| `analysis/deep-2026-10-28` | deep analysis of v70 games (recall timer conflict) |
| `build/pure-algorithm-zero` | the DZ (pure-algorithm) bot line |
| `experiment/dz-lifecycle-repair-2026-11-01`, `experiment/dz-no-varg-draft-2026-11-01` | DZ experiments by other agents: read only, never touch |
| `checkpoint/research-v85-2026-10-28` | v85 research checkpoint |
| `claude/compare-fix-replay-decoder` | replay decoder fixes, v67 thresholds |
| `maps/generated-suite-120` | the 120-map suite (70 official + 50 generated; tools/mapgen) |
| `ops` | earlier job-runner and starter prompts |

Also read every `README*`, `HANDOFF*`, `HANDOVER*`, `STATUS*`, `FINDINGS*` and `research/**/*.md` you find. Note in
g5060/STATUS.md anything that changes how you run jobs (for example an existing tool that does a job better).
Ladder matches against other teams are run from the PC only (its CLI login); you never log in.
