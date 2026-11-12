"""Neural bot stage 2: reinforcement learning (PPO) of the teacher's target head in the real engine (fuel ignored).
Per iteration: export the teacher -> build v4/bots/nnrl (v92 + A2_NN target + bank, A2_NN_RL sampling at TEMP) -> play
GAMES games against the opponent league on training maps (both sides, 8 at a time) -> parse the NRL rows, which the bot
writes only on turns its target choice is applied (farm(); fighting / banking turns are not decisions) -> PPO update
on the GPU.
Return per decision (round t, horizon H): (own value at t+H - own value at t) / OWN_SCALE + TEAM_W x (team banked lead
change) / LEAD_SCALE + Z_W x final result; own value = gems this champion banked so far + gems it carries. Trained on
every target change and a KEEP_FRAC sample of keep turns, the latter weighted 1 / KEEP_FRAC (no selection bias).
Loss: clipped PPO on the target head + value net (advantage = return - V(s)) + KL to the frozen imitation teacher on
the target head (BETA_KL) and on the behaviour head (BETA_BEH: banking runs on it and shares the trunk) - entropy bonus.
Every EVAL_EVERY iterations the deterministic network (argmax) plays v92 on the held-out ladder maps (70 x 2) and
pool-test maps (0-149 x 2); the best checkpoint by total is kept (best.pt).
With --gae: GAE(lambda) per champion decision sequence (GAMMA / LAMBDA per round), value target = advantage + V.
usage (project root): python -P agent2/lab/nn_rl.py WORKDIR INIT_TEACHER.pt ITERS [--games 800] [--eval-every 2] [--gae]
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
GAMES, OPPS = arg("--games", 800), arg("--opps", "v92,x1,x3ctr").split(",")
SETS = arg("--sets", "maps,maps_real250,maps_pooltrain").split(",")
EVAL_EVERY = arg("--eval-every", 2)
TEMP, CLIP, BETA_KL, BETA_BEH, ENT, LR, EPOCHS = 0.4, 0.2, 0.02, 1.0, 0.003, 2e-4, 4
HORIZON, OWN_SCALE, TEAM_W, LEAD_SCALE, Z_W, KEEP_FRAC = 100, 30.0, 0.5, 60.0, 0.3, 0.1
FUEL = "20000000"  # the teacher needs ~2M fuel a turn (fuel ignored, both sides)
GAE = "--gae" in A  # GAE(lambda) over each champion's decision sequence instead of the fixed-horizon return
GAMMA, LAMBDA = 0.995, 0.98  # per round (decisions are irregularly spaced)
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


def build(name, wh, rl):
    """Build v4/bots/NAME with weights header WH (incremental when it exists: only nn_weights.h changes)."""
    if os.path.exists(os.path.join(V4, "bots", name, ".cambc", "build-release", "bot.wasm")):
        shutil.copyfile(wh, os.path.join(V4, "bots", name, "src", "nn_weights.h"))
        r = subprocess.run([os.path.join(V4, "cambc.exe"), "build", f"bots/{name}", "--release"], cwd=V4, capture_output=True, text=True)
        ok = r.returncode == 0
    else:
        extra = ["A2_NN_RL=1", "A2_NN_RL_T=" + str(TEMP)] if rl else []
        r = subprocess.run([sys.executable, "-P", os.path.join(LAB, "nn_mkbot.py"), name, wh, "A2_NN=3", *extra], capture_output=True, text=True)
        ok = "built" in r.stdout and "FAILED" not in r.stdout
    if not ok:
        log(f"BUILD FAILED {name} " + (r.stdout + r.stderr)[-2000:]); sys.exit(2)


def play(lines, tag):
    """Run a manifest (8 at a time, RAM watchdog)."""
    man = os.path.join(V4, f".m_{os.path.basename(tag)}.txt")
    open(man, "w").write("\n".join(lines) + "\n")
    while free_gb() < 3.0:
        time.sleep(30)
    p = subprocess.Popen([os.path.join(V4, "cambc.exe"), "run-batch", man, "--jobs", "8", "--json", "--color", "never", "--release",
                          "--fuel-quantum", FUEL, "--log-limit", "67108864"], cwd=V4, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    while p.poll() is None:
        time.sleep(3)
        if free_gb() < 2.0:
            p.kill(); log("KILLED by watchdog")


def result(jf, side):
    d = json.load(open(jf))
    oc = d["match"].get("outcome")
    gems = {t["team"]: int(t["submittedGems"]) for t in d.get("teams", [])}
    me, them = ("teamA", "teamB") if side == "A" else ("teamB", "teamA")
    return (1.0 if oc == me else -1.0 if oc == them else 0.0), gems.get(me, 0), gems.get(them, 0)


EVAL_MAPS = [("maps", f) for f in sorted(os.listdir(os.path.join(V4, "maps"))) if f.endswith(".map26a")][:70] + \
            [("maps_pooltest", f) for f in sorted(os.listdir(os.path.join(V4, "maps_pooltest"))) if f.endswith(".map26a")][:150]


def evaluate(it, wh):
    build("nnrl_eval", wh, rl=False)
    tag = os.path.join("bench_out", "nnrl", f"eval{it}")
    shutil.rmtree(os.path.join(V4, tag), ignore_errors=True)
    os.makedirs(os.path.join(V4, tag))
    jobs, lines = [], []
    for s, m in EVAL_MAPS:
        for side in "AB":
            a, b = ("nnrl_eval", "v92") if side == "A" else ("v92", "nnrl_eval")
            f = f"{tag}/{s}_{m[:-7]}_{side}".replace("\\", "/")
            lines.append(f"bots/{a} bots/{b} {s}/{m} {f}.repl26a --statistics {f}.json --json")
            jobs.append((s, os.path.join(V4, f + ".json"), side))
    play(lines, tag)
    w = {"maps": [0.0, 0], "maps_pooltest": [0.0, 0]}
    for s, jf, side in jobs:
        try:
            z, _, _ = result(jf, side)
        except Exception:
            continue
        w[s][0] += 1.0 if z > 0 else 0.5 if z == 0 else 0.0
        w[s][1] += 1
    shutil.rmtree(os.path.join(V4, tag), ignore_errors=True)
    tot = (w["maps"][0] + w["maps_pooltest"][0]) / max(1, w["maps"][1] + w["maps_pooltest"][1])
    log(f"{time.strftime('%H:%M:%S')} EVAL iter {it} vs v92 (deterministic): ladder {w['maps'][0]:.0f}/{w['maps'][1]}, "
        f"pool-test {w['maps_pooltest'][0]:.0f}/{w['maps_pooltest'][1]}, total {100 * tot:.1f}%")
    return tot


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
it0, best = 0, arg("--baseline", 0.5)  # DAgger-3 teacher, same eval: ladder 58/140 + pool-test 162/300
if os.path.exists(state_f):
    st = json.load(open(state_f))
    it0, best = st["iter"], st.get("best", -1.0)
    net.load_state_dict(torch.load(os.path.join(WD, f"teacher_{it0}.pt"), map_location=dev))
    value.load_state_dict(torch.load(os.path.join(WD, f"value_{it0}.pt"), map_location=dev))
maps = [(s, f) for s in SETS for f in sorted(os.listdir(os.path.join(V4, s))) if f.endswith(".map26a")]
evset = {m for m in EVAL_MAPS if m[0] == "maps_pooltest"}
maps = [m for m in maps if m not in evset]  # pool-test maps never appear in rollouts (ladder maps are the deployment set)



def gae_game(rows, lead, final_lead, z, Vg):
    """GAE over each champion's decisions in one game. rows: (round, slot, own value) in log order; lead: team banked
    lead at each row; Vg: V(s) per row. Reward between a champion's consecutive decisions = own value change / OWN_SCALE
    + TEAM_W x lead change / LEAD_SCALE; after its last decision = TEAM_W x (final lead - lead) / LEAD_SCALE + Z_W x
    result. Returns (advantages, value targets)."""
    gadv, gret = np.zeros(len(rows)), np.zeros(len(rows))
    by_slot = {}
    for i, r in enumerate(rows):
        by_slot.setdefault(r[1], []).append(i)
    for idxs in by_slot.values():
        acc = 0.0
        for pos in range(len(idxs) - 1, -1, -1):
            i = idxs[pos]
            if pos == len(idxs) - 1:
                acc = TEAM_W * (final_lead - lead[i]) / LEAD_SCALE + Z_W * z - Vg[i]
            else:
                j = idxs[pos + 1]
                dt = max(1, rows[j][0] - rows[i][0])
                rew = (rows[j][2] - rows[i][2]) / OWN_SCALE + TEAM_W * (lead[j] - lead[i]) / LEAD_SCALE
                acc = rew + GAMMA ** dt * Vg[j] - Vg[i] + (GAMMA * LAMBDA) ** dt * acc
            gadv[i], gret[i] = acc, acc + Vg[i]
    return gadv, gret

def vfeat(X):
    x = X.float()
    return torch.sign(x) * torch.log1p(x.abs())


def export(tag):
    pt = os.path.join(WD, f"teacher_{tag}.pt")
    torch.save(net.state_dict(), pt)
    wh = os.path.join(WD, "teacher_w.h")
    subprocess.run([sys.executable, "-P", os.path.join(LAB, "nn_export.py"), pt, "teacher", wh], check=True, capture_output=True)
    return wh


for it in range(it0 + 1, it0 + ITERS + 1):
    t0 = time.time()
    wh = export("cur")
    build("nnrl", wh, rl=True)
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
    play(lines, tag)
    Xs, As, Ls, Gs, Ws, Zs, ADVs = [], [], [], [], [], [], []
    res = {o: [0, 0] for o in OPPS}
    nchg = nkeep = 0
    for k, ((s, m), o, side) in enumerate(games):
        try:
            z, gm, gt = result(os.path.join(V4, tag, f"g{k}.json"), side)
            txt = zipfile.ZipFile(os.path.join(V4, tag, f"g{k}.repl26a")).read(f"team-{side.lower()}.stdout").replace(b"\0", b"").decode("utf-8", "replace")
        except Exception as e:
            if k < 3:
                log(f"game {k} unreadable: {e!r}")
            continue
        res[o][0] += z > 0; res[o][1] += 1
        rows = []
        for l in txt.splitlines():
            if not l.startswith("NRL "):
                continue
            q = l.split()
            if len(q) != 8:
                continue
            try:
                x = np.frombuffer(base64.b64decode(q[7]), np.int16)
            except Exception:
                continue
            if len(x) != NF:
                continue
            rows.append((int(q[1]), int(q[2]), int(q[3]), float(q[4]), int(q[5]), int(q[6]), x))
        if not rows:
            continue
        # team banked lead over time (all rows: features 1 / 2 = ally / enemy banked score); own value per champion slot
        rnd = np.array([r[0] for r in rows])
        lead = np.array([int(r[6][1]) - int(r[6][2]) for r in rows])
        order = np.argsort(rnd, kind="stable")
        rs_all, lead_all = rnd[order], lead[order]
        own = {}
        for r0, sl, _, _, _, val, _ in rows:
            own.setdefault(sl, []).append((r0, val))
        own = {sl: (np.array([a for a, _ in v]), np.array([b for _, b in v])) for sl, v in own.items()}
        final_lead = gm - gt
        if GAE:
            # reward between a champion's consecutive decisions: own value change + team banked-lead change; at its
            # last decision: the lead change to the end + the result. delta = r + g V(s') - V(s); A = sum (g l)^k delta
            with torch.no_grad():
                Vg = value(vfeat(torch.as_tensor(np.stack([r[6] for r in rows])).to(dev))).squeeze(1).cpu().numpy()
            gadv, gret = gae_game([(r[0], r[1], r[5]) for r in rows], lead, final_lead, z, Vg)
        for ri, ((r0, sl, a, lp, ch, val, x), ld) in enumerate(zip(rows, lead)):
            if not ch and rng.random() > KEEP_FRAC:
                continue
            if GAE:
                Xs.append(x); As.append(a); Ls.append(lp); Zs.append(z); Gs.append(gret[ri]); ADVs.append(gadv[ri])
                Ws.append(1.0 if ch else 1.0 / KEEP_FRAC)
                nchg += ch; nkeep += not ch
                continue
            j = np.searchsorted(rs_all, r0 + HORIZON)
            later_lead = lead_all[j] if j < len(rs_all) else final_lead
            orr, ov = own[sl]
            jj = np.searchsorted(orr, r0 + HORIZON)
            later_own = ov[jj] if jj < len(orr) else ov[-1]
            Xs.append(x); As.append(a); Ls.append(lp); Zs.append(z)
            Gs.append((later_own - val) / OWN_SCALE + TEAM_W * (later_lead - ld) / LEAD_SCALE + Z_W * z)
            Ws.append(1.0 if ch else 1.0 / KEEP_FRAC)
            nchg += ch; nkeep += not ch
    shutil.rmtree(os.path.join(V4, tag), ignore_errors=True)
    if not Xs:
        log(f"iter {it}: no samples"); continue
    X = torch.as_tensor(np.stack(Xs)).to(dev)
    Aa = torch.as_tensor(As).to(dev)
    L0 = torch.as_tensor(Ls).to(dev)
    G = torch.as_tensor(Gs, dtype=torch.float32).to(dev)
    Wt = torch.as_tensor(Ws, dtype=torch.float32).to(dev)
    ADV = torch.as_tensor(ADVs, dtype=torch.float32).to(dev) if GAE else None
    n = len(X)
    with torch.no_grad():  # critic quality before the update: explained variance of the return
        v0 = torch.cat([value(vfeat(X[s:s + 8192])).squeeze(1) for s in range(0, n, 8192)])
        ev = 1.0 - ((G - v0).var() / G.var().clamp_min(1e-6)).item()
    zc = float(np.corrcoef(np.array(Gs), np.array(Zs))[0, 1]) if np.std(Zs) > 0 else 0.0
    stats = []
    for ep in range(EPOCHS):
        perm = torch.randperm(n, device=dev)
        for s0 in range(0, n, 4096):
            idx = perm[s0:s0 + 4096]
            xb, wb = X[idx], Wt[idx] / Wt[idx].mean()
            out = net(xb)
            lp = F.log_softmax(out["target"] / TEMP, -1)
            lpa = lp.gather(1, Aa[idx, None]).squeeze(1)
            v = value(vfeat(xb)).squeeze(1)
            adv = ADV[idx] if GAE else (G[idx] - v).detach()
            adv = (adv - adv.mean()) / (adv.std() + 1e-6)
            ratio = torch.exp(lpa - L0[idx])
            pg = -(wb * torch.min(ratio * adv, ratio.clamp(1 - CLIP, 1 + CLIP) * adv)).mean()
            with torch.no_grad():
                rout = ref(xb)
                rlp = F.log_softmax(rout["target"] / TEMP, -1)
                rbe = F.log_softmax(rout["behaviour"], -1)
            pr = lp.exp()
            kl = (pr * (lp - rlp)).sum(-1).mean()
            be = F.log_softmax(out["behaviour"], -1)
            klb = (be.exp() * (be - rbe)).sum(-1).mean()
            ent = -(pr * lp).sum(-1).mean()
            vl = (wb * (v - G[idx]) ** 2).mean()
            loss = pg + BETA_KL * kl + BETA_BEH * klb - ENT * ent + 0.5 * vl
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(list(net.parameters()) + list(value.parameters()), 1.0)
            opt.step()
            stats.append((pg.item(), kl.item(), klb.item(), ent.item(), vl.item(), ratio.mean().item()))
    st_ = np.mean(stats, 0)
    torch.save(net.state_dict(), os.path.join(WD, f"teacher_{it}.pt"))
    torch.save(value.state_dict(), os.path.join(WD, f"value_{it}.pt"))
    wr = ", ".join(f"{o} {a}/{b}" for o, (a, b) in res.items())
    log(f"{time.strftime('%H:%M:%S')} iter {it}: rollouts won {wr} | decisions {nchg} changes + {nkeep} keeps, return "
        f"{G.mean().item():+.3f}+-{G.std().item():.3f}, corr(return, result) {zc:+.2f}, critic EV {ev:+.3f} | pg {st_[0]:+.4f} "
        f"kl {st_[1]:.4f} klbeh {st_[2]:.4f} ent {st_[3]:.3f} vloss {st_[4]:.3f} ratio {st_[5]:.3f} | {time.time() - t0:.0f}s")
    if it % EVAL_EVERY == 0:
        wh = export(f"{it}")
        sc = evaluate(it, wh)
        if sc > best:
            best = sc
            shutil.copyfile(os.path.join(WD, f"teacher_{it}.pt"), os.path.join(WD, "best.pt"))
            log(f"  new best: iter {it} ({100 * sc:.1f}%)")
    json.dump({"iter": it, "best": best}, open(state_f, "w"))
