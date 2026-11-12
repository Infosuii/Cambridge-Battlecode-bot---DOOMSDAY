"""Small independent statistical fixtures, not match/performance evidence."""
import json, random
from pathlib import Path

def assess(rows, expected):
 seen=set()
 for r in rows:
  if r['cell'] in seen:raise ValueError('duplicate paired cell')
  seen.add(r['cell'])
 if seen!=set(expected) or any(r['candidate_status']!='ok' or r['reference_status']!='ok' for r in rows):
  return {'status':'INCOMPLETE','paired_delta':None,'ci95':None}
 fam={}
 for r in rows:
  assert r['candidate_score'] in (0,.5,1) and r['reference_score'] in (0,.5,1)
  fam.setdefault(r['family'],[]).append(r['candidate_score']-r['reference_score'])
 ds=[d for v in fam.values() for d in v]
 keys=sorted(fam);rng=random.Random(1104);stats=[]
 for _ in range(4000):
  sample=[fam[rng.choice(keys)] for _ in keys]
  stats.append(sum(map(sum,sample))/sum(map(len,sample)))
 stats.sort()
 return {'status':'COMPLETE','paired_delta':sum(ds)/len(ds),'ci95':[stats[100],stats[3899]],
  'family_balanced_delta':sum(sum(v)/len(v) for v in fam.values())/len(fam),
  'families':len(fam),'cells':len(ds),'enough_families_for_proposed_confirmation_gate':len(fam)>=20}

def row(i,f,c,b,status='ok'):
 return {'cell':f'cell-{i}','family':f,'candidate_score':c,'reference_score':b,
         'candidate_status':status,'reference_status':'ok'}

cases=[]
def add(name,rows,expected=None):
 schedule=expected if expected is not None else [r['cell'] for r in rows]
 result=assess(rows,schedule);cases.append({'case':name,'expected_cells':schedule,'rows':rows,'expected':result});return result

x=add('identical policies', [row(i,'A' if i<2 else 'B',s,s) for i,s in enumerate([1,0,.5,1])])
assert x['paired_delta']==0 and x['ci95']==[0,0]
x=add('uniform gain, too few families for confirmation',[row(i,'A' if i<2 else 'B',1,0) for i in range(4)])
assert x['paired_delta']==1 and x['ci95']==[1,1] and not x['enough_families_for_proposed_confirmation_gate']
x=add('unequal family sizes change weighting',[row(i,'A' if i<2 else 'B',1 if i<2 else 0,0 if i<2 else 1) for i in range(8)])
assert x['paired_delta']==-.5 and x['family_balanced_delta']==0
x=add('candidate failure cannot be dropped',[row(0,'A',1,0),row(1,'B',0,1,'failed')])
assert x['status']=='INCOMPLETE' and x['paired_delta'] is None
x=add('missing scheduled cell',[row(0,'A',1,0)],['cell-0','cell-1'])
assert x['status']=='INCOMPLETE'
try:assess([row(0,'A',1,0),row(0,'A',1,0)],['cell-0'])
except ValueError:pass
else:raise AssertionError('duplicate must fail')
cases.append({'case':'duplicate paired cell','rows':[row(0,'A',1,0),row(0,'A',1,0)],'expected_cells':['cell-0'],'expected_error':'duplicate paired cell'})
out={'kind':'synthetic paired-statistics fixtures NOT performance evidence',
 'key_contract':'Production cell IDs must encode pinned map hash, side, opponent hash, engine/build/fuel settings and requested RNG variant. Candidate/reference artifact identities remain separately pinned.',
 'estimand':'cell-weighted paired candidate-minus-reference score; equal-family-weighted mean also reported explicitly',
 'bootstrap':'whole families, paired differences, seed1104,reps4000, percentile indices100 and3899',
 'scope':'Correct pair accounting is necessary, not proof of independent held-out families or ladder superiority.', 'cases':cases}
p=Path(__file__).resolve().parent.parent.parent/'outputs/rl-execution/PAIRED_EVALUATION_FIXTURES.json'
p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'cases':len(cases),'checks':'PASS','unequal_family_case':cases[2]['expected']}))
