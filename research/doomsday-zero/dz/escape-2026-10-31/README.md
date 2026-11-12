# Certified recovery execution — 2026-10-31

Unpromoted correctness repair; selected defaults/holdout are unchanged.

Prior layered-B deaths had repeated retreat re-entry/oscillation at low HP. Code
inspection found ordinary Home/Retreat movement bypassed neutral move admission,
and hidden-camp hazards disappeared after one damage-free turn despite an active
recovery latch. The old trace lacks exit coordinates, so it does not prove which
individual move substituted for a planned route. Prior positions are retained.

Implemented frame-local certified first-step execution before optional actions
or generic movement scoring; neutral, checked siege and formed crew exits use it.
A fresh blocked certificate never falls through to an unrelated Home path. A
still-valid previous escape ray is rechecked against current hazards/occupancy
before reuse. Recovery retains uncertain hazards until full healing. Ordinary
recovery/home movement has a separate non-worsening exposure mask, preventing
safe cells from re-entering awake camp range. Enemy retreat retains its existing
trade-off unless neutral recovery is active; general combat remains unfinished.

All16 host suites passed; the added death-geometry, exact-step, retained/blocked/
budget-truncated ray and withdrawal checks were separately compiled/run in the
siege suite. Final02 native banks72/84 on crew and240/42 on layered (collected
423/407), with ZERO deaths/faults/fuel-outs across all four cells. The recorded
ordinary layered-B commands match27/27 next-turn native positions. This is narrow
execution coverage, not a general survival claim. Layered-only01 strict audit
passes40/18 cycles. Final02 has the same passing layered rows; its mixed overall
result remains FALSE because ordinary crew cells have no siege cycles. Reports
and both capsules/six cells verify unchanged.

Banking is WORSE than the prior layered325/108. Do not promote or scale screens.
Next Z8/Z14: separate physical altar reachability from the ability to survive a
submission channel. Current altar_open/altar_access model occupancy/path, while
siege_goal(...altar>=0) can stop cuts when a physical path opens. Add endpoint
exposure, actual bag/channel time, HP/shield/exit and uncertainty to delivery
access; identify remaining threatening camp cuts and integrate them with opening
value and banking commitments. This is an identified modelling gap, not a proven
explanation for all missing banking. Preserve the carrier deadline and checked
execution. Then reduce agreement overhead and finish joint ability/combat/action,
progression and opening/map integration. SafeMode's independent emergency path
and broad conformance remain open. No competitive/validation/release or online
activity. Selected Mac437f91c3/Windows5cf28cb7 unchanged.
