"""Per-game resource curves from local summary.json files (strategic audit 2026-10-28).

Usage: curves.py RUN [RUN...] --out data/NAME.json
For each game of each run: our team's collected gems, earned gold and submitted gems at R50/100/250/500/750,
plus the round our team first reached 1000 submitted gems (None if never), and final outcome.
Champion timelines are step functions of (duration, value) runs starting at round 0.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MARKS = (50, 100, 250, 500, 750)


def at(runs, r):
    t = 0
    v = 0
    for run in runs:
        if t > r:
            break
        v = float(run['value'])
        t += run['duration']
    return v


def first_reach(runs, x):
    t = 0
    for run in runs:
        if float(run['value']) >= x:
            return t
        t += run['duration']
    return None


def game_row(g):
    s = json.loads((ROOT / g['folder'] / 'summary.json').read_text())
    team = 'team' + g['side'].upper()
    other = 'teamB' if team == 'teamA' else 'teamA'
    out = dict(map=g['map'], side=g['side'], seed=g['seed'], win=g['win'], margin=g['margin'],
               rounds=s['match']['roundsCompleted'], fuel_outs=g['fuel'])
    for who, tm in (('us', team), ('them', other)):
        per = {}
        for tl in s['championTimelines']:
            if tl['owner'].get('team') != tm:
                continue
            per.setdefault(tl['metric'], []).append(tl['runs'])
        sub = [t for t in s['teamTimelines'] if t['metric'] == 'submittedGems' and t['owner'] == tm][0]['runs']
        row = {}
        for m in MARKS:
            row[m] = dict(collected=sum(at(r, m) for r in per.get('collectedGems', [])),
                          gold=sum(at(r, m) for r in per.get('earnedGold', [])),
                          spent=sum(at(r, m) for r in per.get('spentGold', [])),
                          deaths=sum(at(r, m) for r in per.get('deaths', [])),
                          submitted=at(sub, m))
        row['reach1000'] = first_reach(sub, 1000)
        row['champions'] = len(per.get('collectedGems', []))
        out[who] = row
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('runs', nargs='+')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    rows = []
    for run in a.runs:
        games = json.loads((ROOT / 'artifacts/evaluations/v67' / run / 'games.json').read_text())['games']
        for g in games:
            r = game_row(g)
            r['run'] = run
            rows.append(r)
    Path(a.out).write_text(json.dumps(rows, indent=0))
    print(len(rows), 'games ->', a.out)


if __name__ == '__main__':
    main()
