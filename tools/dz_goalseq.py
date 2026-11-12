import re, sys
path, slot = sys.argv[1], sys.argv[2]
kinds = {0: 'F', 1: 'B', 2: 'H', 3: 'R', 4: 'I', 5: 'Y', 6: 'X'}
rows = [(int(m[1]), int(m[2]), int(m[3]), m[4], int(m[5])) for m in re.finditer(
    r'DZ_GOAL round=(\d+) slot=' + slot + r' kind=(\d+) index=(-?\d+) pos=(\d+,\d+) bag=(\d+)', open(path, encoding='utf-8', errors='replace').read())]
segs = []
for r, k, i, pos, bag in rows:
    key = (kinds[k], i)
    if segs and segs[-1][0] == key: segs[-1][2] = r; segs[-1][4] = bag
    else: segs.append([key, r, r, pos, bag])
for (k, i), a, b, pos, bag in segs:
    print(f'{a:4d}-{b:4d} {k}{i:<4d} start={pos} bag_end={bag}')
