"""Join v130's debug mode trace (M round id mode group) with replay positions: what were champions doing while they
stood still near the small camps by our spawn? usage: join_modes.py team-a.stdout dump.json"""
import collections, json, re, sys

sys.stdout.reconfigure(encoding="utf-8")
modes = {}
for line in open(sys.argv[1], encoding="utf-8", errors="replace"):
    m = re.match(r"\s*M (\d+) (\d+) (\S+) (-?\d+)", line)
    if m:
        modes[(int(m.group(1)), int(m.group(2)))] = (m.group(3), int(m.group(4)))
d = json.load(open(sys.argv[2], encoding="utf-8"))
fr = d["frames"]
cheb = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
pts = [(c[3], c[4]) for c in fr[1][1] if c[1] == 0 and c[3] is not None]
spawn = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
home = {c[0]: (c[1], c[2]) for c in d["camps0"] if c[3] <= 200 and cheb((c[1], c[2]), spawn) <= 20}
print("spawn", spawn, "home small camps", home)
near, allm = collections.Counter(), collections.Counter()
groups = collections.Counter()
alive = 0
for i in range(1, len(fr)):
    r = fr[i][0]
    prev = {c[0]: c for c in fr[i - 1][1]}
    for c in fr[i][1]:
        if c[1] != 0 or not c[6] or c[3] is None:
            continue
        alive += 1
        md = modes.get((r, c[0])) or modes.get((r - 1, c[0]))
        if not md:
            continue
        allm[md[0]] += 1
        p = prev.get(c[0])
        if p and p[6] and (p[3], p[4]) == (c[3], c[4]) and any(cheb((c[3], c[4]), h) <= 3 for h in home.values()):
            near[md[0]] += 1
            groups[md[1]] += 1
print(f"alive champion-rounds {alive}; still beside home small camps {sum(near.values())} ({100 * sum(near.values()) / alive:.1f}%)")
print("modes while still beside home small camps:", near.most_common(8))
print("their target groups:", groups.most_common(6))
print("all modes (whole game):", allm.most_common(12))
