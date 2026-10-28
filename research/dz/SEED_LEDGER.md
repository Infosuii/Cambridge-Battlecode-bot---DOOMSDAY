# DZ seed and experiment ledger

All experiments must use a unique output directory and record source/Wasm, map and CLI hashes.
Local engine execution is deterministic; seed labels are not independent samples unless source
actually consumes that seed. DZ v0 has no randomness. Do not count duplicate identities twice.

The registry was created before experiments. Entries below record actual use.

| Run | Date | Seed / identity | Scope | Purpose |
|---|---|---|---|---|
| dz-v0-smoke-01 | 2026-10-28 | deterministic; no seed parameter | 00collision vs idle81, side A | first full release game |
| dz-ct-01 | 2026-10-28 | deterministic; Wasm 676bc03cc956 | 4 cells; idle81 | conformance; trace=False |
| dz-trace-01 | 2026-10-28 | deterministic; Wasm e9aa331f30fb | 10 cells; idle81 | smoke; trace=True |
| dz-ct-02 | 2026-10-28 | deterministic; Wasm 676bc03cc956 | 4 cells; idle81 | conformance; trace=False |
| dz-trace-02 | 2026-10-28 | deterministic; Wasm fe242af2bb7c | 10 cells; idle81 | smoke; trace=True |
| dz-trace-03 | 2026-10-28 | deterministic; Wasm b4c34e9b38e2 | 4 cells; idle81 | smoke; trace=True |
| dz-trace-04 | 2026-10-28 | deterministic; Wasm 9d23be963159 | 2 cells; idle81 | smoke; trace=True |
| dz-pool-idle-01 | 2026-10-28 | deterministic; Wasm b08755a2c5c3 | 140 cells; idle81 | smoke; trace=False |
| dz-ct-03 | 2026-10-28 | deterministic; Wasm fa04524d75dd | 4 cells; idle81 | conformance; trace=False |
| dz-trace-05 | 2026-10-28 | deterministic; Wasm c4feac8695f2 | 4 cells; idle81 | smoke; trace=True |
| dz-trace-06 | 2026-10-28 | deterministic; Wasm 721042fbc20e | 2 cells; idle81 | smoke; trace=True |
| dz-pool-idle-02 | 2026-10-28 | deterministic; Wasm c5486461a5f8 | 140 cells; idle81 | smoke; trace=False |
| dz-pool-v65-01 | 2026-10-28 | deterministic; Wasm c5486461a5f8 | 140 cells; v65 | smoke; trace=False |
| dz-v76-screen-01 | 2026-10-28 | deterministic; Wasm c5486461a5f8 | 12 cells; v76 | smoke; trace=False |
| dz-trace-current-v65 | 2026-10-28 | deterministic; Wasm 2debd5aae12d | 6 cells; v65 | smoke; trace=True |
