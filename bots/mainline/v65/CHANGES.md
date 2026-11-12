# v65 (platform v65, uploaded 2026-10-26 21:08 UTC as `v61_engine4.zip`)

Despite the file name, this is **v58** (platform 57) with one change: `A2_KNOBS` in `src/common.h` holds a new
48-value lab-knob vector (v58 had 24 values). The knobs scale aggression, retreat health, danger, bag size, hunting,
chase range, gold weight, cohesion, shopping, targeting weights, tactical-search weights, and more (see the `LABK(i)`
uses and the `A2_LAB` block in `play_turn`). None of the v59-v61 changes (Bruiser stacks, home guard, gold funnel,
opening pack) are in it. Source bundle: `artifacts/release/v65-source.zip`.
