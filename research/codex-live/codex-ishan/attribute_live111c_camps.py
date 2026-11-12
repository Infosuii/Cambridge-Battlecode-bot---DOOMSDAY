"""EXP211: exact native clear/capture packets, with independent ledger checks."""
from collections import Counter, defaultdict
import json
from statistics import mean, median

import ablate_dev as bench
from engine3_pool import HERE, read
from freeze_engine3_discovery import write
from freeze_live111c_discovery import OUT, PREFIX


def audit(doc):
    events = []
    clears = []
    packets = defaultdict(list)
    for e in doc['events']:
        for x in e['entries']:
            if e['kind'] == 'campClear':
                assert x['target']['kind'] == 'campGroup' and float(x['value']) == 1
                clear = {'group':x['target']['id'],'team':e['owner']['team'],'round':x['timestamp']['round'],
                         'input':x['timestamp']['input'],'ordinal':x['timestamp']['ordinal'],'captured':False,'superseded':False}
                events.append((clear['ordinal'], 'clear', clear))
                clears.append(clear)
            elif e['kind'] == 'gemCollection' and x['context'] == 'campGroup':
                assert x['target']['kind'] == 'campGroup'
                packets[(x['target']['id'],x['timestamp']['input'])].append({'owner':e['owner'],**x})
    caps = []
    for (group,input_id),entries in packets.items():
        assert len({e['owner']['team'] for e in entries}) == 1
        assert len({e['timestamp']['round'] for e in entries}) == 1
        assert len({e['owner']['id'] for e in entries}) == len(entries)
        cap = {'group':group,'input':input_id,'round':entries[0]['timestamp']['round'],'team':entries[0]['owner']['team'],
               'ordinal':min(e['timestamp']['ordinal'] for e in entries),'gems':sum(float(e['value']) for e in entries),
               'capturers':len(entries),'shares':[{ 'id':e['owner']['id'],'name':e['owner']['name'],'gems':float(e['value'])} for e in entries]}
        caps.append(cap)
        events.append((cap['ordinal'],'capture',cap))
    latest = {}
    for ordinal,kind,event in sorted(events,key=lambda r:r[0]):
        group = event['group']
        if kind == 'clear':
            if group in latest:
                latest[group]['superseded'] = True
            latest[group] = event
        else:
            clear = latest.pop(group,None)
            event['clear'] = None if clear is None else {k:clear[k] for k in ('team','round','input','ordinal')}
            event['delay_rounds'] = None if clear is None else event['round'] - clear['round']
            if clear is not None:
                assert event['ordinal'] > clear['ordinal'] and event['delay_rounds'] >= 0
                clear['captured'] = True
                clear['capture_team'] = event['team']
                clear['capture_gems'] = event['gems']
    return clears,caps


def summary(rows):
    report = {'n':len(rows),'groups':len({r['group'] for r in rows})}
    for side in ('ours','rival'):
        cs=[c for r in rows for c in r[side]['captures']]
        cl=[c for r in rows for c in r[side]['clears']]
        matched=[c for c in cs if c['clear'] is not None]
        delays=[c['delay_rounds'] for c in matched if c['clear']['team']==c['team']]
        report[side]={'camp_gems':sum(c['gems'] for c in cs),'captures':len(cs),'clears':len(cl),
                      'mean_packet_gems':mean(c['gems'] for c in cs) if cs else None,
                      'split_packets':sum(c['capturers']>1 for c in cs),
                      'clears_captured_by_rival':sum(c['captured'] and c['capture_team']!=c['team'] for c in cl),
                      'clears_not_captured':sum(not c['captured'] for c in cl),
                      'superseded_uncaptured_clears':sum(c['superseded'] for c in cl),
                      'unmatched_capture_packets':len(cs)-len(matched),
                      'median_same_team_delay':median(delays) if delays else None,
                      'phases':{str(t):{'camp_gems':sum(c['gems'] for c in cs if c['round']<=t),'captures':sum(c['round']<=t for c in cs),
                                        'clears':sum(c['round']<=t for c in cl),'split_packets':sum(c['round']<=t and c['capturers']>1 for c in cs)} for t in (150,300,800)}}
    return report


if __name__=='__main__':
    frozen=read(HERE/f'{PREFIX}_DISCOVERY_SPLIT.json')['matches']
    resource={r['matchId']:r for r in read(HERE/f'{PREFIX}_RESOURCE_REPORT.json')['rows']}
    rows=[]
    for r in frozen:
        path=OUT/'summaries'/(r['matchId']+'.json')
        assert bench.digest(path)==resource[r['matchId']]['native_sha256']
        clears,caps=audit(read(path))
        ours='team'+r['side'].upper()
        rival='teamB' if ours=='teamA' else 'teamA'
        row={k:r[k] for k in ('matchId','opponent','partition','group')}
        for side,team in (('ours',ours),('rival',rival)):
            row[side]={'clears':[c for c in clears if c['team']==team],'captures':[c for c in caps if c['team']==team]}
            assert sum(c['gems'] for c in row[side]['captures'])==resource[r['matchId']][side]['camp']
            assert len(row[side]['clears'])==resource[r['matchId']][side]['clears']
        rows.append(row)
    reports={p:summary([r for r in rows if r['partition']==p]) for p in ('discovery','control','confirm')}
    result={'scope':'Exact native attribution; correlated outcome-selected cases, no causal strategy or win ceiling',
            'resource_recount_pass':True,'reports':reports,'rows':rows}
    write(HERE/f'{PREFIX}_CAMP_ATTRIBUTION.json',result)
    print(json.dumps(reports,indent=2),flush=True)
