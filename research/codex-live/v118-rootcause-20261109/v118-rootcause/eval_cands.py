"""Evaluate candidates: incident maps (camp deaths etc.) + broad dev panel (88 dev x 9 styles + 113 stability x 5 styles), paired vs base."""
from pathlib import Path
import sys, json, collections, random, concurrent.futures
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from local_panel import run, read_native, STYLES
from project import ROOT, save
import dev_panel

def deaths(r):
    n = read_native(r['summary']); us = 'team' + r['side'].upper(); d = collections.Counter()
    for e in n['events']:
        if e['kind'] == 'death' and e['owner'].get('kind') == 'champion':
            side = 'us' if e['owner'].get('team') == us else 'them'
            for v in e['entries']:
                d[side] += 1
                if v.get('context') == 'camp' or (v.get('target') or {}).get('kind') == 'camp': d[side + '_camp'] += 1
    return d

def paired(rows, base, cand):
    by = collections.defaultdict(dict)
    for r in rows: by[r['candidate']][(r['opponent'], r['map'], r['side'])] = r
    keys = [k for k in by[cand] if k in by[base]]
    d = collections.defaultdict(list)
    for k in keys: d[k[1]].append(by[cand][k]['score'] - by[base][k]['score'])
    rng = random.Random(3); ms = list(d); out = []
    for _ in range(3000):
        p = [rng.choice(ms) for _ in ms]; out.append(sum(sum(d[m]) for m in p))
    out.sort()
    return {'games': len(keys), 'diff': sum(sum(v) for v in d.values()), 'p05_p95': [out[150], out[2850]] if out else None,
            'score': sum(by[cand][k]['score'] for k in keys), 'base_score': sum(by[base][k]['score'] for k in keys)}

def main(label, cands, base='v18HDR', incident=('03the-front', '04plaza', '01starfish', '00oasis', '00lanes')):
    split = json.loads((HERE / 'map-split.json').read_text())
    pool = {Path(p).stem: Path(p) for p in split['dev'] + split['holdout']}
    inc = run(label + '-incident', [base, 'hp01'] + cands, [pool[m] for m in incident], STYLES, workers=18)
    with concurrent.futures.ThreadPoolExecutor(16) as p: ds = list(p.map(deaths, inc))
    agg = collections.defaultdict(collections.Counter)
    for r, d in zip(inc, ds):
        agg[r['candidate']].update(d); agg[r['candidate']]['games'] += 1; agg[r['candidate']]['score'] += r['score']
    dev = [Path(p) for p in split['dev']]
    gen = sorted((ROOT / 'arena/maps_v113_stability').glob('*.map26a'))
    a = run(label + '-dev', cands, dev, STYLES, workers=18)
    b = run(label + '-gen', cands, gen, dev_panel.DEV_STYLES, workers=18)
    old = []
    for l in ('v118-dev-a', 'v118-dev-b-styles', 'v118-dev-c-generated'):
        old += [r for r in json.loads((ROOT / 'panels' / l / 'results.json').read_text()) if r['candidate'] in (base, 'hp01')]
    rows = a + b + old
    res = {'incident': {c: {k: (round(v / agg[c]['games'], 3) if k not in ('games',) else v) for k, v in agg[c].items()} for c in agg},
           'broad_vs_base': {c: paired(rows, base, c) for c in cands}, 'broad_vs_hp01': {c: paired(rows, 'hp01', c) for c in cands + [base]},
           'faults': {c: sum(r['faults'] for r in a + b if r['candidate'] == c) for c in cands},
           'fuel_per_game': {c: round(sum(r['fuel'] for r in a + b if r['candidate'] == c) / max(1, sum(r['candidate'] == c for r in a + b)), 3) for c in cands}}
    save(HERE / (label + '.json'), res); print(json.dumps(res, indent=1))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2].split(','))
