# Major-system interaction matrix

C = mechanically compatible in the audited configuration; P = potentially conflicting; F = confirmed execution conflict in a faithful replay; ? = insufficient evidence. These labels are not win-rate estimates. The three F cells describe one overlapping F01 mechanism, not three independent bugs.

| System | D | P | W | S | G | C | J | O | L | T | E | A | H | B | N | Q | F | M | X |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D | — | C | C | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | C |
| P | C | — | ? | ? | C | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | C |
| W | C | ? | — | P | ? | ? | ? | ? | ? | ? | F | ? | ? | ? | P | ? | ? | ? | C |
| S | ? | ? | P | — | ? | ? | ? | P | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | C |
| G | ? | C | ? | ? | — | P | P | P | ? | ? | F | ? | ? | ? | ? | ? | P | P | C |
| C | ? | ? | ? | ? | P | — | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | C |
| J | ? | ? | ? | ? | P | ? | — | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | C |
| O | ? | ? | ? | P | P | ? | ? | — | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | C |
| L | ? | ? | ? | ? | ? | ? | ? | ? | — | ? | ? | ? | ? | ? | ? | ? | P | ? | C |
| T | ? | ? | ? | ? | ? | ? | ? | ? | ? | — | P | ? | ? | ? | ? | ? | C | ? | C |
| E | ? | ? | F | ? | F | ? | ? | ? | ? | P | — | ? | ? | P | F | P | ? | ? | C |
| A | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | — | ? | P | ? | ? | ? | ? | C |
| H | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | — | P | ? | ? | ? | ? | C |
| B | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | P | P | P | — | C | ? | ? | ? | C |
| N | ? | ? | P | ? | ? | ? | ? | ? | ? | ? | F | ? | ? | C | — | ? | ? | ? | C |
| Q | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | P | ? | ? | ? | ? | — | ? | ? | C |
| F | ? | ? | ? | ? | P | ? | ? | ? | P | C | ? | ? | ? | ? | ? | ? | — | ? | C |
| M | ? | ? | ? | ? | P | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | — | C |
| X | C | C | C | C | C | C | C | C | C | C | C | C | C | C | C | C | C | C | — |

| ID | System |
| --- | --- |
| D | Draft and map selection |
| P | Profiles and lab knobs |
| W | World and personal vision |
| S | Shared claims and events |
| G | Group scoring and pruning |
| C | Campwatch |
| J | Dominant-group jobs |
| O | Camp staffing and capture |
| L | Siege LOS cache |
| T | Tactical combat forecast |
| E | Combat and retreat |
| A | Fight assistance and hunt |
| H | Home and recovery |
| B | Banking and endgame |
| N | Movement and pathfinding |
| Q | Equipment and support casts |
| F | Fuel admission and fallback |
| M | Learned score residual |
| X | Disabled experiments |

All 171 unordered pairs, with explanations, are in [INTERACTIONS.csv](INTERACTIONS.csv). All 617 conditional identifiers/thresholds are in [FEATURES.csv](FEATURES.csv); they are not 617 independent strategic modules. Exhaustive pairwise competitive testing was not performed.

