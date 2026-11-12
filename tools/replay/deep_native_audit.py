"""Audit official summary JSON internally and against group metadata.

This does not read/reconcile a replay. Reports must keep that distinction.
Raw summaries remain local-only. Inputs are browser download paths plus match IDs.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
from deep_preflight import ROOT, save


def audit(d, metadata):
    checks = {'engine_2_0_0':d['match']['engineVersion']=='2.0.0',
              'rounds_match_metadata':d['match']['roundsStarted']==metadata['rounds']}
    side = 'teamA' if metadata['own_side']=='a' else 'teamB'
    checks['own_score_matches_metadata'] = int(next(t['submittedGems'] for t in d['teams'] if t['team']==side))==metadata['our_score']
    checks['opponent_score_matches_metadata'] = int(next(t['submittedGems'] for t in d['teams'] if t['team']!=side))==metadata['opponent_score']
    checks['outcome_matches_metadata'] = (d['match']['outcome']==side)==(metadata['result']=='win')
    draft = d['roster']['draft']
    champions = d['roster']['champions']
    checks['draft_roster_internal'] = bool(champions) and len({c['id'] for c in champions})==len(champions) and all(
        0 <= c['draftPick'] < len(draft) and draft[c['draftPick']]['team']==c['team'] and
        c['name'] in draft[c['draftPick']]['champion'].split(' & ') for c in champions)
    balances = []
    for c in d['champions']:
        m = c['metrics']
        lost = sum(int(e['value']) for series in d['events']
                   if series['owner'].get('kind')=='champion' and series['owner'].get('id')==c['id']
                   and series['kind']=='gemLoss' for e in series['entries'])
        gem_residual = int(m['collectedGems'])-int(m['submittedGems'])-lost-int(m['gems'])
        gold_residual = int(m['earnedGold'])+int(m['saleRefunds'])-int(m['spentGold'])-int(m['gold'])
        balances.append({'champion':c['id'],'gem_residual':gem_residual,'gold_residual':gold_residual})
    checks['gem_identity_native'] = all(x['gem_residual']==0 for x in balances)
    checks['gold_identity_native'] = all(x['gold_residual']==0 for x in balances)
    checks['team_bank_equals_champion_sum'] = all(
        int(t['submittedGems'])==sum(int(c['metrics']['submittedGems']) for c in d['champions'] if c['team']==t['team']) for t in d['teams'])
    return {'checks':checks,'passed':all(checks.values()),'balances':balances,
            'replay_reconciled':False,'draft_replay_compared':False,
            'caveat':'Native internal consistency and public metadata only; not independent replay validation.'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--downloads',type=Path,required=True,help='JSON [{match_id,path}] with main-container paths')
    a=p.parse_args()
    work=ROOT/'artifacts/local-only/deep-2026-10-28'
    catalog={r['match_id']:r for r in json.loads((work/'catalog.json').read_text())}
    rows=[]
    for item in json.loads(a.downloads.read_text()):
        mid=item['match_id']
        path=Path(item['path'])
        raw=path.read_bytes()
        if len(raw)>32*1024*1024:
            raise ValueError('Summary size cap exceeded')
        d=json.loads(raw)
        target=work/'summaries'/f'{mid}.summary.json'
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists() and target.read_bytes()!=raw:
            raise ValueError('Immutable summary changed')
        if path.resolve()!=target.resolve():
            shutil.copyfile(path,target)
        rows.append({'match_id':mid,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
                     **audit(d,catalog[mid])})
    report={'evidence_label':'measured','native_summaries':len(rows),
            'native_integrity_passed':sum(r['passed'] for r in rows),
            'replay_pairs_reconciled':0,'games':rows}
    save(ROOT/'research/deep-2026-10-28/NATIVE_AUDIT.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='games'}))
    for r in rows:
        if not r['passed']:
            print(json.dumps({'match_id':r['match_id'],'failed':[k for k,v in r['checks'].items() if not v],'balances':r['balances']}))


if __name__=='__main__':
    main()
