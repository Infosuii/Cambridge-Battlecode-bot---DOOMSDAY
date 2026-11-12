"""EXP286: exact initial runtime base gems vs native capture packet residuals."""
from collections import defaultdict
import os
import subprocess
from zipfile import ZipFile
import ablate_dev as bench
from engine3_pool import HERE,ENGINE,read
from freeze_engine3_discovery import write
from live111e_context import OUT
from attribute_live111b_camps import audit as packets_from_native


def metrics(captures,clears,groups,until):
    cs=[c for c in captures if c['round']<=until];cl=[c for c in clears if c['round']<=until]
    hist=defaultdict(lambda:{'packets':0,'base':0,'actual':0,'residual':0})
    shares=defaultdict(lambda:{'recipient_packets':0,'actual_share_gems':0})
    sharing=defaultdict(lambda:{'packets':0,'base':0,'actual':0,'residual':0})
    for c in cs:
        g=groups[c['group']];base=g['gems'];residual=c['gems']-base
        composition=','.join(str(x) for x in sorted(member['type'] for member in g['camps']))
        for row in (hist[composition],sharing[str(c['capturers'])]):
            row['packets']+=1;row['base']+=base;row['actual']+=c['gems'];row['residual']+=residual
        for s in c['shares']:
            row=shares[s['name']];row['recipient_packets']+=1;row['actual_share_gems']+=s['gems']
    actual=sum(c['gems'] for c in cs);base=sum(groups[c['group']]['gems'] for c in cs)
    residual=sum(c['gems']-groups[c['group']]['gems'] for c in cs)
    assert actual==base+residual
    return {'packets':len(cs),'clears':len(cl),'actual':actual,'base':base,'residual':residual,
            'base_clear_gems':sum(groups[c['group']]['gems'] for c in cl),
            'positive_residual_packets':sum(c['gems']>groups[c['group']]['gems'] for c in cs),
            'negative_residual_packets':sum(c['gems']<groups[c['group']]['gems'] for c in cs),
            'composition':dict(sorted(hist.items())),'sharing':dict(sorted(sharing.items())),
            'recipient_hero_shares':dict(sorted(shares.items()))}


if __name__=='__main__':
    proof=read(HERE/'RUNTIME_CAMP_METADATA_PROOF.json');assert proof['pass'] and proof['games']==90
    assert proof['decoder_sha256']==bench.digest(HERE/'extract_runtime_camps.mjs')
    frozen=read(HERE/'LIVE111E_DISCOVERY_SPLIT.json')['matches'];assert len(frozen)==73
    resource={r['matchId']:r for r in read(HERE/'LIVE111E_RESOURCE_REPORT.json')['rows']}
    profiles={p:read(HERE/f'LIVE111E_REPLAY_{p.upper()}.json') for p in ('discovery','control','confirm')}
    out=bench.CACHE/'live111e-value-attribution-20261106';out.mkdir();jobs=[]
    for r in frozen:
        mid=r['matchId'];native=OUT/'summaries'/(mid+'.json');assert bench.digest(native)==resource[mid]['native_sha256']
        doc=read(native);assert doc['match']['engineBuildHash']==ENGINE and doc['diagnostics']['detailedCaptureComplete']
        archive=OUT/'replays'/(mid+'.zip');assert bench.digest(archive)==profiles[r['partition']]['archive_sha256'][mid]
        replay=OUT/f'analysis-{r["partition"]}'/'replays'/(mid+'.repl26a')
        with ZipFile(archive) as z:assert replay.read_bytes()==z.read('replay.repl26a')
        jobs.append({'matchId':mid,'partition':r['partition'],'replay':str(replay),'replay_sha256':bench.digest(replay),
                     'native_sha256':bench.digest(native),'archive_sha256':bench.digest(archive),'map_sha256':doc['match']['mapHash']})
    plan={'games':73,'engine':ENGINE,'decoder_sha256':bench.digest(HERE/'extract_runtime_camps.mjs'),
          'sdk_proof_sha256':bench.digest(HERE/'RUNTIME_CAMP_METADATA_PROOF.json'),'jobs':jobs,
          'scope':'Fixed DiscoveryE packet accounting, initial SDK base rewards vs all residual effects, no causal policy or win claim.'}
    write(HERE/'LIVE111E_CAMP_VALUE_PLAN.json',plan);write(out/'jobs.json',jobs)
    subprocess.run(['node',HERE/'extract_runtime_camps.mjs',out/'jobs.json',out/'decoded.json'],cwd=bench.ROOT,
                   env={**os.environ,'NFS_REPLAY_ENGINE':'3.0.0'},check=True)
    decoded=read(out/'decoded.json');assert decoded['games']==73
    write(HERE/'LIVE111E_RUNTIME_CAMP_METADATA.json',decoded)
    metadata={r['matchId']:r for r in decoded['rows']};rows=[]
    for r in frozen:
        mid=r['matchId'];doc=read(OUT/'summaries'/(mid+'.json'));groups={g['handle']:g for g in metadata[mid]['groups']}
        assert len(groups)==len(metadata[mid]['groups'])
        clears,caps=packets_from_native(doc)
        assert all(c['group'] in groups for c in [*clears,*caps])
        ours='team'+r['side'].upper();rival='teamB' if ours=='teamA' else 'teamA';row={k:r[k] for k in ('matchId','opponent','partition')}
        for label,team in (('ours',ours),('rival',rival)):
            cs=[c for c in caps if c['team']==team];cl=[c for c in clears if c['team']==team]
            assert sum(c['gems'] for c in cs)==resource[mid][label]['camp'] and len(cl)==resource[mid][label]['clears']
            row[label]={str(t):metrics(cs,cl,groups,t) for t in (150,300,800,10**9)}
        rows.append(row)
    reports={}
    for partition in ('discovery','confirm','control'):
        selected=[r for r in rows if r['partition']==partition];report={'games':len(selected),'phases':{}}
        for t in ('150','300','800',str(10**9)):
            phase={}
            for label in ('ours','rival'):
                values=[r[label][t] for r in selected]
                aggregate={k:sum(v[k] for v in values) for k in ('packets','clears','actual','base','residual','base_clear_gems','positive_residual_packets','negative_residual_packets')}
                aggregate['mean_base_per_packet']=aggregate['base']/aggregate['packets'] if aggregate['packets'] else None
                for category in ('composition','sharing','recipient_hero_shares'):
                    table=defaultdict(lambda:defaultdict(float))
                    for v in values:
                        for key,data in v[category].items():
                            for k,value in data.items():table[key][k]+=value
                    aggregate[category]={k:dict(v) for k,v in sorted(table.items())}
                phase[label]=aggregate
            phase['ours_minus_rival']={k:phase['ours'][k]-phase['rival'][k] for k in ('actual','base','residual','packets','clears','base_clear_gems')}
            assert phase['ours_minus_rival']['actual']==phase['ours_minus_rival']['base']+phase['ours_minus_rival']['residual']
            report['phases'][t]=phase
        reports[partition]=report
    result={'pass':True,'games':len(rows),'plan_sha256':bench.digest(HERE/'LIVE111E_CAMP_VALUE_PLAN.json'),
            'metadata_sha256':bench.digest(HERE/'LIVE111E_RUNTIME_CAMP_METADATA.json'),'reports':reports,'rows':rows,
            'limits':'Exact accounting on outcome-selected source-inferred games. Residual includes any modifier/rounding/growth not separated here; no named item attribution, causal targeting/role or recoverable win claim.'}
    write(HERE/'LIVE111E_CAMP_VALUE_ATTRIBUTION.json',result)
    print({p:{t:v['ours_minus_rival'] for t,v in r['phases'].items()} for p,r in reports.items()},flush=True)
