exec(compile(open(__file__.replace('map_container_probe.py','map_format_probe.py'),encoding='utf-8').read().split('m=MapBuilder')[0],__file__,'exec'))
from mapio import read_map
b=(ROOT/'maps/local-benchmarks/01gold-rush.map26a').read_bytes();r=read_map(e,b);m=MapBuilder(e,file_bytes=b)
for _ in r['camps']:
    e.check(e.call('MapBuilder_GetCampHandle',m.h,0,e.out));handle=e.u64(e.out)
    m._c('MapBuilder_RemoveCamp',handle)
for kind,key in [('Bush','bushes'),('Hole','holes'),('Wall','walls'),('Altar','altars')]:
    for x,y in r[key]:m._c('MapBuilder_Remove'+kind,x,y)
m.spawn(1,1,3,3);m.altar(5,15);m.camp('elk',10,10);m.camp('gem',10,20);m.verify()
print('New geometry in old container',loads_in_game(e,m.encode()))
