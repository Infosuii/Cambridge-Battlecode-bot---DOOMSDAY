# Neural framework

The 24 October attempt at a bot whose important gameplay decisions are made by a neural network. A lead agent and
parallel agents (A–H, see [`archive/agents`](../archive/agents)) built it in "waves".

| Folder | Role |
|---|---|
| `python/nfs/` | The Python package: official-engine helpers (`nfs.engine.official_build`), the replay decoder, behaviour-cloning pipeline and training. |
| `bot/` | The framework's bot: the heuristic base plus a neural runtime with fuel routing, teacher capture and staged heads. |
| `schemas/`, `models/`, `configs/`, `config/` | Versioned observation schemas, model files, model and training configs. |
| `evaluation/` | The locked evaluation protocol (`protocol.json` with `.lock` hashes), schedules, map partitions and results. |
| `references/` | The frozen reference bots and builds the protocol compares against. |
| `training/` | The v50 camp-network PPO run (321 parameters, about 3 hours). |

**Outcome:** behaviour cloning on 7.3M top-team decisions trained a policy that scored 0 gems in real games, and the
project returned to the heuristic bot. Small networks running *beside* the heuristic (the draft net, the camp net, and
later Agent 2's nnq4 blend) were the neural parts that worked. See [docs/findings.md §6](../docs/findings.md).

The tests for this package are in [`tests/python`](../tests/python) and [`tests/cpp`](../tests/cpp). Paths inside
the code still refer to the pre-cleanup layout (`python/`, `bot/` at the repository root).
