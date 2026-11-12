#!/bin/bash
# E125: spend spare fuel on the distance fields sooner: plain v92, and the fitted blend (no scoring until they are built), real fuel, official 420 + fresh 498
cd "$(dirname "$0")/../.."
until grep -q E125_B_DONE agent2/lab/e125_b.out; do sleep 5; done
python -P agent2/lab/mk_v92f.py v92f3 3000
Q="A2_NN=11 A2_NN_MACRO=1 A2_NN_FAST=1 A2_NN_VALID=1 A2_NN_BEH=0 A2_NN_ENS=2 A2_NN_LIVE=1 A2_NN_LAZY=1 A2_NN_NNUE=1 A2_NN_Q16=1 A2_NN_SGAUTO=1 A2_FIELD_MARGIN=3000 A2_NN_FIELDS_FIRST=1"
python -P agent2/lab/nn_mkbot.py nnq4 agent2/student_i2m_w.h $Q | tail -1 | cut -c1-200
python -P agent2/lab/nn_mkbot.py nnq4n1 agent2/student_i2m_w.h $Q A2_NN_LJIT=1 A2_NN_LJIT_A=0.1 | tail -1 | cut -c1-200
python -P agent2/lab/nn_mkbot.py nnq4log agent2/student_i2m_w.h $Q A2_FUELLOG=1 | tail -1 | cut -c1-200
export E95_JOBS=8
python -P agent2/lab/held_run.py agent2/lab/e125_fld.tsv v92f3 v92,v92j1,v92j2 ladder | grep --line-buffered "vs " | cut -c1-85
python -P agent2/lab/held_run.py agent2/lab/e125_fld.tsv nnq4,nnq4n1 v92,v92j1,v92j2 ladder | grep --line-buffered "vs " | cut -c1-85
python -P agent2/lab/e125_big.py nnq4log > agent2/lab/e125_big4.out 2>&1
python -P agent2/lab/held_run.py agent2/lab/e125_fldf.tsv v92f3,nnq4 v92 maps_poolfresh:0:250 | grep --line-buffered "vs " | cut -c1-85
echo E125_FIELDS_DONE
