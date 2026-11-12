#!/bin/bash
# Ladder-gap experiments (E118): what v92's per-map tables are worth, and the network without them; version 3.
cd "$(dirname "$0")/../.."
(cd v4 && python -P mkvar.py v92 v92nt LADDER_TABLES=0 A2_LADFIT=0 > /dev/null && ./cambc.exe build bots/v92nt --release > /dev/null && echo "v92nt built")
python -P agent2/lab/mk_v92of.py
F=20000000
python -P agent2/lab/held_run.py agent2/lab/e118_ladder.tsv nnbest_nt,nnv3T,v92nt,v92of v92 ladder --fuel $F | grep "vs v92"
python -P agent2/lab/held_run.py agent2/lab/e118_pool.tsv nnbest_nt,nnv3T v92 maps_pooltest:0:150 --fuel $F | grep "vs v92"
echo E118_DONE
