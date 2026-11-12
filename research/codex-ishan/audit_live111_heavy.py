"""Independently recount every EXP209 native outcome and safety event."""
from collections import defaultdict
import json

import ablate_dev as bench
from engine3_pool import ENGINE,HERE,read
from freeze_engine3_discovery import write

if __name__=='__main__':
    out=bench.CACHE/'live111-heavy-discovery-20261106'
    rows=read(out/'rows.json');saved=read(HERE/'LIVE111_HEAVY_RESULT.json')
    assert len(rows)==1440
    fresh=[]
    for row in rows:
        path=out/f"{row['noise_seed']}-{row['opponent']}"/f"{row['map']}-{row['side']}-{row['arm']}"/'native.json'
        assert bench.digest(path)==row['native_sha256']
        d=read(path);m=d['match'];team='team'+row['side'];rival='teamB' if team=='teamA' else 'teamA'
        assert m['engineBuildHash']==ENGINE and m['engineVersion']=='3.0.0' and d['diagnostics']['detailedCaptureComplete']
        assert m['mapHash']==row['map_hash'] and m['seed']==row['engine_seed']
        f=[x['timestamp']['round'] for e in d['events'] if e['kind']=='fuelExhausted' and e['owner']['team']==team for x in e['entries']]
        score=1 if m['outcome']==team else .5 if m['outcome']=='draw' else 0
        expected={'fuel_outs':len(f),'round1_fuel_outs':f.count(1),'score':score,'faults':d['diagnostics']['botFaults'][team],
                  'opponent_faults':d['diagnostics']['botFaults'][rival],'diagnostic_codes':d['diagnostics']['codes']}
        assert all(row[k]==v for k,v in expected.items())
        fresh.append({**row,**expected})
    key=lambda r:tuple(r[k] for k in ('map_hash','side','noise_seed','opponent','engine_seed'))
    base={key(r):r for r in fresh if r['arm']=='stock'}
    reports={}
    for arm in saved['results']:
        pairs=[(base[key(r)],r) for r in fresh if r['arm']==arm]
        overall=bench.summary(pairs)
        assert overall==saved['results'][arm]['overall']
        assert sum(a['draft']!=b['draft'] for a,b in pairs)==saved['results'][arm]['draft_changes']
        reports[arm]=overall
        for field,groups in saved['results'][arm]['strata'].items():
            for name,expected in groups.items():
                assert bench.summary([(a,b) for a,b in pairs if a[field]==name])==expected
    result={'raw_native_recount_pass':True,'games':len(fresh),'rows_sha256':bench.digest(out/'rows.json'),
            'result_sha256':bench.digest(HERE/'LIVE111_HEAVY_RESULT.json'),'reports':reports}
    write(HERE/'LIVE111_HEAVY_RECOUNT.json',result)
    print({'pass':True,'games':len(fresh)},flush=True)
