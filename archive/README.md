# Archive

Finished or retired material, kept for the record. Nothing current depends on it.

| Path | What it was |
|---|---|
| [`battlecode-agent-36/`](battlecode-agent-36) | The predecessor project (19–21 Oct): bots v34 and v36, the four-agent prompt pack, and Windows integration checks. Merged in with its full history. |
| [`agents/`](agents) | Workspaces of the parallel agents (A–H) that built the neural framework on 24 Oct: reports, contracts, probes, patches. |
| [`release-2026-10-24-draft/`](release-2026-10-24-draft) | First, superseded build of the untrained neural-framework release. |
| [`artifacts/`](artifacts) | Frozen builds (`baselines/heuristic-v1`, `release/`), source bundles and a small dataset. |
| [`continuation/`](continuation) | The portable research checkpoint of 28 Oct. Its split archive parts are only in history. |
| [`handoff-botx3/`](handoff-botx3), [`handoff-botx3-latest/`](handoff-botx3-latest) | Continuation packages from when botx3 was paused (3 Nov). |
| [`coordination/`](coordination) | The availability and lease protocol the agents used to share machines. |
| [`REMOVED_FROM_TREE.tsv`](REMOVED_FROM_TREE.tsv) | Every file removed from the tree in the November cleanup (path, size, blob hash). All of them remain in git history. |

To recover a removed file: `git log --all -- <path>` finds a commit that has it, then
`git show <commit>:<path> > file` restores it. Alternatively, check out the matching `archive/<branch>` tag.
