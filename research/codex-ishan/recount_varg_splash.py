"""Reopen raw sources/native/archive and reconcile SDK snapshots with replay HP."""
import os
import subprocess
from zipfile import ZipFile
import ablate_dev as bench
from engine3_pool import HERE, SDK_ROOT, ENGINE, read
from freeze_engine3_discovery import write
from prove_varg_splash import floating

if __name__=='__main__':
    raw=read(HERE/'VARG_SPLASH_OBSERVATIONS.json');plan=read(HERE/'VARG_SPLASH_PLAN.json')
    assert bench.digest(HERE/'VARG_SPLASH_PLAN.json')==raw['plan_sha256']
    assert bench.digest(HERE/'varg_splash_probe.cpp')==plan['source']
    assert bench.digest(SDK_ROOT/'sdk/cpp/cambc.h')==plan['sdk']
    for b in raw['builds'].values():
        from pathlib import Path
        assert bench.digest(Path(b['path']))==b['wasm']
        assert bench.digest(Path(b['path']).parent/'src/main.cpp')==b['source']
    output=bench.CACHE/'varg-splash-audit-20261106';output.mkdir();jobs=[]
    for i,r in enumerate(raw['rows']):
        d=bench.ROOT/r['directory'];n=read(d/'native.json')
        assert bench.digest(d/'native.json')==r['native_sha256'] and n['match']['engineBuildHash']==ENGINE
        assert n['match']['mapHash']==plan['maps'][r['map']+'.map26a']
        assert not n['diagnostics']['codes'] and not any(n['diagnostics']['botFaults'].values())
        assert not sum(len(e['entries']) for e in n['events'] if e['kind']=='fuelExhausted')
        archive,=d.glob('*.repl26a');assert bench.digest(archive)==r['archive_sha256']
        replay=output/f'{i}.repl26a'
        with ZipFile(archive) as z:
            stdout=z.read('team-'+r['side'].lower()+'.stdout').replace(b'\0',b'').decode('utf8');assert stdout==r['stdout']
            with replay.open('xb') as f:f.write(z.read('replay.repl26a'))
        lines=stdout.splitlines();observed=r['observation']
        if observed:
            a,=[list(map(int,l.split()[1:])) for l in lines if l.startswith('VARG_ATTACK ')]
            camps=[list(map(int,l.split()[1:])) for l in lines if l.startswith('VARG_CAMP ')]
            assert a[0]==observed['round'] and a[1]==observed['actor'] and floating(a[8])==observed['strength']
            assert [(c[0],floating(c[4]),floating(c[5])) for c in camps]==[(c['id'],c['hp_before'],c['hp_after']) for c in observed['camps']]
            champion,=[c for c in n['champions'] if c['id']==observed['actor'] and c['team']=='team'+r['side']]
            assert champion['metrics']['monsterDamageDone']==sum(c['damage'] for c in observed['camps'])
            assert not champion['items'] and not champion['consumables']
        else:assert all(c['metrics']['monsterDamageDone']==0 for c in n['champions'])
        jobs.append({'index':i,'replay':str(replay),'replay_sha256':bench.digest(replay)})
    write(output/'jobs.json',jobs)
    subprocess.run(['node',HERE/'audit_varg_splash.mjs',output/'jobs.json',output/'replay-audit.json'],cwd=bench.ROOT,
                   env={**os.environ,'NFS_REPLAY_ENGINE':'3.0.0'},check=True)
    replay=read(output/'replay-audit.json');results=[]
    for r,t in zip(raw['rows'],replay['rows'],strict=True):
        o=r['observation'];assert not t['casts']
        assert len(t['attacks'])==int(o is not None)
        if o:
            a,=t['attacks'];assert a['actor']==o['actor'] and a['round']==o['round']
            assert [a['to']['x'],a['to']['y']]==o['target_position']
            actual={c['id']:(c['before'],c['after']) for c in a['damage']}
            expected={c['id']:(c['hp_before'],c['hp_after']) for c in o['camps'] if c['damage']>0}
            assert actual==expected,(r['map'],r['side'],actual,expected)
            results.append({'map':r['map'],'side':r['side'],'mode':r['mode'],'hits':len(actual),
                            'same_group_hits':sum(c['damage']>0 and c['group']==o['group'] for c in o['camps']),
                            'partial':o['partial'],'damage':sum(c['damage'] for c in o['camps']),
                            'all_unclipped_hits_equal_strength':all(c['damage']==min(c['hp_before'],o['strength']) for c in o['camps'])})
    write(HERE/'VARG_SPLASH_RECOUNT.json',{'pass':True,'games':len(raw['rows']),'observed':len(results),
          'unavailable':len(raw['rows'])-len(results),'raw_sha256':bench.digest(HERE/'VARG_SPLASH_OBSERVATIONS.json'),
          'replay_audit_sha256':bench.digest(output/'replay-audit.json'),'rows':results,
          'limits':'First fixtures only; duplicate modes reach same four distinct map-side cases. No isolated/overkill control observed, no complete-clear DPS or strength claim.'})
    print({'pass':True,'games':len(raw['rows']),'observed':len(results)},flush=True)
