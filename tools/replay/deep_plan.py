"""Freeze cohorts from an official public ladder snapshot and v69 UI catalog.

This is metadata planning, not replay validation. Does not create any matches.
"""
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from deep_preflight import ROOT, Public, save


def main():
    out = ROOT / 'research/deep-2026-10-28'
    work = ROOT / 'artifacts/local-only/deep-2026-10-28'
    ledger_path = out / 'SCRIMMAGES.json'
    if ledger_path.exists() and any(r.get('group_id') for r in json.loads(ledger_path.read_text()).get('groups', [])):
        raise ValueError('Cohorts are frozen after the first study request; do not refresh this wave')
    ladder = Public(work).get('/api/v1/ladder?page=1&pageSize=100&category=all',
                              'public/ladder-cohorts.json')
    if ladder.get('unavailable'):
        raise RuntimeError('Official ladder unavailable; no substitute snapshot')
    teams = [{k: t.get(k) for k in ('teamId', 'name', 'rank', 'rating', 'category')}
             for t in ladder['teams']]
    by_id = {t['teamId']: t for t in teams}
    catalog = json.loads((work / 'catalog.json').read_text())
    losses = Counter(r['opponent_id'] for r in catalog if r['result'] == 'loss')
    totals = Counter(r['opponent_id'] for r in catalog)
    names = {r['opponent_id']: r['opponent'] for r in catalog}
    learn = sorted((t for t in teams if t['rank'] <= 5), key=lambda t:t['rank'])
    # Eight spaced ranks cover the entire requested 15-40 band without selecting on outcomes.
    ranks = [15, 18, 22, 25, 29, 33, 36, 40]
    climb = [dict(next(t for t in teams if t['rank'] == rank), reason='spaced rank band')
             for rank in ranks]
    worst = sorted(losses, key=lambda tid:(-losses[tid], tid))[:3]
    for tid in worst:
        if tid not in {t['teamId'] for t in climb}:
            climb.append(dict(by_id.get(tid, {'teamId':tid,'name':names[tid],'rank':None,'rating':None}),
                              reason='three largest loss counts in captured v69 catalog'))
    # Prefer four band members with the most existing observations, then proximity to target25.
    wave_climb = sorted(climb[:8], key=lambda t:(-totals[t['teamId']], abs(t['rank']-25), t['rank']))[:4]
    summary = {'evidence_label':'measured', 'recorded_at':datetime.now(timezone.utc).isoformat(),
               'server_updated_at':ladder.get('updatedAt'), 'n_teams':len(teams), 'teams':teams,
               'learn_cohort':learn, 'climb_cohort':climb, 'wave_1_climb':wave_climb,
               'loss_count_additions':[dict(by_id.get(tid, {'teamId':tid,'name':names[tid]}),
                                            losses=losses[tid], games=totals[tid]) for tid in worst],
               'cohorts_finalized':True,
               'caveat':'Loss-count additions use captured actual-v69 groups, not a complete activation-bounded census. Cohorts may overlap. Raw counts reflect unequal opponent exposure; they are not strength rankings.'}
    save(out / 'COHORTS.json', summary)
    ranked = defaultdict(lambda: {'games':0,'losses':0,'margin_sum':0})
    for r in catalog:
        if r['kind'] != 'ranked':
            continue
        x = ranked[r['map']]
        x['games'] += 1
        x['losses'] += r['result']=='loss'
        x['margin_sum'] += (r['our_score'] or 0) - (r['opponent_score'] or 0)
    save(out / 'RANKED_MAP_METADATA.json', dict(ranked))
    print(json.dumps({'learn':[(t['rank'],t['name']) for t in learn],
                      'wave_climb':[(t['rank'],t['name'],totals[t['teamId']]) for t in wave_climb],
                      'loss_additions':summary['loss_count_additions'],
                      'ranked_maps':sorted(ranked.items(), key=lambda kv:(-kv[1]['losses'],kv[1]['margin_sum']))[:12]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
