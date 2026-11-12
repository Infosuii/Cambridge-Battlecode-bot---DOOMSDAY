"""E124: record the blend's states (A2_NN_ENSLOG build, fuel 20M): official maps 65%, generated otherwise, vs v92 and its noisy copies.
Writes OUT.npz: X int16 [N, 500], v92g (v92's group), ng (network's top group), meta [round, slot], game index, official flag per game, keys per game.
usage (project root): python -P agent2/lab/nn_ens_rec.py BOT OUT.npz [GAMES] [--seed S]"""
import base64, os, random, shutil, subprocess, sys, time, zipfile
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
V4 = os.path.join(ROOT, "v4")
A = sys.argv[1:]
SEED = int(A[A.index("--seed") + 1]) if "--seed" in A else 1
A = [a for i, a in enumerate(A) if not a.startswith("--") and (i == 0 or not A[i - 1].startswith("--"))]
BOT, OUT = A[0], A[1]
GAMES = int(A[2]) if len(A) > 2 else 800
NF = int(os.environ.get("NN_NF", "500"))


def free_gb():
    out = subprocess.run(["powershell", "-NoProfile", "-c", "(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB"], capture_output=True, text=True).stdout
    try:
        return float(out.strip().splitlines()[-1])
    except Exception:
        return 99.0


def maplist(s):
    return sorted(f for f in os.listdir(os.path.join(V4, s)) if f.endswith(".map26a"))


SETS = [("maps", 0.65), ("maps_real250", 0.1), ("maps_pooltrain", 0.25)]
M = {s: maplist(s) for s, _ in SETS}
rng = random.Random(SEED)
games = []
for _ in range(GAMES):
    s = rng.choices([x for x, _ in SETS], [w for _, w in SETS])[0]
    games.append((s, rng.choice(M[s]), rng.choice(["v92", "v92j1", "v92j2"]), rng.choice("AB")))
tag = os.path.join("bench_out", "ensrec")
shutil.rmtree(os.path.join(V4, tag), ignore_errors=True)
os.makedirs(os.path.join(V4, tag))
lines = []
for k, (s, m, o, side) in enumerate(games):
    a, b = (BOT, o) if side == "A" else (o, BOT)
    f = f"{tag}/g{k}".replace("\\", "/")
    lines.append(f"bots/{a} bots/{b} {s}/{m} {f}.repl26a --statistics {f}.json --json")
man = os.path.join(V4, ".m_ensrec.txt")
X, V, N, META, G, KEYS, OFF = [], [], [], [], [], [], []
t0 = time.time()
# in batches, so the disk holds few bundles at a time
for b0 in range(0, GAMES, 100):
    open(man, "w").write("\n".join(lines[b0:b0 + 100]) + "\n")
    while free_gb() < 3.0:
        time.sleep(30)
    p = subprocess.Popen([os.path.join(V4, "cambc.exe"), "run-batch", man, "--jobs", "8", "--json", "--color", "never", "--release", "--fuel-quantum", "20000000", "--log-limit", "67108864"],
                         cwd=V4, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    while p.poll() is None:
        time.sleep(3)
        if free_gb() < 2.0:
            p.kill()
            print("KILLED by watchdog", flush=True)
    for k in range(b0, min(b0 + 100, GAMES)):
        s, m, o, side = games[k]
        path = os.path.join(V4, tag, f"g{k}.repl26a")
        try:
            txt = zipfile.ZipFile(path).read(f"team-{side.lower()}.stdout").replace(b"\0", b"").decode("utf-8", "replace")
        except Exception:
            continue
        gi = len(KEYS)
        KEYS.append(f"{s}/{m[:-7]}"), OFF.append(s == "maps")
        for l in txt.splitlines():
            if not l.startswith("NRE "):
                continue
            q = l.split()
            if len(q) != 7:
                continue
            try:
                x = np.frombuffer(base64.b64decode(q[6]), np.int16)
            except Exception:
                continue
            if len(x) != NF:
                continue
            X.append(x), V.append(int(q[3])), N.append(int(q[4])), META.append((int(q[1]), int(q[2]))), G.append(gi)
    shutil.rmtree(os.path.join(V4, tag), ignore_errors=True)
    os.makedirs(os.path.join(V4, tag))
    print(f"{min(b0 + 100, GAMES)}/{GAMES} games, {len(X)} rows, {time.time() - t0:.0f}s", flush=True)
np.savez(OUT, X=np.stack(X), v92g=np.array(V, np.int32), ng=np.array(N, np.int32), meta=np.array(META, np.int32), game=np.array(G, np.int32), keys=np.array(KEYS), off=np.array(OFF))
print("saved", OUT, len(X), "rows", flush=True)
