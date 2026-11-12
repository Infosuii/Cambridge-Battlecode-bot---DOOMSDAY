Continue building our pure-algorithm Cambridge Battlecode bot (DOOMSDAY Zero, "DZ") until the Z plan is finished.

Repository: https://github.com/Infosuii/neural-networkk-battlecode
Branch: build/pure-algorithm-zero (latest pushed commit). Clone it on this laptop:
  git clone --branch build/pure-algorithm-zero https://github.com/Infosuii/neural-networkk-battlecode.git
The companion lab plan lives on branch lab/box of the same repository (git fetch origin lab/box); it holds the
v74h/v75/v76 lab bots and tools (tools/lab/branch_farm.py, plan_model.py, branch_prefix.py, screen120.py).

Read in this order:
1. research/dz/COMBINED_PLAN_2026-10-31.md: the single plan. It combines the Z plan, the lab/v76 plan, a 24-paper
   research review, lab4's branching evidence and the elite-meta study, with an ordered task list (A1-A4, B1-B4,
   C1-C4, D1-D5), each with an exit gate.
2. The PAUSED section at the TOP of CLAUDE_HANDOFF.md, then CONTINUE_HERE.md (fresh-machine setup).
3. research/dz/z-integration-2026-10-31/README.md and RESULTS.json (diagnosis and every screen so far), and
   research/dz/vm2-2026-10-31/RESULTS.json (the passed V-M2 engagement model).

Setup on a fresh Windows laptop: Git, Python 3.12+ (numpy, scikit-learn), Node 24, and a C++20 g++ (winget
BrechtSanders.WinLibs.POSIX.UCRT works; set DZ_CXX to its g++.exe). Then follow CONTINUE_HERE.md: verify and restore
the pinned runtime and supporting evidence, tools/dz.py host / build / verify. The default build must hash to
5cf28cb74612... (the selected release).

First actions:
- Resume the in-flight runs in section 3 of the combined plan (tools/dz_z14_screen.sh; the EE2, gold and style
  screens if any are missing).
- Build the per-map table (tools/dz_plan_select.py), confirm it against v74 and the holdout.
- Then work down the task list: A1 native team plans, A2 branch farm and learned plan selection on DZ, B1 EE2
  decisions plus the enemy-side model, A3 lambda_gold fit, C1 market claims, C2 big groups and gates, C3 elite
  experiments, then combine, ablate, and run G5/G6/G2, Z15 hardening, and G7 once.

Work autonomously and in depth. Implement every idea in the plan, don't ask the user to decide, pick the best
option and say why in one line. Every behaviour change goes behind a DZ_* flag that defaults to 0 until its gate
passes. Screen against one opponent and confirm on another (deterministic games make best-of-K overfit). Keep faults
and fuel-outs at 0.

Authorised: local builds, tests, matches, read-only public replay downloads, map and item tuning on the 70 maps,
and pushes to build/pure-algorithm-zero. Not authorised: submitting, activating, or launching ladder matches or
duels. Old bots are opponents only; never copy their code (re-implement lab ideas natively). Preserve
config/paths.json and completed experiments, use fresh run names, commit evidence capsules with tools/dz.py's
protocol, and keep the handoff sections and this prompt updated and pushed. If the user's usage is getting low,
pause, write the handoffs, commit and push everything, and update this prompt.
