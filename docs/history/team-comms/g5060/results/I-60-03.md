# I-60-03 result: the gate's noise floor, and a paired sign test for every verdict (2 Nov ~17:15 UTC)

Four no-op builds of P4 (bots/x1g60 `X1_G60_NOISE` = 1 / 2 / 3 / 5 volatile steps per turn: identical decisions, a few
instructions more fuel per turn), full gate at 30af738 (x2 + x2-s2, ladder + styled + maze 59, 716 games each),
baseline p4. results.json in results/I-60-03/.

| no-op build | wins Δ vs p4 | ladder / styled / maze Δ | games changed | results flipped (gained / lost) | z |
|---|---|---|---|---|---|
| noise1 | +3 | -1 / +2 / +2 | 77 | 11 / 8 | +0.69 |
| noise2 | -6 | -1 / -4 / -1 | 151 | 18 / 24 | -0.93 |
| noise3 | -7 | -6 / +2 / -3 | 209 | 30 / 37 | -0.86 |
| noise5 | -8 | -2 / +5 / -11 | 296 | 43 / 51 | -0.83 |

A change with no behavioural effect moves the total by up to 8 and a single map kind by up to 11, and the gate rule
would have failed 3 of these 4 no-op builds ("a map kind < -2 points" or the total). Real features reshuffle more
games (446-603 of 716 in J013 / J016), so their chaos is larger still.

**Paired sign test.** Each game is paired with the base's game on the same map and side. If a change has no real
effect, the games it flips are wins and losses about equally, so with W = games it wins that the base lost and L
the reverse, z = (W - L) / sqrt(W + L) is about N(0, 1). The no-op builds give |z| < 1, as they should. Applied to
every line gated on this machine:

| base | line | wins gained W | wins lost L | W-L | z = (W-L)/sqrt(W+L) |
|---|---|---|---|---|---|
| base: p4 (716 games) | g60noise1 | 11 | 8 | +3 | +0.69 |
| base: p4 (716 games) | g60noise2 | 18 | 24 | -6 | -0.93 |
| base: p4 (716 games) | g60noise3 | 30 | 37 | -7 | -0.86 |
| base: p4 (716 games) | g60noise5 | 43 | 51 | -8 | -0.83 |
| base: p4 (716 games) | p4secure | 3 | 1 | +2 | +1.00 |
| base: p4 (716 games) | p4hiderec | 41 | 37 | +4 | +0.45 |
| base: p4 (716 games) | p4bhold | 39 | 41 | -2 | -0.22 |
| base: p4 (716 games) | p4belief | 30 | 45 | -15 | -1.73 |
| base: p4 (716 games) | p4sf55 | 24 | 41 | -17 | -2.11 ** |
| base: p4 (716 games) | p4soak | 87 | 111 | -24 | -1.71 |
| base: p4 (716 games) | p4af5 | 97 | 136 | -39 | -2.55 ** |
| base: p4 (716 games) | p4escort | 100 | 142 | -42 | -2.70 ** |
| base: p4 (716 games) | g60q4e0 | 74 | 88 | -14 | -1.10 |
| base: p4 (716 games) | g60q6 | 96 | 119 | -23 | -1.57 |
| base: p4 (716 games) | g60q20 | 82 | 125 | -43 | -2.99 ** |
| base: x1 (ladder+styled+maze A, 596 games) | bp | 98 | 87 | +11 | +0.81 |
| base: x1 (ladder+styled+maze A, 596 games) | bp2050 | 100 | 90 | +10 | +0.73 |
| base: x1 (ladder+styled+maze A, 596 games) | bpp4r150 | 137 | 106 | +31 | +1.99 |
| base: x1 (ladder+styled+maze A, 596 games) | bpp4r100 | 127 | 105 | +22 | +1.44 |
| base: x1 (ladder+styled+maze A, 596 games) | bptsvis | 104 | 88 | +16 | +1.15 |
| base: x1 (ladder+styled+maze A, 596 games) | bpbelief | 110 | 97 | +13 | +0.90 |
| base: bp (ladder+styled, 480 games) | bpaf3w250 | 80 | 87 | -7 | -0.54 |
| base: bp (ladder+styled, 480 games) | bpaf4 | 72 | 79 | -7 | -0.57 |
| base: bp (ladder+styled, 480 games) | bpp4r100 | 92 | 90 | +2 | +0.15 |
| base: bp (ladder+styled, 480 games) | bpp4r150 | 94 | 84 | +10 | +0.75 |
| base: bp (ladder+styled, 480 games) | bpp6r150 | 77 | 95 | -18 | -1.37 |
| base: bp (ladder+styled, 480 games) | bpburst2 | 62 | 65 | -3 | -0.27 |
| base: bp (ladder+styled, 480 games) | bpstage05 | 64 | 74 | -10 | -0.85 |
| base: bp (ladder+styled, 480 games) | bpwait15 | 78 | 96 | -18 | -1.36 |
| base: bp (ladder+styled, 480 games) | bpneed13 | 70 | 91 | -21 | -1.66 |
| base: bp (ladder+styled, 480 games) | bpprunefix | 89 | 106 | -17 | -1.22 |
| base: bp (ladder+styled, 480 games) | bplocks | 39 | 47 | -8 | -0.86 |
| base: bp (ladder+styled, 480 games) | bpdisengage | 55 | 60 | -5 | -0.47 |
| base: bp (ladder+styled, 480 games) | bpbelief | 30 | 33 | -3 | -0.38 |
| base: bp (ladder+styled, 480 games) | bptsvis | 48 | 47 | +1 | +0.10 |
| base: bp (ladder+styled, 480 games) | P5bp | 89 | 102 | -13 | -0.94 |
| base: bp (ladder+styled, 480 games) | bpsf55 | 15 | 13 | +2 | +0.38 |
| base: x1 (ladder+styled, 480 games) | af3w250 | 109 | 82 | +27 | +1.95 |
| base: x1 (ladder+styled, 480 games) | p4r100 | 105 | 82 | +23 | +1.68 |
| base: x1 (ladder+styled, 480 games) | p4r150 | 101 | 83 | +18 | +1.33 |
| base: x1 (ladder+styled, 480 games) | af4 | 103 | 89 | +14 | +1.01 |
| base: x1 (ladder+styled, 480 games) | soak64 | 64 | 54 | +10 | +0.92 |
| base: x1 (ladder+styled, 480 games) | escort | 92 | 84 | +8 | +0.60 |
| base: x1 (ladder+styled, 480 games) | hiderec | 29 | 22 | +7 | +0.98 |
| base: x1 (ladder+styled, 480 games) | secure15 | 4 | 0 | +4 | +2.00 ** |
| base: x1 (ladder+styled, 480 games) | secure3 | 4 | 0 | +4 | +2.00 ** |
| base: x1 (ladder+styled, 480 games) | bursthold | 39 | 36 | +3 | +0.35 |
| base: x1 (ladder+styled, 480 games) | stage05 | 82 | 71 | +11 | +0.89 |
| base: x1 (ladder+styled, 480 games) | alone | 89 | 114 | -25 | -1.75 |
| base: x1 (ladder+styled, 480 games) | fleehold15 | 69 | 139 | -70 | -4.85 ** |

**Reading (facts):** no gain so far reaches z >= 2 except X1_SECURE (4-0 flips, tiny). The best lines are near it:
BP + plan 4 R150 vs x1 z = +1.99 (596 games), ANTIFEED 3/250 vs x1 +1.95, plan 4 R100 vs x1 +1.68. Several losses
are real: FLEEHOLD 15 -4.85, FIELDQ 20 -2.99, ESCORT on p4 -2.70, ANTIFEED 5/400 on p4 -2.55, SIEGEFUEL on p4 -2.11.
Gains of +10..+27 that "did not carry over" to a new base (J013) are what noise of this size predicts.

**Proposal (PC decides):** (1) put the sign test next to the gate rule: call a gain real only at z >= 2, and a loss
real at z <= -2; between, "not shown" (retry with more games, not rejected). tools/x1_gate_report.py now prints
gained / lost / z on every line (build/z-plan-5060 c754366f). (2) For the ship decision, add games until z settles:
the same lines on a second opponent seed pair (e.g. x2-s3 / v86h-s2) or more generated maps double the flips.
