# Discovery 6 — Early collection and contact

The frozen sample contains 24 distinct ranked losses from 72 eligible rows after excluding earlier cohorts and the direct rival review. At capture time, the global ladder placed DOOMSDAY 64th, QS2isLaw 27th, 0xDEADBEEF 46th and bentheboss 57th. Ranked match summaries do not identify the submission versions. [Frozen sample](DISCOVERY6_SAMPLE.json), [confirmation checks](DISCOVERY6_HYPOTHESES.md).

| Winner's advantage | Discovery | Reserved | Mean gap in reserved games with the pattern | Sum of those gaps |
|---|---:|---:|---:|---:|
| More gems collected by R300 | 13/16 | 5/8 | 84.8 gems | 424 gems |
| More inferred camp gold by R300 | 12/16 | 5/8 | 607.8 gold | 3,039 gold |
| More gems collected by R300 after no lead before first proximity | 8/16 | 3/8 | — | — |
| More wards across the game | 14/16 | 8/8 | 257 wards | 2,056 wards |
| More allies near the first proximity event | 3/16 | 3/8 | — | — |

The gaps are observed, not recoverable gains. Median R300 gaps across all eight reserved losses were 39 gems collected and 348.5 earned gold. The median collection gap before first proximity was zero, and the winner led before proximity in two of eight. DOOMSDAY had more deaths without a recorded PvP attack or cast through R600 in six of eight reserved games and four of 16 discovery games. Treat this as exploratory. [Economy comparison](DISCOVERY6_CONFIRM.json), [proximity comparison](DISCOVERY6_CONTACT_CONFIRM.json).

## Own-view turns at R150

| Game | Team gems collected, DOOMSDAY first | Same-role replay |
|---|---:|---|
| Gift Wrapping vs the ruliad | 72 / 160 | Vendetta had 10 visible camps, carried 16 gems and made a basic attack. Their Vendetta had 16 visible camps, no gems and moved. DOOMSDAY led 1,128 / 946 in earned gold at the same checkpoint. |
| Shortcut vs bentheboss | 51 / 107 | Vendetta was dead. Their Vendetta was alive with 640 HP and 28 carried gems and began recall. Neither own-view snapshot contained a visible enemy. |
| Split vs dromedaries | 77 / 180 | Heart of Ruin carried 23 gems, saw 14 camps and moved. Their Heart carried seven, saw 13 camps and moved and cast. The winner was already ahead by 89 collected gems at the pre-contact checkpoint. |

The visible states and executed actions are reproducible. Historical route intent, safe alternative actions and what caused the team gaps require additional counterfactual checks. The unchanged v92 subsystem control retains 1,280 matched native games across four opponents and two noise seeds. [Six own-view turns](discovery6-turns), [ablation control](ABLATIONS.md), [next experiments](DISCOVERY6_CARDS.md).
