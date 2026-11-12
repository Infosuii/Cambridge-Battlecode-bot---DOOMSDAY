"""Share of our alive champion-rounds spent standing still within 3 tiles of a small (<= 200 hp) camp within 20 tiles of
our spawn ("home small camps"), per game. usage: corner_metric.py DIR_WITH_gN.json_AND_sides.txt [ladder_dump.json]"""
import json, os, sys

def metric(path, us):
    d = json.load(open(path, encoding="utf-8"))
    fr = d["frames"]
    cheb = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
    spawn = None
    for _, cs in fr:
        pts = [(c[3], c[4]) for c in cs if c[1] == us and c[6] and c[3] is not None]
        if pts:
            spawn = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
            break
    home = [(c[1], c[2]) for c in d["camps0"] if c[3] <= 200 and cheb((c[1], c[2]), spawn) <= 20]
    alive = still_home = still_all = 0
    for i in range(1, len(fr)):
        prev = {c[0]: c for c in fr[i - 1][1]}
        for c in fr[i][1]:
            if c[1] != us or not c[6] or c[3] is None:
                continue
            alive += 1
            p = prev.get(c[0])
            if p and p[6] and (p[3], p[4]) == (c[3], c[4]):
                still_all += 1
                if any(cheb((c[3], c[4]), h) <= 3 for h in home):
                    still_home += 1
    return alive, still_all, still_home, len(home), fr[-1][0]

d = sys.argv[1]
rows = []
for line in open(os.path.join(d, "sides.txt")):
    g, side = line.split()
    a, s, h, n, rounds = metric(os.path.join(d, f"g{g}.json"), 0 if side == "A" else 1)
    rows.append((g, side, a, s, h, n, rounds))
    print(f"g{g:4s} v130 side {side} rounds {rounds:5d} home small camps {n} | still {100 * s / a:4.1f}% of alive | "
          f"still by home small camps {100 * h / a:4.1f}%")
A = sum(r[2] for r in rows); H = sum(r[4] for r in rows); S = sum(r[3] for r in rows)
print(f"ALL local: still {100 * S / A:.1f}%, by home small camps {100 * H / A:.1f}%")
if len(sys.argv) > 2:
    a, s, h, n, rounds = metric(sys.argv[2], 0)
    print(f"LADDER match: still {100 * s / a:.1f}%, by home small camps {100 * h / a:.1f}% (home small camps {n})")
