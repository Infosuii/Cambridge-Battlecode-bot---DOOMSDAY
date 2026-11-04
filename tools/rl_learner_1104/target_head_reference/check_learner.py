"""Integration checks on explicitly SYNTHETIC bundles; never playing-strength evidence."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import numpy as np
import torch
from head import TargetHead
from train_head import weight_hash,load_data

torch.set_num_threads(1)
HERE=Path(__file__).resolve().parent

def run(args,success=True):
    r=subprocess.run([sys.executable,str(HERE/'train_head.py'),*map(str,args)],capture_output=True,text=True)
    if (r.returncode==0)!=success:raise AssertionError(r.stdout+r.stderr)
    return r

def dataset(path,checkpoint,allwin=False):
    path.mkdir();ck=torch.load(checkpoint,weights_only=True);m=TargetHead();m.load_state_dict(ck['state'])
    torch.manual_seed(17);n=96;K=4;P=5
    x=torch.randn(n,160);c=torch.randn(n,K,16);f=torch.randn(n,K,4);l=torch.randn(n,K+1)
    v=torch.rand(n,K+1)>.2;v[:,0]=True
    ids=torch.randint(P,(n,K+1));ref=ids[:,0]
    with torch.no_grad():
        p,_,_=m(x,c,f,l,v,ids,ref,P);act=torch.multinomial(p,1).squeeze(1);lp=p.gather(1,act[:,None]).squeeze(1).log()
    d=dict(context=x.numpy(),camps=c.numpy(),features=f.numpy(),native_logits=l.numpy(),valid=v.numpy(),
           mapping=ids.numpy(),reference=ref.numpy(),action=act.numpy(),old_logp=lp.numpy(),game=np.repeat(np.arange(6),16),
           body_id=np.tile(np.repeat([0,1],8),6),decision_index=np.tile(np.arange(1,9),12))
    np.savez(path/'data.npz',**d)
    meta=dict(schema='jd-head-training-adapter-v1',architecture=ck['architecture'],feature_abi_sha256=ck['feature_abi'],
              policy_weights_sha256=ck['weights_sha256'],data_origin='synthetic-test',executor_sha256='a'*64,
              collector_source_sha256='b'*64,wasm_sha256='c'*64,engine_sha256='d'*64,
              data_sha256=hashlib.sha256((path/'data.npz').read_bytes()).hexdigest(),camp_count=K,physical_count=P,
              episodes=[dict(key=str(i),map_sha256='e'*64,status='terminated',truncated=False,all_decisions_present=True,
                             terminal_outcome=1 if allwin or i%2 else -1,decisions=16) for i in range(6)])
    meta['episodes'].append(dict(key='zero-decisions',map_sha256='e'*64,status='terminated',truncated=False,all_decisions_present=True,terminal_outcome=-1,decisions=0))
    (path/'manifest.json').write_text(json.dumps(meta));return meta

with tempfile.TemporaryDirectory(prefix='jd-head-check-') as tmp:
    root=Path(tmp);maps=root/'maps.json';maps.write_text(json.dumps(dict(maps=[dict(sha256='e'*64,split='training')])))
    run(['--init','--feature-abi','f'*64,'--out',root/'init'])
    initial=root/'init/head.pt';dataset(root/'batch',initial,allwin=True)
    base=['--checkpoint',initial,'--data',root/'batch','--map-manifest',maps,'--threads',1]
    run([*base,'--out',root/'wrong-origin'],False)
    run([*base,'--synthetic-test','--out',root/'update'])
    assert json.loads((root/'update/report.json').read_text())['games']==7
    trained=root/'update/head.pt';ck=torch.load(trained,weights_only=True)
    assert ck['updates']==2 and ck['weights_sha256']!=torch.load(initial,weights_only=True)['weights_sha256']
    assert ck['optimizer'] is not None
    dataset(root/'fresh',trained)
    run(['--checkpoint',trained,'--data',root/'fresh','--map-manifest',maps,'--synthetic-test','--threads',1,'--out',root/'resume'])
    assert torch.load(root/'resume/head.pt',weights_only=True)['updates']>=3
    run(['--checkpoint',initial,'--data',root/'fresh','--map-manifest',maps,'--synthetic-test','--out',root/'stale'],False)
    run([*base,'--synthetic-test','--max-kl',0,'--out',root/'rollback'])
    rollback=torch.load(root/'rollback/head.pt',weights_only=True)
    assert rollback['weights_sha256']==torch.load(initial,weights_only=True)['weights_sha256']
    meta=json.loads((root/'batch/manifest.json').read_text());meta['episodes'][0]['truncated']=True
    (root/'batch/manifest.json').write_text(json.dumps(meta))
    run([*base,'--synthetic-test','--out',root/'truncated'],False)
    report=dict(scope='SYNTHETIC learner integration checks only',parameters=11826,
                checks=['initial header/checkpoint','all-win decision rows can update with fixed-zero baseline','zero-decision completed game retained in denominator',
                        'optimizer continuation on fresh matching-policy data','stale policy rejected',
                        'synthetic origin rejected in normal mode','post-step KL rollback preserves checkpoint',
                        'truncated complete-game claim rejected'],
                first_update=json.loads((root/'update/report.json').read_text())['final_exported_float32'])
    (HERE/'learner_check_result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
