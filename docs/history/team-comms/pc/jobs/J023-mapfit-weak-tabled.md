id: J023
title: re-fit v92's weakest TABLED maps (after J022)
commit: build/z-plan c5da0e9 or later (data/ladder/v92/per_map.json = v92's real ladder record per map)
why: on the real ladder v92 wins 61% on maps with its table and 44% without (J022 fixes those). Some tabled maps
still lose badly: 00elkring 0-11, 01gold-rush 3-11, 00quadrants 6-17, 00great-wall 4-11, 00road-of-riches 5-10,
00interlock 5-9, 00fragment 4-6, 00ribs 6-9, 00dunes 4-6, 02geodes 20-27, 00rows 9-12, 02harvest 6-8, 01big-world 7-9.
Their ladfit rows were fitted against v92's own play. X1_MAPFIT rows apply ON TOP of ladfit, so the same ES refits them.
run (after J022, same tools):
  MAPS="00elkring 01gold-rush 00quadrants 00great-wall 00road-of-riches 00interlock 00fragment 00ribs 00dunes 02geodes 00rows 02harvest 01big-world" \
  OPPS=v92,v86h,x1bru,x1 bash tools/x3_mapfit.sh
  (x1 added as a 4th opponent: these are maps where an economy-first opponent beats v92's table)
then python tools/x3_mapfit_table.py (adds the rows; keeps J022's), gate X1_MAPFIT=1 on pool vs v92 / v86h / x1bru / x1.
