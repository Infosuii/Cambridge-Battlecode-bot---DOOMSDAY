"""EXP265: fresh pure V2 controls on all dev terrains/both sides."""
from concurrent.futures import ThreadPoolExecutor
from shutil import copytree
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import CLI,CLI_HASH,ENGINE,HERE,SDK_ROOT,read
from freeze_engine3_discovery import write
from profile_live111_first import exact_build
from qualify_local import partition

if __name__=='__main__':
    assert read(HERE/'DRAFT_BUSH_CACHE_SMOKE_V2.json')['pass']
    old=read(HERE/'GROUPED_BUSH_CODEC_IDLE_PROOF.json');assert old['pass'];index={(r['map'],r['side']):r for r in old['rows']}
    pins=read(HERE/'GROUPED_BUSH_CODEC_PROOF_PLAN.json');base=SDK_ROOT/'bots/grouped-bush-codec-proof-20261106/src'
    assert all(bench.digest(base/n)==h for n,h in pins['sources'].items())
    output=bench.CACHE/'grouped-bush-codec-v2-proof-20261106';output.mkdir();src=output/'source';copytree(base,src)
    (src/'grouped_bush_codec.h').write_bytes((HERE/'grouped_bush_codec_v2.h').read_bytes())
    wasm=exact_build(src,SDK_ROOT/'bots/grouped-bush-codec-v2-proof-20261106',1)
    ref=SDK_ROOT/'bots/offset-aoe-idle-20261106/bot.wasm';assert bench.digest(ref)==old['pins']['idle'] and bench.digest(CLI)==CLI_HASH
    maps=sorted(partition('dev'),key=bench.digest);assert len(maps)==90
    plan={'engine':ENGINE,'cli':CLI_HASH,'probe':bench.digest(wasm),'reference':bench.digest(ref),'sources':{p.name:bench.digest(p) for p in src.iterdir() if p.is_file()},
          'maps':{p.name:bench.digest(p) for p in maps},'games':180,'baseline_sha256':bench.digest(HERE/'GROUPED_BUSH_CODEC_IDLE_PROOF.json'),'scope':'V2 numerical/mask/ID/corruption/draft controls, not production safety/strength.'}
    write(HERE/'GROUPED_BUSH_CODEC_V2_PROOF_PLAN.json',plan)
    def run(job):
        mp,side=job;prior=index[mp.stem,side];native=bench.ROOT/prior['directory']/'native.json';assert bench.digest(native)==prior['native_sha256'];before=read(native)
        d=output/f'{mp.stem}-{side}';d.mkdir();bots=(wasm,ref) if side=='A' else (ref,wasm)
        with (d/'run.log').open('xb') as log:subprocess.run([CLI,'run',*bots,'--map',mp,'--release','--fuel','100000','--json','--log-limit','100000','--statistics',d/'native.json','--out-dir',d],cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
        doc=read(d/'native.json');assert doc['match']['engineBuildHash']==ENGINE and doc['match']['mapHash']==bench.digest(mp) and doc['diagnostics']['detailedCaptureComplete']
        archive,=d.glob('*.repl26a')
        with ZipFile(archive) as z:stdout=z.read('team-'+side.lower()+'.stdout').replace(b'\0',b'').decode('utf8')
        line,=[l for l in stdout.splitlines() if l.startswith('CODEC_PROOF ')];v=list(map(int,line.split()[1:]));assert len(v)==12
        line,=[l for l in stdout.splitlines() if l.startswith('CODEC_BYTES ')];payload=line[len('CODEC_BYTES '):]
        equal=v[:9]==prior['values'][:9] and payload==prior['encoding_hex'];draft=doc['roster']['draft']==before['roster']['draft']
        errors=bool(doc['diagnostics']['codes'] or any(doc['diagnostics']['botFaults'].values()));fuel=sum(len(e['entries']) for e in doc['events'] if e['kind']=='fuelExhausted')
        return {'map':mp.stem,'side':side,'map_hash':bench.digest(mp),'values':v,'encoding_hex':payload,'numerical_equal':equal,'draft_equal':draft,'errors':errors,'fuel':fuel,
                'pass':equal and draft and not errors and not fuel and v[11]==0,'native_sha256':bench.digest(d/'native.json'),'archive_sha256':bench.digest(archive),'directory':d.relative_to(bench.ROOT).as_posix()}
    rows=[]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for r in pool.map(run,[(mp,side) for mp in maps for side in 'AB']):
            rows.append(r)
            if len(rows)%30==0:print(f'{len(rows)}/180',flush=True)
    report={'pins':plan,'games':len(rows),'pass':all(r['pass'] for r in rows),'failed':sum(not r['pass'] for r in rows),'rows':rows}
    write(HERE/'GROUPED_BUSH_CODEC_V2_PROOF.json',report);print({k:v for k,v in report.items() if k not in ('pins','rows')},flush=True)
