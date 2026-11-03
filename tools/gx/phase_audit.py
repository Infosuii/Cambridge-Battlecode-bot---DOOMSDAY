"""Describe opening pace and deposit conversion across comparable match phases."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from statistics import median

PHASES = ((1, 75), (76, 150), (151, 350), (351, 700), (701, 9999))


def match(path):
    d = json.loads(path.read_text())
    me = 'team' + path.parent.name[-1]
    opp = 'team' + ('A' if me == 'teamB' else 'B')
    banks = {t['team']: int(t['submittedGems']) for t in d['teams']}
    phases = [defaultdict(Counter) for _ in PHASES]
    first = defaultdict(dict)
    for event in d['events']:
        t, k = event['owner'].get('team'), event['kind']
        if t not in banks or k not in ('gemCollection', 'gemSubmission', 'gemLoss', 'death', 'kill', 'itemCombination', 'campClear'):
            continue
        for e in event['entries']:
            r = e['timestamp']['round']
            if r <= 0:
                continue
            stat = phases[next(i for i, (lo, hi) in enumerate(PHASES) if lo <= r <= hi)][t]
            if k == 'gemCollection' and e.get('context') == 'campGroup':
                stat['camp_gems'] += int(e['value'])
                stat['camp_captures'] += 1
            elif k == 'gemCollection':
                stat['other_gems'] += int(e['value'])
            elif k == 'gemSubmission':
                stat['banked'] += int(e['value'])
            elif k == 'gemLoss':
                stat['handed'] += int(e['value']) if isinstance(e.get('target'), dict) and e['target'].get('kind') == 'champion' else 0
            elif k == 'death':
                stat['enemy_deaths' if e.get('context') == 'champion' else 'other_deaths'] += 1
            elif k == 'campClear':
                stat['clears'] += 1
            elif k == 'itemCombination':
                stat['emblems'] += 1
            if k in ('gemSubmission', 'itemCombination'):
                first[t][k] = min(r, first[t].get(k, r))
    return dict(won=d['match']['outcome'] == me, banked=banks[me], opp_banked=banks[opp],
        equal_banked=banks[me] == banks[opp], rounds=d['match']['roundsStarted'],
        phases=[(p[me],p[opp]) for p in phases], first=[first[me],first[opp]])


def aggregate(games):
    result = {'games': len(games)}
    if not games:
        return result
    result['equal_banked'] = sum(x['equal_banked'] for x in games)
    result['first'] = []
    for kind in ('gemSubmission', 'itemCombination'):
        row = []
        for team in (0,1):
            values = [r['first'][team][kind] for r in games if kind in r['first'][team]]
            row.append(dict(median=median(values) if values else None, observed=len(values)))
        result['first'].append(dict(kind=kind, us=row[0], opponent=row[1]))
    result['phases'] = []
    for i, (lo,hi) in enumerate(PHASES):
        eligible = [r for r in games if r['rounds'] >= lo]
        totals = (Counter(), Counter())
        for r in eligible:
            for c, p in zip(totals,r['phases'][i]):
                c.update(p)
        result['phases'].append(dict(lo=lo, hi=hi, games=len(eligible),
            us=dict(totals[0]), opponent=dict(totals[1])))
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('scratch',type=Path)
    p.add_argument('tag')
    a=p.parse_args()
    data = {}
    for run in sorted(a.scratch.glob(f'gx-{a.tag}-pool-*')):
        paths = sorted(run.glob('games/*/summary.json'))
        if len(paths) != 172:
            raise ValueError(f'{run.name}: expected 172 summaries, found {len(paths)}')
        matches = [match(path) for path in paths]
        data[run.name] = {name:aggregate(games) for name,games in (
            ('all',matches), ('win',[r for r in matches if r['won']]), ('nonwin',[r for r in matches if not r['won']]))}
    if not data:
        raise ValueError(f'No pool found for {a.tag}')
    print(json.dumps(data,indent=2))


if __name__ == '__main__':
    main()
