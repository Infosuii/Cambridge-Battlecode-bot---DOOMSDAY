"""EXP288 eight fixed discovery views; public observation, not private target inference."""
from concurrent.futures import ThreadPoolExecutor
import os
import subprocess
from zipfile import ZipFile
import ablate_dev as bench
from engine3_pool import HERE,read
from freeze_engine3_discovery import write
from live111e_context import OUT
from discovery_metrics import timeline

if __name__=='__main__':
    mid='01a1afba-9133-7dca-9f23-f94acbedf7eb'
    r,=[r for r in read(HERE/'LIVE111E_DISCOVERY_SPLIT.json')['matches'] if r['matchId']==mid];assert r['partition']=='discovery' and r['side']=='b'
    native=OUT/'summaries'/(mid+'.json');doc=read(native);replay=OUT/'analysis-discovery/replays'/(mid+'.repl26a')
    archive=OUT/'replays'/(mid+'.zip');assert bench.digest(archive)==read(HERE/'LIVE111E_REPLAY_DISCOVERY.json')['archive_sha256'][mid]
    with ZipFile(archive) as z:assert replay.read_bytes()==z.read('replay.repl26a')
    jobs=[(1,6,t) for t in (62,63,70,100)]+[(0,0,t) for t in (62,70,550,558)]
    plan={'matchId':mid,'selection':'Explicit posthoc discovery large-value lifecycle from EXP287; no confirmation fitting.',
          'native_sha256':bench.digest(native),'archive_sha256':bench.digest(archive),'replay_sha256':bench.digest(replay),
          'jobs':jobs,'trace_tool_sha256':bench.digest(HERE/'trace_turn.mjs')}
    write(HERE/'LARGE_REWARD_HANDOFF_VIEWS_PLAN.json',plan)
    out=bench.CACHE/'large-reward-handoff-views-20261106';out.mkdir()
    def run(job):
        team,actor,rnd=job;target=out/f'{team}-{actor}-{rnd}.json'
        with target.with_suffix('.log').open('xb') as log:p=subprocess.run(['node',HERE/'trace_turn.mjs',replay,str(rnd),str(team),str(actor),target],cwd=bench.ROOT,
                     env={**os.environ,'NFS_REPLAY_ENGINE':'3.0.0'},stdout=log,stderr=subprocess.STDOUT)
        if p.returncode:return {'team':team,'actor':actor,'round':rnd,'available':False,'log':str(target.with_suffix('.log'))}
        trace=read(target);unit=trace['observation']['actor'];assert unit['id']==actor and unit['team']==team
        one={'championTimelines':[x for x in doc['championTimelines'] if x['owner']['id']==actor]}
        money={k:[timeline(one,'team'+'AB'[team],k,t) for t in (rnd-1,rnd)] for k in ('gold','gems')}
        assert all(min(v)<=unit[k]<=max(v) for k,v in money.items())
        return {'team':team,'actor':actor,'round':rnd,'available':True,'trace_sha256':bench.digest(target),'native_boundaries':money,
                'observation':trace['observation'],'actions':trace['executed_actions']}
    with ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,jobs))
    result={'matchId':mid,'plan_sha256':bench.digest(HERE/'LARGE_REWARD_HANDOFF_VIEWS_PLAN.json'),'rows':rows,
            'unavailable':sum(not r['available'] for r in rows),'scope':'Observed own views, no historical private target or current-source bug claim.'}
    write(HERE/'LARGE_REWARD_HANDOFF_VIEWS.json',result);print({'requests':len(rows),'unavailable':result['unavailable']},flush=True)
