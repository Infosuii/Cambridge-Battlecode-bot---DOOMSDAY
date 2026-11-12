"""Read the actual live-map groups in one round per layout, without gameplay conclusions."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import zipfile


def read_groups(stdout):
    headers, groups = [], []
    for ln in stdout.replace(chr(0), '').splitlines():
        if ln.startswith('GXMAP '):
            headers.append([int(x) for x in ln.split()[1:]])
        if ln.startswith('GXGROUP '):
            _, gid, gems, gold, count, *members = ln.split()
            tiles = [[int(v) for v in pos.split(',')] for pos in members]
            if len(tiles) != int(count):
                raise ValueError('Truncated group')
            groups.append(dict(id=int(gid), gems=int(gems), gold=int(gold), tiles=tiles))
    if len(headers) != 1 or len(groups) != headers[0][2]:
        raise ValueError('Missing or repeated runtime map report')
    return dict(width=headers[0][0], height=headers[0][1], groups=groups)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('wasm', type=Path)
    cli.add_argument('maps', type=Path)
    cli.add_argument('scratch', type=Path)
    cli.add_argument('--workers', type=int, default=8)
    args = cli.parse_args()
    args.scratch.mkdir(parents=True, exist_ok=False)
    cli_path = os.getenv('DZ_CAMBC', 'cambc')

    def one(p):
        out = args.scratch / p.stem
        out.mkdir()
        log = subprocess.run([cli_path, 'run', str(args.wasm), str(args.wasm), '--map', str(p),
            '--rounds', '1', '--out-dir', str(out), '--statistics', str(out / 'summary.json'), '--json', '--release'],
            capture_output=True, text=True, timeout=60)
        if log.returncode:
            raise RuntimeError(p.name + '\n' + log.stdout + log.stderr)
        with zipfile.ZipFile(next(out.glob('*.repl26a'))) as replay:
            a, b = (read_groups(replay.read(f'team-{s}.stdout').decode()) for s in 'ab')
        if a != b:
            raise ValueError(f'{p.name}: sides disagree on public map groups')
        statistics = out / 'summary.json'
        if statistics.exists():
            summary = json.loads(statistics.read_text())
            if any(summary['diagnostics']['botFaults'].values()):
                raise ValueError(f'{p.name}: probe fault')
        a['map_sha256'] = sha256(p.read_bytes()).hexdigest()
        return p.stem, a

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        data = dict(pool.map(one, sorted(args.maps.glob('*.map26a'))))
    print(json.dumps(data, separators=(',', ':')))


if __name__ == '__main__':
    main()
