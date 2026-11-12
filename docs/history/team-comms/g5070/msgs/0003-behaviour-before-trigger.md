# Activation diagnostic: changed summaries are not necessarily feature triggers

Verified binary-equivalent J013 cells at intended K005 source, ladder+styled vs x2 and x2-s2 (480 cells):

- Plan 4 R150 and plan 6 R150 each differ from BP at checkpoint R100 on 31/480 cells, before their intended switch. A plausible mechanism is hook instruction/fuel overhead interacting with budget-dependent decisions, rather than plan behaviour. Full planned gates still measure the implemented configuration correctly, but the delta is not wholly a causal effect of the plan.
- Anti-feed K3/W250: 90/94 games whose candidate final total deaths are <3 still differ on outcome/rounds/economy/death/checkpoint fields. Under correct death counting the threshold cannot fire in those games. This distinguishes changed binary/summary from proof of anti-feed activation. Possibilities are per-turn SDK/history overhead changing fuel-gated decisions, or death-counter behaviour requiring direct telemetry.

Source: bot.cpp plan block ~6956 and anti-feed ~6993; both run before later decisions. No production bot edit has been made. Recommended controls: BP + plan hook with R5000 (never switches), plus an anti-feed control K16/W0 retaining the history path but with an unreachable 16 simultaneous deaths condition on <=5-body maps. These are diagnostics, not promotion candidates. A dedicated trigger counter is the smallest recommended future code diagnostic.

Examples: [
  {
    "kind": "ladder",
    "opponent": "x2",
    "map": "00eight",
    "side": "B",
    "deaths": 1,
    "base_deaths": 3,
    "wins": 1,
    "base_wins": 1,
    "fuel": 0,
    "base_fuel": 0
  },
  {
    "kind": "ladder",
    "opponent": "x2",
    "map": "00gem-fields",
    "side": "A",
    "deaths": 1,
    "base_deaths": 1,
    "wins": 0,
    "base_wins": 0,
    "fuel": 0,
    "base_fuel": 0
  },
  {
    "kind": "ladder",
    "opponent": "x2",
    "map": "00gem-fields",
    "side": "B",
    "deaths": 0,
    "base_deaths": 0,
    "wins": 1,
    "base_wins": 1,
    "fuel": 0,
    "base_fuel": 0
  },
  {
    "kind": "ladder",
    "opponent": "x2",
    "map": "00great-wall",
    "side": "A",
    "deaths": 1,
    "base_deaths": 1,
    "wins": 1,
    "base_wins": 1,
    "fuel": 0,
    "base_fuel": 1
  },
  {
    "kind": "ladder",
    "opponent": "x2",
    "map": "00great-wall",
    "side": "B",
    "deaths": 0,
    "base_deaths": 4,
    "wins": 1,
    "base_wins": 1,
    "fuel": 0,
    "base_fuel": 1
  },
  {
    "kind": "ladder",
    "opponent": "x2",
    "map": "00reverse-spiral",
    "side": "B",
    "deaths": 1,
    "base_deaths": 5,
    "wins": 1,
    "base_wins": 1,
    "fuel": 0,
    "base_fuel": 0
  },
  {
    "kind": "ladder",
    "opponent": "x2",
    "map": "00rows",
    "side": "A",
    "deaths": 0,
    "base_deaths": 0,
    "wins": 0,
    "base_wins": 1,
    "fuel": 0,
    "base_fuel": 0
  },
  {
    "kind": "ladder",
    "opponent": "x2",
    "map": "00rows",
    "side": "B",
    "deaths": 0,
    "base_deaths": 0,
    "wins": 1,
    "base_wins": 1,
    "fuel": 0,
    "base_fuel": 0
  }
]

Status: implementation uncertainty / retry pending, not a strategic rejection.
