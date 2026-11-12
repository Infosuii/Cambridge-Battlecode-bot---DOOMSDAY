#!/bin/bash
# Lab test set (E61): bot A vs v61_c3 and b5_c3 (fresh seed 3), both sides, on map slices. Prints one line per part
# and the total. Default slices: 25 maps_test4 + 25 maps_mazetest (200 games).
# usage: bash h2h_set.sh A [nmaps=25] [workers=5]     SETS="dir:n:skip dir:n:skip" overrides the slices (n ignored then)
cd "$(dirname "$0")/../.."
export ENGWASM=tools/viz/v2_0_0.wasm BOTS_DIR=v4/bots LAB_DRAFT_FUEL=10000000 H2H_PER_MAP=2
A=$1; N=${2:-25}; W=${3:-5}
SETS=${SETS:-"v4/maps_test4:$N:0 v4/maps_mazetest:$N:0"}
for s in $SETS; do IFS=: read -r d n k <<< "$s"; for o in v61_c3 b5_c3; do
  node agent2/lab/lab_h2h.js $A $o $d $n $W $k 2>/dev/null | grep -a " vs "
done; done | awk '{print} {split($6,a,"/"); w+=a[1]; n+=a[2]} END {printf "TOTAL %s %.1f/%d = %.1f%%\n", "'$A'", w, n, 100*w/n}'
