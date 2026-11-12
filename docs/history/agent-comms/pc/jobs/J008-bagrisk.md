id: J008
title: full gates for X1_BAGRISK (new: bank now with a big bag when enemies are near)
commit: 2636803 on build/z-plan (off build 1746f2bb7fa3)
bot: x1
run: gate (tools/x1_gate.sh), one gate per line; opponents x2 x2-s2; maps ladder styled (maze when it exists)
priority: after J006
switches:
  bag30:  --set X1_BAGRISK=30
  bag50:  --set X1_BAGRISK=50
  bag80:  --set X1_BAGRISK=80
why: x1 audit loss cases (research/x1-audit-2026-11-02/LOSS_CASES.md): single deaths lost bags of 85-154 gems;
  showdown / gemcombat3 / fan lost 308-531 carried gems in one game.
done when: g5060/results/J008.md as J006 (wins vs base, deaths, gold@R250/R500, finish round, fuel-outs, verdict).
