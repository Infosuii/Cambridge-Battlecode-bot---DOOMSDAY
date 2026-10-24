"""Copy a bounded, deterministic sample of replays and their official summaries out of the platform ZIPs (read-only).

Members are chosen in SHA-256(match_id) order per part. Files get short names `p<part>_<kind>_<match8>` because the
original member names can exceed the Windows path limit. `cambc summary` converts each paired .camstat to
`<name>.summary.json` so tools/replay/decode_replays.mjs can check every decoded replay against the official record.
"""
import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEMBER = re.compile(r'^(?:.*/)?(?P<kind>[a-z]+)_(?P<match>[0-9a-f-]{36})_')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--replays', type=Path, required=True, help='folder with replays-<date>-part<N>.zip')
    p.add_argument('--summaries', type=Path, required=True, help='folder with summaries-<date>-part<N>.zip')
    p.add_argument('--parts', type=int, nargs='+', required=True)
    p.add_argument('--per-part', type=int, default=10)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    out = a.out.resolve()
    if not out.is_relative_to(ROOT / 'artifacts'):
        raise SystemExit('output must be inside artifacts/')
    if out.exists():
        raise SystemExit('fresh output directory required')
    out.mkdir(parents=True)
    cli = json.loads((ROOT / 'config/paths.json').read_text())['cli']
    index = {}
    for part in a.parts:
        rz = zipfile.ZipFile(next(a.replays.glob(f'replays-*-part{part}.zip')))
        sz = zipfile.ZipFile(next(a.summaries.glob(f'summaries-*-part{part}.zip')))
        summaries = set(sz.namelist())
        names = sorted(rz.namelist(), key=lambda n: hashlib.sha256(MEMBER.match(n)['match'].encode()).digest())[:a.per_part]
        for name in names:
            m = MEMBER.match(name)
            stem = f'p{part}_{m["kind"]}_{m["match"][:8]}'
            (out / f'{stem}.repl26a').write_bytes(rz.read(name))
            camstat = Path(name).stem + '.camstat'
            index[stem] = dict(part=part, member=name, match_id=m['match'], summary=camstat in summaries)
            if camstat in summaries:
                (out / f'{stem}.camstat').write_bytes(sz.read(camstat))
                subprocess.run([cli, 'summary', f'{stem}.camstat', '-o', f'{stem}.summary.json'], cwd=out, check=True,
                               capture_output=True)
    (out / 'index.json').write_text(json.dumps(index, indent=1) + '\n')
    print(json.dumps(dict(out=str(out), replays=len(index), with_summary=sum(v['summary'] for v in index.values()))))


if __name__ == '__main__':
    main()
