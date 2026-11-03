id: L009
title: Per-map knob fit for your 28 of the 57 remaining pool maps (after L008)
priority: 1 (right after L008). Long job (~6 h); the user wants it run in full.
commit: build/z-plan accf6c25 or later
why: the per-map knob ES is the method that transfers to unseen opponents (x3mf +14 held out); the counter tables
  do not. Every pool map gets its own fit; the PC does the other 29 (research/x3/es/ORDER_ALL.txt).
run:
  MAPS="01shortcut 00quarry adgato-gemcombat1 02fields 01the-farm 00gem-fields 01corridors 00reverse-spiral 01broken-curve 02arena 00oasis 01concentrated-wealth 02uncharted-lands 01yellow-brick-road 02stalactites 00split 00stampede 01hooks adgato-gemcombat2 00pilgrimage 00rushbait-v2 00lanes 00eight 02guardians 00expanse 00collision 00galaxy 00ambush"   OPPS=v92,v86h,x1bru,x3inv WORKERS=14 bash tools/x3_mapfit.sh
push: research/x3/es/mapfit-<map>.json to build/z-plan-g3 after EACH map (the PC merges and builds the table).
post: one line per map in g3/results/L009.md: start fit, best fit, best iteration.
