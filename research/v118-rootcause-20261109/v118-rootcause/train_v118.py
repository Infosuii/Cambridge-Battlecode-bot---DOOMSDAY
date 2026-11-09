"""Isolated on-policy continuation of the exact v113 network on corrected runtime behavior."""
import os,sys,json,time,random,shutil,subprocess,concurrent.futures,hashlib
from pathlib import Path
os.environ['NN_DEPLOY_PREP']='1'
import sys as _s;from pathlib import Path as _P;_s.path.insert(0,str(_P(__file__).resolve().parents[1]));_s.path.insert(0,str(_P(__file__).resolve().parent))
from project import ROOT,ARENA,save,sha,digest,build,check_stop
from local_panel import run,read_native,storage_guard
from prepare_campaign import prepare
from setup_training import setup
setup();LAB=ROOT/'training/agent2/lab';sys.path.insert(0,str(LAB))
import numpy as np,torch
from torch import nn
import torch.nn.functional as F
from nn_model import student,Prep,load
from policy_math import live_logits,blend,vfeat,timelines,priv_features
from team_reward import gae_game
from quant_policy import anchored,validate
from policy_rows import stdout,parse_rows
CAMPAIGN_NAME=os.environ.get('TRAIN_CAMPAIGN_NAME','corrected-v113')
SOURCE_ACTOR=os.environ.get('TRAIN_SOURCE','p15')
PREFIX=os.environ.get('TRAIN_PREFIX','')
LIMIT=int(os.environ.get('TRAIN_ITERATIONS','6'))
LR=float(os.environ.get('TRAIN_LR','.00005'))
WD=ROOT/'training'/CAMPAIGN_NAME;WD.mkdir(exist_ok=True)
DEV='cuda';TEMP=.4

def emit(s):
    print(time.strftime('%H:%M:%S'),s,flush=True)
    with (WD/'training.log').open('a',encoding='utf-8') as f:f.write(time.strftime('%H:%M:%S')+' '+s+'\n')

def actor(name,weights,rl=False):
    src=ARENA/'bots'/name/'src';original=ARENA/'bots'/SOURCE_ACTOR/'src'
    expected={p.name:p.read_bytes() for p in original.iterdir() if p.is_file()}
    expected['nn_weights.h']=Path(weights).read_bytes()
    if rl:expected['common.h']=b'#define A2_NN_RLIVE 1\n#define A2_NN_RL_KEEP 1\n'+expected['common.h']
    if rl:
        # v118: hp01 lineage lacks the verified NRZ/NRQ recorder repair; apply it to rollout actors only.
        import rl_logger
        _o={'nnrec.cpp':expected['nnrec.cpp'].decode('utf-8').replace('\r\n','\n')};rl_logger.patch(_o);expected['nnrec.cpp']=_o['nnrec.cpp'].encode('utf-8')
    if src.exists():assert {p.name:p.read_bytes() for p in src.iterdir()}==expected,'Frozen actor changed'
    else:
        src.mkdir(parents=True)
        for n,b in expected.items():(src/n).write_bytes(b)
    w=build(name,debug=rl)
    save(src.parent/'training-actor.json',{'source_sha256':digest(src),'weights_sha256':sha(weights),'wasm_sha256':sha(w),'rl':rl,'base':SOURCE_ACTOR,'debug':rl})
    return name

def export(net,it):
    pt=WD/f'student_{it}.pt';header=WD/f'student_{it}.h'
    torch.save(net.state_dict(),pt)
    subprocess.run([sys.executable,'-P',str(LAB/'nn_export.py'),str(pt),'student',str(header)],check=True,capture_output=True)
    return header

def evaluate(it,weights,plan):
    name=actor(f'{PREFIX}s{it:03}',weights)
    rows=run(f'{PREFIX}neural-dev-{it:03}',[name],[Path(p) for p in plan['maps']['dev']],plan['styles'],12)
    assert not any(r['faults'] or r['opponent_faults'] for r in rows)
    by={o:sum(r['score'] for r in rows if r['opponent']==o)/sum(r['opponent']==o for r in rows) for o in plan['styles']}
    score=sum(r['score'] for r in rows)/len(rows)
    report={'iteration':it,'actor':name,'score':score,'opponents':by,'fuel':sum(r['fuel'] for r in rows),'games':len(rows),'purpose':'Development checkpoint selection, never final promotion'}
    save(WD/f'eval_{it}.json',report);emit('DEV '+json.dumps(report));return report

def privileged(tl,ids,rounds):
    out=np.zeros((len(rounds),71),np.float32)
    for ti,team in enumerate(ids):
        for slot,body in enumerate(team[:6]):
            m=tl.get(body,{})
            for j,key in enumerate(('gems','submittedGems','earnedGold','kills','deaths')):
                a=m.get(key,np.zeros(1));v=a[np.minimum(rounds,len(a)-1)]
                out[:,ti*30+slot*5+j]=v;out[:,60+ti*5+j]+=v
    out[:,70]=rounds/1000.
    return np.sign(out)*np.log1p(np.abs(out))

def batch(it,weights,plan,value):
    name=actor(f'{PREFIX}r{it:03}',weights,True)
    rng=random.Random(2026110800+it+int(os.environ.get('TRAIN_SEED_OFFSET','0')))
    maps=rng.sample(list(plan['maps']['train']),16)
    styles=plan['styles'][((it-1)%3)*3:((it-1)%3+1)*3]
    schedule=None
    if os.environ.get('TRAIN_BALANCED')=='1':
        inc=[p for p in plan.get('incident_maps',[]) if p in plan['maps']['train']];maps=inc+rng.sample([p for p in plan['maps']['train'] if p not in inc],48-len(inc))
        mix=plan.get('train_styles',plan['styles'])
        styles=list(dict.fromkeys(mix))
        schedule=[(name,mix[(k+it)%len(mix)],m,side) for k,m in enumerate(maps) for side in ('a','b')]
    rows=run(f'{PREFIX}neural-rollouts-{it:03}',[name],list(map(Path,maps)),styles,10,True,schedule=schedule)
    assert len(rows)==96 and not any(r['faults'] or r['opponent_faults'] for r in rows)
    rows.sort(key=lambda r:(r['opponent'],r['map_file'],r['side']))
    chunks=[];games=[]
    for g in rows:
        d=read_native(g['summary']);rs=parse_rows(stdout(g['replay_bundle'],g['side']))
        team='team'+g['side'].upper();tl,lead,ids=timelines(d,team)
        assert {r['me'] for r in rs}<=set(ids[0])
        X=np.stack([r['x'] for r in rs]);Q=np.stack([r['q'] for r in rs]);TA=np.array([r['ta'] for r in rs],np.int64);LP=np.array([r['tlp'] for r in rs],np.float32);BS=np.array([r['bs'] for r in rs],np.int64)
        rnd=np.maximum(0,np.array([r['r'] for r in rs])-1);P=privileged(tl,ids,rnd)
        for k in np.linspace(0,len(rs)-1,min(3,len(rs)),dtype=int):assert np.allclose(P[k],priv_features(tl,ids,int(rnd[k])),atol=2e-6)
        z=2*g['score']-1
        # Monte Carlo terminal-win credit avoids exponentially erasing opening
        # decisions before a fresh critic has learned long-horizon returns.
        ret=(z-.1*np.tanh(lead[np.minimum(rnd,len(lead)-1)]/1000.)).astype(np.float32)
        _,check=gae_game(rs,lead,z,np.zeros(len(rs)),1.,1.)
        assert np.allclose(ret,check,atol=2e-5)
        chunks.append({'X':X,'Q':Q,'TA':TA,'LP':LP,'BS':BS,'P':P,'RET':ret})
        games.append({**g,'rows':len(rs),'bodies':len(set(r['me'] for r in rs))})
    cols={k:np.concatenate([c[k] for c in chunks]) for k in chunks[0]}
    data=WD/f'data_{it}.npz';np.savez_compressed(data,**cols)
    save(WD/f'data_{it}.json',{'games':games,'rows':len(cols['X']),'data_sha256':sha(data),'actor':name,'weights_sha256':sha(weights),'all_decisions_retained':True,'critic_uses_previous_round':True,'return':'terminal team outcome minus bounded previous-round potential; gamma=lambda=1','training_maps_only':True})
    return {k:torch.as_tensor(v,device=DEV) for k,v in cols.items()}

def update(it,data,net,ref,value,opt):
    X,Q,TA,LP,BS,P,RET=(data[k] for k in ('X','Q','TA','LP','BS','P','RET'));n=len(X)
    with torch.no_grad():
        native_error=validate(Q,TA,LP,TEMP)
        old=torch.cat([blend(live_logits(net,X[s:s+4096],X[s:s+4096]),BS[s:s+4096]) for s in range(0,n,4096)])
        unavailable=Q < -1e8
        fd=(F.log_softmax(old.masked_fill(unavailable,-2e9)/TEMP,-1).gather(1,TA[:,None]).squeeze(1)-LP).abs()
        assert float(fd.median())<=.05 and float(fd.quantile(.9))<=.25,'Input/model drift; anchoring cannot conceal bad collection'
        v0=torch.cat([value(torch.cat((vfeat(X[s:s+4096]),P[s:s+4096]),1)).squeeze(1) for s in range(0,n,4096)])
        adv=RET-v0;adv=(adv-adv.mean())/adv.std().clamp_min(1e-6)
    stats=[];stopped=False
    for epoch in range(3):
        permutation=torch.randperm(n,device=DEV)
        for begin in range(0,n,2048):
            check_stop();ix=permutation[begin:begin+2048];x=X[ix];bs=BS[ix]
            current=blend(live_logits(net,x,x),bs);lg=anchored(Q[ix],current,old[ix]);lp=F.log_softmax(lg/TEMP,-1);prob=lp.exp()
            ratio=(lp.gather(1,TA[ix,None]).squeeze(1)-LP[ix]).exp()
            pg=-torch.minimum(ratio*adv[ix],ratio.clamp(.8,1.2)*adv[ix]).mean()
            with torch.no_grad():
                rlg=anchored(Q[ix],blend(live_logits(ref,x,x),bs),old[ix]);rlp=F.log_softmax(rlg/TEMP,-1)
                behavior=F.log_softmax(Q[ix]/TEMP,-1)
            kl=(prob*(lp.clamp_min(-30)-rlp.clamp_min(-30))).sum(-1).mean()
            behavior_kl=(prob*(lp.clamp_min(-30)-behavior.clamp_min(-30))).sum(-1).mean()
            ent=-(prob*lp.clamp_min(-30)).sum(-1).mean()
            vp=value(torch.cat((vfeat(x),P[ix]),1)).squeeze(1);vl=(vp-RET[ix]).square().mean()
            loss=pg+.02*kl-.003*ent+.5*vl
            assert torch.isfinite(loss)
            opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(list(net.parameters())+list(value.parameters()),1.);opt.step()
            stats.append([pg.item(),kl.item(),ent.item(),vl.item(),behavior_kl.item()])
        if np.mean(stats[-max(1,n//2048):],axis=0)[4]>.03:stopped=True;break
    report={'iteration':it,'rows':n,'native_logp_max_error':float(native_error.max()),'float_logp_p50':float(fd.median()),'float_logp_p90':float(fd.quantile(.9)),'float_logp_max':float(fd.max()),'updates':len(stats),'epochs_completed':epoch+1,'trust_region_early_stop':stopped,'mean_pg_kl_entropy_value_behaviorkl':np.mean(stats,axis=0).tolist(),'critic_explained_variance_before':float(1-(RET-v0).var()/RET.var().clamp_min(1e-6))}
    save(WD/f'update_{it}.json',report);emit('UPDATE '+json.dumps(report))

def main():
    plan_file=os.environ.get('TRAIN_PLAN')
    plan=json.loads(Path(plan_file).read_text()) if plan_file else prepare()
    check_stop();assert torch.cuda.is_available();torch.set_num_threads(2);torch.manual_seed(81113);np.random.seed(81113);random.seed(81113)
    if os.environ.get('TRAIN_INITIAL'):
        plan={**plan,'initial_checkpoint':os.environ['TRAIN_INITIAL'],'checkpoint_sha256':sha(os.environ['TRAIN_INITIAL'])}
    assert sha(plan['initial_checkpoint'])==plan['checkpoint_sha256']
    for role in plan['maps'].values():
        for p,h in role.items():assert sha(p)==h
    net=load(student(Prep()),plan['initial_checkpoint'],DEV).to(DEV)
    ref=load(student(Prep()),plan['initial_checkpoint'],DEV).to(DEV).eval()
    for p in ref.parameters():p.requires_grad_(False)
    value=nn.Sequential(nn.Linear(571,256),nn.ReLU(),nn.Linear(256,256),nn.ReLU(),nn.Linear(256,1)).to(DEV)
    opt=torch.optim.Adam([{'params':net.parameters(),'lr':LR},{'params':value.parameters(),'lr':2e-4}])
    state=WD/'state.json';start=0;best=None
    if state.exists():
        st=json.loads(state.read_text());start=st['iteration'];best=st['best']
        checkpoint=torch.load(WD/f'resume_{start}.pt',map_location=DEV,weights_only=True)
        net.load_state_dict(checkpoint['net']);value.load_state_dict(checkpoint['value']);opt.load_state_dict(checkpoint['optimizer'])
        torch.set_rng_state(checkpoint['cpu_rng'].cpu());torch.cuda.set_rng_state_all([r.cpu() for r in checkpoint['cuda_rng']])
    else:
        save(WD/'run.json',{'gpu':torch.cuda.get_device_name(),'torch':torch.__version__,'base_source':SOURCE_ACTOR,'base_source_sha256':digest(ARENA/'bots'/SOURCE_ACTOR/'src'),'initial':plan['checkpoint_sha256'],'script_sha256':sha(__file__),'reward':'team_win_MC','gamma':1.,'lambda':1.,'actor_lr':LR,'critic_lr':2e-4,'native_anchored':True,'disjoint_map_roles':True,'limit_iterations':LIMIT,'balanced_all_styles':os.environ.get('TRAIN_BALANCED')=='1','map_plan_sha256':sha(plan_file) if plan_file else None,'training_opponent_mix':plan.get('train_styles',plan['styles']),'checkpoint_selection':'development release games only'})
        best=evaluate(0,export(net,0),plan)
        torch.save(net.state_dict(),WD/'best.pt')
    for it in range(start+1,LIMIT+1):
        storage_guard();begin=time.monotonic();emit(f'BEGIN {it}/{LIMIT}')
        header=export(net,f'collection_{it}');data=batch(it,header,plan,value);update(it,data,net,ref,value,opt);del data
        torch.cuda.empty_cache();header=export(net,it)
        if it%2==0:
            ev=evaluate(it,header,plan)
            if ev['score']>best['score']:
                best=ev;shutil.copy2(WD/f'student_{it}.pt',WD/'best.pt')
        torch.save({'net':net.state_dict(),'value':value.state_dict(),'optimizer':opt.state_dict(),'cpu_rng':torch.get_rng_state(),'cuda_rng':torch.cuda.get_rng_state_all()},WD/f'resume_{it}.pt')
        save(state,{'iteration':it,'best':best,'elapsed_last_iteration':round(time.monotonic()-begin,1)})
        emit('SAVED '+json.dumps(json.loads(state.read_text())))
    save(WD/'complete.json',{'iterations':LIMIT,'rollout_games':96*LIMIT,'selected':best,'base_source':SOURCE_ACTOR,'note':'Final independent evaluation and behavior retuning remain separate; no ladder changes.'})
if __name__=='__main__':main()
