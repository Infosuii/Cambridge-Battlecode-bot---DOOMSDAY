"""Shared feature definition for fitted intent policy; runtime mirrors these legal observations."""
import math

NAMES=['hp_fraction','hp','max_hp','strength','focus','range','gems','round','ready0','ready1','nearest',
       'allies6','ally_hp6','ally_strength6','enemies6','enemy_hp6','enemy_strength6','ranged_enemies6','weakest_fraction','local_hp_ratio']
NAMES += [f'type_{i}' for i in range(13)]

def features(t):
    dist=lambda e:max(abs(t['x']-e[1]),abs(t['y']-e[2]))
    aa=[e for e in t['allies'] if dist(e)<=6]
    ee=[e for e in t['foes'] if dist(e)<=6]
    ah=sum(e[3] for e in aa);eh=sum(e[3] for e in ee)
    return [t['hp']/max(1,t['max']),t['hp']/1000,t['max']/1000,t['str']/100,t['focus']/100,t['range']/3,
            t['gems']/50,t['round']/1000,float(t['cds'][0]==0),float(t['cds'][1]==0),t['nd']/8,
            len(aa),ah/1000,sum(e[5] for e in aa)/100,len(ee),eh/1000,sum(e[5] for e in ee)/100,
            sum(e[7]>1 for e in ee),min((e[3]/max(1,e[4]) for e in ee),default=1),
            min(5,(t['hp']+ah)/max(1,eh))]+[float(t['type']==i) for i in range(13)]

def label(t):
    acts=t['acts'];moves=[a for a in acts if a[0]==4]
    if moves:
        _,x,y,_=moves[-1]
        nd=min((max(abs(x-e[1]),abs(y-e[2])) for e in t['foes']),default=99)
        if nd>t['nd']:return 0 # retreat, including productive hit-and-retreat
        if nd<t['nd']:return 2 # approach/engage
    if any(a[0] in (5,6) and any(max(abs(a[1]-e[1]),abs(a[2]-e[2]))<=1 for e in t['foes']) for a in acts):return 2
    return 1 # hold; exclude recall/ward bookkeeping from the intent label
