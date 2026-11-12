"""Add L006 fitted rows using recorded runtime keys, preserving untouched J022 rows."""
import argparse, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser()
ap.add_argument('--fp',required=True)
ap.add_argument('--output',default='bots/x3/src/x1_mapfit.h')
ap.add_argument('--min-gain',type=float,default=0.05)
ap.add_argument('--state-dir',default='research/x3/es')
a=ap.parse_args()
fp=json.loads(Path(a.fp).read_text())
source=(ROOT/'bots/x3/src/x1_mapfit.h').read_text()
head,sep,body=source.partition('inline constexpr Row kRows[] = ')
assert sep
old={}
for line in body.splitlines():
    m=re.search(r'// ([^: ]+):',line)
    if m:old[m[1]]=line
rows=dict(old)
for f in sorted((ROOT/a.state_dir).glob('mapfit-*.json')):
    st=json.loads(f.read_text());name=f.stem[len('mapfit-'):]
    if not st.get('iters'):continue
    assert st['args']['opps']=='v92,v86h,x1bru,x3inv',f'wrong opponents: {f}'
    start=st['iters'][0]['mean_fit']/st['iters'][0]['games']
    best=st['best']
    if best['iter']<=0 or best['fit']-start<a.min_gain:
        print(f'{name}: preserve existing/default, gain {best["fit"]-start:.6f}')
        continue
    keys=[tuple(fp[f'{name}-{side}'][:4]) for side in ('A','B')]
    assert keys[0]==keys[1],f'asymmetric runtime key: {name}'
    w,h,groups,gems=keys[0]
    assert len(best['kd'])==24 and len(st['args']['knobs'].split(','))==24
    d=', '.join(f'{v:.4f}f' for v in best['kd'])
    rows[name]=f'    {{{w}, {h}, {groups}, {gems}u, {{{d}}}}}, // {name}: {start:.3f} -> {best["fit"]:.3f}'
    print(f'{name}: runtime key {keys[0]}, gain {best["fit"]-start:.6f}')
seen={}
for name,line in rows.items():
    m=re.search(r'\{(\d+), (\d+), (\d+), (\d+)u,',line)
    assert m,f'unparsed row {name}'
    key=tuple(map(int,m.groups()))
    assert key not in seen or seen[key]==name,f'key collision {name}/{seen[key]}'
    seen[key]=name
assert set(old)<=set(rows),'existing row lost'
out=head+'inline constexpr Row kRows[] = {\n'+'\n'.join(rows[k] for k in sorted(rows))+'\n    {0, 0, 0, 0u, {}}};\n} // namespace x1_mapfit\n'
if rows==old:
    (ROOT/a.output).write_bytes((ROOT/'bots/x3/src/x1_mapfit.h').read_bytes())
else:
    (ROOT/a.output).write_text(out,newline='\n')
print(f'{len(rows)} rows, preserved {len(old)} original named rows; output {a.output}')
