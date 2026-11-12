# Moment review: event labels and surrogate ceilings

105 prediction-first cards cover 90 moments from 65 distinct examined losses and 15 control wins. Exact actor-own observations and conditional rule expectations were committed in b490a1d before the subsequent action extractor ran. The 65 loss games span Learn20/Climb30/Other15 and multiple maps.

**Association only.** These overlapping labels describe what happened inside selected model-drop windows. Their shares are selection-weighted surrogate ceilings for further review; they are not avoidable win rate, causal regret, or a proven fix ceiling. Labels can overlap and sum above100%.

| Event label | Loss moments /90 | Distinct losses /65 | Share of selected surrogate drop | Control-win moments /15 |
|---|---:|---:|---:|---:|
| Opponent purchase in the swing window | 79 | 58 | 81.8% | 11 |
| Opponent camp gem receipt in the swing window | 63 | 51 | 70.5% | 9 |
| Opponent bank in the swing window | 36 | 29 | 44.0% | 7 |
| Our native death in the swing window | 23 | 22 | 28.2% | 5 |
| Our native gem loss >=40 in the swing window | 12 | 12 | 17.1% | 3 |
| Registered D3 repeat death in the swing window | 2 | 2 | 1.9% | 0 |
| None of the six event labels above | 1 | 1 | 0.7% | 1 |

The V75 lone-guard public prerequisites hold in 9/105 pre-window focus observations. Enemy-target actions later appear in cards ['C004', 'C018', 'C030', 'C034', 'C048', 'C070']; neither a cast nor an attack proves the guard was bypassed, because the one-turn-kill exception, flee weaving and exact target/risk branch require traces.

The frozen source defaults disable V75_BAG; a high-bag fighter is not automatically violating that rule. Effective map/lab values and compiler overrides remain unverified against the server build. This avoids interpreting every surprise as a bug.

MATCHED_CONTROLS.json supplies nearest-state own-win and top-winner examples, observed follow-up actions/events and caliper coverage. Controls were chosen among winners, can repeat, and retain draft/opponent/memory confounding. Similar state and a different outcome do not establish a better decision.

Full local contexts preserve each selected actor’s turn-start own view over the expanded window and every recorded focus action. Cards are capped at25 lines; error_analysis.csv has one row per card. Hand auditing, exact reproduction and effective-rule traces are the next gate before marking these event labels as mistakes.
