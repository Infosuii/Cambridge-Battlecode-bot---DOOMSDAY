"""Summarize sealed paired losses without changing the selection."""
from collections import Counter
from pathlib import Path
import json
from local_panel import read_native
from project import ROOT, save


def economy(row):
    n = read_native(row['summary'])
    team = 'team' + row['side'].upper()
    ids = {c['id'] for c in n['roster']['champions'] if c['team'] == team}
    end = Counter()
    for t in n['championTimelines']:
        if t['owner']['id'] in ids and t['metric'] in (
                'collectedGems', 'submittedGems', 'deaths', 'monsterDamageTaken', 'championDamageTaken'):
            end[t['metric']] += float(t['runs'][-1]['value'])
    return {**end, 'fuel': row['fuel'], 'rounds': row['rounds']}


if __name__ == '__main__':
    name = json.loads((ROOT/'qualification-stall/selection.json').read_text())['winner']
    rows = json.loads((ROOT/'panels/stall-sealed-reference/results.json').read_text())
    index = lambda n: {(r['opponent'], r['map_sha256'], r['side']): r for r in rows if r['candidate'] == n}
    active, parent = index(name), index('mx500')
    out = []
    for k, a in sorted(active.items()):
        b = parent[k]
        if a['score'] == b['score'] or a['opponent'] != 'b111':
            continue
        A, B = economy(a), economy(b)
        out.append({'map': a['map'], 'map_sha256': a['map_sha256'], 'side': a['side'],
                    'candidate_score': a['score'], 'parent_score': b['score'],
                    'candidate': A, 'parent': B,
                    'candidate_summary_sha256': a['summary_sha256'], 'parent_summary_sha256': b['summary_sha256']})
    save(ROOT/'stall-audit/sealed-v111-outcome-flips.json', out)
    for direction in (-1, 1):
        s = [r for r in out if direction*(r['candidate_score']-r['parent_score']) > 0]
        keys = ('collectedGems', 'submittedGems', 'deaths', 'monsterDamageTaken', 'championDamageTaken', 'fuel')
        print(json.dumps({'direction': direction, 'cells': len(s), 'delta_per_game': {
            k: round(sum(r['candidate'].get(k, 0)-r['parent'].get(k, 0) for r in s)/len(s), 2) if s else None
            for k in keys}}))
