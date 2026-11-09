from pathlib import Path
import sys, json, collections, random
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from local_panel import run, STYLES
from project import ROOT, save
maps = sorted((ROOT / 'arena/maps_sw08_followup').glob('*.map26a'))
rows = run('v118-confirm-fresh', ['hp01', 'v18HDR'], maps, STYLES, workers=18)
by = collections.defaultdict(dict)
for r in rows: by[r['candidate']][(r['opponent'], r['map'], r['side'])] = r
d = collections.defaultdict(list)
for k, r in by['v18HDR'].items(): d[k[1]].append(r['score'] - by['hp01'][k]['score'])
rng = random.Random(5); ms = list(d); out = []
for _ in range(4000):
    p = [rng.choice(ms) for _ in ms]; out.append(100 * sum(sum(d[m]) for m in p) / sum(len(d[m]) for m in p))
out.sort()
res = {'games': len(by['v18HDR']), 'score': {c: sum(r['score'] for r in v.values()) for c, v in by.items()},
       'paired_diff': sum(sum(v) for v in d.values()), 'pp_p10_p50_p90': [out[400], out[2000], out[3600]],
       'faults': {c: sum(r['faults'] for r in v.values()) for c, v in by.items()}, 'fuel': {c: sum(r['fuel'] for r in v.values()) for c, v in by.items()}}
save(HERE / 'confirm-fresh-result.json', res); print(json.dumps(res))
