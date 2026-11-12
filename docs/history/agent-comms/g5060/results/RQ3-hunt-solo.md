# Retry queue #3: X1_HUNT_SOLO under a hunting plan (idle work, no job number), 2 Nov 05:40 UTC

Commit 0b3703b. Why: RETRY_QUEUE #3 says HUNT_SOLO is a dead path in default play (0 of 240 games changed) and owes a
retest where hunting is common. The early-contact answer (plan 6) turns hunting off (hunt -99), so I used **plan 8
(push: territory 1.0, aggression 1.3, hunt range +3) from R150** as the hunting context.
Lines: p8r150 = `--set X1_PLAN=1 --set X1_PLAN_ROUND=150 --set X1_PLAN_ID=8`; p8r150hs3 / hs5 = that + `--set
X1_HUNT_SOLO=3` / `=5`. Gate: x2 + x2-s2, ladder + styled, both sides (480 a line); no maze cell. results.json in RQ3/.

| line | wins | vs | games changed (R0) | fuel-outs | verdict |
|---|---|---|---|---|---|
| p8r150hs3 | 261 | p8r150 261 | **0 / 480** | equal | **R0 fails: dead path** (identical games, so "pass +0" is not a pass) |
| p8r150hs5 | 261 | p8r150 261 | **0 / 480** | equal | **R0 fails: dead path** |

HUNT_SOLO builds a different binary (sha below) but changes no game even with plan 8's longer hunts. Its trigger
(no ally within 5 and a hunt beyond N tiles) apparently never coincides with a hunt decision in x1; the PC should
look at the trigger before any further retry (protocol: fix the trigger, do not score it).

Side result, plan 8 from R150 as a whole-game setting vs the x1 base (rule R1):

### p8r150: 261 wins vs base 257; verdict **fail** (total +4, fuel-outs +34)

| kind | opp | wins | Δ base | fuel-outs (Δ) | faults | gold@R250 | gold@R500 | deaths/game | finish round | sha |
|---|---|---|---|---|---|---|---|---|---|---|
| ladder | x2 | 69/140 | +1 | 122 (+12) | 0 | 780 | 1709 | 14.77 | 1222 | 28b4d73974a0 |
| ladder | x2-s2 | 71/140 | -4 | 113 (+11) | 0 | 821 | 1755 | 14.26 | 1216 | 28b4d73974a0 |
| styled | x2 | 56/100 | +1 | 77 (+1) | 0 | 893 | 1819 | 16.40 | 1189 | 28b4d73974a0 |
| styled | x2-s2 | 65/100 | +6 | 61 (+10) | 0 | 959 | 1922 | 16.26 | 1195 | 28b4d73974a0 |


## HUNT_SOLO cells vs p8r150

### p8r150hs3: 261 wins vs base 261; verdict **pass** (total +0)

| kind | opp | wins | Δ base | fuel-outs (Δ) | faults | gold@R250 | gold@R500 | deaths/game | finish round | sha |
|---|---|---|---|---|---|---|---|---|---|---|
| ladder | x2 | 69/140 | +0 | 122 (+0) | 0 | 780 | 1709 | 14.77 | 1222 | 38a77ea20eaa |
| ladder | x2-s2 | 71/140 | +0 | 113 (+0) | 0 | 821 | 1755 | 14.26 | 1216 | 38a77ea20eaa |
| styled | x2 | 56/100 | +0 | 77 (+0) | 0 | 893 | 1819 | 16.40 | 1189 | 38a77ea20eaa |
| styled | x2-s2 | 65/100 | +0 | 61 (+0) | 0 | 959 | 1922 | 16.26 | 1195 | 38a77ea20eaa |

### p8r150hs5: 261 wins vs base 261; verdict **pass** (total +0)

| kind | opp | wins | Δ base | fuel-outs (Δ) | faults | gold@R250 | gold@R500 | deaths/game | finish round | sha |
|---|---|---|---|---|---|---|---|---|---|---|
| ladder | x2 | 69/140 | +0 | 122 (+0) | 0 | 780 | 1709 | 14.77 | 1222 | c443e087d264 |
| ladder | x2-s2 | 71/140 | +0 | 113 (+0) | 0 | 821 | 1755 | 14.26 | 1216 | c443e087d264 |
| styled | x2 | 56/100 | +0 | 77 (+0) | 0 | 893 | 1819 | 16.40 | 1189 | c443e087d264 |
| styled | x2-s2 | 65/100 | +0 | 61 (+0) | 0 | 959 | 1922 | 16.26 | 1195 | c443e087d264 |

