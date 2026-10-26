"""Record a restart snapshot as a patch and content hashes; no replays or builds are copied.

Usage: python tools/preserve_v55_experiment.py r9-heart-only artifacts/tmp/v55-r9-heart-only
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
    args = ap.parse_args()
    if not args.label.startswith('r') or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.label):
        raise SystemExit('expected a restart experiment label')
    src = (ROOT / args.snapshot / 'src').resolve()
    if not src.is_relative_to(ROOT):
        raise SystemExit('snapshot must be inside the repository')
    base = ROOT / 'bots/v54/src'
    h = hashlib.sha256()
    files, endings, patch = {}, {}, []
    names = sorted(p.relative_to(src).as_posix() for p in src.rglob('*') if p.is_file())
    if names != sorted(p.relative_to(base).as_posix() for p in base.rglob('*') if p.is_file()):
        raise SystemExit('unexpected source member set')
    for name in names:
        data = (src / name).read_bytes()
        h.update(name.encode() + b'\0' + data + b'\0')
        files[name] = hashlib.sha256(data).hexdigest()
        endings[name] = 'CRLF' if b'\r\n' in data else 'LF'
        before = (base / name).read_text(encoding='utf8').splitlines(keepends=True)
        after = data.decode('utf8').replace('\r\n', '\n').splitlines(keepends=True)
        patch.extend(difflib.unified_diff(before, after, fromfile='a/src/' + name, tofile='b/src/' + name))
    target = ROOT / 'research/v55/V55_RESTART_EXPERIMENTS.json'
    manifest = json.loads(target.read_text(encoding='utf8'))
    if args.label in manifest and manifest[args.label]['tree_sha256'] != h.hexdigest():
        raise SystemExit('refusing to replace a different recorded snapshot')
    patch_path = f'research/v55/experiments/v55-{args.label}.patch'
    (ROOT / patch_path).write_bytes(''.join(patch).encode('utf8'))
    manifest[args.label] = dict(tree_sha256=h.hexdigest(), files=files, line_endings=endings,
                                patch=patch_path, base='bots/v54', seeds=list(range(1, 13)))
    target.write_text(json.dumps(manifest, indent=1) + '\n', encoding='utf8')
    print(args.label, h.hexdigest())


if __name__ == '__main__':
    main()
