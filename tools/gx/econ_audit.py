"""Aggregate local engine summary events without conflating camp income and loot."""
from collections import Counter
import argparse
import json
from pathlib import Path


def economy(path):
    data = json.loads(path.read_text())
    side = 'team' + path.parent.name[-1]
    mine = [c for c in data['champions'] if c['team'] == side]
    m = Counter(games=1, rounds=data['match']['roundsStarted'])
    for c in mine:
        for key in ('collectedGems', 'submittedGems', 'gems', 'deaths', 'kills', 'earnedGold', 'spentGold'):
            m[key] += int(c['metrics'][key])
    first_emblem = {}
    for event in data['events']:
        owner = event['owner']
        if owner.get('team') != side:
            continue
        kind = event['kind']
        if kind not in ('gemCollection','gemLoss','fuelExhausted','itemCombination','buyItem','gemSubmission','campClear'):
            continue
        for entry in event['entries']:
            r = entry['timestamp']['round']
            context = entry.get('context')
            if kind == 'fuelExhausted':
                m['fuel_first' if r <= 1 else 'fuel_early' if r <= 20 else 'fuel_late'] += 1
            elif kind == 'itemCombination':
                first_emblem[owner['id']] = min(r, first_emblem.get(owner['id'], r))
            elif kind == 'buyItem':
                m['first_100_buy_gold'] += int(entry['amount']) if r <= 100 else 0
            elif kind == 'campClear':
                m['first_100_clears'] += r <= 100
            elif kind == 'gemCollection':
                quantity = int(entry['value'])
                m['camp_gems' if context == 'campGroup' else 'other_gem_income'] += quantity
                if r <= 100:
                    m['first_100_collected'] += quantity
            elif kind == 'gemLoss':
                target = entry.get('target')
                if isinstance(target, dict) and target.get('kind') == 'champion':
                    m['lost_to_champion'] += int(entry['value'])
                else:
                    m['lost_other'] += int(entry['value'])
            elif kind == 'gemSubmission':
                m['deposits'] += 1
                if r <= 100:
                    m['first_100_banked'] += int(entry['value'])
    m['first_emblem_round_sum'] = sum(first_emblem.values())
    m['champions_with_emblem'] = len(first_emblem)
    m['champions'] = len(mine)
    return m


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('scratch', type=Path)
    cli.add_argument('tags', nargs='+')
    args = cli.parse_args()
    all_data = {}
    for tag in args.tags:
        runs = {}
        total = Counter()
        for run in sorted(args.scratch.glob('gx-' + tag + '-pool-*')):
            paths = sorted(run.glob('games/*/summary.json'))
            if len(paths) != 172:
                raise ValueError(f'{run}: expected full opponent pool, found {len(paths)}')
            m = Counter()
            for p in paths:
                m.update(economy(p))
            runs[run.name.split('-')[-1]] = dict(m)
            total.update(m)
        if not runs:
            raise ValueError(f'Unknown run tag: {tag}')
        all_data[tag] = dict(opponents=runs, total=dict(total))
    print(json.dumps(all_data, indent=2))


if __name__ == '__main__':
    main()
