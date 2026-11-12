"""Decisive test: can the existing draft clear Homonoliths' home monoliths on time with a crew assigned and retained?"""
from pathlib import Path
import sys, json, collections
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from local_panel import run, read_native
from project import ROOT, save
from sw08_followup import build_from, load
from policy_rows import stdout
import home_siege

def summarise(rows, our_group_for_side):
    out = []
    for r in rows:
        n = read_native(r['summary']); us = 'team' + r['side'].upper()
        caps = sorted((v['timestamp']['round'], e['owner']['team'], v['target']['id'], float(v['value'])) for e in n['events'] if e['kind'] == 'gemCollection'
                      for v in e['entries'] if float(v['value']) and (v.get('target') or {}).get('kind') == 'campGroup')
        deaths = collections.Counter()
        for e in n['events']:
            if e['kind'] in ('championDeath', 'death', 'unitDeath'):
                for v in e['entries']: deaths[(e.get('owner') or {}).get('team')] += 1
        first_us = next((c[0] for c in caps if c[1] == us), None)
        first_home = next((c[0] for c in caps if c[1] == us and c[2] == our_group_for_side[r['side']]), None)
        txt = stdout(r['replay_bundle'], r['side']) if 'dx' in r['candidate'] else ''
        hs = [l.split() for l in txt.splitlines() if l.startswith('HS ')]
        heal = next((l for l in txt.splitlines() if l.startswith('SPAWNHEAL')), None)
        minhp = min((float(p[6]) / float(p[7]) for p in hs), default=None)
        last_hs = max((int(p[1]) for p in hs), default=None)
        out.append({'cand': r['candidate'], 'opp': r['opponent'], 'side': r['side'], 'score': r['score'], 'rounds': r['rounds'], 'fuel': r['fuel'],
                    'first_capture': first_us, 'first_home_capture': first_home, 'banked': {t['team']: t['submittedGems'] for t in n['teams']},
                    'deaths': dict(deaths), 'hs_rows': len(hs), 'hs_min_hp_frac': minhp, 'hs_last_round': last_hs, 'spawnheal': heal})
    return out

def main():
    build_from('dx02', 'hp01', lambda f: home_siege.apply(f, crew=3, trace=True), debug=True)
    build_from('dx03', 'hp01', lambda f: home_siege.apply(f, crew=4, trace=True), debug=True)
    maps = load(ROOT / 'published-maps.json')
    target = Path(next(row['file'] for row in maps if row['name'] == '03homonoliths'))
    rows = run('v118-homonoliths-crew', ['dx02', 'dx03'], [target], ['ref_x1', 'b111', 'teammate_john_nnfinal'], workers=12, debug=True)
    # group 2 is next to spawn A, group 3 next to spawn B
    res = summarise(rows, {'a': 2, 'b': 3})
    save(HERE / 'homonoliths-crew.json', res)
    for x in res: print(json.dumps(x))

if __name__ == '__main__':
    main()
