"""E125: BOT at real fuel on games no earlier test played: 300 official (70 maps x 2 sides vs new noisy copies v92j6 and v92j7, 10 maps x 2 vs v92j8) and 300 unseen (75 maze + 75 real-style maps x 2 sides vs v92,
excluding the maps e124_c4.py used). Rows go to OUT.tsv (held_run.py's format). usage (project root): python -P agent2/lab/e125_c4.py BOT OUT.tsv"""
import json, math, os, random, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
V4 = os.path.join(ROOT, "v4")
BOT, OUT = sys.argv[1], sys.argv[2]


def maps(d):
    return sorted(f for f in os.listdir(os.path.join(V4, d)) if f.endswith(".map26a"))


def free_gb():
    out = subprocess.run(["powershell", "-NoProfile", "-c", "(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB"], capture_output=True, text=True).stdout
    try:
        return float(out.strip().splitlines()[-1])
    except Exception:
        return 99.0


# the unseen maps of the earlier 100-game test (same seed, same order of draws as e124_c4.py)
old = random.Random(124)
old.sample(maps("maps"), 50)
used_m, used_r = set(old.sample(maps("maps_mazetest"), 25)), set(old.sample(maps("maps_real200b"), 25))
rng = random.Random(125)
off = maps("maps")
games = [("official", "maps", m, "v92j6") for m in off] + [("official", "maps", m, "v92j7") for m in off] + [("official", "maps", m, "v92j8") for m in rng.sample(off, 10)]
games += [("unseen", "maps_mazetest", m, "v92") for m in rng.sample([m for m in maps("maps_mazetest") if m not in used_m], 75)]
games += [("unseen", "maps_real200b", m, "v92") for m in rng.sample([m for m in maps("maps_real200b") if m not in used_r], 75)]
tag = f"bench_out/e125c/{BOT}"
shutil.rmtree(os.path.join(V4, tag), ignore_errors=True)
os.makedirs(os.path.join(V4, tag))
lines, keys = [], []
for suite, d, m, o in games:
    for s in "AB":
        a, b = (BOT, o) if s == "A" else (o, BOT)
        f = f"{tag}/{d}_{o}_{m[:-7]}_{s}"
        lines.append(f"bots/{a} bots/{b} {d}/{m} {f}.repl26a --statistics {f}.json --json")
        keys.append((suite, d, m[:-7], o, s, f + ".json"))
man = os.path.join(V4, f".m_e125c_{BOT}.txt")
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
