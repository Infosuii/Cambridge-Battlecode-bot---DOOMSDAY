"""Bounded on-policy DAgger / distillation of a branch-local copy of Agent 2's student (FEAT-003 launch, FEAT-005
harvest). Run with the CUDA venv python, detached (see research/jd-g5070-1104/MODEL_MANIFEST.json "rl_runs"):

  <venv>\\Scripts\\python tools/jd_g5070-1104/rl_dagger.py --run rl-dagger-01 [--hours 5] [--jobs 5] [--cpus 14-19]

Lineage: the student starts from the preserved student_i2.pt (Agent 2's student of macro-RL iteration 2, agent2-neural
56b60b96) and is distilled from the preserved lightly trained teacher nn_rl3/best.pt (same commit), with Agent 2's
nn_model.py / nn_export.py unchanged and nn_distill.py's loss (KL to the teacher on behaviour, target, option at 1.0
and attack / cast / cast_tgt at 0.3). Nothing is pushed to agent2-neural; checkpoints stay in <eval>/rl/<run>/.

Each iteration (DAgger with the teacher as expert, data at the DEPLOYED cadence and fallback):
  1. export the current student (nn_export.py) and build the recorder: the candidate source snapshot taken at launch
     with JD_NN=3, A2_NN_FAST=1, JD_NN_EVENT=1, JD_NN_REC=1 (an NR feature row at every event-driven decision, the
     v92 fallback in force between decisions) at OFFICIAL fuel (no --fuel-quantum);
  2. play it on the training maps (poolfresh sorted 121-209, disjoint from every dev / selection / holdout map by
     SHA-256) vs v92, x3inv, p65pack, both sides; parse NR rows from the replays (replays then deleted);
  3. aggregate all iterations' rows (newest kept whole, older subsampled to --max-rows), split by map (crc32 % 10 == 0
     held out), fine-tune the current student towards the teacher, save iter<k+1>.pt;
  4. evaluate it at official fuel: event-cadence bot vs v92 / x3inv on the eval maps (poolfresh 210-249) both sides,
     paired against the v92 arm on the same cells (computed once); record wins, fuel-outs, faults.
Stops by itself when the next iteration would pass the deadline (--hours from start) or when <run>/STOP exists.
CPU: the process pins itself (and so every child: run-batch games, builds) to --cpus and below-normal priority;
torch uses 2 threads and the GPU.
"""
import argparse, base64, ctypes, datetime as dt, glob, hashlib, json, os, shutil, subprocess, sys, time, zipfile, zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.dirname(os.path.dirname(HERE))
EVAL = os.path.join(os.path.dirname(WT), "jd-eval")
A2 = os.path.join(EVAL, "a2", "research", "agent2-neural", "rl_workspace")
LAB = os.path.join(A2, "agent2", "lab")
CLI = os.path.join(EVAL, "tools", "vendor", "cambc.exe")
MANIFEST = os.path.join(WT, "research", "jd-g5070-1104", "MODEL_MANIFEST.json")
A2_COMMIT = "56b60b9638a0c32116d2d8d86ee31570e9faa868"
os.environ["NN_LAYOUT"] = "2"
sys.path.insert(0, LAB)
import torch  # noqa: E402
import torch.nn.functional as F  # noqa: E402
from nn_model import Prep, load, student, teacher  # noqa: E402

W = {"behaviour": 1.0, "target": 1.0, "option": 1.0, "attack": 0.3, "cast": 0.3, "cast_tgt": 0.3}  # nn_distill.py
REC_DEFINES = ["JD_NN=3", "A2_NN_FAST=1", "JD_NN_EVENT=1", "JD_NN_REC=1"]
EVAL_DEFINES = ["JD_NN=3", "A2_NN_FAST=1", "JD_NN_EVENT=1"]
OPPS_REC = ["v92-448de19b2a28", "x3inv-c5da472cafd8", "p65pack-a1a0211b8399"]
OPPS_EVAL = ["v92-448de19b2a28", "x3inv-c5da472cafd8"]


def now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def tree_digest(src):
    h = hashlib.sha256()
    for root, _, files in os.walk(src):
        for fn in sorted(files):
            p = os.path.join(root, fn)
            h.update(os.path.relpath(p, src).replace("\\", "/").encode() + b"\0" + sha(p).encode() + b"\n")
    return h.hexdigest()


def pin(cpus):
    """Pin this process (children inherit) to logical CPUs lo-hi and lower its priority (Windows)."""
    lo, hi = (int(x) for x in cpus.split("-"))
    mask = sum(1 << i for i in range(lo, hi + 1))
    k = ctypes.windll.kernel32
    k.GetCurrentProcess.restype = ctypes.c_void_p
    k.SetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    k.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    h = k.GetCurrentProcess()
    ok = k.SetProcessAffinityMask(h, mask)
    k.SetPriorityClass(h, 0x4000)  # BELOW_NORMAL_PRIORITY_CLASS
    return bool(ok), mask


class Log:
    def __init__(self, path):
        self.f = open(path, "a", encoding="utf-8")

    def __call__(self, *a):
        s = f"{now()} " + " ".join(str(x) for x in a)
        print(s, flush=True)
        self.f.write(s + "\n")
        self.f.flush()


def map_split():
    """poolfresh maps sorted 121-209 train, 210-249 eval; refuse any map whose SHA-256 is in another partition."""
    pf = sorted(glob.glob(os.path.join(EVAL, "maps", "poolfresh", "*.map26a")))
    used = set()
    for s in ("dev", "select", "conf", "pool", "fresh51104", "official70", "smoke3", "probe4"):
        for m in glob.glob(os.path.join(EVAL, "maps", s, "*.map26a")):
            used.add(sha(m))
    rest = [m for m in pf[120:] if sha(m) not in used]
    assert len(rest) >= 100, len(rest)
    return rest[:89], rest[89:]


def export(pt, out):
    r = subprocess.run([sys.executable, "-P", os.path.join(LAB, "nn_export.py"), pt, "student", out], cwd=A2,
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("export failed: " + r.stderr[-2000:])
    return sha(out)


def make_bot(snapshot, name, header, defines):
    dest = os.path.join(EVAL, "bots", name)
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(snapshot, os.path.join(dest, "src"))
    shutil.copyfile(header, os.path.join(dest, "src", "jd_nn_weights.h"))
    jc = os.path.join(dest, "src", "jd_config.h")
    s = open(jc, encoding="utf-8").read()
    pre = "".join(f"#define {d.split('=')[0]} {d.split('=', 1)[1]}\n" for d in defines)
    open(jc, "w", encoding="utf-8", newline="").write(pre + s)
    wasm = os.path.join(EVAL, "wasm", name + ".wasm")
    r = subprocess.run([CLI, "build", f"bots/{name}", "--release", "--output", wasm], cwd=EVAL, capture_output=True, text=True,
                       timeout=900)
    cc = os.path.join(dest, "compile_commands.json")
    if os.path.exists(cc):
        os.remove(cc)
    if r.returncode != 0 or not os.path.exists(wasm):
        raise RuntimeError("build failed " + name + (r.stdout + r.stderr)[-3000:])
    return sha(wasm)


def play(R, tag, rows_spec, jobs, log):
    """rows_spec: list of (bot, opp, map_path, side, gid). Returns {gid: stats dict or None}."""
    d = os.path.join(R, "games", tag)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(os.path.join(d, "g"))
    lines = []
    for bot, opp, mp, side, gid in rows_spec:
        rel = lambda p: os.path.relpath(p, d).replace("\\", "/")
        A, B = (bot, opp) if side == "A" else (opp, bot)
        lines.append(f"{rel(os.path.join(EVAL, 'bots', A))} {rel(os.path.join(EVAL, 'bots', B))} {rel(mp)} g/{gid}.repl26a "
                     f"--statistics g/{gid}.json --json")
    man = os.path.join(d, "manifest.txt")
    open(man, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    t0 = time.time()
    with open(os.path.join(d, "batch.log"), "w", encoding="utf-8") as bl:
        r = subprocess.run([CLI, "run-batch", man, "--jobs", str(jobs), "--json", "--release", "--color", "never",
                            "--log-limit", "67108864", "--timeout", "900"], cwd=EVAL, stdout=bl, stderr=subprocess.STDOUT)
    log(f"{tag}: {len(lines)} games rc {r.returncode} in {time.time() - t0:.0f}s")
    return d


def game_result(d, gid, side):
    st = os.path.join(d, "g", gid + ".json")
    if not os.path.exists(st):
        return None
    j = json.load(open(st, encoding="utf-8"))
    me, other = "team" + side, "team" + ("B" if side == "A" else "A")
    oc = j["match"].get("outcome")
    score = 1.0 if oc == me else 0.0 if oc == other else 0.5
    fo = sum(len(e["entries"]) for e in j["events"] if e["kind"] == "fuelExhausted" and e["owner"]["team"] == me)
    return dict(score=score, fuel_outs=fo, faults=int(j["diagnostics"]["botFaults"][me]))


def parse_rows(d, gid, side):
    rp = os.path.join(d, "g", gid + ".repl26a")
    if not os.path.exists(rp):
        return []
    out = []
    with zipfile.ZipFile(rp) as z:
        m = f"team-{side.lower()}.stdout"
        if m not in z.namelist():
            return []
        txt = z.read(m).replace(b"\0", b"\n").decode("utf-8", "replace")
    for l in txt.splitlines():
        if l.startswith("NR "):
            p = l.split(" ")
            try:
                f = np.frombuffer(base64.b64decode(p[4]), np.int16)
            except Exception:  # noqa: BLE001
                continue
            if len(f) == 500:
                out.append(f)
    return out


def distill(S, T, X, keys, epochs, lr, log):
    dev = "cuda"
    held = np.array([zlib.crc32(k.encode()) % 10 == 0 for k in keys])
    tr, te = np.where(~held)[0], np.where(held)[0]
    Xt = torch.as_tensor(X).to(dev)
    S.to(dev).train()
    opt = torch.optim.Adam(S.parameters(), lr=lr)
    BS = 2048
    steps = max(1, epochs * (len(tr) // BS))
    sch = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=lr, total_steps=steps)
    rng = np.random.default_rng(len(X))

    def agree():
        S.eval()
        hit = {h: 0 for h in W}
        kl = 0.0
        with torch.no_grad():
            for s0 in range(0, len(te), 8192):
                xb = Xt[torch.as_tensor(te[s0:s0 + 8192], device=dev)]
                to, so = T(xb), S(xb)
                for h in W:
                    hit[h] += (to[h].argmax(-1) == so[h].argmax(-1)).sum().item()
                kl += sum(w * F.kl_div(F.log_softmax(so[h], -1), F.softmax(to[h], -1), reduction="sum").item() for h, w in W.items())
        S.train()
        n = max(1, len(te))
        return {h: round(v / n, 4) for h, v in hit.items()}, kl / n

    a0, k0 = agree()
    log(f"distill: rows {len(X)} train {len(tr)} held-out {len(te)}; before: KL {k0:.4f} agree {a0}")
    done = 0
    for ep in range(epochs):
        perm = rng.permutation(tr)
        tot = 0.0
        for s0 in range(0, len(perm) - BS + 1, BS):
            if done >= steps:
                break
            xb = Xt[torch.as_tensor(perm[s0:s0 + BS], device=dev)]
            with torch.no_grad():
                to = T(xb)
            so = S(xb)
            loss = sum(w * F.kl_div(F.log_softmax(so[h], -1), F.softmax(to[h], -1), reduction="batchmean") for h, w in W.items())
            opt.zero_grad()
            loss.backward()
            opt.step()
            sch.step()
            done += 1
            tot += loss.item()
        a, k = agree()
        log(f"distill epoch {ep + 1}: train KL {tot / max(1, len(perm) // BS):.4f} | held-out KL {k:.4f} agree {a}")
    S.cpu().eval()
    del Xt
    torch.cuda.empty_cache()
    return dict(before=dict(kl=k0, agree=a0), after=dict(kl=k, agree=a), rows=len(X), train=len(tr), held=len(te))


def update_manifest(run, entry_key, value):
    """Read-modify-write MODEL_MANIFEST.json's rl_runs[run][entry_key] (only this key)."""
    try:
        m = json.load(open(MANIFEST, encoding="utf-8"))
    except Exception:  # noqa: BLE001
        m = {}
    m.setdefault("rl_runs", {}).setdefault(run, {})[entry_key] = value
    tmp = MANIFEST + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(m, f, indent=1)
        f.write("\n")
    os.replace(tmp, MANIFEST)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="rl-dagger-01")
    ap.add_argument("--hours", type=float, default=5.0)
    ap.add_argument("--jobs", type=int, default=5)
    ap.add_argument("--cpus", default="14-19")
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--max-rows", type=int, default=1500000)
    ap.add_argument("--seed-pt", default=os.path.join(EVAL, "checkpoints", "student_i2.pt"))
    ap.add_argument("--teacher-pt", default=os.path.join(EVAL, "checkpoints", "nn_rl3", "best.pt"))
    a = ap.parse_args()
    R = os.path.join(EVAL, "rl", a.run)
    os.makedirs(os.path.join(R, "ckpt"), exist_ok=True)
    os.makedirs(os.path.join(R, "data"), exist_ok=True)
    os.makedirs(os.path.join(R, "export"), exist_ok=True)
    log = Log(os.path.join(R, "log.txt"))
    pinned, mask = pin(a.cpus)
    torch.set_num_threads(2)
    t_start = time.time()
    deadline = t_start + a.hours * 3600
    git_head = subprocess.run(["git", "-C", WT, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    snap = os.path.join(R, "src_snapshot")
    if not os.path.exists(snap):
        shutil.copytree(os.path.join(WT, "bots", "jd-g5070-1104", "src"), snap)
    train_maps, eval_maps = map_split()
    status = dict(run=a.run, pid=os.getpid(), started=now(), deadline=dt.datetime.fromtimestamp(deadline, dt.timezone.utc)
                  .strftime("%Y-%m-%dT%H:%M:%SZ"), pinned=pinned, affinity_mask=hex(mask), cpus=a.cpus, jobs=a.jobs,
                  command=" ".join([sys.executable] + sys.argv), candidate_git_head=git_head, snapshot_tree=tree_digest(snap),
                  agent2_commit=A2_COMMIT, seed_pt=a.seed_pt, seed_sha256=sha(a.seed_pt), teacher_pt=a.teacher_pt,
                  teacher_sha256=sha(a.teacher_pt), train_maps=len(train_maps), eval_maps=len(eval_maps),
                  opps_rec=OPPS_REC, opps_eval=OPPS_EVAL, rec_defines=REC_DEFINES, eval_defines=EVAL_DEFINES,
                  torch=torch.__version__, cuda=torch.cuda.get_device_name(0), state="running", iterations=[])
    sp = os.path.join(R, "status.json")
    if os.path.exists(sp):
        old = json.load(open(sp, encoding="utf-8"))
        status["iterations"] = old.get("iterations", [])
        status["resumed_from"] = old.get("started")
    save = lambda: json.dump(status, open(sp, "w", encoding="utf-8"), indent=1)
    save()
    update_manifest(a.run, "run", {k: v for k, v in status.items() if k != "iterations"})
    log(f"start {a.run}: pid {os.getpid()} pinned {pinned} mask {hex(mask)} deadline {status['deadline']} "
        f"train maps {len(train_maps)} eval maps {len(eval_maps)} snapshot {status['snapshot_tree'][:16]}")
    T = load(teacher(Prep()), a.teacher_pt, "cuda").cuda().eval()
    k = len(status["iterations"])
    cur = os.path.join(R, "ckpt", f"iter{k}.pt")
    if k == 0:
        shutil.copyfile(a.seed_pt, cur)
    # v92 base arm on the eval cells (deterministic per cell), once
    base_p = os.path.join(R, "eval_base.json")
    cells = [(o, m, s) for o in OPPS_EVAL for m in eval_maps for s in "AB"]
    gid = lambda o, m, s: f"{o.split('-')[0]}__{os.path.basename(m)[:-7]}__{s}"
    if not os.path.exists(base_p):
        d = play(R, "eval_base", [("v92-448de19b2a28", o, m, s, gid(o, m, s)) for o, m, s in cells], a.jobs, log)
        base = {gid(o, m, s): game_result(d, gid(o, m, s), s) for o, m, s in cells}
        json.dump(base, open(base_p, "w"), indent=0)
        shutil.rmtree(os.path.join(d, "g"), ignore_errors=True)
    base = json.load(open(base_p))
    iter_secs = 0.0

    def evaluate(tag, header):
        name = f"rl-{a.run}-{tag}"
        wsha = make_bot(snap, name, header, EVAL_DEFINES)
        d = play(R, tag, [(name, o, m, s, gid(o, m, s)) for o, m, s in cells], a.jobs, log)
        res = {gid(o, m, s): game_result(d, gid(o, m, s), s) for o, m, s in cells}
        shutil.rmtree(os.path.join(d, "g"), ignore_errors=True)
        shutil.rmtree(os.path.join(EVAL, "bots", name), ignore_errors=True)
        pairs = [(res[g]["score"], base[g]["score"]) for g in res if res[g] and base.get(g)]
        n = len(pairs)
        out = dict(wasm_sha256=wsha, played=sum(1 for v in res.values() if v), cells=len(cells),
                   wins=sum(1 for v in res.values() if v and v["score"] == 1.0),
                   winrate=round(100 * sum(c for c, _ in pairs) / n, 2) if n else None,
                   base_winrate=round(100 * sum(b for _, b in pairs) / n, 2) if n else None,
                   d_score=round(100 * sum(c - b for c, b in pairs) / n, 2) if n else None,
                   fuel_outs=sum(v["fuel_outs"] for v in res.values() if v), faults=sum(v["faults"] for v in res.values() if v),
                   base_fuel_outs=sum(base[g]["fuel_outs"] for g in res if base.get(g)))
        log(f"eval {tag}: {json.dumps(out)}")
        return out

    if k == 0:
        h0 = os.path.join(R, "export", "iter0_w.h")
        hs = export(cur, h0)
        ev0 = evaluate("ev0", h0)
        status["iter0"] = dict(ckpt=cur, sha256=sha(cur), header_sha256=hs, eval=ev0, parent="seed student_i2.pt (unchanged copy)")
        save()
        update_manifest(a.run, "iter0", status["iter0"])
    while True:
        if os.path.exists(os.path.join(R, "STOP")):
            log("STOP file: stopping")
            break
        left = deadline - time.time()
        if left < max(600.0, 1.1 * iter_secs):
            log(f"deadline: {left:.0f}s left, last iteration took {iter_secs:.0f}s: stopping")
            break
        t0 = time.time()
        started = now()
        hdr = os.path.join(R, "export", f"iter{k}_w.h")
        hs = export(cur, hdr)
        rec = f"rl-{a.run}-rec{k}"
        rsha = make_bot(snap, rec, hdr, REC_DEFINES)
        spec = [(rec, o, m, s, f"{o.split('-')[0]}__{os.path.basename(m)[:-7]}__{s}") for o in OPPS_REC for m in train_maps for s in "AB"]
        d = play(R, f"rec{k}", spec, a.jobs, log)
        X, keys, wins, games, fo = [], [], 0, 0, 0
        for _, o, m, s, g in spec:
            rows = parse_rows(d, g, s)
            X += rows
            keys += [os.path.basename(m)[:-7]] * len(rows)
            r = game_result(d, g, s)
            if r:
                games += 1
                wins += r["score"] == 1.0
                fo += r["fuel_outs"]
        shutil.rmtree(os.path.join(d, "g"), ignore_errors=True)
        shutil.rmtree(os.path.join(EVAL, "bots", rec), ignore_errors=True)
        dp = os.path.join(R, "data", f"iter{k}.npz")
        np.savez_compressed(dp, X=np.stack(X) if X else np.zeros((0, 500), np.int16), keys=np.array(keys))
        log(f"rec{k}: {games} games, recorder won {wins}, fuel-outs {fo}, rows {len(X)} -> {dp}")
        # aggregate (DAgger): newest iteration whole, older iterations subsampled to fit --max-rows
        parts = sorted(glob.glob(os.path.join(R, "data", "iter*.npz")), key=lambda p: int(os.path.basename(p)[4:-4]))
        newest = np.load(parts[-1])
        XA, KA = [newest["X"]], [newest["keys"]]
        older = [np.load(p) for p in parts[:-1]]
        room = max(0, a.max_rows - len(XA[0]))
        n_old = sum(len(o["X"]) for o in older)
        rng = np.random.default_rng(k)
        for o in older:
            take = len(o["X"]) if n_old <= room else int(len(o["X"]) * room / max(1, n_old))
            idx = np.sort(rng.choice(len(o["X"]), take, replace=False)) if take < len(o["X"]) else np.arange(len(o["X"]))
            XA.append(o["X"][idx])
            KA.append(o["keys"][idx])
        XA, KA = np.concatenate(XA), np.concatenate(KA)
        S = load(student(Prep()), cur)
        tr = distill(S, T, XA, list(KA), a.epochs, a.lr, log)
        nxt = os.path.join(R, "ckpt", f"iter{k + 1}.pt")
        torch.save(S.state_dict(), nxt)
        hn = os.path.join(R, "export", f"iter{k + 1}_w.h")
        hns = export(nxt, hn)
        ev = evaluate(f"ev{k + 1}", hn)
        iter_secs = time.time() - t0
        entry = dict(iter=k + 1, ckpt=nxt, sha256=sha(nxt), header_sha256=hns, parent=cur, parent_sha256=sha(cur),
                     teacher_sha256=status["teacher_sha256"], agent2_commit=A2_COMMIT, candidate_git_head=git_head,
                     snapshot_tree=status["snapshot_tree"],
                     data=dict(new=dp, new_rows=len(X), new_games=games, recorder_wasm_sha256=rsha, recorder_header_sha256=hs,
                               recorder_wins=wins, recorder_fuel_outs=fo, aggregate_rows=len(XA), iterations=len(parts),
                               maps="poolfresh sorted 121-209", opps=OPPS_REC, fuel="official", cadence="JD_NN_EVENT"),
                     train=tr, eval=ev, command=status["command"], start=started, stop=now(), seconds=round(iter_secs))
        status["iterations"].append(entry)
        save()
        update_manifest(a.run, "checkpoints", [dict(iter=e["iter"], sha256=e["sha256"], parent_sha256=e["parent_sha256"],
                                                    header_sha256=e["header_sha256"], ckpt=e["ckpt"], data=e["data"],
                                                    train_after=e["train"]["after"], eval=e["eval"], start=e["start"],
                                                    stop=e["stop"], command=e["command"],
                                                    source=f"agent2-neural {A2_COMMIT} + {git_head}")
                                               for e in status["iterations"]])
        log(f"iter {k + 1} done in {iter_secs:.0f}s: eval d_score {ev['d_score']} winrate {ev['winrate']} (base {ev['base_winrate']})")
        cur = nxt
        k += 1
    best = max(status["iterations"], key=lambda e: (e["eval"]["d_score"] or -999), default=None)
    status["state"] = "stopped"
    status["stopped"] = now()
    status["best"] = dict(iter=best["iter"], ckpt=best["ckpt"], sha256=best["sha256"], eval=best["eval"]) if best else None
    save()
    update_manifest(a.run, "result", dict(state="stopped", stopped=status["stopped"], best=status["best"],
                                          iter0_eval=status.get("iter0", {}).get("eval")))
    log(f"stopped; best {status['best']}")


if __name__ == "__main__":
    main()
