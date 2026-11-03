"""Neural bot stage 2: reinforcement learning (PPO) of the teacher's target head in the real engine (fuel ignored).
Per iteration: export the teacher -> build v4/bots/nnrl (v92 + A2_NN target + bank, A2_NN_RL sampling / logging) ->
play GAMES games against the opponent league on training maps (both sides, 8 at a time) -> parse the NRL rows (state,
sampled target, log-prob) and each game's result -> PPO update on the GPU: clipped ratio on the target head, a value
net as the baseline (advantage = return - V(s)), a KL penalty to the frozen imitation teacher, entropy bonus.
Return per game: +1 win / -1 loss / 0 draw, + SHAPE x (our banked - their banked) / (sum + 50).
usage (project root): python -P agent2/lab/nn_rl.py WORKDIR INIT_TEACHER.pt ITERS [--games 400] [--opps v92,x1,x3ctr]
"""
import base64, json, os, random, shutil, subprocess, sys, time, zipfile
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nn_model import Prep, teacher  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
V4, LAB = os.path.join(ROOT, "v4"), os.path.join(ROOT, "agent2", "lab")
A = sys.argv[1:]
WD, INIT, ITERS = os.path.abspath(A[0]), A[1], int(A[2])
arg = lambda k, d: type(d)(A[A.index(k) + 1]) if k in A else d
GAMES, OPPS = arg("--games", 400), arg("--opps", "v92,x1,x3ctr").split(",")
SETS = arg("--sets", "maps,maps_real250,maps_pooltrain").split(",")
TEMP, CLIP, BETA_KL, ENT, SHAPE, LR, EPOCHS = 0.4, 0.2, 0.05, 0.003, 0.3, 3e-5, 3
NF = 500
dev = "cuda"
os.makedirs(WD, exist_ok=True)
LOG = os.path.join(WD, "rl.log")


def log(s):
    print(s, flush=True)
    open(LOG, "a").write(s + "\n")


def free_gb():
    out = subprocess.run(["powershell", "-NoProfile", "-c", "(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB"],
                         capture_output=True, text=True).stdout
    try:
        return float(out.strip().splitlines()[-1])
    except Exception:
        return 99.0


net = teacher(Prep())
net.load_state_dict(torch.load(INIT, map_location="cpu"))
ref = teacher(Prep())
ref.load_state_dict(torch.load(INIT, map_location="cpu"))
net.to(dev); ref.to(dev).eval()
for p in ref.parameters():
    p.requires_grad_(False)
value = nn.Sequential(nn.Linear(NF, 256), nn.ReLU(), nn.Linear(256, 256), nn.ReLU(), nn.Linear(256, 1)).to(dev)
opt = torch.optim.Adam(list(net.parameters()) + list(value.parameters()), lr=LR)
state_f = os.path.join(WD, "state.json")
it0 = 0
if os.path.exists(state_f):
    st = json.load(open(state_f))
    it0 = st["iter"]
    net.load_state_dict(torch.load(os.path.join(WD, f"teacher_{it0}.pt"), map_location=dev))
    value.load_state_dict(torch.load(os.path.join(WD, f"value_{it0}.pt"), map_location=dev))
maps = [(s, f) for s in SETS for f in sorted(os.listdir(os.path.join(V4, s))) if f.endswith(".map26a")]


def vfeat(X):
    x = X.float()
    return torch.sign(x) * torch.log1p(x.abs())


for it in range(it0 + 1, it0 + ITERS + 1):
    t0 = time.time()
    pt = os.path.join(WD, f"teacher_cur.pt")
    torch.save(net.state_dict(), pt)
    wh = os.path.join(WD, "teacher_w.h")
    subprocess.run([sys.executable, "-P", os.path.join(LAB, "nn_export.py"), pt, "teacher", wh], check=True, capture_output=True)
    if os.path.exists(os.path.join(V4, "bots", "nnrl", ".cambc", "build-release", "bot.wasm")):
        # incremental: only the weights header changes (nnrec.cpp recompiles, nothing else)
        shutil.copyfile(wh, os.path.join(V4, "bots", "nnrl", "src", "nn_weights.h"))
        r = subprocess.run([os.path.join(V4, "cambc.exe"), "build", "bots/nnrl", "--release"], cwd=V4, capture_output=True, text=True)
        ok = r.returncode == 0
    else:
        r = subprocess.run([sys.executable, "-P", os.path.join(LAB, "nn_mkbot.py"), "nnrl", wh, "A2_NN=3", "A2_NN_RL=3", "A2_NN_RL_T=" + str(TEMP)],
                           capture_output=True, text=True)
        ok = "built" in r.stdout and "FAILED" not in r.stdout
    if not ok:
        log("BUILD FAILED " + (r.stdout + r.stderr)[-2000:]); sys.exit(2)
    rng = random.Random(1000 + it)
    games = [(rng.choice(maps), rng.choice(OPPS), rng.choice("AB")) for _ in range(GAMES)]
    tag = os.path.join("bench_out", "nnrl", f"i{it}")
    shutil.rmtree(os.path.join(V4, tag), ignore_errors=True)
    os.makedirs(os.path.join(V4, tag))
    lines = []
    for k, ((s, m), o, side) in enumerate(games):
        a, b = ("nnrl", o) if side == "A" else (o, "nnrl")
        f = f"{tag}/g{k}".replace("\\", "/")
        lines.append(f"bots/{a} bots/{b} {s}/{m} {f}.repl26a --statistics {f}.json --json")
    man = os.path.join(V4, ".m_nnrl.txt")
    open(man, "w").write("\n".join(lines) + "\n")
    while free_gb() < 3.0:
        time.sleep(30)
    p = subprocess.Popen([os.path.join(V4, "cambc.exe"), "run-batch", man, "--jobs", "8", "--json", "--color", "never", "--release",
                          "--fuel-quantum", "20000000", "--log-limit", "67108864"],  # the teacher needs ~2M fuel a turn
                         cwd=V4, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    while p.poll() is None:
        time.sleep(3)
        if free_gb() < 2.0:
            p.kill(); log("KILLED by watchdog")
    Xs, As, Ls, Gs = [], [], [], []
    res = {o: [0, 0] for o in OPPS}
    for k, ((s, m), o, side) in enumerate(games):
        try:
            d = json.load(open(os.path.join(V4, tag, f"g{k}.json")))
            oc = d["match"].get("outcome")
            gems = {t["team"]: int(t["submittedGems"]) for t in d.get("teams", [])}
            me, them = ("teamA", "teamB") if side == "A" else ("teamB", "teamA")
            z = 1.0 if oc == me else -1.0 if oc == them else 0.0
            G = z + SHAPE * (gems.get(me, 0) - gems.get(them, 0)) / (gems.get(me, 0) + gems.get(them, 0) + 50)
            txt = zipfile.ZipFile(os.path.join(V4, tag, f"g{k}.repl26a")).read(f"team-{side.lower()}.stdout").replace(b"\0", b"").decode("utf-8", "replace")
        except Exception as e:
            if k < 3:
                log(f"game {k} unreadable: {e!r}")
            continue
        res[o][0] += z > 0; res[o][1] += 1
        for l in txt.splitlines():
            if not l.startswith("NRL "):
                continue
            q = l.split()
            try:
                x = np.frombuffer(base64.b64decode(q[5]), np.int16)
            except Exception:
                continue
            if len(x) != NF:
                continue
            Xs.append(x); As.append(int(q[3])); Ls.append(float(q[4])); Gs.append(G)
    shutil.rmtree(os.path.join(V4, tag), ignore_errors=True)
    if not Xs:
        log(f"iter {it}: no samples"); continue
    X = torch.as_tensor(np.stack(Xs)).to(dev)
    Aa = torch.as_tensor(As).to(dev)
    L0 = torch.as_tensor(Ls).to(dev)
    G = torch.as_tensor(Gs, dtype=torch.float32).to(dev)
    n = len(X)
    stats = []
    for ep in range(EPOCHS):
        perm = torch.randperm(n, device=dev)
        for s0 in range(0, n, 4096):
            idx = perm[s0:s0 + 4096]
            xb = X[idx]
            logits = net(xb)["target"] / TEMP
            lp = F.log_softmax(logits, -1)
            lpa = lp.gather(1, Aa[idx, None]).squeeze(1)
            v = value(vfeat(xb)).squeeze(1)
            adv = (G[idx] - v).detach()
            adv = (adv - adv.mean()) / (adv.std() + 1e-6)
            ratio = torch.exp(lpa - L0[idx])
            pg = -torch.min(ratio * adv, ratio.clamp(1 - CLIP, 1 + CLIP) * adv).mean()
            with torch.no_grad():
                rlp = F.log_softmax(ref(xb)["target"] / TEMP, -1)
            pr = lp.exp()
            kl = (pr * (lp - rlp)).sum(-1).mean()
            ent = -(pr * lp).sum(-1).mean()
            vl = F.mse_loss(v, G[idx])
            loss = pg + BETA_KL * kl - ENT * ent + 0.5 * vl
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(list(net.parameters()) + list(value.parameters()), 1.0)
            opt.step()
            stats.append((pg.item(), kl.item(), ent.item(), vl.item(), ratio.mean().item()))
    st_ = np.mean(stats, 0)
    torch.save(net.state_dict(), os.path.join(WD, f"teacher_{it}.pt"))
    torch.save(value.state_dict(), os.path.join(WD, f"value_{it}.pt"))
    json.dump({"iter": it}, open(state_f, "w"))
    wr = ", ".join(f"{o} {a}/{b}" for o, (a, b) in res.items())
    log(f"{time.strftime('%H:%M:%S')} iter {it}: rollouts won {wr} | samples {n}, mean return {G.mean().item():+.3f} | "
        f"pg {st_[0]:+.4f} kl {st_[1]:.4f} ent {st_[2]:.3f} vloss {st_[3]:.3f} ratio {st_[4]:.3f} | {time.time() - t0:.0f}s")
