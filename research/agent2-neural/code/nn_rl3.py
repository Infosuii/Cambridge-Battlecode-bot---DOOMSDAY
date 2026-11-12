"""Neural bot stage 3: RL (PPO + GAE) of the macro policy - the behaviour head (options held until done: farm / bank /
hunt / home / regroup / bank now out of contact via the RL-only option head; nnrec.cpp A2_NN_MACRO) and the target head - in the real
engine with fuel ignored. The bot (v92 + A2_NN 15 + A2_NN_MACRO) samples both heads at TEMP and prints one NRB row per
turn with a decision.
Reward between a champion's consecutive decisions, from the true per-round match timelines (statistics JSON): own
value change (gems it banked + carries) / OWN_SCALE + gold earned / GOLD_SCALE + KILL_W kills + ASSIST_W assists -
DEATH_W deaths + TEAM_W x team banked-lead change / LEAD_SCALE; after its last decision the same to the end + Z_W x
result. Critic: own view + the full game state (all champions' gems / banked / gold / kills / deaths; privileged). GAE(lambda) per champion (GAMMA / LAMBDA per
round); decisions before round EARLY_R weigh EARLY_W. Trained rows: every new non-farm option, every contact decision,
every target change, and a KEEP_FRAC sample of the rest (weighted 1 / KEEP_FRAC).
Loss: clipped PPO on each head present in the row, value net on GAE targets, KL to the frozen start network on both
heads, entropy bonus. League: v92, x1, x3ctr, p65pack (early grouping, E75), b5_c3, and a snapshot of our best network.
Maps: ladder half the time, real250 / pool-train otherwise (pool-test maps never). Held-out deterministic evaluation vs
v92 (ladder 70 x 2 + pool-test 0-149 x 2) at iteration 0 and every EVAL_EVERY iterations; best kept (best.pt).
usage (project root): python -P agent2/lab/nn_rl3.py WORKDIR INIT_TEACHER.pt ITERS [--games 800] [--eval-every 2]
"""
import base64, json, os, random, shutil, subprocess, sys, time, zipfile
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nn_model import Prep, load, teacher  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
V4, LAB = os.path.join(ROOT, "v4"), os.path.join(ROOT, "agent2", "lab")
A = sys.argv[1:]
WD, INIT, ITERS = os.path.abspath(A[0]), A[1], int(A[2])
arg = lambda k, d: type(d)(A[A.index(k) + 1]) if k in A else d
GAMES, EVAL_EVERY = arg("--games", 800), arg("--eval-every", 2)
LEAGUE = [("v92", 0.35), ("x1", 0.15), ("x3ctr", 0.15), ("p65pack", 0.15), ("b5_c3", 0.10), ("nnsnap", 0.10)]
MAPSETS = [("maps", 0.7), ("maps_real250", 0.1), ("maps_pooltrain", 0.2)]  # E118: v92 was tuned on the ladder maps; train mostly there
TEMP, CLIP, BETA_KL, ENT, LR, EPOCHS = 0.4, 0.2, 0.02, 0.003, 2e-4, 4
KEEP_OPT, FORCED = 0.05, [2, 3, 4, 6]  # (unused: the earlier keep-probability scheme, beh_logq)
OPT_T = 1.0  # option head sampling temperature (A2_NN_OPT_T)
OWN_SCALE, GOLD_SCALE, KILL_W, ASSIST_W, DEATH_W, TEAM_W, LEAD_SCALE, Z_W = 30.0, 100.0, 0.5, 0.25, 0.5, 0.5, 60.0, 0.3
GAMMA, LAMBDA, KEEP_FRAC, EARLY_R, EARLY_W = 0.995, 0.98, 0.1, 300, 1.5
FUEL = "20000000"  # the teacher needs ~2M fuel a turn (fuel ignored, both sides)
LAYOUT = os.environ.get("NN_LAYOUT", "2")  # acting network layout (2: 500 features, 3: 828)
BITS = "11"        # target + bank + options (the forced contact verdict lost 18 points, E117 ablation)
NF = 828 if LAYOUT == "3" else 500
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
    """v4/bots/NAME with weights WH (incremental when it exists: only nn_weights.h changes)."""
    if os.path.exists(os.path.join(V4, "bots", name, ".cambc", "build-release", "bot.wasm")):
        shutil.copyfile(wh, os.path.join(V4, "bots", name, "src", "nn_weights.h"))
        r = subprocess.run([os.path.join(V4, "cambc.exe"), "build", f"bots/{name}", "--release"], cwd=V4, capture_output=True, text=True)
        ok = r.returncode == 0
    else:
        extra = ["A2_NN_RL=1", "A2_NN_RL_T=" + str(TEMP), "A2_NN_OPT_T=" + str(OPT_T)] if rl else []
        r = subprocess.run([sys.executable, "-P", os.path.join(LAB, "nn_mkbot.py"), name, wh, "A2_NN=" + BITS, "A2_NN_MACRO=1",
                            "A2_NN_LAYOUT=" + LAYOUT, *extra],
                           capture_output=True, text=True)
        ok = "built" in r.stdout and "FAILED" not in r.stdout
    if not ok:
        log(f"BUILD FAILED {name} " + (r.stdout + r.stderr)[-2000:]); sys.exit(2)


def play(lines, tag):
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


def maplist(s):
    return sorted(f for f in os.listdir(os.path.join(V4, s)) if f.endswith(".map26a"))


EVAL_MAPS = [("maps", f) for f in maplist("maps")][:70] + [("maps_pooltest", f) for f in maplist("maps_pooltest")][:150]
MAPSETS = [(s, w) for s, w in MAPSETS if os.path.isdir(os.path.join(V4, s))]  # suites present on this machine (weights renormalise)
TRAIN_MAPS = {s: [(s, f) for f in maplist(s)] for s, _ in MAPSETS}


def evaluate(it, wh):
    build("nnm_eval", wh, rl=False)
    tag = os.path.join("bench_out", "nnm", f"eval{it}")
    shutil.rmtree(os.path.join(V4, tag), ignore_errors=True)
    os.makedirs(os.path.join(V4, tag))
    jobs, lines = [], []
    for s, m in EVAL_MAPS:
        for side in "AB":
            a, b = ("nnm_eval", "v92") if side == "A" else ("v92", "nnm_eval")
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
    log(f"{time.strftime('%H:%M:%S')} EVAL iter {it} vs v92 (deterministic macro policy): ladder {w['maps'][0]:.0f}/{w['maps'][1]}, "
        f"pool-test {w['maps_pooltest'][0]:.0f}/{w['maps_pooltest'][1]}, total {100 * tot:.1f}%")
    return tot


TL_METRICS = ("gems", "submittedGems", "earnedGold", "kills", "assists", "deaths")
PF = 6 * 2 * 5 + 2 * 5 + 1  # privileged critic features: 6 champions x 2 teams x 5 metrics, team sums, round


def timelines(d, our_team):
    """Per-round truth from the match statistics (run-length timelines): {champion id: {metric: array}}, the team
    banked lead (ours - theirs) per round, and the ids of each team (ours first)."""
    tl = {}
    for t in d["championTimelines"]:
        if t["metric"] not in TL_METRICS:
            continue
        vals = []
        for run in t["runs"]:
            vals.extend([float(run["value"])] * int(run["duration"]))
        tl.setdefault(t["owner"]["id"], {})[t["metric"]] = np.array(vals or [0.0])
    sub = {}
    for t in d["teamTimelines"]:
        if t["metric"] == "submittedGems":
            vals = []
            for run in t["runs"]:
                vals.extend([float(run["value"])] * int(run["duration"]))
            sub[t["owner"]] = np.array(vals or [0.0])
    them = "teamB" if our_team == "teamA" else "teamA"
    n = max(len(sub.get(our_team, [0])), len(sub.get(them, [0])))
    pad = lambda a: np.concatenate([a, np.full(n - len(a), a[-1])]) if len(a) < n else a
    lead = pad(sub.get(our_team, np.zeros(1))) - pad(sub.get(them, np.zeros(1)))
    team_of = {c["id"]: c["team"] for c in d["roster"]["champions"]}
    ids = (sorted(i for i, tm in team_of.items() if tm == our_team), sorted(i for i, tm in team_of.items() if tm == them))
    return tl, lead, ids


def at(a, r):
    return a[min(max(r, 0), len(a) - 1)]


def priv_features(tl, ids, r):
    """Full game state at round r for the critic (never for the policy): every champion's carried / banked gems, gold
    earned, kills, deaths (ours first), both teams' sums, round."""
    f = np.zeros(PF, np.float32)
    k = 0
    for team in ids:
        sums = np.zeros(5)
        for slot in range(6):
            if slot < len(team) and team[slot] in tl:
                m = tl[team[slot]]
                v = [at(m.get(x, np.zeros(1)), r) for x in ("gems", "submittedGems", "earnedGold", "kills", "deaths")]
                f[k:k + 5] = v
                sums += v
            k += 5
        f[60 + (0 if team is ids[0] else 5):60 + (5 if team is ids[0] else 10)] = sums
    f[70] = r / 1000.0
    return np.sign(f) * np.log1p(np.abs(f))


def gae_game(rows, tl, lead, z, Vg):
    """GAE per champion over its decision rows (dicts with r, me = champion id), rewards from the true timelines:
    own value (banked + carried gems) / OWN_SCALE + gold earned / GOLD_SCALE + KILL_W kills + ASSIST_W assists -
    DEATH_W deaths + TEAM_W x team banked-lead change / LEAD_SCALE; after a champion's last decision the same to the end
    of the game + Z_W x result. Returns (advantages, value targets)."""
    adv, ret = np.zeros(len(rows)), np.zeros(len(rows))
    by_me = {}
    for i, r in enumerate(rows):
        by_me.setdefault(r["me"], []).append(i)
    for me, idxs in by_me.items():
        m = tl.get(me, {})
        z0 = np.zeros(1)
        own = lambda r: at(m.get("submittedGems", z0), r) + at(m.get("gems", z0), r)
        score = lambda r: (own(r) / OWN_SCALE + at(m.get("earnedGold", z0), r) / GOLD_SCALE + KILL_W * at(m.get("kills", z0), r)
                           + ASSIST_W * at(m.get("assists", z0), r) - DEATH_W * at(m.get("deaths", z0), r)
                           + TEAM_W * at(lead, r) / LEAD_SCALE)
        end = len(lead) - 1
        acc = 0.0
        for pos in range(len(idxs) - 1, -1, -1):
            i = idxs[pos]
            r0 = rows[i]["r"]
            if pos == len(idxs) - 1:
                acc = score(end) - score(r0) + Z_W * z - Vg[i]
            else:
                j = idxs[pos + 1]
                r1 = rows[j]["r"]
                dt = max(1, r1 - r0)
                acc = score(r1) - score(r0) + GAMMA ** dt * Vg[j] - Vg[i] + (GAMMA * LAMBDA) ** dt * acc
            adv[i], ret[i] = acc, acc + Vg[i]
    return adv, ret


def parse_rows(txt):
    rows = []
    for l in txt.splitlines():
        if not l.startswith("NRB "):
            continue
        q = l.split()
        if len(q) != 14:
            continue
        try:
            x = np.frombuffer(base64.b64decode(q[13]), np.int16)
        except Exception:
            continue
        if len(x) != NF:
            continue
        rows.append(dict(r=int(q[1]), sl=int(q[2]), contact=int(q[3]), ba=int(q[4]), blp=float(q[5]), ta=int(q[6]), tlp=float(q[7]),
                         chg=int(q[8]), val=int(q[9]), gold=int(q[10]), kills=int(q[11]), deaths=int(q[12]), x=x,
                         me=int(x[16 + 31])))  # champion id (= the statistics roster id)
    return rows



def beh_logq(logits, con):
    """Log-probabilities of the bot's behaviour choice (nnrec.cpp): softmax(logits / TEMP), then out of contact the
    forced options keep KEEP_OPT of their probability and the rest moves to 0 (farm = v92's default chain)."""
    p = F.softmax(logits / TEMP, -1)
    out_c = (1.0 - con)[:, None]
    forced = torch.zeros(p.shape[1], device=p.device)
    forced[FORCED] = 1.0
    moved = (p * forced).sum(1) * (1.0 - KEEP_OPT) * (1.0 - con)
    q = p * (1.0 - forced * out_c * (1.0 - KEEP_OPT))
    q = q + F.one_hot(torch.zeros_like(con, dtype=torch.long), p.shape[1]).float() * moved[:, None]
    return torch.log(q.clamp_min(1e-12))

def vfeat(X):
    x = X.float()
    return torch.sign(x) * torch.log1p(x.abs())


if __name__ == "__main__":
    net = load(teacher(Prep()), INIT)  # a fresh option head ("none") when the checkpoint has none
    ref = load(teacher(Prep()), INIT)
    net.to(dev); ref.to(dev).eval()
    for p in ref.parameters():
        p.requires_grad_(False)
    # privileged critic: the champion's own view + the true full game state from the match timelines (training only)
    value = nn.Sequential(nn.Linear(NF + PF, 256), nn.ReLU(), nn.Linear(256, 256), nn.ReLU(), nn.Linear(256, 1)).to(dev)
    opt = torch.optim.Adam(list(net.parameters()) + list(value.parameters()), lr=LR)
    state_f = os.path.join(WD, "state.json")
    it0, best = 0, -1.0
    if os.path.exists(state_f):
        st = json.load(open(state_f))
        it0, best = st["iter"], st.get("best", -1.0)
        load(net, os.path.join(WD, f"teacher_{it0}.pt"), dev)
        value.load_state_dict(torch.load(os.path.join(WD, f"value_{it0}.pt"), map_location=dev))

    def export(tag):
        pt = os.path.join(WD, f"teacher_{tag}.pt")
        torch.save(net.state_dict(), pt)
        wh = os.path.join(WD, f"teacher_w_{tag}.h")
        subprocess.run([sys.executable, "-P", os.path.join(LAB, "nn_export.py"), pt, "teacher", wh], check=True, capture_output=True)
        return wh

    if it0 == 0:
        wh0 = export("0")
        build("nnsnap", wh0, rl=False)  # league snapshot = the start network until a better one is found
        best = evaluate(0, wh0)
        shutil.copyfile(os.path.join(WD, "teacher_0.pt"), os.path.join(WD, "best.pt"))
        torch.save(value.state_dict(), os.path.join(WD, "value_0.pt"))
        json.dump({"iter": 0, "best": best}, open(state_f, "w"))

    for it in range(it0 + 1, it0 + ITERS + 1):
        t0 = time.time()
        wh = export("cur")
        build("nnm", wh, rl=True)
        rng = random.Random(3000 + it)
        games = []
        for _ in range(GAMES):
            s = rng.choices([m for m, _ in MAPSETS], [w for _, w in MAPSETS])[0]
            o = rng.choices([b for b, _ in LEAGUE], [w for _, w in LEAGUE])[0]
            games.append((rng.choice(TRAIN_MAPS[s]), o, rng.choice("AB")))
        tag = os.path.join("bench_out", "nnm", f"i{it}")
        shutil.rmtree(os.path.join(V4, tag), ignore_errors=True)
        os.makedirs(os.path.join(V4, tag))
        lines = []
        for k, ((s, m), o, side) in enumerate(games):
            a, b = ("nnm", o) if side == "A" else (o, "nnm")
            f = f"{tag}/g{k}".replace("\\", "/")
            lines.append(f"bots/{a} bots/{b} {s}/{m} {f}.repl26a --statistics {f}.json --json")
        play(lines, tag)
        cols = {k: [] for k in ("x", "p", "ba", "blp", "ta", "tlp", "adv", "ret", "w", "z", "con")}
        res = {b: [0, 0] for b, _ in LEAGUE}
        nimp = nkeep = nbeh = ncon = 0
        bcount = np.zeros(8, int)
        for k, ((s, m), o, side) in enumerate(games):
            try:
                z, gm, gt = result(os.path.join(V4, tag, f"g{k}.json"), side)
                tl, tlead, ids = timelines(json.load(open(os.path.join(V4, tag, f"g{k}.json"))), f"team{side}")
                txt = zipfile.ZipFile(os.path.join(V4, tag, f"g{k}.repl26a")).read(f"team-{side.lower()}.stdout").replace(b"\0", b"").decode("utf-8", "replace")
            except Exception as e:
                if k < 3:
                    log(f"game {k} unreadable: {e!r}")
                continue
            res[o][0] += z > 0; res[o][1] += 1
            rows = parse_rows(txt)
            if not rows:
                continue
            P = np.stack([priv_features(tl, ids, r["r"]) for r in rows])
            with torch.no_grad():
                Vg = value(torch.cat([vfeat(torch.as_tensor(np.stack([r["x"] for r in rows])).to(dev)),
                                      torch.as_tensor(P).to(dev)], 1)).squeeze(1).cpu().numpy()
            adv, ret = gae_game(rows, tl, tlead, z, Vg)
            for i, r in enumerate(rows):
                important = (r["ba"] >= 0 and (r["ba"] != 0 or r["contact"])) or r["chg"]
                if r["ba"] >= 0:
                    bcount[r["ba"]] += 1
                    nbeh += 1
                    ncon += r["contact"]
                if not important and rng.random() > KEEP_FRAC:
                    continue
                wgt = (1.0 if important else 1.0 / KEEP_FRAC) * (EARLY_W if r["r"] < EARLY_R else 1.0)
                for c, v in (("x", r["x"]), ("p", P[i]), ("ba", r["ba"]), ("blp", r["blp"]), ("ta", r["ta"]), ("tlp", r["tlp"]), ("adv", adv[i]),
                             ("ret", ret[i]), ("w", wgt), ("z", z), ("con", r["contact"])):
                    cols[c].append(v)
                nimp += important; nkeep += not important
        shutil.rmtree(os.path.join(V4, tag), ignore_errors=True)
        if not cols["x"]:
            log(f"iter {it}: no samples"); continue
        X = torch.as_tensor(np.stack(cols["x"])).to(dev)
        PR = torch.as_tensor(np.stack(cols["p"])).to(dev)
        BA = torch.as_tensor(cols["ba"]).to(dev); BLP = torch.as_tensor(cols["blp"], dtype=torch.float32).to(dev)
        TA = torch.as_tensor(cols["ta"]).to(dev); TLP = torch.as_tensor(cols["tlp"], dtype=torch.float32).to(dev)
        ADV = torch.as_tensor(cols["adv"], dtype=torch.float32).to(dev)
        RET = torch.as_tensor(cols["ret"], dtype=torch.float32).to(dev)
        Wt = torch.as_tensor(cols["w"], dtype=torch.float32).to(dev)
        CON = torch.as_tensor(cols["con"], dtype=torch.float32).to(dev)
        n = len(X)
        with torch.no_grad():
            v0 = torch.cat([value(torch.cat([vfeat(X[s:s + 8192]), PR[s:s + 8192]], 1)).squeeze(1) for s in range(0, n, 8192)])
            ev = 1.0 - ((RET - v0).var() / RET.var().clamp_min(1e-6)).item()
        zc = float(np.corrcoef(np.array(cols["ret"]), np.array(cols["z"]))[0, 1]) if np.std(cols["z"]) > 0 else 0.0
        stats = []
        for ep in range(EPOCHS):
            perm = torch.randperm(n, device=dev)
            for s0 in range(0, n, 4096):
                idx = perm[s0:s0 + 4096]
                xb, wb = X[idx], Wt[idx] / Wt[idx].mean()
                out = net(xb)
                adv = ADV[idx]
                adv = (adv - adv.mean()) / (adv.std() + 1e-6)
                hb = (BA[idx] >= 0).float()  # option decisions (out of contact only)
                ht = (TA[idx] >= 0).float()
                lpb = F.log_softmax(out["option"] / OPT_T, -1)
                lpt = F.log_softmax(out["target"] / TEMP, -1)
                rb = torch.exp(lpb.gather(1, BA[idx].clamp_min(0)[:, None]).squeeze(1) - BLP[idx])
                rt = torch.exp(lpt.gather(1, TA[idx].clamp_min(0)[:, None]).squeeze(1) - TLP[idx])
                surr = lambda r: torch.min(r * adv, r.clamp(1 - CLIP, 1 + CLIP) * adv)
                pg = -(wb * (hb * surr(rb) + ht * surr(rt))).mean()
                with torch.no_grad():
                    rout = ref(xb)
                    rlb = F.log_softmax(rout["option"] / OPT_T, -1)
                    rlt = F.log_softmax(rout["target"] / TEMP, -1)
                klb = (lpb.exp() * (lpb - rlb)).sum(-1).mean()
                klt = (lpt.exp() * (lpt - rlt)).sum(-1).mean()
                ent = -(lpb.exp() * lpb).sum(-1).mean() - (lpt.exp() * lpt).sum(-1).mean()
                v = value(torch.cat([vfeat(xb), PR[idx]], 1)).squeeze(1)
                vl = (wb * (v - RET[idx]) ** 2).mean()
                loss = pg + BETA_KL * (klb + klt) - ENT * ent + 0.5 * vl
                opt.zero_grad(); loss.backward()
                torch.nn.utils.clip_grad_norm_(list(net.parameters()) + list(value.parameters()), 1.0)
                opt.step()
                stats.append((pg.item(), klb.item(), klt.item(), ent.item(), vl.item(), rb.mean().item(), rt.mean().item()))
        st_ = np.mean(stats, 0)
        torch.save(net.state_dict(), os.path.join(WD, f"teacher_{it}.pt"))
        torch.save(value.state_dict(), os.path.join(WD, f"value_{it}.pt"))
        wr = ", ".join(f"{b} {a}/{c}" for b, (a, c) in res.items() if c)
        mix = " ".join(f"{i}:{100 * c / max(1, bcount.sum()):.0f}%" for i, c in enumerate(bcount))
        log(f"{time.strftime('%H:%M:%S')} iter {it}: rollouts won {wr} | rows {nimp} important + {nkeep} keeps; options {nbeh} "
            f"({ncon} in contact) mix {mix} | corr(return, result) {zc:+.2f}, critic EV {ev:+.3f} | pg {st_[0]:+.4f} "
            f"kl beh {st_[1]:.4f} tgt {st_[2]:.4f} ent {st_[3]:.3f} vloss {st_[4]:.3f} ratio {st_[5]:.3f}/{st_[6]:.3f} | {time.time() - t0:.0f}s")
        if it % EVAL_EVERY == 0:
            whe = export(f"{it}")
            sc = evaluate(it, whe)
            if sc > best:
                best = sc
                shutil.copyfile(os.path.join(WD, f"teacher_{it}.pt"), os.path.join(WD, "best.pt"))
                build("nnsnap", whe, rl=False)  # the league plays our newest best network
                log(f"  new best: iter {it} ({100 * sc:.1f}%)")
        json.dump({"iter": it, "best": best}, open(state_f, "w"))
