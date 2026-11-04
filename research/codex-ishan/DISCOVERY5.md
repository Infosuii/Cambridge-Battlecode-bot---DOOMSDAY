# Discovery 5 — Collection and banking in fresh ranked losses

The frozen sample contains 16 discovery and eight reserved losses from 152 eligible fresh ranked rows. The ladder snapshot put DOOMSDAY at global rank 68, QS2isLaw at 31, 0xDEADBEEF at 48 and bentheboss at 55. The sample excludes the four prior discovery cohorts and the direct rival review. Ranked summaries do not identify submission versions. [Sample](DISCOVERY5_SAMPLE.json).

| Pattern | Discovery | Reserved | Reserved median winner minus DOOMSDAY |
|---|---:|---:|---:|
| Winner ahead in earned gold by R300 | 12/16 | 6/8 | 202 |
| Winner ahead in inferred camp gold through R300 | 9/16 | 5/8 | 197.5 |
| Winner ahead in gems collected by R300 | 10/16 | 6/8 | 47 |
| Winner ahead in gems banked by R300 | 12/16 | 7/8 | 42.5 |
| Winner banked more despite DOOMSDAY collecting at least as many gems | 4/16 | 1/8 | — |
| Winner banked more and DOOMSDAY lost more gems through R300 | 5/16 | 2/8 | — |
| Winner placed more wards over the game | 13/16 | 5/8 | — |

The reserved sample had 102 versus 112 inferred captures and 6,085 versus 9,477 inferred camp gold, DOOMSDAY first. The opening deficit more often involved collecting fewer gems than converting an equal collection into fewer banked gems. The largest reserved bank gaps also varied across games. Gemfight had a 174-gem deficit and 78 versus zero lost gems, while The Front had a 178-gem deficit with no gem loss on either side through R300. The first sustained 40-gem bank lead appeared by R250 in four of eight reserved losses. [Discovery rows](DISCOVERY5_DISCOVERY.json), [reserved rows](DISCOVERY5_CONFIRM.json).

## Round 150 own-view turns

| Game | Observed choices |
|---|---|
| The Front, `01a1a5dc-69e8-7e4b-a555-d499bcd6c1a1` | The opponent led by 786 earned gold. Our Vendetta had no enemy visible, saw 25 camps and attacked. Their Vendetta saw nine camps, had 140 gold and bought three items. |
| Gemfight, `8e32cc87-4f89-40ed-a7cb-588e6f28243d` | Our Vendetta held 22 gems at 540/1,200 HP, saw 15 camps and no enemy, and ended the turn without a move or basic attack. Their Vendetta moved with two visible enemies. |
| Gold Rush, `01a1a76e-86c3-71d4-97fb-ca71986626d4` | The opponent led by 699 earned gold. Our Vendetta moved and updated priority with three enemies visible. Their Vendetta held 24 gems and 100 gold and moved before recalling. |

The replay records view and actions. It cannot establish why the historical bot selected a camp, whether a visible camp could be attacked from its tile or which private route was planned. Compare local choices against the observed mechanics in `Bot::score_groups`, `Bot::route_search`, `Bot::fight_camps` and `Bot::go_home_if_needed`. [Six exact turn views](discovery5-turns), [existing subsystem ablation](ABLATIONS.md), [new cards](DISCOVERY5_CARDS.md).
