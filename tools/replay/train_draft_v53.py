"""Regularized, strength-adjusted draft model with disjoint team-pair validation.

Reads only compact metadata and final champion types from archived shards.
The full action arrays and bulk training data are never committed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]

def bucket(a, b):
    return int(hashlib.sha256('|'.join(sorted([a,b])).encode()).hexdigest()[:8],16)%10

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,default=ROOT/'artifacts/local-only/replays-20261023')
    p.add_argument('--out',type=Path,default=ROOT/'artifacts/local-only/v53-draft')
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    torch.manual_seed(53);torch.set_num_threads(8)
    cache=a.out/'compact.npz'
    if not cache.exists():
        ratings=json.loads((a.archive/'team_ratings.json').read_text())
        records=ratings['replays'];team_ids=sorted(ratings['ratings']);tid={s:i for i,s in enumerate(team_ids)}
        rows=[];maps=set()
        for sp in sorted(a.archive.glob('part*/shard-*.json')):
            side=json.loads(sp.read_text())
            with np.load(sp.with_suffix('.npz'),allow_pickle=False) as z:
                meta=z['meta'];offset=z['champion_offsets'];ch=z['final_champions']
            for e in side['replays']:
                r=records.get(e['replay']);i=e['row'];m=meta[i]
                if not r or m[6] not in (1,2) or m[10] or r['team_a'] not in tid or r['team_b'] not in tid:continue
                cc=ch[offset[i]:offset[i+1]];draft=np.zeros((2,12),dtype=np.float32)
                for c in cc:
                    if c[1] not in (0,1):continue
                    ct=int(c[2]);dt=3 if ct in (3,4) else ct-(ct>4)
                    draft[c[1],dt]=1
                key=(min(int(m[0]),int(m[1])),max(int(m[0]),int(m[1])),int(draft[0].sum()))
                maps.add(key);rows.append((key,tid[r['team_a']],tid[r['team_b']],int(m[6]==1),bucket(r['team_a'],r['team_b']),draft))
        maps=sorted(maps);mid={m:i for i,m in enumerate(maps)}
        np.savez(cache,map=np.array([mid[r[0]] for r in rows]),teams=np.array([[r[1],r[2]] for r in rows]),
                 y=np.array([r[3] for r in rows],dtype=np.float32),split=np.array([r[4] for r in rows]),
                 drafts=np.stack([r[5] for r in rows]),map_keys=np.array(maps),team_ids=np.array(team_ids))
        print('extracted',len(rows),'maps',len(maps),flush=True)
    z=np.load(cache);maps=z['map_keys'];draft=z['drafts'];y=z['y'];sp=z['split'];teams=z['teams'];m=z['map']
    n=len(y);nm=len(maps);nt=len(z['team_ids']);diff=draft[:,0]-draft[:,1]
    counter=np.stack([draft[:,0,i]*draft[:,1,j]-draft[:,0,j]*draft[:,1,i] for i in range(12) for j in range(i+1,12)],axis=1)
    # Main and map-specific pick effects, antisymmetric counter-pick effects, and map side bias.
    x=np.zeros((n,12+nm*12+66+nm),dtype=np.float32)
    x[:,:12]=diff
    for k in range(nm):x[m==k,12+k*12:12+(k+1)*12]=diff[m==k]
    x[:,12+nm*12:12+nm*12+66]=counter
    x[np.arange(n),12+nm*12+66+m]=1
    device='cuda' if torch.cuda.is_available() else 'cpu'
    X=torch.tensor(x,device=device);Y=torch.tensor(y,device=device);T=torch.tensor(teams,device=device)
    train=torch.tensor(sp<8,device=device);val=torch.tensor(sp==8,device=device);test=torch.tensor(sp==9,device=device)
    def fit(with_draft,reg):
        w=torch.zeros(X.shape[1],device=device,requires_grad=True)
        strength=torch.zeros(nt,device=device,requires_grad=True)
        opt=torch.optim.Adam([w,strength],lr=.04)
        best=None;bestval=1e9
        for epoch in range(301):
            opt.zero_grad()
            ww=w if with_draft else torch.cat([w[:12+nm*12+66]*0,w[12+nm*12+66:]])
            logits=X@ww+strength[T[:,0]]-strength[T[:,1]]
            loss=torch.nn.functional.binary_cross_entropy_with_logits(logits[train],Y[train])
            loss=loss+reg*(ww.square().mean())+.0001*strength.square().mean()
            loss.backward();opt.step()
            if epoch%10==0:
                with torch.no_grad():
                    vl=float(torch.nn.functional.binary_cross_entropy_with_logits(logits[val],Y[val]))
                    if vl<bestval:bestval=vl;best=(ww.detach().clone(),strength.detach().clone(),epoch)
        w,s,epoch=best
        with torch.no_grad():
            logits=X@w+s[T[:,0]]-s[T[:,1]]
            def metrics(mask):return {'n':int(mask.sum()),'logloss':float(torch.nn.functional.binary_cross_entropy_with_logits(logits[mask],Y[mask])),
                                     'accuracy':float(((logits[mask]>0)==(Y[mask]>0)).float().mean())}
        return {'reg':reg,'epoch':epoch,'train':metrics(train),'validation':metrics(val),'test':metrics(test)},w.cpu().numpy()
    base,_=fit(False,.01);models=[fit(True,r) for r in [.001,.01,.1]]
    best=min(models,key=lambda v:v[0]['validation']['logloss'])
    report={'rows':n,'maps':maps.tolist(),'teams':nt,'device':device,'split':'SHA256 unordered team pair: 0-7 train, 8 validation, 9 test; ratings fit only on train',
            'baseline':base,'candidates':[r for r,w in models],'selected':best[0],
            'limitations':['Observational associations, not causal effects.','Final-draft model evaluated on complete drafts; partial-draft inference requires match tests.','Archive is dated 2026-10-23; current bot revisions may differ.']}
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    (a.out/'model.json').write_text(json.dumps({'maps':maps.tolist(),'weights':best[1].tolist(),'report':report}))
    print(json.dumps({'rows':n,'baseline':base,'selected':best[0]}),flush=True)

if __name__=='__main__':main()
