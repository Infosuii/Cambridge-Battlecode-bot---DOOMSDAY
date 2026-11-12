"""Five matched unranked games per version: technical check, not ELO proof."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import random
import sys

BASE=Path(os.environ.get('BATTLECODE_ROOT',r'C:\projects\cambridge battlecode\work\agentic-improvement'))
sys.path.insert(0,str(BASE/'autonomy'))
import ladder
from native_capture import validate
from store import CONFIG, DATA, cli, live, now, save

ROOT=DATA/'experiments/bounded-delivery-retune-20261107-platform-spotcheck'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['baseline','challenger']);ap.add_argument('--version',type=int,required=True)
    args=ap.parse_args();ROOT.mkdir(parents=True,exist_ok=True)
    plan_path=ROOT/'plan.json'
    if plan_path.exists():plan=json.loads(plan_path.read_text(encoding='utf-8'))
    else:
        assert args.phase=='baseline' and args.version==111 and live()[0]==111
        teams=cli('ladder','--limit','100','--json')['teams'];me=next(t for t in teams if t['teamId']==CONFIG['team_id'])
        opponent=min((t for t in teams if t['teamId']!=CONFIG['team_id']),key=lambda t:(abs(t['rank']-me['rank']),t['rank'],t['teamId']))
        catalog=[];page=1
        while page:
            result=cli('maps','list','--page',page,'--limit','100','--json')
            catalog+=result['maps'];page=result.get('nextPage')
        assert len(catalog)>=5 and len({m['mapId'] for m in catalog})==len(catalog)
        save(ROOT/'live-map-catalog.json',{'at':now(),'maps':catalog})
        maps=random.Random(611881607).sample(sorted(catalog,key=lambda m:(m['name'],m['mapId'])),5)
        plan={'at':now(),'baseline_version':111,'our_team':CONFIG['team_id'],'opponent':opponent['teamId'],
              'our_rank_at_selection':me['rank'],'opponent_rank_at_selection':opponent['rank'],
              'maps':[m['name'] for m in maps],'map_ids':[m['mapId'] for m in maps],'sides':['a','b','a','b','a'],
              'selection':'Nearest current ladder rank; five published maps sampled once with seed611881607, independent of win/loss labels.',
              'scope':'Five matched map/side games with opponent bot pinned by source-group. This is a deployment/technical spot check, not powered strength or ELO evidence. Server seed parity is not asserted.'}
        save(plan_path,plan)
    root=ROOT/args.phase;root.mkdir(exist_ok=True)
    request=root/'request.json'
    if request.exists():
        saved=json.loads(request.read_text(encoding='utf-8'));assert saved['version']==args.version;gid=saved['group']
    else:
        source=None
        if args.phase=='challenger':
            baseline=json.loads((ROOT/'baseline/report.json').read_text(encoding='utf-8'))
            assert baseline['complete'] and args.version!=111;source=baseline['group']
        gid=ladder.queue(plan['opponent'],plan['map_ids'],plan['sides'],args.version,source=source,tag='delivery-20261108:map-ids:'+args.phase)
        save(request,{'version':args.version,'group':gid,'source_group':source,'at':now()})
    matches=ladder.collect([gid],timeout=1800)[gid];rows=[]
    for position,meta in enumerate(matches):
        team=next(t for t in meta['teams'] if t['teamId']==CONFIG['team_id'])
        assert meta['map']==plan['maps'][position] and team['side']==plan['sides'][position]
        native_path=root/(meta['matchId']+'.json')
        if not native_path.exists():cli('matches','summary',meta['matchId'],'--json','-o',native_path,parse=False)
        native=json.loads(native_path.read_text(encoding='utf-8'));own='team'+team['side'].upper()
        faults={s:validate(native,s,CONFIG['engine']) for s in ('teamA','teamB')}
        fuel=sum(len(e['entries']) for e in native['events'] if e['kind']=='fuelExhausted' and e['owner'].get('team')==own)
        outcome=native['match']['outcome'];score=1. if outcome==own else .5 if outcome=='draw' else 0.
        rows.append({'match':meta['matchId'],'map':meta['map'],'side':team['side'],'score':score,'our_version':args.version,
                     'both_team_faults':faults,'codes':native['diagnostics']['codes'],'own_faults':faults[own],
                     'own_fuel_exhaustions':fuel,'engine':native['match']['engineVersion'],'engine_build':native['match']['engineBuildHash'],
                     'map_hash':native['match']['mapHash'],
                     'native_sha256':hashlib.sha256(native_path.read_bytes()).hexdigest()})
    report={'at':now(),'complete':True,'group':gid,'version':args.version,'rows':rows,
            'score':sum(r['score'] for r in rows),'games':len(rows),'own_faults':sum(r['own_faults'] for r in rows),
            'scope':plan['scope']}
    if args.phase=='challenger':
        old=json.loads((ROOT/'baseline/report.json').read_text(encoding='utf-8'))
        assert [(r['map'],r['side']) for r in rows]==[(r['map'],r['side']) for r in old['rows']]
        assert [r['map_hash'] for r in rows]==[r['map_hash'] for r in old['rows']], 'Server map bytes changed between versions'
        report['baseline_score']=old['score'];report['score_change']=report['score']-old['score']
    save(root/'report.json',report)
    print(json.dumps(report),flush=True)

if __name__=='__main__':main()
