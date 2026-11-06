"""EXP286 independently aggregate native packets, base rewards and all phase tables."""
from collections import defaultdict
from zipfile import ZipFile
import ablate_dev as bench
from engine3_pool import HERE,ENGINE,read
from freeze_engine3_discovery import write
from live111e_context import OUT

if __name__=='__main__':
    savedpath=HERE/'LIVE111E_CAMP_VALUE_ATTRIBUTION.json';saved=read(savedpath);plan=read(HERE/'LIVE111E_CAMP_VALUE_PLAN.json')
    assert saved['pass'] and bench.digest(HERE/'LIVE111E_CAMP_VALUE_PLAN.json')==saved['plan_sha256']
    assert bench.digest(HERE/'extract_runtime_camps.mjs')==plan['decoder_sha256']
    metadata=read(HERE/'LIVE111E_RUNTIME_CAMP_METADATA.json');assert bench.digest(HERE/'LIVE111E_RUNTIME_CAMP_METADATA.json')==saved['metadata_sha256']
    groups={r['matchId']:{g['handle']:g for g in r['groups']} for r in metadata['rows']}
    jobs={r['matchId']:r for r in plan['jobs']};fresh=[];entries=0
    for row in saved['rows']:
        mid=row['matchId'];job=jobs[mid];native=OUT/'summaries'/(mid+'.json');assert bench.digest(native)==job['native_sha256']
        d=read(native);assert d['match']['engineBuildHash']==ENGINE and d['match']['mapHash']==job['map_sha256'] and d['diagnostics']['detailedCaptureComplete']
        archive=OUT/'replays'/(mid+'.zip');assert bench.digest(archive)==job['archive_sha256']
        with ZipFile(archive) as z:
            import hashlib
            assert hashlib.sha256(z.read('replay.repl26a')).hexdigest()==job['replay_sha256']
        roster={c['id']:c['team'] for c in d['champions']};events=defaultdict(list);clears=[]
        for e in d['events']:
            for x in e['entries']:
                if e['kind']=='gemCollection' and x['context']=='campGroup':
                    assert x['target']['kind']=='campGroup';events[e['owner']['team'],x['target']['id'],x['timestamp']['input']].append((e['owner'],x));entries+=1
                elif e['kind']=='campClear':clears.append((e['owner']['team'],x['target']['id'],x['timestamp']['round']))
        our_team=next(r['side'].upper() for r in read(HERE/'LIVE111E_DISCOVERY_SPLIT.json')['matches'] if r['matchId']==mid)
        teams={'ours':'team'+our_team,'rival':'team'+('B' if our_team=='A' else 'A')};rec={k:row[k] for k in ('matchId','partition','opponent')}
        for label,team in teams.items():
            phases={}
            for t in (150,300,800,10**9):
                totals={k:0 for k in ('packets','clears','actual','base','residual','base_clear_gems','positive_residual_packets','negative_residual_packets')}
                tables={k:defaultdict(lambda:defaultdict(float)) for k in ('composition','sharing','recipient_hero_shares')}
                for (owner,gid,input_id),values in events.items():
                    if owner!=team or values[0][1]['timestamp']['round']>t:continue
                    assert len({x[1]['timestamp']['round'] for x in values})==1 and len({x[0]['id'] for x in values})==len(values)
                    g=groups[mid][gid];actual=sum(float(x['value']) for _,x in values);base=g['gems'];residual=actual-base
                    for k,v in (('packets',1),('actual',actual),('base',base),('residual',residual),('positive_residual_packets',int(residual>0)),('negative_residual_packets',int(residual<0))):totals[k]+=v
                    comp=','.join(map(str,sorted(c['type'] for c in g['camps'])))
                    for category,key in (('composition',comp),('sharing',str(len(values)))):
                        for k,v in (('packets',1),('base',base),('actual',actual),('residual',residual)):tables[category][key][k]+=v
                    for actor,x in values:
                        tables['recipient_hero_shares'][actor['name']]['recipient_packets']+=1
                        tables['recipient_hero_shares'][actor['name']]['actual_share_gems']+=float(x['value'])
                cl=[gid for owner,gid,r in clears if owner==team and r<=t]
                totals['clears']=len(cl);totals['base_clear_gems']=sum(groups[mid][gid]['gems'] for gid in cl)
                for category,table in tables.items():totals[category]={k:dict(v) for k,v in table.items()}
                assert totals==row[label][str(t)],(mid,label,t)
                phases[str(t)]=totals
            rec[label]=phases
        fresh.append(rec)
    for p,report in saved['reports'].items():
        selected=[r for r in fresh if r['partition']==p];assert len(selected)==report['games']
        for t,phase in report['phases'].items():
            for label in ('ours','rival'):
                expected=phase[label]
                for k in ('packets','clears','actual','base','residual','base_clear_gems','positive_residual_packets','negative_residual_packets'):
                    assert sum(r[label][t][k] for r in selected)==expected[k]
                for category in ('composition','sharing','recipient_hero_shares'):
                    table=defaultdict(lambda:defaultdict(float))
                    for r in selected:
                        for key,values in r[label][t][category].items():
                            for k,v in values.items():table[key][k]+=v
                    assert {k:dict(v) for k,v in table.items()}==expected[category]
                assert expected['actual']==expected['base']+expected['residual']
            assert phase['ours_minus_rival']=={k:phase['ours'][k]-phase['rival'][k] for k in ('actual','base','residual','packets','clears','base_clear_gems')}
    report={'pass':True,'native_games_reopened':len(fresh),'recipient_entries':entries,'result_sha256':bench.digest(savedpath),
            'metadata_sha256':saved['metadata_sha256'],'all_phase_composition_sharing_recipient_tables_match':True,
            'scope':'Native exact accounting only; residual mechanisms and causal policy unproven.'}
    write(HERE/'LIVE111E_CAMP_VALUE_RECOUNT.json',report);print(report,flush=True)
