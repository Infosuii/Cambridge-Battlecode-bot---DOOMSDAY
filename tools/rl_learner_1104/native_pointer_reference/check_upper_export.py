from pathlib import Path
import json,tempfile,torch
from qat_upper import NativeUpper
from export_query import values
from export_upper import export
p=Path(__file__).parent;r=p.parent;source=r/'native-upper-actor/bots/submission/src/nn_weights.h';s=source.read_text()
names=['kT_W1_TQ','kT_b1Q','kP_target_qW_TQ','kP_target_qbQ','kP_target_kWQ','kP_target_kbQ','kP_target_EQ'];m=NativeUpper(*[values(s,n,True) for n in names])
with tempfile.TemporaryDirectory() as folder:
 dest=Path(folder)/'noop.h';noop=export(source,m,dest);assert noop['noop'] and dest.read_bytes()==source.read_bytes()
# Diagnostic perturbations of BOTH existing layers; not an RL update.
with torch.no_grad():m.trunk_w[0,0]+=8/16384;m.trunk_bias+=1/256;m.query_w[0,0]+=8/16384;m.query_bias+=1/128
changed=p/'upper_diagnostic_header.h';rep=export(source,m,changed)
assert set(rep['only_changed_arrays'])=={'kT_W1','kT_b1','kT_W1_T','kT_W1_TQ','kT_b1Q','kP_target_qW','kP_target_qb','kP_target_qW_T','kP_target_qW_TQ','kP_target_qbQ'}
report=dict(scope='No-op byte preservation and diagnostic upper/query export; not trained',noop=noop,changed=rep)
(r.parent.parent/'outputs/rl-execution/NATIVE_UPPER_EXPORT_CHECK.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
