# v109 midgame target / execution attribution (JOHNDOE #148/#149), 2026-11-05

Source: exact live v109 (ZIP c013c216, header 6661d16a, CLFS=1) plus the CLTR trace only (v109_trace_patch/: bot.cpp,
bot.h, main.cpp; one CTR row whenever a body's committed target or mode changes). Engine 3.0.0 (cambc 5.0.0, build
96ce858f), release, 100k fuel. 15 development maps x both sides x 3 opponents (v92, native Agent 2, exact v109) = 90
games, 44 wins. The trace prints, so its timing differs slightly from v109 itself. Analysis:
tools/rl_env_1104/strategy/target_trace.py; machine output V109_TARGET_TRACE.json.

Group join check: in 82% of commitments where the body collected anything, it collected from its committed group,
so the bot's internal group index is the engine's campGroup id.

A commitment = consecutive turns with the same committed target (mode changes inside do not end it). Rounds 300-800:

| what ended the commitment | n | mean rounds | body collected nothing from it |
|---|---|---|---|
| v92 re-scored to another group | 5656 | 27 | 70% |
| native actor override | 929 | 21 | 80% |
| poorer ally took the region | 666 | 26 | 93% |
| death | 529 | 45 | 91% (enemy took ~4 gems from that group per commitment) |

Share of body midgame time by outcome of the commitment:

| outcome | time | commitments | mean length |
|---|---|---|---|
| the body collected from its target | 38.7% | 1963 | 38 rounds |
| **nobody collected from it** | **32.9%** | 3881 | 16 rounds |
| a teammate collected there instead | 21.7% | 1657 | 25 rounds |
| the enemy took it | 6.7% | 306 | 43 rounds |

The pattern is the same against all three opponents.

**Highest-impact failure: target churn in execution, not selection.** A third of midgame body-time goes to camps
abandoned before anyone collects. Most switches come from v92's own per-turn re-scoring (72% of commitment ends),
typically after ~16 rounds of travel. The native actor's overrides are a minority (12%). Teammate collection (22%)
is partly legitimate crewing, since only one body gets the capture.

Next candidate (for whoever owns the policy): commitment hysteresis in farm(). Keep the committed group unless the new
pick beats it by a margin, it becomes infeasible, or a fixed number of rounds passes without progress. Measure with
this exact trace: the "nobody collected" time share should fall, with camp gems per game and wins checked on dev cells.
