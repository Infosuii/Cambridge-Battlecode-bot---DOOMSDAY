"""Evaluate contact prognosis across disjoint layouts and a held-out opponent."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x,-40,40)))


def calibrate(x,y,reg=.015):
    mu=x.mean(axis=0)
    scale=np.maximum(x.std(axis=0),1e-4)
    z=np.column_stack((np.ones(len(x)),(x-mu)/scale))
    ridge=np.eye(z.shape[1])*reg
    ridge[0,0]=0
    w=np.zeros(z.shape[1])
    w[0]=np.log((y.mean()+1e-5)/(1-y.mean()+1e-5))
    for _ in range(45):
        p=sigmoid(z@w)
        g=z.T@(p-y)/len(y)+ridge@w
        h=(z.T*(p*(1-p)))@z/len(y)+ridge
        update=np.linalg.solve(h,g)
        w-=np.clip(update,-2,2)
        if max(abs(update))<1e-7:
            break
    raw=w[1:]/scale
    return w[0]-np.dot(raw,mu),raw


def ranking(y,p):
    order=np.argsort(-p,kind='stable')
    y,p=y[order],p[order]
    if len(y)==0 or not 0<y.mean()<1:
        return None,None
    positives=int(y.sum())
    negatives=len(y)-positives
    ends=np.r_[np.flatnonzero(p[:-1]!=p[1:]),len(p)-1]
    tp=np.r_[0,np.cumsum(y)[ends]]
    fp=np.r_[0,ends+1-tp[1:]]
    auc=np.sum(np.diff(fp)*(tp[1:]+tp[:-1]))/(2*positives*negatives)
    ap=np.sum(np.diff(tp)*tp[1:]/(tp[1:]+fp[1:]))/positives
    return float(auc),float(ap)


def metrics(y,p,cut):
    auc,ap=ranking(y,p)
    if not len(y):
        return dict(observations=0)
    alert=p>=cut
    loss=y==1
    return dict(observations=len(y),casualties=int(y.sum()),rate=float(y.mean()),auc=auc,average_precision=ap,
                brier=float(np.mean((y-p)**2)),alert_rate=float(alert.mean()),
                alert_precision=float(y[alert].mean()) if alert.any() else None,
                alert_recall=float(alert[loss].mean()) if loss.any() else None)


def prepare(folder):
    chunks=[]
    maps=[]
    opponents=[]
    fields=None
    runs=set()
    for path in sorted(folder.glob('contacts-*.jsonl')):
        for line in path.read_text().splitlines():
            x=json.loads(line)
            if x['id'] in runs or x['horizon']!=8 or x['interval']!=10:
                raise ValueError(x['id'])
            runs.add(x['id'])
            if fields is None:
                fields=x['fields']
            elif fields!=x['fields']:
                raise ValueError('Feature schema changed')
            if not x['rows']:
                continue
            d=np.asarray(x['rows'],dtype=float)
            if d.shape[1]!=len(fields)+5:
                raise ValueError(d.shape)
            chunks.append(d)
            maps.extend([x['map']]*len(d))
            opponents.extend([x['opponent']]*len(d))
    return np.concatenate(chunks),np.asarray(maps),np.asarray(opponents),fields,runs


def train(path):
    d,maps,opps,fields,runs=prepare(path)
    base={f:d[:,i+5] for i,f in enumerate(fields)}
    # Condition all examples on visible contact. Ratios turn pressure into
    # approximate fractions of health over a fixed, short horizon.
    hp=np.maximum(base['hp'],100.)
    feat=dict(lanch_z=base['lanch_z'],health=base['hp_fraction'],
              enemy_count=base['enemies'],friend_count=base['allies'],
              distance=base['nearest'],carry=np.minimum(base['bag'],120.)/60.,
              basic=np.minimum(base['basic_in']/hp,2.),
              burst=np.minimum(base['burst_in']/hp,3.),
              ready_damage=np.minimum(base['ready_out']/hp,2.),
              camp=np.minimum(base['active_camp_dps']/hp,1.5),
              linked_deficit=np.maximum(0,base['hp_fraction']-base['links_low_hp']),
              exposed_area=np.minimum(base['enemy_area_pairs'],4.),
              shield=np.minimum(base['shield']/hp,1.),
              idle_enemy=base['enemy_idle'],support_reach=base['lane'])
    held={name for name in set(maps) if int.from_bytes(sha256(('gx-contact-holdout:'+name).encode()).digest()[:2],'big')%5<2}
    new_map=np.isin(maps,list(held))
    new_opp=opps=='v92'
    own=d[:,0]==0
    train=~new_map & ~new_opp & own
    y=d[:,3]
    spans={'training':train,'held_layout':new_map&~new_opp&own,
           'held_opponent':new_opp&own,'both_held':new_map&new_opp&own,
           'both_held_early':new_map&new_opp&own&(base['round']<=250),
           'both_held_carriers':new_map&new_opp&own&(base['bag']>=25),
           'both_held_enemy_actors':new_map&new_opp&~own}
    families={
        'lanch':['lanch_z'],
        'health_and_lanch':['lanch_z','health','enemy_count','friend_count','distance','carry'],
        'ready_pressure':['lanch_z','health','enemy_count','friend_count','distance','carry','basic','burst','ready_damage',
                          'camp','linked_deficit','exposed_area','shield','idle_enemy','support_reach'],
    }
    out=dict(games=len(runs),layouts=len(set(maps)),held_layouts=sorted(held),held_opponent='v92',
             target='actor killed by champion in the next eight rounds under the observed policy',models={})
    for name,features in families.items():
        x=np.column_stack([feat[k] for k in features])
        intercept,w=calibrate(x[train],y[train])
        p=sigmoid(intercept+x@w)
        q=float(np.quantile(p[train],0.95))
        out['models'][name]=dict(intercept=float(intercept),weights=dict(zip(features,map(float,w))),
             training_threshold=q,sets={key:metrics(y[mask],p[mask],q) for key,mask in spans.items()})
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('samples',type=Path)
    a=p.parse_args()
    print(json.dumps(train(a.samples),indent=2,sort_keys=True))


if __name__=='__main__':
    main()
