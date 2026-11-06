"""EXP283 clean duplicate builds, exact-off/source/proof identity before games."""
from concurrent.futures import ThreadPoolExecutor
import subprocess
import ablate_dev as bench
from engine3_pool import CLI,CLI_HASH,HERE,SDK_ROOT,read
from freeze_engine3_discovery import write
from live111_varg_capability import prepare

if __name__=='__main__':
    gate=read(HERE/'VARG_WRAPPER_PROOF_R2_RECOUNT.json');assert gate['pass'] and gate['games']==6 and gate['all_original_fixed_controls_rerun']
    assert bench.digest(HERE/'VARG_WRAPPER_PROOF_R2.json')==gate['raw_sha256']
    assert bench.digest(CLI)==CLI_HASH
    base=read(HERE/'LIVE111_SOURCE_VERIFIED.json');proof=read(HERE/'VARG_WRAPPER_PROOF_R2_PLAN.json')
    settings={'off':(False,False),'geometry':(True,False),'geometry-rebuild':(True,False),'model':(True,True),'model-rebuild':(True,True)}
    plan={'base_platform':111,'base_source_archive':base['source_archive_sha256'] if 'source_archive_sha256' in base else '72e9a198135d9b42361a223be505e379b1cf286e1223ee3daf1fbb90a34f8463',
          'base_wasm':base['wasm_sha256'],'settings':settings,'preselected':'model','prepare_sha256':bench.digest(HERE/'live111_varg_capability.py'),
          'wrapper_recount_sha256':bench.digest(HERE/'VARG_WRAPPER_PROOF_R2_RECOUNT.json'),'scope':'Clean builds only, no platform submission or strength claim.'}
    write(HERE/'LIVE111_VARG_CAPABILITY_BUILD_PLAN.json',plan)
    def build(item):
        name,(geometry,model)=item;project=SDK_ROOT/'bots'/f'live111-varg-capability-{name}-20261106';src=project/'src';prepare(src,geometry,model)
        sources={p.name:bench.digest(p) for p in src.iterdir() if p.is_file()}
        assert {n for n,h in base['source_file_hashes'].items() if sources[n]!=h}=={'common.h','bot.h','bot.cpp'}
        assert set(sources)-set(base['source_file_hashes'])=={'varg_group_geometry.h'}
        assert sources['bot.cpp']==proof['sources']['bot.cpp']==gate['production_helper_source_sha256']
        clean_h=(SDK_ROOT/'bots/varg-wrapper-proof-r2-20261106/src/bot.h').read_text(encoding='utf8').replace('    friend void codex_varg_probe(Bot&,bool);\n','')
        assert (src/'bot.h').read_text(encoding='utf8')==clean_h
        wasm=project/'bot.wasm'
        with (project/'build.log').open('xb') as log:subprocess.run([CLI,'build',project,'--release','--output',wasm],cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
        result={'path':str(wasm),'sha256':bench.digest(wasm),'sources':sources,'platform_submission':None}
        print(name,result['sha256'],flush=True);return name,result
    with ThreadPoolExecutor(max_workers=2) as pool:builds=dict(pool.map(build,settings.items()))
    assert builds['off']['sha256']==base['wasm_sha256']
    for name in ('geometry','model'):assert builds[name]['sha256']==builds[name+'-rebuild']['sha256']
    write(HERE/'LIVE111_VARG_CAPABILITY_BUILDS.json',builds)
    print({'exact_off':True,'duplicate_geometry':True,'duplicate_model':True},flush=True)
