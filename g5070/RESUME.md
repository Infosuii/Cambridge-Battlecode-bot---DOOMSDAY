# g5070 continuation — x3 campaign

Updated 2026-11-03 00:22 UTC. K011 accepted; K014 active, K012/K013 pending.

## Latest instruction overrides
**PC 0036 (read00:34UTC): K013 is CANCELLED for g5070.** No further open-ended combat engineering on this machine. Finish K014, work-steal J026 leftovers, then K012 if time remains. Start no new run after2026-11-03 02:15UTC; finish/stop by02:30UTC. Unfinished work goes to5060. Preserve pre-existing isolated prototype as handoff; do not integrate or strength-test it as K013. Write final status with exact done/not-done jobs.

PC 0035 explicitly accepts K011 and establishes **bf3f65d009c0 as the Linux x3 default reference**. Use this hash for future default-off checks. Compare only against our own Linux mf-g5070 runs, never Windows reference strengths. Historical unresolved-hash notes below are superseded by 0035. Do not rerun K011. Own mf-g5070 baseline is running on v92/v86h/x1bru at 18 workers, then K014's 33 supplied lines.

## Latest checkpoint (00:45 UTC)
K014 supplied33/33 complete,0 promotions. J026 safe work stealing7 complete: bhold95,escort95,soak6490,hiderecwt100,hiderec99,beliefwt97,belief97. No duplicate reported5060 line; need13/need115/need15 reserved for its current batch. Next K012 driver artifacts/local-only/g5070/k012_run.py; state k012-state.json, log k012-run.log, report g5070/results/K012.md. It reuses3 exact own mf pool baselines, runs mfst/mfsec full pools, validates styled/maze vs v92/x1bru on any qualifying pool line. Current benchmark source pinned9c1bbde for exact provenance; fetched origin banking-only default-off6f462c4 was deliberately not introduced mid-campaign. K013 CANCELLED per0036; no further feature integration/tests. Deadline: no new runs after02:15UTC, stop by02:30UTC. PC0037 adds45-minute inactive-machine takeover rule; publish at least every30minutes (currently each line).

Historical checkpoints below are superseded by this block.

## Current checkpoint (00:34 UTC)
**00:40 update:** K014 supplied33/33 complete with0 promotions. Best bag80=101/172 (+5,7 gained/2 lost,z1.667), below102. A3_ITEMS1/2 both hash8df6f3fe1c40 and match baseline172/172: null builds due unconditional source override. Do not rerun. Next is J026 work stealing: `G5070_SWEEP=J026 /home/om/Projects/Battlecode/.venv/bin/python artifacts/local-only/g5070/k014_run.py > artifacts/local-only/g5070/j026-worksteal.log 2>&1`. Manifest j026-manifest.json (27 lines reversed); state j026-worksteal-state.json; results K014-J026-worksteal.md. It checks latest5060 results before each line, skips reported lines and reserves next3 unpublished forward lines for the active5060 batch, claims its selected bottom-up line in STATUS before running, and pushes each completed stolen line. PC0036 cutoff enforced in gate entry. K012 remains after work stealing; K013 cancelled.

Own Linux mf baseline complete: 96/115/130=341/516; hash8df6f3fe1c40; fuel-outs171/189/188. K014 23/33 supplied screens complete; best bag80=101 (<102), no promotion. Results/provenance/comparisons under g5070/results/K014; local orchestrator artifacts/local-only/g5070/k014_run.py, manifest k014-manifest.json, authoritative state k014-state.json, log k014-run.log. It reuses completed own runs and checks full map/engine/opponent provenance. Resume the orchestrator after reading updated PC instructions; it skips completed lines. At ten-minute poll it checkpoints/pushes before pull, then exits for instruction review. The first poll hit unstaged per-line report changes and stopped safely at23; fixed by publishing before pull. No benchmark evidence lost, no reruns needed.

Command: `/home/om/Projects/Battlecode/.venv/bin/python artifacts/local-only/g5070/k014_run.py >> artifacts/local-only/g5070/k014-run.log 2>&1` (code checkout, network/cache-capable execution for CLI and g5070-only communication pushes). No source edits until K014 is finished. After supplied33, read J026 and work-steal unfinished rows from the bottom; skip rows already reported by5060, avoid its active line. Then K012 and K013.

Prototype at artifacts/local-only/g5070/prototype/g70_arrival.h and arrival_test.cpp:15 correctness cases passed with g++ C++20 / X1_G70_COORD=1. Isolated, not included in active bots; no strength claim. Idea cards I-70-01 and02 describe queued style/coordination work. Native official replay API GetSharedMemorySize returned8bytes. New fuel-context diagnostic and concrete Heart failure in analysis/K014-secure-fuel.md; source helper artifacts/local-only/g5070/fuel_context.mjs. Raw replays stay local.

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
