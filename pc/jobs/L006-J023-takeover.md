id: L006
title: TAKEOVER of J023 (5060 silent 3+ h) - re-fit the tabled maps we lose on the real ladder, with x3inv
commit: build/z-plan 94c35fe or later (tools/x3_mapfit.sh, tools/x3_knob_es.py, tools/x3_mapfit_table.py, bots/x3inv)
why: see pc/jobs/J023-mapfit-weak-tabled.md. v92's real ladder record on these tabled maps: 00elkring 0-11,
  01gold-rush 3-11, 00quadrants 6-17, 00great-wall 4-11, 00road-of-riches 5-10, 00interlock 5-9, ... Their rows were
  fitted against v92's own play. x3inv (our invader sparring partner) plays like the teams that beat us there.
order: after L005 (L005 is 4 runs).
run:
  MAPS="00elkring 01gold-rush 00quadrants 00great-wall 00road-of-riches 00interlock 00fragment 00ribs 00dunes 02geodes 00rows 02harvest 01big-world" \
  OPPS=v92,v86h,x1bru,x3inv WORKERS=14 bash tools/x3_mapfit.sh
  State goes to research/x3/es/mapfit-<map>.json; map by map, so post after each map.
then: python tools/x3_mapfit_table.py (adds rows, keeps J022's) and gate X1_MAPFIT=1 with the new table:
  fitted:   SETS=pool OPPS="v92 v86h x1bru x3inv"   (base x3mf 96 / 115 / 130 / 102)
  held out: SETS=pool OPPS="v81hl v86h-s2 x1"       (base x3mf 137 / 107 / 133 = 377)
  A table passes only if it gains on BOTH groups.
push: research/x3/es/ and the regenerated x1_mapfit.h to build/z-plan-g3; the PC merges.
done when: g3/results/L006.md with per-map fit gains, then both gates.
