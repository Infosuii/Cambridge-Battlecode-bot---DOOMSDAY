"""Reopen R3native/replay/turn data,6guard fixtures and optimized graph access."""
from hashlib import sha256
from pathlib import Path
import re
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import ENGINE,HERE,read
from freeze_engine3_discovery import write
from turn_prefix import action_prefix


if __name__=='__main__':
    rawpath=HERE/'LIVE109_RUNTIME_TARGET_OWNEDEXEC111R3.json';raw=read(rawpath)
    mechanism=read(HERE/'LIVE111_OWNED_EXECUTOR_MECHANISM_R3.json')
    assert mechanism['pass'] and mechanism['raw_sha256']==bench.digest(rawpath)
    checks=[]
    for r in raw['rows']:
        case=r['case'];d=bench.ROOT/r['directory'];native=read(d/'native.json')
        assert native['match']['engineBuildHash']==ENGINE and native['match']['mapHash']==case['map_hash']
        assert native['diagnostics']['detailedCaptureComplete'] and not native['diagnostics']['codes'] and not any(native['diagnostics']['botFaults'].values())
        archive,=(p for p in d.glob('*.repl26a') if p.name!='raw.repl26a')
        with ZipFile(archive) as z:
            stdout=z.read('team-'+case['side'].lower()+'.stdout').replace(b'\0',b'')
            assert z.read('replay.repl26a')==(d/'raw.repl26a').read_bytes()
        samples=[{'mark':name.decode(),'actual_round':int(actual),'fuel':int(fuel),'a':int(a),'b':int(b)}
                 for rr,tt,name,actual,fuel,a,b in re.findall(rb'CODEX_FINE R(\d+) T(\d+) (\w+) (\d+) (\d+) (-?\d+) (-?\d+)',stdout)
                 if int(rr)==case['round'] and int(tt)==case['type']]
        assert samples==r['samples'] and len(samples)<384
        assert bench.digest(d/'turn.json')==r['turn_sha256']
        oldpath=bench.ROOT/case['traces']['base']['path'];assert bench.digest(oldpath)==case['traces']['base']['sha256']
        turn=read(d/'turn.json');old=read(oldpath)
        for t in (turn,old):t['observation'].pop('input')
        assert turn['observation']==old['observation']
        a,b=action_prefix(old),action_prefix(turn)
        fuel=[x['timestamp']['round'] for e in native['events'] if e['kind']=='fuelExhausted' and e['owner'].get('team')=='team'+case['side'] and e['owner'].get('id')==case['actor'] for x in e['entries']]
        assert fuel==r['native_rounds']
        if case['patched']:
            assert b[:len(a)]==a and len(b)>len(a) and not any(70<=n<=72 for n in fuel)
            pubs=[s for s in samples if s['mark']=='owner_published'];assert pubs==mechanism['publication_marks']
            assert len(pubs)==1 and pubs[0]['actual_round']==pubs[0]['a']==70 and pubs[0]['b']==1
            source=d.parent/'source-ownedexec111';header=(source/'codex_trace.h').read_text(encoding='utf8');body=(source/'nnrec.cpp').read_text(encoding='utf8')
            assert 'records[owner_pub_record].b=std::memcmp(owner_reference,owner_output,sizeof(owner_reference))==0;' in header
            assert 'round,cxowned.captured_at,0);' in body.replace(' ','')
            assert 'owner_pub_record=static_cast<int>(codex_trace::count)-1' in body
            assert 'std::copy(cxowned.features.begin(),cxowned.features.end(),codex_trace::owner_reference)' in body
        else:assert a==b and 70 in fuel
        checks.append({'patched':case['patched'],'native_sha256':bench.digest(d/'native.json'),'archive_sha256':bench.digest(archive),
                       'stdout_sha256':sha256(stdout).hexdigest(),'old_actions':len(a),'actual_actions':len(b),'actor_fuel_rounds':fuel})
    guards=read(HERE/'LIVE111_OWNED_GUARDS_PROOF.json');plan=read(HERE/'LIVE111_OWNED_GUARDS_PLAN.json')
    assert guards['pass'] and guards['available']==guards['games']==6
    for r in guards['rows']:
        d=bench.CACHE/'live111-owned-guards-20261106'/f"{r['map'].removesuffix('.map26a')}-{r['side']}"
        assert bench.digest(d/'native.json')==r['native_sha256']
        native=read(d/'native.json');assert native['match']['engineBuildHash']==ENGINE and native['match']['mapHash']==plan['maps'][r['map']]
        archive,=d.glob('*.repl26a');assert bench.digest(archive)==r['archive_sha256']
        with ZipFile(archive) as z:stdout=z.read('team-'+r['side'].lower()+'.stdout').replace(b'\0',b'').decode('utf8')
        assert stdout==r['stdout'];proofs=[list(map(int,s.split()[1:])) for s in stdout.splitlines() if s.startswith('OWNED_GUARDS ')]
        assert proofs==[r['proof']] and r['proof'][6:]==[1]*7
        v=r['proof'];fuel=[x['timestamp']['round'] for e in native['events'] if e['kind']=='fuelExhausted' and e['owner'].get('team')=='team'+r['side'] and e['owner'].get('id')==v[0] for x in e['entries']]
        assert fuel==r['actor_fuel_rounds'] and not any(v[3]<=n<=v[4] for n in fuel)
        assert not native['diagnostics']['codes'] and not any(native['diagnostics']['botFaults'].values())
    builds=read(HERE/'LIVE111_OWNED_EXECUTOR_BUILDS.json')
    for name,b in builds.items():
        wasm=Path(b['path']);assert bench.digest(wasm)==b['sha256']
        for n,h in b['sources'].items():assert bench.digest(wasm.parent/'src'/n)==h
    assert builds['off']['sha256']==read(HERE/'LIVE111_SOURCE_VERIFIED.json')['wasm_sha256']
    assert builds['on']['sha256']==builds['on-rebuild']['sha256']
    project=Path(builds['on']['path']).parent;commands=project/'.cambc/build-release/compile_commands.json'
    command,=[r for r in read(commands) if r['file'].endswith('nnrec.cpp')]
    prefix=command['command'].split(' -o ',1)[0];assert '"' not in prefix
    out=bench.CACHE/'live111-owned-optimized-access-20261106';out.mkdir()
    ir=out/'nnrec.ll';args=prefix.split()+['-S','-emit-llvm',command['file'],'-o',str(ir)]
    with (out/'compile.log').open('xb') as log:subprocess.run(args,cwd=out,stdout=log,stderr=subprocess.STDOUT,check=True)
    accesses={};function=None
    for line in ir.read_text(encoding='utf8').splitlines():
        match=re.match(r'define .*?@([^ (]+)\(',line)
        if match:function=match[1]
        if function and '@_ZL5nn_lv' in line:accesses[function]=accesses.get(function,0)+1
        if line=='}':function=None
    assert accesses and not any('nn_decide' in fn for fn in accesses)
    source=(project/'src/nnrec.cpp').read_text(encoding='utf8')
    for anchor in ('static void nn_run_stages(std::uint64_t floor, int rnd) {','void Bot::nn_x_refresh(int x) {'):
        assert source.count(anchor+'\n#if CODEX_OWNED_EXEC\n    if(cxowned_active)return;\n#endif')==1
    end=source[source.index('void Bot::nn_turn_end() {'):]
    assert end.index('if(cxowned_active)return;')<end.index('nn::live_camps(')<end.index('nn::live_rebuild(')
    report={'pass':True,'mechanism_recount':checks,'guard_native_archive_stdout_reopened':6,
            'clean_release':builds['on']['sha256'],'optimized_ir_sha256':bench.digest(ir),'optimized_ir_artifact':ir.relative_to(bench.ROOT).as_posix(),
            'direct_global_graph_access_functions':accesses,'nn_decide_has_no_direct_graph_access':True,
            'limits':'Current pinned configuration/source audit and charged isolated controls,not a formal all-state proof or global safety/strength. Source staged/slow writers are fenced; producer Frame pointer access is separately audited. Pre-guard fuel remains recorded.'}
    write(HERE/'LIVE111_OWNED_EXECUTOR_PREREQUISITES_RECOUNT.json',report);print(report,flush=True)
