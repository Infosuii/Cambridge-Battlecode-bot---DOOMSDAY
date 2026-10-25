"""Per-team totals from official match summaries (bot_match.py / policy_ops compare game folders).

    python tools/match_stats.py <evaluation dir> [...]

For each game: per team the final collected, submitted and still-carried gems, gems lost (collected - submitted -
carried), deaths, kills, monster and champion damage, gold earned. Team A is the first bot of the folder's side label.
"""
import json
from pathlib import Path
import sys

METRICS = ('collectedGems', 'submittedGems', 'gems', 'deaths', 'kills', 'monsterDamageDone', 'championDamageDone', 'earnedGold')


def final(timeline):
    return float(timeline['runs'][-1]['value']) if timeline['runs'] else 0.0


def game(path):
    s = json.loads(path.read_text(encoding='utf-8'))
    out = {t: dict.fromkeys(METRICS, 0.0) for t in ('teamA', 'teamB')}
    for t in s['championTimelines']:
        if t['metric'] in METRICS:
            out[t['owner']['team']][t['metric']] += final(t)
    for v in out.values():
        v['lost'] = v['collectedGems'] - v['submittedGems'] - v['gems']
    return s['match']['outcome'], s['match']['roundsStarted'], out


def main():
    cols = ('collectedGems', 'submittedGems', 'lost', 'deaths', 'kills', 'monsterDamageDone', 'championDamageDone')
    print('game'.ljust(28), 'winner rounds |', ' '.join(c[:9].rjust(9) for c in cols), '| (teamA then teamB)')
    for root in map(Path, sys.argv[1:]):
        for path in sorted(root.glob('games/*/summary.json')):
            outcome, rounds, out = game(path)
            for team in ('teamA', 'teamB'):
                print(f'{path.parent.name[:28]:28} {outcome:6} {rounds:6} |', ' '.join(f'{out[team][c]:9.0f}' for c in cols), '|', team)


if __name__ == '__main__':
    main()
