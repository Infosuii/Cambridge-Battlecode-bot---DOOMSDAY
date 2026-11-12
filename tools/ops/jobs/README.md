Push `pending/NN-name.sh` (bash; cwd = training checkout; env: REPO, PY, CLI, PYTHONPATH, TMP). The runner on the
training box executes it within ~10 minutes, then moves it to `done/` and writes `logs/NN-name.log`. Start anything
longer than a few hours detached inside the job and poll it with later jobs.
