"""Golden fixtures for the ported network (FEAT-003, MODEL_ABI.md). Run with the venv python (torch):
  <venv>\\Scripts\\python tools/jd_g5070-1104/nn_golden.py --dump <eval>\\runs\\nn-golden-01 [--pt CKPT] [--min 20]

Checks, exit 0 only if all pass:
  1. feature transport: every JDNDUMP row (features + logits printed by the JD_NN_DUMP build when a pipelined decision
     is published) has the same int16 feature vector as the NR row printed when those features were taken (JD_NN_REC,
     same champion and round), so the pipeline buffer is not clobbered between turns;
  2. WASM vs torch: Agent 2's nn_model.py preprocessing + student forward (CPU, float32) on the dumped features gives
     the same argmax target and behaviour as the in-game network, and the max abs logit error is reported (masked
     pointer slots must be masked in both);
  3. host C++ vs torch: tests/nn_host.cpp (the candidate's nn_infer.h + jd_nn_weights.h, host float path) on the dumped
     rows plus 64 extreme / random full-range int16 rows (saturation) agrees with torch the same way.
"""
import argparse, base64, glob, hashlib, json, os, shutil, subprocess, sys, tempfile, zipfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.dirname(os.path.dirname(HERE))
EVAL = os.path.join(os.path.dirname(WT), "jd-eval")
LAB = os.path.join(EVAL, "a2", "research", "agent2-neural", "rl_workspace", "agent2", "lab")
SRC = os.path.join(WT, "bots", "jd-g5070-1104", "src")
os.environ.setdefault("NN_LAYOUT", "2")
sys.path.insert(0, LAB)
import torch  # noqa: E402
from nn_model import Prep, load, student  # noqa: E402

REL_TOL = 1e-4  # logit tolerance |a - b| / max(1, |b|) vs the exported network (float32 sums in another order)
CKPT_REL_TOL = 5e-3  # vs the unrounded checkpoint (the exporter's 8-digit rounding; argmax must still agree)


def stdout_lines(bundle):
    with zipfile.ZipFile(bundle) as z:
        for m in ("team-a.stdout", "team-b.stdout"):
            if m in z.namelist():
                txt = z.read(m).replace(b"\0", b"\n").decode("utf-8", "replace")
                for l in txt.splitlines():
                    yield m[5], l


def feats(s):
    return np.frombuffer(base64.b64decode(s), np.int16).copy()


def torch_logits(net, X):
    with torch.no_grad():
        o = net(torch.as_tensor(X))
    return o["target"].numpy(), o["behaviour"].numpy(), o["option"].numpy()


def compare(name, T, B, O, tT, tB, tO, report, tol=None):
    """argmax agreement + max abs error on unmasked logits; masked (<= -1e8) slots must be masked in both."""
    mask_ok = bool(np.all((T <= -1e8) == (tT <= -1e8)))
    m = tT > -1e8
    pairs = [(T[m], tT[m]), (B, tB), (O, tO)]
    err = max(float(np.abs(a - b).max()) if a.size else 0.0 for a, b in pairs)
    # relative error (|a - b| / max(1, |b|)): saturated inputs give logits of 1e4+ where float32 order effects scale
    rel = max(float((np.abs(a - b) / np.maximum(1.0, np.abs(b))).max()) if a.size else 0.0 for a, b in pairs)
    at = int((T.argmax(1) == tT.argmax(1)).sum())
    ab = int((B.argmax(1) == tB.argmax(1)).sum())
    tol = REL_TOL if tol is None else tol
    ok = mask_ok and at == len(T) and ab == len(T) and rel <= tol
    report[name] = {"rows": len(T), "target_argmax_agree": at, "behaviour_argmax_agree": ab, "masks_agree": mask_ok,
                    "max_abs_logit_err": err, "max_rel_logit_err": rel, "max_abs_logit": float(max(np.abs(b).max() for _, b in pairs if b.size)), "rel_tol": tol,
                    "pass": ok}
    print(f"{name}: rows {len(T)}, target argmax {at}/{len(T)}, behaviour argmax {ab}/{len(T)}, masks {'ok' if mask_ok else 'DIFFER'}, "
          f"max abs logit err {err:.3e}, max rel err {rel:.3e} -> {'PASS' if ok else 'FAIL'}")
    return ok


def host_cxx():
    cxx = os.environ.get("JD_CXX") or shutil.which("g++") or "C:/msys64/ucrt64/bin/g++.exe"
    return cxx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", required=True)
    ap.add_argument("--pt", default=os.path.join(EVAL, "checkpoints", "student_i2.pt"))
    ap.add_argument("--min", type=int, default=20)
    a = ap.parse_args()
    net = load(student(Prep()), a.pt).eval()
    # nn_export.py writes every float with "%.7e" (8 significant digits); float32 needs 9 to round-trip, so the header
    # differs from the checkpoint by up to ~1 ulp per weight / mean / std, amplified where a std is clamped at 1e-3.
    # `exp` = the network the header actually holds (every parameter and buffer rounded the same way).
    exp = load(student(Prep()), a.pt).eval()
    with torch.no_grad():
        for t in list(exp.parameters()) + list(exp.buffers()):
            v = t.detach().cpu().numpy().ravel()
            t.copy_(torch.as_tensor(np.array([float(f"{x:.7e}") for x in v.tolist()], np.float32).reshape(t.shape)))
    rows, nr = [], {}
    bundles = sorted(glob.glob(os.path.join(a.dump, "games", "*.repl26a")))
    for b in bundles:
        mp = os.path.basename(b)
        for side, l in stdout_lines(b):
            p = l.split(" ")
            if l.startswith("NR ") and len(p) >= 5:
                nr[(mp, side, int(p[2]), int(p[1]))] = p[4]
            elif l.startswith("JDNDUMP ") and len(p) >= 4 + 1 + 11 + 1 + 8 + 1 + 5:
                r, slot = int(p[1]), int(p[2])
                i = p.index("T")
                T = [float(x) for x in p[i + 1:i + 12]]
                B = [float(x) for x in p[i + 13:i + 21]]
                O = [float(x) for x in p[i + 22:i + 27]]
                rows.append((mp, side, slot, r, p[3], T, B, O))
    print(f"{len(bundles)} games, {len(rows)} JDNDUMP rows, {len(nr)} NR rows; checkpoint {a.pt} "
          f"sha256 {hashlib.sha256(open(a.pt, 'rb').read()).hexdigest()}")
    report = {"dump": a.dump, "pt": a.pt, "games": len(bundles), "rows": len(rows)}
    ok = len(rows) >= a.min
    if not ok:
        print(f"FAIL: fewer than {a.min} sampled decisions")
    # 1. feature transport
    same = sum(1 for mp, side, slot, r, fs, *_ in rows if nr.get((mp, side, slot, r)) == fs)
    nomatch = sum(1 for mp, side, slot, r, fs, *_ in rows if (mp, side, slot, r) not in nr)  # NR row dropped (queue full)
    diff = len(rows) - same - nomatch
    report["feature_transport_identical"], report["feature_transport_no_nr_row"], report["feature_transport_differ"] = same, nomatch, diff
    print(f"feature vectors identical to the NR row taken at feature time: {same}/{len(rows)} ({nomatch} without an NR row, {diff} differ)")
    ok &= diff == 0 and same >= a.min
    if rows:
        X = np.stack([feats(x[4]) for x in rows])
        assert X.shape[1] == 500, X.shape
        T = np.array([x[5] for x in rows], np.float32)
        B = np.array([x[6] for x in rows], np.float32)
        O = np.array([x[7] for x in rows], np.float32)
        tT, tB, tO = torch_logits(exp, X)
        ok &= compare("wasm_vs_torch_export", T, B, O, tT, tB, tO, report)
        cT, cB, cO = torch_logits(net, X)
        ok &= compare("wasm_vs_torch_checkpoint", T, B, O, cT, cB, cO, report, CKPT_REL_TOL)
    else:
        X = np.zeros((0, 500), np.int16)
    # 3. host C++ on dumped + extreme rows
    rng = np.random.default_rng(1104)
    ext = [np.zeros(500, np.int16), np.full(500, 32767, np.int16), np.full(500, -32768, np.int16),
           np.where(np.arange(500) % 2 == 1, 32000, -32000).astype(np.int16)]
    for _ in range(60):
        v = rng.integers(-32768, 32768, 500).astype(np.int16)
        for o, n, w in ((60, 5, 12), (120, 8, 16), (248, 10, 22), (468, 4, 8)):
            v[o:o + n * w:w] = rng.integers(0, 3, n)
        ext.append(v)
    XH = np.concatenate([X, np.stack(ext)]).astype(np.int16)
    tmp = tempfile.mkdtemp(prefix="jdgold")
    exe = os.path.join(tmp, "nn_host.exe")
    cxx = host_cxx()
    env = dict(os.environ, PATH=os.path.dirname(cxx) + os.pathsep + os.environ.get("PATH", ""))
    c = subprocess.run([cxx, "-std=c++20", "-O2", "-I", SRC, os.path.join(HERE, "tests", "nn_host.cpp"), "-o", exe],
                       capture_output=True, text=True, env=env)
    if c.returncode:
        print("host build failed", c.stderr[-2000:])
        sys.exit(1)
    fin, fout = os.path.join(tmp, "in.bin"), os.path.join(tmp, "out.bin")
    XH.tofile(fin)
    subprocess.run([exe, fin, fout], check=True, env=env)
    H = np.fromfile(fout, np.float32).reshape(-1, 24)
    hT, hB, hO = H[:, :11], H[:, 11:19], H[:, 19:24]
    sat_finite = bool(np.isfinite(H).all())
    report["host_saturation_finite"] = sat_finite
    print(f"host outputs finite on all {len(XH)} rows (incl. {len(ext)} extreme/random full-range rows): {sat_finite}")
    ok &= sat_finite
    tT2, tB2, tO2 = torch_logits(exp, XH)
    ok &= compare("host_vs_torch_export", hT, hB, hO, tT2, tB2, tO2, report)
    cT2, cB2, cO2 = torch_logits(net, XH)
    ok &= compare("host_vs_torch_checkpoint", hT, hB, hO, cT2, cB2, cO2, report, CKPT_REL_TOL)
    if len(rows):
        ok &= compare("wasm_vs_host", T, B, O, hT[:len(rows)], hB[:len(rows)], hO[:len(rows)], report)
    shutil.rmtree(tmp, ignore_errors=True)
    report["pass"] = bool(ok)
    out = os.path.join(a.dump, "nn_golden.json")
    json.dump(report, open(out, "w"), indent=1)
    print("nn_golden:", "PASS" if ok else "FAIL", "->", out)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
