"""Independent construction families, split before any scheduler selection."""
from pathlib import Path
import hashlib,json,random,sys,math,os
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent/'team-maps'
sys.path[:0]=[str(ROOT/'artifacts/local-only/g5070/deps'),str(ROOT/'tools/mapgen')]
from mapbuilder import Engine,MapBuilder,loads_in_game
assets=Path('C:/Users/omdha/AppData/Local/cambc/assets')
os.environ['BC_ENGINE_WASM']=str(next(p for p in assets.rglob('v2_0_0*.wasm') if 'mapeditor' in p.parts))
e=Engine()
manifest={}
for split,families in [('dev',['open-grid','gated-stripes']),('final',['cellular-caves','concentric-rings'])]:
    folder=OUT/split;folder.mkdir(parents=True,exist_ok=True)
    for family in families:
        for index in range(4):
            seed=2026110200+index;rng=random.Random(seed)
            w=h=40+4*index
            mirror=lambda p:(w-1-p[0],h-1-p[1])
            half={(x,y) for x in range(w//2) for y in range(h)}
            walls=set()
            if family=='gated-stripes':
                walls={(x,y) for x,y in half if x%8 in (0,1) and y%13 not in (3,4,5,6)}
            if family=='concentric-rings':
                walls={(x,y) for x,y in half if int(math.hypot(x-w/2,y-h/2))%8==0 and (x+y)%11>2}
            if family=='cellular-caves':
                cells={(x,y) for x,y in half if rng.random()<0.46}
                for step in range(4):
                    cells={(x,y) for x,y in half if sum((x+dx,y+dy) in cells for dx in [-1,0,1] for dy in [-1,0,1] if dx or dy)>=5}
                walls=cells
            camps=[]
            for x in range(6,w//2-2,7):
                for y in range(6,h-5,7):
                    kind=['wolf','elk','gem','gold'][(x//7+y//7+index)%4]
                    camps.append((kind,x,y))
                    if kind in ['wolf','elk']:camps.append((kind,x+1,y))
            altars=[(5,h//2),(w//2-3,3)]
            # Native-valid access without filtering on a candidate's results.
            # Dig short branches to one vertical spine, preserving family terrain.
            targets=[(x,y) for _,x,y in camps]+altars+[(2,2)]
            clear=set()
            for x,y in targets:
                for xx in range(2,x+1):clear.add((xx,y))
                for yy in range(2,y+1):clear.add((2,yy))
                for dx in [-1,0,1]:
                    for dy in [-1,0,1]:clear.add((x+dx,y+dy))
            for x in range(0,6):
                for y in range(0,6):clear.add((x,y))
            walls-=clear
            name=f'{family}-{index}'
            path=folder/(name+'.map26a')
            if not path.exists():
                mb=MapBuilder(e,w,h,'rotational')
                try:
                    mb.team_size(3+index%3);mb.spawn(1,1,4,4)
                    for x,y in sorted(walls):mb.wall(x,y)
                    for x,y in altars:mb.altar(x,y)
                    for kind,x,y in camps:mb.camp(kind,x,y)
                    mb.verify();data=mb.encode()
                    assert loads_in_game(e,data),name
                    path.write_bytes(data)
                finally:mb.destroy()
            manifest[f'{split}/{name}']=dict(family=family,split=split,seed=seed,width=w,height=h,
                team_picks=3+index%3,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                protected=split=='final',native_load_checked=True)
record=OUT/'manifest.json'
result=dict(generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    rule='Entire construction families held out. Final maps prohibited during repairs/selection.',maps=manifest)
if record.exists():assert json.loads(record.read_text())==result,'Frozen map identity changed'
else:record.write_text(json.dumps(result,indent=2)+'\n')
print('Frozen',len(manifest),'native-valid maps; final families remain unused.')
