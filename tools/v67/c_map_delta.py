"""Per-map paired margin differences (candidate - baseline) pooled over several run pairs, e.g. one pair per opponent.

Usage: c_map_delta.py CAND:BASE [CAND:BASE ...] [--maps m1 m2 ...]
Prints, per map, the mean difference for each pair and the mean over pairs, sorted from worst.
"""
import argparse
import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def per_game(run):
    out = {}
    for g in json.loads((ROOT / 'artifacts/evaluations/v67' / run / 'games.json').read_text())['games']:
        out.setdefault((g['map'], g['side'], g['seed']), g['margin'])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pairs', nargs='+')
    ap.add_argument('--maps', nargs='*')
    a = ap.parse_args()
    table = collections.defaultdict(dict)
    for pair in a.pairs:
        cand, base = pair.split(':')
        c, b = per_game(cand), per_game(base)
        acc = collections.defaultdict(list)
        for k in set(c) & set(b):
            acc[k[0]].append(c[k] - b[k])
        for m, v in acc.items():
            table[m][pair] = sum(v) / len(v)
    rows = sorted(table.items(), key=lambda kv: sum(kv[1].values()) / len(kv[1]))
    for m, d in rows:
        if a.maps and m not in a.maps:
            continue
        mean = sum(d.values()) / len(d)
        print(f'{m:24s} mean {mean:+7.0f}   ' + '  '.join(f'{v:+6.0f}' for v in d.values()))


if __name__ == '__main__':
    main()
