"""Tally a cambc run-batch log: per (candidate, opponent) score and paired map-level comparison vs a reference candidate."""
import re, sys, collections, math

log = sys.argv[1]
cands = sys.argv[2].split(',')
ref = sys.argv[3] if len(sys.argv) > 3 else None
res = collections.defaultdict(lambda: [0, 0])
cell = {}
pat = re.compile(r'TEAM ([AB]) WIN \((\S+)\)\s+(\S+) vs (\S+)\s+(\S+)')
for line in open(log, encoding='utf8', errors='replace'):
    m = pat.search(line)
    if not m:
        continue
    _, wb, a, b, mp = m.groups()
    cand = a if a in cands else b
    opp = b if cand == a else a
    win = wb == cand
    res[(cand, opp)][0 if win else 1] += 1
    cell[(cand, opp, mp, cand == a)] = win
for k, v in sorted(res.items()):
    n = sum(v)
    print(f"{k[0]:>7} vs {k[1]:<6} {v[0]:4d}/{n:<4d} {v[0] / n:.3f}")
if ref:
    for c in cands:
        if c == ref:
            continue
        diffs = []
        for (cc, o, mp, side), w in cell.items():
            if cc != c:
                continue
            r = cell.get((ref, o, mp, side))
            if r is not None:
                diffs.append(int(w) - int(r))
        n = len(diffs)
        if not n:
            continue
        mean = sum(diffs) / n
        sd = math.sqrt(sum((d - mean) ** 2 for d in diffs) / max(1, n - 1))
        se = sd / math.sqrt(n)
        print(f"paired {c} - {ref}: {mean:+.3f} [{mean - 1.96 * se:+.3f}, {mean + 1.96 * se:+.3f}] n={n}")
