"""Correct the contact-turn metric and inventory native early income from existing ladder games."""
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/replay'))
from review_v57_latest import value_at

rows = json.loads((ROOT / 'research/v75/duel_v74.json').read_text())
stats = defaultdict(Counter)
def cheb(a,b): return max(abs(a[1]-b[1]), abs(a[2]-b[2]))
for r in rows:
    folder = ROOT / 'artifacts/local-only/duel-v74' / r['matchId']
    tl = json.loads((folder / 'timeline.json').read_text())
    team = {c['id']:c['team'] for c in tl['champs']}
    us = 0 if r['side']=='a' else 1
    for fr in tl['frames']:
        for x in fr[1]:
            if not x[5] or len(x)<10: continue
            if not any(o[5] and team[o[0]]!=team[x[0]] and cheb(x,o)<=4 for o in fr[1]): continue
            sh='us' if team[x[0]]==us else 'them'
            for key in (sh, f'{sh}-{r["result"]}'):
                k=stats[key]; acts={a[0] for a in x[9]}
                k['contact']+=1
                k['strict_move_only']+=acts=={4}
                k['move_without_attack_or_cast']+=4 in acts and not (acts & {5,6})
                k['cast']+=6 in acts
                k['attack']+=5 in acts
                k['recall_or_cancel']+=bool(acts & {11,16})
    native=json.loads((folder/'summary.json').read_text(encoding='utf-8-sig'))
    for rnd in (100,200,300,500):
        if native['match']['roundsCompleted']<rnd: continue
        for sh,t in [('us','team'+r['side'].upper()),('them','team'+('B' if r['side']=='a' else 'A'))]:
            k=stats[f'{sh}-{r["result"]}']
            k[f'nR{rnd}']+=1
            k[f'goldR{rnd}']+=sum(value_at(x['runs'],rnd) for x in native['championTimelines']
                                  if x['owner']['team']==t and x['metric']=='earnedGold')
for sh,k in stats.items():
    n=max(1,k['contact'])
    print(sh, 'contact', k['contact'], 'old move-only', round(100*k['strict_move_only']/n,1),
          'corrected move without attack/cast', round(100*k['move_without_attack_or_cast']/n,1),
          'cast',round(100*k['cast']/n,1),'recall/cancel',round(100*k['recall_or_cancel']/n,1))
    for rnd in (100,200,300,500):
        if k[f'nR{rnd}']: print(' ',rnd,'native gold',round(k[f'goldR{rnd}']/k[f'nR{rnd}'],1), 'n',k[f'nR{rnd}'])
(ROOT/'research/v81/corrected_contact.json').write_text(json.dumps(stats,indent=1)+'\n')
