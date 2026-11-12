import glob, os, re, sys, collections
run = sys.argv[1]; at = int(sys.argv[2]) if len(sys.argv) > 2 else 500
names = ['travel', 'clear', 'capture', 'bank', 'home', 'retreat', 'idle', 'yield', 'fight', 'channel', 'dead']
tot = collections.Counter(); per_map = {}
for g in sorted(glob.glob(f'artifacts/tmp/dz/{run}/games/*')):
    out = open(os.path.join(g, 'candidate.stdout'), encoding='utf-8', errors='replace').read()
    c = collections.Counter()
    for m in re.finditer(r'DZ_TIME round=(\d+) slot=(\d+)((?: \d+){11})', out):
        if int(m[1]) != at: continue
        for k, v in zip(names, map(int, m[3].split())): c[k] += v
    tot.update(c); s = sum(c.values()) or 1
    per_map[os.path.basename(g)] = {k: round(100 * v / s) for k, v in c.items() if v}
s = sum(tot.values())
print('ALL percent of body-turns to round', at, {k: round(100 * v / s, 1) for k, v in tot.items()})
for k, v in per_map.items(): print(k, v)
