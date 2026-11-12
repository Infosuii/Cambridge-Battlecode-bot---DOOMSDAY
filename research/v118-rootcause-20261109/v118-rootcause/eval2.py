"""Evaluate candidates against any base, reusing the base's cached cells from every earlier v118 panel.

Incident maps (deaths, camp deaths) + broad dev panel (88 dev maps x 9 styles + 113 stability maps x 5 styles).
"""
from pathlib import Path
import sys, json, collections, random, concurrent.futures
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from local_panel import run, STYLES
from project import ROOT, save
import dev_panel
from eval_cands import deaths, paired

CAMP_MAPS = ('03the-front', '04plaza', '01starfish', '00oasis', '00lanes')
BAG_MAPS = ('adgato-gemcombat5', '04comb', '04two-kingdoms', '00great-wall', '04dunes', '04canyons', '04passageway')


def cached(names):
    rows = []
    for p in (ROOT / 'panels').glob('v118-*/results.json'):
        try:
            rows += [r for r in json.loads(p.read_text()) if r['candidate'] in names]
        except Exception:
            pass
    uniq = {}
    for r in rows: uniq[(r['candidate'], r['opponent'], r['map_sha256'], r['side'])] = r
    return list(uniq.values())


def main(label, cands, base, incident):
    split = json.loads((HERE / 'map-split.json').read_text())
    pool = {Path(p).stem: Path(p) for p in split['dev'] + split['holdout']}
    old = cached([base, 'hp01'])
    have = {(r['candidate'], r['opponent'], r['map_sha256'], r['side']) for r in old}
    from project import sha
    inc_maps = [pool[m] for m in incident]
    need_base = any((base, o, sha(m), s) not in have for m in inc_maps for o in STYLES for s in 'ab')
    inc = run(label + '-incident', ([base] if need_base else []) + cands, inc_maps, STYLES, workers=18)
    inc_sha = {sha(m) for m in inc_maps}
    inc_all = inc + [r for r in old if r['map_sha256'] in inc_sha and r['candidate'] in (base, 'hp01')]
    uniq = {}
    for r in inc_all: uniq[(r['candidate'], r['opponent'], r['map_sha256'], r['side'])] = r
    inc_all = list(uniq.values())
    with concurrent.futures.ThreadPoolExecutor(16) as p: ds = list(p.map(deaths, inc_all))
    agg = collections.defaultdict(collections.Counter)
    for r, d in zip(inc_all, ds):
        agg[r['candidate']].update(d); agg[r['candidate']]['games'] += 1; agg[r['candidate']]['score'] += r['score']
    dev = [Path(p) for p in split['dev']]
    gen = sorted((ROOT / 'arena/maps_v113_stability').glob('*.map26a'))
    a = run(label + '-dev', cands, dev, STYLES, workers=18)
    b = run(label + '-gen', cands, gen, dev_panel.DEV_STYLES, workers=18)
    rows = a + b + old
    res = {'base': base,
           'incident': {c: {k: (round(v / agg[c]['games'], 3) if k != 'games' else v) for k, v in agg[c].items()} for c in agg},
           'broad_vs_base': {c: paired(rows, base, c) for c in cands},
           'broad_vs_hp01': {c: paired(rows, 'hp01', c) for c in cands + [base]},
           'faults': {c: sum(r['faults'] for r in a + b if r['candidate'] == c) for c in cands},
           'fuel_per_game': {c: round(sum(r['fuel'] for r in a + b if r['candidate'] == c) / max(1, sum(r['candidate'] == c for r in a + b)), 3) for c in cands}}
    save(HERE / (label + '.json'), res)
    print(json.dumps(res, indent=1))
    return res


if __name__ == '__main__':
    inc = {'camp': CAMP_MAPS, 'bag': BAG_MAPS, 'both': CAMP_MAPS + BAG_MAPS}[sys.argv[4] if len(sys.argv) > 4 else 'both']
    main(sys.argv[1], sys.argv[2].split(','), sys.argv[3], inc)
