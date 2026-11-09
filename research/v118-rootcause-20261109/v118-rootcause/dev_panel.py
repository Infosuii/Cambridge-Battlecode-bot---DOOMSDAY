"""Development paired panel on the 88 dev maps (never the holdout)."""
from pathlib import Path
import sys, json, collections
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from local_panel import run
from project import save
DEV_STYLES = ['b111', 'ref_x1', 'nnm4', 'teammate_john_nnfinal', 'teammate_max_gx']

def summary(rows, base='hp01'):
    by = collections.defaultdict(dict)
    for r in rows: by[r['candidate']][(r['opponent'], r['map'], r['side'])] = r
    out = {}
    for c, d in by.items():
        keys = set(d) & set(by[base])
        diff = sum(d[k]['score'] - by[base][k]['score'] for k in keys)
        maps = collections.Counter()
        for k in keys: maps[k[1]] += d[k]['score'] - by[base][k]['score']
        out[c] = {'games': len(d), 'score': sum(r['score'] for r in d.values()), 'paired_diff': diff, 'faults': sum(r['faults'] for r in d.values()),
                  'fuel': sum(r['fuel'] for r in d.values()), 'by_opp': {o: sum(r['score'] for k, r in d.items() if k[0] == o) for o in DEV_STYLES},
                  'worst_maps': maps.most_common()[-5:], 'best_maps': maps.most_common(5)}
    return out

def main(label, cands, styles=DEV_STYLES, workers=18):
    split = json.loads((HERE / 'map-split.json').read_text())
    maps = [Path(p) for p in split['dev']]
    rows = run(label, cands, maps, styles, workers=workers)
    s = summary(rows)
    save(HERE / (label + '-summary.json'), s)
    for c, v in s.items(): print(c, {k: v[k] for k in ('games', 'score', 'paired_diff', 'faults', 'fuel')}, v['worst_maps'][:3])

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2].split(','))
