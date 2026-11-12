# Final fuel evidence

The production runs use the official100k ordinary quantum,200k first-body turn and10M first draft. The inherited
same-engine probe is preserved in INHERITED_fuel_contract.json. Fresh runs record engine2.0.0/build85aa7167...,
map hashes and actual seeds; paired identities match. No relaxed-fuel score is used.

## Uninstrumented selected candidate (CPG)

Final confirmation:803 engine fuel-exhausted events versus1532 for v92 across2232 games per arm (47.6% reduction).
This does not mean every individual map-side improved. The baseline already suspends; zero baseline was never assumed.
No new bot faults or official diagnostic codes. Silent SDK false-return actions are not separately counted.

On the96 development conformance cells reused for the profiler comparison, the actual unprofiled CPG ordinary-turn
fuel trace has440157 observations: p50=57256,p95=78508,p99=86322,max=100000,31 suspension events. These are measured
quantiles, not a proof of a universal worst-case bound. The core baseline still has suspending paths.

## Diagnostic perturbation

The profiler build on the same cells had432667 observations: p50=66169,p95=84848,p99=91600,mean60111.8 versus51985.6,
118 suspensions versus31, and a-10.42pp score delta versus the uninstrumented CPG build. It materially changes fuel
and trajectories. These games are excluded from the strategy evidence and the source archives disable the profiler.

Stage p50/p95/p99/max by phase/body are in fuel_bench.json. Stage quantiles use conservative1000-fuel histogram bins;
values can exceed a tiny measured maximum because of binning. Maps cover the16 varied heavy development maps and
three opponents, both sides. The profiler cannot establish exact uninstrumented per-stage worst cases.

The diagnostic-only trigger sample confirms actual behavior:1120 flee strikes,190 resets,59 ranged shots,
63 disengages (33 carriers),127 progress-stall releases,39 oscillation releases,43 bank choices and28 re-scores.
These counters are not a claim that the profiler follows the scored trajectories exactly.

The optional governor reserves execution/tail budget, defers group-field preparation and resumes bush labeling;
combat loops are bounded by visible entities/two spells. Unknown/unfinished information falls back to baseline.
The event-neural pipeline now requires fast kernels. Neither neural checkpoint passes release fuel/quality gates.

Remaining uncertainty: lower aggregate suspension counts do not prove there is no new suspension failure mode in
any unseen state. Both candidate packages remain locally measured artifacts; no official ladder qualification occurred.
