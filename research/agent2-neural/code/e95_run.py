"""E95: real-engine screen of v92 variants vs v92 (70 ladder maps x 2 + maps_real250 150-199 x 2 = 240 games each).
Builds each candidate in turn (one build at a time), runs its batch with a RAM watchdog (kills the batch under 2 GB
free), prints ladder / unseen / total.
usage (project root): python agent2/lab/e95_run.py OPP CAND [CAND..] [--maps DIR:A:B,DIR:A:B] [--tag T] [--fuel N]
(--maps: every set but maps/ counts as unseen; results go to bench_out/e95/<T or CAND_vs_OPP>/<l|u>_<suite>~<map>_<A|B>)
"""
import json, os, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
V4 = os.path.join(ROOT, "v4")
CAMBC = os.path.join(V4, "cambc.exe")
ARGS = sys.argv[1:]
MAPSPEC = ARGS[ARGS.index("--maps") + 1] if "--maps" in ARGS else None
TAG = ARGS[ARGS.index("--tag") + 1] if "--tag" in ARGS else None
FUEL = ARGS[ARGS.index("--fuel") + 1] if "--fuel" in ARGS else None  # --fuel N: run-batch --fuel-quantum N (fuel per turn)
ARGS = [a for i, a in enumerate(ARGS) if not a.startswith("--") and (i == 0 or not ARGS[i - 1].startswith("--"))]
OPP, CANDS = ARGS[0], ARGS[1:]


def free_gb():
    out = subprocess.run(["powershell", "-NoProfile", "-c", "(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB"],
                         capture_output=True, text=True).stdout
    try:
        return float(out.strip().splitlines()[-1])
    except Exception:
        return 99.0


def maps(d, a=0, b=10 ** 9):
    return [f"{d}/{f}" for f in sorted(os.listdir(os.path.join(V4, d))) if f.endswith(".map26a")][a:b]


SETS = [("ladder", maps("maps", 0, 70)), ("unseen", maps("maps_real250", 150, 200))]
if MAPSPEC:
    SETS = []
    for spec in MAPSPEC.split(","):
        d, a, b = (spec.split(":") + ["0", "100000"])[:3]
        SETS.append(("ladder" if d == "maps" else "unseen", maps(d, int(a), int(b))))
for cand in CANDS:
    r = subprocess.run([CAMBC, "build", f"bots/{cand}", "--release"], cwd=V4, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"{cand}: BUILD FAILED\n{(r.stdout + r.stderr)[-800:]}", flush=True)
        continue
    tag = f"e95/{TAG or cand + '_vs_' + OPP}"
    # run-batch refuses to overwrite: clear old results so they cannot be read as this run's
    shutil.rmtree(os.path.join(V4, "bench_out", tag), ignore_errors=True)
    os.makedirs(os.path.join(V4, "bench_out", tag), exist_ok=True)
    lines, keys = [], []
    for kind, ms in SETS:
        for m in ms:
            name = (os.path.dirname(m) + "~" if MAPSPEC else "") + os.path.basename(m)[:-7]
            for s in "AB":
                a, b = (cand, OPP) if s == "A" else (OPP, cand)
                f = f"bench_out/{tag}/{kind[0]}_{name}_{s}"
                lines.append(f"bots/{a} bots/{b} {m} {f}.repl26a --statistics {f}.json --json")
                keys.append((kind, s, f + ".json"))
    man = os.path.join(V4, f".m_e95_{cand}.txt")
    open(man, "w").write("\n".join(lines) + "\n")
    while free_gb() < 3.0:
        print("free RAM under 3 GB, waiting 1 min", flush=True)
        time.sleep(60)
    t0 = time.time()
    p = subprocess.Popen([CAMBC, "run-batch", man, "--jobs", os.environ.get("E95_JOBS", "5"), "--json", "--color", "never", "--release"] +
                         (["--fuel-quantum", FUEL] if FUEL else []), cwd=V4,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    killed = False
    while p.poll() is None:
        time.sleep(5)
        if free_gb() < 2.0:
            p.kill()
            killed = True
            print(f"{cand}: KILLED by watchdog (free RAM under 2 GB)", flush=True)
    sc = {"ladder": [0.0, 0], "unseen": [0.0, 0]}
    for kind, s, f in keys:
        try:
            oc = json.load(open(os.path.join(V4, f)))["match"].get("outcome")
        except Exception:
            continue
        me = "teamA" if s == "A" else "teamB"
        sc[kind][0] += 1.0 if oc == me else 0.5 if oc not in ("teamA", "teamB") else 0.0
        sc[kind][1] += 1
    w = sum(v[0] for v in sc.values()); n = sum(v[1] for v in sc.values())
    pct = lambda v: f"{v[0]:.1f}/{v[1]} = {100 * v[0] / max(1, v[1]):.1f}%"
    print(f"{time.strftime('%H:%M:%S')} {cand} vs {OPP}: ladder {pct(sc['ladder'])}, unseen {pct(sc['unseen'])}, "
          f"total {pct([w, n])} ({time.time() - t0:.0f} s){' PARTIAL' if killed else ''}", flush=True)
