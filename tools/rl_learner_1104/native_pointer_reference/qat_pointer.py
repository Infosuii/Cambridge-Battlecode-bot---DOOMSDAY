"""Frozen-trunk native pointer with exact Q16 forward and straight-through gradients.
No game-data adapter, PPO loop or strength claim. Header-array integers define
initial master weights; exporting must update BOTH float and integer native arrays.
"""
import torch
from torch import nn

def ste_round(x):
    return x+(x.round()-x).detach()

def dense_q15(T,b,x):
    # float64 preserves integer multiplication exactly across the int16 domain.
    acc=b.to(torch.float64)[None,:].expand(len(x),-1)
    for i in range(x.shape[-1]):
        raw=(x[:,i,None].to(torch.float64)*T[i].to(torch.float64)+16384)/32768
        rounded=raw+(raw.floor()-raw).detach()
        prod=rounded.clamp(-32768,32767)
        acc=(acc+prod).clamp(-32768,32767)
    return acc

class NativePointer(nn.Module):
    def __init__(self,query_w_input_major,query_bias,key_w,key_bias,far_embedding):
        super().__init__()
        # Masters use original real-valued weight/bias scales, initialized from
        # compiled integers. This is a NEW optimizer start, not restored Adam.
        self.query_w=nn.Parameter(torch.as_tensor(query_w_input_major,dtype=torch.float64).reshape(64,16)/16384)
        self.query_bias=nn.Parameter(torch.as_tensor(query_bias,dtype=torch.float64)/128)
        self.register_buffer('key_w',torch.as_tensor(key_w,dtype=torch.float64).reshape(16,16))
        self.register_buffer('key_bias',torch.as_tensor(key_bias,dtype=torch.float64))
        self.register_buffer('far_embedding',torch.as_tensor(far_embedding,dtype=torch.float64))

    def forward(self,h1_raw,camps_raw,present):
        if h1_raw.ndim!=2 or h1_raw.shape[1]!=64 or camps_raw.shape!=(len(h1_raw),10,16) or present.shape!=(len(h1_raw),10):
            raise ValueError('consumed state shapes')
        if not torch.isfinite(h1_raw).all() or not torch.isfinite(camps_raw).all():raise ValueError('nonfinite state')
        W=ste_round(self.query_w*16384).clamp(-32768,32767)
        b=ste_round(self.query_bias*128).clamp(-32768,32767)
        q=dense_q15(W,b,h1_raw)
        r=dense_q15(self.key_w,torch.zeros(16,dtype=torch.float64,device=q.device),q)
        c0=(q*self.key_bias).sum(-1)
        logits=(camps_raw.to(torch.float64)*r[:,None,:]).sum(-1)+c0[:,None]
        far=(r*self.far_embedding).sum(-1)+c0
        # C++ converts int32 dot to float32 then multiplies by exact 2^-18.
        # Current admitted fixtures have no int32 dot overflow; reject overflow
        # instead of silently claiming an exact wraparound derivative.
        if (logits.abs()>2147483647).any() or (far.abs()>2147483647).any():raise ValueError('int32 range unsupported')
        logits=torch.cat((logits,far[:,None]),-1).to(torch.float32)*(1/262144)
        valid=torch.cat((present.bool(),torch.ones(len(present),1,dtype=torch.bool,device=present.device)),-1)
        logits=logits.masked_fill(~valid,-1e9)
        return logits,dict(query_raw=q,folded_pointer_raw=r,bias_dot=c0)
