# Post-registration implementation correction

Discovered during Session 2 card/action auditing, after the first examined screen.
Registered thresholds and predicates in DETECTOR_SPEC.json are unchanged.

The pinned official engine-2 viewer exports its step labels as `PanelChrome.L`:
4 Move,9 Set priority,15 Consumable,16 Cancel channel,20 Place altar lock,
21 Teleport channel,22 Teleport complete,23 Movement blocked,25 Sell item.
The original detector used `[4,22,23]` as movement. A blocked destination is not
an arrival, even when its from/to fields differ. It now uses only `[4,22]` with
different endpoints. Two semantic cases check blocked movement and teleport
completion, bringing that test to 15 cases.

This corrects implementation of the preregistered physical-arrival predicate;
it does not select a new threshold from the outcomes. D1/D4/D6/D9 and movement
denominators must be regenerated. D3 uses native deaths, D2 native loss/bags,
D5 captures, D7 native fuel/faults, D8 banks, D10 gold and D11 actor vision; those
event sets must agree before/after. Preserve the earlier local runs as audit data.

The timeline action log now includes priority, consumables, channel cancellation,
altar locks and teleport starts, and marks blocked steps unsuccessful. Card
labels for 22/23/25 are corrected. Resource states, actual position-based time
proxies and all registered model feature vectors must be compared across the
two timeline runs before reusing the fitted model. No model selection or test
tuning is authorized by this correction. Pre-action card predictions remain
the immutable b490a1d artifact; only subsequent action extraction/labels change.

The official label is “Turn rollover” for26. Its correspondence to native
fuelExhausted is empirically checked per actor/round in every calibrated and
examined replay, rather than inferred from that label. No generic rollover is
claimed to imply exhaustion outside these verified inputs.

Current corrected calibration source hashes:

- detectors: `5052f2452b3937df587d65800edf0fe8d80a18ef6039e35cf56e3dbca062706a`
- timelines: `3d7291505476e6e71dd82922955223b98951a4e0fb9bacff59c985bee45e5b7f`

Both pass all five calibration games before rerunning the 385 examined games.
No hands-off processing occurred. CORRECTION_VALIDATION.json records the completed
cross-run comparisons when available; older claims about affected rates are
superseded by the corrected P2_DETECTORS.md.
