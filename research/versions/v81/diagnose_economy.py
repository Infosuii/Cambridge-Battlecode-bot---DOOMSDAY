"""Fixed-time native economy comparison; idle-opponent wins are never strength evidence."""
from collections import defaultdict
import json
from pathlib import Path
import statistics as st
import sys

root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'tools/replay'))
from review_v57_latest import value_at
def games(run):
    return {(g['map'],g['side'],g['seed']):(g,json.loads((root/g['folder']/'summary.json').read_text()))
            for g in json.loads((root/'artifacts/evaluations/v67'/run/'games.json').read_text())['games']}
c,b=map(games,sys.argv[1:3]);assert set(c)==set(b)
print(sys.argv[1],'vs',sys.argv[2],len(c),'matched games')
for rnd in (100,200,300):
    for metric in ('earnedGold','collectedGems','monsterDamageDone','deaths'):
        values=[];by=defaultdict(list)
        for key in c:
            if min(c[key][1]['match']['roundsCompleted'],b[key][1]['match']['roundsCompleted'])<rnd:continue
            v=[]
            for table in (c,b):
                g,n=table[key];team='team'+g['side'].upper()
                v.append(sum(value_at(x['runs'],rnd) for x in n['championTimelines'] if x['metric']==metric and x['owner']['team']==team))
            values.append(v);by[key[0]].append(v[0]-v[1])
        print(rnd,metric,'candidate/base',round(st.mean(v[0] for v in values),1),round(st.mean(v[1] for v in values),1),
              'delta',round(st.mean(v[0]-v[1] for v in values),1),'n',len(values),
              'map deltas',{m:round(st.mean(v),1) for m,v in by.items()})
