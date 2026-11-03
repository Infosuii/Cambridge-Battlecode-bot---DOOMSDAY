# g5070 resume — current campaign finished

Updated 2026-11-03 00:53 UTC. **Current PC queue is complete. Do not restart completed experiments.**

## Instructions in force
- PC0035 accepts exact Linux K011 reproduction and establishes default x3 hashbf3f65d009c0. Compare strength only against own Linux bases.
- PC0036 cancels K013 on g5070, transfers future fights work to5060, starts no new run after2026-11-03 02:15UTC and stops by02:30UTC. Do not resume open-ended engineering without reassignment.
- PC0037 requires a result/STATUS commit at least every30minutes while working; a45-minute silent machine may be taken over. Always read pc/msgs before restarting.

## Final state
- K011 PASS:108/172;172/172 exact records;0 faults;186 fuel-outs. PC0035 explicitly supersedes original Windows hash requirement.
- K01433/33 supplied lines complete, no line>=102; bestbag80=101. A3_ITEMS1/2 both baseline-identical. No promotion/validation owed.
- J0267 stolen lines complete;5060 completed other20; coverage27/27, duplicates0. No rows remain.
- K012 baseline341/516, style329/516, G3secure335/516; both fail. No styled/maze gate owed.
- K013 cancelled; pre-existing isolated prototype and cards archived only. No bot feature integrated or promoted.
- No active process, match or benchmark. No pending assigned validation. Final report results/X3-2026-11-03.md; verification results/X3-VERIFICATION.json.

## Git/checkouts
- Code /home/om/Projects/Battlecode/x1work, branch build/z-plan-5070, commite090ae389eede7104d02afada64317bfc6d8ca56; pushed to own branch only.
- Parent upstream6f462c4; own contribution touches only tools/g5070/. Default build after safe post-benchmark refresh remainsbf3f65d009c0419d2b0f04bdfab68b85f397ce6cb2350a36ab8782d4d74cd46a.
- All benchmark capsules preserve original9c1bbde2d5cee6ab53235019027cb452a733b340 provenance. Do not pretend they were run on refreshed source.
- Comms /home/om/Projects/Battlecode/x1-comms, branch comms/x1. Write onlyg5070/. Use SIDE=g5070 bash tools/x1_comms.sh pull/push; never merge comms into code.
- Local code checkout intentionally retains generated SEED_LEDGER.md additions, untracked run evidence under research/dz/runs/, and compiler metadata. These are our generated evidence, not pending bot-source work. Do not delete/reset them. Ledger was safely stashed and restored during the completed rebase; no stash remains from that operation.

## Environment
PY=/home/om/Projects/Battlecode/.venv/bin/python; DZ_CAMBC=/home/om/Projects/Battlecode/.venv/bin/cambc. Python3.12.16,NumPy2.5.4,official CLI4.0.0 (SHA552056aab1b99a6626597b6aaf0ae38f967709626f90f2d6926c4510ca929eb4). CachyOS,20CPUs,30GiB RAM.18 benchmark workers used;0 active. WASI SDK33.0/Clang22.1.0 bundled by official CLI. GitHub auth works via gh keyring outside restricted execution. No credentials saved in artifacts.

## Evidence and exact commands (do not rerun unchanged)
- research/dz/runs/x1g-*-g5070-*/results.json:50 runs. Frozen source/Wasm/provenance/logs/raw replays: artifacts/tmp/dz/<run>/; per-run logs artifacts/tmp/<run>.log.
- K011: SETS=pool OPPS=v86h WORKERS=18 bash tools/x1_gate.sh x3 repro-g5070.
- Own base: SETS=pool OPPS="v92 v86h x1bru" WORKERS=18 bash tools/x1_gate.sh x3 mf-g5070 "--set X1_MAPFIT=1".
- K014 exact33 switches: artifacts/local-only/g5070/k014-manifest.json; state k014-state.json; log k014-run.log. Completed.
- J026 manifest j026-manifest.json; state j026-worksteal-state.json; log j026-worksteal.log. Completed7 safe rows. Combined coverage verified against current5060 results.
- K012 exact3 configurations and comparisons: k012-state.json; runner k012_run.py; log k012-run.log. Completed. A transient concurrent comms push was safely rebased/retried, with no match rerun or lost result.
- tools/g5070/compare_results.py is the reusable record comparator. tools/g5070/prototype/ is explicitly unintegrated pre-cancellation prework,15 host correctness cases only. No match strength evidence.
- Default build check after refresh: cambc build bots/x3 --release --output artifacts/tmp/g5070-final-default.wasm; exactbf3f65d009c0 hash verified.

## Handoff research (not authorization to continue K013)
Read analysis/K011-combat-prework.md, analysis/K014-secure-fuel.md, ideas/I-70-01.md and I-70-02.md. Raw replays stay local; compact diagnostics published. Prototype does not solve shared-state freshness, target-motion uncertainty, path observability or downstream fuel starvation.5060/PC should not infer a winning combat change from it.

Before any newly assigned work: inspect Git state, pull comms, read new PC messages/jobs and takeover status, then honor dependencies/cutoffs. Never push other code branches, alter competition submissions, or authenticate to the competition CLI.
