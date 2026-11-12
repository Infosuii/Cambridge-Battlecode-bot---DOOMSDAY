#!/bin/bash
# Rebuild the map suites left out of the repo for size (about 1.7 GB), identical to Agent 2's: fixed seeds, the first
# maps of every suite checked byte for byte. A suite whose folder already exists is skipped.
# usage (workspace root): bash agent2/lab/regen_maps.sh [SUITE ...]   (default: all six)
cd "$(dirname "$0")/../.."
for s in ${@:-maps_real250 maps_real200b maps_mazetest maps_test4 maps_new4 maps_maze}; do
    [ -d "v4/$s" ] && { echo "$s exists, skipped"; continue; }
    case $s in
        maps_real250)  CLEAN=1 REAL=1 node tools/viz/mapmake4.js v4/$s 250 99400000 ;;         # RL training (nn_rl3.py, 10%)
        maps_real200b) CLEAN=1 REAL=1 node tools/viz/mapmake4.js v4/$s 200 99500000 ;;         # unseen check (final_check.sh)
        maps_mazetest) CLEAN=1 REAL=1 MAZE=1 node tools/viz/mapmake5.js v4/$s 100 55800000 ;;  # unseen check (final_check.sh)
        maps_test4)    CLEAN=1 REAL=1 node tools/viz/mapmake4.js v4/$s 200 99100000 ;;         # imitation / DAgger data
        maps_new4)     CLEAN=1 REAL=1 node tools/viz/mapmake4.js v4/$s 150 77700000 ;;         # imitation / DAgger data
        maps_maze)     CLEAN=1 REAL=1 MAZE=1 node tools/viz/mapmake5.js v4/$s 150 55500000 ;;  # imitation / DAgger data
        *) echo "unknown suite $s"; continue ;;
    esac > /dev/null
    echo "$s: $(ls v4/$s | wc -l) maps"
done
