# What the current bot source actually does

Reviewed against commit `2e1dcc1cf859a3a9162e58c5f2b6285c8217bd8f`.
The comparison baseline is `bots/v52`, documented as live at 12:02 UTC on
25 October. Platform identity still needs separate verification; a source folder
and a deployment timestamp do not prove which exact bytes played a given game.

| Area | Source fact | Implication for replay interpretation |
|---|---|---|
| Draft | `A2_MLDRAFT 1` enables a learned draft attempt on every map. A successful `ml_draft_pick` returns before the lineup and map-specific fallback tables. | Do not describe the normal boss_battle draft as a fixed lineup. Compare observed picks and check whether the model or fallback actually ran. |
| Draft candidate restriction | `ml_draft_pick` marks both own and opposing picks as taken, although the downloaded official replays establish that mirror picks are supported. | Test removing the opposing-pick exclusion separately, keeping weights and own-team duplicate protection unchanged. |
| Farming | `score_groups` scores reward against travel, waiting, estimated kill time, staffing and health cost; a trained 18-feature camp residual can alter the choice. | A large untouched camp may have been rejected by availability, staffing, risk or admission. The replay alone cannot identify the rejecting branch. |
| stampede | `A2_SOLE_GEM 1`, starting at round 500, overrides group choice when one group contains at least 90% of static gem rewards, the champion is at least 60% healthy and its bag is below the current tribute threshold. | This changes target selection. It does not prove the team assembles, survives, captures, banks or repeats the cycle. |
| Banking | v52 sets the base tribute threshold to 72 gems, with adaptive overrides (the generic fallback definition of 64 is inactive). Winning, late-game, proximity, threatened-bag and opening rules can bank earlier. The generic bag/distance rhythm is disabled (`APEX_BANK_RATIO 0`). | Do not infer one universal bank threshold from the median completed bank. Path length, channel safety and map class matter. |
| Early banking | The opening rule uses a 22-gem bag, round limit 250 and distance limit 14; it excludes a capture in progress and usually maps whose largest group has at least 100 gems. | Early scoring on small-group maps and delayed banking on large-objective maps are different intended behaviours. |
| Gated altars | Initialization detects camp-blocked altar access. `update_altar_gates` opens the banking field when a gate camp is dead or its group is no longer alive; `tribute_if_needed` exits immediately while `no_bank` is true. | On boss_battle, lowering the bag threshold alone cannot solve a gate that never opens. Measure clearing and banking separately. |
| Coordination | Claims, seniority, staffing caps and team-job initiation interact. v52's sole-gem override bypasses the normal scoring path; most large jobs use that path. | Do not generalise a stampede fix to every large objective. Check actual arrivals and survival. |
| Purchases | `shop` follows champion-specific build steps and affordability. Noncasters normally use the enabled `UB_BUILD` path; mobility farming maps retain the original build. Tavi's field-shopping capability differs from other bodies. | Raw purchase action count is a poor item-strength comparison: one call can buy several shards and a fifth shard combines into an emblem. Compare inventories at the same round and champion type. |
| Fuel | v52 has a 55,000 route-fuel setting and 35,000 deterministic safety setting; the prior operations report documents sensitivity to even behaviour-preserving hot-loop changes. | Replay counts of exhausted turns show cap hits, not remaining headroom on other turns. Any later change still needs the existing release/default-fuel gate. |
| v53 | `A2_GATE_JOB 0` leaves the experimental forced gate job disabled. Its historical tests were rejected. | A new recommendation to group for the gate must specify readiness and safety; simply re-enabling the rejected rush is unsupported. |

Source locations at the reviewed commit:

- [v52 configuration](https://github.com/Infosuii/neural-networkk-battlecode/blob/2e1dcc1cf859a3a9162e58c5f2b6285c8217bd8f/bots/v52/src/common.h)
- [Draft order and model](https://github.com/Infosuii/neural-networkk-battlecode/blob/2e1dcc1cf859a3a9162e58c5f2b6285c8217bd8f/bots/v52/src/draft.cpp)
- [Shopping, banking and group selection](https://github.com/Infosuii/neural-networkk-battlecode/blob/2e1dcc1cf859a3a9162e58c5f2b6285c8217bd8f/bots/v52/src/bot.cpp)
- [Altar gates and path fields](https://github.com/Infosuii/neural-networkk-battlecode/blob/2e1dcc1cf859a3a9162e58c5f2b6285c8217bd8f/bots/v52/src/world.cpp)
- [Disabled v53 gate rule](https://github.com/Infosuii/neural-networkk-battlecode/blob/2e1dcc1cf859a3a9162e58c5f2b6285c8217bd8f/bots/v53/src/common.h)
- [Prior measurements and version history](https://github.com/Infosuii/neural-networkk-battlecode/blob/2e1dcc1cf859a3a9162e58c5f2b6285c8217bd8f/ops/HANDOFF.md)

These are implementation facts and prior measurements. They are not evidence
that opponents use the same code or that copying a visible habit will improve
our bot.
