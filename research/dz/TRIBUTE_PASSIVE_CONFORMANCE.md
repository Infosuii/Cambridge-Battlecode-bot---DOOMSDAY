# Tribute emblem banking effect — 2026-10-29

CT-12's common banking effect is resolved: the Tribute emblem reduces the
**already rounded base channel timer**, with the result rounded up again.
It does not increase banked gems or gold in these controlled cases. Production
does not buy it, and no gear utility or strategy change was enabled.

## Native checks

Ten final campaigns complete 20 native games, both sides, with zero faults or
fuel-outs. Names are `dz-ct12-{tribute,power}-{7,14,21,35,98}-03`.
Separate official-built fixtures supply the larger bags; none are competition
maps or strategy plans.

Vendetta farms the required gold/gems without an item, starts a baseline tribute,
records its timer and cancels immediately. The whole bag is retained and nothing
is banked. It then buys five Tribute strength shards or a matched plain Power
stat item, and starts a second tribute with **the same bag**. Both initial timer
and actual completion rounds are recorded, along with gem and gold transfers.
Companions park, the opponent idles and no actor dies.

| Bag | Base / Power control | Tribute emblem | Banked gems | Extra gold |
|---:|---:|---:|---:|---:|
| 7 | 1 | 1 | 7 | 0 |
| 14 | 2 | 2 | 14 | 0 |
| 21 | 3 | 3 | 21 | 0 |
| 35 | 4 | 3 | 35 | 0 |
| 98 | 10 | 7 | 98 | 0 |

With runtime setting `base = max(minimum, fixed + ceil(bag × multiplier))`
and the emblem magnitude `m = 0.33`, the observed rule is:

`actual = max(minimum, ceil(base × (1 − m)))`.

The order matters: scaling the unrounded `bag × multiplier` would incorrectly
predict one round for 14 gems; the engine takes two. Do not replace 0.33 by exact
one-third: a three-round base remains three. Once submission starts, its live
timer equals further rounds until completion; there is no extra capture-style
initialization phase.

CPP assertions and a separate numeric checker validate all five bag sizes,
baseline cancellation/retention, paid item construction, unchanged bag before
the second start, initial/live duration, full transfer and zero extra gold.
At the current bank threshold of 30, this timer rule implies no speed saving for
a normal bag of 30 or less; larger bags can benefit. This implication is not a
measured strategy/gear-value promotion.

## Calibration and remaining scope

`dz-ct12-tribute-observe-01` (14 gems) and
`dz-ct12-tribute-observe-large-02` (98 gems) collected the initial phenotype.
Their conformance gate deliberately stays failed because the effect was not yet
asserted; they are preserved as calibration observations. The final 03 suite
asserts the derived rule and adds matched controls and additional bag sizes.
These deterministic reruns are not independent strength samples.

Only one emblem, a healthy uncontested actor and the current pinned banking
settings are covered. Duplicate-family stacking, other heroes/items, damage,
stun/lock interactions, death and altered settings remain outside this fixture.
The broader G0 suite, full SafeMode and objective/gear-model calibration are still
incomplete. No map tuning occurred.
