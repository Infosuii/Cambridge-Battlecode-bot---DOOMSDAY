# EXP-164 result — repaired reporting and exact baseline recount

MEASURED: `py research/codex-ishan/live_control_recount.py` reconstructed all 640 completed EXP-161 native outputs and asserted exact equality for the full historical result dictionary and all 640 rows. Its original rejection is unchanged: 207 versus222 wins over320 paired cells, -4.688pp, map-cluster95% interval[-12.812,+3.750]. The original files were not overwritten.

`py research/codex-ishan/live_control_recount.py --stellar` then recovered all480 completed EXP-163 native outputs with the same thresholds and summary implementation. The report and rows were created with exclusive writes. All map hashes, sides, seeds, engine build, detailed-capture status, opponent hashes and duplicate release hashes were verified. The runner's release path now uses `candidate_wasm`, independent of paired row variable names. No source policy, map, game, threshold or binary changed for this repair.
