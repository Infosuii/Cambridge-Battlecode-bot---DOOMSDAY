"""EXP291 clean disabled/counterfactual/task duplicate builds before any games."""
from concurrent.futures import ThreadPoolExecutor
import subprocess
import ablate_dev as bench
from engine3_pool import CLI,CLI_HASH,ENGINE,HERE,SDK_ROOT
from freeze_engine3_discovery import write
from v92_task_planner import BASE,REFERENCE,prepare

if __name__=='__main__':
    assert bench.digest(CLI)==CLI_HASH
    sources={p.relative_to(BASE).as_posix():bench.digest(p) for p in BASE.rglob('*') if p.is_file()}
    assert len(sources)==35 and bench.digest(BASE.parent/'bot.wasm')==REFERENCE
    settings={'off':0,'planner':1,'planner-rebuild':1,'task':2,'task-rebuild':2}
    parameters=[1.,1.,1.,1.1]
    plan={'experiment':291,'base_platform':80,'base_repo':'bots/v92','base_source_cache':str(BASE),'base_wasm':REFERENCE,
          'sources':sources,'engine':ENGINE,'cli':CLI_HASH,'sdk':bench.digest(SDK_ROOT/'sdk/cpp/cambc.h'),
          'settings':settings,'parameters':parameters,'preselected':'task','recipe':bench.digest(HERE/'v92_task_planner.py'),
          'kernel':bench.digest(HERE/'task_planner.inc'),'scope':'Initial structural prototype builds, no platform submission, qualification or strength claim.'}
    write(HERE/'V92_TASK_PLANNER_BUILD_PLAN.json',plan)
    def build(item):
        name,mode=item;project=SDK_ROOT/'bots'/f'codex-task-planner-{name}-20261106';src=project/'src';prepare(src,mode,parameters)
        hashes={p.relative_to(src).as_posix():bench.digest(p) for p in src.rglob('*') if p.is_file()}
        assert {n for n,h in sources.items() if hashes[n]!=h}=={'common.h','bot.h','bot.cpp'}
        assert set(hashes)-set(sources)=={'codex_task_planner.inc'}
        wasm=project/'bot.wasm'
        with (project/'build.log').open('xb') as log:subprocess.run([CLI,'build',project,'--release','--output',wasm],cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
        result={'path':str(wasm),'sha256':bench.digest(wasm),'sources':hashes,'platform_submission':None}
        print(name,result['sha256'],flush=True);return name,result
    with ThreadPoolExecutor(max_workers=2) as pool:builds=dict(pool.map(build,settings.items()))
    assert builds['off']['sha256']==REFERENCE
    for name in ('planner','task'):assert builds[name]['sha256']==builds[name+'-rebuild']['sha256']
    write(HERE/'V92_TASK_PLANNER_BUILDS.json',builds);print({'off_exact':True,'both_duplicates':True},flush=True)
