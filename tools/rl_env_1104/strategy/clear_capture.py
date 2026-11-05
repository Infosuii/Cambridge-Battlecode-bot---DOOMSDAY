"""Who collects the camps a team clears? (cleared-but-stolen accounting from official events.)

For each campClear by a team (group id, round), the next gemCollection from that group within --window rounds is
attributed: own team (converted), enemy (stolen), or none (unresolved). Also gems per clear.
usage: python -I tools/rl_env_1104/strategy/clear_capture.py <run_eval dir> [--window 40]
"""
import argparse, bisect, collections, json, os

ap = argparse.ArgumentParser(); ap.add_argument("run"); ap.add_argument("--window", type=int, default=40); a = ap.parse_args()
rep = json.load(open(os.path.join(a.run, "report.json"), encoding="utf-8"))
norm = lambda p: os.path.abspath(p).replace("\\", "/").lower()
cands = {norm(v): k for k, v in rep["candidates"].items()}; opps = {norm(v): k for k, v in rep["opponents"].items()}
agg = collections.defaultdict(collections.Counter)
for i, line in enumerate(open(os.path.join(a.run, "work", "batch.txt"), encoding="utf-8")):
    q = line.split(); pa, pb = q[0].lower(), q[1].lower()
    if pa in cands and pb in opps: c, o, our = cands[pa], opps[pb], "teamA"
    elif pb in cands and pa in opps: c, o, our = cands[pb], opps[pa], "teamB"
    else: continue
    s = json.load(open(os.path.join(a.run, "work", f"g{i}.json"), encoding="utf-8"))
    res = "win" if s["match"]["outcome"] == our else "loss"
    clears, cols = [], collections.defaultdict(list)
    for e in s["events"]:
        t = e["owner"].get("team")
        for x in e["entries"]:
            if e["kind"] == "campClear":
                clears.append((x["timestamp"]["ordinal"], x["timestamp"]["round"], x["target"]["id"], t))
            elif e["kind"] == "gemCollection" and x["context"] == "campGroup":
                cols[x["target"]["id"]].append((x["timestamp"]["ordinal"], x["timestamp"]["round"], t, float(x["value"])))
    for g in cols: cols[g].sort()
    for od, rd, g, t in clears:
        side = "our" if t == our else "their"
        lst = cols.get(g, []); j = bisect.bisect_left(lst, (od,))
        k = agg[(c, o, res, side)]; k["clears"] += 1
        if j < len(lst) and lst[j][1] <= rd + a.window:
            got = lst[j][2]; k["gems"] += lst[j][3]
            k["converted" if got == t else "stolen"] += 1
            if got != t: k["stolen_gems"] += lst[j][3]
        else:
            k["none"] += 1
for key in sorted(agg):
    k = agg[key]; n = k["clears"] or 1
    print(f"{key[0]:5s} vs {key[1]:8s} {key[2]:4s} {key[3]:5s}: clears {k['clears']:5d} converted {k['converted']/n:.0%} stolen {k['stolen']/n:.0%} none {k['none']/n:.0%} gems/clear {k['gems']/n:.1f} stolen gems {k['stolen_gems']:.0f}")
