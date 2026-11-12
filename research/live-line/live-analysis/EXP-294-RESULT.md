# EXP294 result — Exact v105/v106 sources and current matched safety

MEASURED. The authenticated team archives for platform v105 and v106 rebuilt twice identically in SDK 5. v105's exact source rebuild reproduces the earlier CPG binary hash and resolves its prior inferred identity. v106's exact source rebuild identifies the local nnq4 field-fix binary. The platform server WASM hashes remain unavailable. [Source archive and per-file hashes](UPLOADED_105_106_SOURCES.json) · [Build and map pins](UPLOADED_105_106_POOL_PLAN.json)

| Platform | Local WASM prefix | Fixed score / 172 | Total fuel-outs | R1 fuel-outs | Cells above v92 total / R1 |
|---|---|---:|---:|---:|---:|
| v80 / v92 | `5704d7ba41ac` | 86 | 203 | 28 | 0 / 0 |
| v105 / CPG | `a06ae0655dc5` | 97 | 106 | 16 | 12 / 0 |
| v106 / nnq4 field fix | `f0ad2c27d773` | 95 | 3,596 | 61 | 167 / 9 |
| v112 | `932030e05e5d` | 98 | 1,610 | 62 | 151 / 9 |
| v113 | `b985b0413279` | 107 | 436 | 64 | 61 / 9 |
| v114 | `2c147d877d4d` | 100 | 1,595 | 64 | 144 / 9 |

All 344 new games passed archive and native checks. All 172 reused v92 control hashes matched the freshly reproduced EXP292 controls. Zero faults and zero diagnostic-code cells in the complete table. v105 has the lowest total fuel-out count among the uploads in this table. Its 12 per-cell increases still veto release. v113 has the highest fixed score here. These scores share maps, sides, engine, and v92 opponent, and remain one deterministic draw per cell. They cannot rank current ladder strength. [EXP294 rows](UPLOADED_105_106_POOL_RESULT.json) · [EXP292 rows](UPLOADED_112_114_POOL_RESULT.json)

Independent fuel timing confirms that v113's improvement occurs within shared early exposure as well. All 172 games per arm completed R300. By then v113 recorded 345 fuel-outs against v112's 860 and v92's 142. This is observed event timing, without information about the code function that exhausted fuel. [Timing recount](UPLOADED_112_114_FUEL_PHASES.json)

The v114 bundle shifted purchases earlier in the same fixed games. For the 171 cells where both teams bought something, v114's first purchase was 15.9 rounds earlier on average and nine rounds earlier at the median. Its R100 spend was 210.4 gold against v112's 153.8, with 80 cells higher, 69 tied and 23 lower. At R300, the bundle had 3.1 fewer camp gems and 7.3 fewer banked gems per game on average. The source changes early shopping and map profiles together, so the result does not isolate either change or establish a ladder gain. [Early economy recount](UPLOADED_V114_EARLY_ECONOMY.json)
