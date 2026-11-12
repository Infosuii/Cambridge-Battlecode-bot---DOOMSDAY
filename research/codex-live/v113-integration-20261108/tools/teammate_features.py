"""Preserve v114 as a control; port only its two isolated strategy additions."""
import json,time,re,concurrent.futures,shutil
from pathlib import Path
from project import ROOT,ARENA,save,sha,digest,build,check_stop
from prepare_campaign import prepare
from local_panel import run
from retune_campaign import aggregate,ranking
from run_checks import sections
WD=ROOT/'teammate-features';WD.mkdir(exist_ok=True)

def make(name,mask,parent,threshold=90,scale=1.):
    src=ARENA/'bots'/parent/'src';out={p.name:p.read_text(encoding='utf-8') for p in src.iterdir() if p.is_file()}
    out['cl_newmap_table.h']=(ROOT/'teammate-v114/src/cl_newmap_table.h').read_text(encoding='utf-8')
    out['teammate_flags.h']=f'''#pragma once
inline volatile int teammate_cfg[4] = {{{mask},1,{threshold},300}};
inline volatile float teammate_scale[2] = {{{scale:.8f}f,1.0f}};
inline bool teammate_enabled(int bit) {{ return teammate_cfg[1]==1 && (teammate_cfg[0]&bit)!=0; }}
static_assert([] {{ for (auto r:cl_newmap::kRows) if(r.profile<0 || r.profile>=cl_newmap::kNumProfiles) return false; return true; }}());
'''
    c=out['bot.cpp'];needle='#include "a2map.h"';assert c.count(needle)==1
    c=c.replace(needle,needle+'\n#include "cl_newmap_table.h"\n#include "teammate_flags.h"')
    marker='''#endif
    }
#endif
#if A2_LAB
    {
        // Engine-lab joint search'''
    assert c.count(marker)==1
    block='''        // Teammate v114: extend profiles only after existing map replacement,
        // once per champion, before this campaign's retuned offsets are applied.
        if (teammate_enabled(2) && !ladder_known)
            for (const auto& row : cl_newmap::kRows)
                if (row.w==w.width && row.h==w.height && row.groups==n_groups && row.gems==total_gems) {
                    for (int i=0;i<48;++i) lab::knobs[i] += cl_newmap::kDelta[row.profile][i]*teammate_scale[0];
                    debug_block({ std::printf("FTPROFILE %d %u %d\\n",round,my_id,row.profile); });
                    break;
                }
'''
    c=c.replace(marker,marker.replace('#endif\n    }','#endif\n'+block+'    }',1))
    marker='    tune::kShopGold = std::max(30, static_cast<int>(static_cast<float>(tune::kShopGold) * GT_SHOP));';assert c.count(marker)==1
    c=c.replace(marker,marker+'''
    if (teammate_enabled(1) && round < teammate_cfg[3]) {
        tune::kShopGold=std::min(tune::kShopGold,static_cast<int>(teammate_cfg[2]));
        debug_block({ if(round==50) std::printf("FTSHOP %d %u %d\\n",round,my_id,tune::kShopGold); });
    }
''')
    out['bot.cpp']=c;dst=ARENA/'bots'/name/'src'
    if dst.exists():assert {p.name:p.read_text(encoding='utf-8') for p in dst.iterdir()}==out
    else:
        dst.mkdir(parents=True)
        for p,t in out.items():(dst/p).write_text(t,encoding='utf-8',newline='\n')
    w=build(name);r={'name':name,'parent':parent,'mask':mask,'threshold':threshold,'scale':scale,'source_sha256':digest(dst),'wasm_sha256':sha(w),'wasm':str(w)}
    save(dst.parent/'teammate-feature.json',r);return r

def main():
    selection=ROOT/'retune/selection.json'
    while not selection.exists():check_stop();time.sleep(2)
    parent=json.loads(selection.read_text())['winner'];p=prepare()
    # Preserve exact supplied v114 as a control, including its inherited runtime.
    dst=ARENA/'bots/b114/src'
    if not dst.exists():shutil.copytree(ROOT/'teammate-v114/src',dst)
    assert digest(dst)==json.loads((ROOT/'teammate-v114/inventory.json').read_text())['source_sha256']
    build('b114')
    jobs=[('ft00',0,90,1.),('ft01',1,90,1.),('ft02',2,90,1.),('ft03',3,90,1.),('ft04',1,110,1.),('ft05',2,90,.5),('ft06',3,110,.5)]
    plan={'parent':parent,'source_archive_sha256':sha(Path(r'C:\Users\omdha\Downloads\bot.zip')),'changes':['early shopping cap before round 300','16-map additive profile extension'],
          'runtime':'Keep our corrected fuel accounting, staged inference, channel guards, banking fixes and coherent neural logs. Do not copy v114 runtime files.',
          'arms':jobs,'repairs':'After original A/B/A+B, test later shopping (110 instead of90), half-size profile changes, and their joint form. Investigate interaction with existing map replacement and retuned shopping thresholds.',
          'selection':'Full development utility using prior retune rule, candidate itself included as a control. Final maps remain sealed.'}
    save(WD/'plan.json',plan)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        specs=dict(zip([j[0] for j in jobs],ex.map(lambda j:make(j[0],j[1],parent,j[2],j[3]),jobs)))
    ctrl=sections(specs['ft00']['wasm'])
    for n,r in specs.items():assert all(sections(r['wasm'])[k]==v for k,v in ctrl.items() if k not in ('0','11'))
    save(WD/'builds.json',specs)
    text=(ROOT/'teammate-v114/src/cl_newmap_table.h').read_text()
    names=set(re.findall(r'// ([^ :]+)\.map26a:',text));allowed={**p['maps']['train'],**p['maps']['dev']}
    profile_maps=[Path(f) for f in allowed if Path(f).stem in names]
    generated=[Path(f) for f in p['maps']['train'] if 'maps_generated_v113' in f][:4]
    maps=profile_maps+generated;assert profile_maps and not set(map(str,maps))&set(p['maps']['final'])
    save(WD/'screen-maps.json',{'profile_maps':list(map(str,profile_maps)),'generated':list(map(str,generated)),'final_maps_excluded':True})
    rows=run('teammate-feature-screen',list(specs)+[parent,'b114'],maps,['b111','nnm4','ref_x1','teammate_max_gx'],12)
    scores=aggregate(rows);rank=ranking(scores,'ft00');save(WD/'screen.json',{'scores':scores,'ranking':rank})
    shortlist=list(dict.fromkeys([parent,'ft00']+[r['name'] for r in rank if r['name'] not in (parent,'ft00','b114')][:3]))
    dev=run('teammate-feature-development',shortlist,list(map(Path,p['maps']['dev'])),p['styles'],12)
    ds=aggregate(dev);dr=ranking(ds,parent);winner=dr[0]['name']
    result={'winner':winner,'ranking':dr,'source_sha256':digest(ARENA/'bots'/winner/'src'),'wasm_sha256':sha(ARENA/'bots'/winner/'.cambc/build-release/bot-injected.wasm'),'base_selection':str(selection),'teammate_features_accepted':winner.startswith('ft') and specs[winner]['mask']!=0,'feature_config':specs.get(winner),'all_fixes_enabled':True,'final_maps_used':False,'classification':'Development selected, independent qualification pending'}
    save(WD/'selection.json',result);save(ROOT/'final-selection.json',result)
    print(json.dumps({'winner':winner,'teammate_features_accepted':result['teammate_features_accepted'],'ranking':[{k:r[k] for k in ('name','score','utility')} for r in dr]},indent=2),flush=True)
if __name__=='__main__':main()
