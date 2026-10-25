# V55 build and evaluation log

Base: frozen v54. No submission authorized. Machine config and pre-existing generated files excluded.

## Predeclared targets and protocol

Targets: fragment, elkring, concentrated-wealth; brawl set eight, quadrants, gold-rush, rows, rushbait-v2. Require clear improvement on both sides across seeds. Major target >=60% wins, >=+100 mean gems against v54, better opening economy, no brawl collapse. Release gate: HANDOFF section 4. Final 12 maps once after freeze; all previously exposed, hooks explicitly used in previous research.

## E1: coupled Vesper economy (WP1)

Hypothesis: Vesper/Heart/Vendetta/Ryth/Marcella plus consistent nearby reward ownership increases capture income and early equipment. Discovery: A2_MLDRAFT=1 returns before NOVA_MAP_LINEUPS, so changing those tables alone would not change most picks. V55_DRAFT bypasses the learned selector but keeps terrain mobility picks. V55_OWNER makes coverage and handoff agree on a nearby Vesper. V55_BUILDS gives Ryth alternating health/strength Bruiser stacks after Treasure/Jungle/Durability; Heart keeps its v54 health/focus build. No waiting for unseen Vesper. Measure capture gold R250/R500, Vesper share, equipment R100/R250/R500. Coupled test followed by ablation.

Ladder refresh: 35 finished games through 16:40:07 UTC, ranked 5/10, unranked 12/25. Thirteen losses against Midnight Wardens; too small/confounded for causal claims. Raw downloads sequential and local-only.

E1 complete: 218/672 (32.4%), -203.8 mean gems, faults 0, fuel 1236/863. Rejected. Snapshot retained locally for ablation. Full actor ledger running. Initial ledger invocation hit Windows command-line length limits; fixed by batching 32 replay paths and merging ordered JSON arrays.

## E2: event-driven two-stop cycles (WP2)

V55_CYCLE, with original v54 draft/items/ownership. Hypothesis: when a chosen camp is more than 20 rounds from respawn, clear a nearby unclaimed solo camp and return by its next cycle. Existing terrain distance rows and cached safety/value tables used; scans only on the long-wait event, at most once per eight rounds, before R500. Detour must finish plus return within gap+6, no enemies, HP >=65%. No work in score_groups loops. Measure respawn-wait R500, capture gold and early equipment. This bounded dynamic route avoids committing draft-time approximate straight-line schedules on disconnected maps.

E2 complete: 338/672 (50.3%), +7.3, faults 0, fuel 1069/1032. Outcome neutral; do not call this a major improvement. Ledger pending.

## E1b: Vesper with learned supporting picks

V55_DRAFT=2 retains the learned selector after forcing Vesper first; OWNER/BUILDS remain coupled. Tests whether E1 failed by replacing useful area-clear/dash roles rather than because of Vesper herself. Compare to E1 with paired tool against identical v54 games.

## E3: post-milestone gem conversion (WP3)

V55_BANK bit1: safe carriers with >=15 equivalent shards keep farming below 36 gems, except forced downtime banks, winning/late/endgame/zero-distance banks. Bit2: halve existing gold weight after milestone, once per turn. Hypothesis: larger productive sorties and more gem-rich objectives improve conversion. Measure bank amounts/counts, bag losses, finish time and big captures; ablate if retained.

## E4: route wards (WP4)

V55_WARDS: place a free ward when recharged on a route or with visible enemies; aim three tiles toward the current objective/nearest enemy, fallback nearby legal tile. Require movement from prior ward while calm, skip spawn. Rules/SDK: one ward replaces the old one, personal vision only, recharge ten owner turn ends. Hypothesis: fresher forward vision reduces full-health and ambush deaths. Measure actual placements and death context, not merely wins.

## E5: equipment-aware exchange (WP5)

V55_GEAR: after existing fight search, compare type-normalized visible item equivalents in local groups; avoid when behind by >5 shards with no numbers advantage, accept when ahead with health/TTK support. Ryth's passive removed from item estimate by existing items_of. No A2_THREAT/DANGERMAP/TEAM levers re-enabled. Hypothesis: better selected contact raises damage exchange and reduces bag deaths. Measure contact damage/deaths and gear-conditioned decisions.

## E6: shard-budget crystal purchase (WP6)

V55_CRYSTAL: buy crystal only from the 10/20-gold remainder after reserving every affordable 30-gold shard. Hypothesis: the old pre-item 10-gold purchase delays an emblem when funds are exactly a 30-gold multiple; this is a candidate explanation, not yet the proven hooks mechanism. Preserve hop implementation and buying on every otherwise unchanged visit. Trace first divergence and purchases on seeds, and check shortcut/concentrated-wealth/big-world gains.
