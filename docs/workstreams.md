# Team, workstreams and the old branches

## Team

| Person | GitHub | Main work |
|---|---|---|
| **Om Dhande** | [`Infosuii`](https://github.com/Infosuii) | **Team lead.** The heuristic ladder sprint v48–v61, repository structure and release process, and the live line v108–v137 (retuned network weights, root-cause cycles) |
| Rishik | [`R1shik123`](https://github.com/R1shik123) | z-plan and the multi-machine campaigns, the RL environment, qualifier-week fixes (v114, v116, v137, v138) |
| Ishan Patil | [`ishanp765`](https://github.com/ishanp765) | The v115 fuel merge, live-safety analysis of v105/v106, deep game analysis |
| Iniya | | The nnq4 neural blend and its RL experiments |

## Machines

Campaigns ran in parallel on a PC, a laptop, `g3`, an RTX 5060 box, an RTX 5070 Ti workstation (20 threads) and
`gmax`. They coordinated through a git message board with jobs, leases and heartbeats:
[`history/team-comms`](history/team-comms).

## Old branches

The repository used to have 33 branches. During the cleanup, every branch was **merged into `main`** (where both sides
had changed a file, `main`'s version was kept), and each tip was saved as a tag `archive/<old-branch-name>`. To see a
branch exactly as it was:

```bash
git fetch --tags
git switch --detach archive/build/z-plan        # or browse the tag on GitHub
```

| Old branch | Line of work | Merged | Content now under |
|---|---|---|---|
| `main` (before cleanup) | v48–v58 heuristic line, neural framework | base | everything |
| `claude/rl-env-1104` | Final development line, RL environment, qualifier fixes | yes | `research/rl-env/`, `bots/rl-env/`, `bots/mainline/` |
| `research/v118-rootcause-20261109` | Live line, root-cause cycles | yes | `research/live-line/` |
| `research/agentic-improvement-20261107` | Live line, automated improvement loop | contained | `research/live-line/` |
| `claude/v115-fuel-merge-1109` | v115 fuel merge | yes | `bots/mainline/v115*`, `research/rl-env/` |
| `ishan/codex-20261104` | v105/v106 safety analysis | yes | `research/live-line/live-analysis/` |
| `johndoe/rl-learner-e3-1104` | Recurrent PPO learner | yes | `research/rl-env/` |
| `johndoe/rl-belief-design-1104` | Belief model design | contained | `research/rl-env/belief-design-1104/` |
| `johndoe/agent-coordination` | Coordination protocol and leases | yes | `archive/coordination/` |
| `johndoe/qualifier-build-prompt` | Qualifier build plan | contained | `docs/history/prompts/`, `research/x-series/x3/` |
| `johndoe/qualifier-builder-g5070-1104` | Qualifier builder on the 5070 | contained | `bots/rl-env/qualifier-g5070-1104/` |
| `johndoe/qualifier-builder-g5070-resume-0715` | Qualifier builder, resumed | contained | `bots/rl-env/qualifier-g5070-resume/` |
| `r1shik/z-plan-handover` | z-plan ladder duels and run ledger | contained | `research/x-series/x3/` |
| `build/z-plan` | Main development line, 28 Oct – 3 Nov | contained | `bots/x-series/`, `research/x-series/` |
| `build/z-plan-g3`, `-5060`, `-5070` | Campaigns on the helper machines | yes | `bots/x-series/`, `docs/history/machines/` |
| `max/gigabot` | gigabot (gx) line | yes | `bots/gigabot/`, `research/gigabot/` |
| `dev/botx3-team-economy-20261102` | botx3 team economy | yes | `bots/botx3/`, `research/botx3/` |
| `build/pure-algorithm-zero` | DOOMSDAY Zero | contained | `bots/doomsday-zero/`, `research/doomsday-zero/` |
| `experiment/dz-lifecycle-repair-2026-11-01` | DZ lifecycle repair | yes | `research/doomsday-zero/` |
| `experiment/dz-no-varg-draft-2026-11-01` | DZ draft without Varg | yes | `research/doomsday-zero/` |
| `agent2-neural` | nnq4 neural blend | yes | `research/neural/nnq4-blend/` |
| `agent2/v61-findings` | Neural findings E56–E76 | yes | `research/neural/v61-findings/`, `bots/neural/nn-v61/` |
| `analysis/deep-2026-10-28` | Deep analysis of v59–v70 | yes | `research/analysis/deep-2026-10-28/` |
| `checkpoint/research-v85-2026-10-28` | Portable research checkpoint | contained | `archive/continuation/` |
| `claude/compare-fix-replay-decoder` | Replay decoder fix, v67 threshold study | contained | `tools/replay/`, `bots/mainline/v67/` |
| `lab/box` | Lab-box builds (v71–v77 variants) and generated maps | yes | `bots/mainline/`, `maps/generated/` |
| `maps/generated-suite-120` | 120-map test suite | contained | `maps/generated/` |
| `research/x1-audit-2026-11-02` | x1 replay diagnosis | yes | `research/x-series/x1-audit-2026-11-02/` |
| `comms/x1` | Team message board | yes, with its own history | `docs/history/team-comms/` |
| `docs/active-work` | Pointer to the active branch | contained | `docs/history/handoffs/ACTIVE_WORK.md` |
| `ops` | v53 starter prompt | contained | `docs/history/prompts/` |

"Contained" means every commit on the branch was already part of a merged branch. Its tip is still tagged.

## Large files

Raw evidence archives (`evidence.zip` game dumps), split archive parts, the vendored `cambc.exe` and any file over
1 MB were removed from the current tree to keep checkouts small. They are **still in the git history** and in the
`archive/*` tags. The full list, with blob hashes, is
[`archive/REMOVED_FROM_TREE.tsv`](../archive/REMOVED_FROM_TREE.tsv).
