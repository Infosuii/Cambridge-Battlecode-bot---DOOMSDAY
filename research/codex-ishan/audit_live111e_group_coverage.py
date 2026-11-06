"""EXP287: exact public map coverage and fixed native packet attribution, no policy."""
from collections import Counter,defaultdict
import ablate_dev as bench
from engine3_pool import HERE,read
from freeze_engine3_discovery import write


def describe(g,stats):
    return {'members':len(g['camps']),'gems':g['gems'],'gold':g['gold'],
            'dangerous_members':sum(stats[c['type']]['strength']>0 for c in g['camps']),
            'initial_hp':sum(stats[c['type']]['hp'] for c in g['camps'])}


def summary(groups,stats):
    values=[describe(g,stats) for g in groups]
    return {'groups':len(values),'histograms':{k:dict(sorted(Counter(v[k] for v in values).items())) for k in values[0]},
            'maxima':{k:max(v[k] for v in values) for k in values[0]}}


if __name__=='__main__':
    dev=read(HERE/'CAMP_GEOMETRY_RAW.json');live=read(HERE/'LIVE111E_RUNTIME_CAMP_METADATA.json');stats={}
    assert read(HERE/'LIVE111E_CAMP_VALUE_RECOUNT.json')['pass']
    for r in dev['rows']:
        for g in r['groups']:
            for c in g['camps']:
                row={k:c[k] for k in ('hp','strength','range')}
                assert c['type'] not in stats or stats[c['type']]==row;stats[c['type']]=row
    unique={};by_match={r['matchId']:r for r in live['rows']}
    for r in live['rows']:
        h=r['map_sha256'];assert h not in unique or unique[h]==r['groups'];unique[h]=r['groups']
    dev_groups=[g for r in dev['rows'] for g in r['groups']];live_groups=[g for groups in unique.values() for g in groups]
    all_types={c['type'] for g in live_groups for c in g['camps']};assert all_types<=set(stats)
    ds=summary(dev_groups,stats);ls=summary(live_groups,stats);maximum=ds['maxima']['members'];rows=[]
    frozen={r['matchId']:r for r in read(HERE/'LIVE111E_DISCOVERY_SPLIT.json')['matches']}
    for r in read(HERE/'LIVE111E_CAMP_ATTRIBUTION.json')['rows']:
        mid=r['matchId'];groups={g['handle']:g for g in by_match[mid]['groups']};row={k:r[k] for k in ('matchId','opponent','partition')};row['map_sha256']=by_match[mid]['map_sha256']
        row['large_groups']=[{'handle':g['handle'],**describe(g,stats)} for g in groups.values() if g['count']>maximum]
        for label in ('ours','rival'):
            row[label]={}
            for t in (150,300,800,10**9):
                cs=[c for c in r[label]['captures'] if c['round']<=t and groups[c['group']]['count']>maximum]
                cl=[c for c in r[label]['clears'] if c['round']<=t and groups[c['group']]['count']>maximum]
                row[label][str(t)]={'packets':len(cs),'base':sum(groups[c['group']]['gems'] for c in cs),'actual':sum(c['gems'] for c in cs),
                                   'clears':len(cl),'base_clear_gems':sum(groups[c['group']]['gems'] for c in cl)}
        rows.append(row)
    reports={}
    for partition in ('discovery','confirm','control'):
        selected=[r for r in rows if r['partition']==partition];phases={}
        for t in ('150','300','800',str(10**9)):
            phases[t]={'games_with_large_groups':sum(bool(r['large_groups']) for r in selected)}
            for label in ('ours','rival'):
                phases[t][label]={k:sum(r[label][t][k] for r in selected) for k in ('packets','base','actual','clears','base_clear_gems')}
            phases[t]['base_gap_games']=sum(r['ours'][t]['base']<r['rival'][t]['base'] for r in selected)
            phases[t]['base_margin']=phases[t]['ours']['base']-phases[t]['rival']['base']
        reports[partition]={'games':len(selected),'phases':phases}
    result={'pass':True,'development_maps':len(dev['rows']),'live_cases':len(live['rows']),'live_unique_maps':len(unique),
            'type_stats_from_sdk':stats,'development':ds,'live_unique':ls,'large_threshold_from_dev_max':maximum,
            'reports':reports,'rows':rows,'metadata_sha256':bench.digest(HERE/'LIVE111E_RUNTIME_CAMP_METADATA.json'),
            'dev_sha256':bench.digest(HERE/'CAMP_GEOMETRY_RAW.json'),
            'limits':'Descriptive exposed public corpus only, not neural training/other workers/sealed suites or a causal win/role recommendation.'}
    write(HERE/'LIVE111E_GROUP_COVERAGE.json',result)
    print({k:v for k,v in result.items() if k in ('development_maps','live_cases','live_unique_maps','large_threshold_from_dev_max')},flush=True)
    print({p:r['phases']['300'] for p,r in reports.items()},flush=True)
