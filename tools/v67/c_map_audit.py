"""Check local map files against the platform: the mapHash in platform summaries (by map name from matches.json)
versus the mapHash the local engine reports for the same map, plus maps present on one side only.

Usage: c_map_audit.py --crawl artifacts/local-only/meta/20261027 --local-runs RUN [RUN ...]
"""
import argparse
import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def norm(name):
    return name.replace('_', '-').lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--crawl', required=True)
    ap.add_argument('--local-runs', nargs='+', required=True)
    a = ap.parse_args()
    crawl = ROOT / a.crawl
    names = {m['matchId']: m['map'] for m in json.loads((crawl / 'matches.json').read_text(encoding='utf-8-sig'))}
    platform = collections.defaultdict(set)
    for p in (crawl / 'summaries').glob('*.json'):
        mid = p.stem
        if mid not in names:
            continue
        d = json.loads(p.read_text(encoding='utf-8-sig'))
        platform[norm(names[mid])].add(d['match']['mapHash'])
    local = collections.defaultdict(set)
    for run in a.local_runs:
        for g in json.loads((ROOT / 'artifacts/evaluations/v67' / run / 'games.json').read_text())['games']:
            d = json.loads((ROOT / g['folder'] / 'summary.json').read_text())
            local[norm(g['map'])].add(d['match']['mapHash'])
    files = {norm(p.stem) for p in (ROOT / 'maps/local-benchmarks').glob('*.map26a')}
    both = sorted(set(platform) & set(local))
    bad = [m for m in both if platform[m] != local[m]]
    print(f'platform maps seen {len(platform)}, local maps played {len(local)}, local map files {len(files)}')
    print(f'compared {len(both)}: identical {len(both) - len(bad)}, DIFFERENT {len(bad)}')
    for m in bad:
        print('  differs:', m, 'platform', sorted(platform[m])[:2], 'local', sorted(local[m])[:2])
    print('platform maps with no local file:', sorted(set(platform) - files))
    print('local files not seen on platform crawl:', sorted(files - set(platform)))


if __name__ == '__main__':
    main()
