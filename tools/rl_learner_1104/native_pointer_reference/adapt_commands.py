"""Audit ALL32 command-policy episodes; no selective omission of failed games."""
from pathlib import Path
import json,hashlib,numpy as np,torch
from command_rows import read
from qat_pointer import NativePointer
from export_query import values
r=Path(__file__).resolve().parents[1];rawroot=r/'runs/native-query-u0-flush-mac32';out=r/'native_pointer_reference/real_batch_u0';assert not out.exists();out.mkdir()
plan=json.loads((rawroot/'plan.json').read_text());runs=json.loads((rawroot/'results.json').read_text())
assert plan['mode']=='stochastic categorical' and plan['schema']=='jd-native-query-command-v2'
manifest=json.loads((r.parent.parent/'outputs/rl-execution/EVALUATION_MAP_MANIFEST.json').read_text());training={m['sha256'] for m in manifest['maps'] if m['split']=='training'}
header=r/'native-query-actor/bots/submission/src/nn_weights.h';assert hashlib.sha256(header.read_bytes()).hexdigest()==plan['native_header_sha256'];s=header.read_text()
m=NativePointer(*[values(s,n,True) for n in ['kP_target_qW_TQ','kP_target_qbQ','kP_target_kWQ','kP_target_kbQ','kP_target_EQ']]);torch.set_num_threads(2)
allrows=[];games=[];episodes=[];report=[];engines=set()
for i,run in enumerate(runs['games']):
 assert run['returncode']==0
 mp=next(z for z in plan['maps'] if z['file']==run['map']);assert mp['sha256'] in training
 stats=json.loads((rawroot/(run['directory']+'.json')).read_text());match=stats['match'];team='team'+run['side'];engines.add(match['engineBuildHash'])
 assert match['mapHash']==mp['sha256'] and match['outcome'] in ('teamA','teamB','draw')
 assert stats['diagnostics']['detailedCaptureComplete'] and not any(stats['diagnostics']['botFaults'].values())
 raw=(rawroot/run['directory']/('team-'+run['side'].lower()+'.stdout')).read_bytes();assert len(raw)<67108864
 # Unknown stdout is not silently accepted as a complete producer.
 assert all(not b.split() or b.split()[0] in (b'JNP2',b'JND1',b'CNK') for b in raw.replace(b'\0',b'').splitlines())
 rows,assoc=read(raw);assert assoc['producer_markers_complete'] and not assoc['logging_round_overruns']
 for row in rows:assert row['temperature']==plan['temperature'] and row['bonus']==plan['v92_bonus']
 replay=0.;native_error=0.
 with torch.no_grad():
  for start in range(0,len(rows),1024):
   z=rows[start:start+1024];logits,_=m(torch.from_numpy(np.stack([v['h1'] for v in z])),torch.from_numpy(np.stack([v['camps'] for v in z])),torch.from_numpy(np.stack([v['present'] for v in z])))
   present=np.concatenate((np.stack([v['present'] for v in z]),np.ones((len(z),1),bool)),-1)
   native_error=max(native_error,float(np.max(np.abs((logits.numpy()-np.stack([v['native_logits'] for v in z]))[present]))))
   score=logits.double();ix=torch.arange(len(z));vs=torch.tensor([v['vslot'] for v in z]);score[ix,vs]+=plan['v92_bonus']
   score=(score/plan['temperature']).masked_fill(~torch.from_numpy(np.stack([v['valid'] for v in z])),-torch.inf)
   lp=score.log_softmax(-1)[ix,torch.tensor([v['action'] for v in z])]
   replay=max(replay,float((lp-torch.tensor([v['old_logp'] for v in z],dtype=torch.double)).abs().max()))
 assert native_error==0 and replay<2e-4
 outcome=0 if match['outcome']=='draw' else 1 if match['outcome']==team else -1
 ep=dict(key='|'.join([mp['sha256'],run['side'],run['opponent'],plan['candidate_wasm_sha256'],match['seed']]),map_sha256=mp['sha256'],family=mp['family'],opponent=run['opponent'],side=run['side'],status='terminated',complete_command_producer=True,outcome=outcome,rows=len(rows))
 episodes.append(ep);allrows+=rows;games += [i]*len(rows)
 fuel=sum(len(e['entries']) for e in stats['events'] if e['kind']=='fuelExhausted' and e['owner'].get('team')==team)
 report.append(dict(map=mp['file'],opponent=run['opponent'],side=run['side'],outcome=outcome,rows=len(rows),departures=sum(v['chosen']!=v['reference'] for v in rows),reported_skips=assoc['reported_skips'],min_completion_fuel=assoc['min_fuel_at_completion_marker'],own_fuel_outs=fuel,max_logp_error=replay))
assert len(engines)==1 and len(episodes)==32 and len({e['key'] for e in episodes})==32
arrays={k:np.stack([z[k] for z in allrows]) for k in ('h1','camps','present','valid')}
arrays.update({k:np.array([z[k] for z in allrows],dtype=np.int64) for k in ('vslot','action','body','index','round','engine_round')})
arrays['old_logp']=np.array([z['old_logp'] for z in allrows],np.float64);arrays['game']=np.array(games,np.int64)
np.savez(out/'data.npz',**arrays)
meta=dict(schema=plan['schema'],mode=plan['mode'],data_origin='engine',temperature=plan['temperature'],v92_bonus=plan['v92_bonus'],policy_seed=plan['policy_seed'],native_header_sha256=plan['native_header_sha256'],wasm_sha256=plan['candidate_wasm_sha256'],source_tree_sha256=plan['source_tree_sha256'],engine_sha256=next(iter(engines)),data_sha256=hashlib.sha256((out/'data.npz').read_bytes()).hexdigest(),episodes=episodes,action_semantics=plan['action_semantics'])
(out/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
rep=dict(scope='REAL native-query target-command stochastic collection; initial policy, no learned strength claim',games=32,families=len({e['family'] for e in episodes}),rows=len(allrows),departures=sum(x['departures'] for x in report),wins=sum(x['outcome']==1 for x in report),losses=sum(x['outcome']==-1 for x in report),draws=sum(x['outcome']==0 for x in report),max_logp_error=max(x['max_logp_error'] for x in report),native_logits_bit_exact=True,all_command_completion_markers_matched=True,collection_wall_seconds=runs['wall_seconds'],games_detail=report)
(out/'collection_report.json').write_text(json.dumps(rep,indent=2)+'\n');(r.parent.parent/'outputs/rl-execution/NATIVE_QUERY_COLLECTION.json').write_text(json.dumps(rep,indent=2)+'\n');print(json.dumps({k:v for k,v in rep.items() if k!='games_detail'},indent=2))
