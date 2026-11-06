"""EXP247: fresh fixed-build four-arm native filter; joint preselected."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import ablate_dev as bench
from engine3_pool import CLI, CLI_HASH, ENGINE, HERE, SDK_ROOT, one, read
from freeze_engine3_discovery import write
from live111_dual_draft_cache import prepare as cache_prepare
from live111_owned_executor import patch, prepare as frame_prepare
from profile_live111_first import exact_build
from qualify_local import partition


def main():
    assert read(HERE/'LIVE111_OWNED_EXECUTOR_MECHANISM_R3.json')['pass']
    assert read(HERE/'LIVE111_OWNED_GUARDS_PROOF.json')['pass']
    assert read(HERE/'LIVE111_OWNED_EXECUTOR_PREREQUISITES_RECOUNT.json')['pass']
    assert bench.digest(CLI)==CLI_HASH
    output=bench.CACHE/'live111-owned-factorial-20261106'
    output.mkdir()
    identity=read(HERE/'LIVE111_SOURCE_VERIFIED.json')
    builds={}
    # Fresh all-off and cache controls as well as both copies of the joint.
    for arm in ('stock','cache','owner','joint','joint-rebuild'):
        src=output/('source-'+arm)
        if arm in ('cache','joint','joint-rebuild'):
            cache_prepare(src,True)
            patch(src,arm!='cache')
        else:
            frame_prepare(src,arm=='owner')
        wasm=exact_build(src,SDK_ROOT/'bots'/('live111-owned-factorial-'+arm+'-20261106'),1)
        builds[arm]={'path':str(wasm),'sha256':bench.digest(wasm),
                     'sources':{p.relative_to(src).as_posix():bench.digest(p) for p in sorted(src.rglob('*')) if p.is_file()}}
        print(arm,builds[arm]['sha256'],flush=True)
    assert builds['stock']['sha256']==identity['wasm_sha256']
    assert builds['cache']['sha256']=='086a14aa12090df556962fc242ad6f6ee4b1b0f3322a1ac1395ccf0518610fe6'
    assert builds['owner']['sha256']==read(HERE/'LIVE111_OWNED_EXECUTOR_BUILDS.json')['on']['sha256']
    assert builds['joint']['sha256']==builds['joint-rebuild']['sha256']
    write(HERE/'LIVE111_OWNED_FACTORIAL_BUILDS.json',builds)
    cases=read(HERE/'LIVE111_LARGE_DEV_CENSUS.json')['rows']
    maps={p.stem:p for p in partition('dev')}
    assert len(cases)==60
    arms=('stock','cache','owner','joint')
    for opponent in {r['opponent'] for r in cases}:
        (output/opponent).mkdir()
        assert bench.digest(bench.CACHE/bench.OPPS[opponent][0])==bench.OPPS[opponent][1]
    write(HERE/'LIVE111_OWNED_FACTORIAL_PLAN.json',{
        'experiment':247,'preselected_contender':'joint','fresh_games':240,
        'criterion':'No faults/codes/draft changes; joint no per-cell total/R1 fuel increases versus stock. Fixed-build outcomes are context only.',
        'engine':ENGINE,'cli':CLI_HASH,'builds':builds,
        'cases':[{k:r[k] for k in ('map','map_hash','side','opponent','engine_seed','noise_seed')} for r in cases],
        'opponents':{o:bench.OPPS[o][1] for o in {r['opponent'] for r in cases}}})
    def play(job):
        case,arm=job
        mp=maps[case['map']]
        assert bench.digest(mp)==case['map_hash']
        wasm=Path(builds[arm]['path'])
        assert bench.digest(wasm)==builds[arm]['sha256']
        row=one((arm,mp,case['side'],wasm,bench.CACHE/bench.OPPS[case['opponent']][0]),
                output=output/case['opponent'],opponent=case['opponent'])
        assert all(row[k]==case[k] for k in ('map_hash','side','opponent','engine_seed','noise_seed'))
        native=output/case['opponent']/f"{mp.stem}-{case['side']}-{arm}/native.json"
        row['native_path']=native.relative_to(bench.ROOT).as_posix()
        row['native_sha256']=bench.digest(native)
        return row
    rows=[]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for row in pool.map(play,[(c,a) for c in cases for a in arms]):
            rows.append(row)
            if len(rows)%40==0:print(f'{len(rows)}/240',flush=True)
    comparisons={}
    for arm in arms[1:]:
        pairs=[(rows[i],rows[i+arms.index(arm)]) for i in range(0,len(rows),4)]
        parity=sum(read(bench.ROOT/a['native_path'])['roster']['draft']==read(bench.ROOT/b['native_path'])['roster']['draft'] for a,b in pairs)
        summary=bench.summary(pairs)
        errors=sum(bool(r['faults'] or r['opponent_faults'] or r['diagnostic_codes']) for pair in pairs for r in pair)
        r1_increases=sum(b['round1_fuel_outs']>a['round1_fuel_outs'] for a,b in pairs)
        comparisons[arm]={'summary':summary,'draft_equal':parity,'error_cells':errors,'r1_cell_increases':r1_increases,
                          'pass':not errors and parity==60 and not r1_increases and not summary['per_cell_fuel_regressions']}
    result={'engine':ENGINE,'builds':builds,'n_games':len(rows),'preselected_contender':'joint',
            'comparisons':comparisons,'pass':comparisons['joint']['pass'],'rows':rows}
    write(HERE/'LIVE111_OWNED_FACTORIAL_RESULT.json',result)
    print(comparisons,flush=True)


if __name__=='__main__':main()
