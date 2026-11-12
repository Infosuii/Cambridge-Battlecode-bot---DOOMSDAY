#!/bin/bash
# Report the machine and check one game runs. Result: ops/box/results/01-smoke.txt
{ echo "threads $(nproc)"; nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null
  "$PY" -c "import torch;print('torch',torch.__version__,'cuda',torch.cuda.is_available())"
  "$PY" tools/mapgen/profile_maps.py --a artifacts/tmp/v74h.wasm --maps maps/local-benchmarks/00rows.map26a --out artifacts/evaluations/box-smoke | tail -1
} > ops/box/results/01-smoke.txt 2>&1
cat ops/box/results/01-smoke.txt
