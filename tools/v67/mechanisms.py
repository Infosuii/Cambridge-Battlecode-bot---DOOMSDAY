"""Native per-game mechanism medians: income, fighting and gems lost, at fixed rounds."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import statistics

ROOT=Path(__file__).resolve().parents[2]
METRICS=['earnedGold','collectedGems','monsterDamageDone','deaths','kills','championDamageDone','submittedGems']

def value_at(timeline,at):
    elapsed=0;last=0
    for run in timeline['runs']:
        last=float(run['value']);elapsed+=int(run['duration'])
        if elapsed>at:return last
    return last

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run',required=True)
    a=ap.parse_args();folder=ROOT/'artifacts/evaluations/v67'/a.run
    games=json.loads((folder/'games.json').read_text())['games']
    samples=defaultdict(lambda:defaultdict(list));mismatches=0
    for game in games:
        data=json.loads((ROOT/game['folder']/'summary.json').read_text())
        ours='team'+game['side'].upper()
        for team in ['teamA','teamB']:
            name='candidate' if team==ours else 'opponent'
            timelines=[t for t in data['championTimelines'] if t['owner'].get('team')==team and t['metric'] in METRICS]
            losses=[e for e in data['events'] if e['kind']=='gemLoss' and e['owner'].get('team')==team]
            for window in [100,250,500,1000,'end']:
                at=100000000 if window=='end' else window
                totals={metric:sum(value_at(t,at) for t in timelines if t['metric']==metric) for metric in METRICS}
                totals['gemsLostToChampions']=sum(int(x['value']) for e in losses for x in e['entries']
                                                if x.get('context')=='champion' and x['timestamp']['round']<=at)
                for metric,value in totals.items():samples[name+'@'+str(window)][metric].append(value)
            for c in data['champions']:
                if c['team']!=team:continue
                events=sum(int(x['value']) for e in losses if e['owner'].get('id')==c['id'] for x in e['entries'])
                m=c['metrics'];balance=int(m['collectedGems'])-int(m['submittedGems'])-int(m['gems'])
                mismatches+=events!=balance
    medians={name:{metric:statistics.median(v) for metric,v in metrics.items()} for name,metrics in samples.items()}
    report=dict(run=a.run,games=len(games),note='Native timeline snapshots; games ending before a window retain their final value. Medians over all scheduled games.',
                gem_loss_accounting_mismatches=mismatches,medians=medians)
    (folder/'mechanisms.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
