"""Verify every reused attribution row against its immutable native report and input pins."""
from datetime import datetime,timezone

import ablate_dev as bench
from engine3_pool import ENGINE,HERE,SDK_ROOT,read
from freeze_engine3_discovery import write
from qualify_local import partition


if __name__=='__main__':
    stock=read(HERE/'LIVE111_LARGE_DEV_CENSUS.json')['rows']
    cache=read(HERE/'LIVE111_DUAL_DRAFT_CACHE_RELEASE_LARGE.json')['pairs']
    maps={p.stem:p for p in partition('dev')}
    source=read(HERE/'LIVE111_SOURCE_VERIFIED.json')['wasm_sha256']
    cache_hash=read(HERE/'LIVE111_DUAL_DRAFT_CACHE_RELEASE_BUILDS.json')['builds']['on']['sha256']
    assert bench.digest(SDK_ROOT/'bots/live111/bot.wasm')==source
    assert bench.digest(SDK_ROOT/'bots/live111-dual-draft-cache-release-on/bot.wasm')==cache_hash
    rows=[]
    for arm,records in (('stock',stock),('cache',[b for a,b in cache])):
        for r in records:
            assert bench.digest(maps[r['map']])==r['map_hash']
            assert bench.digest(bench.CACHE/bench.OPPS[r['opponent']][0])==bench.OPPS[r['opponent']][1]
            label='stock111' if arm=='stock' else 'dual-draft-cache-release'
            root='live111-large-development' if arm=='stock' else 'live111-dual-draft-cache-release'
            path=bench.CACHE/root/r['opponent']/f"{r['map']}-{r['side']}-{label}/native.json"
            d=read(path);m=d['match'];ours='team'+r['side'];them='teamB' if r['side']=='A' else 'teamA'
            assert m['engineBuildHash']==ENGINE and m['engineVersion']=='3.0.0' and d['diagnostics']['detailedCaptureComplete']
            assert (m['mapHash'],m['seed'])==(r['map_hash'],r['engine_seed']) and r['noise_seed']==1
            fuel=[t['timestamp']['round'] for e in d['events'] if e['kind']=='fuelExhausted' and e['owner'].get('team')==ours for t in e['entries']]
            values={'score':1 if m['outcome']==ours else .5 if m['outcome']=='draw' else 0,'fuel_outs':len(fuel),'round1_fuel_outs':fuel.count(1),
                    'faults':d['diagnostics']['botFaults'][ours],'opponent_faults':d['diagnostics']['botFaults'][them],'diagnostic_codes':d['diagnostics']['codes']}
            assert all(r[k]==v for k,v in values.items()),(arm,r['map'],r['side'])
            rows.append({'arm':arm,'map':r['map'],'side':r['side'],'opponent':r['opponent'],'native_sha256':bench.digest(path),'all_recorded_native_values_match':True})
    write(HERE/'LIVE111_INIT_BUDGET_REUSED_AUDIT.json',{'read_utc':datetime.now(timezone.utc).isoformat(),'n':len(rows),'stock_release':source,'cache_release':cache_hash,'pass':True,'rows':rows})
    print({'reused_rows':len(rows),'all_values_and_input_pins_match':True},flush=True)
