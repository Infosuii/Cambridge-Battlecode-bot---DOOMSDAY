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

E1b: 198/672 (29.5%), -241.4, faults 0, fuel 1001/1046. Rejected. E1 capture income actually rose (R250 173 vs152; R500 386 vs346 per actor), while R500 equipment was approximately equal and score collapsed; gold generation alone does not establish a useful composition.

E3: 319/672 (47.5%), -27.9, faults 0, fuel 961/1003. Rejected as an improvement.

E4 initial result is an inert control: 336/672, exactly 0.0 margin, fuel1048/1048, zero faults. Code inspection found APEX_WARDS=0: the old drop_ward entry guard disables the new programme too (existing ladder wards are produced by ward_reveal). The prototype did not activate its mechanism; no causal conclusion about wards. E4b explicitly lets V55_WARDS enable the programme and repeats all12 seeds.

E5: 344/672 (51.2%), -12.8, faults0, fuel1014/1038. Neutral/rejected. Item-equivalent comparisons include Prism's carried-gem focus; a limitation of this rejected prototype, not a validated capital measure.

Historic hooks replay audit: buyonly and nobuy sources differ in TWO places, purchase and the teleport-call guard. Thus their 10vs20 wins cannot identify the causal effect of the physical crystal alone. Audit compares positions, HP, inventory, purchases and action payloads, excluding timeline event IDs (extra purchases renumber later events). No hops in either24-game set. A controlled new purchase-only intervention is E6; historic outcome association is not promoted to a proven engine bug.

## E1c: bounded funding and conservative draft substitution

E1's Vesper receives 49.3% of team capture gold byR250 and45.6% byR500 (668/672 income-positive drafted games). Income increased, but big-capture gems fell129vs154 and equipment stayed near parity. This motivates a specific starvation/role-loss correction: V55_DRAFT=3 preserves learned picks except Cassi/Issac or Prism, replacing those with Vesper then Ryth; V55_OWNER=2 weights Vesper capital at0.6 in BOTH fairness routines, giving preference without unlimited monopoly; V55_BUILDS stays on. Predeclared targets before results: rows, gold-rush, boss-battle (the weak-pick cohort); broad development remains mandatory. This is not a claim that every Vesper pick is beneficial.

## E2b: executable cycle mission

V55_CYCLE=2 keeps the original bounded detour but admits the event scan with28k remaining (E2's55k admission is too restrictive after score selection) and commits to finishing the chosen detour before returning. Same safety/distance/deadline guards; no new work in the group scorer. Hypothesis remains reduced dead-camp waiting; exact wait measurement decides whether the mechanism worked.

E4b activated wards:290/672 (43.2%), -71.6, faults0, fuel2253/1232. Rejected. More vision increases subsequent observation and decision cost; placement/death metrics being checked before attributing the regression causally.
E6:341/672 (50.7%), +17.5, faults0, fuel1034/1004. Best observed mean, far below the major target; does not justify a breakthrough claim.
E1c:327/672 (48.7%), -24.1, faults0, fuel1345/853. Conservative role preservation recovers much of E1's loss, still no improvement.
E2b:331/672 (49.3%), -1.8, faults0, fuel981/974. Neutral; no success claim.

## Freeze for final assessment

Only V55_CRYSTAL=1 enabled; all other V55 switches off. No new target selection based on maps; original target set still fails. Transport safeguards are concentrated-wealth, big-world and shortcut; brawl set as declared earlier. Newer inactive prototype code remains available but must produce identical executable sections to E6 before inheriting its development result. Run frozen candidate vs v53, then the 12 final maps vs v54 ONCE across12 seeds. Holdouts previously exposed including hooks. Recommendation remains do not submit unless final evidence materially changes it. Final source changes after this point require a new assessment.

Ladder refresh:110 finished through17:10:10 UTC, ranked14/25, unranked48/85 (62/110 total);48 losses. The refresh wrote valid JSON then Windows console encoding failed printing a Unicode opponent name; data retained, no fetch coverage lost. Download/analyse all48 losses in a fresh local-only folder, reusing identical earlier downloads.

Freeze finalized by copying the EXACT E6 source snapshot back to bots/v55 (all per-file hashes match V55_EXPERIMENTS.e6). This avoids inferring executable equivalence from inactive-code edits. Later rejected refinements remain in their baseline-relative patches. An attempted restricted-environment direct build was denied filesystem execution access, so final builds use the same approved host Git Bash path as all benches. No source correction was required.
