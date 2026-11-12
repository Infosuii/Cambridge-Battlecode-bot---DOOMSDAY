# Champion draft evidence

These are deliberately selected match-side counts, not champion causal effects. Team, map, opposing draft and hidden submission changes are confounders. The tier labels in CHAMPION_META.md classify confidence in practical use; this table cannot rank intrinsic power.

| Champion | Picks /60 sides | Winning sides | Distinct owning teams |
|---|---|---|---|
| Ryth | 29 | 17 | 11 |
| Vesper Vale | 51 | 25 | 16 |
| Vendetta | 47 | 25 | 16 |
| Cassi & Issac | 6 | 4 | 4 |
| Stellar | 2 | 1 | 1 |
| Prism | 3 | 2 | 2 |
| Marcella | 51 | 25 | 16 |
| Willow | 11 | 2 | 3 |
| Ren | 2 | 2 | 1 |
| Varg | 5 | 3 | 5 |
| Tavi | 9 | 4 | 5 |
| Heart of Ruin | 50 | 23 | 17 |

## Full same-side co-occurrence matrix

Cells are match sides with both champions; diagonal is pick count. See SYNERGY_COUNTS.csv for results and denominators. A high cell mainly reflects common core picks.

| Champion | Ryth | Vesper Vale | Vendetta | Cassi & Issac | Stellar | Prism | Marcella | Willow | Ren | Varg | Tavi | Heart of Ruin |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Ryth | 29 | 22 | 22 | 0 | 2 | 0 | 29 | 1 | 1 | 1 | 4 | 23 |
| Vesper Vale | 22 | 51 | 41 | 5 | 0 | 3 | 42 | 10 | 2 | 4 | 6 | 44 |
| Vendetta | 22 | 41 | 47 | 5 | 0 | 1 | 38 | 10 | 1 | 3 | 7 | 38 |
| Cassi & Issac | 0 | 5 | 5 | 6 | 0 | 0 | 4 | 0 | 1 | 2 | 0 | 6 |
| Stellar | 2 | 0 | 0 | 0 | 2 | 0 | 2 | 0 | 0 | 0 | 0 | 2 |
| Prism | 0 | 3 | 1 | 0 | 0 | 3 | 2 | 2 | 0 | 1 | 2 | 1 |
| Marcella | 29 | 42 | 38 | 4 | 2 | 2 | 51 | 10 | 1 | 3 | 8 | 42 |
| Willow | 1 | 10 | 10 | 0 | 0 | 2 | 10 | 11 | 0 | 1 | 1 | 8 |
| Ren | 1 | 2 | 1 | 1 | 0 | 0 | 1 | 0 | 2 | 0 | 0 | 2 |
| Varg | 1 | 4 | 3 | 2 | 0 | 1 | 3 | 1 | 0 | 5 | 0 | 3 |
| Tavi | 4 | 6 | 7 | 0 | 0 | 2 | 8 | 1 | 0 | 0 | 9 | 5 |
| Heart of Ruin | 23 | 44 | 38 | 6 | 2 | 1 | 42 | 8 | 2 | 3 | 5 | 50 |

## Composition archetypes actually observed

Each entry is an unordered draft set. Small n and repeated team identities prohibit intrinsic composition win-rate claims.

| Composition | Sides | Winning sides | Examples |
|---|---|---|---|
| Ryth, Vesper Vale, Vendetta, Marcella, Heart of Ruin | 14 | 9 | 00dunes 24184b1f; 00dunes 24184b1f; 02tangle 19ab1bcf |
| Vesper Vale, Vendetta, Marcella, Willow, Heart of Ruin | 7 | 1 | 01islands 81686d7d; 01fracture 5e95c8e8; 00eight 4942b190 |
| Vesper Vale, Vendetta, Heart of Ruin | 5 | 2 | 02arena 01018bb3; 01broken_curve 44203a7e; 00fragment 360f42eb |
| Vesper Vale, Vendetta, Cassi & Issac, Marcella, Heart of Ruin | 3 | 2 | 00contest 089ea886; 01yellow_brick_road 89903723; 02treasure_box 371424db |
| Ryth, Vesper Vale, Marcella, Heart of Ruin | 3 | 1 | 00reverse_spiral 3f460d2d; 00vault b739a862; adgato_gemcombat2 b1577eb7 |
| Vesper Vale, Marcella, Heart of Ruin | 3 | 1 | 00anvil 5e9a9b64; 00anvil 5e9a9b64; 01broken_curve 44203a7e |
| Ryth, Vendetta, Marcella | 2 | 2 | 02arena 01018bb3; 00fragment 360f42eb |
| Ryth, Vesper Vale, Vendetta, Marcella, Tavi | 2 | 1 | 00expanse 18e53453; 00lanes 2ccd0703 |
| Ryth, Stellar, Marcella, Heart of Ruin | 2 | 1 | 00reverse_spiral 3f460d2d; adgato_gemcombat2 b1577eb7 |
| Vesper Vale, Vendetta, Marcella, Heart of Ruin | 2 | 1 | 00vault b739a862; 00quarry d8d3355d |
| Vesper Vale, Prism, Marcella, Tavi, Heart of Ruin | 1 | 1 | 00contest 089ea886 |
| Vesper Vale, Vendetta, Cassi & Issac, Varg, Heart of Ruin | 1 | 1 | 00expanse 18e53453 |
| Ryth, Vesper Vale, Marcella, Varg, Heart of Ruin | 1 | 0 | 01boss_battle 3b30c86a |
| Vesper Vale, Vendetta, Prism, Willow, Varg | 1 | 1 | 01boss_battle 3b30c86a |
| Vesper Vale, Vendetta, Cassi & Issac, Ren, Heart of Ruin | 1 | 1 | 01fracture 5e95c8e8 |
| Ryth, Vendetta, Marcella, Tavi | 1 | 1 | 02stalactites 3a7d1da4 |
| Vesper Vale, Vendetta, Tavi, Heart of Ruin | 1 | 0 | 02stalactites 3a7d1da4 |
| Vesper Vale, Vendetta, Marcella, Willow | 1 | 0 | 00swirl 3d98b425 |
| Ryth, Vesper Vale, Vendetta, Marcella | 1 | 1 | 00swirl 3d98b425 |
| Vendetta, Marcella, Tavi, Heart of Ruin | 1 | 1 | 00quarry d8d3355d |
| Ryth, Vesper Vale, Marcella, Ren, Heart of Ruin | 1 | 1 | 00monolith ab6c4fa4 |
| Ryth, Vendetta, Marcella, Tavi, Heart of Ruin | 1 | 0 | 00elkring 346e719d |
| Vesper Vale, Vendetta, Marcella, Varg | 1 | 1 | 00rows cf10b651 |
| Cassi & Issac, Marcella, Varg, Heart of Ruin | 1 | 0 | 00rows cf10b651 |
| Ryth, Vendetta, Marcella, Willow, Heart of Ruin | 1 | 0 | 01elk_arena 24b6f8f8 |
| Vesper Vale, Vendetta, Marcella, Tavi, Heart of Ruin | 1 | 0 | 01yellow_brick_road 89903723 |
| Vesper Vale, Prism, Marcella, Willow, Tavi | 1 | 0 | 02treasure_box 371424db |
