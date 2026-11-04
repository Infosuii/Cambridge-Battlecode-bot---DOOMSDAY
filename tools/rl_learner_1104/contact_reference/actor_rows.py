"""Strict generic contact producer reader and exact Q15 likelihood validation."""
from pathlib import Path
import math
import struct
import torch


def read_rows(path):
    rows, completed, last = [], {}, {}
    for line in Path(path).read_bytes().replace(b'\0', b'').splitlines():
        t = line.decode().split()
        if not t:
            continue
        if t[0] == 'JCA1':
            if len(t) != 14:
                raise ValueError('truncated contact record')
            logical, engine, body, seq, win, danger, action = map(int, t[1:8])
            p = list(map(float, t[8:11]))
            mask = t[11]
            x, z = struct.unpack('<48h', bytes.fromhex(t[12])), struct.unpack('<8h', bytes.fromhex(t[13]))
            if (logical != engine or seq != last.get(body, 0) + 1 or len(mask) != 3
                    or set(mask) - {'0','1'} or mask[0] != '1'
                    or action not in range(3) or mask[action] != '1'
                    or win not in (0,1) or danger not in (0,1)
                    or x[25] != 2048*win or x[26] != 2048*danger or any(z[3:])):
                raise ValueError('invalid contact clock, sequence, mask or feature ABI')
            if any(not math.isfinite(v) or v < 0 for v in p) or abs(sum(p)-1) > 1e-12:
                raise ValueError('invalid probabilities')
            if any(p[j] != 0 for j in range(3) if mask[j] == '0') or p[action] <= 0:
                raise ValueError('invalid probability support')
            last[body] = seq
            rows.append(dict(round=engine, body=body, seq=seq, action=action,
                             p=p, valid=[v=='1' for v in mask], x=x, z=z[:3]))
        elif t[0] == 'JCE1':
            if len(t) != 6:
                raise ValueError('truncated completion')
            body, seq, rnd, fresh, fuel = map(int, t[1:])
            key = body, seq
            if key in completed or fresh != 1:
                raise ValueError('duplicate or stale completion')
            completed[key] = rnd, fuel
        else:
            raise ValueError('unexpected stdout record '+t[0])
    if not rows or len(rows) != len(completed):
        raise ValueError('empty or incomplete contact episode')
    for row in rows:
        if completed.get((row['body'],row['seq']), (None,))[0] != row['round']:
            raise ValueError('missing or delayed completed command')
    return rows


def audit_model(rows, model):
    x = torch.tensor([r['x'] for r in rows], dtype=torch.float64)
    logits, raw = model(x)
    if not torch.equal(raw.detach().long(), torch.tensor([r['z'] for r in rows])):
        raise ValueError('native Q15 score mismatch')
    scores = logits.double()
    scores = scores + torch.tensor([2.,0.,0.], dtype=torch.float64)
    valid = torch.tensor([r['valid'] for r in rows], dtype=torch.bool)
    logp = scores.masked_fill(~valid, -torch.inf).log_softmax(-1)
    actual = logp.exp().detach()
    expected = torch.tensor([r['p'] for r in rows], dtype=torch.float64)
    error = (actual-expected).abs().max().item()
    if error > 1e-12:
        raise ValueError(f'likelihood mismatch {error}')
    return logp, error
