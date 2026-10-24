# Fresh laptop recovery

The active project is at the repository root. Start a new agent with NEXT_AGENT_PROMPT.md and HANDOFF.md.
The direct-policy bot is still under construction. New heads are untrained, and the checked-in release default
keeps them off. A backup does not turn the current work into a trained or finished bot.

## Get everything

The exact saved development environment is Windows x64, Python3.12.14, cambc3.0.5 / engine1.0.3,
WASI SDK33 / clang22.1.0, and the bundled native GCC. A different operating system needs its own native tooling;
the archived Windows binaries cannot run there. Install Git with Git LFS and Python3.12+ on the new laptop first.
Sign in to GitHub with an account allowed to read this private repository.

```powershell
git lfs install
git clone https://github.com/Infosuii/neural-networkk-battlecode.git
cd neural-networkk-battlecode
git lfs pull
python tools/recovery_archive.py verify --full
python tools/recovery_archive.py restore --scope all --dest recovery/restored
python tools/configure_recovery.py --install-cli-cache
. ./.venv/recovery-env.ps1
./.venv/Scripts/python.exe -m unittest discover -s tests/python
./.venv/Scripts/python.exe tools/run_cpp_tests.py
./.venv/Scripts/python.exe tools/check_teacher_exact.py
```

Restore verifies every output file's SHA256 and refuses to overwrite an occupied destination. Archive verification
checks all pack checksums, every block, all manifests and the saved Git histories. No game, training, parameter
update, login to Battlecode or submission occurs during these checks. Keep enough free disk space for the packed
download, approximately120GB of restored originals, and new build scratch space. Exact sizes are in
recovery/snapshot.json after the snapshot finishes. Git LFS must retrieve the real packs, not leave pointer files.

The configuration step recreates a local virtual environment using the exact offline packages from the saved
environment. It rewrites config/paths.json for this clone, sets up a PowerShell environment file, and, with
--install-cli-cache, restores the official cambc tool cache into the new user's LOCALAPPDATA/cambc. It does not
modify bot source or the reference builds. Compiler execution can still require approval in a restricted agent.

## What is preserved

- All project source, models, schemas, tools, tests, reports, prompts, contracts and local Git history.
- Ignored build scratch, CMake caches, replay files, evaluation stdout/results and generated model fixtures.
- The entire local Cambridge Battlecode folder, including earlier experiments, archives, analytics and databases.
- The external official CLI workspace, SDK/runtime cache, maps, native compiler and exact Python base runtime.
- Exact installed Python package versions, the previous environment and its package/download caches.

recovery/files.jsonl.gz maps every original file to its source root, relative path, bytes, modification time,
SHA256 and ordered content blocks. recovery/objects.jsonl.gz maps blocks to standard ZIP packs. Duplicate content
is stored once. These two manifests plus the packs allow a lossless file restore independently of Git checkout.
recovery/histories/ holds git bundle --all snapshots for nested repositories, preserving their committed history
without archiving machine-specific Git credentials. The active repository's history is also pushed normally.

Authentication files and recognizable credentials are excluded and listed by path/reason in
recovery/exclusions.json without their contents. Directory/file links are recorded there for inspection. Read
recovery/source_errors.json: a nonempty list means a source file/root could not be saved, and completion must not
be claimed until resolved. The old configured `21 october matches` folder was absent before this backup;
all available dated archives, including23102026, are preserved. Configuration points at the available archive
folder rather than pretending the missing original path was recovered.

## Preserve experiment meaning

Old manifests, cached paths and historical receipts retain their original machine paths and dates. Do not rewrite
them as new runs. Only config/paths.json is regenerated. CMake caches inside restored scratch trees are evidence;
use fresh build directories. tools/check_teacher_exact.py now always creates a clean scratch directory because
a failed compiler launch previously left an empty Release optimization cache, producing a misleading mismatch.

The inherited draft network is a separate historical trained model. Every new v1/v2 head is untrained. The target
is approximately80% direct neural ownership of important decision opportunities after integration and later
validation; that percentage has not been reached or measured. No new training is authorized by this backup task.

## Snapshot and publication status

The authoritative data snapshot receipt is recovery/snapshot.json. A complete archive requires status=complete,
source_errors=[], all listed packs pushed and a successful remote-clone recovery check. Publication verification
is recorded separately under evaluation/results/recovery_*.json. Do not treat creation of a GitHub repository or
a source-only push as proof that all large data has reached GitHub.
