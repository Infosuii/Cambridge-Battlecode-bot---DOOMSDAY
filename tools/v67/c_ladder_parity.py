"""Our own bot on the platform vs locally: per-team-game fuel-outs and deaths for each ladder duel arm
(research/proxy/ladder_arms.json + artifacts/local-only/duels summaries), next to a local run of the same version.

Usage: c_ladder_parity.py [--local-run RUN]
"""
import argparse
import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def team_fuel(d, team):
    return sum(len(e['entries']) for e in d['events'] if e['kind'] == 'fuelExhausted' and e['owner'].get('team') == team)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--local-run', default='c26-base-s1516')
    a = ap.parse_args()
    arms = json.loads((ROOT / 'research/proxy/ladder_arms.json').read_text())
    games = arms['games']
    print('example arm game:', json.dumps(games[0])[:400])
    acc = collections.defaultdict(lambda: collections.Counter())
    for g in games:
        mid = g.get('match') or g.get('matchId') or g.get('match_id')
        p = ROOT / 'artifacts/local-only/duels' / f'{mid}.json'
        if not p.exists():
            acc[g.get('arm')]['missing'] += 1
            continue
        d = json.loads(p.read_text(encoding='utf-8-sig'))
        side = g.get('side') or g.get('our_side')
        us = 'teamA' if str(side).lower() in ('a', 'teama') else 'teamB'
        them = 'teamB' if us == 'teamA' else 'teamA'
        c = acc[g.get('arm')]
        c['n'] += 1
        c['fuel_us'] += team_fuel(d, us)
        c['fuel_them'] += team_fuel(d, them)
        c['deaths_us'] += sum(int(x['metrics']['deaths']) for x in d['champions'] if x['team'] == us)
    for arm, c in sorted(acc.items()):
        n = max(1, c['n'])
        print(f"ladder arm {arm}: games {c['n']} (missing {c['missing']}), our fuel-outs/game {c['fuel_us'] / n:.2f}, "
              f"theirs {c['fuel_them'] / n:.2f}, our deaths {c['deaths_us'] / n:.1f}")
    run = json.loads((ROOT / 'artifacts/evaluations/v67' / a.local_run / 'games.json').read_text())['games']
    f = sum(g['fuel'] for g in run) / len(run)
    print(f'local {a.local_run}: our fuel-outs/game {f:.2f}, opponent {sum(g["opp_fuel"] for g in run) / len(run):.2f}')


if __name__ == '__main__':
    main()
