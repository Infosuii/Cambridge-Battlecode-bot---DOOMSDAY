# Source review

| Ref | Evidence | Decision |
| --- | --- | --- |
| `build/z-plan` at `9c1bbde` | x3 and x3mf differ only in the X1_MAPFIT default. x3 reproduction confirmed. | Keep x3 as the byte-identity control and x3mf as the strength baseline. |
| `build/z-plan-5060` at `cbd9dd1` | J022 mapfit is already in x3mf; J026 tests the existing feature switches. | Use x3mf for paired runs; leave broad switch sweeps separate. |
| `comms/x1` at `e265f16` | K011 reproduced J018 gameplay with a different native digest. | Compare directly to J018. Windows WASI libraries restored both hashes on macOS; see REPRODUCTION.md. |
| `dev/botx3-team-economy-20261102` at `2bf2652` | Parallel work on team economy. | Check ownership and routing overlap before adding a coordinator. |
