# v71 (2026-10-28)

Base: `bots/v70`. One change: per-map strategy profiles over the runtime lab knobs.

| Switch | What it does |
|---|---|
| `V71_MAP_KNOBS 1` | On the first initialised turn the map is recognised by width, height, camp-group count and total group gems (unique over the 70 pool maps); on 32 maps a strategy profile's knob values overwrite `lab::knobs`. Other maps keep v70's knobs. Table: `research/v71/knob_table_raw.json`; profiles: `tools/v67/c_profiles.py`; patch: `tools/v67/c_v71_knobs.py`. |

Profiles (deltas on the baked A2_KNOBS): aggr, caut, bank, hoard, hunt, group, gems, gold, mid, nomid, search, ranged.
Every profile alone is at or below v70 overall; chosen per map (league of v65, v61, v58, proxy; seeds 1/2; mean gain
> 100 gems per game, no opponent below −250).

Fresh-seed validation against v70 (seeds 15/16, paired, 280 distinct games each, gems per game, 95% CI):

| Opponent | Margin difference | Deaths per game |
|---|---:|---:|
| v65 | +20 [−45, +85] | −0.7 |
| v61 | +56 [+6, +110] | −0.5 |
| v58 | −0 [−50, +47] | −0.2 |
| proxy (top-team drafts) | +58 [+0.5, +122] | −0.7 |

Mechanism check: 116-123 of the 128 games on table maps changed; 141-146 of 152 games on other maps were identical to
v70 (the rest differ through first-turn fuel use).
