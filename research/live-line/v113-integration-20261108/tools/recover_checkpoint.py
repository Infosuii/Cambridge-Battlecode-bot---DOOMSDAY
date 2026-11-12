"""Recover the exact supplied model parameters from its generated C++ weights."""
from pathlib import Path
import sys,re,json,hashlib,subprocess,shutil
import numpy as np
import torch
from project import ROOT,BASE,ARENA,save,sha
LAB=ROOT/'training/agent2/lab'
def arrays(path):
    text=Path(path).read_text(encoding='utf-8');result={}
    for name,body in re.findall(r'inline constexpr float\s+(\w+)\[\]\s*=\s*\{([^}]*)\}',text):
        v=np.fromstring(body.replace('f',''),sep=',',dtype=np.float32)
        assert len(v) and np.isfinite(v).all(),name;result[name]=v
    return result
def main():
    LAB.mkdir(parents=True,exist_ok=True)
    for name in ('nn_model.py','nn_export.py','quant_policy.py'):
        target=LAB/name;original=BASE/'training/agent2/lab'/name
        if not target.exists():shutil.copy2(original,target)
        assert sha(target)==sha(original)
    sys.path.insert(0,str(LAB));from nn_model import Prep,student
    model=student(Prep());weights=arrays(ARENA/'bots/b113/src/nn_weights.h');state=model.state_dict();mapping={}
    for k,v in state.items():
        parts=k.split('.')
        if parts[0]=='prep':name='k'+parts[1][-1]+'_'+parts[1][:-2]
        elif parts[0]=='enc':name='k'+parts[1]+'_'+('W' if parts[3]=='weight' else 'b')+str(int(parts[2])//2)
        elif parts[0]=='trunk':name='kT_'+('W' if parts[2]=='weight' else 'b')+str(int(parts[1])//2)
        elif parts[0]=='lin':name='kH_'+parts[1]+'_'+('W' if parts[2]=='weight' else 'b')
        elif parts[0] in ('q','k'):name='kP_'+parts[1]+'_'+parts[0]+('W' if parts[2]=='weight' else 'b')
        elif parts[0]=='extra':name='kP_'+parts[1]+'_E'
        else:raise ValueError('Unmapped model state '+k)
        assert name in weights and weights[name].size==v.numel(),(k,name,v.shape)
        state[k]=torch.from_numpy(weights[name].copy()).reshape(v.shape);mapping[k]=name
    model.load_state_dict(state,strict=True)
    folder=ROOT/'training';checkpoint=folder/'initial-v113.pt';torch.save(model.state_dict(),checkpoint)
    header=folder/'initial-v113-export.h'
    p=subprocess.run([sys.executable,'-P',str(LAB/'nn_export.py'),str(checkpoint),'student',str(header)],capture_output=True,encoding='utf-8',errors='replace',timeout=90)
    assert p.returncode==0,p.stderr[-1000:]
    regenerated=arrays(header);assert set(regenerated)==set(weights)
    differences={n:int(np.count_nonzero(weights[n].view(np.uint32)!=regenerated[n].view(np.uint32))) for n in weights if not np.array_equal(weights[n].view(np.uint32),regenerated[n].view(np.uint32))}
    assert not differences,('Recovered export differs from supplied deployed weights',differences)
    save(folder/'checkpoint-recovery.json',{'source_header_sha256':sha(ARENA/'bots/b113/src/nn_weights.h'),'checkpoint_sha256':sha(checkpoint),'export_sha256':sha(header),'mapped_tensors':mapping,'all_exported_float_arrays_bit_identical':True,'exported_arrays':len(weights),'cuda_available':torch.cuda.is_available(),'gpu':torch.cuda.get_device_name() if torch.cuda.is_available() else None})
    print(json.dumps({'recovered_tensors':len(mapping),'verified_arrays':len(weights),'checkpoint':str(checkpoint),'cuda':torch.cuda.is_available()},indent=2))
if __name__=='__main__':main()
