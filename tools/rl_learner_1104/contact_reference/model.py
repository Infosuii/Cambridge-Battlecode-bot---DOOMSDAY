"""Diagnostic exact Q15 contact head. No policy execution or RL update."""
import sys
from pathlib import Path
import torch
from torch import nn
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'native_pointer_reference'))
from qat_pointer import dense_q15,ste_round
class ContactHead(nn.Module):
 def __init__(self):
  super().__init__();self.weight=nn.Parameter(torch.tensor([[((i*71+j*97)%1025)-512 for j in range(3)] for i in range(48)],dtype=torch.float64)/16384);self.bias=nn.Parameter(torch.tensor([13,-9,7],dtype=torch.float64)/1024)
 def forward(self,x):
  if x.ndim!=2 or x.shape[1]!=48:raise ValueError('contact feature ABI')
  w=ste_round(self.weight*16384).clamp(-32768,32767);b=ste_round(self.bias*1024).clamp(-32768,32767);raw=dense_q15(w,b,x)
  return raw.to(torch.float32)/1024,raw
