"""E121: read the A2_FUELLOG lines of an A2_NN_LIVE bot from fuel_probe.py's replays: decisions by round 100, overruns by the
kind of turn they happened on, fuel of the first turns and the share of later turns at the 100k cap.
usage (project root): python -P agent2/lab/live_stats.py BOT [OPP]"""
import collections, glob, re, struct, sys, zipfile

BOT = sys.argv[1]
OPP = sys.argv[2] if len(sys.argv) > 2 else "v92"
paths, early, tot_over, tot_turns = collections.Counter(), [], 0, 0
for f in sorted(glob.glob(f"v4/bench_out/fuelprobe/{BOT}_vs_{OPP}_real/*.repl26a")):
    side = f[-9]
    z = zipfile.ZipFile(f)
    t = z.read(f"team-{side.lower()}.stdout").replace(b"\0", b"").decode("utf-8", "replace").splitlines()
    over = 0
    for l in t:
        m = re.match(r"nnover round (\d+) path (\d) kind (\d) mark (\d+) need (\d+) fields (\d+) enemies (\d+)", l)
        if m:
            over += 1
            paths[(m.group(2), m.group(3) if m.group(2) != "3" else "-")] += 1
            if int(m.group(1)) < 100:
                early.append(int(m.group(1)))
    live = [l for l in t if l.startswith("nnlive")]
    r100 = [l for l in live if l.startswith("nnlive round 100 ")]
    b = z.read(f"team-{side.lower()}.fuel")
    n = (len(b) - 13) // 8
    v = struct.unpack(f"<{n}Q", b[13:13 + 8 * n])[8:]
    later = v[16:]
    tot_over += over
    tot_turns += len(v)
    print(f.replace(chr(92), "/").split("/")[-1][:-8], "over", over, "|", r100[0][7:78] if r100 else "", "| fuel", [x // 1000 for x in v[3:13]],
          f"mean {sum(later) / max(1, len(later)) / 1000:.0f}k cap {100 * sum(x >= 100000 for x in later) / max(1, len(later)):.1f}%")
    if live:
        print("   last:", live[-1][7:150])
print(f"overruns {tot_over} of {tot_turns} turns = {100 * tot_over / max(1, tot_turns):.2f}%; before round 100: {len(early)}")
print("by (path, kind); path 0 hold, 1 camps, 2 full, 3 contact; kind 0 no enemy, 1 far, 2 within 10:", paths.most_common(12))
