"""Later-only, bounded direct-policy training. Importing, preparation and preflight never update weights.

Uses terminal Monte Carlo returns, not the legacy residual PPO/GAE adapter. Match outcomes are targets only.
Every optimizer step requires explicit authorization. No automatic collection, promotion or submission.
"""
from __future__ import annotations
from collections import Counter
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import torch
from . import dataset as D, records as R, observation as O, candidates as C, losses as L
from .export import load_blob, load_model, export_model
from .model import HEAD_IDS

ROOT=Path(__file__).resolve().parents[3]

def writable(path):
    path=Path(path).resolve()
    if not path.is_relative_to(ROOT/'artifacts') or path==ROOT/'artifacts':
        raise ValueError('output must be in a dedicated workspace artifacts directory')
    return path

def _sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def terminal_return(game,round_number,gamma=.9997):
    terminal=(2*float(game['win'])-1)+.25*(int(game['gems'])-int(game['opponent_gems']))/1000
    # roundsStarted counts round0. An action in the final started round receives an undiscounted terminal reward.
    last=max(0,int(game['rounds'])-1)
    if int(round_number)<0 or int(round_number)>last:raise ValueError('decision round outside completed match')
    return terminal*gamma**(last-int(round_number))

def prepare(receipts,out,*,gamma=.9997,validation_fraction=.2):
    """Read completed official NFS2 checks. Never run a game or learning job."""
    from nfs import engine
    if not 0<gamma<=1 or not 0<validation_fraction<1:raise ValueError('discount/split range')
    out=writable(out)
    if out.exists():raise FileExistsError('fresh dataset output required')
    training=set(json.loads((ROOT/'evaluation/schedules/map_partitions.json').read_text())['partitions']['training'])
    rows=[];models=set();episodes=set();sources=[]
    for receipt in map(Path,receipts):
        run=json.loads(receipt.read_text());model=receipt.parent/'model';manifest,_=load_blob(model)
        models.add(manifest['checksum']);sources.append(dict(receipt=str(receipt.resolve()),sha256=_sha(receipt)))
        for game in run['games']:
            if game['map'] not in training:raise ValueError('selection/final maps cannot enter training data')
            if game['faults'] or game.get('invalid_records') or game.get('bot_error_lines'):
                raise ValueError('faulty or malformed rollout cannot enter the first experiment')
            folder=Path(game['folder']);identity=json.loads((folder/'engine_identity.json').read_text())
            side=game['side'];key='wasm_a' if side=='A' else 'wasm_b'
            if identity[key]!=run['wasm_sha256']:raise ValueError('receipt/rollout behavior identity mismatch')
            summary=json.loads((folder/'summary.json').read_text())
            if summary['match']['engineVersion']!='1.0.3':raise ValueError('only engine1.0.3 gameplay')
            actual=engine.parse_summary(summary,folder,game['map'],side).row()
            if any(actual[k]!=game[k] for k in ('win','gems','opponent_gems','rounds','faults')):
                raise ValueError('receipt/summary outcome mismatch')
            episode=hashlib.sha256((str(folder.resolve())+side+_sha(folder/'summary.json')).encode()).hexdigest()
            if episode in episodes:raise ValueError('duplicate episode')
            episodes.add(episode)
            # Same map and unordered Wasm pair, including both sides, remain one provenance group.
            group=hashlib.sha256((identity['map']+'|'.join(sorted((identity['wasm_a'],identity['wasm_b'])))).encode()).hexdigest()
            recs=R.decode_stdout(engine.team_stdout(folder,side),expected_obs_hash=O.OBS_SCHEMA_HASH,
                                 expected_action_hash=C.ACTION_SCHEMA_HASH)
            ds=D.build_dataset(recs,episode_id=episode,group_id=group,synthetic=False,
                               expected_action_hash=C.ACTION_SCHEMA_HASH)
            for row in ds.rows:
                row['terminal_return']=terminal_return(actual,row['decision']['round'],gamma)
            rows.extend(ds.rows)
    if len(models)!=1:raise ValueError('one pinned behavior model per batch required')
    groups=sorted({r['group_id'] for r in rows})
    if len(groups)<2:raise ValueError('at least two independent provenance groups required')
    valid={g for g in groups if int(g[:16],16)/2**64<validation_fraction}
    # Predetermined hash-order fallback guarantees nonempty partitions without inspecting outcomes.
    if not valid:valid={groups[0]}
    if len(valid)==len(groups):valid.remove(groups[-1])
    train=[r for r in rows if r['group_id'] not in valid];validation=[r for r in rows if r['group_id'] in valid]
    D.assert_disjoint_groups(train,validation);out.mkdir(parents=True)
    for name,part in (('train',train),('validation',validation)):
        batch=D.collate(part);arrays={k:v.numpy() for k,v in batch.items() if k!='metadata'}
        arrays['terminal_return']=np.asarray([r['terminal_return'] for r in part],np.float32)
        path=out/(name+'.npz');np.savez_compressed(path,**arrays)
        metadata=dict(version=2,format='NFS2',synthetic=False,engine_version='1.0.3',
            obs_hash=O.OBS_SCHEMA_HASH,action_hash=C.ACTION_SCHEMA_HASH,behavior_model_checksum=next(iter(models)),
            target='discounted terminal win plus .25 submitted-margin/1000; terminal MC, no GAE',gamma=gamma,
            rows=batch['metadata'],counts=dict(rows=len(part),matches=len({r['episode_id'] for r in part}),
                ppo_eligible=int(arrays['ppo_mask'].sum()),imitation_eligible=int(arrays['imitation_mask'].sum())),
            sources=sources,sha256=_sha(path))
        path.with_suffix('.manifest.json').write_text(json.dumps(metadata,indent=2)+'\n')
    return out

def read_batch(path):
    arrays,meta=D.load_arrays(path)
    if type(meta.get('synthetic')) is not bool:raise ValueError('explicit synthetic/real data provenance required')
    n=len(arrays['head'])
    if meta.get('engine_version')!='1.0.3' or meta.get('obs_hash')!=O.OBS_SCHEMA_HASH or meta.get('action_hash')!=C.ACTION_SCHEMA_HASH:
        raise ValueError('training batch schema/engine mismatch')
    expected={'obs':(n,O.OBS_DIM),'feat':(n,16,12),'legal':(n,16),'behavior_logits':(n,16),
              'behavior_logp':(n,),'chosen':(n,),'teacher':(n,),'head':(n,),'context':(n,),
              'ppo_mask':(n,),'imitation_mask':(n,),'terminal_return':(n,)}
    for k,shape in expected.items():
        if k not in arrays or arrays[k].shape!=shape:raise ValueError('training batch shape mismatch: '+k)
    if len(meta['rows'])!=n:raise ValueError('metadata row mismatch')
    if any(not np.isfinite(arrays[k]).all() for k in ('obs','feat','behavior_logp','terminal_return')):
        raise ValueError('nonfinite training input/target')
    if not np.isin(arrays['legal'],[0,1]).all() or not np.isin(arrays['head'],list(HEAD_IDS.values())).all():
        raise ValueError('invalid mask/head')
    if not np.isin(arrays['context'],[0,1,2,3]).all():raise ValueError('invalid context code')
    return arrays,meta

def preflight(model_dir,train,validation,head,mode='ppo'):
    if head not in HEAD_IDS or mode not in ('ppo','imitation'):raise ValueError('unknown head/mode')
    manifest,_=load_blob(model_dir,expected_obs=O.OBS_SCHEMA_HASH,expected_action=C.ACTION_SCHEMA_HASH)
    model=load_model(model_dir);datasets=[];groups=[];report={}
    for label,path in (('train',train),('validation',validation)):
        a,m=read_batch(path);datasets.append((a,m));groups.append({r['group_id'] for r in m['rows']})
        if mode=='ppo' and m.get('behavior_model_checksum')!=manifest['checksum']:
            raise ValueError('PPO must start from the exact recorded behavior model')
        mask=np.asarray(a[mode+'_mask' if mode=='ppo' else 'imitation_mask'],bool)&(a['head']==HEAD_IDS[head])
        indices=np.flatnonzero(mask);error=0.
        with torch.no_grad():
            for start in range(0,len(indices),256):
                ix=indices[start:start+256]
                z=model(torch.tensor(a['obs'][ix]),head,torch.tensor(a['feat'][ix]),
                        torch.tensor(a['legal'][ix],dtype=torch.bool),torch.tensor(a['context'][ix]))
                chosen=a['chosen'][ix] if mode=='ppo' else a['teacher'][ix]
                lp,ok=L.selected_logp(z,torch.tensor(a['legal'][ix],dtype=torch.bool),torch.tensor(chosen))
                if not bool(ok.all()):raise ValueError('eligible row has no valid selected action')
                if mode=='ppo':
                    legal=a['legal'][ix].astype(bool);actual=z.numpy()
                    error=max(error,float(np.max(np.abs(actual[legal]-a['behavior_logits'][ix][legal]))))
                    if not np.allclose(actual[legal],a['behavior_logits'][ix][legal],rtol=2e-5,atol=2e-6) or \
                       not np.allclose(lp.numpy(),a['behavior_logp'][ix],atol=2e-5,rtol=0):
                        raise ValueError('behavior logits/logp mismatch; refuse off-policy data')
        report[label]=dict(eligible=len(indices),max_logit_error=error,synthetic=bool(m.get('synthetic')))
    if groups[0]&groups[1]:raise ValueError('train/validation provenance leakage')
    return report,datasets

def fit(model_dir,train,validation,out,*,head='move',mode='ppo',authorized=False,minutes=5,epochs=4,seed=20261024,resume_checkpoint=None):
    # This is intentionally before model, optimizer, filesystem or data work.
    if not authorized:raise PermissionError('explicit --i-authorize-training required; no training performed')
    if not 0<minutes<=30 or not 1<=epochs<=4:raise ValueError('bounded run: 0<minutes<=30, 1..4 epochs')
    out=writable(out)
    if out.exists():raise FileExistsError('fresh run directory required; checkpoints never overwritten')
    report,data=preflight(model_dir,train,validation,head,mode)
    if any(r['synthetic'] for r in report.values()):raise ValueError('synthetic data may not be labelled real training')
    if report['train']['eligible']<16 or report['validation']['eligible']<4:
        raise ValueError('need at least16 eligible training and4 validation rows for this head')
    torch.manual_seed(seed);rng=np.random.default_rng(seed)
    torch.set_float32_matmul_precision('highest')
    device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    actor=load_model(model_dir).to(device)
    # First experiment protects other policies: encoder and other heads stay frozen.
    for p in actor.parameters():p.requires_grad_(False)
    for p in actor.heads[head].parameters():p.requires_grad_(True)
    critic=torch.nn.Sequential(torch.nn.Linear(O.OBS_DIM,64),torch.nn.Tanh(),torch.nn.Linear(64,1)).to(device)
    optimizer=torch.optim.Adam(actor.heads[head].parameters(),lr=1e-4)
    value_optimizer=torch.optim.Adam(critic.parameters(),lr=3e-4)
    a,meta=data[0];mask=a['ppo_mask' if mode=='ppo' else 'imitation_mask'].astype(bool)&(a['head']==HEAD_IDS[head])
    indices=np.flatnonzero(mask);deadline=time.time()+minutes*60
    history=[];updates=0;stop='epochs_complete';start=time.time();completed_epochs=0
    if resume_checkpoint is not None:
        old=torch.load(resume_checkpoint,map_location=device,weights_only=True)
        if (old.get('version'),old.get('head'),old.get('mode'),old.get('train_sha256'))!=(2,head,mode,meta['sha256']):
            raise ValueError('checkpoint/data/head mismatch')
        if old.get('validation_sha256')!=data[1][1]['sha256'] or old.get('max_epochs')!=epochs:
            raise ValueError('checkpoint validation/epoch limit mismatch')
        deadline=float(old['absolute_deadline']);completed_epochs=int(old['completed_epochs'])
        if time.time()>=deadline or completed_epochs>=epochs:raise ValueError('checkpoint deadline expired or experiment complete')
        actor.load_state_dict(old['actor']);critic.load_state_dict(old['critic'])
        optimizer.load_state_dict(old['optimizer']);value_optimizer.load_state_dict(old['critic_optimizer'])
        rng.bit_generator.state=old['rng'];torch.set_rng_state(old['torch_rng'].cpu())
        if torch.cuda.is_available() and old['cuda_rng']:torch.cuda.set_rng_state_all([x.cpu() for x in old['cuda_rng']])
        updates=int(old['updates']);history=old.get('history',[])
    out.mkdir(parents=True)
    behavior,_=load_blob(model_dir)
    export_model(load_model(model_dir),behavior['name'],out/'behavior',behavior['status'],behavior['provenance'])
    def snapshot():
        # Recovery rolls back at most the unfinished epoch. Never extend the original deadline.
        state=dict(version=2,head=head,mode=mode,actor={k:v.detach().cpu() for k,v in actor.state_dict().items()},
            critic={k:v.detach().cpu() for k,v in critic.state_dict().items()},optimizer=optimizer.state_dict(),
            critic_optimizer=value_optimizer.state_dict(),rng=rng.bit_generator.state,torch_rng=torch.get_rng_state(),
            cuda_rng=torch.cuda.get_rng_state_all() if torch.cuda.is_available() else [],behavior_model=str((out/'behavior').resolve()),
            config=actor.cfg,behavior_model_checksum=behavior['checksum'],
            data_paths=dict(train=str(Path(train).resolve()),validation=str(Path(validation).resolve())),
            train_sha256=meta['sha256'],validation_sha256=data[1][1]['sha256'],updates=updates,history=history,
            completed_epochs=completed_epochs,max_epochs=epochs,absolute_deadline=deadline,stop=stop)
        temporary=out/'checkpoint.partial.pt';torch.save(state,temporary);temporary.replace(out/'checkpoint.pt')
    snapshot()
    for epoch in range(completed_epochs,epochs):
        rng.shuffle(indices)
        for offset in range(0,len(indices),256):
            if time.time()>=deadline:stop='deadline';break
            ix=indices[offset:offset+256]
            t=lambda key,dtype=None:torch.as_tensor(a[key][ix],device=device,dtype=dtype)
            obs=t('obs');legal=t('legal',torch.bool)
            logits=actor(obs,head,t('feat'),legal,t('context'))
            if mode=='ppo':
                values=critic(obs).squeeze(-1);target=t('terminal_return');advantages=target-values.detach()
                advantages=(advantages-advantages.mean())/(advantages.std(unbiased=False)+1e-6)
                loss,metrics=L.ppo_loss(logits,legal,t('chosen'),t('behavior_logp'),advantages,
                    ppo_mask=torch.ones(len(ix),device=device,dtype=torch.bool),entropy_coefficient=.003)
                if metrics['approx_kl']>.015:stop='KL_limit';break
                if metrics['entropy']<.05:stop='entropy_collapse';break
                vloss=L.critic_loss(values,target,mask=torch.ones(len(ix),device=device,dtype=torch.bool))
            else:
                loss,metrics=L.imitation_loss(logits,legal,t('teacher'),imitation_mask=torch.ones(len(ix),device=device,dtype=torch.bool))
                vloss=None
            if not bool(torch.isfinite(loss)):raise ValueError('nonfinite loss; stop')
            optimizer.zero_grad();loss.backward()
            norm=torch.nn.utils.clip_grad_norm_(actor.heads[head].parameters(),.5,error_if_nonfinite=True)
            optimizer.step()
            if vloss is not None:
                value_optimizer.zero_grad();vloss.backward()
                torch.nn.utils.clip_grad_norm_(critic.parameters(),.5,error_if_nonfinite=True);value_optimizer.step()
            updates+=1;history.append(dict(epoch=epoch,update=updates,loss=float(loss.detach()),grad_norm=float(norm),**metrics))
        if stop!='epochs_complete':break
        completed_epochs=epoch+1;snapshot()
    snapshot()
    result=dict(status='trained' if updates else 'unmodified',mode=mode,head=head,updates=updates,device=str(device),
        elapsed_seconds=time.time()-start,stop=stop,preflight=report,history=history,
        validation_use='disjoint parity/data gate only; not a strength selection result',submitted=False)
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    if updates:
        export_model(actor.cpu(),'policy_v2_candidate',out/'export','trained',dict(synthetic=False,source='bounded authorized NFS2 '+mode,
            trained_heads=[head],untrained_or_inherited_other_heads=True,shared_encoder_frozen=True,
            parameter_updates=updates,training_data_sha256=meta['sha256'],report=str(out/'report.json')))
    return result
