id: K015 (g5070, now; replaces J027 for the 5060)
title: banking B1-B3 + the sweep's near misses, on x3mf - finish by 02:15 UTC
commit: 6f462c4 on build/z-plan (bots/x3; B1-B3 switches added in 6f462c4; Windows off-hash 5704d7ba41ac - check yours
  against your Linux reference bf3f65d009c0)
bot: x3, every line with --set X1_MAPFIT=1, your own mf-g5070 base (96 / 172 vs v92)
part A - screens vs v92 on pool (promote >= 102 to v86h + x1bru):
  b1:     X1_SAFEROUTE=1
  b1h:    X1_SAFEROUTE=1 X1_SR_HOLD=1
  b12:    X1_SAFEROUTE=1 X1_BAGRISK2=1
  b12r07: X1_SAFEROUTE=1 X1_BAGRISK2=1 X1_BR2_RATE=0.7
  b3:     X1_RACEBANK=1
  b123h:  X1_SAFEROUTE=1 X1_BAGRISK2=1 X1_RACEBANK=1 X1_SR_HOLD=1
part B - pool vs v92, v86h, x1bru (all three, base 341 / 516) for the near misses and stacks:
  bag80:     X1_BAGRISK=80
  hrwt:      A2_HIDEREC=1 X1_WALKTAIL=3
  bag80hrwt: X1_BAGRISK=80 A2_HIDEREC=1 X1_WALKTAIL=3
  + the best part-A line stacked with bag80hrwt (name it best+bh)
report: usual table; for part A also banked / collected and deaths per game vs mf. Stop new runs at 02:15 UTC.
