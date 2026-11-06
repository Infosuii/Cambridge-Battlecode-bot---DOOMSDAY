"""EXP239 frozen own-view comparison without pretending to recover private bot state."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import os
import subprocess

import ablate_dev as bench
from discovery_metrics import timeline
from engine3_pool import HERE, read
from freeze_engine3_discovery import write
from freeze_live111d_discovery import OUT, PREFIX


if __name__ == '__main__':
    index = read(HERE / f'{PREFIX}_DISCOVERY_SPLIT.json')['matches']
    discovery = [r for r in index if r['partition'] == 'discovery']
    counts = Counter(r['opponent'] for r in discovery)
    opponents = (['bentheboss'] if counts['bentheboss'] else [])
    opponents += [n for n in sorted(counts, key=lambda n: (-counts[n], n)) if n not in opponents][:2]
    output = OUT / 'turning-point-views'
    output.mkdir()
    cases = []
    for name in opponents:
        chosen = min((r for r in discovery if r['opponent'] == name), key=lambda r: sha256(r['matchId'].encode()).hexdigest())
        path = OUT / 'summaries' / (chosen['matchId'] + '.json')
        doc = read(path)
        us = 'team' + chosen['side'].upper()
        them = 'teamB' if us == 'teamA' else 'teamA'
        samples = list(range(50, min(800, doc['match']['roundsCompleted']) + 1, 50))
        def behind(t):
            a, b = timeline(doc, us, 'earnedGold', t), timeline(doc, them, 'earnedGold', t)
            return b - a >= max(100, .15 * a)
        first = next((a for a,b in zip(samples, samples[1:]) if behind(a) and behind(b)), None)
        reference = first or 300
        common = [n for n in ('Marcella','Vendetta','Varg','Heart of Ruin','Vesper Vale','Cassi','Issac','Ryth','Stellar','Prism','Tavi','Ren','Willow') if all(any(c['name'] == n and c['team'] == team for c in doc['roster']['champions']) for team in (us,them))]
        assert common, chosen['matchId']
        champion = common[0]
        actors = {label: next(c['id'] for c in doc['roster']['champions'] if c['team'] == team and c['name'] == champion) for label,team in (('ours',us),('rival',them))}
        replay = OUT / 'analysis-discovery/replays' / (chosen['matchId'] + '.repl26a')
        cases.append({**chosen, 'native_sha256': bench.digest(path), 'replay_sha256': bench.digest(replay), 'first_sustained_sample': first,
                      'rounds': [max(1,reference-50),reference], 'champion': champion, 'actors': actors,
                      'gold_samples': {str(t): [timeline(doc, team, 'earnedGold', t) for team in (us,them)] for t in samples}})
    absent = [n for n in ('QS2isLaw','0xDEADBEEF','bentheboss') if not counts[n]]
    write(HERE / f'{PREFIX}_TURNING_VIEWS_PLAN.json', {'selection': 'EXP239 discovery only, fixed opponent/match/champion/round selection before views', 'absent_requested_rivals': absent, 'cases': cases})
    jobs = [(c,label,actor,r) for c in cases for label,actor in c['actors'].items() for r in c['rounds']]
    def run(job):
        case,label,actor,r = job
        mid = case['matchId']
        team = int(case['side'].upper() == 'B') if label == 'ours' else int(case['side'].upper() != 'B')
        target = output / f'{mid}-{label}-{r}.json'
        replay = OUT / 'analysis-discovery/replays' / (mid + '.repl26a')
        with target.with_suffix('.log').open('xb') as log:
            proc = subprocess.run(['node',HERE/'trace_turn.mjs',replay,str(r),str(team),str(actor),target],cwd=bench.ROOT,
                                  env={**os.environ,'NFS_REPLAY_ENGINE':'3.0.0'},stdout=log,stderr=subprocess.STDOUT)
        if proc.returncode:
            return {'matchId':mid,'label':label,'round':r,'actor_id':actor,'available':False,'returncode':proc.returncode,'log':str(target.with_suffix('.log'))}
        turn = read(target)
        observed = turn['observation']['actor']
        assert observed['id'] == actor and observed['team'] == team
        doc = read(OUT/'summaries'/(mid+'.json'))
        one = {'championTimelines':[x for x in doc['championTimelines'] if x['owner']['id'] == actor]}
        boundaries = {metric:[timeline(one,'team'+'AB'[team],metric,t) for t in (r-1,r)] for metric in ('gold','gems')}
        assert all(min(v)<=observed[k]<=max(v) for k,v in boundaries.items()),(mid,label,r,boundaries,observed)
        return {'matchId':mid,'opponent':case['opponent'],'label':label,'round':r,'champion':case['champion'],'available':True,
                'trace_sha256':bench.digest(target),'trace':str(target),'native_boundaries':boundaries,
                'actor':observed,'visible_enemies':len(turn['observation']['visible_enemies']),
                'visible_camps':turn['observation']['visible_camps'],'actions':turn['executed_actions']}
    with ThreadPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(run,jobs))
    result = {'scope':'Observed own views only; historical source identity/private target state inferred, no causal action recommendation',
              'plan_sha256':bench.digest(HERE/f'{PREFIX}_TURNING_VIEWS_PLAN.json'),'rows':rows,'unavailable':sum(not r['available'] for r in rows)}
    write(HERE/f'{PREFIX}_TURNING_VIEWS.json',result)
    print({'cases':len(cases),'views':len(rows),'unavailable':result['unavailable'],'absent_requested_rivals':absent},flush=True)
