"""Pooled report for tools/gauntlet.sh: per-opponent record and margin, then mechanism metrics of the candidate.

Usage: python tools/gauntlet_report.py <gauntlet out dir> <opponent names...>
Mechanism metrics come from each game's native summary (deaths, kills, gems lost on death to champions).
"""
import json
from pathlib import Path
import statistics
import sys


def side_stats(game, team):
    champs = [c for c in game['champions'] if c['team'] == team]
    lost = sum(float(x['value']) for e in game['events'] if e['kind'] == 'gemLoss' and e['owner'].get('team') == team
               for x in e['entries'] if x['context'] == 'champion')
    return dict(deaths=sum(float(c['metrics']['deaths']) for c in champs), kills=sum(float(c['metrics']['kills']) for c in champs),
                lost=lost, gold=sum(float(c['metrics']['earnedGold']) for c in champs))


def main():
    out = Path(sys.argv[1])
    rows = []
    allm = []
    for tag in sys.argv[2:]:
        games = []
        for shard in sorted(out.glob(f'vs-{tag}-seed*-s*')):
            if not (shard / 'summary.json').exists():
                continue
            for pg in json.loads((shard / 'summary.json').read_text(encoding='utf8'))['per_game']:
                folder = Path(pg['folder'])
                g = json.loads((folder / 'summary.json').read_text(encoding='utf8'))
                us = 'team' + pg['side']
                them = 'teamB' if us == 'teamA' else 'teamA'
                games.append(dict(win=pg['win'], margin=pg['gems'] - pg['opponent_gems'], us=side_stats(g, us), them=side_stats(g, them)))
        if not games:
            print(f'{tag:16} no games')
            continue
        m = lambda f: statistics.fmean(f(x) for x in games)
        rows.append((tag, len(games), m(lambda x: x['win']), m(lambda x: x['margin'])))
        allm += games
        print(f'{tag:16} games {len(games):4}  win {m(lambda x: x["win"]):.3f}  margin {m(lambda x: x["margin"]):+7.1f}'
              f'  deaths {m(lambda x: x["us"]["deaths"]):5.2f}/{m(lambda x: x["them"]["deaths"]):5.2f}'
              f'  kills {m(lambda x: x["us"]["kills"]):5.2f}/{m(lambda x: x["them"]["kills"]):5.2f}'
              f'  gems lost on death {m(lambda x: x["us"]["lost"]):6.1f}/{m(lambda x: x["them"]["lost"]):6.1f}'
              f'  gold {m(lambda x: x["us"]["gold"]):6.0f}/{m(lambda x: x["them"]["gold"]):6.0f}')
    if rows:
        print(f'POOL (opponents weighted equally): win {statistics.fmean(r[2] for r in rows):.3f}  margin {statistics.fmean(r[3] for r in rows):+.1f}'
              f'  worst-opponent margin {min(r[3] for r in rows):+.1f}  games {sum(r[1] for r in rows)}')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
