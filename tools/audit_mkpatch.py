"""Agent A patch helpers: make git-applicable unified diffs of lead-owned files and materialise scratch copies.

    python tools/audit_mkpatch.py diff  --base bot/src --mod artifacts/tmp/A/x/bot/src --out archive/agents/A/patches/NN.diff [--files a b]
    python tools/audit_mkpatch.py check --patch archive/agents/A/patches/NN.diff                 # git apply --check from ROOT
    python tools/audit_mkpatch.py scratch --dest artifacts/tmp/A/x [--patch p1 --patch p2 ...]

`scratch` builds <dest>/bot/src from the frozen base (git HEAD bot/src + archive/agents/A/base_stubs + nn_teacher.*; --live: the live bot/src) and applies the patches there with
`git apply -p1 --directory=<dest rel>` (only files under <dest> are written; bot/src is never touched).
"""
from __future__ import annotations

import argparse
import difflib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(p: Path) -> list[str]:
    return p.read_text(encoding='utf-8').splitlines(keepends=True) if p.exists() else []


def make_diff(base: Path, mod: Path, files: list[str] | None, prefix: str = 'bot/src') -> str:
    base, mod = Path(base), Path(mod)
    names = files or sorted({p.name for p in base.iterdir() if p.is_file()} | {p.name for p in mod.iterdir() if p.is_file()})
    out = []
    for name in names:
        a, b = _read(base / name), _read(mod / name)
        if a == b:
            continue
        for lines in (a, b):
            if lines and not lines[-1].endswith('\n'):
                lines[-1] += '\n'  # every file here ends with a newline; keep the diff simple
        rel = f'{prefix}/{name}'
        hdr = [f'diff --git a/{rel} b/{rel}\n']
        if not a:
            hdr.append('new file mode 100644\n')
        out.extend(hdr)
        out.extend(difflib.unified_diff(a, b, fromfile='/dev/null' if not a else f'a/{rel}', tofile=f'b/{rel}', n=3))
    return ''.join(out)


def git(*args, cwd=ROOT) -> subprocess.CompletedProcess:
    return subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True)


def check(patch: Path) -> tuple[bool, str]:
    r = git('apply', '--check', '-v', str(Path(patch).resolve()))
    return r.returncode == 0, (r.stdout + r.stderr).strip()


A_OWNED = ('nn_teacher.h', 'nn_teacher.cpp')


def frozen_base(src: Path) -> None:
    """Lead-committed bot/src (git HEAD, read-only `git show`) + the lead stubs nn_config.h / nn_budget.h saved in
    archive/agents/A/base_stubs + Agent A's nn_teacher.*: a base that other agents' in-progress files in bot/src cannot change."""
    src.mkdir(parents=True)
    names = git('ls-files', 'bot/src').stdout.split()
    for n in names:
        data = subprocess.run(['git', 'show', f'HEAD:{n}'], cwd=ROOT, capture_output=True).stdout
        (src / Path(n).name).write_bytes(data)
    for stub in (ROOT / 'archive/agents/A/base_stubs').iterdir():
        shutil.copyfile(stub, src / stub.name)
    for n in A_OWNED:
        shutil.copyfile(ROOT / 'bot/src' / n, src / n)


def scratch(dest: Path, patches: list[Path], frozen: bool = True) -> Path:
    dest = Path(dest).resolve()
    src = dest / 'bot' / 'src'
    if src.exists():
        shutil.rmtree(src)
    if frozen:
        frozen_base(src)
    else:
        shutil.copytree(ROOT / 'bot' / 'src', src, ignore=shutil.ignore_patterns('.cambc'))
    rel = dest.relative_to(ROOT).as_posix()
    for p in patches:
        r = git('apply', '-p1', f'--directory={rel}', str(Path(p).resolve()))
        if r.returncode:
            raise RuntimeError(f'git apply failed for {p}: {r.stdout}{r.stderr}')
    return dest / 'bot'


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    d = sub.add_parser('diff')
    d.add_argument('--base', default='bot/src')
    d.add_argument('--mod', required=True)
    d.add_argument('--out', required=True)
    d.add_argument('--files', nargs='*')
    c = sub.add_parser('check')
    c.add_argument('--patch', required=True)
    s = sub.add_parser('scratch')
    s.add_argument('--dest', required=True)
    s.add_argument('--patch', action='append', default=[])
    s.add_argument('--live', action='store_true', help='copy the live bot/src instead of the frozen base')
    a = ap.parse_args(argv)
    if a.cmd == 'diff':
        text = make_diff(ROOT / a.base, ROOT / a.mod, a.files)
        Path(ROOT / a.out).parent.mkdir(parents=True, exist_ok=True)
        (ROOT / a.out).write_text(text, encoding='utf-8', newline='\n')
        print(f'wrote {a.out}: {text.count(chr(10))} lines')
        ok, msg = check(ROOT / a.out)
        print('git apply --check:', 'OK' if ok else 'FAILED', '\n' + msg)
        return 0 if ok else 1
    if a.cmd == 'check':
        ok, msg = check(ROOT / a.patch)
        print('OK' if ok else 'FAILED', '\n' + msg)
        return 0 if ok else 1
    if a.cmd == 'scratch':
        print(scratch(ROOT / a.dest, [ROOT / p for p in a.patch], frozen=not a.live))
        return 0
    return 2


if __name__ == '__main__':
    sys.exit(main())
