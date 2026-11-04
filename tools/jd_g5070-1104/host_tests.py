#!/usr/bin/env python3
"""Host fixtures for the jd-g5070-1104 candidate (run with `py tools/jd_g5070-1104/host_tests.py`).

Compiles every tools/jd_g5070-1104/tests/*_test.cpp with g++ -std=c++20 -O2 -Wall -Wextra -Werror against
bots/jd-g5070-1104/src (pattern of tools/dz.py host_tests) and runs it. Exit code 0 only when all pass.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SRC = REPO / 'bots' / 'jd-g5070-1104' / 'src'


def compiler():
    cxx = os.environ.get('JD_CXX') or shutil.which('g++')
    if not cxx and Path('C:/msys64/ucrt64/bin/g++.exe').exists():
        cxx = 'C:/msys64/ucrt64/bin/g++.exe'
    if not cxx:
        sys.exit('no C++20 compiler (set JD_CXX)')
    return cxx


def main():
    cxx = compiler()
    env = dict(os.environ, PATH=str(Path(cxx).parent) + os.pathsep + os.environ.get('PATH', ''))
    out = Path(tempfile.gettempdir()) / 'jd-g5070-1104-host'
    out.mkdir(parents=True, exist_ok=True)
    tests = sorted((HERE / 'tests').glob('*_test.cpp'))
    if not tests:
        sys.exit('no tests found')
    failed = []
    for t in tests:
        exe = out / (t.stem + ('.exe' if os.name == 'nt' else ''))
        c = subprocess.run([cxx, '-std=c++20', '-O2', '-Wall', '-Wextra', '-Werror', '-I', str(SRC), str(t), '-o', str(exe)],
                           capture_output=True, text=True, env=env)
        if c.returncode:
            print(f'{t.name}: COMPILE FAILED\n{c.stdout}{c.stderr}')
            failed.append(t.name)
            continue
        r = subprocess.run([str(exe)], capture_output=True, text=True, env=env)
        print(r.stdout.rstrip())
        if r.returncode:
            print(f'{t.name}: FAILED (exit {r.returncode}) {r.stderr}')
            failed.append(t.name)
    print(f'host_tests: {len(tests) - len(failed)}/{len(tests)} passed')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
