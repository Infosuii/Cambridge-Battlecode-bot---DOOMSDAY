# Team, workstreams and the old branches

## People

Contributors, by the GitHub accounts and commit names in the history.

| Person | Account / commit name | Main work |
|---|---|---|
| Rishik | `R1shik123` | Team lead. Ran the Claude Code workstream: z-plan, the multi-machine campaigns, RL environment and qualifier-week fixes |
| Om Dhande | `Infosuii` (repo owner). Agents on his machine commit as "YourUsername" | Heuristic sprint v48–v61 and repository structure on his machine, and the Codex agentic live line v108–v137 |
| Ishan Patil | `ishanp765` | v115 fuel merge, live-safety analysis (v105/v106), deep analysis |
| Tamim Atiqur | Tamim Atiqur | gigabot (gx) increments, DOOMSDAY Zero |
| Iniya | Iniya | Agent 2 neural work: the nnq4 blend and the RL experiments |
| johndoe | `johndoe123983` | Fuel-safety components and the recurrent PPO learner |

## AI agents and machines

Most code was written by AI coding agents that the team directed:

- **Claude Code**: the lead, z-plan, rl-env and qualifier-week workstreams.
- **Codex / GPT**: the agentic improvement loop on Om's workstation (20 threads, RTX 5070 Ti), and analysis.
- **Agent 2, Agent 4**: named agents from the agent-36 four-agent prompt pack.
- **Machines:** a PC, a laptop, `g3`, an RTX 5060 box, an RTX 5070 Ti box and `gmax`. They coordinated through the
  message board in [`history/agent-comms`](history/agent-comms).

## Old branches

The repository used to have 33 branches. During the cleanup, every leaf branch was **merged into `main`** (conflicting
hunks kept `main`'s side), and each tip was saved as a tag `archive/<old-branch-name>`. To see a branch exactly as it
was:

```bash
git fetch --tags
git switch --detach archive/build/z-plan        # or browse the tag on GitHub
```

| Old branch | Workstream | Merged into main | Content now under |
|---|---|---|---|
| `main` (before cleanup) | v48–v58 heuristic line, neural framework | base | everything |
| `claude/rl-env-1104` | Final development line, RL env, qualifier fixes | yes | `research/rl-env/`, `bots/rl-env/`, `bots/mainline/` |
| `research/v118-rootcause-20261109` | Codex live line, root-cause cycles | yes | `research/codex-live/` |
| `research/agentic-improvement-20261107` | Codex agentic improvement | contained in the above | `research/codex-live/` |
| `claude/v115-fuel-merge-1109` | Ishan's v115 fuel merge | yes | `bots/mainline/v115*`, `research/rl-env/` |
| `ishan/codex-20261104` | Ishan's Codex analysis | yes | `research/codex-live/codex-ishan/` |
| `johndoe/rl-learner-e3-1104` | Recurrent PPO learner | yes | `research/rl-env/jd-*` |
| `johndoe/rl-belief-design-1104` | Belief model design | contained | `research/rl-env/jd-rl-belief-1104/` |
| `johndoe/agent-coordination` | Coordination protocol and leases | yes | `archive/coordination/` |
| `johndoe/qualifier-build-prompt` | Qualifier build prompt | contained | `docs/history/prompts/`, `research/x-series/x3/` |
| `johndoe/qualifier-builder-g5070-1104` | Qualifier builder on the 5070 | contained | `bots/rl-env/jd-g5070-1104/` |
| `johndoe/qualifier-builder-g5070-resume-0715` | Qualifier builder, resumed | contained | `bots/rl-env/jd-g5070-resume-0715/` |
| `r1shik/z-plan-handover` | z-plan ladder duels and run ledger | contained | `research/x-series/x3/` |
| `build/z-plan` | Main development line, 28 Oct – 3 Nov | contained | `bots/x-series/`, `research/x-series/` |
| `build/z-plan-g3`, `-5060`, `-5070` | Campaigns on helper machines | yes | `bots/x-series/`, `docs/history/machines/` |
| `max/gigabot` | gigabot (gx) | yes | `bots/gigabot/`, `research/gigabot/` |
| `dev/botx3-team-economy-20261102` | botx3 team economy | yes | `bots/botx3/`, `research/botx3/` |
| `build/pure-algorithm-zero` | DOOMSDAY Zero | contained | `bots/doomsday-zero/`, `research/doomsday-zero/` |
| `experiment/dz-lifecycle-repair-2026-11-01` | DZ lifecycle repair | yes | `research/doomsday-zero/` |
| `experiment/dz-no-varg-draft-2026-11-01` | DZ draft without Varg | yes | `research/doomsday-zero/` |
| `agent2-neural` | Agent 2 neural bot | yes | `research/neural/agent2-neural/` |
| `agent2/v61-findings` | Agent 2 findings E56–E76 | yes | `research/neural/agent2-v61/`, `bots/neural/agent2-v61/` |
| `analysis/deep-2026-10-28` | Deep analysis of v59–v70 | yes | `research/analysis/deep-2026-10-28/` |
| `checkpoint/research-v85-2026-10-28` | Portable research checkpoint | contained | `archive/continuation/` |
| `claude/compare-fix-replay-decoder` | Replay decoder fix, v67 threshold study | contained | `tools/replay/`, `bots/mainline/v67/` |
| `lab/box` | Lab-box builds (v71–v77 variants) and generated maps | yes | `bots/mainline/`, `maps/generated/` |
| `maps/generated-suite-120` | 120-map test suite | contained | `maps/generated/` |
| `research/x1-audit-2026-11-02` | x1 replay diagnosis | yes | `research/x-series/x1-audit-2026-11-02/` |
| `comms/x1` | Multi-agent message board | yes, own history | `docs/history/agent-comms/` |
| `docs/active-work` | Pointer to the active branch | contained | `docs/history/handoffs/ACTIVE_WORK.md` |
| `ops` | v53 starter prompt | contained | `docs/history/prompts/` |

"Contained" means every commit on the branch was already part of a merged branch. Its tip is still tagged.

## Large files

Raw evidence archives (`evidence.zip` game dumps), split archive parts, the vendored `cambc.exe` and any file over
1 MB were removed from the current tree to keep checkouts small. They are **still in the git history** and in the
`archive/*` tags. The full list, with blob hashes, is
[`archive/REMOVED_FROM_TREE.tsv`](../archive/REMOVED_FROM_TREE.tsv).
