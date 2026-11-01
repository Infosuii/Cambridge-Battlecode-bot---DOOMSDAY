id: J001
title: set up and prove the machines agree
commit: latest build/z-plan
bot: x1
run: other
priority: 1
steps:
  1. Follow docs/x1_5060/README.md (clone, cambc, Python, comms init).
  2. Build bots/x1, bots/x2, bots/x2-s2, bots/v86h, bots/v86h-s2 and record their sha256 (python tools/x1_flag_hashes.py
     is an example of building through tools/dz.py). Expected: x1 1746f2bb7fa3, x2 a9f1bbc43ef7, v86h 0fae1c17ee73,
     v86h-s2 a0d2aabd702a.
  3. Reproduce: python tools/dz.py smoke --name x1e-cw-ladder-x2-g5060 --pool --opponent x2 --candidate-bot x1
     --workers <threads-2>. Expected 68/140 wins, and every game's outcome, banked and rounds equal to
     research/dz/runs/x1e-cw-ladder-x2-01/results.json.
  4. Note games per minute at your worker count (for scheduling).
done when: g5060/STATUS.md has machine specs, hashes, the reproduction verdict (exact or which games differ), games/minute.
If hashes differ but games are identical, say so: that is fine. If games differ, stop and post g5060/msgs/0001.
