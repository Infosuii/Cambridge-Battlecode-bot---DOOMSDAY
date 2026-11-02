"""Per-game ladder table from cambc match summaries (read-only analysis).

  python tools/ladder_analyse.py MATCHES.json SUMMARY_DIR OUT.json [--us DOOMSDAY]

For each match: opponent, result, map, both teams' champions, and per team at rounds 100 / 250 / 500 / end:
collected gems, banked (submitted) gems, earned gold, kills, deaths, gems lost, plus fuel-outs per team.
"""
import argparse, json, os

CHECK = (100, 250, 500, 10 ** 6)
METRICS = ('collectedGems', 'submittedGems', 'earnedGold', 'kills', 'deaths')


def value_at(runs, r):
    t, v = 0, 0
    for run in runs:
        if t >= r:
            break
        v = float(run['value'])
        t += run['duration']
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('matches'); ap.add_argument('summaries'); ap.add_argument('out')
    ap.add_argument('--us', default='DOOMSDAY')
    a = ap.parse_args()
    rows = []
    for m in json.load(open(a.matches)):
        p = os.path.join(a.summaries, m['matchId'] + '.json')
        if not os.path.exists(p):
            continue
        s = json.load(open(p))
        me = next(t for t in m['teams'] if t['name'] == a.us)
        op = next(t for t in m['teams'] if t['name'] != a.us)
        side = {'a': 'teamA', 'b': 'teamB'}
        us, them = side[me['side']], side[op['side']]
        row = {'match': m['matchId'], 'created': m['createdAt'], 'map': m['map'], 'kind': m['kind'],
               'opp': op['name'], 'result': me['result'], 'end_reason': m.get('endReason'),
               'rounds': s['match'].get('roundsCompleted')}
        for tag, team in (('us', us), ('them', them)):
            row[tag + '_champs'] = [c['name'] for c in s['roster']['champions'] if c['team'] == team]
            for metric in METRICS:
                runs = [t['runs'] for t in s['championTimelines']
                        if t['metric'] == metric and t['owner'].get('team') == team]
                for r in CHECK:
                    key = f"{tag}_{metric}_{'end' if r > 10 ** 5 else r}"
                    row[key] = sum(value_at(x, r) for x in runs)
            row[tag + '_fuel_outs'] = sum(len(e['entries']) for e in s['events']
                                          if e['kind'] == 'fuelExhausted' and str(e.get('owner', '')).find(team) >= 0)
            row[tag + '_gem_loss'] = sum(len(e['entries']) for e in s['events']
                                         if e['kind'] == 'gemLoss' and str(e.get('owner', '')).find(team) >= 0)
        rows.append(row)
    json.dump(rows, open(a.out, 'w'), indent=1)
    print(len(rows), 'games')


if __name__ == '__main__':
    main()
