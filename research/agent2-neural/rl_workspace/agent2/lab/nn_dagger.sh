#!/bin/bash
# DAgger for the target head: the network acts (A2_NN=1), rows keep v92's choice; retrain on the aggregate; test.
# usage: nn_dagger.sh ITER PREV_WEIGHTS.h PREV_LABELS.npz[:frac]...   (writes agent2/nn_dag$ITER/...)
set -e
cd "$(dirname "$0")/../.."
I=$1; W=$2; shift 2
python -P agent2/lab/nn_mkbot.py nn2dag "$W" A2_NN=1 BASE=nnrec A2_NNREC=4 | grep -q built
python -P agent2/lab/nn_record.py "agent2/nn_data_dag$I" --opps v92,x1,x3ctr --every 8 --bot nn2dag --sets maps,maps_real250,maps_test4,maps_new4,maps_maze,maps_pooltrain | tail -2
python -P agent2/lab/nn_labels.py "agent2/nn_data_dag$I" "agent2/nn_labels_dag$I.npz" | head -3
python -P agent2/lab/nn_merge.py "agent2/nn_labels_agg$I.npz" "$@" "agent2/nn_labels_dag$I.npz"
python -P agent2/lab/nn_train.py "agent2/nn_labels_agg$I.npz" "agent2/nn_out_dag$I" --epochs 8 --student-epochs 8 | grep "epoch 8"
python -P agent2/lab/nn_export.py "agent2/nn_out_dag$I/student.pt" student "agent2/nn_out_dag$I/student_w.h"
python -P agent2/lab/nn_mkbot.py "nn3t$I" "agent2/nn_out_dag$I/student_w.h" A2_NN=1 | grep -q built
python -P agent2/lab/held_run.py "agent2/lab/nn3t${I}_ladder.tsv" "nn3t$I" v92 ladder --fuel 1000000 | grep "vs v92"
echo DAGGER_DONE $I
