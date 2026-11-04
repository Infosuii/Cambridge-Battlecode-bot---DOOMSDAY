"""Export all147 contact parameters to the padded Q15 native header."""
from pathlib import Path
import re
import torch


def export(model, path):
    w = torch.round(model.weight.detach()*16384).clamp(-32768,32767).long()
    b = torch.round(model.bias.detach()*1024).clamp(-32768,32767).long()
    if w.shape != (48,3) or b.shape != (3,):
        raise ValueError('contact parameter ABI')
    if not torch.isfinite(model.weight).all() or not torch.isfinite(model.bias).all():
        raise ValueError('nonfinite master weights')
    padded = torch.zeros(48,8,dtype=torch.long)
    padded[:,:3] = w
    bias = b.tolist()+[0]*5
    p = Path(path)
    s = p.read_text()
    s, n = re.subn(r'inline constexpr std::array<std::int16_t,48\*8> W\{[^}]*\};',
                  'inline constexpr std::array<std::int16_t,48*8> W{'+','.join(map(str,padded.flatten().tolist()))+'};',s)
    if n != 1:
        raise ValueError('weight declaration missing/ambiguous')
    s, n = re.subn(r'inline constexpr std::int16_t bias\[8\]=\{[^}]*\};',
                  'inline constexpr std::int16_t bias[8]={'+','.join(map(str,bias))+'};',s)
    if n != 1:
        raise ValueError('bias declaration missing/ambiguous')
    p.write_text(s)
    return dict(weight_q14=w.tolist(),bias_q10=b.tolist())
