import sys, os, json, glob, zipfile, collections
W = sys.argv[1]
agg = collections.defaultdict(collections.Counter)
for f in sorted(glob.glob(os.path.join(W, "*.json"))):
    tag = os.path.basename(f)[:-5]; v, side = tag.split("-")[0], tag.split("-")[-1]
    s = json.load(open(f, encoding="utf-8")); our = "team" + side
    txt = zipfile.ZipFile(f[:-5] + ".repl26a").read(f"team-{side.lower()}.stdout").replace(bytes(1), b"\n").decode("utf-8", "replace").splitlines()
    spr = [list(map(int, l.split()[1:])) for l in txt if l.startswith("SPR ")]
    spc = [l for l in txt if l.startswith("SPC ")]
    k = agg[v]; k["games"] += 1; k["wins"] += s["match"]["outcome"] == our
    k["SPR"] += len(spr); k["SPR_none"] += sum(r[4] < 0 for r in spr); k["SPC"] += len(spc)
    # raider target intervals: id -> [(start, group)]
    iv = collections.defaultdict(list)
    for r in spr: iv[r[1]].append((r[0], r[4]))
    raiders = set(iv)
    for e in s["events"]:
        if e["kind"] != "gemCollection" or e["owner"]["team"] != our: continue
        oid = e["owner"]["id"]
        for x in e["entries"]:
            if x["context"] != "campGroup": continue
            val = float(x["value"]); rnd = x["timestamp"]["round"]
            k["team_camp_gems"] += val
            if oid in raiders:
                k["raider_camp_gems"] += val
                cur = None
                for st, g in iv[oid]:
                    if st <= rnd: cur = g
                if cur is not None and cur >= 0 and cur == x["target"]["id"]: k["raider_gems_from_spar_target"] += val
for v, k in agg.items():
    print(v, dict(k))
