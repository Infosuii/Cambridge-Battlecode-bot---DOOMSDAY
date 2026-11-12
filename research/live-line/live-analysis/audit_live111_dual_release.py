"""Complete both registered mechanism controls and draft parity on the rejected dual release."""
import os
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import HERE,read
from freeze_engine3_discovery import write
from turn_prefix import action_prefix


if __name__=='__main__':
    label='dual-draft-cache-release'
    result=read(HERE/'LIVE111_DUAL_DRAFT_CACHE_RELEASE_LARGE.json')
    root=bench.CACHE/('live111-'+label)
    drafts=[]
    for a,b in result['pairs']:
        original=bench.CACHE/'live111-large-development'/a['opponent']/f"{a['map']}-{a['side']}-stock111/native.json"
        candidate=root/b['opponent']/f"{b['map']}-{b['side']}-{label}/native.json"
        x,y=read(original),read(candidate)
        assert all(x['match'][k]==y['match'][k] for k in ('engineBuildHash','mapHash','seed'))
        drafts.append({'map':a['map'],'side':a['side'],'opponent':a['opponent'],'equal':x['roster']['draft']==y['roster']['draft']})
    case=read(HERE/'LIVE111_CACHE_REMAINING_R1_PLAN.json')['case']
    directory=root/case['opponent']/f"{case['map']}-{case['side']}-{label}"
    (archive,)=directory.glob('*.repl26a');replay=directory/'raw.repl26a'
    with ZipFile(archive) as z:
        with replay.open('xb') as f:f.write(z.read('replay.repl26a'))
    turn=directory/'turn.json'
    subprocess.run(['node',HERE/'trace_turn.mjs',replay,'1','0',str(case['actor']),turn],cwd=bench.ROOT,env={**os.environ,'NFS_REPLAY_ENGINE':'3.0.0'},check=True)
    before,after=read(bench.ROOT/case['traces']['base']['path']),read(turn)
    for d in (before,after):d['observation'].pop('input')
    native=read(directory/'native.json')
    r1=any(e['kind']=='fuelExhausted' and e['owner'].get('team')=='teamA' and e['owner'].get('id')==case['actor'] and any(t['timestamp']['round']==1 for t in e['entries']) for e in native['events'])
    mechanism={'case':case,'same_own_view':before['observation']==after['observation'],'same_pre_end_actions':action_prefix(before)==action_prefix(after),'actor_round1_removed':not r1,'turn_sha256':bench.digest(turn),'native_sha256':bench.digest(directory/'native.json')}
    report={'n_drafts':len(drafts),'drafts_equal':sum(r['equal'] for r in drafts),'travel_mechanism':mechanism,'safety_pass':result['pass'],'pass':result['pass'] and all(r['equal'] for r in drafts) and all(mechanism[k] for k in ('same_own_view','same_pre_end_actions','actor_round1_removed')),'drafts':drafts}
    write(HERE/'LIVE111_DUAL_DRAFT_CACHE_RELEASE_CONTROLS.json',report)
    print({k:v for k,v in report.items() if k!='drafts'},flush=True)
