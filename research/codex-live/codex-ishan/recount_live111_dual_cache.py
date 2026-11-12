"""Independently recount all frozen dual-cache controls with repeated valid modes retained."""
from copy import deepcopy

import ablate_dev as bench
from engine3_pool import ENGINE,HERE,read
from freeze_engine3_discovery import write


def passed(row):
    checks=row['checks'];modes={c[4] for c in checks}
    return bool(not row['errors'] and not row['draft_fuel_events'] and row['draft_equal'] and checks and all(all(c[:3]) for c in checks) and
                (modes=={0,1} or modes=={0} and row['absent_mode_rejected'] and all(row['absent_mode_rejected'])) and row['draft_fuel'] and
                all(d[0]>=1000000 and d[1]>0 and d[2] for d in row['draft_fuel']))


if __name__=='__main__':
    before=read(HERE/'LIVE111_DUAL_CACHE_PROOF.json')
    assert before['failed']==2 and not before['pass'] and before['engine']==ENGINE
    proof=bench.CACHE/'live111-dual-cache-proof'
    base={ (r['map'],r['side']):r for r in read(HERE/'LIVE111_DRAFT_CACHE_FULL_PROOF.json')['rows'] if r['arm']=='base'}
    rows=[];corrected=[]
    for row in before['rows']:
        native=proof/f"{row['map']}-{row['side']}/native.json"
        assert bench.digest(native)==row['native_sha256']
        a=read(native);b=base[row['map'],row['side']]
        old=bench.ROOT/b['directory']/'native.json'
        assert bench.digest(old)==b['native_sha256']==row['baseline_native_sha256']
        z=read(old)
        assert a['match']['engineBuildHash']==z['match']['engineBuildHash']==ENGINE
        assert a['match']['mapHash']==z['match']['mapHash']==row['map_hash'] and a['match']['seed']==z['match']['seed']
        assert (a['roster']['draft']==z['roster']['draft'])==row['draft_equal']
        after={**row,'pass':passed(row)}
        if after['pass']!=row['pass']:
            assert row['map']=='pool_1119' and len(row['checks'])>2 and all(all(c[:3]) for c in row['checks'])
            corrected.append({'map':row['map'],'side':row['side'],'old':row['pass'],'new':after['pass'],'modes':[c[4] for c in row['checks']]})
        rows.append(after)
    sample=deepcopy(next(r for r in rows if {c[4] for c in r['checks']}=={0,1}))
    assert passed(sample)
    bad=deepcopy(sample);bad['checks'][0][1]=0;assert not passed(bad)
    bad=deepcopy(sample);bad['checks']=[c for c in bad['checks'] if c[4]==0];bad['absent_mode_rejected']=[];assert not passed(bad)
    bad=deepcopy(sample);bad['checks'][0][4]=2;assert not passed(bad)
    bad=deepcopy(sample);bad['draft_equal']=False;assert not passed(bad)
    result={**before,'original_report_sha256':bench.digest(HERE/'LIVE111_DUAL_CACHE_PROOF.json'),'pass':all(r['pass'] for r in rows),
            'failed':sum(not r['pass'] for r in rows),'all_native_hashes_and_stock_pairs_reverified':True,'negative_controls_pass':True,'corrected':corrected,'rows':rows}
    write(HERE/'LIVE111_DUAL_CACHE_PROOF_RECOUNT.json',result)
    print({k:v for k,v in result.items() if k!='rows'},flush=True)
