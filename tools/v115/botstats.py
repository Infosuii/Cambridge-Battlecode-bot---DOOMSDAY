import json,glob,collections,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from analyse import team_metrics
agg=collections.defaultdict(collections.Counter)
for p in glob.glob(sys.argv[1]+'/*.json'):
  try: d=json.load(open(p,encoding='utf8'))
  except Exception: continue
  parts=os.path.basename(p)[:-5].split('_')
  a=parts[-1][:-1]; c,o=parts[0],parts[1]; b=o if a==c else c
  for team,bot in (('teamA',a),('teamB',b)):
    m=team_metrics(d,team); g=agg[bot]; g['n']+=1
    for k in ('fuel_out','deaths','camps','gold300','gold600','faults'): g[k]+=m[k]
for bot,g in sorted(agg.items()):
  n=g['n']; print(bot, n, {k:round(g[k]/n,2) for k in ('fuel_out','deaths','camps','gold300','gold600','faults')})
