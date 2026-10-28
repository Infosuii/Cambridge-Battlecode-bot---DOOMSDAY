# Continue DOOMSDAY Zero — 2026-10-28

## Current authorization and branch

- Branch: `build/pure-algorithm-zero`, remote `origin`:
  `https://github.com/Infosuii/neural-networkk-battlecode.git`.
- User explicitly approved pushing this branch to that repository. Commit/push
  reviewable checkpoints. Build fresh algorithmic C++; **no old bot code in DZ**.
- User confirmed the existing 70-map pool is the target and authorized read-only
  top-team replay downloads. Do not assume approval for ladder games or activation.
- Never submit, activate, create match groups, or run `ladder_duel.py run` without
  separate authorization. The live bot is unchanged. v76 is the local comparator;
  final fallback selection remains the user's decision.
- Preserve this laptop's pre-existing `config/paths.json` edit and unrelated
  generated/untracked artifacts. Stage explicit paths, never `git add .`.

## What is built

Fresh `bots/dz/src/` implementation, using the official SDK and standard library:
kernel/Actuator/stale-turn guard, budgeted startup and fields, observation, camp
memory and contracts, claim codec, research-prior draft, fixed gear, nearest-group
farming/capture, basic banking and recovery, payload-based attack/reset/damage/CC/
shield spells, dynamic movement and ward placement. Detailed scope and omissions:
`bots/dz/README.md`.

**Advanced models remain disabled/unimplemented.** No auction, validated ObjModel,
EE, crew stance, optimized gear, opening rollout or per-map draft tables yet.
This is a tested walking skeleton. It is not a strong bot or a release candidate.

## Verified results and failures

- Host: 1,536 codec cases plus stale guard, contracts, ledger and bank-rule edge checks pass.
- Same frozen release source: `dz-pool-idle-02` 140 games, `dz-pool-v65-01` 140,
  `dz-v76-screen-01` 12; **0 faults, 0 fuel-outs**, worst pooled-run p99 64,076.
- Against idle: mean 917.1 banked; some maps win on the gold tiebreak.
- Against v65: **0/140 wins**, mean 182.0 banked. Against v76 screen: **0/12**.
- Major camp deaths on 00contest, 01starvation, 02guardians, 02the-pack and
  01shortcut. Models/crews/survival are essential, not optional polish.
- Read `RESULTS.md` for retained failed campaigns and `CONFORMANCE.md` for the
  exact observed/pending mechanics. G0/G1/parity/promotion/holdout are not passed.
- `python tools/dz.py verify` authenticates all completed experiment capsules.

## Next implementation milestone (do this before tuning)

1. Finish CT-11 camp cadence/targeting and CT-7 movement/spell allowances; CT-8/9
   visibility; CT-16/17 channels; CT-24–26 capture/credit/reset. Add automatic
   diagnostic transcript assertions and the complete canonical CT-27 fingerprint.
   Keep deliberate-fault/fuel-out tests isolated from candidates.
2. Extract objective arrival/clear/camp damage/capture data from the preserved
   **SA-IDLE-v76** replays. Build pure ObjModel and host tests, then perform V-M1
   offline (clear error <=20% median, bias <=10%, damage bias <=20%, arrival <=3 rounds).
   No previous bot implementation may be copied; measurements/evaluation tools are allowed.
3. Fix camp survival and add validated crew allocation/single capturer/cluster
   circuits behind explicit flags, one mechanism per experiment. Begin with the
   highest-death idle maps as correctness cases. Do not try to rescue an invalid
   model with threshold tuning.
4. Run idle non-inferiority and a matched v76-on-idle R250/R500 benchmark. Build
   the timeline extractor before claiming the idle parity gate; final totals alone
   cannot prove opening or income parity.
5. Only after conformance/model gates, add the auction, marginal gear and hazard
   banking, then threat/EE offline calibration and controlled contested experiments.

The full 21-file design is in `research/zero-bot-plan-2026-10-28/`; it was read
before implementation. It supersedes the on-v76 design, but is not infallible:
unchanged shared slots cannot prove age; parity/TTL alone cannot prove message
freshness; group >=112 must not alias group 111. See `DECISIONS.md`.
Also check `research/v81/RESEARCH.md`: the broad historical "step-away" metric was
corrected (46.6% vs 42.9%, not the advertised factor-of-two gap). Do not tune against
that invalid headline. The earlier deep-analysis reserved set is spent.

## Portable source/evidence and fresh-system commands

Read root `CONTINUE_HERE.md`. No venv, NumPy, credentials or machine config is
needed for `tools/dz.py`; it uses the vendored official CLI and root CMake/SDK.

```powershell
python tools/continuation_checkpoint.py verify
python tools/continuation_checkpoint.py restore --install-runtime
python tools/dz_support.py verify
python tools/dz_support.py restore
python tools/dz.py verify
python tools/dz.py host
python tools/dz.py build
python tools/dz.py smoke --name UNIQUE-IDLE-RUN --pool
python tools/dz.py smoke --name UNIQUE-V65-RUN --pool --opponent v65
```

- `continuation/checkpoint-2026-10-28/`: existing SHA-authenticated official Windows
  runtime and earlier research evidence. Git contains every part; no LFS download required.
- `research/dz/supporting/`: 61,643,106-byte archive in two <=40 MiB parts, 2,931 files:
  full SA-IDLE-v76 / SA-P-base / SA-C-base summaries/replays/build provenance, plus
  the deep-study research, next-bot brief and loss cases at 19109c4. SHA verified.
  Restore into repo-relative paths; no different file is overwritten. The deep-study
  snapshot restores under `research/dz/supporting/deep-19109c4/` to preserve history.
- `research/dz/runs/*/evidence.zip`: exact candidate and benchmark source, both Wasm,
  logs, full native summary and replay per schedule cell. Current source is not
  substituted into old experiments. ZIPs were fully CRC/content-hash verified.
- `PORTABILITY_VERIFIED.json`: a fresh source-only Git export (no local settings
  or prior bot build cache) rebuilt byte-for-byte to the tested Wasm hash. This was
  tested on the same Windows host using its installed official toolchain; it is
  not a claim of rerunning installation on a second physical machine.
- Replay decoding: Node 24, `NFS_REPLAY_ENGINE=2.0.0`; extract `replay.repl26a`
  from each bundle before decoding. The old camp-regeneration script hard-codes
  the previous laptop path; use a portable copy/import when running it elsewhere.
- Native tests: install C++20 g++ or set `DZ_CXX`. Official bot builds use the
  restored WASI SDK, independent of the native compiler.

## Evaluation discipline

Read `HOLDOUT.md` and `SEED_LEDGER.md` before experiments. Seeds 101–110 dev,
111–120 validation, 121–124 once-only frozen release holdout; 3/4 prohibited.
DZ v0 is deterministic and does not consume a seed. Do not relabel duplicate
identities as independent samples. Bug/geometry checks can use all maps; parameter
selection must respect the held-out-map partition. No new top-team download was
needed for this starter; existing data was enough.

## Scheduled continuation

A single active heartbeat, `continue-dz-build-once`, is scheduled for **2026-10-29
04:07 Europe/London** in this chat. It resumes this work once and creates no
additional schedules. It depends on this machine/app being available and account
usage being available. The original interval/count attempts were rejected; the
successful schedule has one future occurrence only. Do not duplicate it.

The starter checkpoint is intended to be committed and pushed on this branch;
verify `git status` and the remote HEAD on resumption. Use the milestone list above
for further implementation. The measured current Wasm SHA-256 is
`c5486461a5f8704409f5cf9293a3ca20a49ba7f53152732ba20a068e2d2a9872`.
