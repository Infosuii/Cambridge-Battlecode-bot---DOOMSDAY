import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/replay'))
from review_v57_latest import value_at
rows=json.loads((ROOT/'research/v81/current_top_matches.json').read_text())
seen=set()
for r in rows:
    m=r['match'];mid=m['matchId']
    if mid in seen:continue
    seen.add(mid)
    n=json.loads((ROOT/'artifacts/local-only/v81-current'/mid/'summary.json').read_text())
    print(mid,m['map'],'rounds',n['match']['roundsStarted'],n['match']['engineVersion'])
    for t in m['teams']:
        team='team'+t['side'].upper()
        income={rnd:round(sum(value_at(x['runs'],rnd) for x in n['championTimelines'] if x['metric']=='earnedGold' and x['owner']['team']==team))
                for rnd in (100,200,300,500) if n['match']['roundsCompleted']>=rnd}
        deaths=sum(int(c['metrics']['deaths']) for c in n['champions'] if c['team']==team)
        fuel=sum(len(e['entries']) for e in n['events'] if e['kind']=='fuelExhausted' and e['owner']['team']==team)
        print(' ',t['name'],t['result'],'draft',t['draftPicks'],'income',income,'deaths',deaths,'fuel',fuel)
