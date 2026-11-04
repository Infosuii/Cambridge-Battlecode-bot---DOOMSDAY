"""Bounded Mac CPU throughput probe using synthetic data, never a game-training claim."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import numpy as np
import torch
from head import TargetHead

HERE=Path(__file__).resolve().parent
torch.set_num_threads(2)
with tempfile.TemporaryDirectory(prefix='head-throughput-',dir=HERE.parent) as tmp:
    root=Path(tmp);init=root/'init';data=root/'data';data.mkdir()
    subprocess.run([sys.executable,str(HERE/'train_head.py'),'--init','--feature-abi','f'*64,'--out',str(init)],check=True)
    ck=torch.load(init/'head.pt',weights_only=True);m=TargetHead();m.load_state_dict(ck['state'])
    n,K,P,G=35144,10,14,16;torch.manual_seed(71)
    x=torch.randn(n,160);c=torch.randn(n,K,16);f=torch.randn(n,K,4);l=torch.randn(n,K+1)
    v=torch.rand(n,K+1)>.15;v[:,0]=True;ids=torch.randint(P,(n,K+1));ref=ids[:,0]
    with torch.no_grad():
        prob,_,_=m(x,c,f,l,v,ids,ref,P);act=torch.multinomial(prob,1).squeeze(1);lp=prob.gather(1,act[:,None]).squeeze(1).log()
    game=np.empty(n,dtype=np.int64);ix=np.empty(n,dtype=np.int64);episodes=[]
    for i,rows in enumerate(np.array_split(np.arange(n),G)):
        game[rows]=i;ix[rows]=np.arange(1,len(rows)+1)
        episodes.append(dict(key=str(i),map_sha256='e'*64,status='terminated',truncated=False,all_decisions_present=True,
                             terminal_outcome=(-1 if i%2 else 1),decisions=len(rows)))
    np.savez(data/'data.npz',context=x.numpy(),camps=c.numpy(),features=f.numpy(),native_logits=l.numpy(),valid=v.numpy(),mapping=ids.numpy(),reference=ref.numpy(),action=act.numpy(),old_logp=lp.numpy(),game=game,body_id=np.zeros(n,dtype=np.int64),decision_index=ix)
    meta=dict(schema='jd-head-training-adapter-v1',architecture=ck['architecture'],feature_abi_sha256=ck['feature_abi'],policy_weights_sha256=ck['weights_sha256'],data_origin='synthetic-test',executor_sha256='a'*64,collector_source_sha256='b'*64,wasm_sha256='c'*64,engine_sha256='d'*64,data_sha256=hashlib.sha256((data/'data.npz').read_bytes()).hexdigest(),camp_count=K,physical_count=P,episodes=episodes)
    (data/'manifest.json').write_text(json.dumps(meta));maps=root/'maps.json';maps.write_text(json.dumps(dict(maps=[dict(sha256='e'*64,split='training')])))
    args=['/usr/bin/time','-l',sys.executable,str(HERE/'train_head.py'),'--checkpoint',str(init/'head.pt'),'--data',str(data),'--map-manifest',str(maps),'--synthetic-test','--out',str(root/'updated'),'--threads','2']
    start=time.perf_counter();r=subprocess.run(args,capture_output=True,text=True);wall=time.perf_counter()-start
    if r.returncode:raise RuntimeError(r.stdout+r.stderr)
    report=json.loads((root/'updated/report.json').read_text());rss=re.search(r'(\d+)\s+maximum resident set size',r.stderr)
    result=dict(scope='Synthetic Mac CPU learner throughput only; not simulator/game collection or playing strength',device='MacBook M2 8GB CPU,2torch threads',torch=torch.__version__,decisions=n,games=G,camps=K,parameters=11826,requested_epochs=2,accepted_epochs=report['accepted_updates'],wall_seconds_including_python_start_load_validation_update_export=wall,peak_child_rss_mib=int(rss.group(1))/1048576 if rss else None,npz_bytes=(data/'data.npz').stat().st_size,final_kl=report['final_exported_float32']['full_old_to_new_kl'],notes=['Synthetic random inputs and outcomes; actual rollout distributions can change costs','Temporary payload removed after probe','CPU only; no Kaggle/GPU session or quota consumed','Does not measure C++ runtime fuel or prove collection throughput'])
    (HERE/'learner_profile_result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
