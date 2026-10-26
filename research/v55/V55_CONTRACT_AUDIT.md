# V55 rules-to-code audit (in progress)

The user asked for a broader audit after finding the draft availability mismatch. GameRules.md and BotAPICpp.md are contracts, not agent instructions. Findings are checked against sdk/cpp/cambc.h/imports.h and actual engine replays. This audit does not claim that all possible bugs have been excluded.

| Area | Finding | Status / evidence |
|---|---|---|
| Draft availability | draft.cpp masks enemy picks as unavailable, while mirrors are allowed | Confirmed mismatch. Actual130-game listing has119games with mirrored choices. R1 corrects the mask, but672same-lineage games are identical to v54. Kept in R10 as a necessary contract correction, with no claimed competitive gain. |
| Camp danger lists | world.cpp awake_camps_near and tsearch.cpp fast cache filter damaged individual camps; healthy members of an awakened group are omitted | Confirmed model mismatch with whole-group awakening. R4 exact visible masks:342/672,+6.1,95%[-13.2,+30.8],not retained. SDK state differs from health. |
| Camp sleep | Damage is treated as a permanent wake signal in the coarse hot_zone, although camps can sleep again after no targets | Confirmed conservative approximation; R4 corrects detailed tactical lists only, not all routing/recall uses. Do not call every conservative prediction a proven gameplay defect. |
| Mission completion | Learned off-base camp targets stay committed up to40rounds even after capture | Confirmed missing completion event. R2 pooled24seeds726/1344,+19.8,95%[+3.5,+37.1]. Retained foundation; waiting -11.1%,capture income +3.9% byR500. |
| Ward programme | Old APEX_WARDS=0 disables drop_ward; ward_reveal still places wards | Configuration, not an API violation. Earlier E4 was inert; E4b activated the programme and lost. |
| Capital estimate | items_of removes Ryth health-derived strength but includes Prism bag-derived focus | Confirmed contamination of a stat-derived capital proxy. Its contribution to reward allocation is unmeasured; not automatically a proven cause of losses. |
| Shared claims |6*7bits, on-site64-111 only when <=48groups, fight112-118 | Bounds and code spaces checked; no collision found in these enabled paths. Draft memory is separate1024bytes. |
| Group respawn cache | Known respawn events reset remembered hp/dead flags | Checked in apply_event and observe_groups; no stale-dead bug found on these paths. |
| Cast/move/attack allowances | Self actions generally use SDK can_move/can_attack and cast_done/cooldowns | Audit continuing across exclusive movement and reset abilities; approximate enemy simulations require separate calibration. |
| Gold/items | Treasure+Vesper bonuses are engine-owned, stats retained in repeated Bruiser emblems | Contracts checked; no agent-side multiplication of gold bonuses found.10gold crystal can displace a30gold shard: earlier E6 fixes that budget event but loses transport maps and is unretained. |

## R4: exact awake-camp tactical cache

Independent base v54. V55_AWAKE_EXACT queries personal visible camp tiles minus personal asleep-camp tiles once when needed per observation update, caches camp indices, and uses them in both World::awake_camps_near and the fast caster micro cache. This captures healthy awakened camps and excludes injured sleeping camps. No omniscient inputs. New work is outside score_groups, once per turn on demand; near-tile scans reuse a short list. Coarse hot_zone remains conservative. Visibility limitations and the32camp tactical cap remain. Measure camp damage/deaths and fuel, then full12-seed score with clustered interval. Correctness does not by itself prove a competitive gain.

## Additional spell execution gaps

- In the ordinary camp combat path, cast_on_camp(t) can kill the target, but the next basic attack still addresses that same target. Retargeting happens after a BASIC attack kills it, not after a spell. R6 tests a bounded live-target refresh after a successful camp spell (up to4dead target skips); other turns are unchanged. This is a missing completion event in action execution. Quantify actual additional attack/capture production before claiming impact.
- Heart of Ruin's damaging/stunning dash has a dedicated champion-target implementation, but cast_on_camp has no dash case, and my_dps also omits dash damage. Travel dashes can incidentally hit camps, but deliberate camp use is absent. The SDK ability_dash explicitly carries landing radius, modifier and stun duration; GameRules describes1.5*Focus damage to enemies AND camps. This is a confirmed controller coverage gap, not proof that indiscriminate camp dashes are beneficial. A bounded legal landing/target implementation is being prepared.

R2 replication on seeds13-24:360/672,+12.8,zero faults. Pooled24-seed index:726/1344(54.0%),+19.8,clustered95%[+3.5,+37.1]. Both independent sets improved; waiting -11.1% and capture gold+3.9% in the first ledger. First restart mechanism meeting the confidence criterion; further gate and opponent checks remain. R5 runtime optimization lost316/672,-27.4,95%[-56.6,-0.7] despite fewer fuel stalls; reject it. More compute alone does not ensure better choices.

R10 freezes the bounded Heart strike plus validated mission completion and draft legality.414/672wins,+106.0,95%[+44.5,+174.9],both teams0faults. Heart addition to R2:+79.2,[+4.2,+160.6]. Extra damage-model/cache and spell-kill retargeting do not earn incremental support and remain disabled. The pure Heart variant R9 is also positive. Correctness candidates are recorded separately from demonstrated competitive gains; this is not a claim that every possible API or strategy bug has been eliminated.
