# Diagnostic corrections — 4 November 2026

The original EXP-012, EXP-013 and EXP-016 diagnostic runs inherited `--log-limit 0` from the strength benchmark. Replay stdout was empty even when an instrumented branch ran. Those results cannot support a zero-trigger conclusion. We retained the original results as history and reran the identical diagnostic WASMs with a one-megabyte log limit per stream. The [corrected native recount](DIAGNOSTIC_RECOUNT.json) records the engine, fixture hashes, output byte counts and parsed markers. The earlier 172-game L0 comparisons use native statistics and are unaffected.

| Diagnostic | Games | Observations after correction | Affected cells |
|---|---:|---:|---:|
| Late reactive ward cooldown check | 16 | 756 | 14 |
| Safe unused early staging basic attack | 16 | 0 | 0 |
| Early one-turn deposit displaced by an ordinary hunt | 64 | 0 | 0 |

EXP-016's opportunity check passes. A clean early-cooldown release can be tested under the original gate. EXP-012 and EXP-013 still end before a candidate for their exact tested conditions. The charge from instrumentation limits all three diagnostics. None estimates a win effect.

The EXP-009 and EXP-010 timing fixtures also used SDK `is_set` and `set` calls for the independent reference flood. In production, v92 uses `bit` and `set_bit` at `world.cpp:217–238`, implemented as direct chunked memory access at `common.h:1482` and `:1498` (df2975cb). The original fixtures can still check component equivalence. Their fuel totals compare against an independent SDK flood and cannot be interpreted as savings versus the actual v92 labeller. EXP-009's publication schedule additionally differed from its integration.

The corrected draft fixture calls the actual `World::bush_cluster` implementation in each frozen snapshot on every tile in row-major order, including complete component publication. In 16 conformance maps, all three arms matched the component counts, label digests and published masks. The same loop consumed 13,036,117 fuel with v92, 13,701,325 with bushlinear (+5.10%), and 13,744,977 with bushsparse (+5.44%). No draft suspension or bot fault occurred in the diagnostic games. The query order and draft budget differ from gameplay. The independent whole-match pool failures are the release decisions.
