# v70 (2026-10-28)

Base: `bots/v69` (v65 + 00vault siege fix + island escape + capture stall breaker). One change: a per-map draft.

| Switch | What it does |
|---|---|
| `V70_DRAFT_TABLE 1` | On 29 of the 70 pool maps, draft a fixed lineup instead of the learned draft; the map is recognised in the draft turn by width, height, team size and camp-group count (unique across the pool). Other maps are unchanged. Table: `research/v70/draft_table_v70.json`; patch: `tools/v67/c_v70_draft.py`. |

How the table was chosen (`research/v70/V70.md`): seven candidate lineups were played on every pool map from both sides
against four opponents (v65, v61, v58, and the proxy, which plays each top team's exact per-map drafts); per map, a
lineup replaces the learned draft only if its mean gain over the four opponents exceeds 100 gems per game and it
loses no more than 250 against any one of them (`tools/v67/c_draft_league.py`). Three entries that lost on the first
fresh validation were removed.

Fresh-seed validation against v69 (paired, 280 distinct games per row, our bot as shipped):

| Opponent | Seeds 11/12 | Seeds 13/14 | Deaths per game |
|---|---:|---:|---:|
| v65 | +74 [+4, +143] | +169 [+90, +258] | −2.0 |
| v61 | +58 [−9, +129] | +63 [+11, +123] | −1.4 to −1.7 |
| v58 | +70 [−2, +133] | +75 [+14, +144] | −1.7 to −2.2 |
| proxy (top-team drafts) | +39 [−11, +89] | +15 [−33, +67] | −0.5 |

Gems per game, 95% CI. Seeds 11/12 include three entries later pruned; 13/14 is the final table. A first table chosen
against v65 alone (`bots/v70v65`) gained +190 against v65 but nothing against v61 or v58: a counter to v65's own draft,
not a better draft.
