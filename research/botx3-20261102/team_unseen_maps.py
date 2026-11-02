"""Fresh resource layouts and banking routes, frozen without candidate outcomes."""
from pathlib import Path
import hashlib,json,random,sys,os
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent/'team-unseen-maps'
sys.path[:0]=[str(ROOT/'artifacts/local-only/g5070/deps'),str(ROOT/'tools/mapgen')]
from mapbuilder import Engine,MapBuilder,loads_in_game
os.environ['BC_ENGINE_WASM']=str(next(Path('C:/Users/omdha/AppData/Local/cambc/assets').rglob('mapeditor/assets/v2_0_0*.wasm')))
e=Engine();OUT.mkdir(exist_ok=True);records={}
for fi,family in enumerate(['recursive-rooms','perimeter-banking']):
    for index in range(3):
        seed=798401+fi*7001+index*43;r=random.Random(seed);w=h=53+index*6
        walls=set()
        def divide(x0,y0,x1,y1,depth):
            if depth<=0 or min(x1-x0,y1-y0)<9:return
            if x1-x0>y1-y0:
                x=(x0+x1)//2;gap=r.randrange(y0+2,y1-2)
                walls.update((x,y) for y in range(y0,y1+1) if abs(y-gap)>1)
                divide(x0,y0,x-1,y1,depth-1);divide(x+1,y0,x1,y1,depth-1)
            else:
                y=(y0+y1)//2;gap=r.randrange(x0+2,x1-2)
                walls.update((x,y) for x in range(x0,x1+1) if abs(x-gap)>1)
                divide(x0,y0,x1,y-1,depth-1);divide(x0,y+1,x1,y1,depth-1)
        if fi==0:divide(5,5,w//2-2,h-5,4)
        else:walls={(x,y) for x in range(8,w//2-3,6) for y in range(5,h-5) if y<h-12}
        nodes=[]
        for attempt in range(2000):
            x=r.randrange(6,w//2-3);y=r.randrange(6,h-7 if fi==0 else h//2)
            if all(max(abs(x-a),abs(y-b))>=5 for a,b in nodes):nodes.append((x,y))
            if len(nodes)>=9+index:break
        camps=[]
        for i,(x,y) in enumerate(nodes):
            kind=['gem','elk','gold','wolf'][(i+index)%4]
            for dx in range(2 if kind in ['gem','wolf'] else 1):camps.append((kind,x+dx,y))
        altars=[(4,h-5),(w//2-4,h-8 if fi else h//2)]
        for x,y in nodes+altars+[(2,2)]:
            walls.difference_update((xx,y) for xx in range(2,x+2))
            walls.difference_update((2,yy) for yy in range(2,y+2))
            for dx in range(-1,3):
                for dy in [-1,0,1]:walls.discard((x+dx,y+dy))
        name=f'{family}-{index}';p=OUT/(name+'.map26a')
        if not p.exists():
            mb=MapBuilder(e,w,h,'rotational')
            try:
                mb.team_size(3+index);mb.spawn(1,1,4,4)
                for x,y in sorted(walls):mb.wall(x,y)
                for x,y in altars:mb.altar(x,y)
                for kind,x,y in camps:mb.camp(kind,x,y)
                mb.verify();data=mb.encode();assert loads_in_game(e,data),name;p.write_bytes(data)
            finally:mb.destroy()
        records[name]=dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),family=family,seed=seed,
            width=w,height=h,picks=3+index,resource_nodes=nodes,altars=altars,native_load_checked=True)
manifest=dict(generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              rule='New topology, resource, size and bank placements; no candidate measurements during generation.',maps=records)
target=OUT/'manifest.json'
if target.exists():assert json.loads(target.read_text())==json.loads(json.dumps(manifest))
else:target.write_text(json.dumps(manifest,indent=2)+'\n')
print('Frozen',len(records),'new resource-layout maps.')
