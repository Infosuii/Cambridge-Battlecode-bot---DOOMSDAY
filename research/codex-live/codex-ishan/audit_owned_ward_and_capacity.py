"""Independent raw-file checks of the matched cold query and static geometry census."""
from hashlib import sha256
import re
from zipfile import ZipFile

import ablate_dev as bench
from census_static_bush_cache import encode
from engine3_pool import ENGINE,HERE,SDK_ROOT,read
from freeze_engine3_discovery import write
from turn_prefix import action_prefix

if __name__=='__main__':
    rawpath=HERE/'LIVE109_RUNTIME_TARGET_OWNEDJOINTWARD111.json';raw=read(rawpath);r,=raw['rows'];case=r['case']
    plan=read(HERE/'LIVE111_OWNED_JOINT_REGRESSION_PLAN.json');assert case==plan['case'] and raw['off']==plan['source_build']
    project=SDK_ROOT/'bots/live111-owned-joint-ward-ownedjointward111-ownedjointregression111-11801'
    assert bench.digest(project/'bot.wasm')==r['diagnostic']
    assert bench.digest(SDK_ROOT/'bots/live111-owned-joint-ward-ownedjointward111-off-11801/bot.wasm')==raw['off']
    original=SDK_ROOT/'bots/live111-owned-factorial-joint-20261106/src'
    assert (project/'src/world.cpp').read_bytes()==(original/'world.cpp').read_bytes()
    assert (project/'src/nnrec.cpp').read_bytes()==(original/'nnrec.cpp').read_bytes()
    d=bench.ROOT/r['directory'];native=read(d/'native.json')
    assert native['match']['engineBuildHash']==ENGINE and native['match']['mapHash']==case['map_hash']
    assert native['diagnostics']['detailedCaptureComplete'] and not native['diagnostics']['codes'] and not any(native['diagnostics']['botFaults'].values())
    archive,=(p for p in d.glob('*.repl26a') if p.name!='raw.repl26a')
    with ZipFile(archive) as z:
        assert z.read('replay.repl26a')==(d/'raw.repl26a').read_bytes()
        stdout=z.read('team-a.stdout').replace(b'\0',b'')
    samples=[{'mark':n.decode(),'actual_round':int(rr),'fuel':int(f),'a':int(a),'b':int(b)}
             for _,_,n,rr,f,a,b in re.findall(rb'CODEX_FINE R(\d+) T(\d+) (\w+) (\d+) (\d+) (-?\d+) (-?\d+)',stdout)]
    assert samples==r['samples'] and len(samples)<96
    oldpath=bench.ROOT/case['traces']['base']['path'];assert bench.digest(oldpath)==case['traces']['base']['sha256']
    old,turn=read(oldpath),read(d/'turn.json')
    for t in (old,turn):t['observation'].pop('input')
    assert old['observation']==turn['observation'] and action_prefix(old)==action_prefix(turn)
    fuel=[x['timestamp']['round'] for e in native['events'] if e['kind']=='fuelExhausted' and e['owner'].get('team')=='teamA' and e['owner'].get('id')==case['actor'] for x in e['entries']]
    assert fuel==r['native_rounds']==[218]
    cross,=[(a,b) for a,b in zip(samples,samples[1:]) if a['actual_round']!=b['actual_round']]
    a,b=cross;assert a['mark']=='bush_begin' and b['mark']=='bush_end' and a['b']==0 and b['a']==2
    span=100000*(b['actual_round']-a['actual_round'])+a['fuel']-b['fuel'];assert span==84473
    assert any(s['mark']=='ward_ahead_profile' for s in samples)
    updates=[s for s in samples if s['mark'] in ('ward_update_begin','ward_update_end')];assert all(s['actual_round']==219 for s in updates)
    ward_report={'pass':True,'same_own_view_action_native':True,'cold_static_query_span':span,'query_linear_index':a['a'],
          'world_and_nn_source_unchanged':True,'native_sha256':bench.digest(d/'native.json'),'archive_sha256':bench.digest(archive),'stdout_sha256':sha256(stdout).hexdigest(),'raw_sha256':bench.digest(rawpath),
          'limits':'One matched development execution; includes charged diagnostic marks, not global frequency, win effect or private graph-state equality.'}
    ward_path=HERE/'LIVE111_OWNED_WARD_RECOUNT.json'
    if ward_path.exists():assert read(ward_path)==ward_report
    else:write(ward_path,ward_report)
    rawpath=HERE/'STATIC_BUSH_CACHE_CAPACITY.json';data=read(rawpath);plan=read(HERE/'STATIC_BUSH_CACHE_CAPACITY_PLAN.json');assert data['pins']==plan
    assert len(data['rows'])==90 and len(plan['maps'])==90
    for r in data['rows']:
        assert plan['maps'][r['map']+'.map26a']==r['map_hash']
        directory=bench.ROOT/r['directory'];p=directory/'native.json';assert bench.digest(p)==r['native_sha256']
        doc=read(p);assert doc['match']['engineBuildHash']==ENGINE and doc['match']['mapHash']==r['map_hash'] and doc['diagnostics']['detailedCaptureComplete']
        assert not doc['diagnostics']['codes'] and not any(doc['diagnostics']['botFaults'].values()) and not sum(len(e['entries']) for e in doc['events'] if e['kind']=='fuelExhausted')
        archive,=directory.glob('*.repl26a');assert bench.digest(archive)==r['archive_sha256']
        with ZipFile(archive) as z:stdout=z.read('team-a.stdout').replace(b'\0',b'').decode('utf8')
        line,=[l for l in stdout.splitlines() if l.startswith('STATIC_BUSH ')]
        _,w,h,g,mis,cost,bits=line.split();assert (int(w),int(h),int(g),int(mis),int(cost),bits)==(r['width'],r['height'],r['groups'],0,r['export_and_tile_audit_cost'],r['packed_hex'])
        encoding=encode(bytes.fromhex(bits),int(w),int(h));assert all(r[k]==v for k,v in encoding.items())
        assert r['combined_bytes']==48+4*r['groups']+encoding['encoded_bytes'] and r['fits']==(r['combined_bytes']<=496)
    fits=sum(r['fits'] for r in data['rows']);assert fits==data['fits']==82 and data['unsupported']==8
    write(HERE/'STATIC_BUSH_CACHE_CAPACITY_RECOUNT.json',{'pass':True,'native_replays_reopened':90,'sdk_packing_mismatches':0,'run_encode_decode_mismatches':0,'fits':fits,'unsupported':8,'raw_sha256':bench.digest(rawpath),
          'limits':'Static data capacity only; no C++ cache implementation, performance, policy or safety claim.'})
    print({'ward_recount':True,'cold_query_span':span,'capacity_recount':True,'fits':fits,'unsupported':8},flush=True)
