"""Freeze fresh post-capture cells and whole-group confirmation before reading metrics."""
from collections import Counter,defaultdict
from datetime import datetime,timezone
from hashlib import sha256
import importlib.util
import json
import sys

import ablate_dev as bench
from engine3_pool import CLI,CLI_HASH,HERE,read
from freeze_engine3_discovery import write

OUT=bench.CACHE/'live111c-discovery-20261106'
PREFIX='LIVE111C'


if __name__=='__main__':
    assert bench.digest(CLI)==CLI_HASH
    previous=read(HERE/'LIVE111B_DISCOVERY_SPLIT.json')
    cutoff=datetime.fromisoformat(previous['created_utc'])
    old_ids={r['matchId'] for r in previous['matches']}
    old_groups={r['group'] for r in previous['matches']}
    earlier=read(HERE/'LIVE111_DISCOVERY_SPLIT.json')
    old_ids.update(r['matchId'] for r in earlier['matches'])
    old_groups.update(r['group'] for r in earlier['matches'])
    OUT.mkdir();raw=OUT/'raw';raw.mkdir()
    spec=importlib.util.spec_from_file_location('losses_recent',bench.ROOT/'tools/ladder/losses_recent.py')
    collector=importlib.util.module_from_spec(spec);spec.loader.exec_module(collector)
    collector.CLI=str(CLI);original=collector.cli_json;snapshots=[]
    def capture(args,*more,**kwargs):
        result=original(args,*more,**kwargs)
        name=f'{len(snapshots):03d}-{args[0]}.json';write(raw/name,result)
        snapshots.append({'args':args,'path':name,'sha256':bench.digest(raw/name)})
        return result
    collector.cli_json=capture;collector.download=lambda *args:None
    sys.argv=[str(spec.origin),'--hours','48','--min-rating','0','--out',str(OUT/'inventory48'),'--replays',str(OUT/'unused-replays')]
    collector.main()
    ladder=read(OUT/'inventory48/ladder.json');ours=ladder['DOOMSDAY']
    census={}
    for snap in snapshots:
        if snap['args'][0]!='matches':continue
        kind=snap['args'][snap['args'].index('--kind')+1]
        for row in read(raw/snap['path'])['matches']:
            census[row['matchId']]={**row,'kind':row.get('kind',kind)}
    candidates=[]
    for m in census.values():
        group=m.get('groupId') or m['matchId']
        if m['status']!='finished' or datetime.fromisoformat(m['createdAt'].replace('Z','+00:00'))<=cutoff or m['matchId'] in old_ids or group in old_groups:continue
        us=next(t for t in m['teams'] if t['name']=='DOOMSDAY')
        rival=next(t for t in m['teams'] if t['name']!='DOOMSDAY')
        if any(t['engineVersion']!='3.0.0' for t in m['teams']):continue
        if rival['name'] not in {'QS2isLaw','0xDEADBEEF','bentheboss'} and ladder.get(rival['name'],{}).get('rating',-1)<=ours['rating']:continue
        signature=[rival['name'],m['map'],us['side'],us.get('draftPicks'),rival.get('draftPicks')]
        cell=sha256(json.dumps(signature,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        candidates.append({'matchId':m['matchId'],'group':group,'createdAt':m['createdAt'],'map':m['map'],'side':us['side'],'opponent':rival['name'],'result':us['result'],'kind':m['kind'],
                           'our_draft':us.get('draftPicks'),'their_draft':rival.get('draftPicks'),'cell_key':cell})
    by_cell=defaultdict(list)
    for r in candidates:by_cell[r['cell_key']].append(r)
    representatives=[min(rs,key=lambda r:sha256(r['matchId'].encode()).hexdigest()) for rs in by_cell.values()]
    losses=[];wins=[]
    for r in representatives:
        bucket=int(sha256(r['group'].encode()).hexdigest(),16)%3
        if r['result']=='loss':losses.append({**r,'partition':'confirm' if bucket==0 else 'discovery'})
        elif r['result']=='win' and bucket!=0:wins.append({**r,'partition':'control'})
    wins=sorted(wins,key=lambda r:sha256(r['matchId'].encode()).hexdigest())[:18]
    rows=sorted(losses,key=lambda r:r['createdAt'])+wins
    assert len({r['cell_key'] for r in rows})==len(rows)
    assert not ({r['group'] for r in rows if r['partition']=='confirm'} & {r['group'] for r in rows if r['partition']!='confirm'})
    result={'created_utc':datetime.now(timezone.utc).isoformat(),'source':'INFERRED111 interval only; hidden historical source/opponent binaries not supplied by listings',
            'after_previous_capture':cutoff.isoformat(),'previous_split_sha256':bench.digest(HERE/'LIVE111B_DISCOVERY_SPLIT.json'),'our_ladder':ours,
            'named_rivals':{n:ladder.get(n) for n in ('QS2isLaw','0xDEADBEEF','bentheboss')},'counts':dict(Counter(r['partition'] for r in rows)),
            'raw_eligible':len(candidates),'unique_visible_cells':len(representatives),'duplicate_rows_discarded':len(candidates)-len(representatives),
            'cells_with_outcome_disagreement':sum(len({r['result'] for r in rs})>1 for rs in by_cell.values()),'snapshots':snapshots,'matches':rows}
    write(HERE/f'{PREFIX}_DISCOVERY_SPLIT.json',result)
    write(HERE/f'{PREFIX}_DISCOVERY_REPLAY_SAMPLE.json',{'selection':'All frozen EXP208 cases and controls; no metric-based replay selection','split_sha256':bench.digest(HERE/f'{PREFIX}_DISCOVERY_SPLIT.json'),'matches':rows})
    print({k:result[k] for k in ('counts','our_ladder','named_rivals','raw_eligible','unique_visible_cells','duplicate_rows_discarded','cells_with_outcome_disagreement')},flush=True)
