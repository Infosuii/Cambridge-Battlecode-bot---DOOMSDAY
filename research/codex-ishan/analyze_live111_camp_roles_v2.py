"""Recount every native fixture; descriptive mechanics only, retain censoring/failures."""
from collections import defaultdict
from pathlib import Path
from statistics import mean,median

import ablate_dev as bench
from engine3_pool import CLI,CLI_HASH,ENGINE,HERE,read
from freeze_engine3_discovery import write


def aggregate(rows):
    return {'n':len(rows),'clears':sum(r['clear_count'] for r in rows),'no_clear':sum(not r['clear_count'] for r in rows),
            'first_clear_capped301_mean':mean(r['first_clear_capped301'] for r in rows),
            'first_clear_observed_median':median(r['first_clear_capped301'] for r in rows if r['clear_count']) if any(r['clear_count'] for r in rows) else None,
            **{k:sum(r[k] for r in rows) for k in ('camp_gems','deaths','fuel','round1_fuel','earned_gold','monster_damage','monster_damage_taken','early_end','errors')}}


if __name__=='__main__':
    path=HERE/'LIVE111_CAMP_ROLES_V2_RAW.json';raw=read(path);planpath=HERE/'LIVE111_CAMP_ROLES_V2_PLAN.json';plan=read(planpath)
    assert bench.digest(planpath)==raw['plan_sha256'] and len(raw['rows'])==raw['n_games']==plan['n_games']==1440
    assert plan['engine']==ENGINE and plan['cli']==CLI_HASH==bench.digest(CLI)
    for arm,build in plan['builds'].items():
        wasm=Path(build['path']);assert bench.digest(wasm)==build['sha256']
        for name,sha in build.get('sources',{}).items():assert bench.digest(wasm.parent/'src'/name)==sha
    rows=[];index={}
    for r in raw['rows']:
        p=bench.ROOT/r['native_path'];assert bench.digest(p)==r['native_sha256']
        doc=read(p);m=doc['match'];team='team'+r['side']
        assert m['engineBuildHash']==ENGINE and m['engineVersion']=='3.0.0'
        assert m['mapHash']==plan['maps'][r['map']+'.map26a']==r['map_hash'] and m['seed']==r['engine_seed']
        assert doc['diagnostics']['detailedCaptureComplete'] and doc['diagnostics']==r['diagnostics']
        actor,=[c for c in doc['champions'] if c['team']==team and c['name'].lower()==r['role']]
        assert actor['id']==r['actor_id'] and actor['metrics']==r['metrics']
        events=[e for e in doc['events'] if e['owner'].get('team')==team and e['owner'].get('id')==actor['id']]
        clears=[{'round':x['timestamp']['round'],'group':x['target']['id']} for e in events if e['kind']=='campClear' for x in e['entries']]
        fuel=[x['timestamp']['round'] for e in events if e['kind']=='fuelExhausted' for x in e['entries']]
        assert clears==r['clears'] and fuel==r['fuel_rounds']
        assert all(float(c['metrics']['monsterDamageDone'])==0 for c in doc['champions'] if c['team']!=team or c['id']!=actor['id'])
        gems=sum(float(x['value']) for e in events if e['kind']=='gemCollection' for x in e['entries'] if x['context']=='campGroup')
        row={k:r[k] for k in ('role','mode','map','side')}
        row.update({'clear_count':len(clears),'first_clear_capped301':min((x['round'] for x in clears),default=301),
                    'camp_gems':gems,'fuel':len(fuel),'round1_fuel':fuel.count(1),'early_end':int(m['roundsCompleted']<300),
                    'errors':int(bool(doc['diagnostics']['codes'] or any(doc['diagnostics']['botFaults'].values()))),
                    **{k:float(actor['metrics'][v]) for k,v in (('deaths','deaths'),('earned_gold','earnedGold'),('monster_damage','monsterDamageDone'),('monster_damage_taken','monsterDamageTaken'))}})
        key=(r['map'],r['side'],r['role'],r['mode']);assert key not in index
        rows.append(row);index[key]=row
    summary={}
    for role in plan['roles']:
        summary[role]={mode:aggregate([r for r in rows if r['role']==role and r['mode']==mode]) for mode in ('original','aoeplay')}
        pairs=[(r,index[r['map'],r['side'],role,'aoeplay']) for r in rows if r['role']==role and r['mode']=='original']
        assert len(pairs)==180
        summary[role]['play_difference']={k:sum(b[k]-a[k] for a,b in pairs) for k in ('clear_count','camp_gems','fuel','round1_fuel','deaths','earned_gold','monster_damage','monster_damage_taken')}
        summary[role]['play_difference']['clear_improved_equal_worse']=[sum((b['clear_count']>a['clear_count'],b['clear_count']==a['clear_count'],b['clear_count']<a['clear_count'])[i] for a,b in pairs) for i in range(3)]
        summary[role]['play_difference']['fuel_cell_increases']=sum(b['fuel']>a['fuel'] or b['round1_fuel']>a['round1_fuel'] for a,b in pairs)
    write(HERE/'LIVE111_CAMP_ROLES_V2_ANALYSIS.json',{'raw_sha256':bench.digest(path),'recount_pass':True,'native_cells_reopened':1440,
          'scope':'Artificial forced single-farmer descriptive mechanics; original neural/policy may choose different jobs. No win estimate, production roster conclusion or qualified hash.',
          'summary':summary,'rows':rows})
    print(summary,flush=True)
