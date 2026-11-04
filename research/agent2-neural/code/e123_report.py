"""E123: official-map matrix report from held_run.py rows: per bot wins vs each opponent, total, and by map size (longer side), with the standard error of the total.
usage (project root): python -P agent2/lab/e123_report.py FILE.tsv [FILE.tsv ...]"""
import collections, math, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
s = open(os.path.join(ROOT, "v4", "bots", "v92", "src", "ladfit.h"), encoding="utf-8").read()
fp = re.findall(r"\{(\d+),(\d+),(\d+),(\d+)u\}", s)[:70]
names = sorted(f[:-7] for f in os.listdir(os.path.join(ROOT, "v4", "maps")) if f.endswith(".map26a"))
size = {n: max(int(a), int(b)) for n, (a, b, _, _) in zip(names, fp)}
BINS = [("<=40", 0, 40), ("41-60", 41, 60), (">60", 61, 999)]
rows = collections.defaultdict(lambda: collections.defaultdict(lambda: [0.0, 0]))
for f in sys.argv[1:]:
    for l in open(f):
        bot, opp, mp, side, win = l.split("\t")[:5]
        mp = mp.split("~")[-1]
        for key in (opp, "total") + tuple(b for b, lo, hi in BINS if lo <= size.get(mp, 0) <= hi and mp in size):
            rows[bot][key][0] += float(win)
            rows[bot][key][1] += 1
opps = sorted({k for t in rows.values() for k in t if k not in ("total",) and k not in [b for b, _, _ in BINS]})
print(f"{'bot':10s} " + " ".join(f"{o:>8s}" for o in opps) + "    total      %   +-SE | " + " | ".join(f"{b:>12s}" for b, _, _ in BINS))
for bot, t in rows.items():
    w, n = t["total"]
    p = w / max(1, n)
    print(f"{bot:10s} " + " ".join(f"{t[o][0]:8.0f}" if t[o][1] else f"{'-':>8s}" for o in opps) +
          f" {w:6.0f}/{n:<4d} {100 * p:5.1f} {100 * math.sqrt(p * (1 - p) / max(1, n)):5.1f} | " +
          " | ".join(f"{t[b][0]:4.0f}/{t[b][1]:<3d} {100 * t[b][0] / max(1, t[b][1]):3.0f}%" for b, _, _ in BINS))
