import os,sys,json
os.environ['NN_DEPLOY_PREP']='1'
from project import ROOT,save
from setup_training import setup
setup();sys.path.insert(0,str(ROOT/'training/agent2/lab'))
import numpy as np,torch
from nn_model import student,Prep,load
from policy_math import live_logits,blend
from policy_rows import stdout,parse_rows
from quant_policy import validate

if __name__=='__main__':
    torch.set_num_threads(2);net=load(student(Prep()),str(ROOT/'training/initial-v113.pt'),'cuda').to('cuda').eval()
    results=[]
    for game in json.loads((ROOT/'panels/rl-recorder-qa-v1/results.json').read_text()):
        txt=stdout(game['replay_bundle'],game['side']);rows=parse_rows(txt)
        me={r['me'] for r in rows};native=json.loads(open(game['summary']).read())
        allowed={c['id'] for c in native['roster']['champions'] if c['team']=='team'+game['side'].upper()}
        assert me<=allowed,(me,allowed)
        errors=[];fd=[]
        for start in range(0,len(rows),4096):
            rs=rows[start:start+4096];x=torch.as_tensor(np.stack([r['x'] for r in rs]),device='cuda');bs=torch.as_tensor([r['bs'] for r in rs],device='cuda')
            q=torch.as_tensor(np.stack([r['q'] for r in rs]),device='cuda');a=torch.as_tensor([r['ta'] for r in rs],device='cuda');lp=torch.as_tensor([r['tlp'] for r in rs],device='cuda')
            with torch.no_grad():
                errors.extend(validate(q,a,lp,.4).cpu().tolist())
                lg=blend(live_logits(net,x,x),bs)
                fd.extend((lg.div(.4).log_softmax(-1).gather(1,a[:,None]).squeeze(1)-lp).abs().cpu().tolist())
        result={'map':game['map'],'side':game['side'],'rows':len(rows),'bodies':sorted(me),'publications':len({(r['me'],r['zid']) for r in rows}),'native_lp_max':max(errors),'float_lp_p50':float(np.median(fd)),'float_lp_p90':float(np.quantile(fd,.9)),'float_lp_max':max(fd),'fix_spawn_events':txt.count('FIXSPAWN '),'fix_respawn_events':txt.count('FIXRESPAWN ')}
        results.append(result);print(json.dumps(result),flush=True)
    save(ROOT/'training/record-qa.json',results)
    assert all(r['float_lp_p50']<=.05 and r['float_lp_p90']<=.25 for r in results),'Input/model mismatch must be resolved before training'
