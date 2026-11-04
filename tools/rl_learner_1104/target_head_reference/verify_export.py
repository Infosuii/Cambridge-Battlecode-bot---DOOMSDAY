"""Compare generated export probe stdout to its paired PyTorch expectations."""
import json
import math
import sys
from pathlib import Path

root=Path(__file__).resolve().parent
expected=json.loads((root/'export_expected.json').read_text())
lines=Path(sys.argv[1]).read_text().splitlines()
rows={}
for line in lines:
    if line.startswith('EXPORT '):
        parts=line.split();i=int(parts[1])
        if i in rows:raise ValueError('duplicate fixture')
        rows[i]=(float(parts[2]),list(map(float,parts[3:])))
assert set(rows)==set(range(len(expected['alpha'])))
pe=ae=le=0.
for i,(alpha,prob) in rows.items():
    target=expected['probabilities'][i]
    assert len(prob)==len(target) and all(math.isfinite(z) and z>=0 for z in prob)
    assert abs(sum(prob)-1)<1e-12
    ae=max(ae,abs(alpha-expected['alpha'][i]))
    for z,t in zip(prob,target):
        assert (z>0)==(t>0)
        pe=max(pe,abs(z-t))
        if z>0:le=max(le,abs(math.log(z)-math.log(t)))
assert pe<2e-5 and ae<2e-5 and le<2e-4,(pe,ae,le)
print(json.dumps(dict(cases=len(rows),max_probability_error=pe,max_alpha_error=ae,max_logp_error=le)))
