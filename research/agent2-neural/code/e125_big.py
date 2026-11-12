"""E125: why does the fitted blend lose on big official maps? A fuel-log build on every official map, one side vs v92: scoring share, fuel left at v92's choice, search skips, turns at the cap, win, by map size.
usage (project root): python -P agent2/lab/e125_big.py LOGBOT"""
import collections, json, os, re, shutil, struct, subprocess, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
V4 = os.path.join(ROOT, "v4")
BOT = sys.argv[1]
s = open(os.path.join(V4, "bots", "v92", "src", "ladfit.h"), encoding="utf-8").read()
fp = re.findall(r"\{(\d+),(\d+),(\d+),(\d+)u\}", s)[:70]
names = sorted(f[:-7] for f in os.listdir(os.path.join(V4, "maps")) if f.endswith(".map26a"))
info = {n: (max(int(a), int(b)), int(c)) for n, (a, b, c, _) in zip(names, fp)}
tag = f"bench_out/e125big_{BOT}"
shutil.rmtree(os.path.join(V4, tag), ignore_errors=True)
os.makedirs(os.path.join(V4, tag))
lines = [f"bots/{BOT} bots/v92 maps/{n}.map26a {tag}/{n}.repl26a --statistics {tag}/{n}.json --json" for n in names]
man = os.path.join(V4, ".m_e125big.txt")
open(man, "w").write("\n".join(lines) + "\n")
subprocess.run([os.path.join(V4, "cambc.exe"), "run-batch", man, "--jobs", "6", "--json", "--color", "never", "--release", "--log-limit", "67108864"], cwd=V4, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
B = collections.defaultdict(lambda: collections.defaultdict(float))
pat = re.compile(r"nnfarm n (\d+) left ((?:\d+ ?){11}) gate ((?:\d+ ?){11}) est (\d+) floor (\d+) full (\d+) hold (\d+)")
for n in names:
    size, groups = info[n]
    k = "<=40" if size <= 40 else "41-60" if size <= 60 else ">60"
    try:
        z = zipfile.ZipFile(os.path.join(V4, tag, n + ".repl26a"))
        t = z.read("team-a.stdout").replace(b"\0", b"").decode("utf-8", "replace").splitlines()
        b = z.read("team-a.fuel")
        res = json.load(open(os.path.join(V4, tag, n + ".json")))
    except Exception:
        continue
    N = (len(b) - 13) // 8
    v = struct.unpack(f"<{N}Q", b[13:13 + 8 * N])[8:]
    later = v[16:]
    d = B[k]
    d["games"] += 1
    d["groups"] += groups
    d["win"] += res["match"].get("outcome") == "teamA"
    d["turns"] += len(later)
    d["cap"] += sum(x >= 100000 for x in later)
    d["fuel"] += sum(later)
    # one champion's counters at its last print, per champion block
    lv = [l for l in t if l.startswith("nnlive")]
    for l in lv[-6:]:
        m = re.search(r"camps (\d+) hold (\d+)", l)
        if m:
            d["camps"] += int(m.group(1))
            d["hold"] += int(m.group(2))
    fm = [pat.match(l) for l in t if l.startswith("nnfarm")]
    fm = [m for m in fm if m]
    for m in fm[-6:]:
        for i, c in enumerate(m.group(2).split()):
            d[f"left{i}"] += int(c)
        d["est"] += int(m.group(4))
        d["floor"] += int(m.group(5))
        d["fm"] += 1
print("size  games groups  win%  mean fuel  cap%  scored%   est  floor | fuel left at v92's choice, share by 10k: 0-10 .. 100+")
for k in ("<=40", "41-60", ">60"):
    d = B[k]
    tot = sum(d[f"left{i}"] for i in range(11)) or 1
    print(f"{k:6s}{d['games']:5.0f} {d['groups'] / max(1, d['games']):6.1f} {100 * d['win'] / max(1, d['games']):5.1f} {d['fuel'] / max(1, d['turns']) / 1000:8.0f}k {100 * d['cap'] / max(1, d['turns']):5.2f} {100 * d['camps'] / max(1, d['camps'] + d['hold']):7.1f} {d['est'] / max(1, d['fm']) / 1000:5.0f}k {d['floor'] / max(1, d['fm']) / 1000:5.0f}k | " + " ".join(f"{100 * d[f'left{i}'] / tot:3.0f}" for i in range(11)))
shutil.rmtree(os.path.join(V4, tag), ignore_errors=True)
