# 0034: g5070 - START HERE (everything you need, in order)

To: g5070. From the PC, on Rishik's behalf. No manual steps: this file and the files it names are your full brief.

1. Update your code checkout: `cd x1work && git fetch origin && git checkout build/z-plan && git reset --hard
   origin/build/z-plan` (drop any old local cherry-pick of 57af220; DZ_MAX_PARALLEL is in build/z-plan now).
   Then `git checkout -B build/z-plan-5070 origin/build/z-plan && git push -u origin build/z-plan-5070`, back to
   build/z-plan, and `SIDE=g5070 bash tools/x1_comms.sh pull`.
2. Read `docs/x1_5070/HANDOVER_X3.md` (your rules, base x3mf, test protocol), then msgs 0031, 0032, 0033.
3. Jobs, in this order:
   - **K011** reproduction check: `SETS=pool OPPS=v86h WORKERS=18 bash tools/x1_gate.sh x3 repro-g5070` must give
     108 / 172, all 172 games equal to g5060/results/J018/x1g-x3-pool-v86h-01.json. Mismatch: report and stop.
   - **K014** feature sweep rows 14-26 on x3mf (urgent; work-steal J026's leftovers after).
   - **K012** fight switches on x3mf, then **K013** your fights area.
4. Post results after every 3 lines to g5070/results/, and a g5070/STATUS.md line at least every 30 minutes.
   Pull comms every 10 minutes; never end your session while idle.
Write only g5070/ on comms and build/z-plan-5070 for code. Never touch max/* (GX) or anyone else's branch.
