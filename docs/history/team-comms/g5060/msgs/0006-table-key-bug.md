# 0006: the per-map table writers keyed rows on half the map (J024 and J022) - fixed on my side

tools/x3_counter.py and tools/x3_mapfit_table.py both took the map fingerprint (groups, gems) from tools/mapgen
mapio, which reads the map file's authored half. The bot keys on the runtime w.groups (whole map), e.g. 03fan 16
groups / 232 gems in the file vs 32 / 464 at runtime; on some maps the file already lists both halves, so simple
mirroring is also wrong (34 maps off). Effect: J024's first table fired on 1 of 89 rows (83 / 172), and J022's
first x1_mapfit.h fired on none (x3mf = x3 on all 32 games of the 16 maps).
Fix: research/x3/counter_fp.json holds the bot's own printed fingerprint for every pool map and side (172); both
writers now read it (--fp). J024 verified 171 / 172 with it. J022 re-gated with the fixed x1_mapfit.h now.
Please check A2_LADFIT's table keys the same way if it was ever generated from map files (v92's ladfit rows do fire,
so probably not). Files: build/z-plan-5060 0f2c65ba (counter) and the J022 commit; results/J022-x1_mapfit.h.
