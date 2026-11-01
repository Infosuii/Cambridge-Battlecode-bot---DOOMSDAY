# Continue DZ on a fresh laptop

Recovery was checked from a clean Git export on Windows: current/best and two
older frozen runs, all20 reference files, the tracked runtime digest and the
portable CLI tests passed. No installed runtime/assets were used for evidence
verification. See the exact [verification report](research/dz/legacy-transfer-2026-11-01/FRESH_CLONE_CHECK.json).

Latest work is on **`experiment/dz-lifecycle-repair-2026-11-01`**, not the old
default-branch handoff. Gameplay work is paused by the user. Repository sync and
this portability check were subsequently authorised; they do not resume matches,
release changes or submission. Current bot source is unpromoted candidate24.

```sh
git clone --branch experiment/dz-lifecycle-repair-2026-11-01 https://github.com/Infosuii/neural-networkk-battlecode.git
cd neural-networkk-battlecode
```

Read these in order:

1. [Paused handoff](research/dz/legacy-transfer-2026-11-01/HANDOFF.md).
2. [Next-agent prompts](research/dz/legacy-transfer-2026-11-01/NEXT_AGENT_PROMPTS.md).
3. [Decision-transfer roadmap](research/dz/LEGACY_TRANSFER_ROADMAP.md).
4. [Original request](research/dz/legacy-transfer-2026-11-01/ORIGINAL_REQUEST.md)
   and [later steering](research/dz/legacy-transfer-2026-11-01/USER_STEERING.md).

## Already in Git

- Current DZ source, local comparator sources v76lab/v81hl, SDK4 headers,
  all70 published maps, generated correctness fixture, tests and analysis tools.
- All24 new experiment capsules covering98 cells, including failures and
  exact frozen source, binaries, logs, summaries and native replay bundles.
  Earlier lifecycle capsules, including05 and10, are retained too.
- All20 retained strong-team reference files: the original4 replay downloads,
  native payloads, full summaries, personal-view traces and retrieval metadata.
  They are in a4.9MB compressed archive with a SHA-256 manifest.
- The unmodified official **Windows x64 CLI4.0.0** is already tracked at
  `tools/vendor/cambc.exe` (82,220,032 bytes), with its digest in
  `tools/vendor/manifest.json`. Other operating systems need their native
  official CLI4.0.0; set `DZ_CAMBC` to its executable or put `cambc` on PATH.

## Recover ignored working folders without the old laptop

Python3.12+ is enough to restore and verify evidence. Run from this checkout:

```sh
python tools/dz_restore_run.py --references
python tools/dz_restore_run.py --run dz-transfer-first-phase-24
python tools/dz_restore_run.py --run dz-transfer-execution-budget-15
python tools/dz_restore_run.py --run dz-cycle-execution-repair-10
python tools/dz_restore_run.py --run dz-cycle-collision-v76-05
```

The helper reconstructs the old handoff's `artifacts/tmp/dz/<run>/` and
`artifacts/local-only/dz-cycle-reference-2026-11-01/` paths. It checks hashes,
rejects unsafe archive paths and refuses to overwrite different existing files.
Every other retained capsule can be restored by its run name. A new destination
inside the checkout can be supplied with `--destination`. Frozen source is at
`artifacts/tmp/dz/<run>/build/candidate/src`; reuse with `tools/dz.py --source`
as described in the handoff. Do not treat old absolute paths in provenance as
requirements for the new laptop.

## Local dependencies after explicit gameplay resume

- Python3.12+; the DZ runner/restore/report tools use the standard library.
  Neural training packages, CUDA and the historical training data are unnecessary.
- Official CLI4.0.0 / engine2.0.0. Windows uses the tracked executable by default;
  native installs on other platforms use PATH or `DZ_CAMBC`.
- A native C++20 compiler for host tests, selected with `DZ_CXX` if necessary.
  Windows can use MSYS2 UCRT64 g++; macOS/Linux can use their supported compiler.
- Node20+ for offline replay analysis.

The first official build downloads its pinned WASI toolchain into the CLI's
cache. The official `cambc view <replay>` installs the visualiser assets. These
installable runtime caches and operating-system packages are not copied from
the old machine. No login or credentials are needed for local builds, restored
evidence or local games. Online activity remains unauthorised.

For engine2 offline analysis, set `NFS_REPLAY_ENGINE=2.0.0`. The loader searches
the usual Windows, macOS and Linux data/cache locations; alternatively set
`NFS_REPLAY_ASSETS` to the official `visualiser/assets` directory. Pinned hashes
are checked before loading it. Historical tools default to engine1.0.3, so do
not omit the engine selection for current replays.

```powershell
# Windows examples, after explicit resume:
$env:NFS_REPLAY_ENGINE='2.0.0'
python tools/dz.py build
python tools/dz.py host
```

`config/paths.json` contains historical/machine-specific settings. The DZ runner
does not require it. Do not overwrite it or reuse another laptop's paths. Local
optional settings can use `config/paths.local.json` or documented environment
overrides. Generated build directories, compile databases, unrelated historical
binaries and user credentials are not continuation inputs.

## Known WIP state is intentionally preserved

The bot is **not competitively accepted**. Candidate15's914-versus498 improvement
and subsequent regressions are all recorded. Candidate24 still loses all six
contested development games. The new host test in `sequence_test.cpp` attempts
to copy a deliberately noncopyable search object; fixing that test fixture is
the first resume task. It has not been silently fixed or hidden by this sync.
The handoff lists the missing physical crew execution proof and next steps.
