import sys, os, json, collections
sys.path.insert(0, sys.argv[1])
from carrier_events import measure
run = sys.argv[2]
rep = json.load(open(os.path.join(run, "report.json"), encoding="utf-8"))
norm = lambda p: os.path.abspath(p).replace("\\", "/").lower()
cands = {norm(v): k for k, v in rep["candidates"].items()}
opps = {norm(v): k for k, v in rep["opponents"].items()}
agg = collections.defaultdict(collections.Counter)
for i, line in enumerate(open(os.path.join(run, "work", "batch.txt"), encoding="utf-8")):
    q = line.split(); a, b = q[0].lower(), q[1].lower()
    if a in cands and b in opps: c, o, our = cands[a], opps[b], "teamA"
    elif b in cands and a in opps: c, o, our = cands[b], opps[a], "teamB"
    else: continue
    m = measure(json.load(open(os.path.join(run, "work", f"g{i}.json"), encoding="utf-8")))
    th = "teamB" if our == "teamA" else "teamA"
    k = agg[(c, o)]; k["games"] += 1
    for e in m["episodes"]:
        if e["team"] == th: k["enemy_ep"] += 1; k["enemy_" + e["outcome"]] += 1
        else: k["our_ep"] += 1; k["our_" + e["outcome"]] += 1
    for f, v in m["teams"][th].items(): k["enemy_tot_" + f] += v
out = {}
for (c, o), k in sorted(agg.items()):
    n = k["enemy_ep"] or 1
    out[f"{c} vs {o}"] = dict(k, enemy_lost_rate=round(k["enemy_lost_at_death"] / n, 3), enemy_dep_rate=round(k["enemy_deposited"] / n, 3))
    r = out[f"{c} vs {o}"]
    print(f"{c:8s} vs {o:8s} enemy 30+ carriers {k['enemy_ep']:4d}  lost {k['enemy_lost_at_death']:3d} ({r['enemy_lost_rate']:.3f})  deposited {k['enemy_deposited']:3d} ({r['enemy_dep_rate']:.3f})  enemy death gems/game {k['enemy_tot_death_gems']/k['games']:.1f}  enemy large death losses {k['enemy_tot_large_death_losses']}  | our carriers lost {k['our_lost_at_death']}/{k['our_ep']}")
json.dump(out, open(sys.argv[3], "w"), indent=1)
