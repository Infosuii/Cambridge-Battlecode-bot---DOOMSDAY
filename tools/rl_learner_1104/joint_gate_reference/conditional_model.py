"""Learner model for R1's proposed six-input conditional actor (#62).

Feature floats are CONSUMED runtime values, never recomputed in the learner.
Header format/feature-ABI hash must still be pinned against actual runtime.
"""
import sys
from pathlib import Path
import torch
from torch import nn
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'target_head_reference'))
from head import TargetHead

class ConditionalActor(nn.Module):
    def __init__(self, head_state, temperature=1., initial_alpha=.02):
        super().__init__()
        if temperature <= 0 or not 0 < initial_alpha < 1:
            raise ValueError('invalid policy configuration')
        self.head=TargetHead();self.head.load_state_dict(head_state,strict=True)
        # Retain old layer for exact header round trips; conditional runtime never uses it.
        self.head.gate.requires_grad_(False)
        self.cheap_gate=nn.Linear(6,1)
        nn.init.zeros_(self.cheap_gate.weight)
        nn.init.constant_(self.cheap_gate.bias,torch.logit(torch.tensor(initial_alpha)).item())
        self.temperature=float(temperature)

    def gate_logits(self, consumed_gate_inputs):
        if consumed_gate_inputs.ndim!=2 or consumed_gate_inputs.shape[1]!=6:
            raise ValueError('gate feature shape')
        return self.cheap_gate(consumed_gate_inputs).squeeze(-1)

    def conditional_distribution(self, context,camps,features,native_logits,valid,mapping,physical_count):
        # Called on INVOKED rows only. No old mixture or expensive old gate.
        n,K=camps.shape[:2]
        if context.shape!=(n,160) or features.shape!=(n,K,4) or native_logits.shape!=(n,K+1):
            raise ValueError('conditional input shape')
        if valid.shape!=(n,K+1) or mapping.shape!=valid.shape or valid.dtype!=torch.bool:
            raise ValueError('conditional mask/mapping shape')
        if not valid.any(-1).all() or ((mapping[valid]<0)|(mapping[valid]>=physical_count)).any():
            raise ValueError('conditional support')
        h=self.head.context(context).relu(); query=self.head.query(h)
        keys=self.head.key(camps)+self.head.features(features)
        residual=(keys*query[:,None]).sum(-1)/4
        scores=(native_logits+torch.cat((residual,self.head.far(h)),-1))/self.temperature
        slot=scores.masked_fill(~valid,-torch.inf).softmax(-1)
        physical=slot.new_zeros(n,physical_count)
        return physical.scatter_add_(1,mapping.clamp(0,physical_count-1),slot)

    def chosen_joint_logp(self,gate_inputs,invoke,conditional,physical_count):
        from joint_gate import joint_logp
        logits=self.gate_logits(gate_inputs)
        if len(conditional['action'])!=int(invoke.sum()):
            raise ValueError('invoke rows differ from conditional rows')
        if invoke.any():
            p=self.conditional_distribution(*[conditional[k] for k in ('context','camps','features','native_logits','valid','mapping')],physical_count)
            chosen=p.gather(1,conditional['action'][:,None]).squeeze(1)
            if not (chosen>0).all():raise ValueError('unsupported chosen action')
            qlogp=chosen.log()
        else:qlogp=logits.new_empty(0)
        return joint_logp(logits,invoke,None,qlogp)
