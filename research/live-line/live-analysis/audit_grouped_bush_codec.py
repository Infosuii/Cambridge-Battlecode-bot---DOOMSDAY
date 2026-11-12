"""Reopen both180-game codec fixtures without rewriting either result."""
from hashlib import sha256
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import ENGINE,HERE,SDK_ROOT,read
from freeze_engine3_discovery import write

if __name__=='__main__':
    a=read(HERE/'GROUPED_BUSH_CODEC_PROOF.json');b=read(HERE/'GROUPED_BUSH_CODEC_IDLE_PROOF.json')
    assert a['pass'] is False and a['failed']==1 and b['pass'] and b['failed']==0
    assert a['pins']['probe']==b['pins']['unchanged_probe']
    project=SDK_ROOT/'bots/grouped-bush-codec-proof-20261106'
    assert bench.digest(project/'bot.wasm')==a['pins']['probe']
    for n,h in a['pins']['sources'].items():assert bench.digest(project/'src'/n)==h
    by={r['map']:r for r in read(HERE/'GROUPED_BUSH_CACHE_CAPACITY.json')['rows']}
    original={}
    for r in read(HERE/'LIVE111_DRAFT_CACHE_FULL_PROOF.json')['rows']:
        if r['arm']=='base':original[r['map'],r['side']]=r
    records=[];draft_matches=0;own_fuel=opponent_fuel=idle_fuel=0
    for label,report in (('active-opponent',a),('idle',b)):
        assert report['games']==len(report['rows'])==180
        for r in report['rows']:
            d=bench.ROOT/r['directory'];native=d/'native.json';assert bench.digest(native)==r['native_sha256']
            doc=read(native);assert doc['match']['engineBuildHash']==ENGINE and doc['match']['mapHash']==r['map_hash'] and doc['diagnostics']['detailedCaptureComplete']
            assert not doc['diagnostics']['codes'] and not any(doc['diagnostics']['botFaults'].values())
            archive,=d.glob('*.repl26a');assert bench.digest(archive)==r['archive_sha256']
            with ZipFile(archive) as z:stdout=z.read('team-'+r['side'].lower()+'.stdout').replace(b'\0',b'').decode('utf8')
            line,=[l for l in stdout.splitlines() if l.startswith('CODEC_PROOF ')];values=list(map(int,line.split()[1:]));assert values==r['values'] and len(values)==12
            line,=[l for l in stdout.splitlines() if l.startswith('CODEC_BYTES ')];payload=line[len('CODEC_BYTES '):]
            expected=by[r['map']];assert payload==r['encoding_hex']==expected['encoding_hex'] and values[3]==expected['components'] and values[4]==expected['encoded_bytes']
            assert values[5]==0 and values[6]==values[3] and values[7]==values[8] and values[11]==0
            events=[(e['owner'],x) for e in doc['events'] if e['kind']=='fuelExhausted' for x in e['entries']]
            assert len(events)==r['fuel']
            if label=='idle':assert not events and r['pass'];idle_fuel+=len(events)
            else:
                old=original[r['map'],r['side']];oldpath=bench.ROOT/old['directory']/'native.json';assert bench.digest(oldpath)==old['native_sha256']
                before=read(oldpath);assert doc['roster']['draft']==before['roster']['draft'];draft_matches+=1
                oldevents=[(e['owner'],x) for e in before['events'] if e['kind']=='fuelExhausted' for x in e['entries']]
                for event in events:
                    if event[0]['team']=='team'+r['side']:own_fuel+=1
                    else:opponent_fuel+=1;assert event in oldevents
            records.append(r['native_sha256']+r['archive_sha256']+sha256(stdout.encode()).hexdigest())
    assert draft_matches==180 and own_fuel==0 and opponent_fuel==1 and idle_fuel==0
    write(HERE/'GROUPED_BUSH_CODEC_RECOUNT.json',{'pass':True,'native_archives_reopened':360,'codec_ID_mask_payload_controls':360,
        'original_draft_matches':draft_matches,'original_aggregate_pass':False,'original_own_fuel':own_fuel,'original_inherited_opponent_fuel':opponent_fuel,
        'idle_aggregate_pass':True,'idle_fuel':idle_fuel,'proof_build':a['pins']['probe'],'raw_record_digest':sha256(''.join(records).encode()).hexdigest(),
        'limits':'Data structure correctness and draft identity under these fixtures only, no production-cache performance/safety/strength claim.'})
    print({'reopened':360,'codec_controls':360,'draft_matches':180,'own_fuel':0,'idle_fuel':0,'inherited_opponent_fuel':1},flush=True)
