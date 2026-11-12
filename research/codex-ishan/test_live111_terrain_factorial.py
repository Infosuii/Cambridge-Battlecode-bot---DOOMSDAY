"""EXP269: clean interval-terrain cache, preselected joint, 2x2 plus stock anchor."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from shutil import copytree

import ablate_dev as bench
from engine3_pool import CLI,CLI_HASH,ENGINE,HERE,SDK_ROOT,one,read
from freeze_engine3_discovery import write
from live111_draft_bush_cache import patch
from profile_live111_first import exact_build
from qualify_local import partition

def source_from(build,destination):
    source=Path(build['path']).parent/'src'
    paths={p.relative_to(source).as_posix():bench.digest(p) for p in source.rglob('*') if p.is_file()}
    assert paths==build['sources'];copytree(source,destination)

if __name__=='__main__':
    prerequisite=read(HERE/'DRAFT_BUSH_CACHE_V3_PREREQUISITES_RECOUNT.json');assert prerequisite['pass']
    assert prerequisite['source_codec']==bench.digest(HERE/'grouped_bush_codec_v3.h')
    for label,name in (('pure','GROUPED_BUSH_CODEC_V3_PROOF.json'),('cache','DRAFT_BUSH_CACHE_FULL_V3.json'),('steady','DRAFT_BUSH_CACHE_STEADY_V3_R2.json')):
        assert bench.digest(HERE/name)==prerequisite['raw_result_hashes'][label]
    assert bench.digest(CLI)==CLI_HASH
    oldbuilds=read(HERE/'LIVE111_OWNED_FACTORIAL_BUILDS.json');output=bench.CACHE/'live111-terrain-factorial-20261106';output.mkdir()
    builds={}
    for name,old in (('stock','stock'),('cache','cache'),('graph','joint')):
        b=oldbuilds[old];assert bench.digest(Path(b['path']))==b['sha256']
        source=Path(b['path']).parent/'src';assert all(bench.digest(source/n)==h for n,h in b['sources'].items());builds[name]=b
    jobs=[('off','joint',False),('terrain','cache',True),('terrain-rebuild','cache',True),('joint','joint',True),('joint-rebuild','joint',True)]
    def build(job):
        name,base,enabled=job;src=output/('source-'+name);source_from(oldbuilds[base],src);patch(src,enabled,False)
        (src/'grouped_bush_codec.h').write_bytes((HERE/'grouped_bush_codec_v3.h').read_bytes())
        assert bench.digest(src/'nnrec.cpp')==oldbuilds[base]['sources']['nnrec.cpp']
        for n in ('draft.cpp','draft_net.h','nn_weights.h','nn_infer.h','bot.cpp','fight.cpp','economy.cpp'):
            assert bench.digest(src/n)==oldbuilds[base]['sources'][n]
        wasm=exact_build(src,SDK_ROOT/'bots'/f'live111-terrain-factorial-{name}-20261106',1)
        result={'path':str(wasm),'sha256':bench.digest(wasm),'sources':{p.relative_to(src).as_posix():bench.digest(p) for p in sorted(src.rglob('*')) if p.is_file()}}
        print(name,result['sha256'],flush=True);return name,result
    with ThreadPoolExecutor(max_workers=2) as pool:
        for name,b in pool.map(build,jobs):builds[name]=b
    assert builds['off']['sha256']==builds['graph']['sha256']
    assert builds['terrain']['sha256']==builds['terrain-rebuild']['sha256']
    assert builds['joint']['sha256']==builds['joint-rebuild']['sha256']
    write(HERE/'LIVE111_TERRAIN_FACTORIAL_BUILDS.json',builds)
    cases=read(HERE/'LIVE111_LARGE_DEV_CENSUS.json')['rows'];assert len(cases)==60
    maps={p.stem:p for p in partition('dev')};arms=('stock','cache','graph','terrain','joint')
    opponents={r['opponent'] for r in cases}
    for opponent in opponents:
        (output/opponent).mkdir();assert bench.digest(bench.CACHE/bench.OPPS[opponent][0])==bench.OPPS[opponent][1]
    plan={'experiment':269,'preselected_contender':'joint','fresh_games':300,'arms':arms,'engine':ENGINE,'cli':CLI_HASH,'builds':builds,
          'cases':[{k:r[k] for k in ('map','map_hash','side','opponent','engine_seed','noise_seed')} for r in cases],
          'opponents':{o:bench.OPPS[o][1] for o in opponents},'prerequisite_recount_sha256':bench.digest(HERE/'DRAFT_BUSH_CACHE_V3_PREREQUISITES_RECOUNT.json'),
          'criterion':'Joint no faults/codes/draft changes or per-cell total/R1 fuel increases versus original stock; fixed-build wins context only.'}
    write(HERE/'LIVE111_TERRAIN_FACTORIAL_PLAN.json',plan)
    def play(job):
        c,arm=job;mp=maps[c['map']];assert bench.digest(mp)==c['map_hash'];b=builds[arm];wasm=Path(b['path']);assert bench.digest(wasm)==b['sha256']
        r=one((arm,mp,c['side'],wasm,bench.CACHE/bench.OPPS[c['opponent']][0]),output=output/c['opponent'],opponent=c['opponent'])
        assert all(r[k]==c[k] for k in ('map_hash','side','opponent','engine_seed','noise_seed'))
        native=output/c['opponent']/f'{mp.stem}-{c["side"]}-{arm}/native.json';r['native_path']=native.relative_to(bench.ROOT).as_posix();r['native_sha256']=bench.digest(native);return r
    rows=[]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for r in pool.map(play,[(c,a) for c in cases for a in arms]):
            rows.append(r)
            if len(rows)%50==0:print(f'{len(rows)}/300',flush=True)
    index={(r['map'],r['side'],r['opponent'],r['arm']):r for r in rows}
    old=read(HERE/'LIVE111_OWNED_FACTORIAL_RESULT.json')['rows'];oldindex={(r['map'],r['side'],r['opponent'],r['arm']):r for r in old}
    reproduced=0
    for c in cases:
        for arm,oldarm in (('stock','stock'),('cache','cache'),('graph','joint')):
            key=(c['map'],c['side'],c['opponent']);a=index[*key,arm];b=oldindex[*key,oldarm]
            assert read(bench.ROOT/a['native_path'])==read(bench.ROOT/b['native_path']);reproduced+=1
    comparisons={}
    for base,candidate in (('stock','cache'),('stock','graph'),('stock','terrain'),('stock','joint'),('cache','terrain'),('cache','graph'),('graph','joint'),('terrain','joint')):
        pairs=[(index[c['map'],c['side'],c['opponent'],base],index[c['map'],c['side'],c['opponent'],candidate]) for c in cases]
        summary=bench.summary(pairs);parity=sum(read(bench.ROOT/a['native_path'])['roster']['draft']==read(bench.ROOT/b['native_path'])['roster']['draft'] for a,b in pairs)
        errors=sum(bool(r['faults'] or r['opponent_faults'] or r['diagnostic_codes']) for p in pairs for r in p);r1=sum(b['round1_fuel_outs']>a['round1_fuel_outs'] for a,b in pairs)
        comparisons[base+'->'+candidate]={'summary':summary,'draft_equal':parity,'error_cells':errors,'r1_cell_increases':r1,
                                          'pass':not errors and parity==60 and not r1 and not summary['per_cell_fuel_regressions']}
    result={'engine':ENGINE,'builds':builds,'n_games':len(rows),'preselected_contender':'joint','old_control_native_equal':reproduced,
            'comparisons':comparisons,'pass':comparisons['stock->joint']['pass'],'rows':rows}
    write(HERE/'LIVE111_TERRAIN_FACTORIAL_RESULT.json',result);print(comparisons,flush=True)
