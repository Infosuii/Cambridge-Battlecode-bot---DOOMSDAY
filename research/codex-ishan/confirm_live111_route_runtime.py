"""EXP220 disjoint-map route confirmation and controlled runtime interaction."""
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import json
import re

import ablate_dev as bench
from engine3_pool import CLI,CLI_HASH,ENGINE,HERE,SDK_ROOT,read
from engine3_qualify import build,play
from freeze_engine3_discovery import write
from live111_runtime_ablation import prepare
from profile_live111_first import exact_build
from qualify_local import DEV,partition

ARMS={'stock':(False,False),'route':(True,False),'nn_off':(False,True),'joint':(True,True)}
SEEDS=(61879,64223)


if __name__=='__main__':
    assert bench.digest(CLI)==CLI_HASH
    out=bench.CACHE/'live111-route-runtime-confirm-20261106';out.mkdir()
    old=read(HERE/'LIVE111_HEAVY_PLAN.json')['maps']
    cats=read(HERE/'ENGINE3_CATEGORIES_DEV.json')['maps']
    groups=defaultdict(list)
    for mp in partition('dev'):
        assert bench.digest(mp)==cats[mp.stem]['map_hash']
        if mp.name not in old:groups[cats[mp.stem]['category']].append(mp)
    for group in groups.values():group.sort(key=lambda p:bench.digest(p))
    maps=[]
    while len(maps)<12:
        for category in sorted(groups):
            if groups[category]:maps.append(groups[category].pop(0))
            if len(maps)==12:break
    assert not set(old)&{p.name for p in maps}
    opponents={n:bench.CACHE/bench.OPPS[n][0] for n in DEV}
    pins={n:bench.OPPS[n][1] for n in DEV}
    opponents['live109']=SDK_ROOT/'bots/live109/bot.wasm';pins['live109']=read(HERE/'LIVE109_SOURCE_VERIFIED.json')['wasm_sha256']
    assert all(bench.digest(p)==pins[n] for n,p in opponents.items())
    write(HERE/'LIVE111_ROUTE_RUNTIME_PLAN.json',{'engine':ENGINE,'cli':CLI_HASH,'arms':ARMS,'seeds':SEEDS,'games':960,
          'selection':'Category round-robin and content SHA over dev excluding all EXP209 maps',
          'maps':{p.name:{'sha256':bench.digest(p),'category':cats[p.stem]['category']} for p in maps},'opponents':pins})
    sources={}
    for arm,(route,nn) in ARMS.items():
        src=out/(arm+'-source');prepare(src,nn)
        if route:
            header=src/'common.h';data=header.read_bytes()
            data,n=re.subn(rb'(?m)^#define APEX_ROUTE_DEPTH 2(?=\s|$)',b'#define APEX_ROUTE_DEPTH 1',data,count=1)
            assert n==1;header.write_bytes(data)
        sources[arm]=src
    def release(arm):
        hashes=[]
        for suffix in ('','-rebuild') if arm!='stock' else ('',):
            hashes.append(bench.digest(exact_build(sources[arm],SDK_ROOT/'bots'/('route-runtime-'+arm+suffix+'-20261106'),1)))
        assert len(set(hashes))==1
        print('release',arm,hashes[0],flush=True)
        return arm,hashes[0]
    with ThreadPoolExecutor(max_workers=2) as pool:releases=dict(pool.map(release,ARMS))
    assert releases['stock']==read(HERE/'LIVE111_SOURCE_VERIFIED.json')['wasm_sha256']
    assert releases['route']==read(HERE/'LIVE111_HEAVY_RELEASES.json')['releases']['route_off']
    assert releases['nn_off']==read(HERE/'LIVE111_RUNTIME_ABLATION_BUILDS.json')['releases']['ablation']
    write(HERE/'LIVE111_ROUTE_RUNTIME_RELEASES.json',{'releases':releases,'sources':{a:{p.name:bench.digest(p) for p in s.iterdir() if p.is_file()} for a,s in sources.items()}})
    binaries={(a,s):build(src,SDK_ROOT/'bots'/f'route-runtime-{a}-{s}-20261106',s) for a,src in sources.items() for s in SEEDS}
    write(HERE/'LIVE111_ROUTE_RUNTIME_BINARIES.json',{f'{a}-{s}':bench.digest(p) for (a,s),p in binaries.items()})
    for s in SEEDS:
        for n in opponents:(out/f'{s}-{n}').mkdir()
    jobs=[(a,s,n,mp,side,binaries[a,s],ref,out/f'{s}-{n}',cats[mp.stem]['category']) for mp in maps for n,ref in opponents.items() for side in 'AB' for s in SEEDS for a in ARMS]
    rows=[]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for row in pool.map(play,jobs):
            path=out/f"{row['noise_seed']}-{row['opponent']}"/f"{row['map']}-{row['side']}-{row['arm']}"/'native.json'
            row['native_sha256']=bench.digest(path);row['draft']=read(path)['roster']['draft'];rows.append(row)
            if len(rows)%60==0:print(f'{len(rows)}/{len(jobs)}',flush=True)
    write(out/'rows.json',rows)
    key=lambda r:tuple(r[k] for k in ('map_hash','side','opponent','noise_seed','engine_seed'))
    by={a:{key(r):r for r in rows if r['arm']==a} for a in ARMS}
    results={}
    for a,b in (('stock','route'),('stock','nn_off'),('stock','joint'),('nn_off','joint'),('route','joint')):
        pairs=[(by[a][k],by[b][k]) for k in by[a]];strata={}
        for field in ('opponent','category','size'):
            grouped=defaultdict(list)
            for x,y in pairs:grouped[x[field]].append((x,y))
            strata[field]={n:bench.summary(v) for n,v in sorted(grouped.items())}
        overall=bench.summary(pairs);errors=sum(bool(r['faults'] or r['opponent_faults'] or r['diagnostic_codes']) for p in pairs for r in p)
        passed=(not errors and overall['round1'][1]<=overall['round1'][0] and overall['fuel'][1]<=overall['fuel'][0] and overall['map_cluster_ci_pp'][1]>=0 and all(v['delta_pp']>=-10 for g in strata.values() for v in g.values()))
        results[a+'->'+b]={'overall':overall,'strata':strata,'error_cells':errors,'draft_changes':sum(x['draft']!=y['draft'] for x,y in pairs),'local_filter_pass':passed}
    result={'scope':'EXP220 disjoint-dev confirmation/interaction,not ladder/release proof','engine':ENGINE,'releases':releases,'games':len(rows),'results':results}
    write(HERE/'LIVE111_ROUTE_RUNTIME_CONFIRM.json',result)
    print(json.dumps({k:{a:b for a,b in v.items() if a!='strata'} for k,v in results.items()},indent=2),flush=True)
