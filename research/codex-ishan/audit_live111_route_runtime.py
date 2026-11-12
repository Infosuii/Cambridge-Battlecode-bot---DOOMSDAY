"""Recount EXP220 from native outputs and recheck every evaluated binary/source pin."""
from hashlib import sha256
import json
import re

import ablate_dev as bench
from engine3_pool import ENGINE,HERE,SDK_ROOT,read
from freeze_engine3_discovery import write

if __name__=='__main__':
    out=bench.CACHE/'live111-route-runtime-confirm-20261106'
    saved=read(HERE/'LIVE111_ROUTE_RUNTIME_CONFIRM.json');plan=read(HERE/'LIVE111_ROUTE_RUNTIME_PLAN.json')
    releases=read(HERE/'LIVE111_ROUTE_RUNTIME_RELEASES.json');binaries=read(HERE/'LIVE111_ROUTE_RUNTIME_BINARIES.json')
    for name,expected in binaries.items():
        project=SDK_ROOT/'bots'/('route-runtime-'+name+'-20261106')
        assert bench.digest(project/'bot.wasm')==expected
        arm,seed=name.rsplit('-',1)
        source=project/'src';release_source=out/(arm+'-source')
        for filename,digest in releases['sources'][arm].items():
            data=(release_source/filename).read_bytes();assert sha256(data).hexdigest()==digest
            if filename=='common.h':
                for macro,old,new in (('NOVA_SEED','1',seed),('NOVA_SEED_EPS','0.04f','0.005f')):
                    data,n=re.subn(rb'(?m)^#define '+macro.encode()+b' '+re.escape(old.encode())+rb'(?=\s|$)',f'#define {macro} {new}'.encode(),data,count=1)
                    assert n==1
            assert (source/filename).read_bytes()==data
    rows=read(out/'rows.json');assert len(rows)==960
    for r in rows:
        path=out/f"{r['noise_seed']}-{r['opponent']}"/f"{r['map']}-{r['side']}-{r['arm']}"/'native.json'
        assert bench.digest(path)==r['native_sha256'];d=read(path);m=d['match']
        assert (m['engineVersion'],m['engineBuildHash'])==('3.0.0',ENGINE) and d['diagnostics']['detailedCaptureComplete']
        assert (m['seed'],m['mapHash'])==(r['engine_seed'],r['map_hash'])
        us='team'+r['side'];rival='teamB' if us=='teamA' else 'teamA'
        fuel=[x['timestamp']['round'] for e in d['events'] if e['kind']=='fuelExhausted' and e['owner'].get('team')==us for x in e['entries']]
        expected={'score':1 if m['outcome']==us else .5 if m['outcome']=='draw' else 0,'fuel_outs':len(fuel),'round1_fuel_outs':fuel.count(1),
                  'faults':d['diagnostics']['botFaults'][us],'opponent_faults':d['diagnostics']['botFaults'][rival],'diagnostic_codes':d['diagnostics']['codes']}
        assert all(r[k]==v for k,v in expected.items()) and r['draft']==d['roster']['draft']
    key=lambda r:tuple(r[k] for k in ('map_hash','side','opponent','noise_seed','engine_seed'))
    by={a:{key(r):r for r in rows if r['arm']==a} for a in plan['arms']}
    assert all(len(v)==240 for v in by.values())
    summaries={}
    for label,report in saved['results'].items():
        a,b=label.split('->');assert by[a].keys()==by[b].keys()
        pairs=[(by[a][k],by[b][k]) for k in by[a]];overall=bench.summary(pairs)
        assert overall==report['overall']
        assert sum(x['draft']!=y['draft'] for x,y in pairs)==report['draft_changes']
        assert sum(bool(r['faults'] or r['opponent_faults'] or r['diagnostic_codes']) for p in pairs for r in p)==report['error_cells']
        for field,groups in report['strata'].items():
            for n,expected in groups.items():assert bench.summary([(x,y) for x,y in pairs if x[field]==n])==expected
        passed=(not report['error_cells'] and overall['round1'][1]<=overall['round1'][0] and overall['fuel'][1]<=overall['fuel'][0] and overall['map_cluster_ci_pp'][1]>=0 and all(v['delta_pp']>=-10 for g in report['strata'].values() for v in g.values()))
        assert passed==report['local_filter_pass'];summaries[label]=overall
    result={'raw_native_recount_pass':True,'binary_source_pins_pass':True,'games':len(rows),'result_sha256':bench.digest(HERE/'LIVE111_ROUTE_RUNTIME_CONFIRM.json'),
            'rows_sha256':bench.digest(out/'rows.json'),'reports':summaries}
    write(HERE/'LIVE111_ROUTE_RUNTIME_RECOUNT.json',result)
    print({'pass':True,'games':len(rows)},flush=True)
