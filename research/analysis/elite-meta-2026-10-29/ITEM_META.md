# Item economics and conditional purchasing

All 7320 native purchase/combination records, including exact round, cursor, ordinal, quantity and gold amount, are in PURCHASES.csv. Emblem completions and per-body progressions appear in every match dossier. Raw round states preserve all inventory quantities and effective stats. Purchases are observed; the foregone value of another purchase is not experimentally identified.

The pinned engine was queried afresh for all 84 item records. They agree with the repository's Sprint 3 SDK facts within float precision. There are 14 families with three stat variants and shard/emblem tiers. A shard costs 30; five matching shards produce most 150-gold emblems. Greed takes 25 shards/750 gold and grants 35 growth points. Duplicate emblem stats stack; family passives do not. Gold refunds from Tavi sales must not be classified as earned income.

## Item families and their actual decision conditions

| Family | Current effect | When it is a defensible candidate |
|---|---|---|
| Monster | +15% camp damage | Camp damage is the limiting stage and saved rounds can be used. |
| Power | Six main-stat points for five bought | Immediate main-stat output matters more than another passive. |
| Durability | 10% less incoming damage | Both PvP and neutral damage threaten productive time or bags. |
| Treasure | +10 percentage points of gold gain | Sufficient future qualifying income remains; useful same-stat alternative. |
| Jungle | 30% less camp damage received | Neutral survival/recall frequency limits repeated farming. |
| Home | Five recall ticks become three | Saved travel/recovery cycles repay the alternative passive. |
| Bruiser | Five chosen-stat plus one each other stat | Mixed offensive/survival value; repeated copies add stats, not passive. |
| Tribute | 33% shorter tribute duration | Large protected deliveries; little benefit on already one-tick bags. |
| Capture | Caps remaining capture timer at three | Frequent captures or useful mid-capture arrival, not arbitrary allies waiting. |
| Prospector | +25% of the holder's own cluster reward share, rounded down | Gold/gem clusters, correct receiver present at completion. It does not multiply every monster reward. |
| Hunter | +50 base gold per credited champion kill | A credible, survivable kill flow; not an unconditional farming opener. |
| Skirmish | +5% damage to champions | PvP is the current throughput/access bottleneck. |
| Greed | 35 main-stat growth points at 750g | A completed late spike is affordable without missing an earlier productive milestone. |
| Collectors | +1% damage per distinct completed family | Several useful families already exist; duplicate variants add no families. |

Treasure's isolated bonus-gold repayment is 150/0.10=1500 base gold, ignoring rounding, the stat value and foregone alternatives. This is not an instruction to reject it below 1500: the purchased shards also improve output. Conversely, high popularity does not prove its opportunity cost is low. With Vesper, 33% and 10% add to 43%; multiplying 1.33 by 1.10 is wrong.

Prospector's corresponding gold-only repayment is 600 qualifying base cluster gold, before rounding. Gems have separate winning value. Sharing 20 cluster gold between two allies gives a Prospector holder floor(10×.25)=2 extra gold; moving another holder onto the region can change both allocation and rounding. Do not apply this calculation to elk gold. An early Prospector on a monster-only route may be mostly a stat purchase with an unused passive.

Greed's finished 35 growth points cost about 21.43 gold per point, compared with 25 for a completed Power emblem's six points. Before completion, however, its 25 shards supply 25 points; five Power emblems supply 30. This creates a horizon/liquidity problem. Pure long-run efficiency cannot justify carrying unspent cash or waiting for a spike while losing the next objective.

## What the elite sample changes

At R250,79/272 physical bodies have completed a Treasure emblem and 62 have completed Prospector. These are observational body counts within 30 matches, not 272 independent trials. Jungle and Treasure both occur across successful controllers. Mite's sampled Jungle-first systems win contest, broken_curve and packs, while its yellow_brick_road loss has a different execution problem and an opposing successful economy. Fish wins expanse while its Vesper's Treasure is only R290; the losing Vesper completed Treasure at R54. Neither timing alone explains the game.

The strongest role-specific examples are Marcella's Treasure/Durability scoring loop on eight, Vesper's Prospector/Treasure/Jungle economy on swirl, and the gate-support ensemble on boss_battle. Varg's Tribute Emblem of Health at R624 supports the later 49→249 bank in four ticks. These are complete job contexts, not isolated item prescriptions.

Proposed purchase policy: estimate the next two feasible objectives and delivery path, identify whether survival, clear damage, capture waiting or channel duration is binding, and compare one completed milestone against the best alternative. Account for shopping access and the cost of leaving an objective. Tavi can buy shards in the field but cannot field-buy consumables, and field Health purchases do not heal. On spawn, Health purchases do restore the gained health. These are different tactical values for the same stat purchase.

Current DOOMSDAY source already has sophisticated plans; recommending merely adding Prospector or Capture would repeat implemented work. The supplied-v69 and conditional-v71 source comparisons in DOOMSDAY_GAP.md instead identify where expected future job value should choose between plans. No item A/B strength result is claimed for this new study.
