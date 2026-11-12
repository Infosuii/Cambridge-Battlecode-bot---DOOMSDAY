# Combat prework while K011 build identity is unresolved

This is offline analysis of the unchanged **plain x3** reproduction vs v86h, not a feature screen and not an x3mf comparison. No K014/K012/K013 strength runs have started. Source is build/z-plan 9c1bbde; canonical build hashes remain unresolved.

## Three reproduced losses, with native-death reconciliation

Decoded the existing K011 replays with tools/replay/fight_review.mjs, selecting NFS_REPLAY_ENGINE=2.0.0 and the pinned native visualiser asset directory. All sampled deaths equal the corresponding official summary count. Candidate side B is team index 1, not index 0.

| Case | Candidate deaths | No ally within 4 at last living sample | Enemies within 4 > allies within 4 + self | HP >=80% five sampled rounds earlier | Camp attacks in preceding five rounds |
|---|---:|---:|---:|---:|---:|
| 03one-gem A | 72 | 29 | 15 | 27 | 11 |
| 00oasis A | 50 | 17 | 12 | 11 | 10 |
| 00contest B | 58 | 29 | 22 | 28 | 8 |

These are deliberately selected high-death losses, not population estimates. Radius counts are omniscient last-living round snapshots, not the bot's visibility or exact decision state. Cassi/Issac linked deaths are separate bodies, not independent fights. The hp5 field uses the existing reader's five-sample history; do not interpret it as a precise continuous-time measurement. Raw replay archives stay local.

Concrete example: 03one-gem A, R87, Cassi id 2 dies at (43,16), 40 Chebyshev tiles from the first spawn sample; last living sample has four enemies and zero allies within 4 (also zero allies within 8). It had moved in four of the preceding five sampled rounds and made PvP actions in one. Issac id 3 dies in the linked event at (39,7), despite hp5=1.0. This establishes failed isolated survival; the replay alone does not prove which internal verdict caused it.

## Source-backed findings for later K013 work

1. `world.cpp::observe_champions` already reads actual observed health/max-health/strength/focus from the SDK for both allies and enemies. Equipment-aware work should first audit forecast usage/calibration, not invent a missing stat feed.
2. AllyRec omits gems and state. G3 SECURE therefore recruits an ally using position and health without knowing whether its bag or channel makes participation unlikely. Its damage discount `dps/(1+arrival)` grants positive damage immediately even to an ally that must spend the short horizon walking. A future mechanism should count feasible damage after arrival, not merely discount sustained DPS.
3. Current `lanch::kOrder` is **1.000**, so the count exponent is zero. The written `pow(count, kOrder-1)` is not evidence of an expensive runtime power calculation; the compiler can eliminate it. Profile actual fuel before claiming that deleting pow solves the +14–15 G3 fuel-outs.
4. G3 STYLE recomputes a local power verdict late in handle_enemies. The A3 backoff block can set winning=true/in_danger=false after earlier burst and other safety decisions. A future refinement should track why danger was set and distinguish a soft retreat threshold from an immediate lethal-threat veto.
5. `X1_G3_STYLE_EQ` is a **target health-fraction threshold for an equal-numbers exception**. The observed top-team backoff rate 0.263 is a **frequency of actions in contact**. They have different meanings; setting EQ=0.26 is not a calibrated way to reproduce a 26% backoff rate.
6. The SDK authenticates one champion per guest instance (`cached_self`/`is_draft`); shared team bytes are accessed through host reads/writes. A C++ static cache is not a team-wide once-per-round computation. Existing code already packs claims and sightings into a shared word. Capacity, freshness and ordering need explicit verification before any coordinator allocates shared state. Per-actor immutable-observation caching is the safe initial scope.
7. The new mechanism must stop optional work at 60k remaining fuel and preserve sufficient worst-case tail reserve. Fewer deaths are not enough; validate on x3mf, win screens and paired gates after prerequisites clear.

## K014 preparation only

All 33 supplied lines have a local manifest with exact discovered switch names. The anti-feed window is `X1_ANTIFEED_WIN`. A3_ITEMS is defined unconditionally to 0 in common.h before its later #ifndef fallback; `dz.py --set` appends an override to x1_config.h for common.h flags, so A3_ITEMS appears shadowed. No bot edits; mark actual build behavior honestly when the row is reached. Local manifest: artifacts/local-only/g5070/k014-manifest.json.

No feature is implemented or claimed effective by this document. K014 and K012 retain priority when K011 is resolved.
