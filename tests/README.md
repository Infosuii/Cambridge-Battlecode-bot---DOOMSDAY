# Tests

| Folder | Covers |
|---|---|
| `python/` | The neural-framework package: data archives and splits, the evaluation protocol, gates and statistics, observation encoding. Run with `PYTHONPATH=neural/python python -m unittest discover -s tests/python`. |
| `cpp/` | Native checks: observation parity, runtime kernels and records, policy model and schedule. |
| `dz/` | DOOMSDAY Zero probes and conformance tests for individual mechanics: capture, dash, death, draft, vision and more. |
| `fixtures/`, `loss_cases/` | Recorded inputs and ladder loss cases used by the tests. |
