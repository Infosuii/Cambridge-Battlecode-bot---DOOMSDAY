"""Independent event-vs-final-metric checks before constructing dense rewards."""
from collections import defaultdict


def audit(stats):
    if not stats['diagnostics']['detailedCaptureComplete'] or any(stats['diagnostics']['botFaults'].values()):
        raise ValueError('incomplete or faulted statistics')
    metrics = {}
    for champion in stats['champions']:
        key = champion['team'], int(champion['id'])
        if key in metrics:
            raise ValueError('duplicate champion identity')
        metrics[key] = {k:int(champion['metrics'][k]) for k in ('collectedGems','submittedGems','gems')}
    events = defaultdict(lambda:defaultdict(int))
    contexts = defaultdict(set)
    for event in stats['events']:
        if event['kind'] not in ('gemCollection','gemLoss','gemSubmission'):
            continue
        owner = event['owner']
        if owner['kind'] != 'champion':
            raise ValueError('unexpected gem-event owner')
        key = owner['team'], int(owner['id'])
        if key not in metrics:
            raise ValueError('unknown gem-event body')
        for entry in event['entries']:
            amount = int(entry['value'])
            if amount < 0:
                raise ValueError('negative gem amount')
            events[key][event['kind']] += amount
            contexts[event['kind']].add(entry.get('context'))
    teams = defaultdict(lambda:defaultdict(int))
    for key, final in metrics.items():
        e = events[key]
        if e['gemCollection'] != final['collectedGems'] or e['gemSubmission'] != final['submittedGems']:
            raise ValueError(f'event/final-metric mismatch {key}')
        balance = e['gemCollection'] - e['gemLoss'] - e['gemSubmission']
        if balance != final['gems']:
            raise ValueError(f'event balance differs from independently recorded inventory {key}: {balance} != {final["gems"]}')
        for field, value in final.items():
            teams[key[0]][field] += value
        teams[key[0]]['lostGems'] += e['gemLoss']
    for team in stats['teams']:
        if teams[team['team']]['submittedGems'] != int(team['submittedGems']):
            raise ValueError('champion/team submitted total mismatch')
    return dict(bodies=len(metrics),teams={k:dict(v) for k,v in teams.items()},
                contexts={k:sorted(v,key=str) for k,v in contexts.items()},
                independent_final_inventory_check=True)
