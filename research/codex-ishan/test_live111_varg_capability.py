"""EXP283 preselected shared-capability DEVELOPMENT filter, strict old safety."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import ablate_dev as bench
from engine3_pool import CLI,CLI_HASH,ENGINE,HERE,one,read
from freeze_engine3_discovery import write
from qualify_local import partition


if __name__=='__main__':
    assert bench.digest(CLI)==CLI_HASH
    builds=read(HERE/'LIVE111_VARG_CAPABILITY_BUILDS.json')
    original=read(HERE/'LIVE111_OWNED_FACTORIAL_BUILDS.json')['stock'];builds['stock']=original
    assert builds['off']['sha256']==original['sha256']
    for name in ('geometry','model'):assert builds[name]['sha256']==builds[name+'-rebuild']['sha256']
    for b in builds.values():
        p=Path(b['path']);assert bench.digest(p)==b['sha256']
        assert {q.relative_to(p.parent/'src').as_posix():bench.digest(q) for q in (p.parent/'src').rglob('*') if q.is_file()}==b['sources']
    cases=read(HERE/'LIVE111_TERRAIN_FACTORIAL_PLAN.json')['cases'];assert len(cases)==60
    maps={p.stem:p for p in partition('dev')};arms=['stock','geometry','model']
    out=bench.CACHE/'live111-varg-capability-filter-20261106';out.mkdir()
    opponents=sorted({c['opponent'] for c in cases})
    for o in opponents:(out/o).mkdir();assert bench.digest(bench.CACHE/bench.OPPS[o][0])==bench.OPPS[o][1]
    plan={'experiment':283,'preselected':'model','games':180,'cases':cases,'arms':arms,'builds':builds,'engine':ENGINE,'cli':CLI_HASH,
          'opponents':{o:bench.OPPS[o][1] for o in opponents},
          'wrapper_recount_sha256':bench.digest(HERE/'VARG_WRAPPER_PROOF_R2_RECOUNT.json'),
          'criterion':'Original per-cell total/R1fuel/fault/code/draft veto versus stock; deterministic wins context only. All60stock native controls reproduce.'}
    write(HERE/'LIVE111_VARG_CAPABILITY_FILTER_PLAN.json',plan)
    def run(job):
        c,arm=job;mp=maps[c['map']];assert bench.digest(mp)==c['map_hash']
        r=one((arm,mp,c['side'],Path(builds[arm]['path']),bench.CACHE/bench.OPPS[c['opponent']][0]),output=out/c['opponent'],opponent=c['opponent'])
        assert all(r[k]==c[k] for k in ('map_hash','side','opponent','engine_seed','noise_seed'))
        native=out/c['opponent']/f'{mp.stem}-{c["side"]}-{arm}/native.json';r['native_path']=native.relative_to(bench.ROOT).as_posix();r['native_sha256']=bench.digest(native);return r
    rows=[]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for r in pool.map(run,[(c,a) for c in cases for a in arms]):
            rows.append(r)
            if len(rows)%30==0:print(f'{len(rows)}/180',flush=True)
    index={(r['map'],r['side'],r['opponent'],r['arm']):r for r in rows};old={(r['map'],r['side'],r['opponent'],r['arm']):r for r in read(HERE/'LIVE111_OWNED_FACTORIAL_RESULT.json')['rows']}
    reproduced=0
    for c in cases:
        key=(c['map'],c['side'],c['opponent'],'stock');before=old[key];assert bench.digest(bench.ROOT/before['native_path'])==before['native_sha256']
        assert read(bench.ROOT/index[key]['native_path'])==read(bench.ROOT/before['native_path']);reproduced+=1
    comparisons={}
    for base,candidate in (('stock','geometry'),('stock','model'),('geometry','model')):
        pairs=[(index[c['map'],c['side'],c['opponent'],base],index[c['map'],c['side'],c['opponent'],candidate]) for c in cases]
        summary=bench.summary(pairs)
        parity=sum(read(bench.ROOT/a['native_path'])['roster']['draft']==read(bench.ROOT/b['native_path'])['roster']['draft'] for a,b in pairs)
        errors=sum(bool(r['faults'] or r['opponent_faults'] or r['diagnostic_codes']) for p in pairs for r in p);r1=sum(b['round1_fuel_outs']>a['round1_fuel_outs'] for a,b in pairs)
        comparisons[base+'->'+candidate]={'summary':summary,'draft_equal':parity,'error_cells':errors,'r1_cell_increases':r1,
                                         'pass':not(errors or r1 or summary['per_cell_fuel_regressions']) and parity==60}
    result={'preselected':'model','games':len(rows),'builds':builds,'old_stock_controls_equal':reproduced,'comparisons':comparisons,
            'pass':comparisons['stock->model']['pass'],'rows':rows}
    write(HERE/'LIVE111_VARG_CAPABILITY_FILTER_RESULT.json',result);print(comparisons,flush=True)
