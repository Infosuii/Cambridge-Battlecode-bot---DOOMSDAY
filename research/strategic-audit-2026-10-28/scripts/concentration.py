"""Gold concentration and recall frequency per team from replay timeline.json files (tools/v67/c_timeline.mjs format).

Usage: concentration.py TIMELINE.json [...] [--until 300]
Per team: wallet gold gained by R<until> (sum of positive wallet steps, so kill/capture/bank gold, not refunds),
the top earner's share, Vesper's share (if drafted), items held by the top earner, recalls per champion per 100
alive rounds, and team champions. Frame row layout: [id, x, y, hp, maxhp, alive, gold, ?, items, actions].
"""
import argparse
import json
from pathlib import Path

NAMES = 'ryth vesper vendetta cassi issac stellar prism marcella willow ren varg tavi heart'.split()
ap = argparse.ArgumentParser()
ap.add_argument('timelines', nargs='+')
ap.add_argument('--until', type=int, default=300)
ap.add_argument('--json')
a = ap.parse_args()
out = []
for path in a.timelines:
    tl = json.load(open(path))
    frames = [f for f in tl['frames'] if f[0] <= a.until]
    typ = {c['id']: NAMES[c['type']] for c in tl['champs']}
    for t in (0, 1):
        ids = [c['id'] for c in tl['champs'] if c['team'] == t]
        gold, rec, alive, items = {}, {}, {}, {}
        for cid in ids:
            rows = [next(x for x in f[1] if x[0] == cid) for f in frames]
            gold[cid] = sum(max(0, r2[6] - r1[6]) for r1, r2 in zip(rows, rows[1:]))
            rec[cid] = sum(1 for r in rows for k in (r[9] if len(r) > 9 else []) if k[0] == 11)
            alive[cid] = sum(1 for r in rows if r[5])
            items[cid] = rows[-1][8]
        tot = sum(gold.values()) or 1
        top = max(ids, key=lambda c: gold[c])
        ves = [c for c in ids if typ[c] == 'vesper']
        row = dict(file=str(Path(path).parent.name), team=t, champs=[typ[c] for c in ids], gold=tot,
                   top=typ[top], top_share=gold[top] / tot, top_items=items[top],
                   vesper_share=(gold[ves[0]] / tot) if ves else None,
                   recalls_per100=100 * sum(rec.values()) / max(1, sum(alive.values())))
        out.append(row)
        print(f"{row['file'][:10]} t{t} gold {tot:5d} top {row['top']:8s} {row['top_share']:.2f} items {row['top_items']:2d}"
              f" vesper {'-' if row['vesper_share'] is None else round(row['vesper_share'], 2)} rec/100 {row['recalls_per100']:.2f} {row['champs']}")
if a.json:
    json.dump(out, open(a.json, 'w'), indent=1)
