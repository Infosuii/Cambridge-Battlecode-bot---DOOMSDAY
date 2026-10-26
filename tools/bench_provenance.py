"""Prevent comparing benchmarks from different engines/SDKs as candidate changes."""
import glob
import json
from pathlib import Path


def environment(prefix):
    path = Path(prefix + '-environment.json')
    if path.exists():
        d = json.loads(path.read_text())
        return ('fingerprinted', d['fingerprint'])
    versions = set()
    for name in glob.glob(prefix + '-seed*-s*/summary.json'):
        shard = json.loads(Path(name).read_text(encoding='utf8'))
        if shard['per_game']:
            native = Path(shard['per_game'][0]['folder']) / 'summary.json'
            versions.add(json.loads(native.read_text(encoding='utf8'))['match']['engineVersion'])
    if len(versions) != 1:
        raise SystemExit('Missing or mixed engine provenance: ' + prefix)
    return ('legacy-engine-only', versions.pop())


def require_compatible(a, b=None):
    ea = environment(a)
    if b is not None and ea != environment(b):
        raise SystemExit('Cannot compare different build environments or legacy runs with fingerprinted runs')
