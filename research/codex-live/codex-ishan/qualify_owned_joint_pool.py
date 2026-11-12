"""EXP251 original safety pool, conditional on the preselected joint native filter."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import ablate_dev as bench
from engine3_pool import CLI,CLI_HASH,ENGINE,HERE,SDK_ROOT,one,read
from freeze_engine3_discovery import write


if __name__=='__main__':
    filter_result=read(HERE/'LIVE111_OWNED_FACTORIAL_RESULT.json')
    recount=read(HERE/'LIVE111_OWNED_FACTORIAL_RECOUNT.json')
    assert filter_result['pass'] and recount['pass'] and recount['candidate_filter_pass']
    builds=read(HERE/'LIVE111_OWNED_FACTORIAL_BUILDS.json')
    candidate=Path(builds['joint']['path']);reference=SDK_ROOT/'bots/v92-e3/bot.wasm'
    assert bench.digest(CLI)==CLI_HASH and bench.digest(candidate)==builds['joint']['sha256']==builds['joint-rebuild']['sha256']
    assert bench.digest(reference)==bench.OPPS['v92'][1]
    baseline_doc=read(HERE/'ENGINE3_REBASELINE_POOL.json');assert baseline_doc['engine']==ENGINE
    bases={(r['map'],r['side']):r for r in baseline_doc['rows'] if r['arm']=='base'}
    stock={(r['map'],r['side']):r for r in read(HERE/'LIVE111_POOL_SAFETY.json')['rows']}
    maps=sorted((bench.ROOT/'maps/ladder-pool').glob('*.map26a'));assert len(maps)==86 and len(bases)==172
    pins={}
    for mp in maps:
        assert bench.digest(mp)==bases[mp.stem,'A']['map_hash']==bases[mp.stem,'B']['map_hash']
        for side in 'AB':
            p=bench.CACHE/'engine3-pool-20261105'/f'{mp.stem}-{side}-base/native.json'
            d=read(p);r=bases[mp.stem,side];team='team'+side
            assert d['match']['engineBuildHash']==ENGINE and d['match']['mapHash']==r['map_hash'] and d['match']['seed']==r['engine_seed']
            fuel=[x['timestamp']['round'] for e in d['events'] if e['kind']=='fuelExhausted' and e['owner'].get('team')==team for x in e['entries']]
            assert len(fuel)==r['fuel_outs'] and fuel.count(1)==r['round1_fuel_outs'] and not d['diagnostics']['codes'] and not any(d['diagnostics']['botFaults'].values())
            pins[mp.stem+'-'+side]=bench.digest(p)
    output=bench.CACHE/'engine3-owned-joint-pool-20261106';output.mkdir()
    write(HERE/'LIVE111_OWNED_JOINT_POOL_PLAN.json',{'experiment':251,'candidate':builds['joint'],'reference':bench.digest(reference),
          'engine':ENGINE,'cli':CLI_HASH,'games':172,'maps':{p.name:bench.digest(p) for p in maps},'reused_native_controls':pins,
          'criterion':'Original strict no faults/codes/per-cell total/R1 fuel increases versus frozen v92; no tuning on individual official failures.'})
    def play(job):
        mp,side=job;r=one(('joint',mp,side,candidate,reference),output=output)
        native=output/f'{mp.stem}-{side}-joint/native.json';d=read(native)
        stock_native=bench.CACHE/'engine3-live111-pool'/f'{mp.stem}-{side}-candidate/native.json'
        sd=read(stock_native)
        assert all(d['match'][k]==sd['match'][k] for k in ('engineBuildHash','mapHash','seed'))
        r.update({'native_sha256':bench.digest(native),'stock_native_sha256':bench.digest(stock_native),
                  'draft_equals_stock111':d['roster']['draft']==sd['roster']['draft']})
        return r
    rows=[]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for r in pool.map(play,[(p,s) for p in maps for s in 'AB']):
            rows.append(r)
            if len(rows)%40==0:print(f'{len(rows)}/172',flush=True)
    pairs=[(bases[r['map'],r['side']],r) for r in rows]
    for a,b in pairs:assert all(a[k]==b[k] for k in ('map_hash','side','opponent','engine_seed'))
    overall=bench.summary(pairs);errors=sum(bool(r['faults'] or r['opponent_faults'] or r['diagnostic_codes']) for r in rows)
    draft_equal=sum(r['draft_equals_stock111'] for r in rows)
    result={'candidate_release':bench.digest(candidate),'reference_release':bench.digest(reference),'engine':ENGINE,
            'overall':overall,'error_cells':errors,'draft_equals_stock111':draft_equal,
            'safety_pass':not errors and not overall['per_cell_fuel_regressions'] and draft_equal==172,
            'scope':'Original full-pool safety; fixed-build outcomes context only,no strength/ladder claim. Individual failures not design input.','rows':rows}
    write(HERE/'LIVE111_OWNED_JOINT_POOL_SAFETY.json',result)
    print({k:v for k,v in result.items() if k!='rows'},flush=True)
