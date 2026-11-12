"""Prospective correction of one synthetic map before any final evaluation."""
from pathlib import Path
import copy
import hashlib
import json
import random
import re
import sys
import psutil

BASE=Path(r'C:\projects\cambridge battlecode\work\agentic-improvement')
LIVE=Path(__file__).resolve().parent/'live-map-audit-20261108/maps'
sys.path.insert(0,str(BASE/'autonomy'))
from store import save, now
WD=BASE/'training/runs/bounded-delivery-retune-v1'
ROOT=WD/'published-map-correction-20261108'
DATA=BASE/'autonomy/data/experiments/bounded-retune-data-20261107/data-plan.json'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def norm(name):return name.lower().replace('-','_')

def main():
    before=read(ROOT/'owner-before-stop.json')
    for spec in [before]+before['children']:
        try: assert psutil.Process(spec['pid']).create_time()!=spec['birth'], f'Owned process still running: {spec["pid"]}'
        except psutil.NoSuchProcess:pass
    assert read(WD/'runtime.json')['status']=='failed' and not (BASE/'training/training.lock').exists()
    marker=BASE/'autonomy/STOP'
    assert marker.read_text(encoding='utf-8').startswith('Internal maintenance: correct final published-map contamination')
    assert not (WD/'frozen-finalists.json').exists()
    assert not any((BASE/'autonomy/data/benchmarks'/('bounded-delivery-retune-20261107-'+tag)).exists() for tag in ('final_a','final_b','published'))
    data=read(DATA);plan=read(WD/'frozen-plan.json');assert plan['data']==data and plan['data_sha256']==sha(DATA)
    assert data['final_candidate_games_played']==0
    official={norm(p.stem):{'file':str(p),'sha256':sha(p)} for p in LIVE.glob('*.map26a')}
    catalog=read(BASE/'autonomy/data/experiments/bounded-delivery-retune-20261107-platform-spotcheck/live-map-catalog.json')
    assert len(official)==len(catalog['maps'])==128
    assert set(official)=={norm(m['name']) for m in catalog['maps']}
    pub=data['roles']['published']
    invalid=[p for p,h in pub.items() if norm(Path(p).stem) not in official]
    assert invalid==['arena\\maps\\cast_008_major_objectives.map26a'], invalid
    for p,h in pub.items():
        if p not in invalid: assert official[norm(Path(p).stem)]['sha256']==h==sha(BASE/p),p
    cpp=(BASE/'arena/bots/auto_bank_arrive_original/src/bot.cpp').read_text(encoding='utf-8')
    a=cpp.index('kRows[]');b=cpp.index('for (const auto& r : kRows)',a)
    named={norm(s) for s in re.findall(r'//\s+([^:\s]+):',cpp[a:b])}
    used={h for maps in data['roles'].values() for h in maps.values()}
    available=[]
    for path in sorted((BASE/'arena/maps').glob('*.map26a')):
        key=norm(path.stem)
        if key in official and key not in named and official[key]['sha256']==sha(path) and sha(path) not in used:
            available.append(path)
    assert available
    replacement=random.Random(611891607).choice(available)
    replacement_path=str(replacement.relative_to(BASE));replacement_hash=sha(replacement)
    train_fresh=copy.deepcopy({k:data['roles'][k] for k in ('train','fresh','final_a','final_b')})
    decision={'at':now(),'reason':'Directory glob included two custom fixtures in public_pool; one synthetic fixture entered final published44. Correct taxonomy before any final candidate game.',
              'removed':{invalid[0]:pub[invalid[0]]},'replacement':{replacement_path:replacement_hash},
              'selection_seed':611891607,'eligible_replacements':{str(p.relative_to(BASE)):sha(p) for p in available},
              'selection_rule':'One uniformly seeded choice among live official map bytes, same other-published filename-proxy stratum, hash-disjoint from every existing role. No policy outcomes used.',
              'live_pool':official,'live_catalog_sha256':sha(BASE/'autonomy/data/experiments/bounded-delivery-retune-20261107-platform-spotcheck/live-map-catalog.json'),
              'before_data_sha256':sha(DATA),'before_frozen_plan_sha256':sha(WD/'frozen-plan.json'),
              'completed_o_result_sha256':sha(WD/'o-result.json'),'all_final_candidate_games_unstarted':True,
              'scope':'Only one final published map changes. TRAIN/FRESH, generated finals, variants, source pins, policies and every completed game remain unchanged. Published maps may have historical exposure.'}
    for path,label in [(DATA,'data-plan-before.json'),(WD/'frozen-plan.json','frozen-plan-before.json')]:
        backup=ROOT/label;assert not backup.exists();backup.write_bytes(path.read_bytes())
    save(ROOT/'decision.json',decision)
    pub[replacement_path]=replacement_hash;del pub[invalid[0]]
    assert {k:data['roles'][k] for k in train_fresh}==train_fresh
    assert len(pub)==44 and all(official[norm(Path(p).stem)]['sha256']==h for p,h in pub.items())
    hashes=[h for maps in data['roles'].values() for h in maps.values()]
    assert len(hashes)==len(set(hashes))==260
    assert sum(norm(Path(p).stem) in named for p in pub)==12
    data['prospective_amendment']={'receipt':str((ROOT/'decision.json').relative_to(BASE)),'sha256':sha(ROOT/'decision.json')}
    data['scope']+=' Prospective 8Nov correction replaces one synthetic fixture wrongly labelled published; final44 all match downloaded live official bytes. See amendment receipt.'
    save(DATA,data)
    plan['data']=data;plan['data_sha256']=sha(DATA);plan['prospective_amendment']=data['prospective_amendment']
    save(WD/'frozen-plan.json',plan)
    save(ROOT/'applied.json',{'at':now(),'data_sha256':sha(DATA),'frozen_plan_sha256':sha(WD/'frozen-plan.json'),
                            'all_260_role_hashes_distinct':True,'all_44_final_published_match_live_official_bytes':True,
                            'unchanged_training_fresh_generated_finals':True,'replacement':replacement_path})
    marker.unlink()
    print(json.dumps({'corrected':True,'replacement':replacement_path,'all_final44_current_bytes_verified':True,'cached_games_preserved':True}))

if __name__=='__main__':main()
