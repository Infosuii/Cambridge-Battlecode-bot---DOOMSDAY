"""Once-only validation layouts; freeze all bytes before measuring any candidate."""
from pathlib import Path
import hashlib,json,random,sys,os,math
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent/'draft-summary-final-maps'
deps=os.environ.get('DZ_MAPGEN_DEPS')
if deps:sys.path.insert(0,deps)
sys.path.insert(0,str(ROOT/'tools/mapgen'))
from mapbuilder import Engine,MapBuilder,loads_in_game
if not os.environ.get('BC_ENGINE_WASM'):
 assets=Path(os.environ['LOCALAPPDATA'])/'cambc/assets' if os.name=='nt' else Path.home()/'.local/share/cambc/assets'
 os.environ['BC_ENGINE_WASM']=str(next(assets.rglob('mapeditor/assets/v2_0_0*.wasm')))
e=Engine();OUT.mkdir(exist_ok=True);records={}
for fi,family in enumerate(['diagonal-switchbacks','radial-hubs']):
 for index in range(4):
  seed=4198703+fi*10007+index*131;r=random.Random(seed);w=h=45+6*index
  walls=set()
  if fi==0:
   walls={(x,y) for x in range(6,w//2) for y in range(5,h-4) if (x+2*y)%13 in (0,1) and (3*x-y)%17>3}
  else:
   walls={(x,y) for x in range(5,w//2) for y in range(5,h-4) if int(math.hypot(x-w//2,y-h//2))%9 in (0,1) and (x+3*y)%19>4}
  nodes=[]
  for _ in range(5000):
   x=r.randrange(6,w//2-3);y=r.randrange(6,h-5)
   if all(max(abs(x-a),abs(y-b))>=4 for a,b in nodes):nodes.append((x,y))
   if len(nodes)>=10+index:break
  altars=[(4,h-5),(w//2-3,5+((index*7)%(h-12)))]
  camps=[]
  for j,(x,y) in enumerate(nodes):
   kind=r.choice(['gem','gem','gold','wolf','elk'])
   for dx in range(1+(kind=='gem' and j%3==0)):camps.append((kind,x+dx,y))
  # Connect objectives by alternating L routes, rather than a shared perimeter spine.
  previous=(3,3)
  for x,y in nodes+altars:
   px,py=previous
   if r.randrange(2):
    route=[(xx,py) for xx in range(min(px,x),max(px,x)+1)]+[(x,yy) for yy in range(min(py,y),max(py,y)+1)]
   else:route=[(px,yy) for yy in range(min(py,y),max(py,y)+1)]+[(xx,y) for xx in range(min(px,x),max(px,x)+1)]
   walls.difference_update(route)
   for dx in range(-1,3):
    for dy in [-1,0,1]:walls.discard((x+dx,y+dy))
   previous=(x,y)
  walls.difference_update((x,y) for x in range(1,6) for y in range(1,6))
  name=f'{family}-{index}';p=OUT/(name+'.map26a')
  if not p.exists():
   mb=MapBuilder(e,w,h,'rotational')
   try:
    mb.team_size(3+index%3);mb.spawn(1,1,4,4)
    for x,y in sorted(walls):mb.wall(x,y)
    for x,y in altars:mb.altar(x,y)
    for kind,x,y in camps:mb.camp(kind,x,y)
    mb.verify();data=mb.encode();assert loads_in_game(e,data),name;p.write_bytes(data)
   finally:mb.destroy()
  records[name]=dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),family=family,seed=seed,width=w,picks=3+index%3,resource_nodes=nodes,altars=altars,native_load_checked=True)
manifest=dict(generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),rule='New fixed seeds, terrain, resource and bank layout families. Once-only validation; no candidate-dependent regeneration or tuning.',maps=records)
p=OUT/'manifest.json'
if p.exists():assert json.loads(p.read_text())==json.loads(json.dumps(manifest))
else:p.write_text(json.dumps(manifest,indent=2)+'\n')
print('Frozen',len(records),'new native-valid maps',flush=True)
