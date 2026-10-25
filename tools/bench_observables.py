"""Derived mechanism measurements from official summaries (no replay bytes or machine paths in outputs).
Usage: python tools/bench_observables.py <bench prefix> <output.json>
"""
from pathlib import Path
from collections import defaultdict
import glob,json,statistics as st,sys

def at(runs, sample):
    n=0
    for r in runs:
        n+=int(r['duration'])
        if sample<n:return float(r['value'])
    return float(runs[-1]['value']) if runs else 0.0

def one(g):
    d=json.loads((Path(g['folder'])/'summary.json').read_text(encoding='utf8'))
    team='team'+g['side']; other='team'+('B' if g['side']=='A' else 'A')
    result=[]
    for t in (team,other):
        cs=[c for c in d['champions'] if c['team']==t]
        es=[e for e in d['events'] if isinstance(e['owner'],dict) and e['owner'].get('team')==t]
        banks=[int(x['value']) for e in es if e['kind']=='gemSubmission' for x in e['entries']]
        buys=[x for e in es if e['kind']=='buyItem' for x in e['entries']]
        # Official buy event context is gold BEFORE the purchase (verified against replay snapshots).
        crystals=[x for e in es if e['kind']=='buyConsumable' for x in e['entries'] if x['target'].get('name')=='Teleport Crystal']
        row={'wards':sum(len(e['entries']) for e in es if e['kind']=='wardPlacement'),
             'banks':len(banks),'bank_size_mean':st.mean(banks) if banks else None,'bank_size_median':st.median(banks) if banks else None,
             'deaths':sum(int(c['metrics']['deaths']) for c in cs),
             'bag_lost':sum(int(c['metrics']['collectedGems'])-int(c['metrics']['submittedGems'])-int(c['metrics']['gems']) for c in cs),
             'champion_damage':sum(float(c['metrics']['championDamageDone']) for c in cs),
             'crystal_buys':len(crystals),
             'crystal_buys_displacing_shard':sum(int(x['context'])//30>(int(x['context'])-10)//30 for x in crystals),
             'faults':int(d['diagnostics']['botFaults'][t]),'fuel':sum(len(e['entries']) for e in es if e['kind']=='fuelExhausted')}
        row['wards_per_1000_rounds']=1000*row['wards']/max(1,int(d['match']['roundsStarted']))
        for W in (100,250,500):
            row[f'equipment_bought_R{W}']=sum(x['amount'] for x in buys if x['timestamp']['round']<=W)
            tls=[x for x in d['championTimelines'] if x['metric']=='earnedGold' and x['owner'].get('team')==t]
            income=sum(at(x['runs'],W) for x in tls)
            row[f'gold_per_actor_R{W}']=income/max(1,len(cs))
            vs=[x for x in tls if x['owner'].get('name')=='Vesper Vale']
            if vs and income:row[f'Vesper_gold_share_R{W}']=sum(at(x['runs'],W) for x in vs)/income
            else:row[f'Vesper_gold_share_R{W}']=None
        row['first_1000']=None
        tl=next((x for x in d['teamTimelines'] if x['metric']=='submittedGems' and x['owner']==t),None)
        if tl:
            n=0
            for r in tl['runs']:
                if int(r['value'])>=1000:row['first_1000']=n;break
                n+=int(r['duration'])
        result.append(row)
    return result

def main():
    rows=[]
    for p in sorted(glob.glob(sys.argv[1]+'-seed*-s*/summary.json')):
        seed=Path(p).parent.name.split('-seed')[-1].split('-')[0]
        for g in json.loads(Path(p).read_text(encoding='utf8'))['per_game']:
            a,b=one(g);rows.append({'map':g['map'],'side':g['side'],'seed':seed,'candidate':a,'opponent':b})
    aggregate={}
    for k in rows[0]['candidate']:
        v={}
        for side in ('candidate','opponent'):
            xs=[r[side][k] for r in rows if r[side][k] is not None]
            v[side]={'n':len(xs),'mean':st.mean(xs) if xs else None,'median':st.median(xs) if xs else None,'sum':sum(xs) if xs else None}
        aggregate[k]=v
    Path(sys.argv[2]).write_text(json.dumps({'games':len(rows),'metrics':aggregate,'per_game':rows},indent=1)+'\n',encoding='utf8')
    print(len(rows),'games')
    for k,v in aggregate.items():print(k,v['candidate']['mean'],v['opponent']['mean'])
if __name__=='__main__':main()
