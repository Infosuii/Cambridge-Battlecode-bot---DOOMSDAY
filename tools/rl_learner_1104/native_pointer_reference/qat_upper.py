"""Train the existing upper trunk and query from consumed h0 (Q9).

JNP2 h1 rows cannot be used: the lower network remains frozen, while h1 now
depends on trained parameters. No additional deployment layer is introduced.
"""
import torch
from torch import nn
from qat_pointer import NativePointer, dense_q15, ste_round

class NativeUpper(NativePointer):
    def __init__(self, trunk_w, trunk_bias, *pointer):
        super().__init__(*pointer)
        self.trunk_w = nn.Parameter(torch.as_tensor(trunk_w, dtype=torch.float64).reshape(64,64)/16384)
        self.trunk_bias = nn.Parameter(torch.as_tensor(trunk_bias, dtype=torch.float64)/256)

    def forward(self, h0_raw, camps_raw, present):
        if h0_raw.ndim != 2 or h0_raw.shape[1] != 64 or not torch.isfinite(h0_raw).all():
            raise ValueError('consumed h0 shape/nonfinite')
        if (h0_raw < 0).any() or (h0_raw > 32767).any():
            raise ValueError('consumed h0 is native int16 ReLU')
        W = ste_round(self.trunk_w*16384).clamp(-32768,32767)
        b = ste_round(self.trunk_bias*256).clamp(-32768,32767)
        h1 = dense_q15(W,b,h0_raw).clamp(min=0)
        logits, aux = super().forward(h1,camps_raw,present)
        aux['h1_raw'] = h1
        return logits, aux
