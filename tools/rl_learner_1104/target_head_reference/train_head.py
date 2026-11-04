"""Bounded on-policy target-head learner. Input adapter contract is in LEARNER_INPUT.md.
No game data is synthesized here. All supplied complete games are validated or refused.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import numpy as np
import torch
from head import TargetHead

ABI='jd-target-head-160-16-4-v1'

def packed(model):
    values=[]
    for name in ('context','query','key','features','far','gate'):
        layer=getattr(model,name)
        values.extend(layer.weight.detach().cpu().T.contiguous().flatten().tolist())
        values.extend(layer.bias.detach().cpu().tolist())
    return np.asarray(values,dtype='<f4')

def weight_hash(model):
    return hashlib.sha256(packed(model).tobytes()).hexdigest()

def export(model,path):
    values=packed(model)
    path.write_text('#pragma once\nnamespace jd_head_weights {\ninline constexpr float values[11826] = {'+
                    ','.join(float(v).hex()+'f' for v in values)+'};\n}\n')

def save(model,opt,out,updates,feature_abi,history):
    out.mkdir(parents=True,exist_ok=False)
    torch.save(dict(state=model.state_dict(),optimizer=opt.state_dict() if opt else None,
                    updates=updates,architecture=ABI,feature_abi=feature_abi,weights_sha256=weight_hash(model)),out/'head.pt')
    export(model,out/'head_weights.h')
    (out/'report.json').write_text(json.dumps(history,indent=2)+'\n')

def load_data(folder,map_manifest,ck,synthetic_test=False):
    meta=json.loads((folder/'manifest.json').read_text())
    if meta['data_origin'] != ('synthetic-test' if synthetic_test else 'engine'):
        raise ValueError('data origin does not match explicitly selected mode')
    if meta['schema']!='jd-head-training-adapter-v1' or meta['architecture']!=ABI:
        raise ValueError('incompatible adapter/architecture')
    if meta['feature_abi_sha256']!=ck['feature_abi'] or meta['policy_weights_sha256']!=ck['weights_sha256']:
        raise ValueError('feature ABI or collection weights differ from checkpoint')
    for key in ('executor_sha256','collector_source_sha256','wasm_sha256','engine_sha256'):
        if len(meta[key])!=64 or any(c not in '0123456789abcdef' for c in meta[key]):
            raise ValueError('missing provenance '+key)
    datafile=folder/'data.npz'
    if hashlib.sha256(datafile.read_bytes()).hexdigest()!=meta['data_sha256']:raise ValueError('data hash differs')
    maps=json.loads(map_manifest.read_text())
    train={m['sha256'] for m in maps['maps'] if m['split']=='training'}
    episodes=meta['episodes'];keys=[e['key'] for e in episodes]
    if not episodes or len(set(keys))!=len(keys):raise ValueError('missing/duplicate complete games')
    with np.load(datafile,allow_pickle=False) as z:d={k:z[k] for k in z.files}
    n=len(d['action']);K=int(meta['camp_count']);P=int(meta['physical_count'])
    if n==0 or not 1<=K<=63 or not 1<=P<=64:raise ValueError('invalid sizes')
    shapes={'context':(n,160),'camps':(n,K,16),'features':(n,K,4),'native_logits':(n,K+1),
            'valid':(n,K+1),'mapping':(n,K+1),'reference':(n,),'action':(n,),'old_logp':(n,),
            'game':(n,),'body_id':(n,),'decision_index':(n,)}
    for name,shape in shapes.items():
        if name not in d or d[name].shape!=shape:raise ValueError('bad shape '+name)
        if not np.isfinite(d[name]).all():raise ValueError('nonfinite '+name)
    for name in ('mapping','reference','action','game','body_id','decision_index'):
        if d[name].dtype.kind not in 'iu':raise ValueError('noninteger '+name)
    if not np.isin(d['valid'],[0,1]).all():raise ValueError('invalid mask')
    valid=d['valid'].astype(bool)
    if not valid.any(-1).all():raise ValueError('empty support')
    if ((d['mapping'][valid]<0)|(d['mapping'][valid]>=P)).any():raise ValueError('mapping bounds')
    if ((d['action']<0)|(d['action']>=P)|(d['reference']<0)|(d['reference']>=P)).any():raise ValueError('action bounds')
    for name in ('reference','action'):
        if not (valid&(d['mapping']==d[name][:,None])).any(-1).all():raise ValueError('missing '+name+' support')
    if set(d['game'].tolist())!={i for i,e in enumerate(episodes) if e['decisions']>0}:raise ValueError('game IDs or empty/missing decisions')
    returns=np.empty(n,dtype=np.float32)
    for i,e in enumerate(episodes):
        if (e['map_sha256'] not in train or e['status']!='terminated' or e['truncated'] or not e['all_decisions_present']
                or e['terminal_outcome'] not in (-1,0,1)):raise ValueError('ineligible episode '+e['key'])
        sel=d['game']==i
        if int(sel.sum())!=e['decisions']:raise ValueError('decision count '+e['key'])
        for body in np.unique(d['body_id'][sel]):
            ix=d['decision_index'][sel&(d['body_id']==body)]
            if not np.array_equal(np.sort(ix),np.arange(1,len(ix)+1)):raise ValueError('missing/replayed decision index')
        returns[sel]=e['terminal_outcome']
    tensors={k:torch.as_tensor(d[k],dtype=torch.float32) for k in ('context','camps','features','native_logits','old_logp')}
    tensors.update({k:torch.as_tensor(d[k],dtype=torch.long) for k in ('mapping','reference','action','game')})
    tensors['valid']=torch.as_tensor(valid);tensors['returns']=torch.as_tensor(returns)
    return meta,tensors,P

def distribution(model,d,P,sl):
    return model(d['context'][sl],d['camps'][sl],d['features'][sl],d['native_logits'][sl],
                 d['valid'][sl],d['mapping'][sl],d['reference'][sl],P)[0]

def chosen_logp(p,action):
    v=p.gather(1,action[:,None]).squeeze(1)
    if not (v>0).all() or not torch.isfinite(v).all():raise ValueError('nonpositive/nonfinite chosen probability')
    return v.log()

def diagnostics(model,d,P,old,chunk):
    kl=0.;max_logp=0.;count=len(d['action']);entropy=0.
    with torch.no_grad():
        for start in range(0,count,chunk):
            sl=slice(start,start+chunk);p=distribution(model,d,P,sl);o=old[sl]
            # Both policies have the same mathematical support; distinguish true zero from underflow.
            if ((o>0)&(p<=0)).any():raise ValueError('support lost during update')
            pos=o>0
            kval=torch.zeros_like(o);kval[pos]=o[pos]*(o[pos].log()-p[pos].log())
            kl+=kval.sum().item()
            lp=chosen_logp(p,d['action'][sl]);max_logp=max(max_logp,(lp-d['old_logp'][sl]).abs().max().item())
            pos=p>0;entropy-=(p[pos]*p[pos].log()).sum().item()
    return dict(full_old_to_new_kl=kl/count,max_chosen_logp_change=max_logp,mean_entropy=entropy/count)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--synthetic-test',action='store_true',help='explicit test fixtures only; never report as game training')
    ap.add_argument('--init',action='store_true');ap.add_argument('--seed',type=int,default=1104)
    ap.add_argument('--feature-abi',help='SHA256 of frozen feature/executor observation ABI (init only)')
    ap.add_argument('--checkpoint',type=Path);ap.add_argument('--data',type=Path);ap.add_argument('--map-manifest',type=Path)
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--epochs',type=int,default=2)
    ap.add_argument('--lr',type=float,default=1e-4);ap.add_argument('--clip',type=float,default=.1)
    ap.add_argument('--entropy',type=float,default=.003);ap.add_argument('--max-kl',type=float,default=.01)
    ap.add_argument('--grad-norm',type=float,default=.5);ap.add_argument('--chunk',type=int,default=1024)
    ap.add_argument('--threads',type=int,default=2)
    a=ap.parse_args();torch.set_num_threads(a.threads);torch.manual_seed(a.seed)
    if a.out.exists():raise ValueError('output directory must be new')
    model=TargetHead()
    if a.init:
        if not a.feature_abi or len(a.feature_abi)!=64 or any(c not in '0123456789abcdef' for c in a.feature_abi):
            raise ValueError('init requires frozen feature ABI SHA256')
        save(model,None,a.out,0,a.feature_abi,dict(kind='initialization only, NOT trained',weights_sha256=weight_hash(model)))
        return
    if not a.checkpoint or not a.data or not a.map_manifest:raise ValueError('checkpoint/data/map manifest required')
    ck=torch.load(a.checkpoint,weights_only=True,map_location='cpu')
    if ck['architecture']!=ABI:raise ValueError('checkpoint architecture differs')
    model.load_state_dict(ck['state'],strict=True)
    if weight_hash(model)!=ck['weights_sha256']:raise ValueError('checkpoint weight hash differs')
    meta,d,P=load_data(a.data,a.map_manifest,ck,a.synthetic_test);n=len(d['action']);ng=len(meta['episodes'])
    old=[]
    with torch.no_grad():
        for start in range(0,n,a.chunk):old.append(distribution(model,d,P,slice(start,start+a.chunk)))
    old=torch.cat(old)
    replay=(chosen_logp(old,d['action'])-d['old_logp']).abs().max().item()
    if replay>2e-4:raise ValueError('collection replay failed '+str(replay))
    opt=torch.optim.Adam(model.parameters(),lr=a.lr)
    if ck['optimizer'] is not None:opt.load_state_dict(ck['optimizer'])
    # Fixed zero baseline. No same-batch outcome centering, no critic/GAE implied.
    advantage=d['returns'];history=[];accepted=0
    for epoch in range(a.epochs):
        previous=copy.deepcopy(model.state_dict());previous_opt=copy.deepcopy(opt.state_dict())
        opt.zero_grad();loss_sum=0.;clipped=0
        for start in range(0,n,a.chunk):
            sl=slice(start,start+a.chunk);p=distribution(model,d,P,sl);lp=chosen_logp(p,d['action'][sl])
            ratio=(lp-d['old_logp'][sl]).exp();adv=advantage[sl]
            surrogate=torch.minimum(ratio*adv,ratio.clamp(1-a.clip,1+a.clip)*adv)
            entropy=-(p*p.clamp_min(torch.finfo(p.dtype).tiny).log()).sum(-1)
            loss=-(surrogate+a.entropy*entropy).sum()/ng
            loss.backward();loss_sum+=loss.detach().item();clipped+=((ratio-1).abs()>a.clip).sum().item()
        norm=torch.nn.utils.clip_grad_norm_(model.parameters(),a.grad_norm,error_if_nonfinite=True)
        opt.step();diag=diagnostics(model,d,P,old,a.chunk)
        record=dict(epoch=epoch,loss=loss_sum,gradient_norm_before_clip=norm.item(),pre_step_clip_fraction=clipped/n,**diag)
        if diag['full_old_to_new_kl']>a.max_kl:
            model.load_state_dict(previous);opt.load_state_dict(previous_opt)
            record['accepted']=False;record['reason']='post-step full KL exceeds threshold; rolled back';history.append(record);break
        record['accepted']=True;history.append(record);accepted+=1
    final=diagnostics(model,d,P,old,a.chunk)
    rep=dict(kind=('SYNTHETIC TEST ONLY' if a.synthetic_test else 'bounded target-head PPO, no strength claim'),games=ng,decisions=n,parameters=sum(p.numel() for p in model.parameters()),
             objective='sum across team stochastic decisions per game, mean across games',reward='gamma1 terminal team outcome',
             baseline='fixed zero',settings=dict(lr_requested=a.lr,lr_effective=opt.param_groups[0]['lr'],clip=a.clip,entropy=a.entropy,max_kl=a.max_kl,grad_norm=a.grad_norm,chunk=a.chunk,threads=a.threads),initial_replay_max_error=replay,epochs=history,final_exported_float32=final,
             weights_sha256=weight_hash(model),feature_abi_sha256=ck['feature_abi'],parent_checkpoint=str(a.checkpoint),
             dataset_manifest_sha256=hashlib.sha256((a.data/'manifest.json').read_bytes()).hexdigest(),
             map_manifest_sha256=hashlib.sha256(a.map_manifest.read_bytes()).hexdigest(),accepted_updates=accepted)
    save(model,opt,a.out,ck['updates']+accepted,ck['feature_abi'],rep)
    print(json.dumps(rep,indent=2))

if __name__=='__main__':main()
