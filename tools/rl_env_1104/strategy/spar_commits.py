"""Per-raid-commitment accounting for sparring runs with stdout logs (JOHNDOE #164).

A commitment is an SPR row with group >= 0 for one raider; it lasts until that raider's next SPR row (or match end).
It *completes* when our team collects camp gems from that group during the commitment plus a 10-round tail; the
enemy *took* it when the enemy collected from it in the same window. Two raiders on the same group at the same round
are counted as a shared commitment.
usage: python -I tools/rl_env_1104/strategy/spar_commits.py <run_eval dir> <candidate>
"""
import collections, json, os, sys, zipfile

run, cand = sys.argv[1], sys.argv[2]
rep = json.load(open(os.path.join(run, "report.json"), encoding="utf-8"))
norm = lambda p: os.path.abspath(p).replace("\\", "/").lower()
cdir = norm(rep["candidates"][cand]); opps = {norm(v): k for k, v in rep["opponents"].items()}
agg = collections.defaultdict(collections.Counter)
for i, line in enumerate(open(os.path.join(run, "work", "batch.txt"), encoding="utf-8")):
    q = line.split(); a, b = q[0].lower(), q[1].lower()
    if a == cdir and b in opps: o, our, side = opps[b], "teamA", "a"
    elif b == cdir and a in opps: o, our, side = opps[a], "teamB", "b"
    else: continue
    s = json.load(open(os.path.join(run, "work", f"g{i}.json"), encoding="utf-8"))
    txt = zipfile.ZipFile(os.path.join(run, "work", f"g{i}.repl26a")).read(f"team-{side}.stdout").replace(bytes(1), b"\n").decode("utf-8", "replace").splitlines()
    spr = [list(map(int, l.split()[1:6])) for l in txt if l.startswith("SPR ")]
    end = s["match"]["roundsCompleted"]
    col = collections.defaultdict(list)
    for e in s["events"]:
        if e["kind"] == "gemCollection":
            for x in e["entries"]:
                if x["context"] == "campGroup":
                    col[x["target"]["id"]].append((x["timestamp"]["round"], e["owner"]["team"], float(x["value"])))
    by = collections.defaultdict(list)
    for r in spr: by[r[1]].append(r)
    starts = collections.Counter((r[0] // 5, r[4]) for r in spr if r[4] >= 0)
    k = agg[o]; k["games"] += 1; k["wins"] += s["match"]["outcome"] == our
    for rid, rs in by.items():
        for j, r in enumerate(rs):
            if r[4] < 0: continue
            st, g = r[0], r[4]; en = rs[j + 1][0] if j + 1 < len(rs) else end
            ev = [x for x in col.get(g, []) if st <= x[0] <= en + 10]
            ours = sum(v for _, t, v in ev if t == our); theirs = sum(v for _, t, v in ev if t != our)
            k["commits"] += 1; k["commit_rounds"] += en - st
            k["completed"] += ours > 0; k["enemy_took"] += theirs > 0 and ours == 0
            k["gems_won"] += ours; k["shared"] += starts[(st // 5, g)] > 1
for o, k in sorted(agg.items()):
    n = k["commits"] or 1
    print(f"{cand} vs {o}: {k['wins']}/{k['games']} wins | commits/game {k['commits']/k['games']:.1f}, mean length {k['commit_rounds']/n:.0f} rounds, "
          f"completed {k['completed']/n:.0%}, enemy took first {k['enemy_took']/n:.0%}, gems won/commit {k['gems_won']/n:.1f}, shared starts {k['shared']/n:.0%}")
