import json,hashlib,random,shutil,concurrent.futures
from pathlib import Path
from project import ROOT,ARENA,save,sha,digest,build
from merge import sources,replace
from local_panel import run,STYLES

def prepare():
    frozen=ROOT/'campaign.json'
    if frozen.exists():return json.loads(frozen.read_text())
    pool=json.loads((ROOT/'published-maps.json').read_text());exposed={'00the_line','01islands','03homonoliths','00happy_halloween','02guardians','00rows','00vault','04comb'}
    rest=sorted([r for r in pool if r['name'] not in exposed],key=lambda r:hashlib.sha256(('v113-split-0813|'+r['sha256']).encode()).hexdigest())
    dev=[r for r in pool if r['name'] in exposed]+rest[:8]
    final=rest[8:32];train=rest[32:]
    gen=sorted((ARENA/'maps_generated_v113').glob('*.map26a'))
    assert len(gen)==120
    roles={'train':[Path(r['file']) for r in train]+gen[:60],'dev':[Path(r['file']) for r in dev]+gen[60:68],'final':[Path(r['file']) for r in final]+gen[80:104]}
    hashes={k:{str(p):sha(p) for p in paths} for k,paths in roles.items()}
    assert all(len(set(v.values()))==len(v) for v in hashes.values())
    for a,b in [('train','dev'),('train','final'),('dev','final')]:assert not set(hashes[a].values())&set(hashes[b].values())
    # Hash-disjoint geometry. Published maps were historically exposed; generated
    # final maps are fresh and kept sealed until checkpoint/parameter selection.
    plan={'maps':hashes,'styles':STYLES,'initial_checkpoint':str(ROOT/'training/initial-v113.pt'),'checkpoint_sha256':sha(ROOT/'training/initial-v113.pt'),'neural_plan':{'iterations':6,'games_per_iteration':96,'evaluate_every':2,'reward':'team terminal win, bounded previous-round lead potential','on_policy':'native distribution and frozen published features; all rows retained','learning_rate':.00005,'epochs':3},'strength_gate':{'paired_reference_gain_pp':8,'direct_score':.60,'runtime_faults':0},'exposure':'Development includes diagnostic published maps; published final maps may have historical exposure. Fresh generated final maps are untouched by selection. All final cells run after selection is frozen.'}
    save(frozen,plan);return plan

def candidate(name,mask,healthy,debug=False):
    original,out=sources(mask)
    if healthy:
        out['bot.cpp']=replace(out['bot.cpp'],'bit(w.hot_zone, pos) && hp < max_hp) {','bit(w.hot_zone, pos) && hp < max_hp && hp >= max_hp * 0.85f) {')
    dst=ARENA/'bots'/name/'src'
    if not dst.exists():
        dst.mkdir(parents=True)
        for p,t in out.items():(dst/p).write_text(t,encoding='utf-8',newline='\n')
    else:assert {p.name:p.read_text(encoding='utf-8') for p in dst.iterdir()}==out
    w=build(name,debug);return {'source':digest(dst),'wasm':sha(w),'healthy_escape_threshold':.85 if healthy else 0,'mask':mask,'debug':debug}

if __name__=='__main__':
    plan=prepare()
    jobs=[('p00',0,True,False),('p15',15,True,False),('d15',15,True,True)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:specs=dict(zip([j[0] for j in jobs],ex.map(lambda j:candidate(*j),jobs)))
    save(ROOT/'pretrain-builds.json',specs)
    maps=[Path(p) for p in plan['maps']['dev'] if Path(p).name[:2] in ('00','01','02','03','04')]
    run('pretrain-health-repair',['p00','p15','n15','n04','b113'],maps[:8],['b111','nnm4','ref_x1','teammate_max_gx'],12)
    run('mechanism-traces',['d15'],[Path(p) for p in list(plan['maps']['train'])[:20]]+maps[:8],['b111','nnm4'],10,True)
