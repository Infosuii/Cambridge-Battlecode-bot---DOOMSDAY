"""Training-only legal event-return components; no reward mixture chosen here.

Only strictly later rounds supply future returns, because command logs have no
input/substep timestamp. Past baselines exclude the current round too. These
labels must never be added to deployment actor inputs.
"""
import numpy as np
from gem_accounting import audit


def components(stats, rounds, bodies, team, horizon):
    audit(stats)
    rr=np.asarray(rounds,dtype=np.int64)
    bb=np.asarray(bodies,dtype=np.int64)
    if rr.ndim!=1 or bb.shape!=rr.shape or (rr<0).any() or horizon<=0:
        raise ValueError('return component arguments')
    if team not in ('teamA','teamB'):
        raise ValueError('unknown team')
    final=int(stats['match']['roundsStarted'])
    if (rr>final).any():
        raise ValueError('command after match')
    prefix={};team_events={'teamA':[],'teamB':[]};body_events={}
    body_ids={int(c['id']) for c in stats['champions'] if c['team']==team}
    if not set(bb.tolist())<=body_ids:
        raise ValueError('command body absent from own roster')
    for e in stats['events']:
        if e['kind']!='gemCollection':continue
        owner=e['owner'];which=owner.get('team')
        for x in e['entries']:
            if x.get('context')!='campGroup':continue
            event_round=int(x['timestamp']['round'])
            if not 0<=event_round<=final:
                raise ValueError('event outside match')
            pair=(event_round,int(x['value']))
            team_events[which].append(pair)
            if which==team:body_events.setdefault(int(owner['id']),[]).append(pair)
    for key,pairs in [('own',team_events[team]),('enemy',team_events['teamB' if team=='teamA' else 'teamA'])]+list(body_events.items()):
        pairs.sort()
        prefix[key]=(np.array([v[0] for v in pairs],dtype=np.int64),np.r_[0,np.cumsum([v[1] for v in pairs],dtype=np.int64)])
    def interval(key,start,end,left_side,right_side):
        er,sums=prefix.get(key,(np.array([],dtype=np.int64),np.array([0],dtype=np.int64)))
        return sums[np.searchsorted(er,end,side=right_side)]-sums[np.searchsorted(er,start,side=left_side)]
    end=np.minimum(rr+horizon,final)
    result={
        'future_own':interval('own',rr,end,'right','right'),
        'future_enemy':interval('enemy',rr,end,'right','right'),
        'past_own':interval('own',np.maximum(rr-horizon,0),rr,'left','left'),
        'past_enemy':interval('enemy',np.maximum(rr-horizon,0),rr,'left','left'),
        'future_body':np.zeros_like(rr),
        'future_rounds':end-rr,
        'full_horizon':rr+horizon<=final,
    }
    for bid in np.unique(bb):
        idx=np.where(bb==bid)[0]
        result['future_body'][idx]=interval(int(bid),rr[idx],end[idx],'right','right')
    if any((result[k]<0).any() for k in result if k!='full_horizon'):
        raise ValueError('negative event count or duration')
    return result
