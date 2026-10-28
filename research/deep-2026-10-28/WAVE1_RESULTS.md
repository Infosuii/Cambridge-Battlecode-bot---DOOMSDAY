# Wave 1: measured outcomes; replay diagnosis pending

Recorded 2026-10-28T12:53:39.380580+00:00. All 14 unranked groups / 70 games finished.
Maps, ordered sides, opponent identities and unranked status agree with all
14 reservations. Authenticated pages, each anchored
to its own immutable group ID, show our version 69 for all 14 groups.
No uploads, activations or ranked requests were made.

| Opponent | Wins/games | Mean gem margin | 95% Wilson win interval |
| --- | ---: | ---: | --- |
| Mite | 2/10 | -660.2 | 5.7%–51.0% |
| Intercontinental Fish | 0/10 | -732.9 | 0.0%–27.8% |
| Ad Astra | 2/10 | -540.8 | 5.7%–51.0% |
| Univardisty of Shingtonwash | 1/10 | -573.6 | 1.8%–40.4% |
| Rogue Lock Pickers | 1/10 | -400.3 | 1.8%–40.4% |
| subscribe to caterpillow | 2/10 | -232.9 | 5.7%–51.0% |
| Zarzorki | 2/10 | -247.9 | 5.7%–51.0% |

Each row has n=10 games: five maps, both sides, one game per map/side.
These are descriptive **measured** scores. The intervals assume independent games;
shared maps, paired opponents and selective map coverage limit that assumption.
These are not broad ladder win-rate estimates or causal tests of bot changes.

Opponent pins use the immutable source-group references in SCRIMMAGES.json.
The first subscribe to caterpillow and Zarzorki groups used their then-current bot;
each mirror pins that first group's opponent. Other pairs pin existing groups.
The service hides numeric opponent submission versions in public metadata.

The Mite pair won only on 01islands (2/2 on that map, 0/8 elsewhere; n=10 games).
This is a small **association**, not an explanation of why the other maps lose.
No detector rates or causal code findings are available: replay reconciliation n=0.

Source rows and intervals: WAVE1_METADATA.json. Full IDs, maps, sides and scores:
SCRIMMAGES.json. No further wave 1 requests. Wave 2 retains 10 groups and requires
FAST_FINDINGS.md plus written hypothesis/prediction/decision rules first.
