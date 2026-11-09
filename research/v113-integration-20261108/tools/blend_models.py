"""Bounded native-export damping after two correctly collected PPO attempts."""
import os,sys,json,time,subprocess,shutil
from pathlib import Path
from project import ROOT,save,sha,check_stop
from prepare_campaign import prepare
from local_panel import run
WD=ROOT/'training/q15-model-selection';WD.mkdir(exist_ok=True)

def main():
    complete=ROOT/'training/corrected-q15/complete.json'
    while not complete.exists():check_stop();time.sleep(2)
    out=WD/'complete.json'
    if out.exists():return json.loads(out.read_text())
    os.environ.update(TRAIN_SOURCE='q15',TRAIN_CAMPAIGN_NAME='corrected-q15',TRAIN_PREFIX='q')
    from train_campaign import actor,LAB
    import torch
    p=prepare();base=ROOT/'training/corrected-q15'
    reports=[json.loads((base/f'eval_{i}.json').read_text()) for i in (2,4)]
    trained=max(reports,key=lambda r:r['score']);existing=json.loads(complete.read_text())['selected']
    original=torch.load(p['initial_checkpoint'],map_location='cpu',weights_only=True)
    current=torch.load(base/f'student_{trained["iteration"]}.pt',map_location='cpu',weights_only=True)
    names=[]
    plan={'trained_checkpoint':trained,'incumbent':existing,'alphas':[.125,.25,.5],'reason':'Valid PPO batches did not improve the native release. Test smaller native parameter changes to preserve effective old decisions while retaining some of the learned update; this is a bounded repair attempt, not evidence that quantization caused the regressions.','maps_role':'development only'}
    save(WD/'plan.json',plan)
    for alpha in plan['alphas']:
        name=f'mx{round(alpha*1000):03}';names.append(name)
        mixed={}
        for key,value in original.items():
            if value.is_floating_point():mixed[key]=value*(1-alpha)+current[key]*alpha
            else:assert torch.equal(value,current[key]);mixed[key]=value
        pt=WD/(name+'.pt');header=WD/(name+'.h');torch.save(mixed,pt)
        subprocess.run([sys.executable,'-P',str(LAB/'nn_export.py'),str(pt),'student',str(header)],check=True,capture_output=True)
        actor(name,header)
    rows=run('native-weight-damping',names,list(map(Path,p['maps']['dev'])),p['styles'],12)
    assert not any(r['faults'] or r['opponent_faults'] for r in rows)
    scores=[]
    for name in names:
        rs=[r for r in rows if r['candidate']==name]
        by={o:sum(r['score'] for r in rs if r['opponent']==o)/sum(r['opponent']==o for r in rs) for o in p['styles']}
        score=sum(r['score'] for r in rs)/len(rs)
        admissible=by['b111']>=existing['opponents']['b111']-1/48 and min(by[o]-existing['opponents'][o] for o in by)>=-.10
        scores.append({'actor':name,'score':score,'opponents':by,'games':len(rs),'fuel':sum(r['fuel'] for r in rs),'admissible':admissible,'alpha':int(name[2:])/1000})
    winner=max([existing]+[s for s in scores if s['admissible']],key=lambda r:r['score'])
    result={'selected':winner,'original_training_selection':existing,'damping_candidates':scores,'final_maps_used':False,'classification':'Native damping was tested; unchanged weights remain eligible if none improves the actual released bot.'}
    save(out,result);print(json.dumps(result,indent=2),flush=True);return result
if __name__=='__main__':main()
