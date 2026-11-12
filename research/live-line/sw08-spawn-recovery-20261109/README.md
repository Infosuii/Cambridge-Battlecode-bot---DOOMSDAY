# Spawn recovery on v113

rv11 counterattacked below 85% health. The matched trace showed a 537-round wait at roughly 95% health. The fix detects a plateau at any incomplete health above the lower safety threshold and lets the champion fight back from spawn. The second arm also tracks the best health reached and prefers an adjacent safe spawn tile. The third arm allows a safe exit at high health. In the measured Homonoliths fixture, successful counterattacks drove the change and neither movement branch triggered.

- b113 had 6,505 corroborated heal-wait rounds and a longest confirmed run of 584 rounds. The spawn-area stall rate was 3.30% per alive round.
- hp01 had 1,375 corroborated heal-wait rounds and a longest confirmed run of 100 rounds. The spawn-area stall rate was 0.56% per alive round.
- hp02 had 1,257 corroborated heal-wait rounds and a longest confirmed run of 100 rounds. The spawn-area stall rate was 0.53% per alive round.
- hp03 had 1,257 corroborated heal-wait rounds and a longest confirmed run of 100 rounds. The spawn-area stall rate was 0.52% per alive round.

`hp01` was frozen after development.

The frozen build ran 976 strength games. Its pooled change versus v113 was +0.25 percentage points and its direct score was 49.2%. Ladder delivery phase was active.

The weights header matched v113 byte for byte. In the 400 paired shared-opponent cells, 12 losses became wins and 11 wins became losses. The observed improvement is shorter spawn healing stalls.

A separate Islands candidate moved off expired camp tiles 11 times in traced games. Idle time on those tiles fell from 316 to 0 rounds in the fixture. Its source experiment is in the tools directory.
