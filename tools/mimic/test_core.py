"""Run the core regression tests with the bot's actual wasm SIMD compiler and Node's WASI host."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_kernel import wasi_sdk


def main():
    sdk = wasi_sdk()
    out = ROOT / 'artifacts/tmp/mimic/core-test.wasm'
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(sdk / 'bin/clang++.exe'), f'--sysroot={sdk / "share/wasi-sysroot"}',
                    '-std=c++20', '-O3', '-msimd128', '-Wall', '-Wextra', '-Werror',
                    str(ROOT / 'tools/mimic/core_test.cpp'), str(ROOT / 'bots/mimic/src/core.cpp'), '-o', str(out)],
                   check=True)
    script = ('const fs=require("fs");const {WASI}=require("wasi");const w=new WASI({version:"preview1"});'
              f'WebAssembly.instantiate(fs.readFileSync({json.dumps(str(out))}),'
              '{wasi_snapshot_preview1:w.wasiImport}).then(({instance})=>w.start(instance));')
    subprocess.run(['node', '--no-warnings', '-e', script], check=True)


if __name__ == '__main__':
    main()
