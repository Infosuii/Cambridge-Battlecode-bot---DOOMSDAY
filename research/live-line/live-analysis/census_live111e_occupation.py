"""EXP289 fixed corpus occupation episodes, normal offline official replay accounting."""
import os
import subprocess
from statistics import median
from pathlib import Path
import ablate_dev as bench
from engine3_pool import HERE,read
from freeze_engine3_discovery import write
from live111e_context import OUT

if __name__=='__main__':
    meta=read(HERE/'LIVE111E_RUNTIME_CAMP_METADATA.json');frozen={r['matchId']:r for r in read(HERE/'LIVE111E_DISCOVERY_SPLIT.json')['matches']}
    jobs=[]
    for r in meta['rows']:
        row=frozen[r['matchId']];replay=OUT/f'analysis-{r["partition"]}'/'replays'/(r['matchId']+'.repl26a')
        assert bench.digest(replay)==r['replay_sha256']
        jobs.append({**r,'replay':str(replay),'ours':int(row['side']=='b'),'opponent':row['opponent']})
    plan={'games':73,'until':800,'definition':'EXP289 first champion-phase rewardAvailable+both team physical spawn-tile presence; resource-flat/known action flags explicit',
          'tool_sha256':bench.digest(HERE/'reward_occupation_episodes.mjs'),'metadata_sha256':bench.digest(HERE/'LIVE111E_RUNTIME_CAMP_METADATA.json'),
          'groups':{p:sum(j['partition']==p for j in jobs) for p in ('discovery','control','confirm')}}
    write(HERE/'LIVE111E_OCCUPATION_PLAN.json',plan)
    out=bench.CACHE/'live111e-occupation-20261106';out.mkdir();rows=[]
    for partition in ('discovery','control','confirm'):
        selected=[j for j in jobs if j['partition']==partition];input=out/(partition+'-jobs.json');target=out/(partition+'.json');write(input,selected)
        subprocess.run(['node',HERE/'reward_occupation_episodes.mjs',input,target],cwd=bench.ROOT,env={**os.environ,'NFS_REPLAY_ENGINE':'3.0.0'},check=True)
        rows+=read(target)['rows']
    reports={}
    for p in ('discovery','control','confirm'):
        selected=[r for r in rows if r['partition']==p];es=[(r,e) for r in selected for e in r['episodes']];durations=[e['duration'] for _,e in es]
        report={'games':len(selected),'affected_games':sum(bool(r['episodes']) for r in selected),'episodes':len(es),'group_rounds':sum(durations),
                'duration_min_median_max':[min(durations),median(durations),max(durations)] if durations else None,
                'missing_resource_samples':sum(r['missing_resource_samples'] for r in selected)}
        for label in ('ours','rival'):
            report[label]={k:sum(e[k][r['ours'] if label=='ours' else 1-r['ours']] for r,e in es) for k in ('occupant_rounds','extra_occupant_rounds','stationary_resource_flat_no_known_action')}
        reports[p]=report
    result={'pass':True,'plan_sha256':bench.digest(HERE/'LIVE111E_OCCUPATION_PLAN.json'),'reports':reports,'rows':rows,
            'limits':'Exposed outcome-selected source-inferred corpus. First snapshots miss intra-round changes; flat/no-known-action is not a recoverable idle/win estimate. No SDKcontest query or private decision reconstruction.'}
    write(HERE/'LIVE111E_OCCUPATION_EPISODES.json',result);print(reports,flush=True)
