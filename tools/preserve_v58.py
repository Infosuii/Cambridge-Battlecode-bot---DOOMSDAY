"""Preserve an immutable v58 prototype as a v57-relative patch and source hashes (no replays/builds).

Usage: python tools/preserve_v58.py d1 artifacts/tmp/v58-d1 --state rejected --reason "mechanism targets missed"
"""
import argparse
import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('label')
    ap.add_argument('snapshot')
    ap.add_argument('--state', choices=('rejected', 'unretained', 'accepted', 'invalid'), required=True)
    ap.add_argument('--reason', required=True)
    a = ap.parse_args()
    assert all(c in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in a.label)
    src = (ROOT / a.snapshot / 'src').resolve()
    assert src.is_relative_to(ROOT)
    base = ROOT / 'bots/v57/src'
    names = sorted({p.name for p in src.iterdir() if p.is_file()} | {p.name for p in base.iterdir() if p.is_file()})
    files, endings, diff = {}, {}, []
    tree = hashlib.sha256()
    for name in names:
        p, before = src / name, base / name
        if p.exists():
            raw = p.read_bytes()
            tree.update(name.encode() + b'\0' + raw)
            files[name] = hashlib.sha256(raw).hexdigest()
            endings[name] = 'CRLF' if b'\r\n' in raw else 'LF'
        old = before.read_text(encoding='utf8').splitlines(keepends=True) if before.exists() else []
        new = p.read_text(encoding='utf8').splitlines(keepends=True) if p.exists() else []
        diff.extend(difflib.unified_diff(old, new, fromfile='a/src/' + name if before.exists() else '/dev/null', tofile='b/src/' + name if p.exists() else '/dev/null'))
    target = ROOT / 'research/v58/V58_EXPERIMENTS.json'
    manifest = json.loads(target.read_text(encoding='utf8')) if target.exists() else {}
    if a.label in manifest:
        assert manifest[a.label]['source_sha256'] == tree.hexdigest(), 'recorded source changed'
    directory = 'rejected' if a.state in ('rejected', 'invalid') else 'experiments'
    patch = f'research/v58/{directory}/v58-{a.label}.diff'
    (ROOT / patch).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / patch).write_bytes(''.join(diff).encode('utf8'))
    manifest[a.label] = dict(base='bots/v57', source_sha256=tree.hexdigest(), files=files, line_endings=endings,
                            patch=patch, state=a.state, reason=a.reason, evaluation_prefix='artifacts/evaluations/v58-' + a.label)
    target.write_text(json.dumps(manifest, indent=1) + '\n', encoding='utf8')
    print(a.label, a.state, tree.hexdigest())


if __name__ == '__main__':
    main()
