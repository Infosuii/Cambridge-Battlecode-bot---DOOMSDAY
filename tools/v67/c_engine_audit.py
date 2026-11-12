"""Compare engine identity fields of local benchmark summaries with downloaded platform summaries.

Usage: c_engine_audit.py --local artifacts/evaluations/v67/<run> --platform <dir with platform summary json files>
Prints the distinct engineVersion / engineBuildHash / metricSemanticsVersion values on each side, whether local
duplicate jobs (same map, side, seed, wasm) share an engine seed, and fuel-exhaustion rates per team-game.
"""
import argparse
import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def ident(d):
    m = d['match']
    return (m.get('engineVersion'), m.get('engineBuildHash'), m.get('metricSemanticsVersion'))


def fuel_outs(d):
    return sum(len(e['entries']) for e in d['events'] if e['kind'] == 'fuelExhausted')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--local', required=True)
    ap.add_argument('--platform', required=True)
    ap.add_argument('--limit', type=int, default=300)
    a = ap.parse_args()
    local = ROOT / a.local
    games = json.loads((local / 'games.json').read_text())['games']
    ids, seeds, fo = collections.Counter(), collections.defaultdict(set), []
    for g in games:
        d = json.loads((ROOT / g['folder'] / 'summary.json').read_text())
        ids[ident(d)] += 1
        seeds[(g['map'], g['side'], g['seed'])].add(d['match'].get('seed'))
        fo.append(fuel_outs(d))
    print('local identities:', dict(ids))
    dup = [k for k, v in seeds.items() if len(v) > 1]
    multi = sum(1 for g in games if sum(1 for x in games if (x['map'], x['side'], x['seed']) == (g['map'], g['side'], g['seed'])) > 1)
    print(f'local duplicate jobs: {multi} games in repeated cells; cells with differing engine seeds: {len(dup)}')
    print('example local engine seeds:', [next(iter(v)) for v in list(seeds.values())[:3]])
    print(f'local fuel-outs per game (both teams): {sum(fo) / len(fo):.2f}')
    pids, pfo, pseeds = collections.Counter(), [], []
    for p in sorted(Path(a.platform).rglob('*.json'))[:a.limit]:
        try:
            d = json.loads(p.read_text(encoding='utf-8-sig'))
        except Exception:
            continue
        if 'match' not in d or 'teams' not in d:
            continue
        pids[ident(d)] += 1
        pfo.append(fuel_outs(d))
        pseeds.append(d['match'].get('seed'))
    print('platform identities:', dict(pids))
    if pfo:
        print(f'platform fuel-outs per game (both teams): {sum(pfo) / len(pfo):.2f} over {len(pfo)} games')
    print('example platform seeds:', pseeds[:3])
    keys = set()
    for p in sorted(Path(a.platform).rglob('*.json'))[:1]:
        d = json.loads(p.read_text(encoding='utf-8-sig'))
        keys = set(d.get('match', {}).keys())
    print('platform match keys:', sorted(keys))


if __name__ == '__main__':
    main()
