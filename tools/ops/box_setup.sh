#!/bin/bash
# One-time setup of the 5070 Ti box (docs/HANDOVER_5070TI.md). Safe to re-run. Prints one line per step; on a
# failure it stops and prints the reason. Needs: Windows, Git Bash, winget, internet. No credentials are entered.
set -e
cd "$(dirname "$0")/.."
say() { echo "[setup] $*"; }

if ! py -3.12 --version >/dev/null 2>&1; then
  say "installing Python 3.12"; winget install --id Python.Python.3.12 -e --scope user --silent --accept-source-agreements --accept-package-agreements >/dev/null
fi
if ! command -v node >/dev/null 2>&1 && [ ! -x "/c/Program Files/nodejs/node.exe" ]; then
  say "installing Node.js LTS"; winget install --id OpenJS.NodeJS.LTS -e --silent --accept-source-agreements --accept-package-agreements >/dev/null
fi
VENV="$HOME/nnbc-venv"
[ -x "$VENV/Scripts/python.exe" ] || { say "creating venv $VENV"; py -3.12 -m venv "$VENV"; }
PYV="$VENV/Scripts/python.exe"
say "installing Python packages (CUDA torch for the RTX 5070 Ti)"
"$PYV" -m pip install -q --upgrade pip >/dev/null 2>&1 || true
"$PYV" -m pip install -q numpy==2.5.2 scikit-learn==1.9.1 wasmtime==49.0.0 >/dev/null
"$PYV" -m pip install -q torch --index-url https://download.pytorch.org/whl/cu128 >/dev/null
"$PYV" -c "import torch; print('[setup] torch', torch.__version__, 'cuda', torch.cuda.is_available())"
say "configuring machine paths (config/paths.json, kept out of git)"
"$PYV" tools/configure_dev.py --python "$(cygpath -m "$PYV")" --cli tools/vendor/cambc.exe --native-cxx "$(cygpath -m "$PYV")" >/dev/null
git update-index --skip-worktree config/paths.json
say "smoke build (downloads the compiler once, about 600 MB)"
export PYTHONPATH="$PWD/python" TMP="$PWD/artifacts/tmp" TEMP="$PWD/artifacts/tmp"; mkdir -p artifacts/tmp
"$PYV" -c "from pathlib import Path; from nfs import engine; engine.official_build(Path('bots/v74h'), Path('artifacts/tmp/v74h.wasm')); print('[setup] build ok')"
rm -rf bots/v74h/.cambc bots/v74h/compile_commands.json
say "done: threads $(nproc), now start the runner (see the handover)"
