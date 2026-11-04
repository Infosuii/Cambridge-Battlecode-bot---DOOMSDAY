from pathlib import Path
import hashlib,json,numpy as np
r=Path(__file__).resolve().parent;p=r/'runs/base-budget-profile-01'
results=json.loads((p/'results.json').read_text());names=['play_turn','heuristic_score','neural_lazy','neural_decide','neural_background','farm']
allrows=[];cells=[]
for c in results['cells']:
 raw=(p/c['directory']/('team-a.stdout' if c['side']=='A' else 'team-b.stdout')).read_bytes()
 rows=[]
 for line in raw.replace(b'\0',b'\n').splitlines():
  if line.startswith(b'JDBP '):
   a=list(map(int,line.split()[1:]));assert len(a)==7
   round_,body,section,calls,used,interrupted,maximum=a
   rows.append(dict(round=round_,body=body,section=section,calls=calls,raw_fuel=used,interrupted=interrupted,max_complete_call_fuel=maximum))
 latest={}
 for row in rows:
  key=(row['body'],row['section'])
  if key in latest:assert row['calls']>=latest[key]['calls']
  latest[key]=row
 stats=json.loads((p/(c['directory']+'.json')).read_text())
 assert not any(stats['diagnostics']['botFaults'].values())
 assert stats['diagnostics']['detailedCaptureComplete']
 sections={}
 for i,name in enumerate(names):
  x=[v for v in latest.values() if v['section']==i]
  calls=sum(v['calls'] for v in x);interrupted=sum(v['interrupted'] for v in x);fuel=sum(v['raw_fuel'] for v in x)
  sections[name]=dict(calls=calls,interrupted_calls=interrupted,completed_call_raw_fuel=fuel,
   mean_completed_call_fuel=fuel/(calls-interrupted) if calls>interrupted else None)
 cells.append(dict(map=c['map'],side=c['side'],profiled_bodies=len({v['body'] for v in latest.values()}),
  last_report_round_range=[min(v['round'] for v in latest.values()),max(v['round'] for v in latest.values())],sections=sections))
 allrows.extend(latest.values())
summary={}
for i,name in enumerate(names):
 x=[v for v in allrows if v['section']==i];calls=sum(v['calls'] for v in x);intr=sum(v['interrupted'] for v in x);fuel=sum(v['raw_fuel'] for v in x)
 summary[name]=dict(calls=calls,interrupted_calls=intr,completed_call_raw_fuel=fuel,mean_completed_call_fuel=fuel/(calls-intr) if calls>intr else None,
  per_game_mean_p10_p50_p90=list(map(float,np.quantile([c['sections'][name]['mean_completed_call_fuel'] for c in cells if c['sections'][name]['mean_completed_call_fuel'] is not None],[.1,.5,.9]))))
turns=summary['play_turn']['calls'];heuristic=sum(c['sections']['heuristic_score']['completed_call_raw_fuel'] for c in cells)
report=dict(scope='Instrumented actual RELEASE games at100k fuel, TRAINING maps only; diagnostic costs, not strength evidence',
 candidate_wasm_sha256=hashlib.sha256((r/'base-budget-profile/compiled.wasm').read_bytes()).hexdigest(),
 source_ref='8cccf446b0371d04f6c627e5a5a882ba286dd629 isolated source; CLNA defines removed; jd raw-fuel scopes added',
 games=len(cells),wall_seconds=results['wall_seconds'],summary=summary,
 heuristic_completed_fuel_per_observed_play_turn=heuristic/turns,cells=cells,
 limitations=['Instrumentation/reporting changes fuel timing and trajectories; no uninstrumented strength inference.',
 'Nested inclusive scopes: farm contains heuristic and neural lazy work; do not sum them as separate costs.',
 'play_turn excludes main-loop nn_turn_end background and diagnostic report writes.',
 'Reported counters are last periodic snapshots for each body, not all terminal calls. Dead/short-lived bodies without a report can be absent.',
 'Interrupted calls omitted from measured fuel but counted separately; completed-call means have survivor bias.',
 'Profiler uses raw remaining fuel rather than existing native virtual fuel+nn_spent accounting.',
 'Savings require a trained replacement: removing a scorer changes reference, support and state; this report is not a deletion recommendation.'])
out=r.parent.parent/'outputs/rl-execution/BASE_BUDGET_PROFILE.json';out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['cells','limitations']},indent=2))
