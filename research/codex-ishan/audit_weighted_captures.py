"""EXP288 value-weighted last-clear/collection association, not exclusive ownership."""
from collections import Counter
from statistics import median
import ablate_dev as bench
from engine3_pool import HERE,read
from freeze_engine3_discovery import write

if __name__=='__main__':
    meta=read(HERE/'LIVE111E_RUNTIME_CAMP_METADATA.json');groups={r['matchId']:{g['handle']:g for g in r['groups']} for r in meta['rows']}
    old=read(HERE/'LIVE111E_CAMP_ATTRIBUTION.json');values=read(HERE/'LIVE111E_CAMP_VALUE_ATTRIBUTION.json');assert read(HERE/'LIVE111E_CAMP_VALUE_RECOUNT.json')['pass']
    frozen={r['matchId']:r for r in read(HERE/'LIVE111E_DISCOVERY_SPLIT.json')['matches']};rows=[]
    for r in old['rows']:
        mid=r['matchId'];ours='team'+frozen[mid]['side'].upper();row={k:r[k] for k in ('matchId','opponent','partition')}
        for label,team in (('ours',ours),('rival','teamB' if ours=='teamA' else 'teamA')):
            row[label]={}
            for until in (150,300,800,10**9):
                caps=[c for c in r[label]['captures'] if c['round']<=until]
                same=[c for c in caps if c['clear'] and c['clear']['team']==team]
                cross=[c for c in caps if c['clear'] and c['clear']['team']!=team]
                delays=[c['delay_rounds'] for c in same];weight=sum(groups[mid][c['group']]['gems'] for c in same)
                row[label][str(until)]={'packets':len(caps),'total_base':sum(groups[mid][c['group']]['gems'] for c in caps),
                    'cross_team_last_clear_packets':len(cross),'cross_base':sum(groups[mid][c['group']]['gems'] for c in cross),
                    'cross_actual':sum(c['gems'] for c in cross),'same_packets':len(same),'same_base':weight,
                    'same_delay_histogram':dict(sorted(Counter(delays).items())),
                    'same_base_weighted_delay_numerator':sum(groups[mid][c['group']]['gems']*c['delay_rounds'] for c in same),
                    'unmatched':sum(c['clear'] is None for c in caps)}
        rows.append(row)
    reports={}
    for p in ('discovery','confirm','control'):
        selected=[r for r in rows if r['partition']==p];phases={}
        for t in ('150','300','800',str(10**9)):
            phase={}
            for label in ('ours','rival'):
                agg={k:sum(r[label][t][k] for r in selected) for k in ('packets','total_base','cross_team_last_clear_packets','cross_base','cross_actual','same_packets','same_base','same_base_weighted_delay_numerator','unmatched')}
                h=Counter()
                for r in selected:h.update(r[label][t]['same_delay_histogram'])
                agg['same_delay_histogram']=dict(sorted(h.items()));agg['median_same_delay']=median(h.elements()) if h else None
                agg['base_weighted_same_delay']=agg['same_base_weighted_delay_numerator']/agg['same_base'] if agg['same_base'] else None
                assert agg['total_base']==values['reports'][p]['phases'][t][label]['base']
                phase[label]=agg
            phase['rival_minus_our_cross_base']=phase['rival']['cross_base']-phase['ours']['cross_base'];phases[t]=phase
        reports[p]={'games':len(selected),'phases':phases}
    result={'pass':True,'games':len(rows),'reports':reports,'rows':rows,'metadata_sha256':bench.digest(HERE/'LIVE111E_RUNTIME_CAMP_METADATA.json'),
            'capture_sha256':bench.digest(HERE/'LIVE111E_CAMP_ATTRIBUTION.json'),
            'limits':'Association with final camp-clear credit, not exclusive team damage, avoidable theft, counterfactual ownership or recoverable wins. Delay can be contested.'}
    write(HERE/'LIVE111E_WEIGHTED_CAPTURES.json',result)
    print({p:{t:{label:{k:v[label][k] for k in ('cross_team_last_clear_packets','cross_base','base_weighted_same_delay')} for label in ('ours','rival')} for t,v in r['phases'].items()} for p,r in reports.items()},flush=True)
