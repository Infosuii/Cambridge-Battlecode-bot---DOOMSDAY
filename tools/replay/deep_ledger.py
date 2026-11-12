"""Plan/reserve/confirm unranked UI requests; never sends a website request.

Reservations consume budget until resolved, preventing duplicate uncertain writes.
"""
import argparse
import json
import uuid
from datetime import datetime, timezone
from deep_preflight import ROOT, save

OUT = ROOT / 'research/deep-2026-10-28'
LEDGER = OUT / 'SCRIMMAGES.json'


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['plan','reserve','confirm','status'])
    p.add_argument('--number', type=int)
    p.add_argument('--group')
    p.add_argument('--source-group')
    p.add_argument('--state', choices=['queued','playing','finished','error'])
    a = p.parse_args()
    ledger = json.loads(LEDGER.read_text())
    if a.action == 'plan':
        if ledger['groups']:
            raise ValueError('Existing plan/reservations are immutable; inspect the ledger')
        c = json.loads((OUT / 'COHORTS.json').read_text())
        catalog = json.loads((ROOT / 'artifacts/local-only/deep-2026-10-28/catalog.json').read_text())
        map_ids = {r['map']:r['map_id'] for r in catalog}
        maps = {
            'Learn':['00reverse_spiral','01boss_battle','01islands','01shortcut','02treasure_box'],
            'Climb':['00galaxy','00reverse_spiral','00road_of_riches','01islands','02harvest'],
        }
        groups = []
        for cohort, opponents in [('Learn',c['learn_cohort'][:3]), ('Climb',c['wave_1_climb'])]:
            for team in opponents:
                existing = [r for r in catalog if r['opponent_id']==team['teamId']]
                source = max(existing,key=lambda r:r['created_at'])['group_id'] if existing else None
                for mirror in range(2):
                    groups.append({'number':len(groups)+1,'wave':1,'cohort':cohort,
                                   'opponent_id':team['teamId'],'opponent':team['name'],
                                   'rank_at_plan':team['rank'],'maps':maps[cohort],
                                   'map_ids':[map_ids[m] for m in maps[cohort]],
                                   'sides':(['a','b','a','b','a'] if mirror==0 else ['b','a','b','a','b']),
                                   'pair':len(groups)//2+1,'mirror':mirror,
                                   'status':'planned','group_id':None,
                                   'opponent_source_group':source,
                                   'opponent_version_id':None,
                                   'pin_policy':'previous match source; if first group has no history, current bot then pin mirror to first group',
                                   'purpose':'coverage and paired sides; descriptive, no causal claim',
                                   'our_platform_version_expected':69})
        ledger.update(groups=groups,status='wave_1_planned',planned_at=now(),
                      quota_observed={'remaining':50,'maximum':50,'basis':'authenticated Play unranked UI','observed_at':now()},
                      live_submission_verified=True,source_hash_verified=False,
                      source_identity_basis='user-provided archive LIVE_SOURCE.json; no independent server hash',
                      activation_time=None,
                      version_attribution='explicit platform-v69 UI rows; do not infer from time',
                      map_selection='RANKED_MAP_METADATA.json: reverse_spiral 3 losses/3 games; treasure_box and harvest 2/2; galaxy and shortcut 2/3; road_of_riches 2/4. Add boss_battle 1/1 and islands as uncertainty/geometry coverage. Counts are metadata-only, confounded by opponents. No causal family labels inferred from names.')
    elif a.action in ['reserve','confirm']:
        row = next(r for r in ledger['groups'] if r['number']==a.number)
        if a.action=='reserve':
            if row['status']!='planned':
                raise ValueError('Request already reserved/sent; never retry an uncertain write')
            consumed = [r for r in ledger['groups'] if r['status']!='planned']
            if len(consumed)>=ledger['total_group_cap'] or sum(r['wave']==1 for r in consumed)>=ledger['wave_1_group_cap']:
                raise ValueError('Budget exhausted')
            if a.source_group:
                row['opponent_source_group']=str(uuid.UUID(a.source_group))
            if row['mirror'] and row['opponent_source_group'] is None:
                first = next(r for r in ledger['groups'] if r['pair']==row['pair'] and not r['mirror'])
                if not first['group_id']:
                    raise ValueError('Confirm first group before pinning its mirror')
                row['opponent_source_group']=first['group_id']
            row.update(status='reserved',reserved_at=now())
        else:
            gid = str(uuid.UUID(a.group))
            if row['status'] not in ['reserved','queued','playing','finished']:
                raise ValueError('Reserve before creating a match')
            if row['group_id'] not in [None,gid]:
                raise ValueError('Cannot replace a confirmed request')
            if any(r['group_id']==gid and r is not row for r in ledger['groups']):
                raise ValueError('Group already claimed by a different reservation')
            row.update(group_id=gid,status=a.state or 'queued',confirmed_at=now())
        ledger['groups_queued']=sum(r['group_id'] is not None for r in ledger['groups'])
        ledger['games_requested']=5*ledger['groups_queued']
        ledger['reservations_unresolved']=sum(r['status']=='reserved' for r in ledger['groups'])
    if a.action!='status':
        save(LEDGER, ledger)
    print(json.dumps({k:ledger.get(k) for k in ['status','groups_queued','games_requested','reservations_unresolved']}))
    if a.number:
        print(json.dumps(next(r for r in ledger['groups'] if r['number']==a.number),ensure_ascii=False))


if __name__ == '__main__':
    main()
