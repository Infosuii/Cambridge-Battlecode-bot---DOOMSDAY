# g5070 continuation — x3 campaign

Updated 2026-11-03 00:22 UTC. K011 accepted; K014 active, K012/K013 pending.

## Latest instruction overrides
PC 0035 explicitly accepts K011 and establishes **bf3f65d009c0 as the Linux x3 default reference**. Use this hash for future default-off checks. Compare only against our own Linux mf-g5070 runs, never Windows reference strengths. Historical unresolved-hash notes below are superseded by 0035. Do not rerun K011. Own mf-g5070 baseline is running on v92/v86h/x1bru at 18 workers, then K014's 33 supplied lines.

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
- K011 GAMEPLAY COMPLETE, BUILD IDENTITY UNRESOLVED. Direct and frozen x3 native SHA256 bf3f65d009c0419d2b0f04bdfab68b85f397ce6cb2350a36ab8782d4d74cd46a differs from expected 5704d7ba41acca8f5c369c963cec1719c1285780a532cc797857d8d7e3a06d47. Opponent native 90f8527bdea758d75cafb81859d0506ffb88d0e2fd619676c3c733db53c466d3 differs from 0fae1c17ee73. K011 measured 108/172, all 172 map/side/outcome/banked, deaths, rounds, map/engine hashes and per-game fault/fuel-outs identical to J018. 0 faults, 186 fuel-outs. Whole gate 25.960s, 397.53 games/min. DO NOT RERUN UNCHANGED. K011 report/JSON/provenance published; msg 0013 requests canonical binaries/build metadata. Dependent jobs held. Local comparison helper artifacts/local-only/g5070/compare_results.py checks unique records, aggregates and paired flips; self-checks passed.
- Reference ../x1-comms/g5060/results/J018/x1g-x3-pool-v86h-01.json: 108/172, engine 2.0.0, engine hash 85aa7167b44db7cea97509f55e997750520e33d644e9f4f90d6128c50eba1d21.
- K014 pending: 33 supplied lines; x3mf vs v92 expected 96/172, own mf-g5070 baseline required. Exact window name X1_ANTIFEED_WIN. A3_ITEMS has an unconditional earlier define in common.h: check actual --set effect without editing bot source.
- K012/K013 pending; no implemented features or measured strength results yet.
- Additional unchanged v92 native build equals x3 byte-for-byte (bf3f65d009c0); canonical hash still unresolved. Binary section manifests accompany K011.
- Independent combat prework is in analysis/K011-combat-prework.md: three exact reproduced-loss replays decoded and candidate-side death counts reconciled to native summaries (72/50/58). Important findings: actual equipment stats already observed, G3 arrival-DPS optimism, late backoff safety override, kOrder=1 makes pow simplification a weak fuel hypothesis, EQ threshold != observed retreat frequency, static guest caches are not team caches.
- Local static preparation artifacts/local-only/g5070/k014-manifest.json contains all 33 unique lines. No dependent runs started. Replay analysis outputs artifacts/local-only/g5070/k011-loss-fights.json, k011-loss-summary.json, k011-hurt-contact.json; raw replay copies in .../replays remain local.

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
