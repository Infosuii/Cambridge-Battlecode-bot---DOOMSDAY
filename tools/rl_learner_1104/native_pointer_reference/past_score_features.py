"""Training-only history features from timestamped engine events.
Only events with round STRICTLY LESS than the command's actual engine round
are used. Never use final score or same-round events as a baseline input.
"""
import numpy as np

def event_prefixes(stats):
 out={}
 for team in ('teamA','teamB'):
  events=[]
  for e in stats['events']:
   if e['kind']=='gemSubmission' and e['owner'].get('team')==team:
    for x in e['entries']:
     amount=int(x['value']);assert amount>=0
     events.append((int(x['timestamp']['round']),amount))
  events.sort();rounds=np.array([x[0] for x in events],np.int64);sums=np.concatenate(([0],np.cumsum([x[1] for x in events],dtype=np.int64)))
  final=next(int(t['submittedGems']) for t in stats['teams'] if t['team']==team)
  assert sums[-1]==final,'event accounting differs from authoritative final score'
  out[team]=(rounds,sums)
 return out

def past_total(prefix,rounds):
 er,total=prefix
 # left insertion excludes every event from the queried round.
 ix=np.searchsorted(er,rounds,side='left')
 return total[ix]

def features(stats,engine_round,team):
 rr=np.asarray(engine_round,dtype=np.int64);assert (rr>=0).all()
 pref=event_prefixes(stats);other='teamB' if team=='teamA' else 'teamA'
 own=past_total(pref[team],rr);enemy=past_total(pref[other],rr)
 own_prev=past_total(pref[team],np.maximum(rr-50,0));enemy_prev=past_total(pref[other],np.maximum(rr-50,0))
 return np.stack((rr/2000,own/1000,enemy/1000,(own-enemy)/1000,
                  (own+1)/(own+enemy+2),(own-own_prev)/100,(enemy-enemy_prev)/100,
                  ((own-own_prev)-(enemy-enemy_prev))/100),-1).astype(np.float32)
