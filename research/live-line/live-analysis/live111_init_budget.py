"""Compose exactly the two proved mechanisms and retain all attribution arms."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import ablate_dev as bench
from engine3_pool import CLI,CLI_HASH,ENGINE,HERE,SDK_ROOT,one,read
from freeze_engine3_discovery import write
from live111_cold_reserve import patch
from live111_dual_draft_cache import prepare as prepare_cache
from profile_live111_first import exact_build
from qualify_local import partition


def prepare(target,cache,cold):
    prepare_cache(target,cache)
    patch(target,cold,require_ready=True)
    header=(target/'common.h').read_text(encoding='utf8')
    assert '#define CODEX_COLD_SCOPED 0' in header and '#define CODEX_DRAFT_CACHE_PROBE 0' in header
    assert '#define CODEX_COLD_ROUND' not in header and '#define CODEX_COLD_TYPE' not in header


if __name__=='__main__':
    assert bench.digest(CLI)==CLI_HASH
    identity=read(HERE/'LIVE111_SOURCE_VERIFIED.json')
    old=read(HERE/'LIVE111_DUAL_DRAFT_CACHE_RELEASE_LARGE.json')
    output=bench.CACHE/'live111-init-budget';output.mkdir()
    sources={};projects={}
    settings=(('off',False,False),('cache',True,False),('cold',False,True),('joint',True,True))
    for arm,cache,cold in settings:
        for suffix in ('','-rebuild') if cold else ('',):
            name=arm+suffix;src=output/(name+'-source');prepare(src,cache,cold)
            sources[name]=src;projects[name]=SDK_ROOT/'bots'/('live111-init-budget-'+name)
    def build(name):
        wasm=exact_build(sources[name],projects[name],1)
        return name,{'wasm_sha256':bench.digest(wasm),'source_file_hashes':{p.relative_to(sources[name]).as_posix():bench.digest(p) for p in sources[name].rglob('*') if p.is_file()}}
    with ThreadPoolExecutor(max_workers=2) as pool:builds=dict(pool.map(build,projects))
    assert builds['off']['wasm_sha256']==identity['wasm_sha256']
    assert builds['cache']['wasm_sha256']==old['builds']['on']['sha256']
    for arm in ('cold','joint'):assert builds[arm]['wasm_sha256']==builds[arm+'-rebuild']['wasm_sha256']
    write(HERE/'LIVE111_INIT_BUDGET_BUILDS.json',{'source111_archive':identity['archive_sha256'],'builds':builds})
    stock=read(HERE/'LIVE111_LARGE_DEV_CENSUS.json')['rows']
    key=lambda r:tuple(r[k] for k in ('map_hash','side','opponent','engine_seed','noise_seed'))
    rows={'stock':stock,'cache':[b for a,b in old['pairs']],'cold':[],'joint':[]}
    assert {key(r) for r in stock}=={key(r) for r in rows['cache']}
    maps={p.stem:p for p in partition('dev')}
    originals={key(r):r for r in stock}
    for arm in ('cold','joint'):
        for opponent in {r['opponent'] for r in stock}:(output/(arm+'-'+opponent)).mkdir()
    write(HERE/'LIVE111_INIT_BUDGET_PLAN.json',{'engine':ENGINE,'source_releases':{k:v['wasm_sha256'] for k,v in builds.items()},'cells':[{k:r[k] for k in ('map','map_hash','side','opponent','engine_seed','noise_seed')} for r in stock],
          'opponents':{n:bench.OPPS[n][1] for n in {r['opponent'] for r in stock}},'preselected_candidate':'joint','new_games':120,'reused_attribution_games':120})
    def run(job):
        arm,base=job;mp=maps[base['map']];ref=bench.CACHE/bench.OPPS[base['opponent']][0]
        assert bench.digest(mp)==base['map_hash'] and bench.digest(ref)==bench.OPPS[base['opponent']][1]
        original=bench.CACHE/'live111-large-development'/base['opponent']/f"{base['map']}-{base['side']}-stock111/native.json"
        original_doc=read(original)
        wasm=projects[arm]/'bot.wasm';assert bench.digest(wasm)==builds[arm]['wasm_sha256']
        row=one((arm,mp,base['side'],wasm,ref),output=output/(arm+'-'+base['opponent']),opponent=base['opponent'])
        assert key(row)==key(base)
        native=output/(arm+'-'+base['opponent'])/f"{base['map']}-{base['side']}-{arm}/native.json"
        doc=read(native)
        row['draft_equal_stock']=original_doc['roster']['draft']==doc['roster']['draft']
        row['native_sha256']=bench.digest(native)
        return arm,row
    with ThreadPoolExecutor(max_workers=6) as pool:
        for i,(arm,row) in enumerate(pool.map(run,[(a,r) for r in stock for a in ('cold','joint')]),1):
            rows[arm].append(row)
            if i%30==0:print(f'{i}/120',flush=True)
    indexed={arm:{key(r):r for r in records} for arm,records in rows.items()}
    summaries={f'{a}->{b}':bench.summary([(indexed[a][k],indexed[b][k]) for k in originals]) for a,b in (('stock','cache'),('stock','cold'),('stock','joint'),('cold','joint'),('cache','joint'))}
    errors=sum(bool(r['faults'] or r['opponent_faults'] or r['diagnostic_codes']) for records in rows.values() for r in records)
    draft_changes=sum(not r['draft_equal_stock'] for arm in ('cold','joint') for r in rows[arm])
    result={'engine':ENGINE,'releases':{k:v['wasm_sha256'] for k,v in builds.items()},'new_games':120,'reused_games':120,'summaries':summaries,'error_cells':errors,'draft_changes':draft_changes,
            'native_filter_pass':not errors and not draft_changes and not summaries['stock->joint']['per_cell_fuel_regressions'],'rows':rows}
    write(HERE/'LIVE111_INIT_BUDGET_LARGE.json',result)
    print({k:v for k,v in result.items() if k!='rows'},flush=True)
