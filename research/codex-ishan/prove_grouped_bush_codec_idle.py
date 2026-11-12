"""EXP262: identical C++ correctness probe, all dev/both sides, neutral opponent."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import CLI,CLI_HASH,ENGINE,HERE,SDK_ROOT,read
from freeze_engine3_discovery import write
from qualify_local import partition

if __name__=='__main__':
    oldpath=HERE/'GROUPED_BUSH_CODEC_PROOF.json';old=read(oldpath);assert old['pass'] is False and old['failed']==1
    assert all(r['python_encoding_equal'] and r['draft_equal'] and not r['errors'] and r['values'][5]==0 and r['values'][7]==r['values'][8] and r['values'][11]==0 for r in old['rows'])
    index={(r['map'],r['side']):r for r in old['rows']};assert len(index)==180
    failed,=[r for r in old['rows'] if not r['pass']]
    native=read(bench.ROOT/failed['directory']/'native.json')
    events=[(e['owner'],x) for e in native['events'] if e['kind']=='fuelExhausted' for x in e['entries']]
    assert len(events)==1 and events[0][0]['team']!='team'+failed['side']
    controls=read(HERE/'LIVE111_DRAFT_CACHE_FULL_PROOF.json')['rows']
    control,=[r for r in controls if r['arm']=='base' and r['map']==failed['map'] and r['side']==failed['side']]
    path=bench.ROOT/control['directory']/'native.json';assert bench.digest(path)==control['native_sha256']
    before=read(path);baseline_events=[(e['owner'],x) for e in before['events'] if e['kind']=='fuelExhausted' for x in e['entries']]
    assert events[0] in baseline_events
    wasm=SDK_ROOT/'bots/grouped-bush-codec-proof-20261106/bot.wasm';assert bench.digest(wasm)==old['pins']['probe']
    for n,h in old['pins']['sources'].items():assert bench.digest(wasm.parent/'src'/n)==h
    ref=SDK_ROOT/'bots/offset-aoe-idle-20261106/bot.wasm';assert bench.digest(ref)==read(HERE/'OFFSET_AOE_ACTION_PROOF.json')['builds']['idle']
    assert bench.digest(CLI)==CLI_HASH
    maps=sorted(partition('dev'),key=bench.digest);assert {p.name:bench.digest(p) for p in maps}==old['pins']['maps']
    output=bench.CACHE/'grouped-bush-codec-idle-proof-20261106';output.mkdir()
    pins={'original_report_sha256':bench.digest(oldpath),'unchanged_probe':bench.digest(wasm),'idle':bench.digest(ref),'engine':ENGINE,'cli':CLI_HASH,
          'maps':old['pins']['maps'],'games':180,'original_draft_parity':180,'inherited_opponent_event':events[0],
          'scope':'Repaired isolated numerical fixture, not strength/production safety or different-opponent draft parity.'}
    write(HERE/'GROUPED_BUSH_CODEC_IDLE_PROOF_PLAN.json',pins)
    def run(job):
        mp,side=job;d=output/f'{mp.stem}-{side}';d.mkdir();bots=(wasm,ref) if side=='A' else (ref,wasm)
        with (d/'run.log').open('xb') as log:subprocess.run([CLI,'run',*bots,'--map',mp,'--release','--fuel','100000','--json','--log-limit','100000','--statistics',d/'native.json','--out-dir',d],cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
        doc=read(d/'native.json');assert doc['match']['engineBuildHash']==ENGINE and doc['match']['mapHash']==bench.digest(mp) and doc['diagnostics']['detailedCaptureComplete']
        archive,=d.glob('*.repl26a')
        with ZipFile(archive) as z:stdout=z.read('team-'+side.lower()+'.stdout').replace(b'\0',b'').decode('utf8')
        line,=[l for l in stdout.splitlines() if l.startswith('CODEC_PROOF ')];v=list(map(int,line.split()[1:]));assert len(v)==12
        line,=[l for l in stdout.splitlines() if l.startswith('CODEC_BYTES ')];payload=line[len('CODEC_BYTES '):]
        prior=index[mp.stem,side];numerical=v[:9]==prior['values'][:9] and payload==prior['encoding_hex']
        errors=bool(doc['diagnostics']['codes'] or any(doc['diagnostics']['botFaults'].values()));fuel=sum(len(e['entries']) for e in doc['events'] if e['kind']=='fuelExhausted')
        return {'map':mp.stem,'side':side,'map_hash':bench.digest(mp),'values':v,'encoding_hex':payload,'numerical_equal':numerical,
                'errors':errors,'fuel':fuel,'pass':numerical and v[11]==0 and not errors and not fuel,
                'native_sha256':bench.digest(d/'native.json'),'archive_sha256':bench.digest(archive),'directory':d.relative_to(bench.ROOT).as_posix()}
    rows=[]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for r in pool.map(run,[(mp,side) for mp in maps for side in 'AB']):
            rows.append(r)
            if len(rows)%30==0:print(f'{len(rows)}/180',flush=True)
    report={'pins':pins,'games':len(rows),'pass':all(r['pass'] for r in rows),'failed':sum(not r['pass'] for r in rows),
            'max_full_reference_fixture_cost':max(r['values'][10] for r in rows),'rows':rows}
    write(HERE/'GROUPED_BUSH_CODEC_IDLE_PROOF.json',report);print({k:v for k,v in report.items() if k not in ('pins','rows')},flush=True)
