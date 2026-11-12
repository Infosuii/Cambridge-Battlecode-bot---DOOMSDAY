id: K010
title: head-to-heads with v92, and an INDEPENDENT analysis of x1c1's ladder games (Rishik's request)
commit: build/z-plan head (adds bots/v92 = Rishik's v92_engine4.zip, build 5704d7ba41ac; bots/x1c1 = ladder v76,
        build 22e6067a4233; data/ladder/x1c1/)
priority: FIRST, before everything else. Stop current controls after the line in progress.

Part A, tests (gate tool, ladder + styled + maze 59, both sides; x1g-TAG-SET-OPP naming):
  bash tools/x1_gate.sh x1c1 c1 ""     with OPPS="v92"
  bash tools/x1_gate.sh x1   x1 ""     with OPPS="v92"
  bash tools/x1_gate.sh v86h v86h ""   with OPPS="v92"      (if bots/v86h builds as a candidate; else skip)
  bash tools/x1_gate.sh x1   x1 ""     with OPPS="v86h"     (x1 vs v86h head-to-head, maze included)
Already done by the PC (on build/z-plan, research/dz/runs/x1g-c1-*): x1c1 vs x1 (ladder 63/140, styled 48/100,
maze 66/118) and x1c1 vs v86h (75/140, 55/100, 68/118). Do not rerun those.

Part B, independent analysis (no comms with the PC until you post): analyse
  - data/ladder/x1c1/: 90 real-ladder games of x1c1 (v76) from 14:38 UTC, matches_x1c1.json (teams, drafts, results),
    summaries.zip (cambc match summaries), replays/ (.repl26a);
  - data/ladder/x1/ and research/x1/LADDER_2026-11-01.md: the earlier x1 (v73) and v86h (v74) ladder games;
  - the local head-to-heads above and Part A.
Questions: why does x1c1 lose (0-25 vs 0xDEADBEEF, 0-25 vs Claudus Maximus, 10-15 vs QS2isLaw, 6-4 Tatakai, 4-1
Tzunami); what changed vs x1's ladder record against the same teams; when and how games are decided (economy vs
fights, by round, by champion / draft); which of our behaviours lose them; what you would build next and why.
Use numbers from the data for every claim. **Do not read pc/analysis/ until your report is committed.**
Write g5070/analysis/K010.md, then post. The PC writes its own report blind in pc/analysis/ and then compares.
