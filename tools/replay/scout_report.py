"""Validate and compact the bounded study's local replay decodes.

No training arrays or raw actions are copied to the report directory.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[2]
DRAFT = ['Ryth','Vesper Vale','Vendetta','Cassi & Issac','Stellar','Prism',
         'Marcella','Willow','Ren','Varg','Tavi','Heart of Ruin']
BODY = ['Ryth','Vesper Vale','Vendetta','Cassi','Issac','Stellar','Prism',
        'Marcella','Willow','Ren','Varg','Tavi','Heart of Ruin']


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def save(p, value):
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8', newline='\n')


def median(rows, key):
    xs = [r[key] for r in rows if r.get(key) is not None]
    return statistics.median(xs) if xs else None


def compact_body(c):
    items = c['items']
    # Emblem counts are exact inventory counts, not inferred purchase order.
    return dict(champion=BODY[c['type']], team=c['team'], alive=c['alive'],hp=c['hp'], max_hp=c['max_hp'],
                gems=c['gems'], gold=c['gold'], earned_gold=c['earned_gold'],
                emblems={family:sum(items[o+1:o+6:2]) for family,o in
                         [('monster',0),('power',6),('durability',12),('treasure',18),
                          ('jungle',24),('home',30),('bruiser',36)]})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
    selection = read(a.work/'selection.json')
    ladder = read(a.work/'ladder.json')
    rankings = {t['teamId']: t for t in ladder['teams']}
    normal = {r['replay'].removesuffix('.repl26a'): r
              for r in map(json.loads, (a.work/'decoded.jsonl').read_text().splitlines())}
    downloads = {r['match_id']:r for r in read(a.work/'downloads.json')}
    rows, matches, cases, curves, checks, inventories = [], [], [], [], [], []
    for m in selection:
        mid = m['id']; n = normal[mid]; s = read(a.work/'states'/f'{mid}.json')
        sides = sorted(m['sides'], key=lambda t:t['side'])
        scores = [t['score'] for t in s['teams']]
        actual_drafts = [[int(x) for x in side['draft']] for side in sides]
        winner = next((i+1 for i,t in enumerate(sides) if t['result']=='win'), None)
        c = dict(match_id=mid, normal_decode=n['ok'], census_decode=s['ok'],
                 scores_match_metadata=scores==[t['score'] for t in sides],
                 rounds_match_metadata=s['rounds']==m['rounds'],
                 outcome_match_metadata=s['outcome']==winner,
                 drafts_match_metadata=s['drafts']==actual_drafts,
                 scores_match_standard=scores==n['submitted_gems'],
                 steps_match_standard=s['steps']==n['steps'],
                 fuel_matches_standard=sum(t['actions'].get('fuel_exhausted',0) for t in s['teams'])==n['fuel_exhausted_turns'],
                 errors_match_standard=sum(t['actions'].get('error',0) for t in s['teams'])==n['error_turns'],
                 action_counts_match_standard=all(sum(t['actions'].get(k,0) for t in s['teams'])==v for k,v in n['counts'].items()),
                 replay_sha256=s['replay_sha256']==downloads[mid]['replay_sha256'],
                 no_unknown_actor_actions=s['unknown_actor_actions']==0)
        c['passed'] = all(v for k,v in c.items() if k!='match_id')
        checks.append(c)
        if not c['passed']:
            raise ValueError('Study validation failed: '+json.dumps(c))
        focal = next(i for i,t in enumerate(sides) if t['teamId']==m['focal_team'])
        match = dict(match_id=mid,group_id=m['group_id'],map=m['map'],map_id=m['mapId'],
                     created_at=m['createdAt'],cohort=m['cohort'],focal_side=focal,
                     end_reason=m.get('endReason'),
                     rounds=s['rounds'],scores=scores,winner_side=s['outcome']-1,
                     teams=[t['teamName'] for t in sides],team_ids=[t['teamId'] for t in sides],
                     drafts=[[DRAFT[x] for x in d] for d in actual_drafts],
                     version_verified=m.get('version_verified',False),
                     replay_sha256=s['replay_sha256'],bundle_sha256=downloads[mid]['bundle_sha256'],
                     bundle_bytes=downloads[mid]['bundle_bytes'],replay_bytes=downloads[mid]['replay_bytes'],
                     replay_header=downloads[mid]['replay_header'],
                     source_url='https://2026a.battlecode.co.uk/game/match-groups/'+m['group_id'])
        matches.append(match)
        curves.append(dict(match_id=mid,map=m['map'],focal_side=focal,curve=s['curve']))
        for cp in s['checkpoints']:
            if cp['round'] not in [250,500,1000]:
                continue
            for body in cp['champions']:
                bc=compact_body(body)
                inv=dict(match_id=mid,map=m['map'],cohort=m['cohort'],round=cp['round'],
                         is_focal=body['team']==focal,team=sides[body['team']]['teamName'],
                         champion=bc['champion'],body_id=body['id'],alive=bc['alive'],hp=bc['hp'],
                         max_hp=bc['max_hp'],gems=bc['gems'],gold=bc['gold'],earned_gold=bc['earned_gold'])
                inv.update({k+'_emblems':v for k,v in bc['emblems'].items()})
                inventories.append(inv)
        for i, t in enumerate(s['teams']):
            side=sides[i]; body_rounds=max(1,s['rounds']*len(t['champions']))
            row=dict(match_id=mid,map=m['map'],cohort=m['cohort'],is_focal=i==focal,
                     team=side['teamName'],team_id=side['teamId'],side=['a','b'][i],
                     rank=rankings.get(side['teamId'],{}).get('rank'),
                     rating=rankings.get(side['teamId'],{}).get('rating'),
                     result=side['result'],rounds=s['rounds'],bodies=len(t['champions']),
                     score=t['score'],opponent_score=scores[1-i],final_carried=t['final_carried'],
                     first_bank_round=t['first_bank_round'],banks=t['bank_events'],median_bank=t['median_bank'],
                     peak_single_bag=t['peak_single_bag_round_sample'],
                     rounds_with_100_bag=t['rounds_with_100_bag'],
                     physical_body_deaths=t['physical_body_deaths'],kills=t['kills'],
                     deaths_per_1000_body_rounds=1000*t['physical_body_deaths']/body_rounds,
                     earned_gold=t['earned_gold'],unspent_gold=t['unspent_gold'],
                     fuel_exhausted=t['actions'].get('fuel_exhausted',0),
                     errors=t['actions'].get('error',0),draft=', '.join(match['drafts'][i]))
            for k in ['attack','cast','move','dash_move','buy','recall','ward','submit_start']:
                row[k]=t['actions'].get(k,0)
                row[k+'_per_1000_body_rounds']=1000*row[k]/body_rounds
            rows.append(row)
        if m['map'] in ['01boss_battle','00stampede','01concentrated_wealth']:
            important=sorted(s['groups'],key=lambda g:g['gems'],reverse=True)[:3]
            important=[dict(g,**{k:[compact_body(c) for c in g[k]]
                                for k in ['near_first_damage','near_first_clear'] if k in g})
                       for g in important]
            cases.append(dict(match_id=mid,map=m['map'],teams=match['teams'],scores=scores,
                              drafts=match['drafts'],focal_side=focal,groups=important,
                              banks=[t['banks'] for t in s['teams']],
                              checkpoints=[dict(round=c['round'],champions=[compact_body(b) for b in c['champions']])
                                           for c in s['checkpoints'] if c['round'] in [250,500,1000,1500]]))
    focal_rows=[r for r in rows if r['is_focal']]
    summaries={}
    for cohort in sorted({r['cohort'] for r in focal_rows}):
        rs=[r for r in focal_rows if r['cohort']==cohort]
        summaries[cohort]=dict(games=len(rs),maps=len({r['map'] for r in rs}),
          wins=sum(r['result']=='win' for r in rs),
          medians={k:median(rs,k) for k in ['score','final_carried','first_bank_round','median_bank',
            'physical_body_deaths','peak_single_bag','earned_gold','unspent_gold',
            'deaths_per_1000_body_rounds','cast_per_1000_body_rounds','attack_per_1000_body_rounds']},
          fuel_exhausted=sum(r['fuel_exhausted'] for r in rs),errors=sum(r['errors'] for r in rs))
    save(a.out/'matches.json',matches)
    index=['# Replay index — 25 October 2026','',
           'Each link opens the official five-game match group. The match ID and map identify the selected replay.',
           'Scores are submitted gems; a tied score can still have a winner by tiebreak. Raw files remain local.','',
           '| Cohort | Match ID | Map | Team A | Team B | Score A–B | Winner |',
           '|---|---|---|---|---|---|---|']
    for m in matches:
        esc=lambda v:str(v).replace('|','\\|').replace('\n',' ')
        fields=[m['cohort'],f"[{m['match_id']}]({m['source_url']})",m['map'],
                *m['teams'],f"{m['scores'][0]}–{m['scores'][1]}",m['teams'][m['winner_side']]]
        index.append('| '+' | '.join(map(esc,fields))+' |')
    (a.out/'MATCH_INDEX.md').write_text('\n'.join(index)+'\n',encoding='utf-8',newline='\n')
    save(a.out/'ladder_snapshot.json',dict(teams=[{k:t[k] for k in ['teamId','name','rank','rating']}
                                                for t in ladder['teams']],
                                          revision=ladder.get('revision'),freshness=ladder.get('freshness')))
    save(a.out/'checks.json',checks)
    save(a.out/'curves.json',curves)
    save(a.out/'objective_cases.json',cases)
    draft_counts={}
    for cohort in sorted({m['cohort'] for m in matches}):
        ms=[m for m in matches if m['cohort']==cohort]
        draft_counts[cohort]=dict(games=len(ms),counts=dict(Counter(c for m in ms for c in m['drafts'][m['focal_side']])))
    save(a.out/'draft_audit.json',dict(cohorts=draft_counts,
      mirror_pick_matches=[dict(match_id=m['match_id'],map=m['map'],
                                shared_picks=sorted(set(m['drafts'][0])&set(m['drafts'][1])))
                           for m in matches if set(m['drafts'][0])&set(m['drafts'][1])]))
    inventory_summary=[]
    for rnd in [250,500,1000]:
        for cohort in sorted({r['cohort'] for r in inventories}):
            rs=[r for r in inventories if r['is_focal'] and r['cohort']==cohort and r['round']==rnd]
            inventory_summary.append(dict(round=rnd,cohort=cohort,physical_bodies=len(rs),
                matches=len({r['match_id'] for r in rs}),
                bodies_with_emblem={f:sum(r[f+'_emblems']>0 for r in rs)
                    for f in ['treasure','durability','monster','jungle','bruiser']},
                median_earned_gold=median(rs,'earned_gold')))
    save(a.out/'inventory_summary.json',inventory_summary)
    map_comparison=[]
    for name in sorted({r['map'] for r in focal_rows}):
        for cohort in sorted({r['cohort'] for r in focal_rows}):
            rs=[r for r in focal_rows if r['map']==name and r['cohort']==cohort]
            if rs:
                map_comparison.append(dict(map=name,cohort=cohort,games=len(rs),
                    wins=sum(r['result']=='win' for r in rs),
                    banking_games=sum(r['first_bank_round'] is not None for r in rs),
                    **{k:median(rs,k) for k in ['score','first_bank_round','final_carried',
                       'physical_body_deaths','deaths_per_1000_body_rounds','fuel_exhausted']}))
    with (a.out/'map_comparison.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(map_comparison[0]),lineterminator='\n');w.writeheader();w.writerows(map_comparison)
    with (a.out/'teams.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    with (a.out/'inventory_checkpoints.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(inventories[0]),lineterminator='\n');w.writeheader();w.writerows(inventories)
    save(a.out/'summary.json',dict(cohorts=summaries,
         ladder_freshness=ladder.get('freshness'),ladder_revision=ladder.get('revision'),
         top6=[{k:t[k] for k in ['teamId','name','rank','rating']} for t in ladder['teams'][:6]],
         all_checks_passed=all(c['passed'] for c in checks),
         downloads_bytes=sum(m['bundle_bytes'] for m in matches),
         sha256=dict(standard_decoded_local=hashlib.sha256((a.work/'decoded.jsonl').read_bytes()).hexdigest()),
         engine_assets=read(a.work/'states/run.json')['pinned'],
         definitions=dict(first_bank_round='First positive submitted-score delta; exact engine step, not channel start.',
          physical_body_deaths='Sum of final per-body engine KDA deaths; Cassi and Issac counted separately.',
          peak_single_bag='Maximum carried gems in one physical body at a round-boundary census; may miss within-round peaks.',
          first_clear_round='First round census where every camp in the group has zero health; not capture completion.',
          near_first_clear='Alive bodies within Chebyshev distance 8 at the first clear census; proximity is not damage attribution.',
          rates='Actions or deaths / (final round times physical body count), scaled by 1000; includes dead-time.',
          cohorts='Top rows are the preselected focal side only, four games per top-six team; ours are post-deployment, exact platform version hidden.')))
    print(json.dumps(dict(matches=len(matches),team_rows=len(rows),validated=len(checks),summaries=summaries),indent=2))


if __name__=='__main__':
    main()
