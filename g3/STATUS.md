# g3 status —3 November2026,06:15 UTC

CURRENT L006 ACTIVE: fixed-seed refits of13 weak tabled maps, per pc/jobs/L006-J023-takeover.md/msg0047. Code x1g3/build/z-plan-g3 on8bbe438 (base94c35fe plus tooling fixes). Bots unchanged. Starting default hash check then artifacts/tmp/g3_l006.py, log artifacts/tmp/g3-L006-fit.log. Sixiterations/threepairs/sigma0.5/lr1/seed1, four fitted opponents v92,v86h,x1bru,x3inv,14workers. State research/x3/es/mapfit-<map>.json. ES run names have -g3 via X3_RUN_SUFFIX. One heavy campaign; do not launch another. Expect several hours; status posted per iteration and at most15min apart, states/code/results pushed per map.
Tooling: new tools/x3_g3_mapfit_table.py uses recorded runtimefp research/x3/counter_fp.json copied from g5060/J024, preserves13original J022 rows, refuses key collisions/asymmetric fingerprints. Dry-run/no-state preserves exactbytes; new-row fixture preservesall13 and correctkey. Do NOT use upstream x3_mapfit_table.py (authored-half bug and would drop rows without original states).
NEXT after13fits: python tools/x3_g3_mapfit_table.py --fp research/x3/counter_fp.json; verify default hash, then fitted gate poolv92/v86h/x1bru/x3inv (base96/115/130/102=443) and held-out poolv81hl/v86h-s2/x1 (base137/107/133=377); table must gain on BOTH; report fuel/faults/pairs. Push states/header only to g3 branch, PC merges.
L005 four runs complete: fullinvader102,invasion-only84,aggression-only88,item-only93 of172; allfaults0,pattern/loss-cell reports posted. Fullinvader PCaggregate102 matches; exactpergame reference still requested,msg0003. Final L005 report notes limitation. L004 completed,allfourfeatures below377baseline,noadoption. L002/L003 withdrawn.
Machine ASUS_LAPTOP/i5-12500H/16threads/16,858,320,896bytesRAM. WORKERS=DZ_MAX_PARALLEL14,NFS_REPLAY_ENGINE2.0.0,Python3.12.14/numpy2.3.5. Plugged-in screen/sleep Never. Only g3/commswrites and build/z-plan-g3codepushes; no ladder/login/uploads/submissions or sources edits. Preserveall local evidence,neverstage runnerledger/artifactreplays.

L006 CURRENT fitting 00elkring; six iterations,three pairs,four opponents,seed1; no simultaneous gate.

L006 00elkring iter 0: mean fit/game 0.632 wins 5/8 best iter 0 grad |0.414|

L006 00elkring iter 1: mean fit/game 0.832 wins 6/8 best iter 1 grad |0.497|

L006 00elkring iter 2: mean fit/game 0.943 wins 7/8 best iter 2 grad |0.284|
