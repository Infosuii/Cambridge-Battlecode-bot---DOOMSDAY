# Overnight plan (user asleep; authorised 2026-10-25 ~01:00 to run the remaining steps automatically)

Repo: `C:\projects\cambridge battlecode\work\neural-full-stack`, branch `claude/compare-fix-replay-decoder`.
User goal: a bot that, once trained, can win the competition. Budget-conscious: be terse, avoid re-reading big files.
Python (CUDA): `C:/projects/cambridge battlecode/work/neural-gameplay/.venv/Scripts/python.exe`; set
PYTHONPATH=<repo>/python, TMP/TEMP=<repo>/artifacts/tmp, PATH prefix C:/msys64/ucrt64/bin.

## Hard rules (unchanged)
No promotion/activation/submission/login/push. Never modify `artifacts/baselines/heuristic-v1`, references, SDK, maps or
engine fuel. Bounded jobs only; GPU training runs in the background with checkpoints. Never weaken gates. Keep
existing trainers untouched; new code goes in new files. Commit to the branch only (no push), small commits.

## Steps
1. DONE/RUNNING — full-day replay decode into action shards: `tools/replay/decode_archive.py`, output
   `artifacts/local-only/replays-20261023/part<N>/` (manifest.json per part, log in `decode.log`). Restartable.
2. Behaviour-cloning (BC) extractor `tools/replay/bc_extract.mjs`: at each champion turn, compute the 173-float
   observation and move/combat/shop candidate sets exactly as the C++ builders define them (schemas/policy_v2.json,
   bot/src/nn_policy_tactics.cpp, nn_policy_capture.cpp), using engine legality from the replay engine. Label =
   the candidate matching the replay action. The 6 bot-internal inputs use hard-coded rules:
   goal = position ~10 rounds later (hindsight); role from behaviour (gems+altar → carrier, champion fights →
   fighter, camp attacks → farmer, near carrier → escort, else scout); hot_zone = 0; ally claim code = 0.
3. BC trainer `tools/policy_bc.py` (new): whole DirectPolicyNet (encoder + heads) cross-entropy on legal-masked
   logits, grouped split by match, CUDA, checkpoints, export with existing `nfs.policy.export.export_model`.
4. Evaluate the export with `tools/policy_ops.py compare` vs untrained + heuristic-v1 on the 6 selection maps.
5. Write `research/early/NIGHT_REPORT.md` for the user (results, limits, next steps).

## Status
See `research/early/NIGHT_STATUS.md` (updated by whichever session is working; contains the last step done).

## UPDATE 2026-10-25 ~01:35 GMT — steps 2-5 DONE; remaining work BLOCKED on a user decision
All buildable steps are complete; see research/early/NIGHT_REPORT.md. The neural runtime refuses ~98% of
move-head decisions for fuel budget, so further training cannot improve play until the user decides on the C++
fuel/runtime fix. A resumed session must NOT start new training, extraction or C++ changes. Its only job: check
whether artifacts/local-only/replays-20261023/decode.log shows "complete" (or which part is running), append that line
to NIGHT_STATUS.md, and add one line to the "Data" section of NIGHT_REPORT.md. If the decode process died, restart it
with the same command (it skips finished parts):
  python -I tools/replay/decode_archive.py --replays "C:/projects/cambridge battlecode/match summaries 23102026/math replays" --out artifacts/local-only/replays-20261023 --workers 18
