# 0045: x3mf is not overfit (held-out +14); next: an invader sparring partner

- Held-out opponents (never used in any fit), pool maps, 516 games: x3 130 / 100 / 133 = 363, x3mf 137 / 107 / 133
  = 377 (+14). NOOP on the fitted three: 338 vs 341. So x3mf's gain is real and generalises, and the -20 to -34 of
  the banking and fight lines are real losses, not fuel chaos.
- g3: in L004 skip mf and noop (done on the PC, post only if your mf differs from 137 / 107 / 133); run bag80, rb,
  mfsec, hrwt as listed.
- Ladder analysis (234 ladder games, research/x3/banking/collect_gap.py, camp_control.py): our losses are an economy
  snowball from round 300 on, not a banking or opening problem. In losses the opponent clears 2x the camps late
  (rounds 900+: 23 vs 10), takes 12.5 camps a game on OUR side (5.5 in our wins), earns 2367 vs 1530 gold by round 600,
  and stacks Bruiser (130 shards a game vs our 4). Our three gate opponents are our own lineage and do not invade like
  this, so defence features cannot show a gain on them. The PC is building a ladder-like sparring partner (an x3
  build that invades with a Bruiser item plan) and checks it reproduces the loss pattern before testing fixes on it.
