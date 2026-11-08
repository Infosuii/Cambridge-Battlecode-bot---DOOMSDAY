"""EXP290 all73 unaffected original controls plus independent aggregate/source recount."""
from pathlib import Path
from statistics import median
import ablate_dev as bench
from engine3_pool import HERE,read
from freeze_engine3_discovery import write

if __name__=='__main__':
    old=read(HERE/'LIVE111E_OCCUPATION_EPISODES.json');path=HERE/'LIVE111E_OCCUPATION_R2_EPISODES.json';new=read(path)
    assert old['reports']==new['reports'] and old['rows']==new['rows'] and new['pass']
    plan=read(HERE/'LIVE111E_OCCUPATION_R2_PLAN.json');assert bench.digest(HERE/'LIVE111E_OCCUPATION_R2_PLAN.json')==new['plan_sha256']
    assert bench.digest(HERE/'reward_occupation_episodes_r2.mjs')==plan['tool_sha256']
    metadata=read(HERE/'LIVE111E_RUNTIME_CAMP_METADATA.json');assert bench.digest(HERE/'LIVE111E_RUNTIME_CAMP_METADATA.json')==plan['metadata_sha256']
    groups={r['matchId']:{g['handle']:g for g in r['groups']} for r in metadata['rows']};seen=set();reopened=0
    for p in ('discovery','control','confirm'):
        raw=read(bench.CACHE/'live111e-occupation-r2-20261106'/(p+'.json'));selected=[r for r in new['rows'] if r['partition']==p]
        assert selected==raw['rows'] and raw['games']==len(selected);reopened+=len(selected)
        for r in selected:
            assert r['matchId'] not in seen;seen.add(r['matchId'])
            replay=Path(next(j['replay'] for j in read(bench.CACHE/'live111e-occupation-r2-20261106'/(p+'-jobs.json')) if j['matchId']==r['matchId']))
            assert bench.digest(replay)==r['replay_sha256']
            ranges={}
            for e in r['episodes']:
                assert 0<=e['start']<=e['end']<=800 and e['duration']==e['end']-e['start']+1
                assert not e['censored'] and e['missing_resource_samples']==0
                assert e['base_gems']==groups[r['matchId']][e['group']]['gems'] and e['members']==groups[r['matchId']][e['group']]['count']
                assert all(e['extra_occupant_rounds'][i]==e['occupant_rounds'][i]-e['duration'] for i in (0,1))
                ranges.setdefault(e['group'],[]).append((e['start'],e['end']))
            for intervals in ranges.values():
                ordered=sorted(intervals);assert all(a[1]+1<b[0] for a,b in zip(ordered,ordered[1:]))
        episodes=[(r,e) for r in selected for e in r['episodes']];d=[e['duration'] for _,e in episodes]
        report={'games':len(selected),'affected_games':sum(bool(r['episodes']) for r in selected),'episodes':len(episodes),
                'group_rounds':sum(d),'duration_min_median_max':[min(d),median(d),max(d)] if d else None,
                'missing_resource_samples':sum(r['missing_resource_samples'] for r in selected)}
        for label in ('ours','rival'):
            report[label]={k:sum(e[k][r['ours'] if label=='ours' else 1-r['ours']] for r,e in episodes) for k in ('occupant_rounds','extra_occupant_rounds','stationary_resource_flat_no_known_action')}
        assert report==new['reports'][p]
    assert reopened==len(seen)==73
    result={'pass':True,'replays_reopened':reopened,'all73_original_metrics_unchanged':True,'raw_sha256':bench.digest(path),
            'original_sha256':bench.digest(HERE/'LIVE111E_OCCUPATION_EPISODES.json'),'reports':new['reports'],
            'limits':'Physical occupation/resource flags, no SDKcontest/private target/current-source cause or recoverable win claim.'}
    write(HERE/'LIVE111E_OCCUPATION_R2_RECOUNT.json',result);print({k:v for k,v in result.items() if k!='reports'},flush=True)
