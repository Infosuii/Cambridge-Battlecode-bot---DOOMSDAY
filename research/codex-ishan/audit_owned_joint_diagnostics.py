"""Reopen rejected-joint diagnostic evidence and freshly reproduce exact control."""
import re
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import CLI,CLI_HASH,ENGINE,HERE,SDK_ROOT,one,read
from freeze_engine3_discovery import write
from qualify_local import partition
from turn_prefix import action_prefix

if __name__=='__main__':
    plan=read(HERE/'LIVE111_OWNED_JOINT_REGRESSION_PLAN.json');case=plan['case']
    identity=read(HERE/'LIVE111-OWNED-FACTORIAL-JOINT-20261106_SOURCE_VERIFIED.json')
    original=SDK_ROOT/'bots/live111-owned-factorial-joint-20261106/src'
    assert plan['source_build']==identity['wasm_sha256']
    assert bench.digest(CLI)==CLI_HASH
    assert all(bench.digest(original/n)==h for n,h in identity['source_file_hashes'].items())
    records=[]
    specs=[('ownedjointregression111r2','live111-owned-joint-target',{'common.h','main.cpp','bot.cpp','nnrec.cpp'}),
           ('ownedjointminimal111','live111-owned-joint-minimal',{'common.h','main.cpp'}),
           ('ownedjointcoarse111','live111-owned-joint-coarse',{'common.h','main.cpp','bot.cpp'}),
           ('ownedjointtail111','live111-owned-joint-tail',{'common.h','main.cpp','bot.cpp','bot.h'})]
    for label,prefix,allowed in specs:
        path=HERE/f'LIVE109_RUNTIME_TARGET_{label.upper()}.json'
        if not path.exists():continue
        raw=read(path);assert raw['off']==plan['source_build'] and raw['engine']==ENGINE
        off=SDK_ROOT/'bots'/f'{prefix}-{label}-off-11801/bot.wasm'
        assert bench.digest(off)==raw['off']
        for row in raw['rows']:
            assert row['case']==case
            wasm=SDK_ROOT/'bots'/f'{prefix}-{label}-{case["stage"]}-11801/bot.wasm'
            assert bench.digest(wasm)==row['diagnostic']
            source=wasm.parent/'src';changed={n for n,h in identity['source_file_hashes'].items() if bench.digest(source/n)!=h}
            assert changed<=allowed
            if label!='ownedjointregression111r2':assert (source/'nnrec.cpp').read_bytes()==(original/'nnrec.cpp').read_bytes()
            directory=bench.ROOT/row['directory'];doc=read(directory/'native.json')
            assert doc['match']['engineBuildHash']==ENGINE and doc['match']['mapHash']==case['map_hash']
            assert doc['diagnostics']['detailedCaptureComplete'] and not doc['diagnostics']['codes'] and not any(doc['diagnostics']['botFaults'].values())
            archive,=(p for p in directory.glob('*.repl26a') if p.name!='raw.repl26a')
            with ZipFile(archive) as z:
                assert z.read('replay.repl26a')==(directory/'raw.repl26a').read_bytes()
                stdout=z.read('team-'+case['side'].lower()+'.stdout').replace(b'\0',b'')
            samples=[{'mark':n.decode(),'actual_round':int(r),'fuel':int(f),'a':int(a),'b':int(b)}
                     for rr,tt,n,r,f,a,b in re.findall(rb'CODEX_FINE R(\d+) T(\d+) (\w+) (\d+) (\d+) (-?\d+) (-?\d+)',stdout)
                     if int(rr)==case['round'] and int(tt)==case['type']]
            assert samples==row['samples']
            oldpath=bench.ROOT/case['traces']['base']['path'];turnpath=directory/'turn.json'
            assert bench.digest(oldpath)==case['traces']['base']['sha256'] and bench.digest(turnpath)==row['turn_sha256']
            old,new=read(oldpath),read(turnpath)
            for t in (old,new):t['observation'].pop('input')
            same_view=old['observation']==new['observation'];same_prefix=action_prefix(old)==action_prefix(new)
            fuel=[x['timestamp']['round'] for e in doc['events'] if e['kind']=='fuelExhausted' and e['owner'].get('id')==case['actor'] and e['owner'].get('team')=='team'+case['side'] for x in e['entries']]
            assert (same_view,same_prefix,case['round'] in fuel)==(row['same_own_view'],row['same_action_prefix'],row['same_native_actor_round'])
            assert fuel==row['native_rounds']
            records.append({'label':label,'matched':same_view and same_prefix and case['round'] in fuel,
                'same_turn_bytes':turnpath.read_bytes()==oldpath.read_bytes(),'native_sha256':bench.digest(directory/'native.json'),
                'archive_sha256':bench.digest(archive),'stdout_sha256':sha256(stdout).hexdigest(),
                'source_hashes':{p.name:bench.digest(p) for p in source.iterdir() if p.is_file()},
                'diagnostic_wasm':row['diagnostic'],'changed_original_files':sorted(changed),'result_sha256':bench.digest(path)})
    assert any(r['label']=='ownedjointminimal111' and r['matched'] and r['same_turn_bytes'] for r in records)
    out=bench.CACHE/'live111-owned-joint-diagnostic-control-20261106';out.mkdir()
    maps={p.stem:p for p in partition('dev')};mp=maps[case['map']]
    reference=bench.CACHE/bench.OPPS[case['opponent']][0]
    assert bench.digest(mp)==case['map_hash'] and bench.digest(reference)==bench.OPPS[case['opponent']][1]
    off=SDK_ROOT/'bots/live111-owned-joint-minimal-ownedjointminimal111-off-11801/bot.wasm'
    actual=one(('exact-joint',mp,case['side'],off,reference),output=out,opponent=case['opponent'])
    frozen=read(HERE/'LIVE111_OWNED_FACTORIAL_RESULT.json')['rows']
    old,=[r for r in frozen if all(r[k]==case[k] for k in ('map','side','opponent')) and r['arm']=='joint']
    assert all(actual[k]==old[k] for k in ('map_hash','score','fuel_outs','round1_fuel_outs','faults','opponent_faults','diagnostic_codes','engine_seed'))
    fresh=out/f'{mp.stem}-{case["side"]}-exact-joint/native.json'
    doc=read(fresh);before=read(bench.ROOT/old['native_path']);assert bench.digest(bench.ROOT/old['native_path'])==plan['joint_native']
    assert doc==before
    report={'pass':True,'limits':'Matched recorded own-view/action/native-event checks, not a proof of private graph-state identity or a strength result.',
            'records':records,'exact_control_whole_native_equal':True,'control_native_sha256':bench.digest(fresh),
            'control_summary':actual,'source_build':plan['source_build']}
    write(HERE/'LIVE111_OWNED_JOINT_DIAGNOSTIC_RECOUNT.json',report)
    print({'pass':True,'matched':[(r['label'],r['matched']) for r in records],'whole_control_native_equal':True},flush=True)
