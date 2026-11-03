"""B1: are teams' openings repeatable? For each (team, map key, side) with 2+ games in a decoded set (p1_decode.js
output), pairs of games: the first round where this team's champions' positions differ (champions matched by type and
draft order) and the first round where any enemy came within 6 tiles of one of them (contact). If divergence ~=
contact, the opening is a fixed script until the enemy is seen, so a recorded opening is an exact opponent model.
usage: python -P b1_repeat.py DECODED_DIR [bt25.tsv top-N]"""
import base64, collections, gzip, itertools, json, os, sys
import numpy as np
D = sys.argv[1]
top = None
if len(sys.argv) > 2:
    rows = [l.rstrip("\n").split("\t") for l in open(sys.argv[2])][1:]
    top = {r[0] for r in rows[:int(sys.argv[3])]}
games = collections.defaultdict(list)
for f in os.listdir(D):
    if not f.endswith(".json.gz"):
        continue
    d = json.load(gzip.open(os.path.join(D, f)))
    cs = np.frombuffer(base64.b64decode(d["cs"]), np.int16).reshape(len(d["rounds"]), d["NS"], d["NF"])
    for t in (0, 1):
        tid = d["teams"][t]
        if top is not None and tid not in top:
            continue
        mine = [i for i, c in enumerate(d["champs"]) if c["team"] == t]
        theirs = [i for i, c in enumerate(d["champs"]) if c["team"] != t]
        games[(tid, d["key"], t)].append((f, d["rounds"], cs, mine, theirs, tuple(sorted(d["champs"][i]["type"] for i in mine))))
div, con, same_lu, n = [], [], 0, 0
for k, gl in games.items():
    for a, b in itertools.combinations(gl[:6], 2):
        n += 1
        if a[5] != b[5]:
            continue
        same_lu += 1
        R = min(len(a[1]), len(b[1]), 400)
        ma = sorted(a[3], key=lambda i: (a[2][0, i, 0], i)); mb = sorted(b[3], key=lambda i: (b[2][0, i, 0], i))
        dr = R
        for r in range(R):
            if any(a[2][r, i, 0] != b[2][r, j, 0] or a[2][r, i, 1] != b[2][r, j, 1] for i, j in zip(ma, mb)):
                dr = r; break
        cr = R
        for g in (a, b):
            for r in range(R):
                P = g[2][r]
                if any(P[i, 6] and P[e, 6] and max(abs(int(P[i, 0]) - P[e, 0]), abs(int(P[i, 1]) - P[e, 1])) <= 6 for i in g[3] for e in g[4]):
                    cr = min(cr, r); break
        div.append(a[1][dr] if dr < R else 9999); con.append(a[1][cr] if cr < R else 9999)
div, con = np.array(div), np.array(con)
print(f"team-map-sides with 2+ games {sum(len(v) > 1 for v in games.values())}, pairs {n}, same lineup {same_lu}")
if len(div):
    print("divergence round quantiles 10/25/50/75/90:", np.percentile(div, [10, 25, 50, 75, 90]).astype(int))
    print("contact round quantiles:", np.percentile(con, [10, 25, 50, 75, 90]).astype(int))
    print(f"diverge before contact (by >2 rounds): {np.mean(div < con - 2):.2f}; at/after contact: {np.mean(div >= con - 2):.2f}")
# macro repeatability: per pair with the same lineup, share of champions within 3 / 8 tiles of the other game's
# same-type champion at rounds 20 / 40 / 60 / 100 / 150 (types matched greedily by distance)
near = collections.defaultdict(list)
for k, gl in games.items():
    for a, b in itertools.combinations(gl[:6], 2):
        if a[5] != b[5]:
            continue
        for R in (20, 40, 60, 100, 150):
            ia = [i for i, r in enumerate(a[1]) if r == R]; ib = [i for i, r in enumerate(b[1]) if r == R]
            if not ia or not ib:
                continue
            Pa, Pb = a[2][ia[0]], b[2][ib[0]]
            for i in a[3]:
                ti = None
                ds = [max(abs(int(Pa[i, 0]) - Pb[j, 0]), abs(int(Pa[i, 1]) - Pb[j, 1])) for j in b[3]]
                near[R].append(min(ds))
for R in sorted(near):
    v = np.array(near[R])
    print(f"round {R}: champions within 3 tiles of a same-team champion in the other game {np.mean(v <= 3):.2f}, within 8 {np.mean(v <= 8):.2f}")
# baseline: two different teams on the same map and side
bykey = collections.defaultdict(list)
for (tid, key, t), gl in games.items():
    bykey[(key, t)].append(gl[0])
base = collections.defaultdict(list)
for k, gl in bykey.items():
    for a, b in itertools.combinations(gl[:6], 2):
        for R in (20, 40, 60, 100, 150):
            ia = [i for i, r in enumerate(a[1]) if r == R]; ib = [i for i, r in enumerate(b[1]) if r == R]
            if not ia or not ib:
                continue
            Pa, Pb = a[2][ia[0]], b[2][ib[0]]
            for i in a[3]:
                base[R].append(min(max(abs(int(Pa[i, 0]) - Pb[j, 0]), abs(int(Pa[i, 1]) - Pb[j, 1])) for j in b[3]))
for R in sorted(base):
    v = np.array(base[R])
    print(f"baseline (different teams) round {R}: within 3 {np.mean(v <= 3):.2f}, within 8 {np.mean(v <= 8):.2f} (n {len(v)})")
# different teams, same map, side and lineup: is the opening a property of the lineup (meta) or of the team?
bykl = collections.defaultdict(list)
for (tid, key, t), gl in games.items():
    for g in gl[:3]:
        bykl[(key, t, g[5])].append((tid, g))
ml = collections.defaultdict(list)
for k, gl in bykl.items():
    for (ta, a), (tb, b) in itertools.combinations(gl, 2):
        if ta == tb:
            continue
        for R in (40, 60, 100):
            ia = [i for i, r in enumerate(a[1]) if r == R]; ib = [i for i, r in enumerate(b[1]) if r == R]
            if ia and ib:
                Pa, Pb = a[2][ia[0]], b[2][ib[0]]
                for i in a[3]:
                    ml[R].append(min(max(abs(int(Pa[i, 0]) - Pb[j, 0]), abs(int(Pa[i, 1]) - Pb[j, 1])) for j in b[3]))
for R in sorted(ml):
    v = np.array(ml[R])
    print(f"different teams, same lineup, round {R}: within 3 {np.mean(v <= 3):.2f}, within 8 {np.mean(v <= 8):.2f} (n {len(v)})")
