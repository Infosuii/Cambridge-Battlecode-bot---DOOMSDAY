"""Describe which deficits coexist in lost pool games; estimates are bounds, not counterfactuals."""
from collections import Counter
import argparse
import json
from pathlib import Path

def one(path):
    d = json.loads(path.read_text())
    side = path.parent.name[-1]
    me = 'team'+side
    opponent = 'team'+('B' if side=='A' else 'A')
    if d['match']['outcome'] == me:
        return None
    bank = {x['team']: int(x['submittedGems']) for x in d['teams']}
    camp = Counter()
    handed = Counter()
    dead = Counter()
    first_bag_death = None
    for event in d['events']:
        owner = event['owner'].get('team')
        for e in event['entries']:
            if event['kind'] == 'gemCollection' and e.get('context') == 'campGroup':
                camp[owner] += int(e['value'])
            elif event['kind'] == 'gemLoss':
                target = e.get('target')
                if isinstance(target, dict) and target.get('kind') == 'champion':
                    qty = int(e['value'])
                    handed[owner] += qty
                    if owner == me and qty >= 40:
                        r = e['timestamp']['round']
                        first_bag_death = min(r, first_bag_death) if first_bag_death is not None else r
            elif event['kind'] == 'death' and e['timestamp']['round'] <= 150:
                dead[owner] += 1
    carried = sum(int(x['metrics']['gems']) for x in d['champions'] if x['team'] == me)
    lost = handed[me]
    return dict(map=path.parent.name[:-2],side=side,outcome=d['match']['outcome'],
        banked=bank[me],opponent_banked=bank[opponent],camp_gems=camp[me],
        opponent_camp_gems=camp[opponent],handed=lost,carried=carried,
        bag_death_round=first_bag_death,early_deaths=dead[me],enemy_early_deaths=dead[opponent],
        could_exceed_without_stolen_bags=bank[me]+lost > bank[opponent],
        could_exceed_with_remaining_bag=bank[me]+lost+carried > bank[opponent],
        could_exceed_if_stolen_bags_were_banked=bank[me]+lost+carried > max(0,bank[opponent]-lost))


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('runs',type=Path)
    cli.add_argument('tag')
    args=cli.parse_args()
    groups={}
    for run in sorted(args.runs.glob(f'gx-{args.tag}-pool-*')):
        paths=sorted(run.glob('games/*/summary.json'))
        if len(paths) != 172:
            raise ValueError(f'Incomplete pool: {run}')
        rows=[x for p in paths if (x:=one(p)) is not None]
        total=Counter(nonwins=len(rows))
        for x in rows:
            total['ties']+=x['outcome'] not in ('teamA','teamB')
            total['camp_deficit_20pct']+=x['camp_gems'] < .8*x['opponent_camp_gems']
            total['bag_death_40plus']+=x['bag_death_round'] is not None
            total['first150_death_deficit']+=x['early_deaths'] > x['enemy_early_deaths']
            for metric in ('could_exceed_without_stolen_bags','could_exceed_with_remaining_bag',
                           'could_exceed_if_stolen_bags_were_banked'):
                total[metric]+=x[metric]
        groups[run.name.rsplit('-',1)[1]]=dict(total=total,cells=rows)
    print(json.dumps(groups,indent=2))

if __name__=='__main__':
    main()
