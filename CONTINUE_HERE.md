# DOOMSDAY Zero: continue the pure algorithm bot build

**Active branch: `build/pure-algorithm-zero`.** The user resumed work on 2026-10-28
and authorized a clean-slate algorithmic bot, local tests, read-only replay downloads,
and pushing this build branch to `Infosuii/neural-networkk-battlecode`.

Read [the current continuation state](CLAUDE_HANDOFF.md) first, then
[the DZ architecture handoff](research/dz/HANDOFF.md),
[results and failures](research/dz/RESULTS.md), and
[the bot guide](bots/dz/README.md). Build work and all supplied research are committed
on this branch. Historical "paused / not yet approved" statements below and in the
planning documents do not supersede the user's current build authorization.

The starter completed 292 release games with zero faults/fuel-outs but lost every
contested game against v65/v76. It is a foundation, not a finals candidate.

Fresh Windows x64 machine (from the clone root):

```powershell
git clone --branch build/pure-algorithm-zero https://github.com/Infosuii/neural-networkk-battlecode.git
cd neural-networkk-battlecode
python tools/continuation_checkpoint.py verify
python tools/continuation_checkpoint.py restore --install-runtime
python tools/dz_support.py verify
python tools/dz_support.py restore
python tools/dz.py verify
python tools/dz.py build
python tools/dz.py host
```

Python 3.12+ and Git are required; native host tests additionally need C++20 g++
(MSYS2 UCRT64 on this laptop), on PATH or selected by `DZ_CXX`. DZ's build/test
runner uses only Python's standard library and repo-relative paths. Do not commit
`config/paths.json`, which belongs to this laptop. No login is required for local
builds or matches. The large original archive supplies the pinned Windows official
runtime; the DZ support archive supplies 2,931 offline evidence files, including the
SA-IDLE-v76 calibration replays and the deep-study reports at 19109c4. Both restorers
verify content and refuse to overwrite different source/evidence files.

Other operating systems need their matching official CLI/toolchain; only Windows
x64 restoration has been packaged/tested. Node 24 is needed only for the optional
replay decoders, with `NFS_REPLAY_ENGINE=2.0.0`.

Do not submit, activate, create ladder match groups or run ladder duels without
separate authorization. Never copy old bot code into DZ. The next agent should
finish engine conformance and validate the objective model before enabling the
economy auction or EE. Preserve the registered release holdout.

The previous checkpoint guide is retained at
[continuation/RESEARCH_CHECKPOINT_HANDOFF.md](continuation/RESEARCH_CHECKPOINT_HANDOFF.md).

---

# Historical paused research checkpoint (superseded for active build status)

Research was paused at the user's request on2026-10-28. **No live change is authorized.**
Read [the precise handoff](research/v81/HANDOFF.md), [the mission](research/v81/MISSION.md),
[research results](research/v81/RESEARCH.md), and [the new five-loss analysis](research/v75/MG_18208504.md).
V76 is the established local comparator; V80-85 are not proven upgrades. Repo v74 is live platform68.

## Fresh Windows laptop

Install Git/Git Bash, Python3.12+ and Node24 (tested here:24.20.0). Clone this checkpoint branch (the GitHub checkpoint commit is the
authoritative snapshot; do not assume main has the newest research). In Git Bash:

```bash
git clone --branch checkpoint/research-v85-2026-10-28 https://github.com/Infosuii/neural-networkk-battlecode.git
cd neural-networkk-battlecode
python tools/continuation_checkpoint.py verify --full
python tools/continuation_checkpoint.py restore --install-runtime
python -m venv .venv
.venv/Scripts/python.exe -m pip install numpy==2.5.2
```

The restore command verifies all archive hashes and installs the saved official Windows SDK/CMake/Ninja/replay
assets into `%LOCALAPPDATA%/cambc`. It restores ignored evidence into its original repository paths and never
overwrites Git source. If a different official runtime is already installed, restore without `--install-runtime`
and use the extracted `artifacts/portable-runtime` separately. Replay tools accept `NFS_REPLAY_ASSETS` pointing to
its `assets/<hash>/visualiser/assets` directory containing the pinned engine2.0.0 Wasm. No credentials or login
sessions are archived.

Configure paths for this clone:

```bash
.venv/Scripts/python.exe tools/configure_dev.py --cli tools/vendor/cambc.exe
export PYTHONPATH="$PWD/python" NFS_REPLAY_ENGINE=2.0.0
export TMP="$PWD/artifacts/tmp" TEMP="$PWD/artifacts/tmp" PYTHONDONTWRITEBYTECODE=1
```

`configure_dev.py` expects native g++. Install MSYS2 UCRT64 if needed; it is used for standalone C++ policy parity
checks. The official Wasm bot build uses the restored WASI toolchain. Python fitting here needs only NumPy, not CUDA
or sklearn. Do not run the older full training/recovery workflows. `config/paths.json` is laptop-specific and must
not be committed. The source and official CLI/SDK/maps are already vendored.

The user must log in separately for official read-only ladder requests. No login is needed for local builds/replays.
Never run submit/activate/ladder_duel without explicit approval. No experiments should start until the user resumes.

Suggested first prompt for the new agent:

> Continue the paused DOOMSDAY structural research. First read CONTINUE_HERE.md and research/v81/HANDOFF.md, then the
> saved mission and MG_18208504.md. Verify the portable evidence and build provenance. Preserve frozen V76/V80.
> Resume the research loop from the recorded failures and objective-conversion questions. Do not submit or activate.
