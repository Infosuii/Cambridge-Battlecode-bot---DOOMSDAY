id: J010
title: full gates for X1_FLEEDROP and the X1_ECON multipliers
commit: 33c2498 on build/z-plan (off build 1746f2bb7fa3)
bot: x1
run: gate (tools/x1_gate.sh); opponents x2 x2-s2; maps ladder styled (maze when it exists)
priority: right after J009 (before J006)
switches:
  fd25:    --set X1_FLEEDROP=25
  fd40:    --set X1_FLEEDROP=40
  fd60:    --set X1_FLEEDROP=60
  fd15:    --set X1_FLEEDROP=15
  wait15:  --set X1_ECON=1 --set X1_WAIT_MULT=1.5f
  wait20:  --set X1_ECON=1 --set X1_WAIT_MULT=2.0f
  stage05: --set X1_ECON=1 --set X1_STAGE_MULT=0.5f
  need13:  --set X1_ECON=1 --set X1_NEED_MULT=1.3f
PC quick screens (19 ladder maps vs x2, base 17 wins / 326 deaths / 29,893 banked): fd25 22 wins, 249 deaths,
33,007 banked; fd10 15 (269); wait15 19; stage05 18 (293); need13 17.
done when: g5060/results/J010.md, same columns as J006.
