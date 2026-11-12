"""Observed command persistence, not downstream executed-action duration."""
from pathlib import Path
import json,time,numpy as np
from upper_rows import read
r=Path(__file__).resolve().parents[1]
folders=[r/'runs/native-upper-u0-mac32-02']+[r/f'runs/native-upper-continuation-01/cycle{i}/raw' for i in range(1,5)]
rows_count=0;departures=0;next_gaps=[];spans=[];next_same=0;next_reference=0;censored=0;games=0;start=time.monotonic()
for folder in folders:
 runs=json.loads((folder/'results.json').read_text())
 for game in runs['games']:
  assert game['returncode']==0
  rows,assoc=read((folder/game['directory']/('team-'+game['side'].lower()+'.stdout')).read_bytes());assert assoc['producer_markers_complete'] and not assoc['logging_round_overruns'];games+=1;rows_count+=len(rows)
  for body in {x['body'] for x in rows}:
   z=[x for x in rows if x['body']==body];change=[None]*len(z);future=None
   for i in range(len(z)-2,-1,-1):
    if z[i+1]['chosen']!=z[i]['chosen']:future=i+1
    change[i]=future
   for i,x in enumerate(z):
    if x['chosen']==x['reference']:continue
    departures+=1
    if i+1==len(z):censored+=1;continue
    following=z[i+1];next_gaps.append(following['engine_round']-x['engine_round'])
    next_same+=following['chosen']==x['chosen'];next_reference+=following['chosen']==following['reference']
    if change[i] is not None:spans.append(z[change[i]]['engine_round']-x['engine_round'])
    else:censored+=1
 def quant(v):return dict(zip(['min','p25','median','p75','p90','max'],map(float,np.quantile(v,[0,.25,.5,.75,.9,1]))))
 print(folder.name,games,flush=True)
report=dict(scope='Observed persistence among logged target commands; not physical action execution or causal attribution',games=games,rows=rows_count,departures=departures,departure_next_logged_gap_rounds=quant(next_gaps),observed_until_different_command_rounds=quant(spans),next_logged_command_same_group_fraction=next_same/len(next_gaps),next_logged_command_is_its_own_reference_fraction=next_reference/len(next_gaps),right_censored_departures=censored,wall_seconds=time.monotonic()-start,limitations=['Frozen downstream executor may cancel/reassign before the next log; these are not measured executed option durations.','A command may target the same physical group while game state/task changes.','Only related local opponents/training families, no ladder claim.','No proof that longer commitment improves performance; this identifies an experimental question.'])
(r.parent.parent/'outputs/rl-execution/TARGET_COMMAND_PERSISTENCE.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
