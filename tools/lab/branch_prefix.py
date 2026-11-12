"""First round at which two branch games diverge (all team and champion timelines compared round by round).

Usage: python tools/lab/branch_prefix.py <profile dir A> <profile dir B>
Both dirs come from tools/mapgen/profile_maps.py with the same maps and sides. Prints, per game, the first round where
any timeline value differs (or 'identical'). For a valid branch at round R every divergence must be at or after R.
"""
import json
import sys
from pathlib import Path


def expand(runs):
    out = []
    for r in runs:
        out += [r['value']] * int(r['duration'])
    return out


def series(summary):
    s = {}
    for kind in ('teamTimelines', 'championTimelines'):
        for t in summary.get(kind, []):
            o = t['owner']
            key = (kind, t['metric'], o if isinstance(o, str) else (o.get('team'), o.get('id')))
            s[key] = expand(t['runs'])
    return s


def first_diff(a, b):
    sa, sb = series(a), series(b)
    first = None
    for k in set(sa) | set(sb):
        x, y = sa.get(k, []), sb.get(k, [])
        n = min(len(x), len(y))
        d = next((i for i in range(n) if x[i] != y[i]), n if len(x) != len(y) else None)
        if d is not None and (first is None or d < first):
            first = d
    return first


def main():
    da, db = Path(sys.argv[1]) / 'games', Path(sys.argv[2]) / 'games'
    for g in sorted(p.name for p in da.iterdir()):
        a, b = da / g / 'summary.json', db / g / 'summary.json'
        if a.exists() and b.exists():
            d = first_diff(json.loads(a.read_text(encoding='utf-8')), json.loads(b.read_text(encoding='utf-8')))
            print(f'{g:28s} first difference at round {d}' if d is not None else f'{g:28s} identical')


if __name__ == '__main__':
    main()
