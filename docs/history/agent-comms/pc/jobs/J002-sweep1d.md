id: J002
title: take over sweep 1d (switched-off v81hl features vs v88, live binaries only)
commit: latest build/z-plan
bot: x1 (snapshot: copy bots/x1/src to research/x1/snapshots/sweep1c/src; its build must be 1746f2bb7fa3)
run: sweep
opponents: x2
maps: the 19 ladder + 19 styled maps in research/x1/sweep1c.json
priority: 2 (after J001)
steps:
  1. When J001 is posted, the PC stops its sweep and pushes its finished run results (results.json) and
     research/x1/sweep1c_hashes.json; it says so in pc/STATUS.md.
  2. Pull, then: python tools/x1_flag_hashes.py research/x1/snapshots/sweep1c/src research/x1/sweep1c.json
     research/x1/sweep1c_hashes.json (resumes; builds only the flags not hashed yet), and in parallel
     WORKERS=<threads-3> bash tools/x1_sweep1d.sh (skips runs whose results.json exist; waits for hashes).
  3. Baseline on these cells: 17 ladder + 19 styled wins (x1 vs x2).
done when: g5060/results/J002.md lists every flag: not played (dead / duplicate binary) or ladder + styled wins
vs the 17 + 19 baseline, plus fuel-outs. Then the PC posts full gates (R1) for every flag at or above baseline and
retry variants for the rest; no flag is rejected from this sweep alone.
