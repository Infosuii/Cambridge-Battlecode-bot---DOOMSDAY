"""Descriptive departure/nearby-reference collection comparison; no causal claim."""
from pathlib import Path
import json
import time
import numpy as np
from upper_rows import read
from gem_accounting import audit

root = Path(__file__).resolve().parents[1]
folders = [root/'runs/native-upper-u0-mac32-02'] + [root/f'runs/native-upper-continuation-01/cycle{i}/raw' for i in range(1,5)]
horizons = (50,150,300)
manifest = json.loads((root.parent.parent/'outputs/rl-execution/EVALUATION_MAP_MANIFEST.json').read_text())
training = {x['sha256'] for x in manifest['maps'] if x['split']=='training'}
details=[];started=time.monotonic();total_rows=0;total_departures=0
for folder in folders:
    plan=json.loads((folder/'plan.json').read_text())
    results=json.loads((folder/'results.json').read_text())
    assert len(results['games'])==32 and plan['schema']=='jd-native-upper-command-v3'
    for game in results['games']:
        assert game['returncode']==0
        mp=next(x for x in plan['maps'] if x['file']==game['map'])
        assert mp['sha256'] in training
        stats=json.loads((folder/(game['directory']+'.json')).read_text())
        audit(stats)
        assert stats['match']['mapHash']==mp['sha256']
        rows,assoc=read((folder/game['directory']/('team-'+game['side'].lower()+'.stdout')).read_bytes())
        assert assoc['producer_markers_complete'] and not assoc['logging_round_overruns']
        team='team'+game['side'];end=stats['match']['roundsCompleted']
        events={};all_events=[]
        for e in stats['events']:
            if e['kind']!='gemCollection' or e['owner'].get('team')!=team:continue
            for x in e['entries']:
                if x['context']!='campGroup':continue
                pair=int(x['timestamp']['round']),int(x['value'])
                events.setdefault(int(e['owner']['id']),[]).append(pair);all_events.append(pair)
        def future(pairs,rr,H):
            pairs=sorted(pairs)
            er=np.array([v[0] for v in pairs],dtype=np.int64)
            sums=np.concatenate(([0],np.cumsum([v[1] for v in pairs],dtype=np.int64)))
            # Strictly later rounds: logs lack per-input timestamp, so no same-round attribution.
            return sums[np.searchsorted(er,rr+H,side='right')]-sums[np.searchsorted(er,rr,side='right')]
        body=np.array([x['body'] for x in rows]);rr=np.array([x['engine_round'] for x in rows])
        departure=np.array([x['chosen']!=x['reference'] for x in rows]);total_rows+=len(rows);total_departures+=int(departure.sum())
        for H in horizons:
            matches=[];teams=[];count=0;eligible_departures=0
            team_return=future(all_events,rr,H)
            for bid in np.unique(body):
                ix=np.where(body==bid)[0];r=rr[ix];dep=departure[ix]
                ret=future(events.get(int(bid),[]),r,H)
                ref=np.where((~dep)&(r+H<=end))[0]
                for j in np.where(dep&(r+H<=end))[0]:
                    eligible_departures+=1
                    near=ref[np.abs(r[ref]-r[j])<=20]
                    if not len(near):continue
                    matches.append(float(ret[j]-ret[near].mean()))
                    teams.append(float(team_return[ix[j]]-team_return[ix[near]].mean()))
                    count+=1
            details.append(dict(family=mp['family'],map=mp['file'],side=game['side'],opponent=game['opponent'],
                                cycle=folder.parent.name if folder.name=='raw' else folder.name,horizon=H,
                                eligible_departures=eligible_departures,matched_departures=count,
                                body_difference=float(np.mean(matches)) if matches else None,
                                team_difference=float(np.mean(teams)) if teams else None))
    print(folder.name,total_rows,flush=True)
summary={};rng=np.random.default_rng(110722)
for H in horizons:
    subset=[x for x in details if x['horizon']==H];fam=sorted({x['family'] for x in subset})
    result={}
    for key in ['body_difference','team_difference']:
        means=np.array([np.mean([x[key] for x in subset if x['family']==f and x[key] is not None]) for f in fam])
        assert np.isfinite(means).all()
        boot=means[rng.integers(0,len(means),(10000,len(means)))].mean(1)
        result[key]=dict(equal_family_mean=float(means.mean()),family_bootstrap_95=np.quantile(boot,[.025,.975]).tolist())
    summary[H]=dict(families=len(fam),eligible_departures=sum(x['eligible_departures'] for x in subset),
                    matched_departures=sum(x['matched_departures'] for x in subset),**result)
report=dict(scope='Descriptive SAME-body/game departures versus reference decisions within20 rounds; not causal or a decisive RL falsifier',
            games=160,rows=total_rows,departures=total_departures,horizons=summary,wall_seconds=time.monotonic()-started,
            return_definition='CampGroup gemCollection in strictly later rounds (r,r+H], exclude commands without full H follow-up',
            weighting='Within-game mean per departure then equal game means within family, equal families. References may be reused; uncertainty clusters whole family.',
            limitations=['Current command can be cancelled/overridden by frozen downstream executor or later commands.',
                         'Nearby decisions occur in different states; matching does not control state confounding.',
                         'Windows overlap heavily; decisions are not independent samples.',
                         'A null difference does not establish no action-conditional learnable effect or falsify sequential policy improvement.',
                         'No inverse-propensity weighting: this comparison is descriptive, not an off-policy estimator.',
                         'Only training families and related v92/native opponents; no reserved maps used.'],games_detail=details)
out=root.parent.parent/'outputs/rl-execution/COLLECTION_DEPARTURE_DIAGNOSTIC.json'
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='games_detail'},indent=2))
