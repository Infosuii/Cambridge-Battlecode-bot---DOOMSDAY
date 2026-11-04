# Decision memo: next RL intervention (strategy lead, JOHNDOE #118)

Date 2026-11-04. Evidence: `decomposition.json` (tools/rl_env_1104/strategy/decompose.py), 578 distinct finished local
games (516 development-map, 62 training-map; reserved confirmation maps excluded), official engine statistics. Every
team row satisfies submitted = collected − lost − held exactly (max error 0).

## What decides games (measured)

| component of the score margin (ours − theirs) | share of margin variance, all | training maps only |
|---|---|---|
| camp-gem collection | **0.85** | 0.73 |
| gems taken from / lost to champion kills (a transfer; enters both teams) | 0.09 | 0.14 |
| gems lost to camps (deaths to monsters) | −0.01 | −0.01 |
| gems held at the end (not banked) | −0.02 | 0.01 |

- The winner collected more camp gems in 91% of games: +388 gems, +9.5 clears, +2,270 earned gold on average.
- Camp collection splits about evenly: number of clears carries 43% of its variance, gems per clear 57%. Gems per clear
  is target value and selection.
- The collection lead builds late: winners reach half their final camp-gem lead at 69% of the game (median; IQR
  49-80%). Late-game target choice and respawn timing matter, not only the opening.
- Banking/carry (gems held at end, gems lost to camps) explains ~0 of the margin in this data.

Caveat: most of these games are v92-family bots vs v92 or Agent 2 native. Opponent diversity is low, so the same
decomposition must be run on the decoded live replays (#113/#117) before final weighting. It is cheap and must not be
used to fit policies to those losses. Big World (0 deaths, lower collection) matches the dominant pattern.

## Top recommendation: economy target selection with a dense, legal collection signal

All our learning attempts so far (gate, head, native query, upper trunk; ~1.3k training games) acted on the right
boundary, the farm-target choice, which is exactly where 85% of the margin is decided. They stayed within noise of
native for two reasons we can fix:

1. **Credit assignment.** The reward was terminal win/loss over ~2-5k decisions per game, with a ~0.5% departure rate.
   The engine logs each body's camp-gem collections with round timestamps (gemCollection events), which is a dense
   signal that carries 85% of the margin variance. It is legal to use as a training reward, never as an actor input.
2. **Action support / value.** Half of the collection gap is gems per clear, i.e. which group. The native pointer
   scores only the 10 nearest groups plus "far"; on maps with more groups (71/86 have > 10, median 19.5) the high-value
   choice can be out of support (JOHNDOE's GLOBAL_OBJECTIVE_HYPOTHESIS).

Design sketch (to be developed in depth next):
- **Actor:** JOHNDOE's in-place native-query/upper actor, unchanged at runtime (it already has high coverage, ~native
  fuel, and bit-exact replay). Training first; action-support widening comes second, as its own ablation.
- **Reward:** per-body, per-decision-interval camp gems collected (attributed to the body that collected), discounted
  over a horizon of ~100-200 rounds, plus the terminal team outcome. A GAE critic or JOHNDOE's validated prior-round
  value baseline supplies variance reduction. Report both terms; the terminal term guards against reward hacking
  (e.g. farming cheap groups while losing the race).
- **Teamwork:** credit per body over-rewards colliding on the same group. Use the team's collection in the interval as
  the shared term, plus the per-body term with a small weight, so overlap is discouraged.
- **Budget:** the same 32-game cycles as #108-#116, training maps only, both sides, v92 + native opponents. At least 5
  cycles (160 games) before one scheduled development checkpoint.

**Falsifiers** (stop or redirect if):
- after 160 training games the trained actor does not raise camp gems collected per game vs its own initial policy on
  development (paired, family-clustered CI excluding 0), or
- collection rises but win rate vs v92/native does not move at all: the dense signal is misaligned and the terminal
  term must dominate, or
- offline, the dense reward is not predictable from the actor's inputs better than a constant on held-out families
  (cheap to check first, with JOHNDOE's existing value-trial machinery).

## Strongest alternative: contact/fight verdict (JOHNDOE's current direction)

Champion-kill transfer carries 9-14% of the margin. That is real and the second-largest component, but it is a
smaller target. The shadow prototype's runtime cost already hurts vs native, and it does not explain Big World-type
losses.

**What would make it the top choice instead:** the live-replay decomposition (diverse, stronger opponents) shows
champion transfer carrying a much larger share than here; or recommendation 1 is falsified on the economy signal.
**Falsifier for the alternative itself:** if a no-cost shadow version cannot predict fight outcomes better than v92's
own heuristic on held-out families, training it will not help.

## Deprioritized

Banking/carry timing: ~0 share of the margin in local data. The Line's large bags at death are real but rare across
578 games. Revisit only if the live-replay decomposition disagrees.

## Next outputs (strategy lead)

1. Run the decomposition on JOHNDOE's decoded live replays, reported separately, no fitting.
2. Offline learnability check of the dense reward (falsifier 3) on existing training shards.
3. In-depth design doc for recommendation 1: reward attribution code against engine events, horizon, critic,
   overlap term, admission/fuel (unchanged actor), and the evaluation protocol with stop criteria.
