"""EXP242 frozen repeated-position/zero-productivity census; no intervention."""
from collections import Counter,defaultdict
import os
import subprocess

import ablate_dev as bench
from discovery_metrics import timeline
from engine3_pool import ENGINE,HERE,read
from freeze_engine3_discovery import write
from freeze_live111d_discovery import OUT,PREFIX


def windows(raw,native):
    by=defaultdict(list)
    for s in raw['samples']:by[s['actor']].append(s)
    combat={r['key'] for r in raw['combat_actions']}
    fuel=defaultdict(set)
    for e in native['events']:
        if e['kind']=='fuelExhausted':fuel[e['owner']['id']].update(x['timestamp']['round'] for x in e['entries'])
    all_windows=[];excluded=Counter()
    for actor,samples in by.items():
        samples.sort(key=lambda r:r['round'])
        stats={'championTimelines':[s for s in native['championTimelines'] if s['owner']['id']==actor]}
        team='team'+'AB'[samples[0]['team']]
        found=[]
        for i in range(len(samples)):
            for period in range(2,9):
                chunk=samples[i:i+3*period]
                if len(chunk)<3*period:continue
                first,last=chunk[0],chunk[-1]
                if last['round']-first['round']!=len(chunk)-1 or not all(r['alive'] for r in chunk):continue
                points=[(r['x'],r['y']) for r in chunk]
                if len(set(points))<2 or any(p!=points[j%period] for j,p in enumerate(points)):continue
                if any(abs(r['hp']-first['hp'])>.01 or r['gold']!=first['gold'] or r['gems']!=first['gems'] for r in chunk):continue
                if any(f"{r['round']}:{actor}" in combat for r in chunk):
                    excluded['basic_or_cast_windows']+=1;continue
                if any(first['round']-1<=r<=last['round']+1 for r in fuel[actor]):
                    excluded['fuel_adjacent_windows']+=1;continue
                metrics=('earnedGold','collectedGems','submittedGems','monsterDamageDone','championDamageDone')
                if any(timeline(stats,team,m,first['round']-1)!=timeline(stats,team,m,last['round']) for m in metrics):
                    excluded['native_productivity_windows']+=1;continue
                found.append({'actor':actor,'team':samples[0]['team'],'type':samples[0]['type'],
                              'start':first['round'],'end':last['round'],'periods':[period],
                              'first_position':[first['x'],first['y']],'hp':first['hp'],'gold':first['gold'],'gems':first['gems']})
                break
        merged=[]
        for w in sorted(found,key=lambda w:(w['start'],w['end'])):
            if merged and w['start']<=merged[-1]['end']:
                merged[-1]['end']=max(merged[-1]['end'],w['end'])
                merged[-1]['periods']=sorted(set(merged[-1]['periods']+w['periods']))
            else:merged.append(w)
        all_windows.extend(merged)
    return all_windows,dict(excluded)


if __name__=='__main__':
    split=read(HERE/f'{PREFIX}_DISCOVERY_SPLIT.json')['matches']
    output=OUT/'motion-cycles';output.mkdir()
    write(HERE/f'{PREFIX}_MOTION_CYCLES_PLAN.json',{'experiment':242,'split_sha256':bench.digest(HERE/f'{PREFIX}_DISCOVERY_SPLIT.json'),
          'definition':'Period2..8,three repeated nonconstant cycles,consecutive alive owner turns throughR800,HP.01/gold/gems flat,no basic/cast,zero native income/submission/damage,no adjacent actor fuel; overlapping windows merged.',
          'source_hashes':{n:bench.digest(HERE/n) for n in ('extract_owner_paths.mjs','census_live111d_motion_cycles.py')},
          'games':len(split),'order':['discovery','control','confirm'],'scope':'Narrow descriptive repeated-motion pattern; no private objective/cause/policy claim.'})
    trace=read(HERE/f'{PREFIX}_TURNING_VIEWS_R2.json')['rows'];rows=[]
    for part in ('discovery','control','confirm'):
        selected=[r for r in split if r['partition']==part]
        jobs=[]
        for r in selected:
            replay=OUT/f'analysis-{part}/replays'/f"{r['matchId']}.repl26a"
            assert replay.exists()
            jobs.append({'matchId':r['matchId'],'replay':str(replay),'output':str(output/(r['matchId']+'.json'))})
        jobpath=output/(part+'-jobs.json');write(jobpath,jobs)
        subprocess.run(['node',HERE/'extract_owner_paths.mjs',jobpath],cwd=bench.ROOT,
                       env={**os.environ,'NFS_REPLAY_ENGINE':'3.0.0'},check=True)
        for r in selected:
            path=output/(r['matchId']+'.json');raw=read(path);native=read(OUT/'summaries'/(r['matchId']+'.json'))
            assert native['match']['engineBuildHash']==ENGINE and native['diagnostics']['detailedCaptureComplete']
            for old in trace:
                if old['matchId']==r['matchId'] and old['available']:
                    actor=old['actor'];sample,=[s for s in raw['samples'] if s['actor']==actor['id'] and s['round']==old['round']]
                    assert (sample['x'],sample['y'])==(actor['pos']['x'],actor['pos']['y'])
                    assert all(abs(sample[k]-actor[k])<.001 for k in ('hp','gold','gems'))
            detected,excluded=windows(raw,native)
            rows.append({k:r[k] for k in ('matchId','group','opponent','partition','side') }|{
                'raw_path':path.relative_to(bench.ROOT).as_posix(),'raw_sha256':bench.digest(path),
                'native_sha256':bench.digest(OUT/'summaries'/(r['matchId']+'.json')),
                'samples':len(raw['samples']),'windows':detected,'excluded':excluded})
        print(part,'census verified',flush=True)
    reports={}
    for part in ('discovery','control','confirm'):
        selected=[r for r in rows if r['partition']==part];report={'n':len(selected),'groups':len({r['group'] for r in selected})}
        for label in ('ours','rival'):
            def selected_windows(r):
                ours=int(r['side'].upper()=='B');team=ours if label=='ours' else 1-ours
                return [w for w in r['windows'] if w['team']==team]
            report[label]={'games_with_pattern':sum(bool(selected_windows(r)) for r in selected),
                           'groups_with_pattern':len({r['group'] for r in selected if selected_windows(r)}),
                           'merged_windows':sum(len(selected_windows(r)) for r in selected),
                           'actor_rounds':sum(w['end']-w['start']+1 for r in selected for w in selected_windows(r))}
        reports[part]=report
    write(HERE/f'{PREFIX}_MOTION_CYCLES.json',{'scope':'No causal loop/target/alternative action inference; productive/fuel windows excluded,not silently counted as zero.',
          'plan_sha256':bench.digest(HERE/f'{PREFIX}_MOTION_CYCLES_PLAN.json'),'reports':reports,'rows':rows})
    print(reports,flush=True)
