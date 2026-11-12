"""E123: compare two A2_NN_DBG builds of the same network on the same games (BOT1, BOT2 vs OPP, real engine, fuel 20M): per (round, slot) do the features and logits match, and where do the games part?
usage (project root): python -P agent2/lab/nnd_compare.py BOT1 BOT2 OPP MAPDIR:A:B"""
import base64, collections, json, os, shutil, subprocess, sys, zipfile
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
V4 = os.path.join(ROOT, "v4")
B1, B2, OPP, SPEC = sys.argv[1:5]
d, a, b = SPEC.split(":")
maps = sorted(f for f in os.listdir(os.path.join(V4, d)) if f.endswith(".map26a"))[int(a):int(b)]
tag = "bench_out/nndc"
shutil.rmtree(os.path.join(V4, tag), ignore_errors=True)
os.makedirs(os.path.join(V4, tag))
lines = []
for bot in (B1, B2):
    for m in maps:
        f = f"{tag}/{bot}_{m[:-7]}"
        lines.append(f"bots/{bot} bots/{OPP} {d}/{m} {f}.repl26a --statistics {f}.json --json")
man = os.path.join(V4, ".m_nndc.txt")
open(man, "w").write("\n".join(lines) + "\n")
subprocess.run([os.path.join(V4, "cambc.exe"), "run-batch", man, "--jobs", "6", "--json", "--color", "never", "--release", "--fuel-quantum", "20000000", "--log-limit", "67108864"],
               cwd=V4, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def rows(bot, m):
    txt = zipfile.ZipFile(os.path.join(V4, tag, f"{bot}_{m[:-7]}.repl26a")).read("team-a.stdout").replace(b"\0", b"").decode("utf-8", "replace")
    out = {}
    for l in txt.splitlines():
        if l.startswith("NND "):
            q = l.split()
            out[(int(q[1]), int(q[2]))] = (int(q[3]), int(q[4]), np.frombuffer(base64.b64decode(q[5]), np.int16), np.array([float(v) for v in q[6:]]))
    return out


NAMES = {}
for i in range(16): NAMES[i] = f"g{i}"
for i in range(44): NAMES[16 + i] = f"s{i}"
for e in range(5):
    for i in range(12): NAMES[60 + e * 12 + i] = f"a{e}.{i}"
for e in range(8):
    for i in range(16): NAMES[120 + e * 16 + i] = f"e{e}.{i}"
for e in range(10):
    for i in range(22): NAMES[248 + e * 22 + i] = f"c{e}.{i}"
for e in range(4):
    for i in range(8): NAMES[468 + e * 8 + i] = f"l{e}.{i}"
tot_fields = collections.Counter()
for m in maps:
    r1, r2 = rows(B1, m), rows(B2, m)
    res = []
    for bot in (B1, B2):
        st = json.load(open(os.path.join(V4, tag, f"{bot}_{m[:-7]}.json")))
        res.append(f"{bot} {st['match']['outcome']} r{st['match']['roundsCompleted']}")
    keys = sorted(set(r1) & set(r2))
    only = len(set(r1) ^ set(r2))
    first_feat = first_logit = first_dec = None
    ndiff = 0
    for k in keys:
        a1, a2 = r1[k], r2[k]
        same_f = np.array_equal(a1[2], a2[2])
        if not same_f:
            ndiff += 1
            if first_feat is None:
                first_feat = k
                idx = np.where(a1[2] != a2[2])[0]
                first_list = [(NAMES.get(int(i), str(i)), int(a1[2][i]), int(a2[2][i])) for i in idx[:12]]
            if first_dec is None:
                for i in np.where(a1[2] != a2[2])[0]:
                    tot_fields[NAMES.get(int(i), str(i)).split(".")[-1] if "." in NAMES.get(int(i), str(i)) else NAMES.get(int(i), str(i))] += 1
        if first_logit is None and same_f and np.abs(a1[3] - a2[3]).max() > 0.01:
            first_logit = (k, float(np.abs(a1[3] - a2[3]).max()))
        if first_dec is None and (a1[0] != a2[0] or a1[1] != a2[1]):
            first_dec = (k, a1[0], a2[0], a1[1], a2[1])
    print(f"{m[:-7]}: {res}; rows {len(keys)} common, {only} one-sided; rows with other features {ndiff}; first features differ {first_feat}; logits differ on same features {first_logit}; first decision differs {first_dec}")
    if first_feat is not None:
        print("   first differing fields (name, bot1, bot2):", first_list)
print("fields differing before the first decision differs:", tot_fields.most_common(20))
shutil.rmtree(os.path.join(V4, tag), ignore_errors=True)
