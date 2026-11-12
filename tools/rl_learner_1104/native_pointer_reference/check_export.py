from pathlib import Path
import json,numpy as np,torch
from qat_pointer import NativePointer
from export_query import values,export
r=Path(__file__).resolve().parents[1];p=Path(__file__).parent;header=r/'native-pointer-audit/bots/submission/src/nn_weights.h';s=header.read_text()
m=NativePointer(*[values(s,n,True) for n in ['kP_target_qW_TQ','kP_target_qbQ','kP_target_kWQ','kP_target_kbQ','kP_target_EQ']])
noop=export(header,m,p/'noop_native_header.h');assert noop['noop'] and noop['source_sha256']==noop['export_sha256']
with torch.no_grad():
 m.query_bias.add_(torch.tensor([2,-2,3,-3,1,-1,2,-2,3,-3,1,-1,2,-2,3,-3],dtype=torch.float64)/128)
 m.query_w[0,0].add_(1/16384)
changed=export(header,m,p/'diagnostic_native_header.h');assert not changed['noop']
s2=(p/'diagnostic_native_header.h').read_text();m2=NativePointer(*[values(s2,n,True) for n in ['kP_target_qW_TQ','kP_target_qbQ','kP_target_kWQ','kP_target_kbQ','kP_target_EQ']])
with np.load(p/'consumed_inputs.npz') as z:d={k:torch.from_numpy(z[k]) for k in z.files}
a,aux=m(d['h1'],d['camps'],d['present']);b,_=m2(d['h1'],d['camps'],d['present']);assert torch.equal(a,b)
assert not torch.equal(aux['query_raw'].long(),d['q'])
rep=dict(scope='Native target-query header export check on NONTRAINED diagnostic perturbation, no strength claim',noop=noop,changed=changed,
 roundtrip_target_logits_bit_exact=True,diagnostic_query_differs_from_original=True)
(r.parent.parent/'outputs/rl-execution/NATIVE_QUERY_EXPORT_CHECK.json').write_text(json.dumps(rep,indent=2)+'\n');print(json.dumps(rep,indent=2))
