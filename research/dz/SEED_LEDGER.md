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
| dz-ct11-cadence-01 | 2026-10-28 | deterministic; Wasm 82a257324d15 | 4 cells; idle81 | conformance; trace=False |
| dz-ct11-cadence-02 | 2026-10-28 | deterministic; Wasm 2f019369d4af | 4 cells; idle81 | conformance; trace=False |
| dz-ct11-asserted-03 | 2026-10-28 | deterministic; Wasm 2f019369d4af | 4 cells; idle81 | conformance; trace=False |
| dz-kernel-02-idle | 2026-10-28 | deterministic; Wasm 28cf25593b87 | 140 cells; idle81 | smoke; trace=False |
| dz-ct7-actions-01 | 2026-10-28 | deterministic; Wasm 725767d60fb2 | 4 cells; idle81 | conformance; trace=False |
| dz-ct11-asserted-04 | 2026-10-28 | deterministic; Wasm 82117bb4da41 | 4 cells; idle81 | conformance; trace=False |
| dz-fundamentals-02-idle | 2026-10-28 | deterministic; Wasm a627767e243e | 140 cells; idle81 | smoke; trace=False |
| dz-fundamentals-02-v65 | 2026-10-28 | deterministic; Wasm a627767e243e | 140 cells; v65 | smoke; trace=False |
| dz-camp-budget-control | 2026-10-28 | deterministic; Wasm 43ecdede5d96 | 140 cells; idle81 | smoke; trace=False |
| dz-camp-budget-on | 2026-10-28 | deterministic; Wasm 2c7894c3ea86 | 140 cells; idle81 | smoke; trace=False |
| dz-camp-budget-02-focused | 2026-10-28 | deterministic; Wasm 71c4af33c2a9 | 8 cells; idle81 | smoke; trace=False |
| dz-ct16-channels-01 | 2026-10-28 | deterministic; Wasm a20b5574f330 | 4 cells; idle81 | conformance; trace=False |
| dz-ct8-visibility-01 | 2026-10-28 | deterministic; Wasm a9cce4aaa7ce | 4 cells; idle81 | conformance; trace=False |
| dz-camp-budget-02-control | 2026-10-28 | deterministic; Wasm b97ec6398795 | 140 cells; idle81 | smoke; trace=False |
| dz-camp-budget-02-on | 2026-10-28 | deterministic; Wasm 71c4af33c2a9 | 140 cells; idle81 | smoke; trace=False |
| dz-ct24-capture-01 | 2026-10-29 | deterministic; Wasm 14ad9780fa5f | 4 cells; idle81 | conformance; trace=False |
| dz-ct8-visibility-02 | 2026-10-29 | deterministic; Wasm e707c70705c1 | 4 cells; idle81 | conformance; trace=False |
| dz-ct16-channels-02 | 2026-10-29 | deterministic; Wasm d969cb744d5a | 4 cells; idle81 | conformance; trace=False |
| dz-ct16-channels-03 | 2026-10-29 | deterministic; Wasm b06455736fb1 | 4 cells; idle81 | conformance; trace=False |
| dz-camp-budget-03-v65-control | 2026-10-29 | deterministic; Wasm 324f017920ef | 140 cells; v65 | smoke; trace=False |
| dz-camp-budget-03-v65-on | 2026-10-29 | deterministic; Wasm d8b97b0730a0 | 140 cells; v65 | smoke; trace=False |
| dz-camp-budget-04-runtime | 2026-10-29 | deterministic; Wasm 270db465d29c | 6 cells; v65 | smoke; trace=True |
| dz-ct24-capture-02 | 2026-10-29 | deterministic; Wasm 14ad9780fa5f | 4 cells; idle81 | conformance; trace=False |
| dz-ct26-reset-01 | 2026-10-29 | deterministic; Wasm 949c0755cf27 | 4 cells; idle81 | conformance; trace=False |
| dz-ct24-capture-03 | 2026-10-29 | deterministic; Wasm 9ed9e28f827a | 4 cells; idle81 | conformance; trace=False |
| dz-ct24-capture-04 | 2026-10-29 | deterministic; Wasm 9de620ea3d8c | 4 cells; idle81 | conformance; trace=False |
| dz-fundamentals-03-idle | 2026-10-29 | deterministic; Wasm 4c9fa7d0df8e | 140 cells; idle81 | smoke; trace=False |
| dz-fundamentals-04-focused | 2026-10-29 | deterministic; Wasm c3e671c09c44 | 10 cells; v65 | smoke; trace=True |
| dz-ct24-capture-05 | 2026-10-29 | deterministic; Wasm e0358761e417 | 6 cells; idle81 | conformance; trace=False |
| dz-ct24-capture-06 | 2026-10-29 | deterministic; Wasm a26d1e5f0eb1 | 6 cells; idle81 | conformance; trace=False |
| dz-fundamentals-05-idle | 2026-10-29 | deterministic; Wasm caaafee0b576 | 140 cells; idle81 | smoke; trace=False |
| dz-fundamentals-05-trace | 2026-10-29 | deterministic; Wasm 47a130cae941 | 10 cells; v65 | smoke; trace=True |
| dz-fundamentals-06-trace | 2026-10-29 | deterministic; Wasm e17de1486745 | 6 cells; v65 | smoke; trace=True |
| dz-recall-regression-01 | 2026-10-29 | deterministic; Wasm 18c4e89bf6c4 | 8 cells; idle81 | smoke; trace=True |
| dz-capture-regression-01 | 2026-10-29 | deterministic; Wasm 320a0ce24679 | 2 cells; idle81 | smoke; trace=True |
| dz-capture-regression-02 | 2026-10-29 | deterministic; Wasm 6b2bebf85aad | 8 cells; idle81 | smoke; trace=True |
| dz-fundamentals-07-idle-control | 2026-10-29 | deterministic; Wasm 8696597f8281 | 140 cells; idle81 | smoke; trace=False |
| dz-fundamentals-07-idle-safety | 2026-10-29 | deterministic; Wasm 386280f3b66c | 140 cells; idle81 | smoke; trace=False |
| dz-ct27-fingerprint-01 | 2026-10-29 | deterministic; Wasm 80d530c16a9c | 4 cells; idle81 | conformance; trace=False |
| dz-fundamentals-07-v65-control | 2026-10-29 | deterministic; Wasm 8696597f8281 | 140 cells; v65 | smoke; trace=False |
| dz-fundamentals-07-v65-safety | 2026-10-29 | deterministic; Wasm 386280f3b66c | 140 cells; v65 | smoke; trace=False |
| dz-ct27-fingerprint-02 | 2026-10-29 | deterministic; Wasm 3e14ac65a383 | 4 cells; idle81 | conformance; trace=False |
| dz-ct27-fingerprint-03 | 2026-10-29 | deterministic; Wasm 3e14ac65a383 | 4 cells; idle81 | conformance; trace=False |
| dz-fundamentals-08-v65-trace | 2026-10-29 | deterministic; Wasm 6b2bebf85aad | 140 cells; v65 | smoke; trace=True |
