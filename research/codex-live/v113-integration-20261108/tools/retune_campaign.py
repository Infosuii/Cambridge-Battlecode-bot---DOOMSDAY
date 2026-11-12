"""Bounded mechanism-led retuning after neural continuation; untouched final maps stay sealed."""
import json,time,concurrent.futures,hashlib,os
from pathlib import Path
import numpy as np
from project import ROOT,ARENA,save,sha,digest,build,check_stop
from local_panel import run
from prepare_campaign import prepare
from run_checks import sections
AXES=(3,4,8,10,12,33,36,37)
MEANINGS={3:'danger-health threshold',4:'carried gems before banking',8:'gold valuation',10:'crew health budget',12:'shopping gold threshold',33:'Marcella carried-gem threshold',36:'near-altar banking distance',37:'endgame banking score'}
WD=ROOT/'retune';WD.mkdir(exist_ok=True)
MARKER='''        if (!based) {
            based = true;
            b_hunt_range = tune::kHuntRange, b_hunt_gems = tune::kHuntGems, b_chase = tune::kChaseRange, b_stage = tune::kStageTimeout;'''

def make(name,theta,parent):
    assert len(theta)==len(AXES) and max(map(abs,theta))<=1.00001
    source=ARENA/'bots'/parent/'src';dst=ARENA/'bots'/name/'src'
    expected={p.name:p.read_text(encoding='utf-8') for p in source.iterdir() if p.is_file()}
    values=','.join(f'{v:.9f}f' for v in theta)+',1.000000000f'
    code='''            static volatile float retune_table[9] = {'''+values+'''};
            static constexpr int retune_axes[8] = {'''+','.join(map(str,AXES))+'''};
            if (retune_table[8] == 1.0f) {
                for (int i=0;i<8;++i) lab::knobs[retune_axes[i]] += retune_table[i];
            }
'''
    assert expected['bot.cpp'].count(MARKER)==1
    expected['bot.cpp']=expected['bot.cpp'].replace(MARKER,MARKER.replace('            based = true;\n','            based = true;\n'+code))
    if dst.exists():assert {p.name:p.read_text(encoding='utf-8') for p in dst.iterdir()}==expected
    else:
        dst.mkdir(parents=True)
        for p,t in expected.items():(dst/p).write_text(t,encoding='utf-8',newline='\n')
    w=build(name)
    result={'name':name,'theta':theta,'axes':list(AXES),'parent':parent,'source_sha256':digest(dst),'wasm_sha256':sha(w),'wasm':str(w)}
    save(dst.parent/'retune.json',result);return result

def aggregate(rows):
    out={}
    for name in sorted({r['candidate'] for r in rows}):
        rs=[r for r in rows if r['candidate']==name]
        by={o:sum(r['score'] for r in rs if r['opponent']==o)/sum(r['opponent']==o for r in rs) for o in {r['opponent'] for r in rs}}
        out[name]={'score':sum(r['score'] for r in rs)/len(rs),'opponents':by,'fuel':sum(r['fuel'] for r in rs),'faults':sum(r['faults']+r['opponent_faults'] for r in rs),'games':len(rs)}
    return out

def ranking(scores,base):
    b=scores[base];out=[]
    for name,s in scores.items():
        worst=min(s['opponents'][o]-b['opponents'][o] for o in b['opponents'])
        direct=s['opponents']['b111']
        utility=s['score']+.25*(direct-.5)-2*max(0.,-worst-.10)
        out.append({'name':name,**s,'worst_opponent_change':worst,'utility':utility})
    return sorted(out,key=lambda r:(r['faults']==0,r['utility'],r['score'],-r['fuel']),reverse=True)

def main():
    campaign=prepare();done=ROOT/'training'/os.environ.get('RETUNE_TRAINING','corrected-v113')/'complete.json'
    while not done.exists():check_stop();time.sleep(2)
    training=json.loads(done.read_text());parent=training['selected']['actor']
    vectors={'t000':[0.]*len(AXES)}
    for i,axis in enumerate(AXES):
        for sign in (-1,1):
            v=[0.]*len(AXES);v[i]=.5*sign;vectors[f't{len(vectors):03}']=v
    maps=list(campaign['maps']['train']);pub=[p for p in maps if 'maps_generated_v113' not in p];gen=[p for p in maps if 'maps_generated_v113' in p]
    key=lambda p:hashlib.sha256(('retune-screen|'+p).encode()).hexdigest()
    screen=list(map(Path,sorted(pub,key=key)[:4]+sorted(gen,key=key)[:4]))
    plan={'parent':parent,'parent_wasm_sha256':sha(ARENA/'bots'/parent/'.cambc/build-release/bot-injected.wasm'),'axes':{str(k):MEANINGS[k] for k in AXES},'vectors':vectors,'screen_maps':{str(p):sha(p) for p in screen},'screen_styles':['b111','nnm4','ref_x1','teammate_max_gx'],'joint_attempts':'Coordinate-informed sum, half-size sum, and double strongest coordinate. All mechanisms remain enabled. No arbitrary rescue search.','selection':'Pooled development score + .25*(direct-v111 score-.5), penalize any opponent regression beyond ten points; runtime-fault-free only. Final evaluation follows frozen selection.'}
    save(WD/'plan.json',plan)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:specs=dict(zip(vectors,ex.map(lambda n:make(n,vectors[n],parent),vectors)))
    control=sections(specs['t000']['wasm'])
    for n,s in specs.items():
        sec=sections(s['wasm']);assert all(v==sec[k] for k,v in control.items() if k not in ('0','11')),'Retune changed executable code'
    save(WD/'builds.json',specs)
    rows=run('retune-coordinate-screen',list(vectors),screen,plan['screen_styles'],12)
    scores=aggregate(rows);rank=ranking(scores,'t000');save(WD/'screen.json',{'scores':scores,'ranking':rank})
    # Choose beneficial directions using paired screen cells. A worse first test
    # is not rejection: retain it, then inspect joint/size interactions explicitly.
    base=scores['t000']['score'];best_axes={}
    for n,v in vectors.items():
        if n=='t000':continue
        i=next(i for i,x in enumerate(v) if x)
        if scores[n]['score']>base and (i not in best_axes or scores[n]['score']>scores[best_axes[i]]['score']):best_axes[i]=n
    selected=sorted(best_axes.values(),key=lambda n:scores[n]['score'],reverse=True)[:4]
    if not selected:selected=[r['name'] for r in rank if r['name']!='t000'][:1]
    joint=[sum(vectors[n][i] for n in selected) for i in range(len(AXES))]
    strongest=vectors[selected[0]]
    extra={'t017':joint,'t018':[x*.5 for x in joint],'t019':[x*2 for x in strongest]}
    save(WD/'repair-rationale.json',{'chosen_directions':selected,'mechanisms':[MEANINGS[AXES[i]] for i in best_axes],'vectors':extra,'reason':'Resolve interactions among banking timing, map resource valuation, crew budget and danger thresholds after corrected runtime and new neural weights; shrink joint changes or strengthen one measured direction.'})
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        for s in ex.map(lambda n:make(n,extra[n],parent),extra):
            assert sections(s['wasm'])['10']==control['10'];specs[s['name']]=s
    save(WD/'builds.json',specs)
    extra_rows=run('retune-joint-screen',list(extra),screen,plan['screen_styles'],12)
    scores.update(aggregate(extra_rows));rank=ranking(scores,'t000')
    shortlist=list(dict.fromkeys(['t000']+[r['name'] for r in rank if r['name']!='t000'][:4]+[parent]))
    save(WD/'dev-shortlist.json',{'names':shortlist,'selection_used_only_screen':True})
    dev=run('retune-development',shortlist,list(map(Path,campaign['maps']['dev'])),campaign['styles'],12)
    ds=aggregate(dev);dr=ranking(ds,'t000');winner=dr[0]['name']
    # The exact unmodified trained actor is a control and can win this comparison.
    result={'winner':winner,'ranking':dr,'source_sha256':digest(ARENA/'bots'/winner/'src'),'wasm_sha256':sha(ARENA/'bots'/winner/'.cambc/build-release/bot-injected.wasm'),'classification':'Development-selected; final qualification pending','all_fixes_enabled':True,'final_maps_used':False,'training_parent':parent}
    save(WD/'selection.json',result);print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
