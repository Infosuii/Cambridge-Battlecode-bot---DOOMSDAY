id: J020
title: map strategy work (your ideation area) + the compute for the PC's ideas
commit: build/z-plan head (bots/x3; research/x3/mapplan = the PC's per-map plan search vs v92, 17 settings x 16 maps;
        tools/x3_mapplan_search.sh; X1_MAPPLAN table hook in x3 (x1_mapplan.h); X1_FIRSTFIELD switch)
Roles (Rishik): the PC is in charge (direction, review, merges); ideation is split; you run most of the compute.

Your ideation areas (own them: research, ideas, build behind X1_G60_* or X1_* switches on x3, test, report):
  A. **Per-map strategy for the competition pool.** Finish the plan search on the 16 maps without a ladder fit:
     OPPS="v86h x1bru" bash tools/x3_mapplan_search.sh (v92 is done, research/x3/mapplan). Build x1_mapplan.h (best
     plan per map by summed margin over the 3 opponents and both sides; keep "base" unless a plan beats it by a clear
     margin) and gate X1_PLAN=1 X1_MAPPLAN=1 on pool vs v92 / v86h / x1bru.
  B. **Map structure clusters -> strategies (generalise to unseen maps).** Compute structural features for all maps
     we have (pool 86, styled, maze; tools/mapgen/mapio.py reads any map; the PC's feature set is in
     research/x1/CBR_IM_ARCHITECTURE.md section 6: size, team, groups, spawn distance, wall / bush share, home /
     contested value share, corridor width, chokes, plus anything you find useful: gem-only maps, camp density, altar
     distance). Cluster them; find which plan / knob setting wins per cluster (from A and the gates); make a lookup
     by nearest cluster for maps with no table entry. Test on held-out maps (leave-one-map-out).
  C. Conversion (I-60-04) and economy rows of J019, as before.
Compute for the PC (run as posted): J019 switch rows; gates for PC features as they arrive.
Order: J018 (finish) -> A (search, ~20 min) -> J019 screens interleaved with B.
Also screen X1_FIRSTFIELD=1 on pool vs v92 (fixes turn-1 fuel-outs on the largest maps); check the x3 default build
is still 5704d7ba41ac at this commit.
