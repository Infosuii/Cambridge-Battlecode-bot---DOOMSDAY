#!/usr/bin/env bash
# One-time setup inside a remote Linux box (GitHub Codespace) for CPU PPO retraining.
# Copy the slim bundle first (local): gh codespace cp -c <name> artifacts/tmp/cl_bundle.tar.gz remote:~/cl_bundle.tar.gz
# Then (remote): bash codespace_setup.sh ~/cl_bundle.tar.gz
# Installs CPU-only torch (no CUDA), the official cambc 5.0.0 engine/CLI and small deps into ~/venv; unpacks ~/bundle.
set -euo pipefail
BUNDLE="${1:-$HOME/cl_bundle.tar.gz}"
python3 -m venv "$HOME/venv"
. "$HOME/venv/bin/activate"
pip install -q --upgrade pip
pip install -q "cambc==5.0.0" numpy psutil
pip install -q torch --index-url https://download.pytorch.org/whl/cpu
cd "$HOME"
rm -rf bundle
tar xzf "$BUNDLE"
command -v cambc
cambc --version
python -c "import torch, numpy, psutil; print('torch', torch.__version__, 'threads', torch.get_num_threads())"
nproc; free -g | head -2
echo "ready: cd ~/bundle && PY=\$HOME/venv/bin/python TRAIN_CLI=\$(command -v cambc) TRAIN_JOBS=\$(( \$(nproc) - 1 )) bash cl_train.sh RUN ITERS GAMES EVERY"
