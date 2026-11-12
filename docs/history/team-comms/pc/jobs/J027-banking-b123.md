id: J027 (5060) - the 5070 may take it as K015 only if it has finished K014 + J026 leftovers before 02:00 UTC
title: banking B1-B3 screens on x3mf (after the sweep J026 / K014 is complete)
commit: 6f462c4 on build/z-plan (bots/x3; off = 5704d7ba41ac). PC smoke: builds fine, 0 fuel-outs on 4 games.
bot: x3
run: screen on pool vs v92 (base mf = 96), every line with --set X1_MAPFIT=1; promote >= 102 to v86h + x1bru (341)
lines:
  b1:     X1_SAFEROUTE=1
  b1h:    X1_SAFEROUTE=1 X1_SR_HOLD=1
  b12:    X1_SAFEROUTE=1 X1_BAGRISK2=1
  b12r07: X1_SAFEROUTE=1 X1_BAGRISK2=1 X1_BR2_RATE=0.7
  b3:     X1_RACEBANK=1
  b123h:  X1_SAFEROUTE=1 X1_BAGRISK2=1 X1_RACEBANK=1 X1_SR_HOLD=1
priority: 1 (right after the sweep rows; before J023 resumes)
done when: results file with the usual table; for each line also banked / collected per game and deaths per game
  vs mf (the target is conversion: share of collected gems banked).
