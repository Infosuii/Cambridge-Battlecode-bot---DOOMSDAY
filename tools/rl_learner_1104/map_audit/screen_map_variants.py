"""Outcome-free heuristic similarity screen; not a proof of independent maps."""
from pathlib import Path
import json, zipfile, itertools
import numpy as np
r=Path(__file__).resolve().parent
m=json.loads((r.parent.parent/'outputs/rl-execution/EVALUATION_MAP_MANIFEST.json').read_text())
features=[]
for row in m['maps']:
 with zipfile.ZipFile(r/'runs/map-audit/v3'/Path(row['file']).with_suffix('.repl26a').name) as z:
  ls=z.read('team-a.stdout').replace(b'\0',b'').decode().splitlines()
 _,w,h,_=next(l for l in ls if l.startswith('JDMAP ')).split();w,h=int(w),int(h)
 a=np.frombuffer(bytes.fromhex(next(l for l in ls if l.startswith('JDTILES ')).split()[1]),dtype=np.uint8).reshape(h,w)
 layers=[(a&b)!=0 for b in [1,2,4,8]]+[(a&48)!=0]
 # Keep camp-kind channels separate. Fixed enum range covers all observed nonnegative types.
 camps=np.zeros((16,h,w),dtype=bool)
 for line in ls:
  if line.startswith('JDGROUP '):
   for token in line.split()[4:]:
    x,y,k=map(int,token.split(','));assert 0<=k<16;camps[k,y,x]=True
 layers+=list(camps)
 f=np.zeros((len(layers),16,16))
 for i,layer in enumerate(layers):
  ys,xs=np.nonzero(layer)
  np.add.at(f[i],(ys*16//h,xs*16//w),1)
  if len(xs): f[i]/=len(xs)  # position distribution, so sparse objectives retain weight
 features.append(f)
def similarity(a,b):
 active=(a.sum((1,2))+b.sum((1,2)))>0
 v=[]
 for flip in [False,True]:
  for rot in range(4):
   t=np.rot90(b[:,:,::-1] if flip else b,rot,axes=(1,2))
   union=np.maximum(a,t).sum((1,2));overlap=np.minimum(a,t).sum((1,2))
   v.append(float((overlap[active]/union[active]).mean()))
 return max(v)
assert all(abs(similarity(f,f)-1)<1e-12 for f in features)
pairs=[]
for i,j in itertools.combinations(range(len(features)),2):
 if m['maps'][i]['split']==m['maps'][j]['split']:continue
 s=similarity(features[i],features[j]);assert 0<=s<=1+1e-12
 pairs.append({'a':m['maps'][i]['file'],'a_split':m['maps'][i]['split'],'b':m['maps'][j]['file'],'b_split':m['maps'][j]['split'],'similarity':s})
pairs.sort(key=lambda x:-x['similarity'])
out={'kind':'heuristic_cross_split_map_similarity_screen','maps':len(features),
 'method':'16x16 normalized position distributions for terrain, combined spawn and separate camp kinds; mean soft-Jaccard across nonempty channels; max over D4 orientations.',
 'limitations':'Heuristic only. Different resolutions, tile quantization, resource amounts, path connectivity and camp-group semantics can differ. No threshold establishes independence; do not automatically change split or claim it sealed.',
 'outcomes_used':False,'top_cross_split_pairs':pairs[:20]}
p=r.parent.parent/'outputs/rl-execution/MAP_VARIANT_SCREEN.json';p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'pairs_checked':len(pairs),'top':pairs[:5]}))
