"""Extract static geometry from SDK probe logs; never inspect game outcomes."""
import hashlib, json, zipfile
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parent
manifest=json.loads((root.parent.parent/'outputs/rl-execution/EVALUATION_MAP_MANIFEST.json').read_text())
rows=[]
for row in manifest['maps']:
 p=root/'runs/map-audit/v3'/Path(row['file']).with_suffix('.repl26a').name
 with zipfile.ZipFile(p) as z: log=z.read('team-a.stdout').replace(b'\0',b'').decode()
 header=[l for l in log.splitlines() if l.startswith('JDMAP ')]
 tiles=[l for l in log.splitlines() if l.startswith('JDTILES ')]
 assert len(header)==len(tiles)==1,(p,'missing or repeated dump')
 _,w,h,sym=header[0].split();w,h,sym=map(int,(w,h,sym))
 a=np.frombuffer(bytes.fromhex(tiles[0].split()[1]),dtype=np.uint8).reshape(h,w)
 assert np.all(a<64)
 gs=[]
 for l in log.splitlines():
  if l.startswith('JDGROUP '):
   q=l.split();gs.append([int(q[1]),int(q[2]),int(q[3]),[list(map(int,t.split(','))) for t in q[4:]]])
 assert gs and all(0<=x<w and 0<=y<h and k>=0 for g in gs for x,y,k in g[3])
 variants=[]
 for flip in (False,True):
  for rot in range(4):
   b=np.fliplr(a) if flip else a
   b=np.rot90(b,rot)
   def point(x,y):
    ww,hh=w,h
    if flip:x=ww-1-x
    for _ in range(rot):x,y=y,ww-1-x;ww,hh=hh,ww
    return x,y
   transformed=[]
   for gold,gems,timer,camps in gs:
    transformed.append([gold,gems,timer,sorted([*point(x,y),k] for x,y,k in camps)])
   for swap in (False,True):
    v=b if not swap else ((b&15)|((b&16)<<1)|((b&32)>>1))
    variants.append(json.dumps([list(v.shape),v.tobytes().hex(),sorted(transformed)],separators=(',',':')))
 canonical=hashlib.sha256(min(variants).encode()).hexdigest()
 rows.append(dict(file=row['file'],map_sha256=row['sha256'],probe_log_sha256=hashlib.sha256(log.encode()).hexdigest(),split=row['split'],family=row['family'],
  width=w,height=h,symmetry_enum=sym,canonical_static_sha256=canonical,
  tiles={name:int(np.count_nonzero(a&bit)) for name,bit in [('wall',1),('hole',2),('bush',4),('altar',8),('spawnA',16),('spawnB',32)]},
  groups=len(gs),camp_entities=sum(len(g[3]) for g in gs),group_gold=sum(g[0] for g in gs),group_gems=sum(g[1] for g in gs)))
clusters={}
for r in rows:clusters.setdefault(r['canonical_static_sha256'],[]).append(r)
duplicates=[[r['file'] for r in rs] for rs in clusters.values() if len(rs)>1]
leaks=[[r['file'] for r in rs] for rs in clusters.values() if len({r['split'] for r in rs})>1]
report={'schema':'jd-sdk-static-geometry-audit-v1','maps_checked':len(rows),
 'method':'Official SDK release probe at 20M diagnostic fuel prints terrain/spawns/camp kinds, positions, rewards and respawn durations before resignation; no performance outcomes read. Canonicalize all D4 transforms and team swaps. This is NOT a real-fuel playing-strength test.',
 'scope':'Exact static geometry equivalence only, not a complete near-variant/topology or data-exposure audit.',
 'rejected_probe_attempts':'100k-fuel diagnostic dumps were incomplete on large maps and rejected; only complete v3 20M static dumps are included.',
 'probe_wasm_sha256':hashlib.sha256((root/'mac-project/bots/jd-map-audit/.cambc/build-release/bot.wasm').read_bytes()).hexdigest(),
 'probe_source_sha256':hashlib.sha256((root/'mac-project/bots/jd-map-audit/src/bot.cpp').read_bytes()).hexdigest(),
 'sdk_header_sha256':hashlib.sha256((root/'mac-project/sdk/cpp/cambc.h').read_bytes()).hexdigest(),
 'duplicate_geometry_clusters':duplicates,'cross_split_exact_geometry_clusters':leaks,'maps':rows}
assert len(rows)==86
out=root.parent.parent/'outputs/rl-execution/MAP_GEOMETRY_AUDIT.json'
out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='maps'}))
