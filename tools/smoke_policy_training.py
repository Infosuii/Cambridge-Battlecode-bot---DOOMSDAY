"""Tiny labelled SYNTHETIC optimizer/checkpoint/GPU functional test. Never uses match data or real model files."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'python'))
from nfs.policy import training as T,model as M,export as E,observation as O,candidates as C
import numpy as np
import torch

def smoke(out,device='cpu'):
    out=Path(out).resolve()
    if not out.is_relative_to((ROOT/'artifacts/tmp').resolve()):raise ValueError('synthetic smoke output must stay in artifacts/tmp')
    if out.exists():raise FileExistsError('fresh synthetic directory required')
    out.mkdir(parents=True);model=M.init_untrained(M.build_model('policy_v2'),99)
    manifest=E.export_model(model,'synthetic_optimizer_only',out/'model','untrained',dict(synthetic=True,source='tiny functional test only'))
    before=E.checksum(E.state_to_blob(model.state_dict(),model.cfg));rng=np.random.default_rng(77)
    for name,n in (('train',32),('validation',8)):
        obs=rng.normal(0,.1,(n,O.OBS_DIM)).astype(np.float32)
        obs[:,90:95]=0;obs[:,40:90]=0;obs[:,167:173]=0;obs[:,95:167]=0
        feat=rng.normal(0,.2,(n,16,12)).astype(np.float32);legal=np.zeros((n,16),bool);legal[:,:4]=True
        context=np.arange(n,dtype=np.int64)%4;chosen=np.arange(n,dtype=np.int64)%4
        with torch.no_grad():
            logits=model(torch.tensor(obs),'move',torch.tensor(feat),torch.tensor(legal),torch.tensor(context))
            logp=torch.log_softmax(logits,dim=-1).gather(1,torch.tensor(chosen)[:,None]).squeeze(1)
        path=out/(name+'.npz');np.savez_compressed(path,obs=obs,feat=feat,legal=legal,context=context,
            chosen=chosen,teacher=np.full(n,-1,np.int64),head=np.full(n,M.HEAD_IDS['move'],np.int64),
            behavior_logits=logits.numpy(),behavior_logp=logp.numpy(),ppo_mask=np.ones(n,bool),imitation_mask=np.zeros(n,bool),
            terminal_return=np.linspace(-.5,.5,n,dtype=np.float32))
        metadata=dict(version=2,format='NFS2',synthetic=True,engine_version='1.0.3',obs_hash=O.OBS_SCHEMA_HASH,
            action_hash=C.ACTION_SCHEMA_HASH,behavior_model_checksum=manifest['checksum'],
            rows=[dict(episode_id='synthetic_'+name,group_id='synthetic_'+name,synthetic=True) for _ in range(n)],
            sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        path.with_suffix('.manifest.json').write_text(json.dumps(metadata),encoding='utf-8')
    args=dict(head='move',mode='ppo',authorized=True,minutes=1,epochs=2,device=device,_synthetic_test=True)
    full=T.fit(out/'model',out/'train.npz',out/'validation.npz',out/'uninterrupted',**args)
    resumed=T.fit(out/'model',out/'train.npz',out/'validation.npz',out/'resumed',
        resume_checkpoint=out/'uninterrupted/checkpoints/epoch-0001.pt',**args)
    a=torch.load(out/'uninterrupted/checkpoint.pt',map_location='cpu',weights_only=True)
    b=torch.load(out/'resumed/checkpoint.pt',map_location='cpu',weights_only=True)
    def equal(x,y):
        if isinstance(x,torch.Tensor):return isinstance(y,torch.Tensor) and torch.equal(x,y)
        if isinstance(x,dict):return x.keys()==y.keys() and all(equal(x[k],y[k]) for k in x)
        if isinstance(x,(list,tuple)):return len(x)==len(y) and all(equal(i,j) for i,j in zip(x,y))
        return x==y
    checks={key:equal(a[key],b[key]) for key in ('actor','critic','optimizer','critic_optimizer','rng','torch_rng','cuda_rng','updates','completed_epochs')}
    original=E.state_to_blob(E.load_model(out/'model').state_dict(),model.cfg)
    changed=[k for k,v in a['actor'].items() if not torch.equal(v,model.state_dict()[k])]
    checks['only_selected_head_changed']=bool(changed) and all(k.startswith('heads.move.') for k in changed)
    checks['baseline_unchanged']=E.checksum(original)==before
    checks['two_total_updates']=a['updates']==2 and b['updates']==2
    checks['not_trained_lifecycle']=json.loads((out/'uninterrupted/export/manifest.json').read_text())['status']=='untrained'
    report=dict(synthetic=True,match_data_used=False,real_model_parameter_updates=0,device=full['device'],
        gpu=torch.cuda.get_device_name(0) if full['device']=='cuda' else None,torch_version=str(torch.__version__),
        checks=checks,passed=all(checks.values()),source_model_checksum=before,full=full,resumed=resumed)
    (out/'synthetic_smoke.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,default=ROOT/'artifacts/tmp'/('synthetic_optimizer_'+str(time.time_ns())))
    p.add_argument('--device',choices=('cpu','cuda'),default='cpu');a=p.parse_args()
    report=smoke(a.out,a.device);print(json.dumps(dict(passed=report['passed'],synthetic=True,device=report['device'],checks=report['checks'],report=str(a.out/'synthetic_smoke.json')),indent=2))
    if not report['passed']:raise SystemExit(1)
