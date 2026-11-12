# Group visibility: one spawn tile

Four completed native diagnostics, both sides, engine 2.0.0 / SDK 4.0.0:

| Run | Controlled order | Evidence per side |
|---|---|---|
| dz-ct10-single-spawn-01 | Visible member defeated last | 89 alive, 6 reward, 17 cooldown observations |
| dz-ct10-single-spawn-first-02 | Visible member defeated first | 44 alive with visible member alive, 44 alive with visible member defeated, 6 reward, 17 cooldown observations |

The observer sees exactly one of twelve gold-cluster spawn tiles. Other allied
bodies park far away. A scripted enemy clears and captures the group. Five
reward-phase samples per side have a hidden enemy capturer. Both state() and
capture_state() remain readable throughout. The enemy receives exactly 240 gold.
Visible camp health reads 120; the hidden member's health query rejects with 97.
All four games have measured zero native faults and fuel-outs on both teams.

The first-order variant forces the observer-visible endpoint to die before the
other members. This distinguishes visibility of a spawn tile from visibility of
a live camp identity: forty-four samples still report group alive while no live
member is visible. Production memory must continue using spawn-tile visibility
to decide whether a defeated member can be observed. An empty visible live-camp
set cannot imply that all group members are defeated.

The map is separate from the competition pool, SHA256
1155b1eedfc8ecc941a943e5c1eabbef315c268a543b785aa0243cf11ebcaca6.
Frozen sources, binaries, runner, official summaries and native replays are in
each run's evidence.zip. Checks require the single-spawn boundary, all state
phases, hidden capturer and actor receipt. The first-order variant additionally
requires at least five alive-group samples with the visible member defeated.
The measurement unit test rejects missing coverage and actor receipts.

Scope: an open map, twelve harmless members, one observer and one capturer.
Bush/ward visibility, completely unseen groups, shared vision, channel-time
queries and combat occlusion remain separate questions. No production change
or strength claim follows from these diagnostics.
