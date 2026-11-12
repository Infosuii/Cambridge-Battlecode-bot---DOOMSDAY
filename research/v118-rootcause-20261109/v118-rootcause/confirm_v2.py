"""Run pre-registered confirmation protocol v2 (release-protocol-v2.json) for one candidate. Run ONCE.

python v118-rootcause/confirm_v2.py v18HDRWTQ
Primary: sealed arena/maps_v118_confirm (96 maps) x 9 styles x 2 sides vs hp01, + direct vs hp01.
Secondary: 40-map published holdout (reused), candidate cells only (hp01 cells cached from v118-holdout-reference).
"""
from pathlib import Path
import sys, json, collections, random
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from local_panel import run, STYLES
from project import ROOT, save, sha


def paired(rows, cand, base='hp01'):
    by = collections.defaultdict(dict)
    for r in rows: by[r['candidate']][(r['opponent'], r['map'], r['side'])] = r
    d = collections.defaultdict(list)
    for k, r in by[cand].items():
        if k in by[base]: d[k[1]].append(r['score'] - by[base][k]['score'])
    n = sum(len(v) for v in d.values()); rng = random.Random(118); ms = list(d); out = []
    for _ in range(4000):
        p = [rng.choice(ms) for _ in ms]; out.append(100 * sum(sum(d[m]) for m in p) / max(1, sum(len(d[m]) for m in p)))
    out.sort()
    worst = sorted(((sum(v), m) for m, v in d.items()))[:5]
    return {'games': n, 'diff': sum(sum(v) for v in d.values()), 'pp': 100 * sum(sum(v) for v in d.values()) / max(1, n),
            'p10': out[400], 'p50': out[2000], 'worst_maps': worst}


def main(cand):
    proto = json.loads((HERE / 'release-protocol-v2.json').read_text())
    assert proto['primary_sealed_set']['manifest_sha256'] == sha(ROOT / 'arena/maps_v118_confirm/manifest.json')
    fresh = sorted((ROOT / 'arena/maps_v118_confirm').glob('*.map26a'))
    prim = run('v118-confirm2-primary', ['hp01', cand], fresh, STYLES, workers=18)
    direct = run('v118-confirm2-direct', [cand], fresh, ['hp01'], workers=18)
    hold = [Path(p) for p in json.loads((HERE / 'map-split.json').read_text())['holdout']]
    sec = run('v118-confirm2-holdout', [cand], hold, STYLES, workers=18)
    sec_base = [r for r in json.loads((ROOT / 'panels/v118-holdout-reference/results.json').read_text()) if r['candidate'] == 'hp01']
    P = paired(prim, cand); S = paired(sec + sec_base, cand)
    cr = [r for r in prim if r['candidate'] == cand] + direct + sec; ir = [r for r in prim if r['candidate'] == 'hp01']
    fuel_c = sum(r['fuel'] for r in prim if r['candidate'] == cand) / max(1, len(ir)); fuel_i = sum(r['fuel'] for r in ir) / max(1, len(ir))
    dscore = sum(r['score'] for r in direct) / max(1, len(direct))
    gates = {'P2_faults': sum(r['faults'] for r in cr) == 0, 'P3_fuel': fuel_c <= 1.2 * fuel_i + 0.05,
             'P4_primary_strength': P['diff'] >= 0 and P['p10'] >= -1.5, 'P5_direct': dscore >= 0.5, 'P6_secondary': S['pp'] >= -1.0}
    res = {'candidate': cand, 'primary': P, 'secondary_holdout': S, 'direct_score': dscore, 'direct_games': len(direct),
           'fuel_per_game': {cand: fuel_c, 'hp01': fuel_i}, 'faults': sum(r['faults'] for r in cr), 'gates': gates,
           'note': 'P1 targets come from the incident panels (incident-checks.json, v118-eval-wtq.json); check them before upload.'}
    save(HERE / f'confirm2-{cand}.json', res); print(json.dumps(res, indent=1))


if __name__ == '__main__':
    main(sys.argv[1])
