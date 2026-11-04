from pathlib import Path
import torch,numpy as np,json,time,copy
from qat_dense_vectorized import dense_q15 as fast
from qat_pointer import dense_q15 as reference
import qat_pointer,qat_upper
from qat_upper import NativeUpper
from export_query import values
torch.set_num_threads(2);torch.manual_seed(110630);p=Path(__file__).parent
# Both ordinary and deliberately saturating recurrences, with input/weight/bias gradients.
checks=[]
for saturated in [False,True]:
 x=(torch.randint(-32768,32768,(17,64)) if saturated else torch.randint(0,2000,(17,64))).double().requires_grad_();w=(torch.randint(-32768,32768,(64,64)) if saturated else torch.randint(-3000,3000,(64,64))).double().requires_grad_();b=(torch.randint(-32768,32768,(64,)) if saturated else torch.randint(-500,500,(64,))).double().requires_grad_()
 a=reference(w,b,x);z=fast(w,b,x);assert torch.equal(a,z)
 target=torch.randn_like(a);ga=torch.autograd.grad((a*target).sum(),(x,w,b),retain_graph=True);gb=torch.autograd.grad((z*target).sum(),(x,w,b));err=max(float((u-v).abs().max()) for u,v in zip(ga,gb));assert err<1e-10;checks.append(dict(saturated=saturated,forward_exact=True,max_gradient_error=err))
header=(p/'upper_u0_header.h').read_text();names=['kT_W1_TQ','kT_b1Q','kP_target_qW_TQ','kP_target_qbQ','kP_target_kWQ','kP_target_kbQ','kP_target_EQ'];m=NativeUpper(*[values(header,n,True) for n in names])
with np.load(p/'upper_batch01/data.npz') as z:d={k:torch.from_numpy(z[k][:512]) for k in ['h0','camps','present']}
def model_run(use_fast,grad):
 qat_pointer.dense_q15=fast if use_fast else reference;qat_upper.dense_q15=fast if use_fast else reference;m.zero_grad();out,aux=m(*[d[k] for k in ['h0','camps','present']]);loss=-out.log_softmax(-1)[:,-1].sum()
 if grad:loss.backward()
 return out.detach().clone(),{n:v.grad.detach().clone() for n,v in m.named_parameters()} if grad else {}
a,ga=model_run(False,True);b,gb=model_run(True,True);assert torch.equal(a,b);err=max(float((ga[n]-gb[n]).abs().max()) for n in ga);assert err<1e-8
results={}
for use_fast in [False,True]:
 times=[]
 for i in range(5):
  start=time.perf_counter();model_run(use_fast,True);times.append(time.perf_counter()-start)
 results['fast' if use_fast else 'reference']=float(np.median(times))
report=dict(scope='Opt-in learner-only Q15 vectorization parity and throughput; not actor/fuel/strength result',synthetic_checks=checks,actual_consumed_rows=512,actual_model_logits_bit_exact=True,max_model_gradient_error=err,median_forward_backward_seconds=results,speedup=results['reference']/results['fast'],current_paired_trial_modified=False,limitations=['Fast path proves all prefix sums remain int16; otherwise uses unchanged sequential saturated recurrence.','512-row CPUmicrobenchmark with2threads; complete training throughput and memory need separate evaluation.','Not enabled in the running pairedtrial; preserve experimental comparability.'])
(p.parents[2]/'outputs/rl-execution/QAT_DENSE_VECTORIZATION_CHECK.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
