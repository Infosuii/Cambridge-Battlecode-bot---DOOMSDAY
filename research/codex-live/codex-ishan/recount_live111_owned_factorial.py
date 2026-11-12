"""Independent native recount of all EXP247 cells, identities and draft parity."""
from collections import defaultdict
from pathlib import Path

import ablate_dev as bench
from engine3_pool import CLI,CLI_HASH,ENGINE,HERE,read
from freeze_engine3_discovery import write
from qualify_local import partition


if __name__=='__main__':
    file=HERE/'LIVE111_OWNED_FACTORIAL_RESULT.json'
    data=read(file);plan=read(HERE/'LIVE111_OWNED_FACTORIAL_PLAN.json')
    assert plan['preselected_contender']==data['preselected_contender']=='joint'
    assert data['n_games']==len(data['rows'])==plan['fresh_games']==240
    assert bench.digest(CLI)==CLI_HASH==plan['cli']
    maps={p.stem:p for p in partition('dev')}
    for arm,build in data['builds'].items():
        wasm=Path(build['path']);assert bench.digest(wasm)==build['sha256']
        for name,sha in build['sources'].items():assert bench.digest(wasm.parent/'src'/name)==sha
    assert data['builds']==plan['builds']
    assert data['builds']['joint']['sha256']==data['builds']['joint-rebuild']['sha256']
    index={};draft={}
    for r in data['rows']:
        p=bench.ROOT/r['native_path'];assert bench.digest(p)==r['native_sha256']
        doc=read(p);m=doc['match'];ours='team'+r['side'];other='teamB' if ours=='teamA' else 'teamA'
        assert m['engineVersion']=='3.0.0' and m['engineBuildHash']==ENGINE==plan['engine']
        assert m['mapHash']==r['map_hash']==bench.digest(maps[r['map']]) and m['seed']==r['engine_seed']
        assert doc['diagnostics']['detailedCaptureComplete']
        fuel=[x['timestamp']['round'] for e in doc['events'] if e['kind']=='fuelExhausted' and e['owner']['team']==ours for x in e['entries']]
        expected={'score':1 if m['outcome']==ours else .5 if m['outcome']=='draw' else 0,
                  'fuel_outs':len(fuel),'round1_fuel_outs':fuel.count(1),
                  'faults':doc['diagnostics']['botFaults'][ours],'opponent_faults':doc['diagnostics']['botFaults'][other],
                  'diagnostic_codes':doc['diagnostics']['codes']}
        assert all(r[k]==v for k,v in expected.items())
        key=(r['map'],r['side'],r['opponent'],r['arm']);assert key not in index
        index[key]=r;draft[key]=doc['roster']['draft']
    comparisons={}
    for arm in ('cache','owner','joint'):
        pairs=[];parity=0
        for c in plan['cases']:
            key=(c['map'],c['side'],c['opponent'])
            a,b=index[*key,'stock'],index[*key,arm]
            assert all(a[k]==b[k]==c[k] for k in ('map_hash','side','opponent','engine_seed','noise_seed'))
            assert bench.digest(bench.CACHE/bench.OPPS[c['opponent']][0])==plan['opponents'][c['opponent']]
            pairs.append((a,b));parity+=draft[*key,'stock']==draft[*key,arm]
        summary=bench.summary(pairs)
        errors=sum(bool(r['faults'] or r['opponent_faults'] or r['diagnostic_codes']) for pair in pairs for r in pair)
        r1=sum(b['round1_fuel_outs']>a['round1_fuel_outs'] for a,b in pairs)
        report={'summary':summary,'draft_equal':parity,'error_cells':errors,'r1_cell_increases':r1,
                'pass':not errors and parity==60 and not r1 and not summary['per_cell_fuel_regressions']}
        assert report==data['comparisons'][arm];comparisons[arm]=report
    # Fresh fixed-build controls must independently reproduce the original census.
    old=read(HERE/'LIVE111_LARGE_DEV_CENSUS.json')['rows']
    for r in old:
        fresh=index[r['map'],r['side'],r['opponent'],'stock']
        assert all(fresh[k]==r[k] for k in ('map_hash','engine_seed','score','fuel_outs','round1_fuel_outs','faults','opponent_faults','diagnostic_codes'))
    assert data['pass']==comparisons['joint']['pass']
    write(HERE/'LIVE111_OWNED_FACTORIAL_RECOUNT.json',{'pass':True,'candidate_filter_pass':data['pass'],
        'native_cells_reopened':240,'stock_controls_reproduced':60,'result_sha256':bench.digest(file),'comparisons':comparisons})
    print(comparisons,flush=True)
