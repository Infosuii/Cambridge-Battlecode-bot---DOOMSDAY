Ladder data snapshots (2026-10-25). Produced on the training box with the logged-in `cambc` CLI; see ops/HANDOFF.md section 7.
- ladder_top400_20261025.json: `cambc ladder --json` pages 1-4 (rank, name, teamId, rating).
- doomsday_ranked_800_20261025.json: our last 800 ranked matches (`cambc matches list --team me --kind ranked --json`).
- doomsday_since_v51.json: tools/replay/track_submission.py output since 2026-10-25T11:30Z.
- team_ratings_20261023_compact.json: Bradley-Terry ratings from the 23 Oct archive (tools/replay/team_ratings.py).
- doomsday_losses/: decode_replays.mjs rows of 46 downloaded losses on our worst maps (+ meta) and 30 user-supplied losses.
- match_groups_20261025.json: unranked groups queued with v52.
