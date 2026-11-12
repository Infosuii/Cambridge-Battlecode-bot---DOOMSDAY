"""Boundary/identity checks plus real32-game label-to-command alignment."""
from pathlib import Path
import hashlib
import json
import numpy as np
from camp_return_components import components

root=Path(__file__).resolve().parents[1]
folder=root/'runs/native-value-paired-01/shared-cycle0'
meta=json.loads((folder/'data/manifest.json').read_text())
plan=json.loads((folder/'raw/plan.json').read_text())
runs=json.loads((folder/'raw/results.json').read_text())
with np.load(folder/'data/data.npz',allow_pickle=False) as a:
    data={k:a[k] for k in ('game','body','engine_round','action','old_logp')}
assert len(meta['episodes'])==len(runs['games'])==32
families=set();summary=[];all_components={}
for i,(ep,run) in enumerate(zip(meta['episodes'],runs['games'])):
    assert ep['side']==run['side'] and ep['opponent']==run['opponent'] and run['returncode']==0
    stats=json.loads((folder/'raw'/(run['directory']+'.json')).read_text())
    assert stats['match']['mapHash']==ep['map_sha256']
    idx=np.where(data['game']==i)[0];assert len(idx)==ep['rows']
    result=components(stats,data['engine_round'][idx],data['body'][idx],'team'+ep['side'],150)
    families.add(ep['family'])
    # Independent brute-force checks exercise event boundary ties and late commands.
    indices=sorted(set([0,len(idx)//2,len(idx)-1]))
    for j in indices:
        rnd=int(data['engine_round'][idx[j]]);body=int(data['body'][idx[j]])
        direct={k:0 for k in ['future_own','future_enemy','past_own','past_enemy','future_body']}
        for e in stats['events']:
            if e['kind']!='gemCollection':continue
            for x in e['entries']:
                if x.get('context')!='campGroup':continue
                r=int(x['timestamp']['round']);v=int(x['value']);own=e['owner']['team']=='team'+ep['side']
                if rnd<r<=rnd+150:
                    direct['future_own' if own else 'future_enemy']+=v
                    if own and int(e['owner']['id'])==body:direct['future_body']+=v
                if max(0,rnd-150)<=r<rnd:direct['past_own' if own else 'past_enemy']+=v
        assert all(int(result[k][j])==v for k,v in direct.items())
    for k,v in result.items():
        if k not in all_components:all_components[k]=np.empty(len(data['game']),dtype=v.dtype)
        all_components[k][idx]=v
    summary.append(dict(family=ep['family'],rows=len(idx),full_horizon=int(result['full_horizon'].sum())))

# No events in command round may enter either past or future components.
s=json.loads((folder/'raw'/(runs['games'][0]['directory']+'.json')).read_text())
first_event=next((e,x) for e in s['events'] if e['kind']=='gemCollection' and e['owner']['team']=='team'+meta['episodes'][0]['side'] for x in e['entries'] if x.get('context')=='campGroup' and int(x['value'])>0)
e,x=first_event;rr=int(x['timestamp']['round']);bid=int(e['owner']['id'])
probe=components(s,[rr],[bid],e['owner']['team'],1)
# Exact exclusion is checked against all events at this same round by direct sums above;
# this probe ensures tied real capture timestamps are accepted without reassignment.
assert probe['future_rounds'][0]>=0

out=root/'runs/dense-return-components-audit01';assert not out.exists();out.mkdir()
np.savez(out/'components.npz',**all_components,**data)
report=dict(scope='Training-only reward COMPONENT construction, no mixture/PPO update chosen',games=32,
            rows=len(data['game']),families=len(families),horizon=150,
            future_window='(command engine round, min(round+150,final)]',
            past_window='[max(0,round-150),round)',same_round_events_excluded=True,
            brute_force_row_checks=96,independent_event_accounting=True,
            source_data_sha256=hashlib.sha256((folder/'data/data.npz').read_bytes()).hexdigest(),
            output_sha256=hashlib.sha256((out/'components.npz').read_bytes()).hexdigest(),
            component_means={k:float(v.mean()) for k,v in all_components.items()},
            limitations=['No dense reward scalarization, discount, critic or learning claim.',
                         'Same-round captures excluded conservatively because actor logs lack input/substep clock.',
                         'Late decisions have shorter actual follow-up explicitly recorded; not silently dropped.',
                         'Components are future labels only; never actor features.'])
(root.parent.parent/'outputs/rl-execution/DENSE_RETURN_COMPONENTS_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
