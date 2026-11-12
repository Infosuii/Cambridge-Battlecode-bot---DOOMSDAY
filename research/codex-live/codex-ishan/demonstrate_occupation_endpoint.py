import hashlib
import os
import subprocess
import ablate_dev as bench
from engine3_pool import HERE,read
from freeze_engine3_discovery import write
from live111e_context import OUT

if __name__=='__main__':
    old=read(HERE/'LIVE111E_OCCUPATION_EPISODES.json');assert all(not e['censored'] for r in old['rows'] for e in r['episodes'])
    candidates=[r for r in old['rows'] if r['partition']=='discovery' and read(OUT/'summaries'/(r['matchId']+'.json'))['match']['roundsCompleted']>801]
    r=min(candidates,key=lambda r:hashlib.sha256(r['matchId'].encode()).hexdigest());replay=OUT/'analysis-discovery/replays'/(r['matchId']+'.repl26a')
    assert bench.digest(replay)==r['replay_sha256']
    target=bench.CACHE/'live111e-occupation-20261106/endpoint-demo.json'
    subprocess.run(['node',HERE/'demonstrate_occupation_endpoint.mjs',replay,target],cwd=bench.ROOT,env={**os.environ,'NFS_REPLAY_ENGINE':'3.0.0'},check=True)
    report={'case':r['matchId'],'replay_sha256':bench.digest(replay),'old_result_sha256':bench.digest(HERE/'LIVE111E_OCCUPATION_EPISODES.json'),
            'all73_saved_metrics_unaffected_no_open_episode':True,**read(target)}
    write(HERE/'OCCUPATION_ENDPOINT_DEMONSTRATION.json',report);print(report,flush=True)
