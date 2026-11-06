"""EXP286: crosscheck every runtime ABI group against all old charged SDK controls."""
import os
import subprocess
from zipfile import ZipFile
import ablate_dev as bench
from engine3_pool import HERE,SDK_ROOT,ENGINE,read
from freeze_engine3_discovery import write

if __name__=='__main__':
    rawpath=HERE/'CAMP_GEOMETRY_RAW.json';raw=read(rawpath);assert len(raw['rows'])==90
    out=bench.CACHE/'runtime-camp-metadata-proof-20261106';out.mkdir();jobs=[]
    for r in raw['rows']:
        d=bench.ROOT/r['directory'];assert bench.digest(d/'native.json')==r['native_sha256']
        n=read(d/'native.json');assert n['match']['engineBuildHash']==ENGINE and n['match']['mapHash']==r['map_sha256'] and n['diagnostics']['detailedCaptureComplete']
        archive,=d.glob('*.repl26a');assert bench.digest(archive)==r['archive_sha256']
        replay=out/(r['map']+'.repl26a')
        with ZipFile(archive) as z:
            stdout=z.read('team-a.stdout').replace(b'\0',b'').decode('utf8');assert stdout==r['stdout']
            with replay.open('xb') as f:f.write(z.read('replay.repl26a'))
        jobs.append({'map':r['map'],'replay':str(replay),'replay_sha256':bench.digest(replay),'native_sha256':r['native_sha256'],'archive_sha256':r['archive_sha256']})
    plan={'games':90,'scope':'All existing SDKcensus controls, read-only runtime public ABI only','engine':ENGINE,
          'sdk_header':bench.digest(SDK_ROOT/'sdk/cpp/cambc.h'),'sdk_imports':bench.digest(SDK_ROOT/'sdk/cpp/imports.h'),
          'decoder':bench.digest(HERE/'extract_runtime_camps.mjs'),'sdk_census_sha256':bench.digest(rawpath),'jobs':jobs}
    write(HERE/'RUNTIME_CAMP_METADATA_PROOF_PLAN.json',plan);write(out/'jobs.json',jobs)
    subprocess.run(['node',HERE/'extract_runtime_camps.mjs',out/'jobs.json',out/'decoded.json'],cwd=bench.ROOT,
                   env={**os.environ,'NFS_REPLAY_ENGINE':'3.0.0'},check=True)
    decoded=read(out/'decoded.json');assert decoded['games']==90;groups=members=0
    for a,b in zip(raw['rows'],decoded['rows'],strict=True):
        assert a['map']==b['map'] and len(a['groups'])==len(b['groups']) and b['initial_snapshot_camps_match']
        expected=[{**{k:g[k] for k in ('handle','gems','gold','respawn','count')},'camps':[{k:c[k] for k in ('handle','x','y','type')} for c in g['camps']]} for g in a['groups']]
        assert expected==b['groups'],a['map'];groups+=len(expected);members+=sum(g['count'] for g in expected)
    report={'pass':True,'games':90,'groups':groups,'members':members,'plan_sha256':bench.digest(HERE/'RUNTIME_CAMP_METADATA_PROOF_PLAN.json'),
            'decoded_sha256':bench.digest(out/'decoded.json'),'decoder_sha256':bench.digest(HERE/'extract_runtime_camps.mjs'),
            'scope':'Exact public SDK/runtime membership/base rewards/respawn/type/position, no policy or strength claim.'}
    write(HERE/'RUNTIME_CAMP_METADATA_PROOF.json',report);print(report,flush=True)
