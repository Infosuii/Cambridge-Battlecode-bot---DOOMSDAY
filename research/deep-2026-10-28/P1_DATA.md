# Session 1 data and exclusions

**Measured metadata intake; accepted decoded/reconciled dataset n=0.**

Existing catalog: n=455 games,239 wins and216 losses,91 version-filtered
groups, created09:20:04.612Z–12:00:05.488Z on28 October2026.
It is the captured UI catalog, not a proven complete activation-bounded census.
Wave1 adds n=70 games. Top-v-top adds n=30 games in6 groups.
All metadata rows identify engine 2.0.0; no old-engine replay was substituted.

| Primary cohort | Games | Wins | Losses | Side A | Side B |
| --- | ---: | ---: | ---: | ---: | ---: |
| Climb | 295 | 173 | 122 | 135 | 160 |
| Learn | 80 | 8 | 72 | 40 | 40 |
| Other | 150 | 68 | 82 | 66 | 84 |
| Top-v-top | 30 | n/a | n/a | n/a | n/a |

Counts include the five calibration games. Learn takes precedence for tabulation
when Learn and Climb overlap; Control means our wins across all cohorts.
Full membership/ranks/ratings and timestamps: COHORTS.json.

## Candidate partition frozen before trajectory review

Seed 20261028; cohort×map strata; nearest70% Hamilton allocation and seeded shuffle.
Examined candidates n=385; hands-off candidates n=165;
calibration-excluded n=5. CANDIDATE_MANIFEST.json
fixes IDs, selection, partitions and method. These are candidate assignments,
not accepted games. Preserve assignments through reconciliation failures.
Outcome metadata was visible during coverage selection; current replay trajectories
were not reviewed. Hands-off trajectories and detector outputs remain unopened.

## Attribution and exclusions

- The authenticated Matches filter group-version=69 and each study-group UI page
  supply actual platform-version evidence. The same time window also contains v67
  games, so a timestamp-only filter would mix sources. Activation time remains unknown.
- The user supplied the live source; all 33 frozen files are exact. No independent
  server-source hash was obtained. Platform identity and source identity remain distinct.
- Native summaries n=2 pass metadata score/round/outcome and internal
  draft/roster/gem/gold checks. This is not replay reconciliation; independent pairs n=0.
- Initial five-game native-download selection produced two usable unique JSONs,
  one binary instead of requested JSON, one duplicate/mismatched JSON and one absent
  file. The latter three stay quarantined; see DOWNLOAD_EXCLUSIONS.json.
- Both current replay download controls returned paths with no corresponding file.
  No current replay entered analysis. CLI 4.0.0 remains unauthenticated.
- Fourteen older cached ZIPs contain engine 0.0.3/format 0.0.3 replays; exclude all 14.
- Unequal exposure is substantial: error404 accounts for215/455 existing games
  (measured, n=455). Loss-count cohort additions are not opponent-strength rankings.

## Counts by map (metadata only)

| Map | Learn | Climb | Other | Top-v-top |
| --- | ---: | ---: | ---: | ---: |
| 00ambush | 0 | 5 | 2 | 0 |
| 00anvil | 0 | 4 | 4 | 1 |
| 00breadcrumbs | 0 | 4 | 1 | 0 |
| 00collision | 0 | 4 | 1 | 2 |
| 00contest | 1 | 4 | 2 | 1 |
| 00corners | 1 | 4 | 2 | 1 |
| 00crater | 2 | 4 | 2 | 1 |
| 00dunes | 4 | 6 | 1 | 3 |
| 00eight | 2 | 4 | 2 | 1 |
| 00elkring | 1 | 4 | 3 | 1 |
| 00expanse | 0 | 5 | 3 | 1 |
| 00fragment | 3 | 4 | 1 | 0 |
| 00galaxy | 1 | 12 | 4 | 1 |
| 00gem_fields | 0 | 4 | 1 | 1 |
| 00gemfight | 0 | 4 | 1 | 0 |
| 00great_wall | 1 | 4 | 2 | 1 |
| 00interlock | 0 | 5 | 0 | 0 |
| 00lanes | 2 | 5 | 1 | 0 |
| 00lost_world | 0 | 4 | 2 | 0 |
| 00monolith | 1 | 4 | 2 | 0 |
| 00oasis | 0 | 4 | 0 | 2 |
| 00packs | 0 | 7 | 2 | 1 |
| 00pilgrimage | 0 | 4 | 4 | 0 |
| 00quadrants | 0 | 4 | 5 | 0 |
| 00quarry | 0 | 4 | 1 | 1 |
| 00reverse_spiral | 6 | 11 | 3 | 1 |
| 00ribs | 0 | 3 | 1 | 1 |
| 00road_of_riches | 1 | 12 | 4 | 1 |
| 00rows | 2 | 3 | 1 | 0 |
| 00rushbait_v2 | 1 | 3 | 1 | 0 |
| 00split | 1 | 3 | 2 | 0 |
| 00stampede | 0 | 4 | 2 | 0 |
| 00swirl | 0 | 4 | 1 | 0 |
| 00the_line | 0 | 3 | 1 | 0 |
| 00vault | 1 | 3 | 3 | 0 |
| 01big_world | 2 | 3 | 1 | 0 |
| 01boss_battle | 6 | 5 | 4 | 0 |
| 01broken_curve | 1 | 4 | 2 | 0 |
| 01concentrated_wealth | 0 | 3 | 4 | 0 |
| 01corridors | 0 | 4 | 2 | 0 |
| 01elk_arena | 1 | 3 | 2 | 0 |
| 01fracture | 1 | 3 | 1 | 0 |
| 01gold_rush | 0 | 3 | 0 | 0 |
| 01hooks | 1 | 4 | 2 | 1 |
| 01islands | 7 | 11 | 1 | 0 |
| 01shortcut | 7 | 3 | 4 | 0 |
| 01starfish | 1 | 3 | 1 | 0 |
| 01starvation | 0 | 3 | 2 | 0 |
| 01the_farm | 1 | 3 | 0 | 0 |
| 01yellow_brick_road | 0 | 3 | 4 | 1 |
| 02arena | 2 | 4 | 0 | 1 |
| 02crossing | 1 | 3 | 1 | 0 |
| 02cuts | 0 | 3 | 5 | 2 |
| 02famine | 3 | 3 | 4 | 0 |
| 02fields | 1 | 3 | 2 | 0 |
| 02geodes | 2 | 3 | 2 | 0 |
| 02gift_wrapping | 0 | 3 | 4 | 0 |
| 02guardians | 1 | 3 | 5 | 0 |
| 02harvest | 1 | 11 | 5 | 1 |
| 02stalactites | 0 | 3 | 6 | 0 |
| 02tangle | 1 | 3 | 0 | 0 |
| 02the_pack | 0 | 3 | 1 | 0 |
| 02the_pond | 0 | 3 | 3 | 0 |
| 02treasure_box | 7 | 5 | 4 | 2 |
| 02uncharted_lands | 1 | 3 | 2 | 0 |
| adgato_gemcombat1 | 0 | 3 | 1 | 0 |
| adgato_gemcombat2 | 0 | 3 | 1 | 0 |
| adgato_gemcombat3 | 0 | 3 | 2 | 0 |
| adgato_gemcombat4 | 1 | 3 | 2 | 0 |
| adgato_gemcombat5 | 0 | 3 | 2 | 0 |

No loss-versus-win detector intervals, final win-probability decomposition or
next-bot causal recommendations can be supported until current replays reconcile.
