# Controlled stationary duel fixture

```
python tools/dz.py conformance --name FRESH --fixture duel --fixture-opponent --map-dir tests/dz/maps --maps isolated-wolf --diagnostic-rounds 160
```

The candidate defaults to Heart, scripted opponent to Varg. Override boolean
DZ_DUEL_HEART / DZ_DUEL_OTHER_HEART for the other combinations. Both teams use
new prescribed basic/reset/shield controllers; no historical opponent code.
Non-subject bodies stay at spawn. Subjects meet on legal adjacent tiles above
the central altar and remain stationary. The actual visible state is quoted.

DZ_DUEL_PRECAST=1 forces a shield at round29 before any quote and begins the
ordinary duel policy at round30. This tests existing-state and duration0 cases.
DZ_DUEL_SLOT / DZ_DUEL_OTHER_SLOT select draft slot0 or1. Equal default ranks
use alternating round lead; differing ranks use a fixed pair order. These
choices only describe this controlled no-priority fixture, not live inference.

Initial, first active-shield and first duration0-defender windows must match
outcome, owner-observed rounds, HP and own accepted attack/cast counts. Missing
or false assertions fail. Truncated native fault totals are not measured;
overlapping windows and side assignments are not independent strength trials.
See research/dz/duel-2026-10-30 for the failed setup/order attempts and limits.
