"""Reopen all V3 numerical, schema and steady100k raw controls; retain old failures."""
from hashlib import sha256
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import ENGINE,HERE,SDK_ROOT,read
from freeze_engine3_discovery import write

if __name__=='__main__':
    definitions=[('pure','GROUPED_BUSH_CODEC_V3_PROOF.json','grouped-bush-codec-v3-proof-20261106'),
                 ('cache','DRAFT_BUSH_CACHE_FULL_V3.json','draft-bush-cache-smoke-v3-probe-20261106'),
                 ('steady','DRAFT_BUSH_CACHE_STEADY_V3_R2.json','draft-bush-cache-steady-v3-r2-probe-20261106')]
    controls={(r['map'],r['side']):r for r in read(HERE/'GROUPED_BUSH_CODEC_IDLE_PROOF.json')['rows']}
    records=[];stats={};pins={}
    for label,name,project_name in definitions:
        path=HERE/name;report=read(path);assert report['pass']
        project=SDK_ROOT/'bots'/project_name;assert bench.digest(project/'bot.wasm')==report['pins']['probe']
        for n,h in report['pins']['sources'].items():assert bench.digest(project/'src'/n)==h
        assert bench.digest(project/'src/grouped_bush_codec.h')==bench.digest(HERE/'grouped_bush_codec_v3.h')
        pins[label]=bench.digest(path);stats[label]={'games':len(report['rows']),'native_fuel':0,'draft_equal':0}
        for r in report['rows']:
            directory=bench.ROOT/r['directory'];native=directory/'native.json';assert bench.digest(native)==r['native_sha256']
            doc=read(native);assert doc['match']['engineBuildHash']==ENGINE and doc['match']['mapHash']==r['map_hash'] and doc['diagnostics']['detailedCaptureComplete']
            assert not doc['diagnostics']['codes'] and not any(doc['diagnostics']['botFaults'].values())
            fuel=sum(len(e['entries']) for e in doc['events'] if e['kind']=='fuelExhausted');assert fuel==r['fuel']==0
            archive,=directory.glob('*.repl26a');assert bench.digest(archive)==r['archive_sha256']
            with ZipFile(archive) as z:stdout=z.read('team-'+r['side'].lower()+'.stdout').replace(b'\0',b'').decode('utf8')
            if label=='pure':
                line,=[l for l in stdout.splitlines() if l.startswith('CODEC_PROOF ')];v=list(map(int,line.split()[1:]));assert v==r['values']
                line,=[l for l in stdout.splitlines() if l.startswith('CODEC_BYTES ')];assert line[len('CODEC_BYTES '):]==r['encoding_hex']
                assert r['numerical_equal'] and v[5]==v[11]==0 and v[6]==v[3] and v[7]==v[8]
            else:
                line,=[l for l in stdout.splitlines() if l.startswith('DRAFT_BUSH_PROOF ')];draft=list(map(int,line.split()[1:]));assert draft==r['draft'] and draft[5]==0
                line,=[l for l in stdout.splitlines() if l.startswith('PLAY_BUSH_PROOF ')];play=list(map(int,line.split()[1:]));assert play==r['play'] and play[4]==0
                assert play[0]==play[1]==int(draft[3]==1) and draft[3] in (1,2,3)
                if draft[3]==1:assert draft[6]==draft[7]==12
            prior=controls[r['map'],r['side']];p=bench.ROOT/prior['directory']/'native.json';assert bench.digest(p)==prior['native_sha256']
            before=read(p);assert before['roster']['draft']==doc['roster']['draft'];stats[label]['draft_equal']+=1
            records.append(r['native_sha256']+r['archive_sha256']+sha256(stdout.encode()).hexdigest())
        assert stats[label]['games']==(8 if label=='steady' else 180)
    full=read(HERE/'DRAFT_BUSH_CACHE_FULL_V3.json');assert (full['admitted'],full['budget_refused'],full['space_refused'])==(168,6,6)
    source=(SDK_ROOT/'bots/draft-bush-cache-steady-v3-r2-probe-20261106/src/main.cpp').read_text(encoding='utf8')
    assert source.count('bc::end_turn();const auto r0=bc::round_number();')==1
    assert source.count('const auto call_elapsed=bc::round_number()-r0;bc::end_turn();')==1
    assert 'cost=100000ull*(bc::round_number()-call_round)+f-bc::fuel_remaining();' in source
    # Recount all original incomplete steady archives, with every actor's report retained.
    oldplan=read(HERE/'DRAFT_BUSH_CACHE_STEADY_V3_PLAN.json');old=[]
    oldroot=bench.CACHE/'draft-bush-cache-steady-v3-20261106'
    for mp,maphash in oldplan['maps'].items():
        for side in 'AB':
            directory=oldroot/f'{mp.removesuffix(".map26a")}-{side}';doc=read(directory/'native.json')
            assert doc['match']['engineBuildHash']==ENGINE and doc['match']['mapHash']==maphash and doc['diagnostics']['detailedCaptureComplete']
            archive,=directory.glob('*.repl26a')
            with ZipFile(archive) as z:stdout=z.read('team-'+side.lower()+'.stdout').replace(b'\0',b'').decode('utf8')
            reports=[list(map(int,l.split()[1:])) for l in stdout.splitlines() if l.startswith('PLAY_BUSH_PROOF ')]
            fuel=[(e['owner'],x['timestamp']) for e in doc['events'] if e['kind']=='fuelExhausted' for x in e['entries']]
            old.append({'map':mp,'side':side,'reports':reports,'fuel':fuel,'native_sha256':bench.digest(directory/'native.json'),'archive_sha256':bench.digest(archive),'stdout_sha256':sha256(stdout.encode()).hexdigest()})
    assert len(old)==8 and sum(len(r['reports'])==6 for r in old)==2 and sum(len(r['fuel']) for r in old)==12
    write(HERE/'DRAFT_BUSH_CACHE_STEADY_V3_ATTEMPT_RECOUNT.json',{'pass':False,'reason':'Original immediate-output fixture/reader did not complete; report records and all native events retained.','rows':old})
    write(HERE/'DRAFT_BUSH_CACHE_V3_PREREQUISITES_RECOUNT.json',{'pass':True,'raw_result_hashes':pins,'stats':stats,
        'admitted':168,'budget_refused':6,'space_refused':6,'source_codec':bench.digest(HERE/'grouped_bush_codec_v3.h'),
        'record_digest':sha256(''.join(records).encode()).hexdigest(),'normal100k_boundary_and_deferred_charged_output_verified':True,
        'limits':'These are isolated data/codec/schema/normal-budget correctness controls, not clean release or full-game safety/strength. Older prototype and immediate-output failures remain.'})
    print({'pass':True,'stats':stats,'native_archives_reopened':368,'old_incomplete_steady_archives_retained':8},flush=True)
