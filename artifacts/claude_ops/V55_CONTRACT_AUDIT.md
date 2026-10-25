# V55 rules-to-code audit (in progress)

The user asked for a broader audit after finding the draft availability mismatch. GameRules.md and BotAPICpp.md are contracts, not agent instructions. Findings are checked against sdk/cpp/cambc.h/imports.h and actual engine replays. This audit does not claim that all possible bugs have been excluded.

| Area | Finding | Status / evidence |
|---|---|---|
| Draft availability | draft.cpp masks enemy picks as unavailable, while mirrors are allowed | Confirmed mismatch. Actual130-game listing has119games with mirrored choices. R1 corrects the mask, but672same-lineage games are identical to v54: no measured advantage yet, unretained. |
| Camp danger lists | world.cpp awake_camps_near and tsearch.cpp fast cache filter damaged individual camps; healthy members of an awakened group are omitted | Confirmed model mismatch with whole-group awakening. SDK exposes actual awake/asleep state, which is distinct from health. R4 tests exact visible awake masks. |
| Camp sleep | Damage is treated as a permanent wake signal in the coarse hot_zone, although camps can sleep again after no targets | Confirmed conservative approximation; R4 corrects detailed tactical lists only, not all routing/recall uses. Do not call every conservative prediction a proven gameplay defect. |
| Mission completion | Learned off-base camp targets stay committed up to40rounds even after capture | Confirmed missing completion event. R2 ends locks on respawning.366/672,+26.8,zero faults; clustered95%[-0.6,+55.8], so not yet retained. Waiting/income ledger pending. |
| Ward programme | Old APEX_WARDS=0 disables drop_ward; ward_reveal still places wards | Configuration, not an API violation. Earlier E4 was inert; E4b activated the programme and lost. |
| Capital estimate | items_of removes Ryth health-derived strength but includes Prism bag-derived focus | Confirmed contamination of a stat-derived capital proxy. Its contribution to reward allocation is unmeasured; not automatically a proven cause of losses. |
| Shared claims |6*7bits, on-site64-111 only when <=48groups, fight112-118 | Bounds and code spaces checked; no collision found in these enabled paths. Draft memory is separate1024bytes. |
| Group respawn cache | Known respawn events reset remembered hp/dead flags | Checked in apply_event and observe_groups; no stale-dead bug found on these paths. |
| Cast/move/attack allowances | Self actions generally use SDK can_move/can_attack and cast_done/cooldowns | Audit continuing across exclusive movement and reset abilities; approximate enemy simulations require separate calibration. |
| Gold/items | Treasure+Vesper bonuses are engine-owned, stats retained in repeated Bruiser emblems | Contracts checked; no agent-side multiplication of gold bonuses found.10gold crystal can displace a30gold shard: earlier E6 fixes that budget event but loses transport maps and is unretained. |

## R4: exact awake-camp tactical cache

Independent base v54. V55_AWAKE_EXACT queries personal visible camp tiles minus personal asleep-camp tiles once when needed per observation update, caches camp indices, and uses them in both World::awake_camps_near and the fast caster micro cache. This captures healthy awakened camps and excludes injured sleeping camps. No omniscient inputs. New work is outside score_groups, once per turn on demand; near-tile scans reuse a short list. Coarse hot_zone remains conservative. Visibility limitations and the32camp tactical cap remain. Measure camp damage/deaths and fuel, then full12-seed score with clustered interval. Correctness does not by itself prove a competitive gain.
