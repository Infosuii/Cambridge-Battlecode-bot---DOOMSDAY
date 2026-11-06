"""Ideal integer basic-only model; no runtime bot, fitted scalar or map identity."""
from math import ceil


def near(a,b):return max(abs(a[0]-b[0]),abs(a[1]-b[1]))<=1


def wave(camps,damage=50):
    if not 0<len(camps)<=12 or damage<=0:raise ValueError('unsupported shape/damage')
    hp=[c['hp'] for c in camps];points=[c['position'] for c in camps]
    if any(h<0 or int(h)!=h for h in hp) or int(damage)!=damage:raise ValueError('integer proof only')
    hp=list(map(int,hp));damage=int(damage);sequence=[];waves=[]
    while any(hp):
        alive=[i for i,h in enumerate(hp) if h]
        primary=min(alive,key=lambda i:hp[i]-1000*camps[i]['strength']-2000*sum(j!=i and near(points[i],points[j]) for j in alive))
        hits=[j for j in alive if near(points[primary],points[j])]
        steps=min((hp[j]+damage-1)//damage for j in hits)
        sequence.extend([camps[primary]['id']]*steps)
        for j in hits:hp[j]=max(0,hp[j]-steps*damage)
        waves.append({'primary':camps[primary]['id'],'attacks':steps,'hp_after':list(hp)})
    return {'attacks':len(sequence),'sequence':sequence,'waves':waves}


def reference(camps,damage=50):
    # Independent enumeration recomputes every target and applies exactly one attack.
    health={c['id']:int(c['hp']) for c in camps};by_id={c['id']:c for c in camps};order=[c['id'] for c in camps]
    attacks=[];history=[]
    while any(health.values()):
        best=None;best_key=None
        for ident in order:
            if health[ident]<=0:continue
            c=by_id[ident];neighbours=0
            for other in order:
                if other!=ident and health[other]>0:
                    p,q=c['position'],by_id[other]['position']
                    if abs(p[0]-q[0])<=1 and abs(p[1]-q[1])<=1:neighbours+=1
            key=health[ident]-1000*c['strength']-2000*neighbours
            if best_key is None or key<best_key:best=ident;best_key=key
        attacks.append(best);p=by_id[best]['position']
        for ident in order:
            q=by_id[ident]['position']
            if abs(p[0]-q[0])<=1 and abs(p[1]-q[1])<=1:health[ident]=max(0,health[ident]-damage)
        history.append([health[i] for i in order])
    return attacks,history
