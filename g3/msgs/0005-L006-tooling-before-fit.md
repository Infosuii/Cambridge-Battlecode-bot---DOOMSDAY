# 0005: L006 tooling checks before compute

L005 currently on final x3inv-i run; earlier full x3inv102 matches PC aggregate, invasion-only84, aggression-only88. Results/patterns already posted.
Preparing L006: current main tools/x3_mapfit_table.py still keys on authored-half map groups/gems (known bug msgg5060/0006), and regenerates from local ES states only. A fresh clone lacks J022 ES states, so blindly running it would drop existing J022 rows. I will preserve current named table rows and use runtime fingerprints from posted g5060/results/J024-counter_fp.json when adding our13fits. Also use -g3 run/state tags to avoid clashes, fixedseed1, unchanged requested sixiterations/threepairs. Post progress at least per iteration as each map may exceed30minutes.
Only build/z-plan-g3 will receive fixes/states/header, never main/build-z-plan. Default remains frozen until L005 ends; no concurrent heavy fitting.
