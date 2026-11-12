"""Actual home-clear/collect transitions, baseline debug decisions, and native income."""
import json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(root/'python'),str(root/'tools/replay')]
from nfs.engine import team_stdout
from review_v57_latest import value_at
for run in sys.argv[1:]:
 print('\nRUN',run)
 for g in json.loads((root/'artifacts/evaluations/v67'/run/'games.json').read_text())['games']:
  folder=root/g['folder'];d=json.loads((folder/'audit500.json').read_text());us=0 if g['side']=='a' else 1
  print('SIDE',g['side'],'win',g['win'],'fuel',g['fuel'])
  for gi,k in enumerate(d['groups']):
   if k['gold']<600:continue
   print('GROUP',gi,'gold',k['gold'],'gems',k['gems'],'camps',len(k['camps']),'start',k['camps'][0])
   print('stateR0',d['frames'][0][2][gi])
   last=None;states=[]
   for fr in d['frames']:
    k=fr[2][gi];state=(k.get('rewardAvailable'),k.get('aliveCount'),k.get('cooldown'),k.get('captureTeam'))
    # Print actual reward/respawn changes, not each capture counter.
    q=(k.get('rewardAvailable'),k.get('respawning'))
    if q!=last:states.append((fr[0],k));last=q
   print('transitions',json.dumps(states))
  native=json.loads((folder/'summary.json').read_text())
  for rnd in (100,200,300,500):
   if native['match']['roundsCompleted']<rnd:continue
   print('GOLD',rnd,sum(value_at(x['runs'],rnd) for x in native['championTimelines'] if x['owner']['team']=='team'+g['side'].upper() and x['metric']=='earnedGold'))
  log=team_stdout(folder,g['side'])
  if log:
   print('decisions first100:')
   for line in log.splitlines():
    if line.startswith('HO R'):
     r=int(line.split()[1][1:])
     if r<=100:print(line)
    elif line.startswith('HG R'):
     r=int(line.split()[1][1:])
     if r<=100 and (' g0 ' in line or ' g1 ' in line):print(line)
