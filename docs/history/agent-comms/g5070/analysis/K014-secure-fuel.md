# K014 row 14: cheap securing still changes fuel exhaustion

Native Linux, unchanged x3 source at 9c1bbde, all lines on `X1_MAPFIT=1`. This is diagnosis of completed required screens, not a new candidate or an accepted improvement.

| Line | Wins/172 | Fuel-outs | Deaths/game |
|---|---:|---:|---:|
| Own mf baseline | 96 | 171 | 11.994186 |
| SECURE MULT=3 | 96 | 181 | 12.151163 |
| SECURE MULT=1.5 | 96 | 180 | 12.116279 |
| SECURE MULT=6 | 97 | 181 | 12.139535 |

`X1_SECURE` only multiplies target worth when existing ttk<=1; it does not add G3's target-centered Lanchester rescans. Yet its extra exhaustions concentrate in 01yellow-brick-road A: baseline 4, all three securing variants 13. MULT=3 adds another exhaustion in 03colosseum A (0 ->1), where the outcome also flips from win to loss. See K014's per-run comparison JSONs.

On 01yellow-brick-road A, native summary counts were reconciled against step-kind-26 events in the existing raw replays (4 baseline, 13 MULT=3). Baseline Heart of Ruin exhausts once at R511. MULT=3 Heart exhausts at R503,570,693,710,712,714,876,878,880,884 (10 times). The other three bodies' exhaustions account for the remaining 3 in each run.

At R710/712/714 the variant Heart remains at (25,12), with nearest enemy at Chebyshev distance 1, and HP 5645.60/5393.60/5141.60 of 6200. Its recorded same-round steps preceding exhaustion include no basic attack (kind5), cast (kind6), ordinary move (kind4) or dash movement (kind23). R876/878/880/884 repeats this failure at (26,12), again one tile from an enemy. This establishes an important action-starvation symptom. It does **not** identify the internal computation stage; replay actions do not log time spent in C++ helpers.

Three of the Heart exhaustions have the nearest omniscient enemy farther than 8 (R503 distance14; R693 distance16; baseline R511 distance9). A start guard inside a kill-coordinator alone cannot be assumed to prevent every exhaustion induced by its changed routes/state.

Implication for K013: do not attribute G3's +14–15 exhaustions solely to pow/exp overhead, and do not claim a cheaper forecast solved fuel regression without full paired counts. Preserve a >=60k admission guard for new coordination, then inspect stage-specific worst-case reserve and essential-action ordering if newly chosen paths still exhaust. Default-off behavior and existing required gates remain mandatory.

Compact diagnostic JSON: K014-secure-fuel/context.json. Raw replays remain local. The event x/y fields in the official fuelExhausted summary are (0,0) placeholders here; positions above come from pinned replay snapshots, not those summary placeholders.
