# First pool diagnostics

## Opponent identification

The draft audit removes duplicate (team, map, side, ordered picks) records from two historical match files. There are 809 distinct observations. Training on one map fold and evaluating the other, a pure lookup of full picks identified 252 teams correctly, 3 incorrectly and abstained on 554. It only registers a key when all training observations agree and span at least three distinct maps. Prefixes identified 207 correctly and 5 incorrectly, with lower coverage.

This does not transfer reliably between ladder snapshots. A table fitted on x1c1-era matches identified 62 correctly and 45 incorrectly on the v92-era file, abstaining on 656; on fresh maps it got 20 correct and 18 wrong. Opponents change lineups, and multiple teams choose the same champions. Leave opponent-name selection off; a future policy can respond to an observed playstyle rather than a name.

## Gem economy

x3mf's exact pool baseline is 341/516, with 548 fuel-outs and no faults. The first two versions of a return-cost scorer came in at 271 and 306. The difference between collection and conversion matters: a safer-looking ratio can improve while banked score falls, because the team stops collecting the most valuable camps. Claims and route costs need to account for both camp ownership and delivery, and should be diagnosed with actual gem transfers rather than the banked/collected ratio alone.

Carrier cover lost 13 games with zero change in fuel-outs. With a 40-gem trigger, small redeployments may give up as much farm time as they protect. Test the same move at a higher bag threshold and compare conversion and carrier deaths.

## Fuel

84 of the baseline's fuel-outs happen in round one. Instrumented play on six heavy maps found 36 round-one suspensions at the field build checkpoint. It also found nine later suspensions during siege cache setup and two inside the sight scan. The profiler changes fuel use and outcomes, so these are location measurements. Field ordering and siege cache allocation are separate candidates.
