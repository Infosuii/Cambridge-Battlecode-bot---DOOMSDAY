# EXP292 result — Exact v112–v114 all fail the unchanged fuel gate

MEASURED. The team's authenticated download controls gave the exact source archives for platform v112, v113, and v114. Each rebuilt twice to the same local SDK 5 WASM. These are the identities of the local audit projects, while the platform server WASM hash remains unavailable. [Source file and archive hashes](UPLOADED_112_114_SOURCES.json) · [Exact local build hashes](UPLOADED_112_114_BUILDS.json)

| Platform | Audit project | Local WASM prefix | Fixed score / 172 | Total fuel-outs | Round-one fuel-outs | Cells above v92 total / round one |
|---|---|---|---:|---:|---:|---:|
| v80 | v92-e3 | `5704d7ba41ac` | 86 | 203 | 28 | 0 / 0 |
| v112 | codex-upload-audit-v112-release-20261108 | `932030e05e5d` | 98 | 1,610 | 62 | 151 / 9 |
| v113 | codex-upload-audit-v113-release-20261108 | `b985b0413279` | 107 | 436 | 64 | 61 / 9 |
| v114 | codex-upload-audit-v114-release-20261108 | `2c147d877d4d` | 100 | 1,595 | 64 | 144 / 9 |

All 688 native summaries and replay archives passed the planned checks. The 172 new v92 controls reproduced the original full native JSON and frozen rows. There were zero faults and zero diagnostic-code cells across all arms. v113 reduced fuel versus v112 in 147 cells, tied 22, and increased it in three. Its total decreased by 72.9%, while round-one fuel increased from 62 to 64. Each upload failed the per-cell gate. Fixed scores describe this one deterministic control matchup. [Safety plan](UPLOADED_112_114_POOL_PLAN.json) · [All rows and raw hashes](UPLOADED_112_114_POOL_RESULT.json)

The v113 archive changes ten existing source files and adds `channel_retry.h`. It checks actual remaining fuel at optional admission points, raises CLFS from 9 to 15, and changes recall and submission retry behavior. Its result measures the whole upload. v114 instead changes `bot.cpp` and `common.h` and adds `cl_newmap_table.h`. It caps the gold-only shopping threshold at 90 before round 300 and applies profile offsets to 16 map signatures using dimensions, group count and total gems. It shares v112's channel and fuel logic. This source confirmation supersedes the unverified-source note in the previous wrap-up. [Team upload report](https://github.com/Infosuii/neural-networkk-battlecode/issues/5#issuecomment-6728457394)

The ranked capture contains 555 completed games in 111 groups from the fixed 05:30–23:50 GMT window. There were 18 wins in 30 games before v114's upload during the nominal v113 window and 2 wins in 5 games started after v114's active status timestamp. The archived public listing and native data lack per-match submission IDs. The cutoffs describe observed activity, and the opponent and map mixes differ. None of these groups is a pinned comparison. [Ranked window plan](RANKED_112_114_TRANSITION_PLAN.json) · [95 native summaries recounted](RANKED_112_114_TRANSITION_RESULT.json)

There were four wins in 20 games against 0xDEADBEEF in the frozen window. Across its 16 wins against us, our camp income at round 300 averaged 225.6 gems versus 207.9, while the opponent banked 176.8 to our 119.0 and had spent 258.8 gold to our 156.9 at round 100. By the end we averaged 234.9 fewer camp gems, the largest loss component in eight of the 16 games. Fights led in five and unbanked gems in three. Production was the largest terminal deficit in 32 of all 49 audited losses. These resource accounts agree with independent native team totals and champion timelines. [Resource audit](RANKED_112_114_RESOURCE_AUDIT.json)

The refreshed official index still lists Patch 4.0.0 from 4 November as newest. The UK qualifier lock is Tuesday, 10 November at 23:59 GMT. This audit used no ladder quota and changed no platform selection. The established fallback remains v80/v92. [Patch notes](https://2026a.battlecode.co.uk/game/patch-notes/27bb962b-12a2-4355-b3b4-f6b36150fdc3) · [Tournament schedule](https://2026a.battlecode.co.uk/game/tournaments)
