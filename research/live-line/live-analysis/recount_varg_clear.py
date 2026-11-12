"""EXP279: every archived fixture, native damage and official replay action/HP audit."""
import os
from pathlib import Path
import subprocess
from zipfile import ZipFile
import ablate_dev as bench
from engine3_pool import HERE, SDK_ROOT, ENGINE, read
from freeze_engine3_discovery import write
from prove_varg_clear import parse

if __name__=='__main__':
    rawpath=HERE/'VARG_CLEAR_OBSERVATIONS.json';raw=read(rawpath);plan=read(HERE/'VARG_CLEAR_PLAN.json')
    assert bench.digest(HERE/'VARG_CLEAR_PLAN.json')==raw['plan_sha256']
    assert bench.digest(HERE/'varg_clear_probe.cpp')==plan['source'] and bench.digest(SDK_ROOT/'sdk/cpp/cambc.h')==plan['sdk']
    for b in raw['builds'].values():
        assert bench.digest(Path(b['path']))==b['wasm'] and bench.digest(Path(b['path']).parent/'src/main.cpp')==b['source']
    out=bench.CACHE/'varg-clear-audit-20261106';out.mkdir();jobs=[];natives=[]
    for i,r in enumerate(raw['rows']):
        directory=bench.ROOT/r['directory'];native=directory/'native.json';assert bench.digest(native)==r['native_sha256']
        doc=read(native);assert doc['match']['engineBuildHash']==ENGINE and doc['match']['mapHash']==r['map_hash']==plan['maps'][r['map']+'.map26a']
        assert doc['diagnostics']['detailedCaptureComplete'] and not doc['diagnostics']['codes'] and not any(doc['diagnostics']['botFaults'].values())
        assert not sum(len(e['entries']) for e in doc['events'] if e['kind']=='fuelExhausted')
        archive,=directory.glob('*.repl26a');assert bench.digest(archive)==r['archive_sha256']
        replay=out/f'{i}.repl26a'
        with ZipFile(archive) as z:
            stdout=z.read('team-'+r['side'].lower()+'.stdout').replace(b'\0',b'').decode('utf8');assert stdout==r['stdout'] and parse(stdout)==r['observation']
            with replay.open('xb') as f:f.write(z.read('replay.repl26a'))
        actor,=[c for c in doc['champions'] if c['id']==r['observation']['actor'] and c['team']=='team'+r['side']]
        assert not actor['items'] and not actor['consumables']
        natives.append(actor['metrics']['monsterDamageDone'])
        jobs.append({'index':i,'replay':str(replay),'replay_sha256':bench.digest(replay)})
    write(out/'jobs.json',jobs)
    subprocess.run(['node',HERE/'audit_varg_splash.mjs',out/'jobs.json',out/'replay-audit.json'],cwd=bench.ROOT,
                   env={**os.environ,'NFS_REPLAY_ENGINE':'3.0.0'},check=True)
    replay=read(out/'replay-audit.json');rows=[]
    for r,t,native_damage in zip(raw['rows'],replay['rows'],natives,strict=True):
        o=r['observation'];assert not t['casts'] and len(t['attacks'])==len(o['frames'])
        ids={c['id'] for c in o['design']};positions={c['id']:c['position'] for c in o['design']}
        total=outside=0;outside_ids=set();clipped=0;missing=0;multi=0;single=0
        for f,a in zip(o['frames'],t['attacks'],strict=True):
            assert a['actor']==o['actor'] and a['round']==f['round']
            assert [a['to']['x'],a['to']['y']]==positions[f['primary']]
            expected={c['id']:(c['before'],c['after']) for c in f['camps'] if c['before'] is not None and c['after'] is not None and c['before']>c['after']}
            actual={c['id']:(c['before'],c['after']) for c in a['damage'] if c['id'] in ids}
            assert expected==actual,(r['map'],r['side'],f['round'],expected,actual)
            for c in a['damage']:
                loss=c['before']-c['after'];total+=loss
                if c['id'] not in ids:outside+=loss;outside_ids.add(c['id'])
                if loss<f['strength']-.001:clipped+=1
            missing+=sum(c['before'] is None or c['after'] is None for c in f['camps'])
            multi+=len(actual)>1;single+=len(actual)==1
        assert abs(total-native_damage)<1e-5 and abs(total-r['snapshot_damage']-outside)<1e-5
        if o['reason']==1:assert o['frames'] and all(c['after']==0 for c in o['frames'][-1]['camps'])
        rows.append({'map':r['map'],'side':r['side'],'mode':r['mode'],'reason':o['reason'],'attacks':len(o['frames']),
                     'native_damage':native_damage,'outside_group_damage':outside,'outside_group_ids':sorted(outside_ids),
                     'clipped_hits':clipped,'missing_camp_snapshots':missing,'multi_hit_attacks':multi,'single_hit_attacks':single})
    result={'pass':True,'games':len(rows),'raw_sha256':bench.digest(rawpath),'replay_audit_sha256':bench.digest(out/'replay-audit.json'),
            'extra_verification':'Expanded fixed12 to all360 after two native/selected-group mismatches. No selection/model/outcome change.',
            'outside_group_cases':sum(r['outside_group_damage']>0 for r in rows),'missing_snapshots':sum(r['missing_camp_snapshots'] for r in rows),
            'clipped_hits':sum(r['clipped_hits'] for r in rows),'rows':rows}
    write(HERE/'VARG_CLEAR_RECOUNT.json',result);print({k:v for k,v in result.items() if k!='rows'},flush=True)
