"""E123: DAgger distillation for the deployed bot. The student's first distillation (nn_distill.py on nn_labels_dag3) saw official maps in only 54 of 1,074 games, and
never the states it reaches itself at real fuel. Each round here: the student plays at real fuel (A2_NN_LIVE debug build, as nn_rl4.py: sampled targets, rows logged in debug_block, no
fuel), official maps 65%, vs v92; the rows of all rounds + part of nn_labels_dag3 train it to match the teacher's target head. The student's scores are computed as deployed
(summary from the features behind the summary in force, camps from this turn's), the teacher's from this turn's features: what the teacher would do if it could run every turn.
Rows where the teacher moves off the current target count MW times. Check after each round, release build at real fuel: official 70 x 2 vs v92, v92j1, v92j2 (420 games) and maps_poolfresh (498) vs v92.
usage (project root): [NN_STUDENT=ExT] python -P agent2/lab/nn_dag4.py WORKDIR TEACHER.pt INIT_STUDENT.pt ROUNDS [--games 500] [--epochs 6] [--mw 4] [--base-rows 500000]"""
import json, os, random, shutil, subprocess, sys, time, zipfile, zlib
import numpy as np
import torch
import torch.nn.functional as F

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
A = sys.argv[1:]
WD, TPT, INIT, ROUNDS = os.path.abspath(A[0]), A[1], A[2], int(A[3])
arg = lambda k, d: type(d)(A[A.index(k) + 1]) if k in A else d
GAMES, EPOCHS, MW, BASE_ROWS = arg("--games", 500), arg("--epochs", 6), arg("--mw", 4.0), arg("--base-rows", 500000)
sys.argv = ["nn_rl4", WD, INIT, "0"]
import nn_rl4 as R  # noqa: E402
from nn_model import Prep, load, student, teacher  # noqa: E402

dev = R.dev
BS = 2048
COFF, KCF, FLAG = R.COFF, R.KCF, 21


def log(s):
    print(s, flush=True)
    open(os.path.join(WD, "dag.log"), "a").write(s + "\n")


def export(net, tag):
    pt = os.path.join(WD, f"student_{tag}.pt")
    torch.save(net.state_dict(), pt)
    wh = os.path.join(WD, f"student_w_{tag}.h")
    subprocess.run([sys.executable, "-P", os.path.join(R.LAB, "nn_export.py"), pt, "student", wh], check=True, capture_output=True)
    return wh


def score(jf, side):
    z = R.result(jf, side)
    return 1.0 if z > 0 else 0.5 if z == 0 else 0.0


def evaluate(it, wh):
    """Real fuel, release build, the deployed policy."""
    R.build("nnq_eval", wh, rl=False)
    tag = os.path.join("bench_out", "nnq", f"dag{it}")
    shutil.rmtree(os.path.join(R.V4, tag), ignore_errors=True)
    os.makedirs(os.path.join(R.V4, tag))
    jobs, lines = [], []
    sets = [("maps", o, R.maplist("maps")[:70]) for o in ("v92", "v92j1", "v92j2")] + [("maps_poolfresh", "v92", R.maplist("maps_poolfresh")[:249])]
    for s, o, ms in sets:
        for m in ms:
            for side in "AB":
                a, b = ("nnq_eval", o) if side == "A" else (o, "nnq_eval")
                f = f"{tag}/{s}_{o}_{m[:-7]}_{side}".replace("\\", "/")
                lines.append(f"bots/{a} bots/{b} {s}/{m} {f}.repl26a --statistics {f}.json --json")
                jobs.append((s, o, os.path.join(R.V4, f + ".json"), side))
    R.play(lines, tag, debug=False)
    w = {}
    for s, o, jf, side in jobs:
        try:
            v = score(jf, side)
        except Exception:
            continue
        for k in (s, f"{s}/{o}"):
            w.setdefault(k, [0.0, 0])
            w[k][0] += v
            w[k][1] += 1
    shutil.rmtree(os.path.join(R.V4, tag), ignore_errors=True)
    of, fr = w.get("maps", [0, 1]), w.get("maps_poolfresh", [0, 1])
    log(f"{time.strftime('%H:%M:%S')} CHECK round {it} at real fuel: official {of[0]:.0f}/{of[1]} = {100 * of[0] / max(1, of[1]):.1f}% (" +
        ", ".join(f"{o} {w.get('maps/' + o, [0])[0]:.0f}" for o in ("v92", "v92j1", "v92j2")) + f"), fresh {fr[0]:.0f}/{fr[1]} = {100 * fr[0] / max(1, fr[1]):.1f}%")
    return of[0] / max(1, of[1]), fr[0] / max(1, fr[1])


def rollouts(it, wh):
    """Rows of this round as files: x, xz (int16), chg, official (bool per row)."""
    R.build("nnq", wh, rl=True)
    rng = random.Random(7000 + it)
    games = []
    for _ in range(GAMES):
        s = rng.choices([m for m, _ in R.MAPSETS], [w for _, w in R.MAPSETS])[0]
        games.append((rng.choice(R.TRAIN_MAPS[s]), rng.choice("AB")))
    tag = os.path.join("bench_out", "nnq", f"dagr{it}")
    shutil.rmtree(os.path.join(R.V4, tag), ignore_errors=True)
    os.makedirs(os.path.join(R.V4, tag))
    lines = []
    for k, ((s, m), side) in enumerate(games):
        a, b = ("nnq", "v92") if side == "A" else ("v92", "nnq")
        f = f"{tag}/g{k}".replace("\\", "/")
        lines.append(f"bots/{a} bots/{b} {s}/{m} {f}.repl26a --statistics {f}.json --json")
    t0 = time.time()
    R.play(lines, tag, debug=True)
    X, XZ, CHG, OFF = [], [], [], []
    won = n = 0
    for k, ((s, m), side) in enumerate(games):
        try:
            won += score(os.path.join(R.V4, tag, f"g{k}.json"), side)
            n += 1
            txt = zipfile.ZipFile(os.path.join(R.V4, tag, f"g{k}.repl26a")).read(f"team-{side.lower()}.stdout").replace(b"\0", b"").decode("utf-8", "replace")
        except Exception:
            continue
        for r in R.parse_rows(txt):
            X.append(r["x"]), XZ.append(r["xz"]), CHG.append(r["chg"]), OFF.append(s == "maps")
    shutil.rmtree(os.path.join(R.V4, tag), ignore_errors=True)
    np.save(os.path.join(WD, f"x_{it}.npy"), np.stack(X))
    np.save(os.path.join(WD, f"xz_{it}.npy"), np.stack(XZ))
    np.save(os.path.join(WD, f"chg_{it}.npy"), np.array(CHG, np.int8))
    np.save(os.path.join(WD, f"off_{it}.npy"), np.array(OFF, np.bool_))
    log(f"{time.strftime('%H:%M:%S')} round {it} rollouts: {won:.0f}/{n} won, {len(X)} rows ({sum(CHG)} changes), {time.time() - t0:.0f}s")


def load_gpu(path):
    a = np.load(path, mmap_mode="r")
    parts = [torch.from_numpy(np.array(a[s:s + 100000])).to(dev) for s in range(0, len(a), 100000)]
    return torch.cat(parts)


def moves(x, to):
    c = x[:, COFF + FLAG::KCF][:, :R.KC] == 1
    cur = torch.where(c.any(-1), c.float().argmax(-1), torch.full((len(x),), -1, device=dev))
    return to.argmax(-1) != cur


def teacher_target(T, x):
    return torch.cat([T(x[s:s + 8192])["target"] for s in range(0, len(x), 8192)])


def fidelity(S, T, x, xz, label):
    """Same argmax as the teacher, as deployed (stale summary), weighted back to all turns is left out: changes + kept rows as logged."""
    with torch.no_grad():
        to = teacher_target(T, x)
        so = torch.cat([R.live_logits(S, xz[s:s + 8192], x[s:s + 8192]) for s in range(0, len(x), 8192)])
    same = to.argmax(-1) == so.argmax(-1)
    m = moves(x, to)
    log(f"  {label}: student = teacher on {100 * same.float().mean().item():.1f}% of {len(x)} rows, on teacher's moves {100 * same[m].float().mean().item():.1f}% ({100 * m.float().mean().item():.0f}% of rows)")


def train(S, T, it):
    xs, xzs, ws = [], [], []
    for r in range(1, it + 1):
        x = load_gpu(os.path.join(WD, f"x_{r}.npy"))
        xs.append(x), xzs.append(load_gpu(os.path.join(WD, f"xz_{r}.npy")))
        chg = torch.as_tensor(np.load(os.path.join(WD, f"chg_{r}.npy"))).to(dev)
        ws.append(torch.where(chg > 0, torch.tensor(1.0, device=dev), torch.tensor(float(R.KEEP), device=dev)))
    n_new = sum(len(x) for x in xs)
    if BASE_ROWS:
        b = os.path.join(WD, "base_x.npy")
        x = load_gpu(b)
        xs.append(x), xzs.append(x), ws.append(torch.full((len(x),), float(R.KEEP), device=dev))  # (no stale summary recorded for these)
    X, XZ, W = torch.cat(xs), torch.cat(xzs), torch.cat(ws)
    del xs, xzs, ws
    n = len(X)
    with torch.no_grad():
        TO = teacher_target(T, X)
        W = W * (1.0 + (MW - 1.0) * moves(X, TO).float())
    opt = torch.optim.Adam(S.parameters(), lr=1e-3)
    steps = EPOCHS * (n // BS)
    sch = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=1.5e-3, total_steps=steps, pct_start=0.15)
    t0 = time.time()
    S.train()
    for ep in range(EPOCHS):
        perm = torch.randperm(n, device=dev)
        tot = 0.0
        for s0 in range(0, n - BS + 1, BS):
            idx = perm[s0:s0 + BS]
            so = R.live_logits(S, XZ[idx], X[idx])
            kl = F.kl_div(F.log_softmax(so, -1).clamp_min(-30), F.softmax(TO[idx], -1), reduction="none").sum(-1)
            loss = (kl * W[idx]).sum() / W[idx].sum()
            opt.zero_grad(); loss.backward(); opt.step(); sch.step()
            tot += loss.item()
        log(f"  epoch {ep + 1}: KL {tot / max(1, n // BS):.4f}, {time.time() - t0:.0f}s ({n} rows, {n_new} from play)")
    S.eval()
    fidelity(S, T, X[:n_new], XZ[:n_new], "after training, rows from play")
    del X, XZ, W, TO
    torch.cuda.empty_cache()


if __name__ == "__main__":
    os.makedirs(WD, exist_ok=True)
    T = load(teacher(Prep()), TPT, dev).to(dev).eval()
    for p in T.parameters():
        p.requires_grad_(False)
    S = load(student(Prep()), INIT, dev).to(dev).eval()
    log(f"student parameters {sum(p.numel() for p in S.parameters())}")
    if BASE_ROWS and not os.path.exists(os.path.join(WD, "base_x.npy")):
        d = np.load(os.path.join(R.ROOT, "agent2", "nn_labels_dag3.npz"), mmap_mode="r")
        Xb = d["X"]
        idx = np.sort(np.random.default_rng(0).choice(len(Xb), min(BASE_ROWS, len(Xb)), replace=False))
        np.save(os.path.join(WD, "base_x.npy"), np.asarray(Xb[idx]))
        del Xb, d
    best = evaluate(0, export(S, "0"))
    for it in range(1, ROUNDS + 1):
        rollouts(it, export(S, "cur"))
        x = load_gpu(os.path.join(WD, f"x_{it}.npy")); xz = load_gpu(os.path.join(WD, f"xz_{it}.npy"))
        off = torch.as_tensor(np.load(os.path.join(WD, f"off_{it}.npy"))).to(dev)
        fidelity(S, T, x[off], xz[off], f"round {it} before training, official maps")
        fidelity(S, T, x[~off], xz[~off], f"round {it} before training, generated maps")
        del x, xz, off
        torch.cuda.empty_cache()
        train(S, T, it)
        evaluate(it, export(S, f"{it}"))
