"""QAT forward parity and nonzero gradient on real diagnostic states; no training."""
from pathlib import Path
import json,re,numpy as np,torch
from qat_pointer import NativePointer
root=Path(__file__).resolve().parents[1];p=Path(__file__).parent
header=(p/'original_native_header.h' if (p/'original_native_header.h').exists() else root/'native-pointer-audit/bots/submission/src/nn_weights.h').read_text()
def arr(name):return np.array([int(x) for x in re.search(r'inline constexpr short '+name+r'\[\] = \{([^}]+)\}',header).group(1).split(',')],np.int64)
m=NativePointer(*[arr(n) for n in ['kP_target_qW_TQ','kP_target_qbQ','kP_target_kWQ','kP_target_kbQ','kP_target_EQ']])
with np.load(p/'consumed_inputs.npz') as z:d={k:torch.from_numpy(z[k]) for k in z.files}
logits,aux=m(d['h1'],d['camps'],d['present'])
assert torch.equal(logits,d['logits'])
for name,key in [('query_raw','q'),('folded_pointer_raw','r'),('bias_dot','c0')]:assert torch.equal(aux[name].detach().long(),d[key])
# Diagnostic gradient only: choose far target, not a fabricated game action.
loss=-logits.log_softmax(-1)[:,-1].mean();loss.backward()
assert all(torch.isfinite(p.grad).all() and p.grad.abs().sum()>0 for p in m.parameters())
report=dict(scope='Exact live consumed-input forward replay plus diagnostic STE gradient; NO RL update or playing-strength claim',
 rows=len(logits),target_float32_logits_bit_exact=True,query_folded_pointer_bias_bit_exact=True,
 trainable_parameters=sum(p.numel() for p in m.parameters()),
 gradient_norm=float(torch.sqrt(sum((p.grad*p.grad).sum() for p in m.parameters()))),
 limitations=['STE is a surrogate gradient, not mathematical derivative through integer rounding.',
 'Initial master weights reconstructed from quantized header; optimizer state not restored.',
 'Integer-overflow cases explicitly unsupported/refused.',
 'Native header export and fresh stochastic complete-game collector still required before training.'])
(root.parent.parent/'outputs/rl-execution/NATIVE_POINTER_QAT_CHECK.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
