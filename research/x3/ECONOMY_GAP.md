# Why we lose on the ladder: the mid-game economy snowball (3 Nov 2026)

Data: 234 ladder games (data/ladder/x1c1, data/ladder/v92: 84 wins, 150 losses), team DOOMSDAY. Scripts:
`research/x3/banking/early_fight.py`, `collect_gap.py` (rounds and metrics as arguments), `camp_control.py`.
Medians over games; "us / them".

## 1. The gap opens after round 300 and keeps growing

| losses | r200 | r400 | r600 | r800 | r1000 |
|---|---|---|---|---|---|
| camp (monster) damage done | 8.8k / 10.2k | 17.3k / 19.5k | 23.7k / 31.2k | 32.4k / 45.1k | 41.4k / 60.0k |
| gold earned | 525 / 644 | 1124 / 1409 | 1530 / 2367 | 1949 / 3191 | 2282 / 3904 |
| gems collected | 80 / 100 | 181 / 252 | 364 / 476 | 558 / 698 | 681 / 1008 |
| champion damage done | 1.5k / 2.0k | 4.0k / 5.7k | 6.0k / 8.7k | 8.2k / 14.1k | 10.4k / 18.9k |
| gold held (unspent) | 127 / 82 | 120 / 123 | 110 / 159 | 99 / 243 | 97 / 255 |

In wins every row is the other way round (r1000: 98k / 63k camp damage, 5470 / 3013 gold). We do not hoard gold
(about 100 held throughout); we earn less. From rounds 400 to 800 the opponent does about 2x our camp damage per
round (58 vs 32, then 70 vs 44).

## 2. They take our camps

| | camp clears r0-300 | r300-600 | r600-900 | r900+ | their clears on our side, per game |
|---|---|---|---|---|---|
| losses | 16.6 / 15.3 | 13.8 / 16.3 | 10.1 / 14.7 | 10.2 / 23.0 | **12.5** |
| wins | 15.4 / 12.5 | 16.2 / 11.9 | 13.7 / 10.0 | 12.1 / 11.4 | 5.5 |

"Our side" = nearer the centroid of our own clears than of theirs. The opening is even (we clear more by round 300
in losses too); from round 300 they invade and farm our half.

## 3. Fights and items

- Deaths: falling behind on deaths by round 80 is bad (4 / 33 won, against 67 / 172 when level), but it covers only
  29 of 150 losses. Being ahead on deaths by round 80 wins only 13 / 29: we win early fights and still lose the economy.
- Items per game in losses: they buy 130 Bruiser shards and 25 Bruiser emblems, we buy 4. We buy Prospector,
  Durability, Greed and Collectors (economy and passives). In our wins we buy 82 Greed shards (we are rich and
  uncontested). Shards all add stats, so the item mix matters less than the gold behind it, but the Bruiser emblem
  (+1 of each other stat) is the top teams' fight build.

## 4. Why the local gate cannot see this

All three gate opponents (v92, v86h, x1bru) are our own lineage with HOME_SIDE on: they value enemy-side camps at 0.3
and fight at 0.8 aggression, so they do not invade. Defence and economy features cannot show a gain against bots
that never take our camps. Held-out check (3 Nov): x3mf beats x3 on unseen opponents too (377 vs 363 of 516), so
the per-map fit is real; the problem is what the gate measures, not overfitting.

## 5. Plan

1. A sparring partner that reproduces the loss pattern: `bots/x3inv` = x3mf with no home discount (HOME_TERR 1.0),
   full aggression (HOME_AGGR 1.0) and the Treasure + Bruiser item plan (V58_ITEM_PLAN 0, so V54_ITEMS 3). Check it
   invades (their clears on our side, gold gap from round 300) before using it.
2. Gate = the three usual opponents (must not regress) + x3inv + the top-12 proxy (`bots/proxy`).
3. Defence features against it: camp defence when an invader is on our side (A2_STANCE 2 forced on, camp watch),
   an adaptive item switch to Bruiser once invaded, and holding numbers on our half after round 300.

## 6. Results against x3inv (3 Nov, pool, 172 games, x3mf = 102)

x3inv reproduces the loss pattern: in x3mf's 70 losses it takes 11.3 camps a game on our side (ladder 12.5, v92 9.1)
and our gold at round 600 is 74% of its (ladder 65%). x3mf kills more of x3inv than it loses (2657 vs 2318 deaths).

| x3mf + | wins | |
|---|---|---|
| V58_ITEM_PLAN 0 (Treasure + Bruiser items) | 91 | -11 |
| HOME_AGGR 1.0 | 103 | +1 |
| A2_CAMPWATCH 1 | 102 | not wired on x3 (same build) |
| X1_DEFEND 1 (stance defence on every map) | 101 | -1 |
| X1_DEFEND 1, trigger 4 | 104 | +2 |
| HOME_TERR 1.0 (no home discount) | 86 | -16 |
| HOME_TERR 0.6 | 95 | -7 |

None adopted. Staying home is right (the discount is worth 16 games); playing the invader's own items or
aggression does not help. Next: the losses are concentrated on 16 maps lost on both sides (02guardians 0 banked and
35 deaths, 03one-gem 65 deaths, 01concentrated-wealth 38, 00crater 34): a per-map look at those games, and a per-map
fit against x3inv (the X1_COUNTER machinery) as a robustness layer.
