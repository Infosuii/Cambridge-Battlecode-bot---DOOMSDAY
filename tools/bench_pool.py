"""Index disjoint completed bench3 runs for bench_compare; creates no new games or replay copies.

Usage: python tools/bench_pool.py <output prefix> <input prefix> <input prefix> --provenance <out.json>
"""
import argparse
import glob
import hashlib
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output')
    ap.add_argument('inputs', nargs='+')
    ap.add_argument('--provenance', required=True)
    a = ap.parse_args()
    if glob.glob(a.output + '-seed*-s*'):
        raise SystemExit('output index already exists')
    keys, files, sources, destinations = set(), [], [], set()
    for prefix in a.inputs:
        count = 0
        summaries = sorted(glob.glob(prefix + '-seed*-s*/summary.json'))
        if not summaries:
            raise SystemExit('no summaries for ' + prefix)
        for f in summaries:
            raw = Path(f).read_bytes()
            d = json.loads(raw)
            suffix = Path(f).parent.name[len(Path(prefix).name):]
            seed = suffix.split('-seed')[-1].split('-')[0]
            if d['games'] != len(d['per_game']):
                raise SystemExit('shard count mismatch')
            for g in d['per_game']:
                key = (g['map'], g['side'], seed)
                if key in keys:
                    raise SystemExit('overlapping games: ' + repr(key))
                keys.add(key)
                count += 1
            dest = Path(a.output + suffix) / 'summary.json'
            if dest in destinations:
                raise SystemExit('inputs must use disjoint seed/shard suffixes')
            destinations.add(dest)
            files.append((dest, raw))
        sources.append(dict(prefix=prefix, games=count, summaries=len(summaries),
                            summary_hashes={Path(f).parent.name: hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in summaries}))
    for dest, raw in files:
        dest.parent.mkdir(parents=True, exist_ok=False)
        dest.write_bytes(raw)
    provenance = dict(output=a.output, games=len(keys), new_games=0,
                      note='Analysis index only; game folders reference the original completed runs. No replay copies.', sources=sources)
    Path(a.provenance).write_text(json.dumps(provenance, indent=1) + '\n', encoding='utf8')
    print(f'{len(keys)} original games indexed; zero new games')


if __name__ == '__main__':
    main()
