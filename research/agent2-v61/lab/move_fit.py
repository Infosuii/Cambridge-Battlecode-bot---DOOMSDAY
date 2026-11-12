"""Movement intent of a 1v1 fighter (micro_lab.js MICRO_TRAJ trajectories): does the real bot step closer to its
opponent, stay, sidestep or step away? A small network on the fighter's situation, trained on the even positions and
scored on the odd ones (the split behave_swap.js --half uses). Writes move_model.h for the simulator (A2_MOVENET).

usage: python move_fit.py traj.jsonl [out_header]
"""
import json
import sys

import numpy as np

NT = 13  # champion type ids 0-12 (12 = Stellar in engine numbering)
KINDS = 8


def cheb(a, b):
    return max(abs(a["x"] - b["x"]), abs(a["y"] - b["y"]))


def feats(me, op):
    """Actor-centric features; the same order is computed in ts::act (tsearch.h)."""
    hpf, ohpf = me["hp"] / max(1, me["maxhp"]), op["hp"] / max(1, op["maxhp"])
    d = cheb(me, op)
    rng, orng = max(1, me["range"]), max(1, op["range"])
    ttk = op["hp"] / max(1.0, me["str"])
    ttd = me["hp"] / max(1.0, op["str"])
    kit = me.get("kit") or [None, None]
    okit = op.get("kit") or [None, None]
    cd = me.get("cd") or [1, 1]
    ocd = op.get("cd") or [1, 1]
    rdy = [1.0 if kit[s] and cd[s] <= 0 else 0.0 for s in (0, 1)]
    ordy = [1.0 if okit[s] and ocd[s] <= 0 else 0.0 for s in (0, 1)]
    kinds = np.zeros(KINDS)
    for s in (0, 1):
        if kit[s] and 0 <= kit[s]["kind"] < KINDS:
            kinds[kit[s]["kind"]] += rdy[s]
    t = np.zeros(NT)
    if 0 <= me["type"] < NT:
        t[me["type"]] = 1
    ot = np.zeros(NT)
    if 0 <= op["type"] < NT:
        ot[op["type"]] = 1
    base = [hpf, ohpf, hpf - ohpf, d / 4.0, d <= rng, d <= orng, d <= orng + 1, rng > 1, orng > 1, rng - orng,
            np.log(ttk + 0.1), np.log(ttd + 0.1), np.log(ttk + 0.1) - np.log(ttd + 0.1), *rdy, *ordy,
            float(bool(me.get("stun"))), float(bool(op.get("stun"))), (me.get("shield") or 0) / 100.0, 1.0]
    return np.concatenate([base, kinds, t, ot]).astype(np.float32)


def label(pre_me, post_me, op):
    d0, d1 = cheb(pre_me, op), cheb(post_me, op)
    if (post_me["x"], post_me["y"]) == (pre_me["x"], pre_me["y"]):
        return 1  # stay
    return 0 if d1 < d0 else 3 if d1 > d0 else 2  # closer / away / side


def samples(rows):
    X, Y, P = [], [], []
    for pi, r in enumerate(rows):
        for o in r["options"]:
            for t in o.get("tr") or []:
                pre, post = t["pre"], t.get("post")
                ai = next((i for i, u in enumerate(pre) if u["h"] == t["actor"]), -1)
                if ai < 0 or not post or not pre[ai]["alive"] or pre[ai].get("stun") or len(pre) != 2:
                    continue
                op = pre[1 - ai]
                if not op["alive"] or cheb(post[ai], pre[ai]) > 1:
                    continue
                X.append(feats(pre[ai], op))
                Y.append(label(pre[ai], post[ai], op))
                P.append(pi)
    return np.array(X), np.array(Y), np.array(P)


def main():
    rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
    rows = [r for r in rows if r.get("options") and len(r["start"]) == 2]
    X, Y, P = samples(rows)
    tr, te = P % 2 == 0, P % 2 == 1
    mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-3
    Xn = (X - mu) / sd
    rng = np.random.default_rng(3)
    D, Hd, C = X.shape[1], 32, 4
    W1 = rng.normal(0, 0.2, (D, Hd)); b1 = np.zeros(Hd); W2 = rng.normal(0, 0.2, (Hd, C)); b2 = np.zeros(C)
    ps = [W1, b1, W2, b2]; m = [np.zeros_like(p) for p in ps]; v = [np.zeros_like(p) for p in ps]; step = 0
    idx = np.where(tr)[0]
    for ep in range(30):
        rng.shuffle(idx)
        for s0 in range(0, len(idx), 256):
            b = idx[s0:s0 + 256]
            h = np.tanh(Xn[b] @ W1 + b1)
            z = h @ W2 + b2
            z -= z.max(1, keepdims=True)
            p = np.exp(z); p /= p.sum(1, keepdims=True)
            g = p.copy(); g[np.arange(len(b)), Y[b]] -= 1; g /= len(b)
            gW2 = h.T @ g; gb2 = g.sum(0)
            gh = (g @ W2.T) * (1 - h * h)
            gW1 = Xn[b].T @ gh; gb1 = gh.sum(0)
            step += 1
            for i, (p_, g_) in enumerate(zip(ps, [gW1, gb1, gW2, gb2])):
                g_ = g_ + 1e-4 * p_
                m[i] = 0.9 * m[i] + 0.1 * g_; v[i] = 0.999 * v[i] + 0.001 * g_ * g_
                p_ -= 3e-3 * (m[i] / (1 - 0.9 ** step)) / (np.sqrt(v[i] / (1 - 0.999 ** step)) + 1e-8)
    pred = (np.tanh(Xn @ W1 + b1) @ W2 + b2).argmax(1)
    names = ["closer", "stay", "side", "away"]
    print(f"{len(Y)} turns ({te.sum()} held out by position). held-out accuracy {np.mean(pred[te] == Y[te]):.1%}; "
          f"majority class {np.bincount(Y[te], minlength=4).max() / te.sum():.1%}")
    for c in range(4):
        sel = te & (Y == c)
        print(f"   real {names[c]:6s} {sel.sum():6d}  predicted right {np.mean(pred[sel] == c):.1%}")
    if len(sys.argv) > 2:
        fmt = lambda a: ", ".join(f"{x:.6e}f" for x in np.ravel(a))
        with open(sys.argv[2], "w") as fh:
            fh.write(f"// Movement intent (closer, stay, side, away) of a 1v1 fighter, agent2/lab/move_fit.py on engine trajectories.\n"
                     f"// Held-out accuracy {np.mean(pred[te] == Y[te]):.1%}.\n#pragma once\nnamespace move_model {{\n")
            fh.write(f"inline constexpr int kIn = {D}, kHidden = {Hd}, kOut = {C};\n")
            fh.write(f"inline constexpr float kMu[kIn] = {{{fmt(mu)}}};\ninline constexpr float kSd[kIn] = {{{fmt(sd)}}};\n")
            fh.write(f"inline constexpr float kW1[kIn][kHidden] = {{{', '.join('{' + fmt(r) + '}' for r in W1)}}};\n")
            fh.write(f"inline constexpr float kB1[kHidden] = {{{fmt(b1)}}};\n")
            fh.write(f"inline constexpr float kW2[kHidden][kOut] = {{{', '.join('{' + fmt(r) + '}' for r in W2)}}};\n")
            fh.write(f"inline constexpr float kB2[kOut] = {{{fmt(b2)}}};\n}}\n")
        print("wrote", sys.argv[2])


if __name__ == "__main__":
    main()
