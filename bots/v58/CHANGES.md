# v58: Sprint3 economy and faster contested-camp tracking

Submitted2026-10-26T13:23:03.916Z as platform57 (repository v58). Selected; compilation queued at the last check.
Previous platform56 remains active while compilation is queued. This is the combined
package requested by the user, based on frozen v57. Development uses official SDK/CLI4.0.0 and engine2.0.0,
with the official100000 fuel/turn and doubled opening allowance. No fuel, round or rule overrides.

## Result and release checks

| Check vs frozen v57 rebuilt on SDK4 | Record | Margin | Fuel-outs/game |
|---|---:|---:|---:|
| Development,28 maps/both sides/seeds1-12 |430/672 (64.0%)|+153.0|0.999|
| Original12-map holdout,once,seeds1-4 |67/96 (69.8%)|+152.0|0.240|
| Previous fresh15 pool,once,seeds1-4 |69/120 (57.5%)|+127.1|0.000|
| Additional15 new Sprint3 maps,once,seeds1-4 |73/120 (60.8%)|+79.5|1.867|

Development map-cluster95%[+107.5,+202.8]. Bayesian mean+202.5, P(gain)=1.0000 in6000 posterior draws.
Every run exited0 with complete coverage and zero native faults on both teams. The original fresh pool has
historical v55-v57 exposure; new02 maps had recent-loss analysis exposure. No holdout was used to tune this source.
This establishes an improvement against our lineage; it does not establish rank25 or superiority to Claudus.

## What changed

- Keep a safe, visible capture anchor while other bodies fight; shift within the capture region when that is safe.
  Deny only immediately reachable, supported enemy captures. Finish nearby work before a healthy shopping reset,
  and finish engaged camps when visible enemies remain outside immediate reach. Preserve legal attacks/resets
  after walking or dashing. The broad team director, forced carry draft, broad retreat, extra wards and locks stay off.
- Read champion starting stats and shard growth from the official runtime metadata once per guest. This covers
  every Sprint3 champion buff/nerf; existing spell metadata already reads Ren/Tavi modifiers from the engine.
- Replace the nerfed Treasure opening with same-stat Prospector, retain role-specific Jungle/Durability mitigation,
  add Monster and Capture, then Collectors and alternating Greed offense/health milestones. Marcella keeps a hybrid
  focus/health/strength core. Reserve the first emblem budget before optional consumables, retaining crystals on
  disconnected terrain. Tribute/Skirmish/Hunter are available through the updated SDK and passive model, but are
  not blindly added to this default budget. Capture is mostly a mid-game purchase, not an early opening claim.
- Fix shopping accounting: repeated milestones include purchases already made that visit; prices and combination
  counts come from metadata. Greed correctly uses25 shards/750 gold and yields35 stat shards. Cache each guest's
  static build plan and refresh passive bookkeeping only after purchases/combinations.
- Use current Monster15% and cached Capture3-turn/Prospector/Collectors/Skirmish passive metadata. Families count
  once across duplicate stat variants. The engine owns actual payout/channel rules; the planner's duration is an
  estimate, including a possible already-started capture when Tavi shops in the field.
- Enable the existing exact fast camp-contact marking path (A2_FASTGRP). It replaces enemies x groups x camps
  scans with a shared spatial query. Six diagnostic games compared the old/new marks at every observation with
  zero assertion faults. Strength tests use the normal build, without diagnostic work. Fuel fell from1510/672
  (2.247/game) to671/672 (0.999/game), a55.6% reduction, while maintaining the overall improvement.

## Recent loss review and remaining shortfalls

Downloaded350 engine2 native summaries:330 ranked and20 extra Claudus games. Ranked games follow v57 activation;
individual match metadata does not expose the submission version. Extra unranked games have unverified source
identity and are not attributed to v57. In158 ranked losses, R250 earned gold averaged798.7 versus1042.7 and deaths
2.40 versus1.56. Native income includes kills/bonuses. This supports the economy/death-spiral diagnosis; it is not
proof of patch causality. The new opening economy, mitigation, capture retention and reduced lost turns address
that pattern without promising immunity to stronger opponents. The repeated-death routing experiment was deferred
so the frozen winning strategy could receive a focused computation optimization.

The original mechanism goals are not all reached. Across all672 final games, deaths fall13.25% (14.52 versus16.74),
short of30%. In the prespecified seed1 audit (56 games,all28 development maps/both sides), R250 capture gold is
711.9 versus689.7 (target900), elk-size captures2.79 (target3.5), carry share27.5% (target40%), and capture delay
7.86 versus8.52 rounds. Distributed ownership replaces the forced carry plan that lost strength; no Claudus proxy
qualifies. Treasure-by120 is superseded by Prospector: native team-first Prospector median115, conditional on
acquisition, versus v57 Treasure135. This is not a claim about designated-carry timing. Full native R250 earned gold
is948.8 versus878.8, including kills/bonuses; it must not be labelled capture gold. Carried gems lost per game remain
250.8 versus233.5 despite fewer deaths, so high-value bag survival remains open. CHANGES explains these shortfalls
under the brief's explicit release exception and the user's subsequent whole-package instruction.

## Reproducibility

Frozen source SHA256:38754076d690d5e0cc434b27719785046aac0c84f1e63c340b3113091d031f19.
An independent source-only copy builds byte-identically to seed1:
9f4890b764a18ca3edee8bbeb310677d87c8aadfb0cb815993a13d5608a71cba.
The official bundle contains exactly33 src/ files,279034 bytes; its source bytes equal the benchmarked source.
Frozen v57 release file hashes are unchanged. Build caches are now namespaced by CLI/SDK/CMake/toolchain fingerprint;
cross-environment comparisons are rejected. New replay analysis explicitly selects the pinned engine2 decoder,
verified against a native final round/score. Legacy training labels remain separated on engine1.0.3.

See research/v58/V58_SPRINT3_RESULTS.md, V58_RELEASE.json, V57_SPRINT3_LOSS_REVIEW.json and
results/v58-s3-clean-build.json. No new match groups were queued.
