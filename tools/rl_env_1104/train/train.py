"""E142, from nn_rl4.py: retrain on nnm4 (nnfinal rules + fuel parts), against nnm4 copies and v92, on the current 86-map pool; checkpoints chosen with noise on both sides.
Neural bot stage 4: RL (PPO + GAE) of the deployed bot at real fuel. The student network plays as it does in a real game (A2_NN_LIVE,
nnrec.cpp): camps scored fresh at the start of each turn with the last summary of the slow part, which advances by stages on
the fuel v92 leaves; v92 banks. So training sees the delays and the fuel limits of deployment. Rollouts are debug builds:
sampling and logging sit inside debug_block, which spends no fuel (the deployed release build has neither).
The bot prints NRZ (the features a summary in force was computed from) and NRL rows (every target change and 1 in A2_NN_RL_KEEP of
the rest: round, slot, sampled slot, its log-probability, changed, summary id, this turn's features). The trainer recomputes
each decision exactly as the bot makes it: summary from the NRZ features, camps from the NRL features.
Reward between a champion's logged rows, from the match statistics timelines, as nn_rl3.py. Critic: own view + the full game state
(training only). Loss: clipped PPO on the target head, value net on GAE targets, KL to the start network, entropy bonus.
Opponent: v92 and two noisy copies of it. Maps: official 65%, generated otherwise (pool-test and pool-fresh never). Deterministic check at real fuel (official 70 x 2 x 3 opponents + pool-test 0-149 x 2) at iteration 0 and every
EVAL_EVERY iterations; best kept (best.pt).
usage (project root): python -P agent2/lab/nn_rl4.py WORKDIR INIT_STUDENT.pt ITERS [--games 800] [--eval-every 2]"""
import base64, json, os, random, shutil, subprocess, sys, time, zipfile
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import train_ops as ops
import torch
import torch.nn as nn
import torch.nn.functional as F
import quant_policy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nn_model import BLK, LAYOUT, NFEAT, Prep, load, split_blocks, student  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
V4, LAB = os.path.join(ROOT, "v4"), os.path.join(ROOT, "agent2", "lab")
A = sys.argv[1:]
WD, INIT, ITERS = os.path.abspath(A[0]), A[1], int(A[2])
arg = lambda k, d: type(d)(A[A.index(k) + 1]) if k in A else d
GAMES, EVAL_EVERY = arg("--games", 800), arg("--eval-every", 2)
LEAGUE = [("nnm4", 0.3), ("nnm4n1", 0.25), ("nnm4n2", 0.25), ("v92", 0.2)]
if os.environ.get('TRAIN_LEAGUE'):
    LEAGUE=[(str(k),float(v)) for k,v in json.loads(os.environ['TRAIN_LEAGUE'])]
elif os.environ.get('TRAIN_BROAD')=='1':
    LEAGUE=[('v111',.20),('nnm4',.15),('nnm4n1',.10),('v92',.10),
            ('ref_x1',.15),('ref_x3ctr',.15),('ref_p65pack',.15)]
MAPSETS = [("maps_train", 0.65), ("maps_real250", 0.1), ("maps_pooltrain", 0.25)]
if os.environ.get('TRAIN_MAPSETS'):
    MAPSETS=[(str(k),float(v)) for k,v in json.loads(os.environ['TRAIN_MAPSETS'])]
    if any('/' in k or '\\' in k or '..' in k or v<=0 for k,v in MAPSETS):raise ValueError('Invalid training map folder')
TEMP, CLIP, BETA_KL, ENT, LR, EPOCHS = 0.4, 0.2, 0.02, 0.003, 1e-4, 4
OWN_SCALE, GOLD_SCALE, KILL_W, ASSIST_W, DEATH_W, TEAM_W, LEAD_SCALE, Z_W = 30.0, 100.0, 0.5, 0.25, 0.5, 0.5, 60.0, 0.3
GAMMA, LAMBDA, KEEP, EARLY_R, EARLY_W = 0.995, 0.98, 10, 300, 1.5
TEAM_WIN = os.environ.get('TRAIN_REWARD') == 'team_win'
if TEAM_WIN:
    GAMMA, LAMBDA, EARLY_W = 1.0, .995, 1.0
if ops.NATIVE_RESIDUAL:KEEP=ops.LOG_KEEP
FLAGS = "A2_NN=11 A2_NN_MACRO=1 A2_NN_FAST=1 A2_NN_VALID=1 A2_NN_BEH=0 A2_NN_ENS=2 A2_NN_LIVE=1 A2_NN_LAZY=1 A2_NN_NNUE=1 A2_NN_Q16=1 A2_NN_SGAUTO=1 A2_FIELD_MARGIN=3000 A2_NN_FIELDS_FIRST=1 A2_STACK=1".split()  # exactly the champion: its setups come from NN_CFG
_c = os.environ.get("NN_CFG", "14377,12297,14377,9").split(",")
FLAGS += [f"A2_CFG_S3={_c[0]}", f"A2_CFG_S4={_c[1]}", f"A2_CFG_S5={_c[2]}", f"CLFS={_c[3]}"]
ENS = 2.0
NF, COFF, KCF, KC, SELF = NFEAT, BLK["c"][0], BLK["c"][2], BLK["c"][1], BLK["s"][0]  # nnrec.cpp
dev = "cuda" if torch.cuda.is_available() else "cpu"
torch.set_num_threads(int(os.environ.get("TRAIN_TORCH_THREADS", "2")))
torch.manual_seed(61110)
np.random.seed(61110)
random.seed(61110)
os.makedirs(WD, exist_ok=True)
LOG = os.path.join(WD, "rl.log")


def log(s):
    print(s, flush=True)
    open(LOG, "a").write(s + "\n")


CAMBC = str(ops.CLI)
def wasm(name, debug):
    return ops.wasm(name, debug)
def build(name, wh, rl):
    ops.build(name, wh, rl)
def debug_build(name):
    ops.compile_bot(name, debug=True)
def play(lines, tag, debug):
    ops.play(lines, tag, debug)


def result(jf, side):
    d = json.load(open(jf))
    oc = d["match"].get("outcome")
    me, them = ("teamA", "teamB") if side == "A" else ("teamB", "teamA")
    return 1.0 if oc == me else -1.0 if oc == them else 0.0


def maplist(s):
    return sorted(f for f in os.listdir(os.path.join(V4, s)) if f.endswith(".map26a"))


MAPSETS = [(s, w) for s, w in MAPSETS if os.path.isdir(os.path.join(V4, s))]
TRAIN_MAPS = {s: [(s, f) for f in maplist(s)] for s, _ in MAPSETS}
_weak = {x for x in os.environ.get("NN_WEAK_MAPS", "").split(",") if x}
if _weak:  # the maps we lose on the platform come up three times as often
    TRAIN_MAPS["maps_pool86"] = TRAIN_MAPS["maps_pool86"] + [(s, f) for s, f in TRAIN_MAPS["maps_pool86"] if f[:-7] in _weak] * 2
EVAL_OPP = ("v111", "nnm4", "v92")
EVAL_MAPS = maplist(ops.EVAL_MAP_DIR)
def evaluate(it, wh):
    return ops.evaluate(it, wh)


TL_METRICS = ("gems", "submittedGems", "earnedGold", "kills", "assists", "deaths")
PF = 6 * 2 * 5 + 2 * 5 + 1  # privileged critic features: 6 champions x 2 teams x 5 metrics, team sums, round


def timelines(d, our_team):
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
    if TEAM_WIN:
        from team_reward import gae_game as team_gae
        return team_gae(rows,lead,z,Vg,GAMMA,LAMBDA)
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
    """NRZ rows: the summary features by (champion, id); NRL rows reference them. A champion's id is in the self block."""
    zs, rows, native = {}, [], {}
    for l in txt.splitlines():
        if l.startswith('NRQ '):
            q=l.split()
            if len(q)!=4:raise ValueError('Malformed native policy vector')
            key=(int(q[2]),int(q[1]))
            if key in native:raise ValueError('Duplicate native decision identity')
            vector=np.frombuffer(base64.b64decode(q[3],validate=True),dtype='<f4').copy()
            if vector.shape!=(11,) or not np.isfinite(vector).all():raise ValueError('Invalid native policy vector')
            native[key]=vector
        elif l.startswith("NRZ "):
            q = l.split()
            if len(q) != 3:
                continue
            try:
                x = np.frombuffer(base64.b64decode(q[2]), np.int16)
            except Exception:
                continue
            if len(x) == NF:
                zs[(int(x[SELF + 31]), int(q[1]))] = x
        elif l.startswith("NRL "):
            q = l.split()
            if len(q) != (9 if ENS else 8):
                continue
            try:
                x = np.frombuffer(base64.b64decode(q[-1]), np.int16)
            except Exception:
                continue
            if len(x) != NF:
                continue
            me = int(x[SELF + 31])
            xz = zs.get((me, int(q[6])))
            if xz is None:
                continue
            rows.append(dict(r=int(q[1]), sl=int(q[2]), ta=int(q[3]), tlp=float(q[4]), chg=int(q[5]), x=x, xz=xz, me=me, bs=int(q[7]) if ENS else 0))
            if ops.NATIVE_RESIDUAL:
                rows[-1]['q']=native.pop((me,int(q[1])))
    if ops.NATIVE_RESIDUAL and native:raise ValueError('Unmatched native policy vector')
    return rows


def vfeat(X):
    x = X.float()
    return torch.sign(x) * torch.log1p(x.abs())


def live_logits(net, Xz, Xc):
    """Target logits exactly as the deployed bot computes them: summary from Xz, camps from Xc."""
    Bz = split_blocks(Xz)
    Pz = net.prep(Bz)
    emb = {k: net.enc[k](Pz[k]) for k in BLK}
    present = {k: (Bz[k][..., 0] != 0) for k in ("a", "e", "c", "l")}
    parts = [emb["g"][:, 0], emb["s"][:, 0]]
    for k in ("a", "e", "c", "l"):
        m = present[k].unsqueeze(-1).float()
        mean = (emb[k] * m).sum(1) / m.sum(1).clamp_min(1.0)
        mx = (emb[k] - 1e4 * (1 - m)).max(1).values * (m.sum(1) > 0).float()
        parts += [mean, mx]
    z = net.trunk(torch.cat(parts, -1))
    Bc = split_blocks(Xc)
    ec = net.enc["c"](net.prep(Bc)["c"])
    pc = Bc["c"][..., 0] != 0
    n = Xc.shape[0]
    keys = torch.cat([net.k["target"](ec), net.k["target"](net.extra["target"]).unsqueeze(0).expand(n, -1, -1)], 1)
    mask = torch.cat([pc, torch.ones(n, 1, dtype=torch.bool, device=Xc.device)], 1)
    s = (keys @ net.q["target"](z).unsqueeze(-1)).squeeze(-1) / net.enc_dim ** 0.5
    return s.masked_fill(~mask, -1e9)


def blend(lg, bs):
    """The deployed choice with the blend: the bonus on v92's slot."""
    return lg.scatter_add(1, bs[:, None], torch.full((len(bs), 1), ENS, device=lg.device)) if ENS else lg


if __name__ == "__main__":
    net = load(student(Prep()), INIT, dev).to(dev)
    ref = load(student(Prep()), str(ops.INITIAL), dev).to(dev).eval()
    for p in ref.parameters():
        p.requires_grad_(False)
    value = nn.Sequential(nn.Linear(NF + PF, 256), nn.ReLU(), nn.Linear(256, 256), nn.ReLU(), nn.Linear(256, 1)).to(dev)
    ops.initialize_run(WD, INIT, value)
    opt = torch.optim.Adam(list(net.parameters()) + list(value.parameters()), lr=LR)
    state_f = os.path.join(WD, "state.json")
    it0, best = 0, -1.0
    if os.path.exists(state_f):
        st = json.load(open(state_f))
        it0, best = st["iter"], st.get("best", -1.0)
        load(net, os.path.join(WD, f"student_{it0}.pt"), dev)
        value.load_state_dict(torch.load(os.path.join(WD, f"value_{it0}.pt"), map_location=dev, weights_only=True))
        ops.restore_optimizer(WD, opt, dev)

    def export(tag):
        pt = os.path.join(WD, f"student_{tag}.pt")
        torch.save(net.state_dict(), pt)
        wh = os.path.join(WD, f"student_w_{tag}.h")
        subprocess.run([sys.executable, "-P", os.path.join(LAB, "nn_export.py"), pt, "student", wh], check=True, capture_output=True)
        return wh

    if it0 == 0:
        wh0 = export("0")
        if any(b == "nnqsnap" for b, _ in LEAGUE):
            build("nnqsnap", wh0, rl=False)
            debug_build("nnqsnap")
        for b, _ in LEAGUE:
            if b != "nnqsnap" and not os.path.exists(wasm(b, True)):
                debug_build(b)
        if not os.path.exists(wasm("v92", False)):
            subprocess.run([CAMBC, "build", "bots/v92", "--release"], cwd=V4, capture_output=True)
        best = evaluate(0, wh0)
        shutil.copyfile(os.path.join(WD, "student_0.pt"), os.path.join(WD, "best.pt"))
        torch.save(value.state_dict(), os.path.join(WD, "value_0.pt"))
        json.dump({"iter": 0, "best": best}, open(state_f, "w"))

    for it in range(it0 + 1, it0 + ITERS + 1):
        ops.check_stop()
        t0 = time.time()
        log(f"BEGIN iter {it}: {GAMES} rollout games")
        wh = export("cur")
        build("nnrq", wh, rl=True)
        rng = random.Random(4000 + it)
        games = []
        for _ in range(GAMES):
            s = rng.choices([m for m, _ in MAPSETS], [w for _, w in MAPSETS])[0]
            o = rng.choices([b for b, _ in LEAGUE], [w for _, w in LEAGUE])[0]
            games.append((rng.choice(TRAIN_MAPS[s]), o, rng.choice("AB")))
        tag = os.path.join("bench_out", ops.RUN, f"i{it}")
        ops.prepare_batch(tag)
        os.makedirs(os.path.join(V4, tag))
        lines = []
        for k, ((s, m), o, side) in enumerate(games):
            a, b = ("nnrq", o) if side == "A" else (o, "nnrq")
            f = f"{tag}/g{k}".replace("\\", "/")
            lines.append(f"bots/{a} bots/{b} {s}/{m} {f}.repl26a --statistics {f}.json --json")
        play(lines, tag, debug=True)
        cols = {k: [] for k in ("x", "xz", "p", "ta", "tlp", "adv", "ret", "w", "z", "bs")}
        if ops.NATIVE_RESIDUAL:cols['q']=[]
        res = {b: [0, 0] for b, _ in LEAGUE}
        nchg = nkeep = 0
        for k, ((s, m), o, side) in enumerate(games):
            try:
                jf = os.path.join(V4, tag, f"g{k}.json")
                z = result(jf, side)
                tl, tlead, ids = timelines(json.load(open(jf)), f"team{side}")
                txt = ops.replay_stdout(os.path.join(V4, tag, f"g{k}.repl26a"), side)
            except Exception as e:
                raise RuntimeError(f"game {k} unreadable: {e!r}") from e
            res[o][0] += z > 0; res[o][1] += 1
            rows = parse_rows(txt)
            if not rows:
                raise RuntimeError(f"game {k}: missing training rows")
            P = np.stack([priv_features(tl, ids, max(0,r["r"]-1) if TEAM_WIN else r["r"]) for r in rows])
            with torch.no_grad():
                Vg = value(torch.cat([vfeat(torch.as_tensor(np.stack([r["x"] for r in rows])).to(dev)),
                                      torch.as_tensor(P).to(dev)], 1)).squeeze(1).cpu().numpy()
            adv, ret = gae_game(rows, tl, tlead, z, Vg)
            for i, r in enumerate(rows):
                wgt = (1.0 if r["chg"] else float(KEEP)) * (EARLY_W if r["r"] < EARLY_R else 1.0)
                for c, v in (("x", r["x"]), ("xz", r["xz"]), ("p", P[i]), ("ta", r["ta"]), ("tlp", r["tlp"]), ("adv", adv[i]), ("ret", ret[i]), ("w", wgt), ("z", z), ("bs", r["bs"])):
                    cols[c].append(v)
                if ops.NATIVE_RESIDUAL:cols['q'].append(r['q'])
                nchg += r["chg"]; nkeep += not r["chg"]
        # Retain game evidence for failure investigation.
        if not cols["x"]:
            log(f"iter {it}: no samples"); continue
        X = torch.as_tensor(np.stack(cols["x"])).to(dev)
        XZ = torch.as_tensor(np.stack(cols["xz"])).to(dev)
        PR = torch.as_tensor(np.stack(cols["p"])).to(dev)
        TA = torch.as_tensor(cols["ta"]).to(dev); TLP = torch.as_tensor(cols["tlp"], dtype=torch.float32).to(dev)
        BS = torch.as_tensor(cols["bs"]).to(dev)
        Q = torch.as_tensor(np.stack(cols['q']),device=dev) if ops.NATIVE_RESIDUAL else None
        ADV = torch.as_tensor(cols["adv"], dtype=torch.float32).to(dev)
        RET = torch.as_tensor(cols["ret"], dtype=torch.float32).to(dev)
        Wt = torch.as_tensor(cols["w"], dtype=torch.float32).to(dev)
        n = len(X)
        with torch.no_grad():
            v0 = torch.cat([value(torch.cat([vfeat(X[s:s + 8192]), PR[s:s + 8192]], 1)).squeeze(1) for s in range(0, n, 8192)])
            ev = 1.0 - ((RET - v0).var() / RET.var().clamp_min(1e-6)).item()
            # the check that the trainer reproduces the bot: on the logged rows the log-probability recomputed here should match
            FLOAT0=torch.cat([blend(live_logits(net,XZ[s:s+8192],X[s:s+8192]),BS[s:s+8192]) for s in range(0,n,8192)])
            lp0=F.log_softmax(FLOAT0/TEMP,-1).gather(1,TA[:,None]).squeeze(1)
            lpdiff = (lp0 - TLP).abs()
            if ops.NATIVE_RESIDUAL:
                if float(lpdiff.median())>.05 or float(lpdiff.quantile(.9))>.25:
                    raise RuntimeError('Broad native/float input-model mismatch; anchoring must not conceal it')
                native_diff=quant_policy.validate(Q,TA,TLP,TEMP)
                ops.atomic_json(os.path.join(WD,f'native_batch_{it}.json'),{'rows':n,'native_logp_max_error':float(native_diff.max()),
                    'float_logp_max_error':float(lpdiff.max()),'float_logp_p90':float(lpdiff.quantile(.9)),
                    'update':'Native old distribution plus differentiable float-logit deltas; new native release still requires independent evaluation.'})
                lpdiff=native_diff
        zc = float(np.corrcoef(np.array(cols["ret"]), np.array(cols["z"]))[0, 1]) if np.std(cols["z"]) > 0 else 0.0
        ops.validate_batch(WD, it, X, XZ, TA, TLP, lpdiff)
        stats = []
        for ep in range(EPOCHS):
            perm = torch.randperm(n, device=dev)
            for s0 in range(0, n, 4096):
                idx = perm[s0:s0 + 4096]
                xb, zb, wb = X[idx], XZ[idx], Wt[idx] / Wt[idx].mean()
                current=blend(live_logits(net,zb,xb),BS[idx])
                logits=quant_policy.anchored(Q[idx],current,FLOAT0[idx]) if ops.NATIVE_RESIDUAL else current
                lpt=F.log_softmax(logits/TEMP,-1)
                adv = ADV[idx]
                adv = (adv - adv.mean()) / (adv.std() + 1e-6)
                rt = torch.exp(lpt.gather(1, TA[idx][:, None]).squeeze(1) - TLP[idx])
                pg = -(wb * torch.min(rt * adv, rt.clamp(1 - CLIP, 1 + CLIP) * adv)).mean()
                with torch.no_grad():
                    reflogits=blend(live_logits(ref,zb,xb),BS[idx])
                    if ops.NATIVE_RESIDUAL:reflogits=quant_policy.anchored(Q[idx],reflogits,FLOAT0[idx])
                    rlt=F.log_softmax(reflogits/TEMP,-1)
                pt = lpt.exp()
                klt = (pt * (lpt.clamp_min(-30) - rlt.clamp_min(-30))).sum(-1).mean()
                ent = -(pt * lpt.clamp_min(-30)).sum(-1).mean()
                v = value(torch.cat([vfeat(xb), PR[idx]], 1)).squeeze(1)
                vl = (wb * (v - RET[idx]) ** 2).mean()
                loss = pg + BETA_KL * klt - ENT * ent + 0.5 * vl
                if not torch.isfinite(loss):
                    raise RuntimeError("Non-finite training loss")
                opt.zero_grad(); loss.backward()
                torch.nn.utils.clip_grad_norm_(list(net.parameters()) + list(value.parameters()), 1.0)
                opt.step()
                stats.append((pg.item(), klt.item(), ent.item(), vl.item(), rt.mean().item()))
        st_ = np.mean(stats, 0)
        torch.save(net.state_dict(), os.path.join(WD, f"student_{it}.pt"))
        torch.save(value.state_dict(), os.path.join(WD, f"value_{it}.pt"))
        wr = ", ".join(f"{b} {a}/{c}" for b, (a, c) in res.items() if c)
        log(f"{time.strftime('%H:%M:%S')} iter {it}: rollouts won {wr} | rows {nchg} changes + {nkeep} keeps | logged vs recomputed lp: median {lpdiff.median().item():.4f}, "
            f"p90 {lpdiff.quantile(0.9).item():.4f} | corr(return, result) {zc:+.2f}, critic EV {ev:+.3f} | pg {st_[0]:+.4f} kl {st_[1]:.4f} ent {st_[2]:.3f} "
            f"vloss {st_[3]:.3f} ratio {st_[4]:.3f} | {time.time() - t0:.0f}s")
        if it % EVAL_EVERY == 0:
            whe = export(f"{it}")
            sc = evaluate(it, whe)
            if sc > best:
                best = sc
                shutil.copyfile(os.path.join(WD, f"student_{it}.pt"), os.path.join(WD, "best.pt"))
                if any(b == "nnqsnap" for b, _ in LEAGUE):
                    build("nnqsnap", whe, rl=False)
                    debug_build("nnqsnap")
                log(f"  new best: iter {it} ({100 * sc:.1f}%)")
        ops.save_resume(WD, it, best, opt)
