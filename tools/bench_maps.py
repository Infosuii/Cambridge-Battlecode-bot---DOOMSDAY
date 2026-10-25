"""Per-map table across several bench2 runs (any seed sets): wins by side, mean margin, worst margin.

Usage: python tools/bench_maps.py <bench2 out prefix>...   (prefixes as passed to bench2.sh)
"""
from collections import defaultdict
import glob
import json
from pathlib import Path
import sys

rows = defaultdict(list)
for prefix in sys.argv[1:]:
    for f in glob.glob(prefix + '-seed*-s*/summary.json'):
        seed = Path(f).parent.name.split('-seed')[-1].split('-')[0]
        for g in json.loads(Path(f).read_text(encoding='utf-8'))['per_game']:
            rows[g['map']].append((g['side'], seed, g['win'], g['gems'] - g['opponent_gems']))
tot = [0, 0, 0.0]
print(f"{'map':24s} {'A wins':>7s} {'B wins':>7s} {'mean':>7s} {'worst':>6s}")
for m in sorted(rows):
    r = rows[m]
    a = [x for x in r if x[0] == 'A']; b = [x for x in r if x[0] == 'B']
    mean = sum(x[3] for x in r) / len(r)
    print(f"{m:24s} {sum(x[2] for x in a):3.0f}/{len(a):<3d} {sum(x[2] for x in b):3.0f}/{len(b):<3d} {mean:+7.1f} {min(x[3] for x in r):+6d}")
    tot[0] += sum(x[2] for x in r); tot[1] += len(r); tot[2] += sum(x[3] for x in r)
print(f"total {tot[0]:.0f}/{tot[1]} = {tot[0] / tot[1]:.3f}, mean margin {tot[2] / tot[1]:+.1f}")
