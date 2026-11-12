"""Find shopping visits where prior consumables delayed an affordable emblem."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path


def match(path):
    data = json.loads(path.read_text())
    side = 'team' + path.parent.name[-1]
    won = data['match']['outcome'] == side
    by_player = defaultdict(list)
    for event in data['events']:
        if event['owner'].get('team') != side or event['kind'] not in ('buyConsumable','buyItem','itemCombination'):
            continue
        for e in event['entries']:
            by_player[event['owner']['id']].append((e['timestamp']['ordinal'],event['kind'],e))
    found = []
    for player, entries in by_player.items():
        rounds = defaultdict(list)
        for _, k, e in sorted(entries):
            rounds[e['timestamp']['round']].append((k,e))
        owned = Counter()
        emblem = 0
        for r, events in sorted(rounds.items()):
            prior = 0
            for kind, e in events:
                item = e['target']['name']
                if kind == 'itemCombination':
                    emblem += 1
                elif kind == 'buyConsumable':
                    prior += int(e['amount'])
                elif kind == 'buyItem':
                    qty = int(e['value'])
                    count = 25 if item.startswith('Greed') else 5
                    to_combine = count - (owned[item] % count)
                    gold = int(e['context'])
                    price = int(e['amount']) // qty
                    # Delaying a lock or crystal at this particular visit would
                    # have paid for an emblem even if previous shard purchases were unchanged.
                    if prior and r <= 250 and qty < to_combine and gold < price * to_combine <= gold + prior:
                        found.append(dict(round=r,player=player,shard=item,next_emblem=emblem+1,
                            needed=price*to_combine,available=gold,consumables=prior))
                    owned[item] += qty
    return won, found


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('scratch',type=Path)
    p.add_argument('tag')
    a=p.parse_args()
    out = {}
    for run in sorted(a.scratch.glob(f'gx-{a.tag}-pool-*')):
        cases, counts = [], Counter()
        for path in sorted(run.glob('games/*/summary.json')):
            won, found = match(path)
            outcome = 'win' if won else 'nonwin'
            counts[outcome+'_games'] += 1
            if not found:
                continue
            counts[outcome+'_affected'] += 1
            counts.update('emblem_'+str(e['next_emblem']) for e in found)
            cases.append(dict(case=path.parent.name,outcome=outcome,events=found))
        out[run.name] = dict(totals=counts,cases=cases)
    if not out:
        raise ValueError('No games')
    print(json.dumps(out,indent=2))


if __name__ == '__main__':
    main()
