import json,sys,statistics as st
def load(name):
    r=json.load(open(f'research/dz/runs/{name}/results.json'))
    return {(g['map'],g['side']):g for g in r['per_game']}
base,cand=load(sys.argv[1]),load(sys.argv[2])
keys=sorted(set(base)&set(cand))
def m(rows,f): return st.mean(f(x) for x in rows)
for label,run in (('base',base),('cand',cand)):
    rows=[run[k] for k in keys]
    cp=lambda k,f:m(rows,lambda x:(x['checkpoints'][k][f] or 0))
    print(f"{label}: n={len(rows)} banked={m(rows,lambda x:x['banked']):.1f} opp={m(rows,lambda x:x['opponent_banked']):.1f} wins={sum(x['outcome']=='team'+x['side'] for x in rows)} "
          f"deaths={m(rows,lambda x:x['deaths']):.2f} rounds={m(rows,lambda x:x['rounds']):.0f} gold={m(rows,lambda x:x['gold']):.0f} faults={sum(x['faults'] for x in rows)} outs={sum(x['fuel_outs'] for x in rows)} "
          f"| R100 {cp('100','banked'):.1f} R250 {cp('250','banked'):.1f} R500 {cp('500','banked'):.1f} (collected R500 {cp('500','collected'):.1f})")
d=[(cand[k]['banked']-base[k]['banked'],k) for k in keys]
print('paired banked delta mean',round(st.mean(x for x,_ in d),1),'better',sum(x>0 for x,_ in d),'worse',sum(x<0 for x,_ in d))
r5=[((cand[k]['checkpoints']['500']['banked'] or 0)-(base[k]['checkpoints']['500']['banked'] or 0)) for k in keys]
print('paired R500 banked delta mean',round(st.mean(r5),1),'better',sum(x>0 for x in r5),'worse',sum(x<0 for x in r5))
d.sort(); print('worst',[(k,round(x)) for x,k in d[:6]]); print('best',[(k,round(x)) for x,k in d[-6:]])
xs=[x for x,_ in d]; print('paired SE',round(st.stdev(xs)/len(xs)**.5,1))
