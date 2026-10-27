"""Build the offline mimic kernel (tools/mimic/kernel.cpp + bots/mimic/src/core.cpp) to artifacts/tmp/mimic/kernel.wasm.

  python tools/mimic/build_kernel.py

Same compiler (the cambc wasi-sdk) and the bot's release code-generation flags (-O3 -msimd128), so the core's float
arithmetic matches the bot's. No exceptions or libc++ are needed: the core uses neither.
"""
from pathlib import Path
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'artifacts/tmp/mimic/kernel.wasm'


def wasi_sdk():
    configured = json.loads((ROOT / 'config/paths.json').read_text(encoding='utf8')).get('wasi_sdk')
    if configured and (Path(configured) / 'bin/clang++.exe').is_file():
        return Path(configured)
    base = Path(os.environ['LOCALAPPDATA']) / 'cambc'
    for d in sorted(base.glob('wasi-sdk-*'), reverse=True):
        if (d / 'bin/clang++.exe').is_file():
            return d
    raise SystemExit('wasi-sdk not found under ' + str(base))


def main():
    sdk = wasi_sdk()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    cmd = [str(sdk / 'bin/clang++.exe'), '--target=wasm32-wasip1', f'--sysroot={sdk / "share/wasi-sysroot"}',
           '-std=c++20', '-O3', '-DNDEBUG', '-msimd128', '-mbulk-memory', '-fno-exceptions', '-mexec-model=reactor',
           '-Wall', '-Wextra', '-Werror', '-o', str(OUT),
           str(ROOT / 'tools/mimic/kernel.cpp'), str(ROOT / 'bots/mimic/src/core.cpp')]
    p = subprocess.run(cmd, capture_output=True, text=True)
    sys.stdout.write(p.stdout + p.stderr)
    if p.returncode:
        raise SystemExit(p.returncode)
    print('kernel', OUT, OUT.stat().st_size, 'bytes')


if __name__ == '__main__':
    main()
