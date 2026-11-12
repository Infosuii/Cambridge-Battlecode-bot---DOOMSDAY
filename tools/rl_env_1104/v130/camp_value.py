"""Is waiting at the small home camps worth it? From v130's debug game: gem income per champion-round while in a
wait-respawn episode at a home small-camp group versus the rest of the time, how often two champions wait together,
and how long each wait lasts. usage: camp_value.py team-a.stdout dump.json summary.json"""
import collections, json, re, sys

sys.stdout.reconfigure(encoding="utf-8")
modes = {}
for line in open(sys.argv[1], encoding="utf-8", errors="replace"):
    m = re.match(r"\s*M (\d+) (\d+) (\S+) (-?\d+)", line)
    if m:
        modes[(int(m.group(1)), int(m.group(2)))] = (m.group(3), int(m.group(4)))
d = json.load(open(sys.argv[2], encoding="utf-8"))
s = json.load(open(sys.argv[3], encoding="utf-8"))
fr = d["frames"]
last = fr[-1][0]
HOME_GROUPS = {10, 12}  # the small home-camp groups the trace showed (camps 62 / 64 by our spawn)

# per champion per round: in a home-camp episode = mode in (wait-respawn, capture, to-capture, fight) with target in HOME_GROUPS
ep = collections.defaultdict(set)
for (r, cid), (md, g) in modes.items():
    if g in HOME_GROUPS and md in ("wait-respawn", "capture", "to-capture", "capture-stand", "fight", "approach"):
        ep[cid].add(r)
# gem collection events of our champions
col = collections.defaultdict(list)
for e in s["events"]:
    if e["kind"] == "gemCollection" and e["owner"].get("kind") == "champion" and e["owner"]["team"] == "teamA":
        for x in e["entries"]:
            col[e["owner"]["id"]].append((x["timestamp"]["round"], int(x["value"])))
tot_in = tot_out = r_in = r_out = 0
for cid in range(6):
    alive_rounds = {f[0] for f in fr for c in f[1] if c[0] == cid and c[6]}
    rin = len(ep[cid] & alive_rounds)
    rout = len(alive_rounds) - rin
    gin = sum(v for r, v in col[cid] if r in ep[cid] or r - 1 in ep[cid])
    gout = sum(v for r, v in col[cid]) - gin
    tot_in += gin; tot_out += gout; r_in += rin; r_out += rout
    print(f"champion {cid}: home-camp rounds {rin:4d}, gems there {gin:4d} ({gin / max(1, rin):.3f}/round) | "
          f"elsewhere {rout:4d} rounds, gems {gout:4d} ({gout / max(1, rout):.3f}/round)")
print(f"TEAM: at home small camps {tot_in} gems in {r_in} champion-rounds = {tot_in / max(1, r_in):.3f}/round; "
      f"elsewhere {tot_out} gems in {r_out} = {tot_out / max(1, r_out):.3f}/round")
# concurrency: rounds with >= 2 of our champions waiting on the same home group
both = collections.Counter()
for r in range(1, last + 1):
    per = collections.Counter(g for cid in range(6) for (md, g) in [modes.get((r, cid), ("", -1))] if md == "wait-respawn" and g in HOME_GROUPS)
    for g, n in per.items():
        if n >= 2:
            both[g] += n - 1
print("extra champion-rounds from 2+ champions waiting on the same home group:", dict(both))
# wait-episode lengths
lens = []
for cid in range(6):
    run = 0
    for r in range(1, last + 2):
        md, g = modes.get((r, cid), ("", -1))
        if md == "wait-respawn" and g in HOME_GROUPS:
            run += 1
        elif run:
            lens.append(run); run = 0
lens.sort()
print(f"wait episodes at home groups: {len(lens)}, median {lens[len(lens) // 2] if lens else 0} rounds, "
      f"p90 {lens[int(.9 * len(lens))] if lens else 0}, total {sum(lens)} champion-rounds")
