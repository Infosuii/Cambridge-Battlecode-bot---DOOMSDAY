"""E124: BOT at real fuel, games it was not picked on: 50 of the 70 official maps x 2 sides vs a new noisy copy of v92 (100 games), and 25 maze + 25 real-style unseen maps x 2 sides vs v92 (100 games).
Maps are a fixed random sample. Rows go to OUT.tsv (held_run.py's format). usage (project root): python -P agent2/lab/e124_c4.py BOT OUT.tsv [OFFICIAL_OPP=v92j5]"""
import json, math, os, random, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
V4 = os.path.join(ROOT, "v4")
BOT, OUT = sys.argv[1], sys.argv[2]
OFF_OPP = sys.argv[3] if len(sys.argv) > 3 else "v92j5"


def maps(d):
    return sorted(f for f in os.listdir(os.path.join(V4, d)) if f.endswith(".map26a"))


def free_gb():
    out = subprocess.run(["powershell", "-NoProfile", "-c", "(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB"], capture_output=True, text=True).stdout
    try:
        return float(out.strip().splitlines()[-1])
    except Exception:
        return 99.0


rng = random.Random(124)
games = [("official", "maps", m, OFF_OPP) for m in rng.sample(maps("maps"), 50)]
games += [("unseen", "maps_mazetest", m, "v92") for m in rng.sample(maps("maps_mazetest"), 25)]
games += [("unseen", "maps_real200b", m, "v92") for m in rng.sample(maps("maps_real200b"), 25)]
tag = f"bench_out/e124c/{BOT}"
shutil.rmtree(os.path.join(V4, tag), ignore_errors=True)
os.makedirs(os.path.join(V4, tag))
lines, keys = [], []
for suite, d, m, o in games:
    for s in "AB":
        a, b = (BOT, o) if s == "A" else (o, BOT)
        f = f"{tag}/{d}_{m[:-7]}_{s}"
        lines.append(f"bots/{a} bots/{b} {d}/{m} {f}.repl26a --statistics {f}.json --json")
        keys.append((suite, d, m[:-7], o, s, f + ".json"))
man = os.path.join(V4, f".m_e124c_{BOT}.txt")
open(man, "w").write("\n".join(lines) + "\n")
while free_gb() < 3.0:
    time.sleep(30)
t0 = time.time()
p = subprocess.Popen([os.path.join(V4, "cambc.exe"), "run-batch", man, "--jobs", "8", "--json", "--color", "never", "--release"], cwd=V4, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
while p.poll() is None:
    time.sleep(3)
    if free_gb() < 2.0:
        p.kill()
        print("KILLED by watchdog (free RAM under 2 GB)", flush=True)
sc = {"official": [0.0, 0], "unseen": [0.0, 0]}
rows = []
for suite, d, m, o, s, f in keys:
    try:
        res = json.load(open(os.path.join(V4, f)))
    except Exception:
        continue
    oc = res["match"].get("outcome")
    me, them = ("teamA", "teamB") if s == "A" else ("teamB", "teamA")
    win = 1.0 if oc == me else 0.0 if oc == them else 0.5
    sc[suite][0] += win
    sc[suite][1] += 1
    gems = {t["team"]: t["submittedGems"] for t in res.get("teams", [])}
    rows.append(f"{BOT}\t{o}\t{d}~{m}\t{s}\t{win}\t{gems.get(me, '')}\t{gems.get(them, '')}\n")
open(OUT, "a").writelines(rows)
shutil.rmtree(os.path.join(V4, tag), ignore_errors=True)
for k, (w, n) in sc.items():
    r = w / max(1, n)
    print(f"{BOT} {k}: {w:.1f}/{n} = {100 * r:.1f}% +- {100 * math.sqrt(r * (1 - r) / max(1, n)):.1f}", flush=True)
print(f"{time.time() - t0:.0f}s", flush=True)
