"""EXP234: fixed artificial single-farmer role/play mechanics, no win inference."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess

import ablate_dev as bench
from engine3_pool import CLI,CLI_HASH,ENGINE,HERE,SDK_ROOT,read
from freeze_engine3_discovery import write
from live111_camp_role_play import fixture,prepare
from profile_live111_first import exact_build
from qualify_local import partition


if __name__=='__main__':
    assert bench.digest(CLI)==CLI_HASH
    output=bench.CACHE/'live111-camp-roles-20261106';output.mkdir()
    roles={'marcella':('marcella',7),'ryth':('ryth',0),'stellar':('stellar',5),'prism':('prism',6)}
    builds={}
    for arm,flag in (('clean-off',False),('clean-on',True),('clean-rebuild',True)):
        src=output/('source-'+arm);prepare(src,flag)
        wasm=exact_build(src,SDK_ROOT/'bots'/('live111-camp-roles-'+arm+'-20261106'),1)
        builds[arm]={'path':str(wasm),'sha256':bench.digest(wasm)}
        print(arm,builds[arm]['sha256'],flush=True)
    assert builds['clean-off']['sha256']==read(HERE/'LIVE111_SOURCE_VERIFIED.json')['wasm_sha256']
    assert builds['clean-on']['sha256']==builds['clean-rebuild']['sha256']
    for role,hero in roles.items():
        for mode in ('original','aoeplay'):
            arm=role+'-'+mode;src=output/('source-'+arm);prepare(src,mode=='aoeplay');fixture(src,hero)
            wasm=exact_build(src,SDK_ROOT/'bots'/('live111-camp-roles-'+arm+'-20261106'),1)
            builds[arm]={'path':str(wasm),'sha256':bench.digest(wasm),
                         'sources':{p.relative_to(src).as_posix():bench.digest(p) for p in sorted(src.rglob('*')) if p.is_file()}}
            print(arm,builds[arm]['sha256'],flush=True)
    write(HERE/'LIVE111_CAMP_ROLES_BUILDS.json',builds)
    maps=sorted(partition('dev'),key=lambda p:bench.digest(p));assert len(maps)==90
    ref=SDK_ROOT/'bots/offset-aoe-idle-20261106/bot.wasm'
    assert bench.digest(ref)==read(HERE/'OFFSET_AOE_ACTION_PROOF.json')['builds']['idle']
    jobs=[(role,mode,mp,side) for mp in maps for side in 'AB' for role in roles for mode in ('original','aoeplay')]
    write(HERE/'LIVE111_CAMP_ROLES_PLAN.json',{'experiment':234,'engine':ENGINE,'cli':CLI_HASH,'horizon':300,'fuel':100000,
          'scope':'Artificial forced-role single-farmer mechanics; idle allies/opponent, no strength/draft-selection conclusion.',
          'maps':{p.name:bench.digest(p) for p in maps},'roles':roles,'builds':builds,'reference':bench.digest(ref),'n_games':len(jobs)})
    def run(job):
        role,mode,mp,side=job;arm=role+'-'+mode;wasm=Path(builds[arm]['path'])
        assert bench.digest(wasm)==builds[arm]['sha256']
        directory=output/f'{mp.stem}-{side}-{arm}';directory.mkdir()
        bots=(wasm,ref) if side=='A' else (ref,wasm)
        with (directory/'run.log').open('xb') as log:
            subprocess.run([CLI,'run',*bots,'--map',mp,'--release','--fuel','100000','--rounds','300','--json','--log-limit','0',
                            '--statistics',directory/'native.json','--out-dir',directory],cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
        doc=read(directory/'native.json');m=doc['match'];ours='team'+side
        assert (m['engineVersion'],m['engineBuildHash'])==('3.0.0',ENGINE) and m['mapHash']==bench.digest(mp)
        assert doc['diagnostics']['detailedCaptureComplete']
        actors=[c for c in doc['champions'] if c['team']==ours and c['name'].lower()==role]
        assert len(actors)==1;actor=actors[0]
        own=[e for e in doc['events'] if e['owner'].get('team')==ours and e['owner'].get('id')==actor['id']]
        clears=[{'round':x['timestamp']['round'],'group':x['target']['id']} for e in own if e['kind']=='campClear' for x in e['entries']]
        captures=[{'round':x['timestamp']['round'],'amount':x['amount'],'context':x.get('context'),'value':x.get('value')} for e in own if e['kind']=='gemCollection' for x in e['entries']]
        fuel=[x['timestamp']['round'] for e in own if e['kind']=='fuelExhausted' for x in e['entries']]
        # Other actors must remain idle; retain all diagnostics instead of dropping bad role cases.
        assert all(float(c['metrics']['monsterDamageDone'])==0 for c in doc['champions'] if c['team']!=ours or c['id']!=actor['id'])
        return {'role':role,'mode':mode,'map':mp.stem,'side':side,'map_hash':m['mapHash'],'engine_seed':m['seed'],
                'rounds_completed':m['roundsCompleted'],'metrics':actor['metrics'],'actor_id':actor['id'],
                'clears':clears,'captures':captures,'fuel_rounds':fuel,'diagnostics':doc['diagnostics'],
                'native_path':(directory/'native.json').relative_to(bench.ROOT).as_posix(),'native_sha256':bench.digest(directory/'native.json')}
    rows=[]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for row in pool.map(run,jobs):
            rows.append(row)
            if len(rows)%120==0:print(f'{len(rows)}/{len(jobs)}',flush=True)
    write(HERE/'LIVE111_CAMP_ROLES_RAW.json',{'n_games':len(rows),'plan_sha256':bench.digest(HERE/'LIVE111_CAMP_ROLES_PLAN.json'),'rows':rows})
    print('Completed',len(rows),'mechanics fixtures',flush=True)
