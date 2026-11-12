id: J006
title: full gate for X1_ANTIFEED (new anti-feeding rule; first promising quick screen)
commit: 846e8ce on build/z-plan (bots/x1; off build = 1746f2bb7fa3)
bot: x1
run: gate (tools/x1_gate.sh), one gate per line
opponents: x2 x2-s2
maps: ladder styled (maze when it exists)
priority: 1 (right after J005, before J002 / J003)
switches:
  af3:      --set X1_ANTIFEED=3
  af4:      --set X1_ANTIFEED=4
  af5:      --set X1_ANTIFEED=5
  af7:      --set X1_ANTIFEED=7
  af3w100:  --set X1_ANTIFEED=3 --set X1_ANTIFEED_WIN=100
  af3w250:  --set X1_ANTIFEED=3 --set X1_ANTIFEED_WIN=250
quick screen (PC, 19 ladder + 19 styled vs x2): K=3 22+22, K=5 22+22 vs base 17+19; deaths -10..-13%.
done when: g5060/results/J006.md: per line and cell wins vs the J003 base gate (or x1e-cw-*-x2 for x2), deaths per
game, gold@R250/R500, finish round, fuel-outs; verdict by the gate rule.
