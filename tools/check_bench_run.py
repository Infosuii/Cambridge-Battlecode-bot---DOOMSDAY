"""Check exact game coverage and BOTH teams' native faults; bench3 exit status must also be zero.

Usage: python tools/check_bench_run.py <prefix> [--seeds 1,2,...] [--maps a,b,...] [--holdout] [--json out.json]
"""
import argparse
import glob
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('prefix')
    ap.add_argument('--seeds', default=','.join(map(str, range(1, 13))))
    ap.add_argument('--maps')
    ap.add_argument('--holdout', action='store_true')
    ap.add_argument('--json')
    a = ap.parse_args()
    partitions = json.loads((ROOT / 'evaluation/schedules/map_partitions.json').read_text())['partitions']
    maps = a.maps.split(',') if a.maps else (partitions['final'] if a.holdout else partitions['training'] + partitions['selection'])
    expected = {(m, side, s) for m in maps for side in ('A', 'B') for s in a.seeds.split(',')}
    actual, duplicates = set(), []
    faults = {'candidate': 0, 'opponent': 0}
    fuel = {'candidate': 0, 'opponent': 0}
    games = wins = 0
    margin = 0
    for f in glob.glob(a.prefix + '-seed*-s*/summary.json'):
        seed = Path(f).parent.name.split('-seed')[-1].split('-')[0]
        data = json.loads(Path(f).read_text(encoding='utf8'))
        if data['games'] != len(data['per_game']):
            raise SystemExit('shard count differs from its game list')
        for g in data['per_game']:
            key = (g['map'], g['side'], seed)
            if key in actual:
                duplicates.append(key)
            actual.add(key)
            native = json.loads((Path(g['folder']) / 'summary.json').read_text(encoding='utf8'))
            us, them = 'team' + g['side'], 'team' + ('B' if g['side'] == 'A' else 'A')
            for label, team in (('candidate', us), ('opponent', them)):
                faults[label] += int(native['diagnostics']['botFaults'][team])
                fuel[label] += sum(len(e['entries']) for e in native['events'] if e['kind'] == 'fuelExhausted' and isinstance(e['owner'], dict) and e['owner'].get('team') == team)
            games += 1
            wins += g['win']
            margin += g['gems'] - g['opponent_gems']
    report = dict(games=games, expected_games=len(expected), wins=wins,
                  win_rate=wins / games if games else None, mean_margin=margin / games if games else None,
                  faults=faults, fuel=fuel, missing=sorted(expected - actual), unexpected=sorted(actual - expected), duplicates=duplicates)
    report['passed'] = actual == expected and not duplicates and sum(faults.values()) == 0
    if a.json:
        Path(a.json).write_text(json.dumps(report, indent=1) + '\n', encoding='utf8')
    print(json.dumps(report))
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
