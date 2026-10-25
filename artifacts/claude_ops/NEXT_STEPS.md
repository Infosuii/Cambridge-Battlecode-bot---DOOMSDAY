# Next steps (state at commit d9e62bc, 2026-10-25)

## Done this round
- Fuel: movement no longer starved (combat_has_choice fix, fail-closed movement builds, cold-field guard, macro
  reserve 20k, typical-cost admission for move/combat/objective, 12-candidate movement cap, hoisted per-row work).
  Gate passes on all 6 selection maps (0-2 fuel exhaustions, 0 faults). All-off build byte-identical.
- Behaviour: champions were holding forever. Causes found and fixed: training goals did not match runtime goals
  (now the runtime's goal rules for the hindsight intent, 150-round farm horizon) and far goals collapsed to hold
  (distance-offset augmentation in policy_bc.py). Hard-coded anti-stall (movement) and anti-passivity (combat) rules.
- Best model: artifacts/runs/bc-v6/export (1,200 ranked replays, winners only, distance augmentation).

## Where it stands
0 wins vs heuristic-v1 in 24 games. Champions now move and hit camps (~1-2.5k camp damage each vs the opponent's
20-70k), but they rarely collect or bank gems and die a lot. Remaining limits: 1,056-parameter model (fuel-bound),
approximate replay features for bot-internal inputs, ~20-35k fuel per movement decision.

## Options (a direction decision)
1. Keep pushing the pure neural bot: more rule layers (bank/deposit, retreat when low HP), more data, per-head
   tuning. Incremental; a long way from heuristic-v1's level.
2. Hybrid: the strong heuristic bot keeps tactics (movement, combat, farming); neural heads only take the decisions
   where replay data can beat the hand-written logic (draft, strategy/objective choice, shopping). Needs a
   per-head teacher fallback in C++.
3. Data-driven heuristic upgrades: analyse what top-rated teams do (item builds, timings, farm routes, banking
   thresholds) in the 245k decoded replays (or newer ones via `cambc matches` if the CLI is logged in) and apply
   it to the heuristic bot.
