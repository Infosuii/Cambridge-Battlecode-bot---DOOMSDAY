"""Measure team and hero-specific support/combat outcomes from completed native match summaries.

Usage: python tools/replay/v58_role_report.py <bench prefix> <report.json>
Hero means are conditional on appearances; rates use match rounds, not alive turns. Draft and duration confound comparisons.
"""
from collections import defaultdict
import glob
import json
from pathlib import Path
import sys

FIELDS = ('healingDone', 'healingReceived', 'shieldingDone', 'monsterDamageDone',
          'championDamageDone', 'deaths', 'earnedGold', 'spentGold')


def main():
    sums = {side: defaultdict(float) for side in ('candidate', 'opponent')}
    heroes = {side: defaultdict(lambda: defaultdict(float)) for side in sums}
    games = 0
    for summary in sorted(glob.glob(sys.argv[1] + '-seed*-s*/summary.json')):
        for g in json.loads(Path(summary).read_text(encoding='utf8'))['per_game']:
            native = json.loads((Path(g['folder']) / 'summary.json').read_text(encoding='utf8'))
            rounds = int(native['match']['roundsStarted'])
            games += 1
            for side, team in [('candidate', 'team' + g['side']), ('opponent', 'team' + ('B' if g['side'] == 'A' else 'A'))]:
                sums[side]['rounds'] += rounds
                for champion in native['champions']:
                    if champion['team'] != team:
                        continue
                    actor = heroes[side][champion['name']]
                    actor['appearances'] += 1
                    actor['rounds'] += rounds
                    for field in FIELDS:
                        value = float(champion['metrics'][field])
                        sums[side][field] += value
                        actor[field] += value
    assert games, 'no completed games'

    def rates(values, denominator):
        return dict(n=denominator, totals=dict(values),
                    mean={key: values[key] / denominator for key in FIELDS},
                    per1000_match_rounds={key: 1000 * values[key] / max(1, values['rounds']) for key in FIELDS})

    result = dict(games=games, note=__doc__.splitlines()[-1],
                  teams={side: rates(data, games) for side, data in sums.items()},
                  heroes={side: {name: rates(data, int(data['appearances'])) for name, data in values.items()}
                          for side, values in heroes.items()})
    Path(sys.argv[2]).write_text(json.dumps(result, indent=1) + '\n', encoding='utf8')
    print('games', games)
    for side in sums:
        print(side, result['teams'][side]['mean'])
        for name, values in result['heroes'][side].items():
            if name == 'Marcella':
                print(side, name, values['n'], values['mean'])


if __name__ == '__main__':
    main()
