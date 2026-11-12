"""Reopen native summaries, replay output and turns for EXP232 mechanism."""
import re
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import ENGINE,HERE,read
from freeze_engine3_discovery import write
from turn_prefix import action_prefix


if __name__=='__main__':
    path=HERE/'LIVE109_RUNTIME_TARGET_FRAMEEXEC111.json'
    raw=read(path)
    result=read(HERE/'LIVE111_FRAME_EXECUTOR_MECHANISM.json')
    assert bench.digest(path)==result['raw_sha256']
    checks=[]
    for row in raw['rows']:
        case=row['case'];directory=bench.ROOT/row['directory']
        native=read(directory/'native.json')
        assert native['match']['engineBuildHash']==ENGINE
        assert native['match']['mapHash']==case['map_hash']
        assert native['diagnostics']['detailedCaptureComplete']
        assert not native['diagnostics']['codes'] and not any(native['diagnostics']['botFaults'].values())
        rounds=[x['timestamp']['round'] for e in native['events'] if e['kind']=='fuelExhausted' and e['owner']['id']==case['actor'] and e['owner']['team']=='team'+case['side'] for x in e['entries']]
        assert rounds==row['native_rounds']
        archive,=(p for p in directory.glob('*.repl26a') if p.name!='raw.repl26a')
        with ZipFile(archive) as z:
            output=z.read('team-'+case['side'].lower()+'.stdout').replace(b'\0',b'')
            assert z.read('replay.repl26a')==(directory/'raw.repl26a').read_bytes()
        samples=[{'mark':name.decode(),'actual_round':int(actual),'fuel':int(fuel),'a':int(a),'b':int(b)}
                 for r,t,name,actual,fuel,a,b in re.findall(rb'CODEX_FINE R(\d+) T(\d+) (\w+) (\d+) (\d+) (-?\d+) (-?\d+)',output)
                 if int(r)==case['round'] and int(t)==case['type']]
        assert samples==row['samples']
        turn=read(directory/'turn.json');base=read(bench.ROOT/case['traces']['base']['path'])
        assert bench.digest(directory/'turn.json')==row['turn_sha256']
        assert bench.digest(bench.ROOT/case['traces']['base']['path'])==case['traces']['base']['sha256']
        for d in (turn,base):d['observation'].pop('input')
        assert turn['observation']==base['observation']
        a,b=action_prefix(base),action_prefix(turn)
        if not case['patched']:
            assert a==b and case['round'] in rounds
        else:
            assert b[:len(a)]==a and len(b)>len(a)
            assert not any(70<=r<=72 for r in rounds)
            pubs=[s for s in samples if s['mark']=='frame_published']
            assert pubs==result['publication_marks'] and len(pubs)==1
            assert pubs[0]['a']==70 and pubs[0]['b']==1 and 70<=pubs[0]['actual_round']<=72
            ends=[s['a'] for s in samples if s['mark']=='frame_step_end']
            assert ends==list(range(5))
        checks.append({'patched':case['patched'],'native_sha256':bench.digest(directory/'native.json'),
                       'archive_sha256':bench.digest(archive),'stdout_sha256':__import__('hashlib').sha256(output).hexdigest(),
                       'initial_view_equal':True,'old_prefix_actions':len(a),'actual_prefix_actions':len(b),'native_actor_rounds':rounds})
    assert result['pass']
    write(HERE/'LIVE111_FRAME_EXECUTOR_MECHANISM_RECOUNT.json',{'pass':True,'raw_sha256':bench.digest(path),'checks':checks,
        'limitation':'One scoped matched diagnostic only; generic helper whole-prefix false is expected because normal additional actions are required. No unmeasured teacher-identity claim.'})
    print(checks,flush=True)
