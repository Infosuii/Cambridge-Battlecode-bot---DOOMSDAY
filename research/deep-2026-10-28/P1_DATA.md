# Session 1 data and exclusions

**Measured intake: 555 replay/native pairs reconciled; accepted study dataset n=550.**

All 111 frozen groups were downloaded through the official website. Existing catalog n=455,
wave 1 n=70 and top-v-top n=30 all pass native/replay checks. Five existing-catalog games
remain calibration-only; they are not additional strength or detector evidence.
DOWNLOADS.json contains file identities and RECONCILIATION.json contains every check.

## Accepted study counts

| Primary cohort | Games | Wins | Losses | Side A | Side B |
| --- | ---: | ---: | ---: | ---: | ---: |
| Climb | 295 | 173 | 122 | 135 | 160 |
| Learn | 80 | 8 | 72 | 40 | 40 |
| Other | 145 | 65 | 80 | 66 | 79 |
| Top-v-top | 30 | n/a | n/a | n/a | n/a |

Learn takes precedence when cohorts overlap. Control is our wins across cohorts.
The accepted sources are existing catalog 450, wave 1 70 and top-v-top 30 (total 550).
COHORTS.json retains ranks, snapshot times and overlap/unequal-exposure caveats.

## Frozen split and restrictions

Seed 20261028; cohort × map strata; 385 examined / 165 hands-off, all reconciled.
The five calibration games remain separate. ID assignments did not change after
downloads. Outcome metadata was seen during catalog selection; no current decision
trajectories were manually reviewed. Hands-off decoding was automated integrity
validation only; no hands-off decision or detector outputs were inspected.

## Attribution and exclusions

- Actual platform-version 69 UI evidence identifies the study. Other versions in
  contemporaneous or later listings are not imported. Exact activation time is unknown.
- The supplied archive and 33 frozen source blobs are exact; server-source hash remains
  independently unverified. This retrieval made no submission or activation change.
- All 555 native summaries pass internal identities and match independent replay states,
  including draft and physical roster. All 5,356 champion-body conservation checks pass.
- The first five-game calibration passed before bulk decoding. All currently selected
  pairs pass; there are no current integrity exclusions. Historical missing/mismatched
  downloads remain quarantined, documented in DOWNLOAD_EXCLUSIONS.json.
- Fourteen older engine/format 0.0.3 archives remain excluded from this study.
- Fresh public reads now restore group metadata for all 111 frozen groups / 555 games.
  IDs, maps, sides, engine and outcomes agree with the frozen manifest; all native scores
  and round counts agree. New raw metadata is local-only in restored-catalog.json;
  METADATA_RESTORE.json records validation. The earlier machine's original snapshot
  was not copied; this is a new read of the same immutable group identities.
- The captured existing catalog remains n=455, 239W/216L, from 91 groups created
  09:20:04.612Z–12:00:05.488Z on 28 October. This is not a proven activation-bounded census.
  error404 accounts for 215/455 games; loss counts are not opponent-strength rankings.

## Original full-intake map coverage (n=555, including five calibration games)


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

P2_DETECTORS.md now reports the examined screen (360 own games,25 reference games).
The 165 hands-off games still have no detector outputs. Decomposition, causal
next-bot recommendations and final held-out confirmation remain pending.
