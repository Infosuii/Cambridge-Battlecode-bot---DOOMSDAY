# Solo capture timing — 2026-10-29

**Configured capture time is not the full wait from new physical entry.** Four
complete native games, both sides of the separate reward fixture, establish the
initialization phase explicitly. All assertions pass with zero native faults or
fuel-outs. Production is unchanged; objective-model decisions remain disabled.

`dz-capture-timing-emblem-01` buys a Capture strength emblem after the first gold
group. `dz-capture-timing-control-01` buys a plain Power strength emblem. Both
record five capture episodes per side: a 12-member gold group, one/two-member
gem clusters, a single gold cluster and a wolf. Companions park; capture is solo
and uncontested. Twenty episodes are recorded in total.

The probe records the earliest **physical eligibility**: all members known dead
and the actor on any group spawn tile, including after its own attack/move in
that same turn. It verifies the actor stays on-site until receipt and records
every SDK capture timer/status. This avoids hiding a movement turn in the timer.

| Situation | Entry-turn SDK state/timer | Later active timers | Entry-to-reward rounds |
|---|---|---|---:|
| No Capture emblem | capture_available / 5 | 5, 4, 3, 2, 1 | **6** |
| Capture emblem | capture_available / 5 | 3, 2, 1 | **4** |

For example, control gold entry R40 yields reward R46. Equipped single-gem
entry R69 yields reward R73 on side A. The first following capture phase
initializes the timer; it does not also decrement it. Once the SDK reports an
active timer N, the reward arrives N further rounds later in these cases.

The pre-initialization value remains 5 even with the emblem. An evaluator must
distinguish `capture_available` from `ally_capturing`, and must read the proposed
capturer's item, rather than interpreting that uninitialized 5 as its actual
configured duration. A new uncontested solo arrival needs configured time +1;
an already initialized countdown must not receive another initialization charge.

This also matters when composing clear time: attack **count** and elapsed attack
rounds differ by one, and melee/ranged movement can overlap differently with the
last attack. Do not stack component offsets without measuring the full episode.

These tests do not establish mixed capturer item ownership, capture after a
contest, interrupted departures, death or late-arrival race behavior. Earlier
CT-24 fixtures cover split/contest/occupied camp respawn separately. The future
objective input should preserve capture status as well as its timer; the current
simple ledger's timer alone is insufficient for a complete model.
