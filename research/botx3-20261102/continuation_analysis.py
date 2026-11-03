"""Paired, map-clustered exploratory analysis; never reruns matches."""
from pathlib import Path
import json,random
BASE=Path(__file__).resolve().parent
names=['team-contract','team-commitments','team-fieldready','team-bank-regression','team-bank-holdout','expiry-regression','draft-paths-v1','draft-paths-v2','draft-paths-regression','draft-paths-v3','draft-paths-v3-regression','draft-paths-holdout']
result={}
def win(r):return int(r['outcome']=='team'+r['side'])
for name in names:
 folder=BASE/name;p=folder/'rows.json'
 if not (folder/'summary.json').exists():continue
 rows=json.loads(p.read_text());arms={}
 for r in rows:arms.setdefault(r['arm'],{})[(r['map_sha256'],r['opponent_sha256'],r['side'])]=r
 control='control' if 'control' in arms else 'transport' if 'transport' in arms else 'never'
 comparisons={}
 for arm,rr in arms.items():
  if arm in ['off','parent',control] or control not in arms:continue
  for ref in [control,'off']:
   paired=[(r,arms[ref][k]) for k,r in rr.items() if k in arms[ref]]
   if not paired:continue
   maps={}
   for r,c in paired:maps.setdefault(r['map'],[]).append(win(r)-win(c))
   rng=random.Random(20261102);keys=list(maps);boot=[]
   for _ in range(2000):
    sample=[maps[rng.choice(keys)] for _ in keys];boot.append(sum(sum(x) for x in sample)/sum(map(len,sample)))
   boot.sort()
   comparisons[f'{arm}-vs-{ref}']=dict(pairs=len(paired),gained=sum(win(r)>win(c) for r,c in paired),lost=sum(win(r)<win(c) for r,c in paired),delta_wins=sum(win(r)-win(c) for r,c in paired),exploratory_map_bootstrap95_pp=[100*boot[50],100*boot[1949]],by_map={k:sum(v) for k,v in maps.items()},by_opponent={o:sum(win(r)-win(c) for r,c in paired if r['opponent']==o) for o in sorted({r['opponent'] for r,c in paired})})
 result[name]=dict(summary=json.loads((folder/'summary.json').read_text()),comparisons=comparisons)
(BASE/'CONTINUATION_ANALYSIS.json').write_text(json.dumps(result,indent=2)+'\n')
for name,v in result.items():
 print(name,{k:(q['delta_wins'],q['exploratory_map_bootstrap95_pp']) for k,q in v['comparisons'].items()},flush=True)
