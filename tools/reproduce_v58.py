"""Reconstruct a hash-exact v58 experiment from frozen v57 and its preserved patch.

Usage: python tools/reproduce_v58.py d6 artifacts/tmp/reproduced-v58-d6
The destination must be new and inside this repository; neither frozen bot is modified.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('experiment')
    ap.add_argument('destination')
    a = ap.parse_args()
    entry = json.loads((ROOT / 'artifacts/claude_ops/V58_EXPERIMENTS.json').read_text(encoding='utf8'))[a.experiment]
    dest = (ROOT / a.destination).resolve()
    if not dest.is_relative_to(ROOT) or dest.exists():
        raise SystemExit('destination must be a new directory inside this repository')
    shutil.copytree(ROOT / entry['base'] / 'src', dest / 'src')
    for p in (dest / 'src').iterdir():
        if p.is_file():
            p.write_bytes(p.read_bytes().replace(b'\r\n', b'\n'))
    subprocess.run(['git', 'apply', '--whitespace=nowarn', '--directory=' + dest.relative_to(ROOT).as_posix(),
                    str(ROOT / entry['patch'])], cwd=ROOT, check=True)
    tree = hashlib.sha256()
    actual_files = {}
    for p in sorted((dest / 'src').iterdir()):
        if not p.is_file():
            continue
        raw = p.read_bytes().replace(b'\r\n', b'\n')
        if entry['line_endings'][p.name] == 'CRLF':
            raw = raw.replace(b'\n', b'\r\n')
        p.write_bytes(raw)
        actual_files[p.name] = hashlib.sha256(raw).hexdigest()
        tree.update(p.name.encode() + b'\0' + raw)
    if actual_files != entry['files'] or tree.hexdigest() != entry['source_sha256']:
        raise SystemExit('reconstruction hash mismatch: ' + tree.hexdigest())
    print(a.experiment, tree.hexdigest(), 'PASS')


if __name__ == '__main__':
    main()
