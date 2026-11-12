"""Reconcile reserved unranked requests with immutable public group metadata.

Uses authenticated UI receipts only for our private version number. Public API
supplies scores/maps/sides. This never creates groups or downloads private files.
"""
import argparse
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from deep_preflight import ROOT, OURS, save
from scout_public import Public


def interval(w,n):
    if not n:
        return [None,None]
    z=1.959963984540054
    q=w/n
    centre=(q+z*z/(2*n))/(1+z*z/n)
    half=z*math.sqrt(q*(1-q)/n+z*z/(4*n*n))/(1+z*z/n)
    return [centre-half,centre+half]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ui',type=Path,required=True)
    a=p.parse_args()
    out=ROOT/'research/deep-2026-10-28'
    work=ROOT/'artifacts/local-only/deep-2026-10-28/wave1'
    api=Public(work)
    ledger=json.loads((out/'SCRIMMAGES.json').read_text())
    ui={r['number']:r for r in json.loads(a.ui.read_text())}
    rows=[]
    for r in ledger['groups']:
        receipt=ui[r['number']]
        if not receipt.get('ui_anchor_verified') or receipt['id']!=r['group_id'] or receipt['platform_version']!=69:
            raise ValueError('UI identity/version receipt missing or inconsistent')
        d=api.json('/api/v1/match-groups/'+r['group_id'],f"groups/{r['group_id']}.json")
        got=[]
        for m in d['matches']:
            own=next(s for s in m['sides'] if s['teamId']==OURS)
            enemy=next(s for s in m['sides'] if s['teamId']!=OURS)
            got.append((m['mapId'],own['side']))
            if enemy['teamId']!=r['opponent_id'] or m['kind']!='unranked':
                raise ValueError('Opponent or match type disagrees with reservation')
            rows.append({'match_id':m['id'],'group_id':r['group_id'],'number':r['number'],
                         'opponent_id':r['opponent_id'],'opponent':r['opponent'],'cohort':r['cohort'],
                         'map':m['map'],'map_id':m['mapId'],'created_at':m['createdAt'],
                         'rounds':m.get('rounds'),'patch_id':m.get('patchId'),'own_side':own['side'],
                         'result':own.get('result'),'our_score':own.get('score'),
                         'opponent_score':enemy.get('score'),'status':m['status'],
                         'platform_version':69,'version_basis':'authenticated own-version UI, anchored to this group ID',
                         'kind':'unranked','reconciled':False})
        if got!=list(zip(r['map_ids'],r['sides'])):
            raise ValueError('Requested map order or sides changed: '+str(r['number']))
        r.update(status=d['group']['status'],metadata_request_check='passed',ui_platform_version=69,
                 results=[{k:x[k] for k in ['match_id','map','own_side','result','our_score','opponent_score','rounds','patch_id']}
                          for x in rows if x['group_id']==r['group_id']],
                 replay_download_status='not_available_in_workspace',replay_reconciled=False,
                 metadata_checked_at=datetime.now(timezone.utc).isoformat())
        save(out/'SCRIMMAGES.json',ledger)
    by_opponent=defaultdict(lambda:{'games':0,'wins':0,'losses':0,'margin_sum':0})
    by_map=defaultdict(lambda:{'games':0,'wins':0,'losses':0,'margin_sum':0})
    for r in rows:
        if r['status']!='finished':
            continue
        for target in (by_opponent[r['opponent']],by_map[r['map']]):
            target['games']+=1
            target['wins']+=r['result']=='win'
            target['losses']+=r['result']=='loss'
            target['margin_sum']+=(r['our_score'] or 0)-(r['opponent_score'] or 0)
    for target in [*by_opponent.values(),*by_map.values()]:
        target['win_rate_wilson_95']=interval(target['wins'],target['games'])
    ledger['status']='wave_1_metadata_checked_replays_pending'
    ledger['reservations_unresolved']=0
    ledger['wave_1_budget_remaining']=0
    ledger['wave_2_budget_remaining']=10
    save(out/'SCRIMMAGES.json',ledger)
    save(work/'ui-receipts.json',list(ui.values()))
    save(work/'catalog.json',rows)
    report={'evidence_label':'measured','groups':len(ledger['groups']),'games':len(rows),
            'finished_games':sum(r['status']=='finished' for r in rows),
            'wins':sum(r['result']=='win' for r in rows),'losses':sum(r['result']=='loss' for r in rows),
            'metadata_request_checks_passed':len(ledger['groups']),
            'reconciled_games':0,'metadata_only':True,
            'by_opponent':dict(by_opponent),'by_map':dict(by_map),
            'rows':rows,'caveat':'Descriptive outcome measurements, not detector evidence or a causal policy test. Wilson intervals assume independent games; paired/map dependence remains.'}
    save(out/'WAVE1_METADATA.json',report)
    print(json.dumps({k:report[k] for k in ['groups','games','finished_games','wins','losses','metadata_request_checks_passed']}))


if __name__=='__main__':
    main()
