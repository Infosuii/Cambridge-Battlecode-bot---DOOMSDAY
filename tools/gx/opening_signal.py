"""Which early match measurements predict the final outcome on held-out layouts?"""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import numpy as np


FEATURES = ('camp_gems', 'banked', 'emblems', 'spent_items', 'champion_kills', 'champion_deaths',
            'non_champion_deaths', 'bag_losses', 'camp_captures')


def one(path, limit):
    d = json.loads(path.read_text())
    if d['match']['roundsStarted'] <= limit:
        return None
    side = path.parent.name[-1]
    me = 'team' + side
    their = 'team' + ('A' if side == 'B' else 'B')
    m = {me:Counter(), their:Counter()}
    for event in d['events']:
        owner, kind = event['owner'], event['kind']
        if owner.get('team') not in m or kind not in ('gemCollection','gemSubmission','itemCombination','buyItem','kill','death','gemLoss'):
            continue
        for e in event['entries']:
            if not 0 < e['timestamp']['round'] <= limit:
                continue
            c = m[owner['team']]
            if kind == 'gemCollection' and e.get('context') == 'campGroup':
                c['camp_gems'] += int(e['value'])
                c['camp_captures'] += 1
            elif kind == 'gemSubmission':
                c['banked'] += int(e['value'])
            elif kind == 'itemCombination':
                c['emblems'] += int(e['value'])
            elif kind == 'buyItem':
                c['spent_items'] += int(e['amount'])
            elif kind == 'kill':
                c['champion_kills'] += 1
            elif kind == 'death':
                c['champion_deaths' if e.get('context') == 'champion' else 'non_champion_deaths'] += 1
            elif kind == 'gemLoss' and isinstance(e.get('target'),dict) and e['target'].get('kind') == 'champion':
                c['bag_losses'] += int(e['value'])
    return ([m[me][f]-m[their][f] for f in FEATURES],d['match']['outcome']==me,path.parent.name[:-2])


def sigmoid(x):
    return 1/(1+np.exp(-np.clip(x,-35,35)))


def model(x,y):
    # Standardise on the training rows only; ridge protects against related counters.
    mean,scale=x.mean(axis=0),np.maximum(x.std(axis=0),1e-8)
    z=np.column_stack((np.ones(len(x)),(x-mean)/scale))
    w=np.zeros(z.shape[1])
    reg=np.diag([.001]+[3.0]*(len(w)-1))
    for _ in range(30):
        p=sigmoid(z@w)
        h=(z.T*(p*(1-p)))@z+reg
        step=np.linalg.solve(h,z.T@(y-p)-reg@w)
        w+=step
        if np.linalg.norm(step)<1e-8:
            break
    return w,mean,scale


def metrics(scores,y):
    positive,negative=scores[y],scores[~y]
    a,b=positive[:,None],negative[None,:]
    auc=float(((a>b)+.5*(a==b)).mean())
    return dict(n=len(y),wins=int(y.sum()),auc=round(auc,4),
                accuracy=round(float(((scores>=0)==y).mean()),4))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('scratch',type=Path)
    p.add_argument('tag')
    p.add_argument('--round',type=int,default=150)
    a=p.parse_args()
    paths=sorted(a.scratch.glob(f'gx-{a.tag}-pool-*/games/*/summary.json'))
    if len(paths)!=516:
        raise ValueError(f'Expected three full opponent runs, found {len(paths)} games')
    rows=[r for path in paths if (r:=one(path,a.round)) is not None]
    x,y,m=(np.array(v) for v in zip(*rows))
    names=sorted(set(m),key=lambda name:sha256(('gx-opening-fold:'+name).encode()).digest())
    selection=np.isin(m,names[::2])
    out=[]
    for take in (selection,~selection):
        w,mean,scale=model(x[take],y[take])
        valid=x[~take]
        z=(valid-mean)/scale
        single={}
        for i,f in enumerate(FEATURES):
            sw,sm,sd=model(x[take,i:i+1],y[take])
            single[f]=metrics(sw[0]+sw[1]*(valid[:,i]-sm[0])/sd[0],y[~take])
        out.append(dict(train_maps=sorted(set(m[take])),test_maps=sorted(set(m[~take])),
            joint=metrics(w[0]+z@w[1:],y[~take]),single=single,
            weights={f:round(float(w[i+1]),4) for i,f in enumerate(FEATURES)}))
    print(json.dumps(dict(observed_round=a.round,games=len(rows),excluded_games=516-len(rows),folds=out),indent=2))


if __name__=='__main__':
    main()
