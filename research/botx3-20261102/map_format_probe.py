from pathlib import Path
import sys,os
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'artifacts/local-only/g5070/deps'),str(ROOT/'tools/mapgen')]
from mapbuilder import Engine,MapBuilder,loads_in_game
os.environ['BC_ENGINE_WASM']=str(next((Path('C:/Users/omdha/AppData/Local/cambc/assets')).rglob('mapeditor/assets/v2_0_0*.wasm')))
e=Engine();old=MapBuilder(e,file_bytes=(ROOT/'maps/local-benchmarks/01gold-rush.map26a').read_bytes())
m=MapBuilder(e,40,40,'rotational')
for name in list(e.ex):
    if name.startswith('MapBuilder_Get') and ('Color' in name or name.endswith('FlowersEnabled')):
        setter=name.replace('_Get','_Set')
        if setter in e.ex:
            e.check(e.call(name,old.h,e.out));v=e.u32(e.out)
            e.check(e.call(setter,m.h,v))
import struct
e.check(e.call('MapBuilder_GetBushTintRange',old.h,e.out,e.out+4))
v=struct.unpack('<II',e.mem.read(e.store,e.out,e.out+8))
e.check(e.call('MapBuilder_SetBushTintRange',m.h,*v))
m.team_size(3);m.spawn(1,1,3,3);m.altar(5,20);m.camp('elk',10,10);m.camp('gem',10,20);m.verify()
data=m.encode();print('With explicit cosmetic defaults',loads_in_game(e,data),data[:24].hex())
(Path(__file__).parent/'minimal-cosmetic.map26a').write_bytes(data)
