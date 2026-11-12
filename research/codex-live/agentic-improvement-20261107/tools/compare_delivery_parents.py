"""Post-retune diagnostic: unchanged frozen parents on identical final maps.

No parameter search and no rewriting of the registered two-finalist outcomes.
"""
from pathlib import Path
import hashlib
import json
import sys
BASE=Path(r'C:\projects\cambridge battlecode\work\agentic-improvement')
sys.path.insert(0,str(BASE/'autonomy'));sys.path.insert(0,str(BASE))
import benchmark
from native_job import lease
from parallel_native_audit import run as audit
from store import DATA, save
from validate_route_economy import namespace_rows
from bounded_delivery_retune import direct_ci, reference_ci, verify

WD=BASE/'training/runs/delivery-parent-comparison-20261108'
FINAL=BASE/'training/runs/bounded-delivery-retune-v1'
PARENTS=['auto_bank_arrive_original','auto_bank_arrive_learned']
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    assert read(FINAL/'runtime.json')['status']=='complete'
    plan=read(FINAL/'frozen-plan.json')
    assert not any(read(FINAL/'outcomes.json')[n]['substantial_gate'] for n in read(FINAL/'outcomes.json'))
    with lease(WD,'delivery-parent-diagnostic-20261108') as status:
        benchmark.CONFIG['jobs']=16
        source={'parents':{n:plan['controls'][n] for n in PARENTS},'registered_final_plan_sha256':sha(FINAL/'frozen-plan.json'),
                'registered_outcomes_sha256':sha(FINAL/'outcomes.json'),'maps':{r:plan['data']['roles'][r] for r in ('final_a','final_b','published')},
                'scope':'Post-retune unchanged-parent comparison on the exact already evaluated final panels, for pragmatic delivery selection. No new tuning. Does not turn registered failed gates into an independent promotion; final selection is adaptive and disclosed.'}
        frozen=WD/'frozen-plan.json'
        if frozen.exists():assert read(frozen)==source
        else:save(frozen,source)
        verify(plan);pooled=[];reports={}
        for role,maps in source['maps'].items():
            label='delivery-parent-diagnostic-20261108-'+role
            status(phase='Unchanged-parent comparison',panel=role,workers=16)
            root=DATA/'benchmarks'/label
            rows=read(root/'results.json') if (root/'results.json').exists() else benchmark.run(label,PARENTS,[BASE/p for p in maps],__import__('representative_search').STYLES)
            receipt=audit(label,8);save(root/'both-team-audit.json',receipt)
            # V111 control and both registered finalists are exact cached rows.
            cached_root=DATA/'benchmarks'/('bounded-delivery-retune-20261107-'+role)
            cached=read(cached_root/'results.json');assert read(cached_root/'manifest.json')['maps']=={Path(p).name:h for p,h in maps.items()}
            combined=rows+cached;save(WD/(role+'-combined.json'),combined)
            reports[role]={n:benchmark.compare(combined,n) for n in PARENTS}
            pooled+=namespace_rows(combined,role,maps);verify(plan)
        save(WD/'pooled-results.json',pooled)
        names=PARENTS+read(FINAL/'frozen-finalists.json')['finalists']
        report={n:{'pooled':benchmark.compare(pooled,n),'reference_cluster95':reference_ci(pooled,n),'direct_cluster95':direct_ci(pooled,n),
                   'panels':{role:benchmark.compare(read(WD/(role+'-combined.json')),n) for role in source['maps']}} for n in names}
        save(WD/'outcomes.json',{'candidates':report,'scope':source['scope']})
        verify(plan)
        print(json.dumps(report),flush=True)

if __name__=='__main__':main()
