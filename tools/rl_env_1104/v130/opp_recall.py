"""FürFortnite's recall pattern from dump.mjs output: where Recall / Cancel sit inside each champion's turn, how many
recalls complete (jump to spawn), what the cancelled channels precede, and both teams' final items.
usage: opp_recall.py dump.json summary.json cambc.h"""
import collections, json, re, sys

sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open(sys.argv[1], encoding="utf-8"))
s = json.load(open(sys.argv[2], encoding="utf-8"))
name = {c["id"]: c["name"] for c in s["roster"]["champions"]}
team = {c["id"]: (0 if c["team"] == "teamA" else 1) for c in s["roster"]["champions"]}
steps, frames = d["steps"], d["frames"]
cheb = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))

# 1) within-turn order: group consecutive steps of one actor in one round
turns = collections.defaultdict(list)
for st in steps:
    turns[(st[0], st[2])].append(st[1])
pos_counter = collections.Counter()
seq_counter = collections.Counter()
for (r, a), ks in turns.items():
    if team.get(a) != 1:
        continue
    for i, k in enumerate(ks):
        if k == "Recall":
            pos_counter["recall is last action of the turn" if i == len(ks) - 1 else "recall mid-turn"] += 1
        if k == "Cancel channel":
            pos_counter["cancel is first action of the turn" if i == 0 else "cancel mid-turn"] += 1
    seq_counter[" > ".join(ks[:6])] += 1
print("opponent: where recall / cancel sit in a turn:", dict(pos_counter))
print("opponent: most common turn sequences:")
for q, n in seq_counter.most_common(8):
    print(f"   {n:5d}  {q}")

# 2) completed recalls: a living champion that jumps > 3 tiles in one round onto (near) its spawn
spawn = {}
for r, cs in frames[:5]:
    for c in cs:
        if c[6] and c[3] is not None:
            spawn.setdefault(c[1], []).append((c[3], c[4]))
jumps = collections.Counter()
for i in range(1, len(frames)):
    prev = {c[0]: c for c in frames[i - 1][1]}
    for c in frames[i][1]:
        p = prev.get(c[0])
        if not (p and p[6] and c[6] and p[3] is not None and c[3] is not None):
            continue
        if cheb((p[3], p[4]), (c[3], c[4])) > 3 and min(cheb((c[3], c[4]), q) for q in spawn[c[1]]) <= 2:
            jumps[c[1]] += 1
print("completed recalls (jump > 3 tiles onto spawn): us", jumps[0], "them", jumps[1])

# 3) what follows a cancelled recall: the next action in the same turn
after = collections.Counter()
for (r, a), ks in turns.items():
    if team.get(a) != 1:
        continue
    for i, k in enumerate(ks):
        if k == "Cancel channel" and i + 1 < len(ks):
            after[ks[i + 1]] += 1
print("opponent: action right after a cancel:", after.most_common(6))

# 4) items: SDK item enum order from cambc.h
h = open(sys.argv[3], encoding="utf-8", errors="replace").read()
start = h.index("class item_type")
block = h[start:h.index("count", h.index("enum class enum_type", start))]
names = re.findall(r"^\s*([a-z_]+),\s*$", block, re.M)
for t in (0, 1):
    tot = collections.Counter()
    for cid, tm, ty, items in d["items"]:
        if tm != t:
            continue
        for i, n in enumerate(items):
            if n:
                tot[names[i] if i < len(names) else str(i)] += n
    print(("us  " if t == 0 else "them"), "final items:", dict(tot.most_common(14)))
