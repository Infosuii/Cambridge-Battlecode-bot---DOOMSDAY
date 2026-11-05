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

## Follow-up: commitment hysteresis (CL_HOLD 20) and the gold-farming check

- 85% of the "nobody collected" time is on camps that nobody clears at all in the window (6% enemy, 6% teammate,
  3% this body gold-only). So it is genuinely abandoned travel, not gold farming.
- CL_HOLD 20 (keep the committed group for 20 rounds unless it respawns, an enemy is in view, or HP < 50%), engine 3,
  50 training maps x A/B, paired with v109: vs v92 46/100 (0.00, CI [-0.12, +0.11]), vs native 43/100 (-0.05, CI
  [-0.18, +0.08]); fuel-outs 829/932 vs 781/907. **No gain.**
- The same trace on the hold build (30 dev games vs v92): "nobody collected" 33.3% vs 32.9% without it. The hold does
  not reduce the churn. The switches that waste travel happen when its exceptions apply, most likely when enemies come
  into view (v92 reacting to threats) or at low HP, not during quiet re-scoring.
- Implication: the churn is threat-driven retargeting. A fix has to change how v92 responds to visible enemies
  mid-commitment (or let the body finish captures it can safely finish), not add a quiet-time hold.

## Correction (trace v2: enemy count and nearest-enemy distance logged at every switch, 90 dev games)

The "threat-driven" reading above was wrong.
- At wasted switches (camp never cleared) an enemy is visible in 19% of cases, the same as at productive switches (21%).
  The nearest enemy is within 5 tiles at 1%, and HP < 50% at 6%.
- Wasted commitments last a median of **4 rounds** (productive ones 24). They are quick flips: of 1,689 midgame
  commitments of at most 6 rounds, 34% return to the previous target (A->B->A).
  - 46% are v92 re-scoring after v92, mostly in "approach" mode.
  - 32% are native actor <-> v92 alternation: the actor's command applies on turns it runs, and v92's pick reasserts
    on the next turn.
- CL_HOLD 20 did engage (short flips 23% -> 17% of commitments; commitments -14%), yet wins did not move (vs v92 0.00,
  vs native -0.05). So target flip-flopping is real but is not the binding constraint on strength in these games.
