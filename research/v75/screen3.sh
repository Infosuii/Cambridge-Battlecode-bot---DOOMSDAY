#!/bin/bash
# lone2 against v61 and v58 on seed 23 (completes the league check for V75_LONE 2 + V75_LONE_ALL).
cd "/c/projects/cambridge battlecode/work/neural-full-stack"
P=../neural-gameplay/.venv/Scripts/python.exe
for o in v61 v58; do $P tools/v67/c_batch.py --seeds 23 --workers 8 --opponent $o V-$o-base=bots/v74 V-$o-lone2=artifacts/tmp/v67/v75r-lone2; done
for o in v61 v58; do $P tools/v67/c_paired.py V-$o-lone2 V-$o-base; done
