#!/bin/bash
# Final validation of a candidate network bot against v92 and held-out opponents, never used for selection:
# ladder (70 x 2), fresh pool-like maps (maps_poolfresh, 249 x 2), unseen (mazetest 0-99 + real200b 50-199),
# and the ladder vs b5_c3 / v61_c3 (held out; v81 / x1 results on ladder maps are inflated for v92-family bots, E119).
# usage (project root): bash agent2/lab/final_check.sh BOT TAG [FUEL=20000000]
cd "$(dirname "$0")/../.."
BOT=$1; TAG=$2; F=${3:-20000000}
python -P agent2/lab/held_run.py "agent2/lab/fc_${TAG}_ladder.tsv" "$BOT" v92,b5_c3,v61_c3 ladder --fuel $F | grep "vs "
python -P agent2/lab/held_run.py "agent2/lab/fc_${TAG}_fresh.tsv" "$BOT" v92 maps_poolfresh:0:250 --fuel $F | grep "vs "
python -P agent2/lab/held_run.py "agent2/lab/fc_${TAG}_unseen.tsv" "$BOT" v92 maps_mazetest:0:100,maps_real200b:50:200 --fuel $F | grep "vs "
echo FINAL_DONE
