"""Per-game metrics from cambc match summaries (JSON).

Usage: python analyse.py OUT.jsonl SUMMARY.json[...] [--us NAME_OR_SIDE_MAP.json]
Each summary row: map, our side, win, rounds, fuel-outs, deaths, kills, camp clears, gem losses,
earned gold at R100/R300/R600, gems submitted, draft; for both teams.
When a file name ends with _<bot>A.json (local panel), team A is <bot>; otherwise a sidecar
mapping {summary_path: "teamA"|"teamB"} names our side.
"""
import json, sys, collections


def at(runs, r):
    t, v = 0, 0.0
    for run in runs:
        if t > r:
            break
        v = float(run['value'])
        t += run['duration']
    return v


def team_metrics(d, team):
    champs = {c['id']: c for c in d['roster']['champions'] if c['team'] == team}
    ev = collections.Counter()
    for e in d['events']:
        o = e.get('owner') or {}
        if o.get('team') == team:
            ev[e['kind']] += len(e['entries'])
    gold = collections.defaultdict(float)
    for tl in d['championTimelines']:
        o = tl['owner']
        if o.get('team') != team or tl['metric'] != 'earnedGold':
            continue
        for r in (100, 300, 600):
            gold[r] += at(tl['runs'], r)
    sub = [t for t in d['teamTimelines'] if t['owner'] == team and t['metric'] == 'submittedGems']
    return {
        'fuel_out': ev['fuelExhausted'], 'deaths': ev['death'], 'kills': ev['kill'], 'camps': ev['campClear'],
        'gem_loss': ev['gemLoss'], 'faults': d['diagnostics']['botFaults'].get(team, 0),
        'gold100': gold[100], 'gold300': gold[300], 'gold600': gold[600],
        'gems': int(next((t['submittedGems'] for t in d['teams'] if t['team'] == team), 0)),
        'draft': [c['champion'] for c in d['roster']['draft'] if c['team'] == team] if d['roster'].get('draft') else [],
    }


def row(path, us):
    d = json.load(open(path, encoding='utf8'))
    them = 'teamB' if us == 'teamA' else 'teamA'
    return {'file': path, 'us': us, 'win': d['match']['outcome'] == us, 'rounds': d['match']['roundsCompleted'],
            'me': team_metrics(d, us), 'op': team_metrics(d, them)}


if __name__ == '__main__':
    out = sys.argv[1]
    args = sys.argv[2:]
    side = {}
    if '--us' in args:
        i = args.index('--us')
        side = json.load(open(args[i + 1], encoding='utf8'))
        args = args[:i] + args[i + 2:]
    with open(out, 'w', encoding='utf8') as f:
        for p in args:
            us = side.get(p)
            if us is None:
                us = 'teamA'  # caller passes the files where we are team A, or a sidecar
            f.write(json.dumps(row(p, us)) + '\n')
