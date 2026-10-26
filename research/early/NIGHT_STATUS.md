# Night status

updated: 2026-10-25T00:47:41+01:00
active session: main Claude Code session
step: 1 running (full decode), 2 in progress (bc_extract.mjs design)
updated: 2026-10-25T00:58:05+01:00
step: 1 running (full decode); 2 bc_extract.mjs move head DONE (600/600, 99.7% labelled); next bc_dataset.py + trainer
updated: 2026-10-25T01:01:28+01:00
step 2 move head: extractor+dataset+trainer DONE, committed. Pilot BC (600 replays): val acc 51.3% vs hold 32.9%. Export: artifacts/runs/bc-move-pilot/export. Next: game check of pilot export, then scale data, then combat/shop/bank/objective heads.
updated: 2026-10-25T01:10:27+01:00
step 2/3: engage+combat+move BC pipeline committed; pilot artifacts/runs/bc-v2-pilot (move 51.8, combat 94.5, engage 78.5 = majority). Next: game check, then bank/objective/shop heads.
updated: 2026-10-25T01:27:31+01:00
ALL buildable steps done; report written (NIGHT_REPORT.md). Blocked on user decision (fuel admission refuses move head). Decode still running (parts 1-2 done).
updated: 2026-10-25T01:31:22+00:00
session: fuel admission fixes committed 153f498 (gate passes); combat_has_choice fix reverted (quadrants exhaustion). See NEXT_STEPS.md
updated: 2026-10-25T02:14:44+00:00
full-day decode COMPLETE (see decode.log)
resume task checked at 2026-10-25T03:41:07+00:00: decode.log complete (parts 1-10, 245,607 replays, 0 failed); no process running; no new work started per plan
