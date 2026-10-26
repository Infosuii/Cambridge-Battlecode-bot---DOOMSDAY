"""Native opening economy and item timing, without reconstructing capture income.

Usage: python tools/replay/bench_native_progress.py <bench prefix> <report.json>
Income includes kills/bonuses; emblem timing medians are conditional on acquisition.
"""
from collections import Counter
import glob
import json
from pathlib import Path
import statistics
import sys
from review_v57_latest import value_at

FIELDS = ['earnedGold', 'collectedGems', 'submittedGems', 'deaths', 'monsterDamageDone', 'championDamageDone']


def main():
    rows, greed = [], Counter()
    for file in glob.glob(sys.argv[1] + '-seed*-s*/summary.json'):
        for game in json.loads(Path(file).read_text(encoding='utf8'))['per_game']:
            native = json.loads((Path(game['folder']) / 'summary.json').read_text(encoding='utf8'))
            row = {}
            assert native['match']['roundsStarted'] >= 250, 'short games need a separately reported cohort'
            for side, team in [('candidate', 'team' + game['side']), ('opponent', 'team' + ('B' if game['side'] == 'A' else 'A'))]:
                fields = {key: sum(value_at(t['runs'], 250) for t in native['championTimelines']
                                   if t['owner']['team'] == team and t['metric'] == key) for key in FIELDS}
                champs = [c for c in native['champions'] if c['team'] == team]
                fields['deaths_final'] = sum(float(c['metrics']['deaths']) for c in champs)
                times = {}
                for event in native['events']:
                    if event['kind'] == 'itemCombination' and event['owner'].get('team') == team:
                        for entry in event['entries']:
                            family = entry['target']['name'].split(' Emblem')[0]
                            times.setdefault(family, []).append(entry['timestamp']['round'])
                fields['emblems'] = {key: dict(count=len(values), before250=sum(x <= 250 for x in values), first=min(values))
                                     for key, values in times.items()}
                row[side] = fields
                if side == 'candidate':
                    for champion in champs:
                        for item in champion['items']:
                            if item['item'].startswith('Greed Emblem'):
                                greed[item['item']] += int(item['quantity'])
            rows.append(row)
    assert rows, 'no games'
    report = dict(games=len(rows), cutoff=250, note=__doc__.splitlines()[-1], candidate={}, opponent={}, candidate_greed_emblems=dict(greed))
    for side in ['candidate', 'opponent']:
        for key in FIELDS + ['deaths_final']:
            report[side][key] = statistics.mean(r[side][key] for r in rows)
        for family in ['Prospector', 'Capture', 'Treasure', 'Monster', 'Collectors', 'Greed']:
            appearances = [r[side]['emblems'][family] for r in rows if family in r[side]['emblems']]
            report[side][family] = dict(games_acquiring=len(appearances), emblems_before250=sum(a['before250'] for a in appearances),
                                        median_first=statistics.median(a['first'] for a in appearances) if appearances else None)
    Path(sys.argv[2]).write_text(json.dumps(report, indent=1) + '\n', encoding='utf8')
    print('native progress:', len(rows), 'games')


if __name__ == '__main__':
    main()
