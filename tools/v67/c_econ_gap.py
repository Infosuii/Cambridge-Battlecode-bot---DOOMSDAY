"""Early economy gap: our local games against top-vs-top ladder games on the same maps.

Usage: c_econ_gap.py RUN [RUN...] [--marks 100 200 300 500] [--metric earnedGold]
Top teams: native summaries in artifacts/local-only/meta/20261027 (both sides of every top-vs-top game). Ours: the
summary.json of every game in each local run (our side only). Early rounds are mostly PvE, so the opponent matters
less there than later. Prints per-map and pooled means per team at each mark, plus deaths.
"""
import argparse
import collections
import json
from pathlib import Path
import statistics as st

ROOT = Path(__file__).resolve().parents[2]
META = ROOT / 'artifacts/local-only/meta/20261027'


def at(t, r):
    cursor = 0
    for run in t['runs']:
        cursor += run['duration']
        if r < cursor:
            return float(run['value'])
    return float(t['runs'][-1]['value']) if t['runs'] else 0.0


def curve(d, team, marks, metrics):
    done = d['match']['roundsCompleted']
    out = {}
    for r in marks:
        if r > done:
            continue
        out[r] = {m: sum(at(t, r) for t in d['championTimelines']
                         if t['owner'].get('team') == team and t['metric'] == m) for m in metrics}
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument('runs', nargs='+')
    p.add_argument('--marks', nargs='+', type=int, default=[100, 200, 300, 500])
    p.add_argument('--metrics', nargs='+', default=['earnedGold', 'collectedGems', 'deaths'])
    p.add_argument('--maps', action='store_true', help='print per-map rows')
    a = p.parse_args()
    names = {m['matchId']: m['map'] for m in json.loads((META / 'matches.json').read_text())}
    top = collections.defaultdict(lambda: collections.defaultdict(list))  # map -> (mark, metric) -> values
    for f in (META / 'summaries').glob('*.json'):
        mp = names.get(f.stem)
        if not mp:
            continue
        d = json.loads(f.read_text())
        for team in ('teamA', 'teamB'):
            for r, v in curve(d, team, a.marks, a.metrics).items():
                for m, x in v.items():
                    top[mp][(r, m)].append(x)
    ours = collections.defaultdict(lambda: collections.defaultdict(list))
    for run in a.runs:
        games = json.loads((ROOT / 'artifacts/evaluations/v67' / run / 'games.json').read_text())['games']
        seen = set()
        for g in games:
            key = (g['map'], g['side'], g['seed'])
            if key in seen:
                continue
            seen.add(key)
            d = json.loads((ROOT / g['folder'] / 'summary.json').read_text())
            team = 'teamA' if g['side'] == 'a' else 'teamB'
            mp = g['map'].replace('-', '_')
            for r, v in curve(d, team, a.marks, a.metrics).items():
                for m, x in v.items():
                    ours[mp][(r, m)].append(x)
    common = sorted(set(top) & set(ours))
    print(f'maps in common: {len(common)} (top-vs-top maps {len(top)}, ours {len(ours)})')
    header = 'map'.ljust(22) + ''.join(f'{m[:5]}@{r}'.rjust(16) for r in a.marks for m in a.metrics)
    print(header + '   (ours / top)')
    pooled = collections.defaultdict(lambda: [[], []])
    for mp in common:
        cells = []
        for r in a.marks:
            for m in a.metrics:
                o, t = ours[mp].get((r, m), []), top[mp].get((r, m), [])
                if o and t:
                    pooled[(r, m)][0].append(st.fmean(o))
                    pooled[(r, m)][1].append(st.fmean(t))
                    cells.append(f'{st.fmean(o):.0f}/{st.fmean(t):.0f}'.rjust(16))
                else:
                    cells.append('-'.rjust(16))
        if a.maps:
            print(f'{mp[:22].ljust(22)}' + ''.join(cells) + f'   n={len(top[mp][(a.marks[0], a.metrics[0])])}')
    print('pooled (map-weighted)'.ljust(22) + ''.join(
        f'{st.fmean(pooled[(r, m)][0]):.0f}/{st.fmean(pooled[(r, m)][1]):.0f}'.rjust(16) if pooled[(r, m)][0] else '-'.rjust(16)
        for r in a.marks for m in a.metrics))


if __name__ == '__main__':
    main()
