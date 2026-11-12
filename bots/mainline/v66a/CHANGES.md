# v66 (2026-10-27)

Base: platform v65 (`v61_engine4.zip`, uploaded by a teammate). Its source is not in this repository; the file name
and size (279,727 bytes against v61's 281,753-byte bundle) mark it as a re-upload of v61, so v66 starts from
`bots/v61`. Sources: `research/v62/BIG_STRATEGIES.md` (the top teams' measured fight rules) and
`research/top-losses-20261026/README.md` (all 502 top-25 losses of 25-26 October).

Each change has its own switch in `src/common.h`; setting it to 0 gives back v61's behaviour.

| Switch | What it does | Evidence |
|---|---|---|
| `V66_ITEMS 1` | Each hero opens with the engine-2 winners' shards, then Bruiser stat stacks: Vesper Treasure/Jungle Strength + Durability; Heart of Ruin Treasure Health + Jungle Focus + Durability; Vendetta Treasure Health + Jungle Strength + Durability; Marcella Jungle Strength + Durability, then Bruiser focus/health/strength; Ryth Treasure Health + Jungle Strength + Bruiser Health; and so on. | About 3,000 winning top-team hero appearances: they buy Treasure and Jungle first and stack Bruiser earlier. We opened with Prospector and bought no Bruiser before round 300 in 105 v62c losses. |
| `V66_LEAVE 1` | Last override on the fight verdict: in contact, below a health line set by the local numbers (0.75 outnumbered, 0.5 even, 0.3 ahead), and not winning the health race against the target, we leave and stay out for 5 rounds. A kill this turn keeps the fight. | We lose 35 health per contact against their 18 and die 13.5 times per loss against 3.7. Top teams end engagements at 0.77-0.94 health; v61 fled only below the 0.19-0.22 danger line. |
| `V59_ALONE 1` | A lone champion (no healthy ally within 5) also leaves two enemies. | The audit confirmed the gap in source: with `APEX_OUTNUMBERED 2` a lone champion stayed against two. Isolated deaths are 33% of ours against 27% of theirs. |
| `V66_WATCHDOG 1` | A champion that has stood still for 40 rounds off spawn, with no enemy in sight, a channel, or a camp about to return, drops its target for 100 rounds and banks its bag. | 85 stationary intervals of 80+ rounds in 30 losses; 82 of them with legal moves (Vault: two champions from round 227 to the end of a 343-347 loss). |
