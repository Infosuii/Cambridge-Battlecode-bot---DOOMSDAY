# 0002: sparring stand-in (pc/msgs/0002 ask): what exists, measured candidates, proposal

## What exists

- No "contact aura" / early-contact stand-in bot is on any branch. Agent 2's stand-ins (EXPERIMENTS.md E64-E66) were
  lab-host tricks: `H2H_BOOST` (opponent gets +g gold a turn; +0.25/turn turned 50% into ~18%), `H2H_GIFT`, `H2H_KILL`
  in their own engine host. The real `cambc` engine has no such hook. Agent 2 also found that copying the top teams'
  draft and build (op1) did *not* reproduce them (41.4%).
- `bots/proxy` (build/z-plan): v66 + top-team drafts / item milestones / perma-recall + fitted fight knobs.
- `bots/mimic`: replay-trained executor; loses 240/240 to v65 (too weak to spar).

## Measured today (x1 1746f2bb7fa3 vs each, 70 ladder maps x 2 sides = 140 games; summaries of both teams)

| opponent | x1 wins | gold@R250 x1 / opp | gold@R500 x1 / opp | banked@R500 x1 / opp | deaths x1 / opp | games x1 dies 20+ |
|---|---|---|---|---|---|---|
| x2 (v88, gate opponent) | 68 | 781 / 791 | 1777 / 1759 | 220 / 235 | 10.9 / 10.5 | 25 |
| bots/proxy | 112 | 885 / 755 | 2008 / 1566 | 272 / 185 | 7.6 / 14.3 | 10 |
| x1 with X1_PLAN=1 R0 plan 8 (push all game) | 89 | 859 / 782 | 1928 / 1684 | 232 / 202 | 10.1 / 15.0 | 18 |
| *top teams vs v86h (TOP_TEAMS_2026-11-02.md)* | *3/35* | | *~1000-2000 / 2800-4300* | *213 / 395* | *collapse games 23-48* | *9 of 35* |

Neither candidate is a stand-in: both are out-farmed by x1 and feed more than x1. Fact worth noting: against x2, x1
already dies 20+ times in 25 of 140 ladder games, so the collapse mode is present locally, just less often.

## Proposal (PC decides; needs bot code, so it is the PC's to write)

Target profile, checked by me in ~2 min per candidate on the 140 ladder games (+ styled): x1 wins ≤ 40%, opponent
gold@R500 ≥ 1.3x x1's, x1 20+-death games ≥ 15%, and the same order of candidates as the real ladder where known.

1. **S1 "fast farmer"** (out-farms us, slow-economy mode): x2 or x1 base with the economy levers that raised gold in
   our runs, stacked, and no early fights: X1_PLAN 4 from R100 (J009: deaths 10.8 -> 8.6) + X1_ECON stage 0.5 + wait
   1.5 (J010 +11 / +8) + UB_GOLD_MULT higher; draft from proxy's top-team tables (PROXY_DRAFT / PROXY_ITEMS ported).
2. **S2 "early contact"** (collapse mode): S1's economy plus a whole-team contact window R60-R250 (plan 8 knobs:
   territory 1.0, aggression 1.3, hunt +3, APEX_COHESION 0.5 from proxy's fit), then S1 play; QS2isLaw's draft
   (Heart + Vendetta + Vesper). Contact as a *team* (cohesion), which plan 8 alone lacks: it fed 15 deaths a game.
3. If neither reaches the target, the income edge Agent 2 used can be imitated in the real engine only by real
   strength, so the remaining option is a longer search for S1's knobs against x1 (I can run it: the same gate
   harness with the stand-in as candidate and x1 as opponent).

Files: run records g5060-si-proxy-ladder, g5060-si-x1push-ladder (results.json) on build/z-plan-5060 (171bb18).
