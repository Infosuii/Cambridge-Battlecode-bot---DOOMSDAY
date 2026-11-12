id: J005
title: branch farm on the x1 team-plan hook (phase 3)
commit: e15b68d on build/z-plan (or later)
bot: x1 with --set X1_PLAN=1, plus per build --set X1_PLAN_ROUND=<r> --set X1_PLAN_ID=<p>
run: farm
priority: 2 (start right after J001; runs alongside nothing else)
design:
  - Baseline build: X1_PLAN=1 X1_PLAN_ROUND=5000 X1_PLAN_ID=6 (never switches; a non-zero id is required so the
    baseline shares the branches' code section). Check: every build's wasm code section (section id 10) sha256 is
    be66c8804ef0... (tools/lab/branch_farm.py on lab/box has code_sha()).
  - Branches: plans 1-8 x rounds 150, 250, 350 = 24 builds. Plans: 1 full map, 2 hoard, 3 fight harder, 4 turtle,
    5 stricter home, 6 early-contact answer, 7 fast bank, 8 push (bots/x1/src/bot.cpp, X1_PLAN block).
  - Opponents x2 and x2-s2; maps: 70 ladder + 50 styled (maps/x1-unseen) + maze set once J004 lands; both sides.
    About 480 baselines + 11,500 branches before maze maps.
  - Reuse tools/lab/branch_farm.py from lab/box (adapt the define names on build/z-plan-5060): it skips branches at
    or after the baseline's last round, orders work so a partial run is a balanced sample, and keeps one row per game.
  - Check prefix identity on a sample (tools/lab/branch_prefix.py): branch games must equal the baseline before the
    switch round. If not, stop and post a message.
  - Order: baselines first; then round 250 (all plans), then 150, then 350.
done when: g5060/results/J005.md with, per plan and round, branches that turn a baseline loss into a win and a win
into a loss, mean banked margin change, by map kind and opponent; plus g5060/results/J005/rows.jsonl (one row per
game: map, side, opponent, round, plan, outcome, banked, opp banked, finish round, deaths, fuel outs, and the
baseline position features at each switch round). Post partial results every 3 hours.
