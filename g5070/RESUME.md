# g5070 continuation — x3 campaign

Updated 2026-11-03 00:10 UTC. K011–K014 are NOT complete.

## Objective and priority
K011 exact reproduction -> urgent K014 -> K012 -> K013. PC messages 0033/0034 supersede the original queue. No dependent comparison before exact K011 pass. Only PC integrates bot changes.

## Checkouts/environment
- Code /home/om/Projects/Battlecode/x1work: branch build/z-plan-5070, 9c1bbde2d5cee6ab53235019027cb452a733b340; remote tracking correct; no bot edits.
- Comms /home/om/Projects/Battlecode/x1-comms: branch comms/x1; write only g5070/. Initialized using tools/x1_comms.sh. Sparse checkout disabled here; code checkout sparse (needed sources/tools/maps/docs, no tools/vendor or historical runs).
- PY=/home/om/Projects/Battlecode/.venv/bin/python; DZ_CAMBC=/home/om/Projects/Battlecode/.venv/bin/cambc. Python 3.12.16, NumPy 2.5.4, native CLI 4.0.0. CLI SHA256 552056aab1b99a6626597b6aaf0ae38f967709626f90f2d6926c4510ca929eb4.
- WORKERS=18 DZ_MAX_PARALLEL=18. 20 logical CPUs, 30 GiB RAM. No CUDA setup needed.
- GitHub sign-in repaired; Git operations need network-capable execution and gh credential helper. No credentials recorded. No competition login.

## Completed reading
HANDOVER_X3, PROTOCOL, IDEATION_RULES, current pc/STATUS, messages 0031–0034, K011–K014, J018; feature tracker, ladder plan, PC K010 analysis, g5060 J017 analysis, g3 I-G3-01/02, Agent 2 HANDOVER/MATCH_ANALYSIS_E63, BIG_STRATEGIES section 4, proxy README; fight sources, G3 hooks, budget helpers, x1_gate.sh, x1_comms.sh, dz.py. Newer instructions override old x1 protocols.

## Actual progress
- Environment and native CLI installed; GitHub repaired; code branch pushed and separate comms initialized.
- K011 pending: direct x3 release build downloading official WASI SDK 33, CMake 3.31.8, Ninja 1.12.1. Output artifacts/tmp/g5070-default.wasm. Expected SHA256 5704d7ba41acca8f5c369c963cec1719c1285780a532cc797857d8d7e3a06d47.
- Reference ../x1-comms/g5060/results/J018/x1g-x3-pool-v86h-01.json: 108/172, engine 2.0.0, engine hash 85aa7167b44db7cea97509f55e997750520e33d644e9f4f90d6128c50eba1d21.
- K014 pending: 33 supplied lines; x3mf vs v92 expected 96/172, own mf-g5070 baseline required. Exact window name X1_ANTIFEED_WIN. A3_ITEMS has an unconditional earlier define in common.h: check actual --set effect without editing bot source.
- K012/K013 pending; no implemented features or measured strength results yet.

## Next commands (code checkout)
```bash
export PY=/home/om/Projects/Battlecode/.venv/bin/python
export DZ_CAMBC=/home/om/Projects/Battlecode/.venv/bin/cambc
export WORKERS=18 DZ_MAX_PARALLEL=18
sha256sum artifacts/tmp/g5070-default.wasm
SETS=pool OPPS=v86h WORKERS=18 bash tools/x1_gate.sh x3 repro-g5070
```
Outputs research/dz/runs/x1g-repro-g5070-pool-v86h-01/results.json and artifacts/tmp/dz/<run>/provenance.json; log artifacts/tmp/<run>.log. Compare 172 unique map/side records, outcomes, banked gems and provenance. Mismatch: report honestly and stop dependent runs.

## Communication/safeguards
Pull every 10 minutes; update STATUS every 30; publish completed runs. K014 report per line and push every 3. Use SIDE=g5070 bash tools/x1_comms.sh push. Code pushes only build/z-plan-5070; comms only g5070/. No destructive resets, force pushes, ladder, competition login or submissions. Preserve active run inputs; never merge comms into code.
