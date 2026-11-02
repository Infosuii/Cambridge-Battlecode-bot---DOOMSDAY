id: J021
title: v92-style knob searches on x3 (Agent 2's method): fight knobs first
commit: build/z-plan 73631cf or later (X1_KD override, tools/x3_knob_es.py, dz --set accepts X1_KD lists)
why: v92's big gain came from a knob search (lab knobs) plus per-map fits. x3 can now take knob deltas per build;
this runs that search on the knobs behind our worst ladder losses (feeding: deaths while fleeing alone).
priority: interleave with J019 / J020 (this one is the PC's main ask; give it at least half the machine).
runs (each resumable; one line per iteration is printed; state in research/x3/es/<name>.json, push it as it grows):
  1. fight-all:  python tools/x3_knob_es.py --name fight-all --knobs 22,23,24,25,26,27,28,29,30,31,41,43,44,59,61,64,65,66 \
                   --map-dir maps/ladder-pool --opps v92,v86h,x1bru --scope 0 --iters 8 --pairs 4 --sigma 0.4 --maps-per-iter 20
     (aggression 22-23, fight/run verdict 24-31, team-fight engage 41, early aggression / hunt 43-44, commander
      threshold 59, Lanchester override 61, alone alert 64, fog regroup 65, burst danger 66)
  2. fight-new:  same knobs, --scope 1 (maps without a ladder table: the 16 new pool maps + styled + maze), --map-dir
                 maps/ladder-pool --maps <the 16 maps from tools/x3_mapplan_search.sh>, iters 8
  3. econ-all:   --knobs 0,1,2,3,4,5,8,9,10,11,12,33,34,35,36,37,38,39,40 (tuning, economy passives, banking, cohesion)
                 --scope 0, after 1.
After each run: screen the BEST X1_KD line on full pool vs v92 (172 games) and post it; >= 92 -> full gate.
Your own idea (B in J020): run the ES per structure cluster (--maps = the cluster's maps) once the clusters exist.
