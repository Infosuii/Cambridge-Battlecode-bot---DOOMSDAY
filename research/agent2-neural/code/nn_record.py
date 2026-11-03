"""Neural bot step 1: imitation data from the recorder (v4/bots/nnrec, agent2/lab/nn_mkrec.py), real engine, fuel ignored.
nnrec (v92 + recorder) plays each opponent on each map of the given sets, both sides. Per game, the nnrec team's stdout
(kept in the replay bundle) is parsed into OUT/<set>__<map>__<opp>_<side>.npz:
    X int16 [N, 500] features; meta int32 [N, 7] (round, slot, fight, mode id, target_group, heading_home, win);
    acts: array of action strings; camps: "handle:group" map per slot; modes: the mode-name vocabulary
and the replay itself (for the privileged critic) to OUT/replays/. Bundles are deleted after parsing. RAM watchdog
(kills the batch under 2 GB free); finished games are skipped on a rerun.
usage (project root): python -P agent2/lab/nn_record.py OUT [--sets maps,maps_real250] [--opps v92,x1,x3ctr,v81,b5_c3]
                      [--every K: every K-th map] [--bot nnrec]
"""
import base64, io, json, os, shutil, subprocess, sys, time, zipfile
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
V4 = os.path.join(ROOT, "v4")
A = sys.argv[1:]
OUT = os.path.abspath(A[0])
arg = lambda k, d: A[A.index(k) + 1] if k in A else d
SETS = arg("--sets", "maps,maps_real250,maps_test4,maps_new4,maps_maze").split(",")
OPPS = arg("--opps", "v92,x1,x3ctr,v81,b5_c3").split(",")
EVERY = int(arg("--every", "1"))
BOT = arg("--bot", "nnrec")  # recorder build (nn2dag etc. for DAgger)
NF = 500
os.makedirs(os.path.join(OUT, "replays"), exist_ok=True)
MODES_F = os.path.join(OUT, "modes.json")
modes = json.load(open(MODES_F)) if os.path.exists(MODES_F) else {}


def free_gb():
    out = subprocess.run(["powershell", "-NoProfile", "-c", "(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB"],
                         capture_output=True, text=True).stdout
    try:
        return float(out.strip().splitlines()[-1])
    except Exception:
        return 99.0


def parse(bundle, team, win):
    z = zipfile.ZipFile(bundle)
    txt = z.read(f"team-{team}.stdout").replace(b"\0", b"").decode("utf-8", "replace")
    X, M, acts, camps = [], [], [], {}
    for l in txt.splitlines():
        if l.startswith("NRC "):
            p = l.split(" ")
            camps[p[1]] = " ".join(p[2:])
            continue
        if not l.startswith("NR "):
            continue
        head, _, act = l.partition(" | ")
        p = head.split(" ")
        if len(p) < 8:
            continue
        try:
            f = np.frombuffer(base64.b64decode(p[4]), np.int16)
        except Exception:
            continue
        if len(f) != NF:
            continue
        mid = modes.setdefault(p[5], len(modes))
        X.append(f); M.append([int(p[1]), int(p[2]), int(p[3]), mid, int(p[6]), int(p[7]), win]); acts.append(act)
    return X, M, acts, camps, z.read("replay.repl26a")


jobs = []
for s in SETS:
    maps = sorted(f for f in os.listdir(os.path.join(V4, s)) if f.endswith(".map26a"))[::EVERY]
    for m in maps:
        for o in OPPS:
            for side in "AB":
                name = f"{s}__{m[:-7]}__{o}_{side}"
                if not os.path.exists(os.path.join(OUT, name + ".npz")):
                    jobs.append((s, m, o, side, name))
print(f"{len(jobs)} games to record", flush=True)
CH = 200
for c0 in range(0, len(jobs), CH):
    chunk = jobs[c0:c0 + CH]
    tag = os.path.join("bench_out", "nnrec_run", f"c{c0}")
    shutil.rmtree(os.path.join(V4, tag), ignore_errors=True)
    os.makedirs(os.path.join(V4, tag))
    lines = []
    for s, m, o, side, name in chunk:
        a, b = (BOT, o) if side == "A" else (o, BOT)
        f = f"{tag}/{name}".replace("\\", "/")
        lines.append(f"bots/{a} bots/{b} {s}/{m} {f}.repl26a --statistics {f}.json --json")
    man = os.path.join(V4, ".m_nnrec_run.txt")
    open(man, "w").write("\n".join(lines) + "\n")
    while free_gb() < 3.0:
        print("free RAM under 3 GB, waiting", flush=True); time.sleep(60)
    t0 = time.time()
    p = subprocess.Popen([os.path.join(V4, "cambc.exe"), "run-batch", man, "--jobs", "8", "--json", "--color", "never", "--release",
                          "--fuel-quantum", "1000000", "--log-limit", "67108864"], cwd=V4, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    killed = False
    while p.poll() is None:
        time.sleep(3)
        if free_gb() < 2.0:
            p.kill(); killed = True
            print("KILLED by watchdog", flush=True)
    rows = wins = done = 0
    for s, m, o, side, name in chunk:
        bundle = os.path.join(V4, tag, name + ".repl26a")
        try:
            d = json.load(open(os.path.join(V4, tag, name + ".json")))
            oc = d["match"].get("outcome")
            win = 1 if oc == f"team{side}" else 0 if oc in ("teamA", "teamB") else -1
            X, M, acts, camps, rep = parse(bundle, side.lower(), win)
        except Exception as e:
            print("parse failed", name, e, flush=True)
            continue
        if not X:
            continue
        np.savez_compressed(os.path.join(OUT, name + ".npz"), X=np.stack(X), meta=np.array(M, np.int32), acts=np.array(acts),
                            camps=json.dumps(camps))
        open(os.path.join(OUT, "replays", name + ".repl26a"), "wb").write(rep)
        rows += len(X); wins += win == 1; done += 1
    json.dump(modes, open(MODES_F, "w"))
    shutil.rmtree(os.path.join(V4, tag), ignore_errors=True)
    print(f"{time.strftime('%H:%M:%S')} chunk {c0 // CH + 1}/{(len(jobs) + CH - 1) // CH}: {done} games, {rows} rows, "
          f"nnrec won {wins}, {time.time() - t0:.0f} s{' PARTIAL' if killed else ''}", flush=True)
print("done")
