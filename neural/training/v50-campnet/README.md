# v50 camp-net training (copied from the training box's `work/neural-gameplay`)

How v50's neural camp policy (`A2_CAMPNET`, 18-16-1 MLP, 321 weights in `bots/v50/src/neural_weights.h`) was trained:
in-engine PPO over 20 parallel CLI match workers plus the GPU, 1 hour (`tools/train.py`) then 2 more hours
(`tools/continue_two_hours.py`). Results: FINAL_REPORT_first_hour.md (38-42 vs v47) and FINAL_REPORT_two_hours.md
(no reliable gain). The scripts hard-code the training box's paths (CLI, SDK, ROOT); adjust ROOT/CLI before running
elsewhere. Large outputs (checkpoints, runs, opponents) stayed on the training box.
