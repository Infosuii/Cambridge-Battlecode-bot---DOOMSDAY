"""B1: can the enemy's draft identify the team? From a decoded set: for each game side, key = (map key, side, sorted
enemy lineup types). Accuracy of 'most frequent team for this key' (leave-one-out), for top-N teams' sides, and the
share of their games whose key is seen only for that team. usage: python -P b1_ident.py DECODED_DIR bt25.tsv N"""
import collections, gzip, json, os, sys
D, BT, N = sys.argv[1], sys.argv[2], int(sys.argv[3])
top = [l.split("\t")[0] for l in open(BT)][:N]
rows = []
for f in os.listdir(D):
    if f.endswith(".json.gz"):
        d = json.load(gzip.open(os.path.join(D, f)))
        for t in (0, 1):
            lu = tuple(sorted(c["type"] for c in d["champs"] if c["team"] == t))
            rows.append((d["teams"][t], d["key"], t, lu))
for name, keyf in (("map+side+lineup", lambda r: (r[1], r[2], r[3])), ("map+lineup", lambda r: (r[1], r[3])), ("lineup only", lambda r: r[3])):
    cnt = collections.defaultdict(collections.Counter)
    for r in rows:
        cnt[keyf(r)][r[0]] += 1
    hit = tot = uniq = 0
    for r in rows:
        if r[0] not in top:
            continue
        c = cnt[keyf(r)].copy(); c[r[0]] -= 1
        c = +c
        if not c:
            continue  # key never seen elsewhere: no evidence
        tot += 1
        hit += c.most_common(1)[0][0] == r[0]
        uniq += len(c) == 1 and r[0] in c
    print(f"{name}: top-{N} sides with a previously seen key {tot}, identified {hit / max(1, tot):.2f}, key unique to the team {uniq / max(1, tot):.2f}")
