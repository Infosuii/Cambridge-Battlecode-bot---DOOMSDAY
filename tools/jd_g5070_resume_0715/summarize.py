"""Summarize frozen, matched confirmation; unknown generated categories stay explicit."""
import collections,json,random
from pathlib import Path
import run as bridge
r=bridge.runner
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'research/jd-g5070-resume-0715'
CATS=json.loads((ROOT/'research/x3/atlas/categories.json').read_text())

def summary(pairs):
    by=collections.defaultdict(list)
    for p in pairs:by[p['map']].append(p['d_score'])
    lo,hi=r.bootstrap(by,random.Random(1104));n=len(pairs)
    return dict(cells=n,maps=len(by),delta_pp=round(sum(x['d_score'] for x in pairs)/n,3),ci95=[round(lo,3),round(hi,3)],cand_wins=sum(x['cand_score']==1 for x in pairs),base_wins=sum(x['base_score']==1 for x in pairs),candidate_only_wins=sum(x['cand_score']==1 and x['base_score']!=1 for x in pairs),baseline_only_wins=sum(x['base_score']==1 and x['cand_score']!=1 for x in pairs),draws=sum(x['cand_score']==.5 for x in pairs),mean_delta_banked=round(sum(x['d_banked'] for x in pairs)/n,3))

def main():
    results={}
    for variant in ['cg','cpg','gov']:
        runs=[json.loads((r.EVAL/'runs'/f'final-{variant}-{m}-01'/'results.json').read_text()) for m in ['pool','fresh51104']]
        assert all(d['missing']==0 and d['failed']==0 and d['played']==d['expected_games'] for d in runs)
        ps=[p for d in runs for p in d['pairs']];assert len(ps)==2232
        strata={}
        for key in ['opp','size']:
            strata[key]={v:summary([p for p in ps if p[key]==v]) for v in sorted({p[key] for p in ps})}
        strata['category']={v:summary([p for p in ps if CATS.get(p['map'],'generated-unclassified')==v]) for v in sorted({CATS.get(p['map'],'generated-unclassified') for p in ps})}
        arms={a:{k:sum(d['arms'][a][k] for d in runs) for k in ['played','wins','draws','faults','fuel_outs','fuel_out_games']} for a in ['cand','base']}
        result=dict(combined=summary(ps),pool=summary(runs[0]['pairs']),fresh=summary(runs[1]['pairs']),arms=arms,strata=strata)
        result['scope']='Local official-fuel current-engine evidence only; no ladder trials'
        result['status']='Accepted (local evidence)' if result['combined']['ci95'][0]>0 and result['fresh']['ci95'][0]>0 and arms['cand']['faults']==0 and arms['cand']['fuel_outs']<=arms['base']['fuel_outs'] and all(s['delta_pp']>=-10 for k in ['opp','category'] for s in strata[k].values()) else 'Conditionally useful / experimental; promotion gate not met'
        result['severe_strata']=[dict(dimension=k,stratum=v,**s) for k,t in strata.items() for v,s in t.items() if s['delta_pp'] < -10]
        results[variant]=result
    payload=dict(source_freeze=json.loads((OUT/'FINAL_FREEZE.json').read_text()),final=results,notes=['No tuning after freeze','Pool includes all70 current official maps; fresh51104=100 unseen generated maps','C1-C7 only for maps with measured atlas categories; generated maps reported by size/opponent and as unclassified','Silent SDK action-failure returns are not instrumented; official diagnostic codes audited separately'])
    (OUT/'RESULTS.json').write_text(json.dumps(payload,indent=2))
    for k,v in results.items(): print(k,v['combined'],v['fresh'],v['status'],v['arms'])
if __name__=='__main__':main()
