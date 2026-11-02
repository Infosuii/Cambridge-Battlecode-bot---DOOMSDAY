# Problems and solutions (2 Nov 2026)

Sources of the problems: research/x1/TOP_TEAMS_2026-11-02.md (35 games vs ranks 1-5 + QS2isLaw + 0xDEADBEEF, 3 wins),
the x1 audit (branch research/x1-audit-2026-11-02, ishanp765: 35 replays, 20 reproduced exactly), and the J005
branch farm (5060, partial: 6,188 branches, all prefix-exact). Every solution is a switch in bots/x1 (off = x1
exactly, hash 1746f2bb7fa3) and goes through the retry protocol (RETRY_QUEUE.md).

## The four problems

| # | Problem | Evidence |
|---|---|---|
| P1 | **Slow collection** | 68% of the audited loss deficit; top teams ~2x our gold by R500, bank 1,000 by ~R700 vs ~R900; dunes R431-471: 0 vs 177 collected while our five wait / stage |
| P2 | **Feeding** | 9/35 top-team games: 23-48 deaths, almost no kills, < 100 banked |
| P3 | **Bags lost / not converted** | single deaths losing 85-154 gems; 308-531 lost per game on three maps; cuts ends 859 banked + 170 carried vs 1083 |
| P4 | **Retreat / farm oscillation** | audit F01: flee, return to the same camp target, flee, ... until death (cuts, galaxy) |

## What the branch farm says (J005 partial)

Switching the whole team to **plan 4 (turtle: own half, aggression x0.65)** mid-game turns the most losses into wins
(net +20 from R150, +27 from R250) with 2 fewer deaths and *more* gold at R500; **plan 6 (early-contact answer)** +17
from R150; push (plan 8) and hoard (plan 2) are the worst. **x1 is over-aggressive** against v88; fewer, better
fights raise the economy too (deaths cost 60 rounds of production and 100 gold to the enemy).

## Solutions

| Problem | Solution | Switch | State |
|---|---|---|---|
| P2, P1 | Play less aggressively all game: plan 4 / plan 6 from R0, R100, R150 | `X1_PLAN=1 X1_PLAN_ROUND=r X1_PLAN_ID=4/6` | J009 (5060) |
| P2 | Team plays safe after K deaths in W rounds | `X1_ANTIFEED` | quick screen 44 vs 36; J006 |
| P3 | Bank now with a big bag when an enemy was seen near | `X1_BAGRISK` | quick screen 50: 20 vs 17, banked +6%; J008 |
| P3 | Win-now counts the team's carried gems | `X1_TEAMWIN` | quick screen 20 vs 17; K002 (5070) |
| P4 | Keep away after a flee | `X1_FLEEHOLD` | quick screen 8: 15 vs 17 (retry 4 / 15); K002 |
| P4 | Drop the fled-from camp target, skip it N rounds (the audit's actual mechanism: the target survives the flee) | `X1_FLEEDROP` | quick screen running |
| P1 | Waiting at respawning camps costs more (go elsewhere) | `X1_ECON X1_WAIT_MULT` | quick screen running |
| P1 | Give up staging for helpers sooner | `X1_ECON X1_STAGE_MULT` | quick screen running |
| P1 | Take more camps alone | `X1_ECON X1_NEED_MULT` | quick screen running |
| P1 | Score camps the pruner dropped before their later bonuses | `X1_PRUNEFIX` | quick screen 21 vs 17, deaths -19%; K002 |
| P1 | Camp danger beyond 12 members | `X1_SOAK64` | quick screen 19; K002 |
| P1 (structural) | **Team camp schedule**: camps with respawn timers are a team orienteering problem with time windows (TOPTW). Plan whole-team camp sequences on spare fuel (hill climber with a shift buffer, Tribes 2.1), each body's next job = first step; claims via the 8-byte protocol | P3 planner | after the knob results; the knobs above tell which costs are wrong first |
| P2 (structural) | Plan selector from the farm: switch to plan 4/6 on positions where the farm says it wins (deaths so far, kills so far, gold gap at R150/250) | phase 4 | after J005 |
| all | Sparring stand-in that farms us (v88 never does) so P2/P3 show up locally | 5060 proposal | after J003 |

## Research notes

- Team orienteering with time windows (TOPTW) and its multi-agent, congestion-aware variants are the standard
  models for picking reward nodes with travel times and windows; congestion-aware multi-agent versions (agents
  queueing at crowded nodes) match two of our champions waiting at one respawning camp.
- Rollout / pilot methods and MCTS are the usual way to improve a greedy schedule with lookahead under a compute
  budget, which is how a fuel-limited team planner should work (greedy x1 choice as the rollout policy).
- Hysteresis / commitment on mode switches (EA paper item 3.12) is the general fix class for P4; FLEEDROP and
  FLEEHOLD are two forms of it.

Sources: Chen, Cheng & Lau, *Multi-agent orienteering problem with time-dependent capacity constraints* (WIAS 12,
2014); *The cooperative orienteering problem with time windows* (Optimization Online); Granda Chico & Vitoriano,
team orienteering with variable time windows (2024); Gama & Fernandes, *RL for the orienteering problem with time
windows* (C&OR 133, 2021); Runarsson, Schoenauer & Sebag, *Pilot, rollout and MCTS methods for job shop
scheduling* (arXiv 1210.0374).
