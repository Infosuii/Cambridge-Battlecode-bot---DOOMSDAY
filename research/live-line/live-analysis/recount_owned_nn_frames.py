"""Reopen all360native/replay outputs from the new in-place numerical probe."""
from collections import Counter
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import ENGINE,HERE,read
from freeze_engine3_discovery import write


if __name__=='__main__':
    path=HERE/'OWNED_NN_FRAME_NUMERIC_PROOF.json';saved=read(path)
    plan=read(HERE/'OWNED_NN_FRAME_NUMERIC_PLAN.json');out=bench.CACHE/'owned-nn-frame-numeric-20261106'
    assert len(saved['rows'])==saved['games']==plan['games']==360
    assert bench.digest(HERE/'owned_nn_frame.h')==plan['frame_header_sha256']
    seen=set();admitted=declined=0;costs=[]
    for r in saved['rows']:
        key=(r['capture'],r['map'],r['side']);assert key not in seen;seen.add(key)
        d=out/r['capture']/f"{r['map'].removesuffix('.map26a')}-{r['side']}"
        assert bench.digest(d/'native.json')==r['native_sha256']
        native=read(d/'native.json')
        assert native['match']['engineBuildHash']==ENGINE and native['match']['mapHash']==plan['maps'][r['map']]
        assert native['diagnostics']['detailedCaptureComplete'] and not native['diagnostics']['codes'] and not any(native['diagnostics']['botFaults'].values())
        archive,=d.glob('*.repl26a');assert bench.digest(archive)==r['archive_sha256']
        with ZipFile(archive) as z:stdout=z.read('team-'+r['side'].lower()+'.stdout').replace(b'\0',b'').decode('utf8')
        proofs=[list(map(int,line.split()[1:])) for line in stdout.splitlines() if line.startswith('FRAME_PROOF ')]
        assert len(proofs)==1 and proofs[0]==r['proof'] and r['available'] and r['valid'] and not r['errors']
        v=proofs[0];assert len(v)==20
        if v[16]:
            assert v[17]==15 and v[18:20]==[1,1] and v[3:6]==[1,1,1] and v[6]==0 and v[2]-v[1]>2
            admitted+=1;costs.append(v[10:16])
        else:
            assert v[17]!=15 and v[18:20]==[0,0] and v[6]==0;declined+=1
        fuel=[x['timestamp']['round'] for e in native['events'] if e['kind']=='fuelExhausted' and e['owner'].get('team')=='team'+r['side'] for x in e['entries']]
        assert len(fuel)==r['own_fuel_outs'] and fuel.count(1)==r['round1_fuel_outs']
    assert admitted==saved['admitted_frames'] and declined==saved['readiness_rejections'] and saved['pass']
    write(HERE/'OWNED_NN_FRAME_NUMERIC_RECOUNT.json',{'pass':True,'native_archive_stdout_reopened':360,
          'admitted_equal_frames':admitted,'explicit_incomplete_refusals':declined,'result_sha256':bench.digest(path),
          'copy_and_stage_maxima':[max(c[i] for c in costs) for i in range(6)],
          'limits':'Borrowed graph numerical equality only; charged diagnostic reference copy/restore/yields are not production ownership, latency or safety evidence. Probe trajectory differs from prior FrameV2.'})
    print({'pass':True,'admitted':admitted,'declined':declined},flush=True)
