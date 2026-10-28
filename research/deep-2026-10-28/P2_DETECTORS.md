# Session 1 detector status

**Replay intake complete; detector implementation/validation is next. No detectors have been accepted.**
Reconciled pairs n=555; accepted study n=550 (385 examined,165 hands-off), plus five calibration-only games.
Loss-versus-win detector-rate denominators remain n=0/n=0 until detectors are validated and run.
There are no valid rates, intervals, example rounds or causal bug candidates yet.
Native-summary internal checks are not independent replay reconciliation.

The next implementation must build on the pinned engine 2 loader and existing
still_runs/death_context/respawn_delay/fuel_outs/home_trips/capture_funnel/
capture_pressure/tp_effects tools. Validate each event and perspective definition
against the official engine before estimating rates; keep hands-off outputs unopened.

| ID | Required signal | Key validation |
|---|---|---|
|D1|alive, no move/attack, not channelling|exclude death, recall, bank and channel turns|
|D2|long high bag without bank attempt; gems lost at death|native gem identity, attempt vs completion|
|D3|repeated spatial/configuration deaths|rounds/positions/foe composition, dynamic roster|
|D4|repeated target/mode alternation|replay movement proxy must not claim hidden mode|
|D5|capture attempts, resets and enemy rewards after clearing|separate clearing, progress and reward owner|
|D6|dead/empty camp waiting and blocked spawn tiles|official respawn/spawn occupancy semantics|
|D7|fuel exhaustion and faults|native fault/events reconciliation by champion|
|D8|blocked altar/gate, failed tribute and locks|legal path/action semantics; map topology|
|D9|hole-island stranding; local1-vs-2 isolation|traversability and actual visible enemy state|
|D10|high unspent gold, late purchases/equipment|count buying while dead; actual item costs|
|D11|deaths after unseen threats; wards by 250|own-perspective visibility over previous 5 rounds|

Thresholds must be registered before examining trajectories, with duration/rate
denominators in champion-rounds and per-game occurrence rates. Report Wilson
intervals for game occurrence plus map/opponent clustering sensitivity; frequency
differences are associations until a valid intervention tests a causal rule.

Do not repeat the historical blanket claim that winners hold spells: the newer
own-perspective cooldown audit did not support it. Historical reports guide
definitions; they are not current-v69 measurements.
