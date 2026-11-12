"""Freeze one development-selected bot, then test on sealed maps and package exact artifacts."""
import os,json,time,hashlib,subprocess,zipfile,shutil,datetime
from pathlib import Path
import numpy as np
from project import ROOT,ARENA,CLI,ENGINE,ENGINE_HASH,save,sha,digest,check_stop
from local_panel import run,artifact,read_native
from prepare_campaign import prepare
WD=ROOT/'qualification';WD.mkdir(exist_ok=True)

def comparison(rows,a,b):
    index=lambda n:{(r['opponent'],r['map_file'],r['side']):r for r in rows if r['candidate']==n}
    A,B=index(a),index(b);assert set(A)==set(B)
    maps=sorted({k[1] for k in A});d={m:[] for m in maps}
    for k in A:d[k[1]].append(A[k]['score']-B[k]['score'])
    values=np.array([np.mean(d[m]) for m in maps]);rng=np.random.default_rng(113114)
    boot=values[rng.integers(0,len(values),(10000,len(values)))].mean(1)
    styles=sorted({k[0] for k in A})
    style={o:float(np.mean([A[k]['score']-B[k]['score'] for k in A if k[0]==o])) for o in styles}
    fresh=[m for m in maps if Path(m).parent.name in ('maps_generated_v113','maps_sw08_followup','maps_v113_stability')]
    subset_gain=lambda subset: float(np.mean([np.mean(d[m]) for m in subset])) if subset else None
    return {'games':len(A),'maps':len(maps),'candidate_score':sum(r['score'] for r in A.values())/len(A),'control_score':sum(r['score'] for r in B.values())/len(B),'gain':float(values.mean()),'map_cluster_bootstrap_95':[float(np.quantile(boot,.025)),float(np.quantile(boot,.975))],'style_deltas':style,'fresh_generated_gain':subset_gain(fresh),'fresh_generated_maps':len(fresh),'published_gain':subset_gain([m for m in maps if m not in fresh])}

def fuel_rate(rows,name):
    events=bodyrounds=0
    for r in rows:
        if r['candidate']!=name:continue
        n=read_native(r['summary']);team='team'+r['side'].upper()
        count=sum(c['team']==team for c in n['roster']['champions'])
        events+=r['fuel'];bodyrounds+=count*r['rounds']
    return {'events':events,'scheduled_champion_rounds':bodyrounds,'per_1000_scheduled_champion_rounds':events*1000/bodyrounds}

def main():
    selected=ROOT/'final-selection.json'
    while not selected.exists():check_stop();time.sleep(2)
    sel=json.loads(selected.read_text());name=sel['winner'];campaign=prepare()
    assert digest(ARENA/'bots'/name/'src')==sel['source_sha256'] and sha(artifact(name))==sel['wasm_sha256']
    refs=json.loads((ROOT/'references.json').read_text())
    for n in ('b112','b113','b114'):refs[n]={'file':str(artifact(n)),'sha256':sha(artifact(n))}
    save(ROOT/'references.json',refs)
    protocol={'selected_before_final_games':sel,'maps':campaign['maps']['final'],'candidates':[name,'b111','b112','b113','b114','bterm'],'styles':campaign['styles'],'head_to_head':['b112','b113','b114'],'engine':ENGINE,'engine_build':ENGINE_HASH,'fuel':'normal default','delivery_gate':{'minimum_current_v113_reference_gain':.03,'positive_95_map_cluster_lower_bound':True,'nonnegative_fresh_generated_gain':True,'direct_v113_score_greater_than':.5,'worst_style_regression_limit':.10,'fuel_rate_ratio_max_vs_v113':1.15,'both_team_faults_and_codes':0},'substantial_goal':{'vs_v111_reference_gain':.08,'direct_v111_score':.60},'limitations':'Published maps may have historical exposure; fresh generated maps are sealed until now. Bootstrap clusters by map, not individual game. Local qualification is not ladder performance. User supplied v114 as a dummy with reported fuel issues: retain as comparison; do not inherit its runtime.'}
    p=WD/'protocol.json'
    if p.exists():assert json.loads(p.read_text())==protocol
    else:save(p,protocol)
    maps=list(map(Path,protocol['maps']))
    rows=run('final-sealed-reference',protocol['candidates'],maps,protocol['styles'],12)
    direct=run('final-sealed-direct',[name],maps,protocol['head_to_head'],12)
    comps={n:comparison(rows,name,n) for n in ('b111','b112','b113','b114','bterm')}
    rates={n:fuel_rate(rows,n) for n in (name,'b111','b112','b113','b114','bterm')}
    h2h={o:{'score':sum(r['score'] for r in direct if r['opponent']==o),'games':sum(r['opponent']==o for r in direct)} for o in protocol['head_to_head']}
    dc=[r for r in rows if r['candidate']==name and r['opponent']=='b111']
    allclean=not any(r['faults'] or r['opponent_faults'] or r['diagnostic_codes'] for r in rows+direct)
    c=comps['b113'];fuelratio=rates[name]['per_1000_scheduled_champion_rounds']/rates['b113']['per_1000_scheduled_champion_rounds']
    gates={'zero_faults_and_codes':allclean,'current_reference_gain':c['gain']>=.03,'positive_cluster_confidence':c['map_cluster_bootstrap_95'][0]>0,'fresh_generated_nonnegative':c['fresh_generated_gain']>=0,'direct_v113_above_half':h2h['b113']['score']/h2h['b113']['games']>.5,'worst_style_bounded':min(c['style_deltas'].values())>=-.10,'fuel_rate_bounded':fuelratio<=1.15}
    result={'candidate':name,'approved_for_upload':all(gates.values()),'gates':gates,'comparisons':comps,'head_to_head':h2h,'direct_v111':{'score':sum(r['score'] for r in dc),'games':len(dc)},'fuel_rates':rates,'fuel_rate_ratio_vs_v113':fuelratio,'substantial_goal_met':comps['b111']['gain']>=.08 and sum(r['score'] for r in dc)/len(dc)>=.60,'runtime_games':len(rows)+len(direct),'source_sha256':sel['source_sha256'],'wasm_sha256':sel['wasm_sha256'],'protocol_sha256':sha(p),'local_only':True}
    save(WD/'result.json',result);print(json.dumps(result,indent=2),flush=True)
    package(name, result, WD/'result.json')

def package(name, result, result_path):
    # Package is reviewable even if qualification fails; upload stays separate.
    dest=ROOT/'release'/name;dest.mkdir(parents=True,exist_ok=True);bundle=dest/'source.zip'
    if not bundle.exists():
        r=subprocess.run([str(CLI),'bundle','bots/'+name,'--output',str(bundle)],cwd=ARENA,capture_output=True,text=True,encoding='utf-8',timeout=120,env={**os.environ,'CAMBC_NO_UPDATE_CHECK':'1'})
        assert r.returncode==0,(r.stdout+r.stderr)[-1000:]
    src=ARENA/'bots'/name
    with zipfile.ZipFile(bundle) as z:
        assert z.testzip() is None
        expected={p.relative_to(src).as_posix():p for p in (src/'src').rglob('*') if p.is_file()}
        assert {n for n in z.namelist() if not n.endswith('/')}==set(expected)
        for n,f in expected.items():assert z.read(n)==f.read_bytes()
    shutil.copy2(artifact(name),dest/'bot-injected.wasm')
    manifest={'candidate':name,'source_digest':digest(src/'src'),'source_zip':{'file':'source.zip','sha256':sha(bundle)},'wasm':{'file':'bot-injected.wasm','sha256':sha(dest/'bot-injected.wasm')},'sdk_digest':digest(ARENA/'sdk/cpp'),'cli_sha256':sha(CLI),'engine':ENGINE,'engine_build':ENGINE_HASH,'qualification_sha256':sha(result_path),'approved_for_upload':result['approved_for_upload'],'all_fixes_enabled':True,'user_authorization':'2026-11-08: once you are satisfied push to ladder please','warning':'Platform compilation and ladder behavior require separate verification.'}
    save(dest/'manifest.json',manifest)
    (dest/'README.md').write_text('# Corrected Battlecode package\n\nExact frozen source and local release Wasm. See manifest.json and '+result_path.relative_to(ROOT).as_posix()+' for identities and evidence. Upload approval: '+str(result['approved_for_upload'])+'.\n',encoding='utf-8')
if __name__=='__main__':main()
