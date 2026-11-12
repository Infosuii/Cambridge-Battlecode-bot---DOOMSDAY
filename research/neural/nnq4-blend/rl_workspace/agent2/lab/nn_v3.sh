#!/bin/bash
# Neural bot version 3 (828 features: 24 camp groups, allies' claimed targets from shared memory). The best RL network
# (500-feature layout, agent2/nn_rl2/best.pt) plays; the recorder logs the version-3 features with what the bot actually
# did (its target choice, v92's actions for the other heads), so the new network starts from the RL gains.
# usage (project root): bash agent2/lab/nn_v3.sh
set -e
cd "$(dirname "$0")/../.."
export NN_LAYOUT=3
python -P agent2/lab/nn_mkrec.py 4
python -P agent2/lab/nn_mkbot.py nnrec3 agent2/nn_rl2/best_w.h A2_NN=3 BASE=nnrec A2_NNREC=4 A2_NNREC_LAYOUT=3 A2_NN_LAYOUT=2 | grep -q built
python -P agent2/lab/nn_record.py agent2/nn_data_v3 --bot nnrec3 --fuel 20000000 --opps v92,x3ctr,p65pack --every 8 \
    --sets maps,maps_real250,maps_pooltrain,maps_test4,maps_new4,maps_maze | tail -2
python -P agent2/lab/nn_labels.py agent2/nn_data_v3 agent2/nn_labels_v3.npz
python -P agent2/lab/nn_train.py agent2/nn_labels_v3.npz agent2/nn_out_v3 --epochs 10 --student-epochs 8 | grep "epoch 10\|epoch 8\|parameters"
python -P agent2/lab/nn_export.py agent2/nn_out_v3/teacher.pt teacher agent2/nn_out_v3/teacher_w.h
python -P agent2/lab/nn_export.py agent2/nn_out_v3/student.pt student agent2/nn_out_v3/student_w.h
python -P agent2/lab/nn_mkbot.py nnv3T agent2/nn_out_v3/teacher_w.h A2_NN=3 A2_NN_LAYOUT=3 | grep -q built
echo V3_DONE
