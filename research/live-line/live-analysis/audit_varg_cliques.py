"""EXP281 exact domain: no model tuning and no production changes."""
from math import ceil
import ablate_dev as bench
from engine3_pool import HERE,read
from freeze_engine3_discovery import write
from varg_capability import reference


def geometry(camps):
    n=len(camps);adj=[]
    for c in camps:
        p=c['position'];adj.append(sum(1<<j for j,d in enumerate(camps) if max(abs(p[0]-d['position'][0]),abs(p[1]-d['position'][1]))<=1))
    remaining=(1<<n)-1;components=[];supported=True
    while remaining:
        reached=remaining&-remaining;prior=0
        while reached!=prior:
            prior=reached
            for i in range(n):
                if reached>>i&1:reached|=adj[i]
        components.append(reached);remaining&=~reached
        if any(adj[i]!=reached for i in range(n) if reached>>i&1):supported=False
    return adj,components,supported


def predict(camps,components):
    return sum(ceil(max((c['hp'] for i,c in enumerate(camps) if mask>>i&1),default=0)/50) for mask in components)


if __name__=='__main__':
    raw=read(HERE/'CAMP_GEOMETRY_RAW.json');static=[];states=0
    def check(camps):
        global states
        adj,components,supported=geometry(camps);alive=sum(1<<i for i,c in enumerate(camps) if c['hp']>0)
        for i,c in enumerate(camps):
            old=sum(j!=i and d['hp']>0 and max(abs(c['position'][0]-d['position'][0]),abs(c['position'][1]-d['position'][1]))<=1 for j,d in enumerate(camps))
            assert old==(adj[i]&alive&~(1<<i)).bit_count()
        if supported:assert predict(camps,components)==len(reference(camps)[0])
        states+=1;return components,supported
    for r in raw['rows']:
        for g in r['groups']:
            camps=[{'id':c['handle'],'position':[c['x'],c['y']],'hp':c['hp'],'strength':c['strength']} for c in g['camps']]
            components,supported=check(camps)
            static.append({'map':r['map'],'group':g['handle'],'members':len(camps),'components':components,'supported':supported})
    observations=read(HERE/'VARG_CLEAR_OBSERVATIONS.json');audit=read(HERE/'VARG_CLEAR_RECOUNT.json');assert audit['pass']
    tasks=[];missing=0
    for r,a in zip(observations['rows'],audit['rows'],strict=True):
        o=r['observation'];design=o['design']
        if not design:continue
        components,supported=check(design)
        for f in o['frames']:
            if any(c['before'] is None for c in f['camps']):missing+=1;continue
            hp={c['id']:c['before'] for c in f['camps']}
            check([{**c,'hp':hp[c['id']]} for c in design])
        complete=o['reason']==1 and a['missing_camp_snapshots']==0 and a['outside_group_damage']==0
        predicted=predict(design,components) if supported else None
        equal=predicted==len(o['frames']) if supported and complete else None
        tasks.append({'map':r['map'],'side':r['side'],'mode':r['mode'],'supported':supported,'complete':complete,
                      'prediction':predicted,'actual_attacks':len(o['frames']),'equal':equal})
    report={'pass':True,'scope':'Integer50strength exact basic count domain and executor neighbour parity only. No movement/survival/spell/float/win claim.',
            'public_groups':len(static),'supported_public_groups':sum(r['supported'] for r in static),
            'multi_supported':sum(r['supported'] and r['members']>1 for r in static),'states_checked':states,'missing_frames':missing,
            'eligible_supported_tasks':sum(r['supported'] and r['complete'] for r in tasks),
            'eligible_supported_disagreements':sum(r['equal'] is False for r in tasks),
            'raw_sha256':bench.digest(HERE/'CAMP_GEOMETRY_RAW.json'),'task_raw_sha256':bench.digest(HERE/'VARG_CLEAR_OBSERVATIONS.json'),
            'static':static,'tasks':tasks}
    write(HERE/'VARG_CLIQUE_DOMAIN_AUDIT.json',report)
    print({k:v for k,v in report.items() if k not in ('static','tasks')},flush=True)
