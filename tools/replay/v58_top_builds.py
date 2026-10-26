"""Describe top-opponent item sequences from cached ladder audits, restricted to development maps.

Usage: python tools/replay/v58_top_builds.py <audit.json> <report.json>
Uses V55_LIFE_DATA.json for sides/opponents and the registered training+selection partition. No replay downloads.
Sequences are descriptive and confounded by hero, map, income and game length; they are not causal build rankings.
"""
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
FAMILIES = ['Monster', 'Power', 'Durability', 'Treasure', 'Jungle', 'Home', 'Bruiser']
STATS = ['strength', 'focus', 'health']


def normal(name):
    return name.replace('_', '').replace('-', '')


def item(index):
    return FAMILIES[index // 6] + ' ' + STATS[(index % 6) // 2]


def main():
    parts = json.loads((ROOT / 'evaluation/schedules/map_partitions.json').read_text())['partitions']
    dev = {normal(m) for m in parts['training'] + parts['selection']}
    meta = {g['id']: g for g in json.loads((ROOT / 'artifacts/claude_ops/V55_LIFE_DATA.json').read_text(encoding='utf8'))}
    counts = defaultdict(Counter)
    games = Counter()
    for g in json.loads(Path(sys.argv[1]).read_text(encoding='utf8')):
        m = meta[g['id']]
        if normal(m['map']) not in dev or m['opp'] != 'Claudus Maximus':
            continue
        us = 0 if m['side'] == 'a' else 1
        for side in (0, 1):
            cohort = 'DOOMSDAY versus Claudus' if side == us else 'Claudus'
            games[cohort] += 1
            seen = defaultdict(list)
            for purchase in g['teams'][side]['purchases']:
                for index, number in purchase['items']:
                    if index % 2 and index not in seen[purchase['type']]:
                        seen[purchase['type']].append(index)
            for hero, seq in seen.items():
                counts[(cohort, hero)][tuple(seq[:6])] += 1
    report = dict(note=__doc__.splitlines()[-1], maps='registered28 development maps only',
                  source='cached v55 ladder audit; historical version, not current v57 strength evidence',
                  games=dict(games), cohorts={})
    for (cohort, hero), sequences in sorted(counts.items()):
        report['cohorts'].setdefault(cohort, {})[str(hero)] = [dict(emblems=[item(i) for i in seq], games=n)
                                                            for seq, n in sequences.most_common()]
    Path(sys.argv[2]).write_text(json.dumps(report, indent=1) + '\n', encoding='utf8')
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
