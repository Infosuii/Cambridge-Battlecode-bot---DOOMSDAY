"""Per-team action counts and per-champion standing-still runs from dump.mjs output.
usage: analyse.py dump.json summary.json"""
import collections, json, sys

sys.stdout.reconfigure(encoding="utf-8")
dump = json.load(open(sys.argv[1], encoding="utf-8"))
summ = json.load(open(sys.argv[2], encoding="utf-8"))
name = {c["id"]: c["name"] for c in summ["roster"]["champions"]}
team = {c["id"]: (0 if c["team"] == "teamA" else 1) for c in summ["roster"]["champions"]}
W, H = summ["match"]["width"], summ["match"]["height"]
frames, steps = dump["frames"], dump["steps"]
print(f"map {W}x{H}, rounds {frames[-1][0]}")

kinds = ["Move", "Attack", "Cast ability", "Recall", "Cancel channel", "Submit gems", "Gems submitted", "Shop",
         "Place ward", "Consumable", "Teleport channel", "Teleport complete", "Place altar lock", "Movement blocked", "Respawn"]
cnt = collections.Counter((team.get(s[2], -1), s[1]) for s in steps)
print(f"{'step':18s} {'us':>7s} {'them':>7s}")
for k in kinds:
    print(f"{k:18s} {cnt[(0, k)]:7d} {cnt[(1, k)]:7d}")

# spawn: first alive position of each champion
first = {}
for r, cs in frames:
    for c in cs:
        if c[6] and c[3] is not None and c[0] not in first:
            first[c[0]] = (c[3], c[4], r)
print("first positions:", {f"{name[i]}({'us' if team[i] == 0 else 'them'})": first[i][:2] for i in sorted(first)})

by_actor = collections.defaultdict(list)
for s in steps:
    by_actor[s[2]].append(s)
print("\nper champion: alive rounds, rounds on the same tile as the round before, recalls, cancels, long still runs (>= 20 rounds)")
for cid in sorted(name):
    hist = [(r, c) for r, cs in frames for c in cs if c[0] == cid]
    alive = sum(1 for _, c in hist if c[6])
    still, runs, start = 0, [], None
    for i in range(1, len(hist)):
        (r0, a), (r1, b) = hist[i - 1], hist[i]
        same = a[6] and b[6] and a[3] == b[3] and a[4] == b[4] and a[3] is not None
        if same:
            still += 1
            if start is None:
                start = i - 1
        elif start is not None:
            runs.append((hist[start][0], hist[i - 1][0], hist[start][1]))
            start = None
    if start is not None:
        runs.append((hist[start][0], hist[-1][0], hist[start][1]))
    acts = collections.Counter(s[1] for s in by_actor[cid])
    long = [(a, b, c) for a, b, c in runs if b - a >= 20]
    print(f"{name[cid]:13s} {'us' if team[cid] == 0 else 'them':4s} alive {alive:4d} still {still:4d} ({100 * still / max(1, alive):4.1f}%) "
          f"recall {acts['Recall']:5d} cancel {acts['Cancel channel']:5d} long-runs {len(long)}")
    for a, b, c in sorted(long, key=lambda x: x[0] - x[1])[:6]:
        rc = sum(1 for s in by_actor[cid] if a <= s[0] <= b and s[1] == "Recall")
        cc = sum(1 for s in by_actor[cid] if a <= s[0] <= b and s[1] == "Cancel channel")
        other = collections.Counter(s[1] for s in by_actor[cid] if a <= s[0] <= b and s[1] not in ("Recall", "Cancel channel"))
        print(f"     rounds {a:4d}-{b:4d} ({b - a + 1:4d}) at ({c[3]},{c[4]}) hp {c[5]} gems {c[7]} gold {c[8]} "
              f"| recalls {rc} cancels {cc} other {dict(other)}")
