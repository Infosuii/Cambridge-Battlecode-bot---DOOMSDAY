#!/bin/bash
# E119: validate the official-map fix (v92of) at real fuel against four opponents and head-to-head; network on it.
cd "$(dirname "$0")/../.."
python -P agent2/lab/held_run.py agent2/lab/e119_real.tsv v92of,v92 x1,x3ctr,b5_c3,v81 ladder | grep "vs "
python -P agent2/lab/held_run.py agent2/lab/e119_h2h.tsv v92of v92 ladder | grep "vs "
python -P agent2/lab/held_run.py agent2/lab/e119_nn.tsv nnbest_of v92 ladder --fuel 20000000 | grep "vs "
echo E119_DONE
