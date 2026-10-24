# Development on a fresh laptop

This setup supports editing, building, tests and engine checks. Training and the large original datasets stay
on the original laptop. The tested platform is Windows x64 with Python3.12 and native GCC16.2.

## Install normal development tools

Install Git, Python3.12 and native g++ (MSYS2 UCRT64 GCC on Windows). With a normal MSYS2 installation, install
mingw-w64-ucrt-x86_64-gcc and use C:/msys64/ucrt64/bin/g++.exe. Keep the UCRT64 installation in its normal layout;
renaming an isolated compiler folder can break its standard-header search paths.

The repository includes an unmodified official cambc3.0.5 Windows CLI in tools/vendor/cambc.exe, with its SHA256
in tools/vendor/manifest.json. It uses the official SDK/tool cache; first official builds can download missing
WASI SDK33/CMake/Ninja assets. On another operating system install the official native CLI and pass --cli.

## Clone and prepare a separate CPU development environment

```powershell
git clone https://github.com/Infosuii/neural-networkk-battlecode.git
cd neural-networkk-battlecode
New-Item -ItemType Directory -Force artifacts/tmp | Out-Null
$env:PIP_CACHE_DIR="$PWD/artifacts/tmp/pip-cache"
$env:TMP="$PWD/artifacts/tmp"
$env:TEMP=$env:TMP
python -m venv .venv-dev
./.venv-dev/Scripts/python.exe -m pip install -r requirements-dev.txt
./.venv-dev/Scripts/python.exe tools/configure_dev.py
. ./artifacts/tmp/dev-env.ps1
```

requirements-dev.txt uses CPU-only PyTorch2.11.0 and pins the remaining packages. This environment is separate
from the original laptop's existing CUDA training environment. That existing environment and all its data remain
unchanged. If g++ is elsewhere, pass --native-cxx with its absolute executable path. The configuration step writes
this clone's tool paths and points maps/SDK paths into this repository. Existing historical/training paths remain
explicitly original-laptop-only; it never guesses or substitutes a training dataset.

## Verified fresh-clone result

The main branch was cloned normally from GitHub and configured with a separately installed CPU-only development
 environment:259 Python tests,11native targets460checks, and official teacher_exact byte identity all passed.
 See evaluation/results/development_clone_verified.json. No raw training archive or old environment copy was
 needed. Native GCC remains a normal installed dependency; the exact official CLI is in the repository.

## Verify

```powershell
./.venv-dev/Scripts/python.exe -m unittest discover -s tests/python
./.venv-dev/Scripts/python.exe tools/run_cpp_tests.py
./.venv-dev/Scripts/python.exe tools/check_teacher_exact.py
```

These run synthetic checks and an official release build; no training or submission. Expected all-off Wasm SHA256:
eb0ea88fc734661cf93935e5eab3c79e7a2658c7d05b7965593fbeb22d9d4442. Agent execution restrictions may require approval
for installed compiler/build tools. Use a fresh CMake build directory; the checker already does this.

The repository contains the frozen reference Wasm files and82small evaluation replays needed by the tests.
All40local maps are reused benchmarks, not newly held-out maps. New direct-policy model artifacts are untrained;
the inherited draft model remains separate. Keep training disabled until the user explicitly authorizes it.

Only Git-tracked development files are shared. data/cache, checkpoints, bulk runs, virtual environments and
artifacts/tmp or artifacts/local-only remain local. Commit useful test evidence explicitly, not entire run folders.
