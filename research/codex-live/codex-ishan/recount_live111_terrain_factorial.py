"""Independent EXP269 native/source/identity/draft/control recount."""
from pathlib import Path

import ablate_dev as bench
from engine3_pool import CLI,CLI_HASH,ENGINE,HERE,read
from freeze_engine3_discovery import write
from qualify_local import partition

if __name__=='__main__':
    path=HERE/'LIVE111_TERRAIN_FACTORIAL_RESULT.json';data=read(path);plan=read(HERE/'LIVE111_TERRAIN_FACTORIAL_PLAN.json')
    assert data['preselected_contender']==plan['preselected_contender']=='joint' and data['n_games']==len(data['rows'])==plan['fresh_games']==300
    assert data['builds']==plan['builds'] and bench.digest(CLI)==CLI_HASH==plan['cli']
    builds=data['builds'];assert builds['off']['sha256']==builds['graph']['sha256']
    for arm in ('terrain','joint'):assert builds[arm]['sha256']==builds[arm+'-rebuild']['sha256']
    for build in builds.values():
        wasm=Path(build['path']);assert bench.digest(wasm)==build['sha256']
        actual={p.relative_to(wasm.parent/'src').as_posix():bench.digest(p) for p in (wasm.parent/'src').rglob('*') if p.is_file()}
        assert actual==build['sources']
    maps={p.stem:p for p in partition('dev')};index={};draft={}
    for r in data['rows']:
        p=bench.ROOT/r['native_path'];assert bench.digest(p)==r['native_sha256'];doc=read(p);match=doc['match'];ours='team'+r['side'];other='teamB' if ours=='teamA' else 'teamA'
        assert match['engineBuildHash']==ENGINE and match['engineVersion']=='3.0.0' and match['mapHash']==r['map_hash']==bench.digest(maps[r['map']]) and match['seed']==r['engine_seed']
        assert doc['diagnostics']['detailedCaptureComplete']
        fuel=[x['timestamp']['round'] for e in doc['events'] if e['kind']=='fuelExhausted' and e['owner'].get('team')==ours for x in e['entries']]
        expected={'score':1 if match['outcome']==ours else .5 if match['outcome']=='draw' else 0,'fuel_outs':len(fuel),'round1_fuel_outs':fuel.count(1),
                  'faults':doc['diagnostics']['botFaults'][ours],'opponent_faults':doc['diagnostics']['botFaults'][other],'diagnostic_codes':doc['diagnostics']['codes']}
        assert all(r[k]==v for k,v in expected.items());key=(r['map'],r['side'],r['opponent'],r['arm']);assert key not in index;index[key]=r;draft[key]=doc['roster']['draft']
    comparisons={}
    for base,candidate in (('stock','cache'),('stock','graph'),('stock','terrain'),('stock','joint'),('cache','terrain'),('cache','graph'),('graph','joint'),('terrain','joint')):
        pairs=[];parity=0
        for c in plan['cases']:
            key=(c['map'],c['side'],c['opponent']);a,b=index[*key,base],index[*key,candidate]
            assert all(a[k]==b[k]==c[k] for k in ('map_hash','side','opponent','engine_seed','noise_seed'))
            assert bench.digest(bench.CACHE/bench.OPPS[c['opponent']][0])==plan['opponents'][c['opponent']]
            pairs.append((a,b));parity+=draft[*key,base]==draft[*key,candidate]
        summary=bench.summary(pairs);errors=sum(bool(r['faults'] or r['opponent_faults'] or r['diagnostic_codes']) for p in pairs for r in p);r1=sum(b['round1_fuel_outs']>a['round1_fuel_outs'] for a,b in pairs)
        value={'summary':summary,'draft_equal':parity,'error_cells':errors,'r1_cell_increases':r1,'pass':not errors and parity==60 and not r1 and not summary['per_cell_fuel_regressions']}
        assert value==data['comparisons'][base+'->'+candidate];comparisons[base+'->'+candidate]=value
    previous=read(HERE/'LIVE111_OWNED_FACTORIAL_RESULT.json')['rows'];old={(r['map'],r['side'],r['opponent'],r['arm']):r for r in previous};reproduced=0
    for c in plan['cases']:
        for arm,oldarm in (('stock','stock'),('cache','cache'),('graph','joint')):
            key=(c['map'],c['side'],c['opponent']);a=index[*key,arm];b=old[*key,oldarm];p=bench.ROOT/b['native_path'];assert bench.digest(p)==b['native_sha256']
            assert read(bench.ROOT/a['native_path'])==read(p);reproduced+=1
    assert reproduced==data['old_control_native_equal']==180 and data['pass']==comparisons['stock->joint']['pass']
    write(HERE/'LIVE111_TERRAIN_FACTORIAL_RECOUNT.json',{'pass':True,'candidate_filter_pass':data['pass'],'native_cells_reopened':300,'old_control_native_equal':180,
          'result_sha256':bench.digest(path),'comparisons':comparisons})
    print({'candidate_filter_pass':data['pass'],'native_cells_reopened':300,'old_controls_equal':180,
           'arms':{a:{'wins':sum(r['score'] for r in data['rows'] if r['arm']==a),'fuel':sum(r['fuel_outs'] for r in data['rows'] if r['arm']==a),'r1':sum(r['round1_fuel_outs'] for r in data['rows'] if r['arm']==a)} for a in plan['arms']}},flush=True)
