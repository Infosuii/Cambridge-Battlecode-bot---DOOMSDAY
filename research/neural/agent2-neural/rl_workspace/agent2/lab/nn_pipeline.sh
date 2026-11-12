#!/bin/bash
# Neural bot pipeline: recorder -> data -> labels -> teacher/student -> export -> bots.  usage: nn_pipeline.sh TAG
set -e
cd "$(dirname "$0")/../.."
T=$1
python -P agent2/lab/nn_mkrec.py 4
(cd v4 && ./cambc.exe build bots/nnrec --release > /dev/null && test -f bots/nnrec/.cambc/build-release/bot.wasm)
python -P agent2/lab/nn_record.py "agent2/nn_data_$T" --opps v92,x1,x3ctr --every 4 | tail -3
python -P agent2/lab/nn_labels.py "agent2/nn_data_$T" "agent2/nn_labels_$T.npz"
python -P agent2/lab/nn_train.py "agent2/nn_labels_$T.npz" "agent2/nn_out_$T" --epochs 8 --student-epochs 8
python -P agent2/lab/nn_export.py "agent2/nn_out_$T/student.pt" student "agent2/nn_out_$T/student_w.h"
echo PIPELINE_DONE
