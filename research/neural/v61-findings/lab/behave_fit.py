"""Learned fight behaviour from real engine games (fight_data.js): what does a champion do in a fight turn?
Classes (as act_model.h): 0 stay, 1 approach, 2 retreat, 3 sidestep, 4 hit+stay, 5 hit+approach/side, 6 hit+retreat,
plus a separate cast yes/no. Features follow tsearch.h enemy_net_class (40 inputs) with the champion-type one-hot filled.
A 40-32-7 tanh network (numpy, Adam), split by game; reports held-out accuracy against the greedy playout policy's
class (bench_sim.js) and the old top-team model, and writes act_model_engine.h for the simulator.

usage: python behave_fit.py fights.jsonl [out_header]
"""
import json
import math
import sys
from collections import Counter

import numpy as np


def cheb(a, b):
    return max(abs(a["x"] - b["x"]), abs(a["y"] - b["y"]))


def features(rec):
    units = rec["units"]
    me = next((u for u in units if u["h"] == rec["actor"]), None)
    if me is None or not me["alive"]:
        return None, None
    f = np.zeros(40, dtype=np.float32)
    if 0 <= me["type"] < 12:
        f[me["type"]] = 1.0
    f[12] = me["hp"] / max(1.0, me["maxhp"])
    f[13] = me["gems"] / 100.0
    f[14] = me["str"] / 100.0
    kit = me.get("kit") or [None, None]
    f[15] = 1.0 if kit[0] and me["cd"][0] == 0 else 0.0
    f[16] = 1.0 if kit[1] and me["cd"][1] == 0 else 0.0
    f[17] = rec["round"] / 1000.0
    near, near_d, reach_me, in_mine = None, 99, 0, 0
    ours, theirs, weakest = me["hp"], 0.0, 1.0
    rng = max(1, me["range"])
    for o in units:
        if o["h"] == me["h"] or not o["alive"]:
            continue
        d = cheb(me, o)
        for k, r in enumerate((3, 5, 8)):
            if d <= r:
                if o["team"] != me["team"]:
                    f[18 + 5 * k] += 1; f[19 + 5 * k] += o["hp"] / 1000.0; f[20 + 5 * k] += o["str"] / 100.0
                else:
                    f[21 + 5 * k] += 1; f[22 + 5 * k] += o["hp"] / 1000.0
        if o["team"] != me["team"]:
            if d < near_d:
                near_d, near = d, o
            reach_me += d <= max(1, o["range"]) + 1
            if d <= rng:
                in_mine += 1
                weakest = min(weakest, o["hp"] / max(1.0, o["maxhp"]))
            if d <= 4:
                theirs += o["hp"]
        elif d <= 4:
            ours += o["hp"]
    if near is None:
        return None, None
    f[33] = near_d / 8.0
    f[34] = near["hp"] / max(1.0, near["maxhp"])
    f[35] = 1.0 if near["range"] > 1 else 0.0
    f[36] = reach_me
    f[37] = in_mine
    f[38] = max(-3.0, min(3.0, math.log((ours + 1.0) / (theirs + 1.0))))
    f[39] = weakest
    return f, (me, near)


def label(rec, me, near):
    acts = [a for a in rec["acts"] if a[-1] == 0]
    if any(a[0] in ("recall", "use_consumable", "submit_gems") for a in acts):
        return None, None
    post = rec["post"][[u["h"] for u in rec["units"]].index(me["h"])]
    if post is None:
        return None, None
    hit = any(a[0] == "attack" for a in acts)
    cast = any(a[0] == "cast" for a in acts)
    moved = post["x"] != me["x"] or post["y"] != me["y"]
    d0 = cheb(me, near)
    d1 = max(abs(post["x"] - near["x"]), abs(post["y"] - near["y"]))
    if not moved:
        c = 4 if hit else 0
    elif d1 < d0:
        c = 5 if hit else 1
    elif d1 > d0:
        c = 6 if hit else 2
    else:
        c = 5 if hit else 3
    return c, int(cast)


def main():
    rows, games = [], []
    for line in open(sys.argv[1]):
        rec = json.loads(line)
        f, mn = features(rec)
        if f is None:
            continue
        c, cast = label(rec, *mn)
        if c is None:
            continue
        rows.append((f, c, cast))
        games.append(rec["game"])
    X = np.stack([r[0] for r in rows]); Y = np.array([r[1] for r in rows]); C = np.array([r[2] for r in rows])
    g_ids = sorted(set(games))
    test_g = set(g_ids[::5])  # every fifth game held out
    te = np.array([g in test_g for g in games]); tr = ~te
    print(f"{len(rows)} turns ({tr.sum()} train / {te.sum()} held out, {len(test_g)} games)")
    print("class mix:", dict(sorted(Counter(Y.tolist()).items())))
    mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-6
    Xn = (X - mu) / sd
    rng = np.random.default_rng(1)
    W1 = rng.normal(0, 0.3, (40, 32)).astype(np.float32); b1 = np.zeros(32, np.float32)
    W2 = rng.normal(0, 0.3, (32, 7)).astype(np.float32); b2 = np.zeros(7, np.float32)
    params = [W1, b1, W2, b2]
    m = [np.zeros_like(p) for p in params]; v = [np.zeros_like(p) for p in params]
    lr, bs, t = 3e-3, 256, 0
    idx = np.where(tr)[0]
    for ep in range(40):
        rng.shuffle(idx)
        for s in range(0, len(idx), bs):
            b = idx[s:s + bs]
            h = np.tanh(Xn[b] @ W1 + b1)
            z = h @ W2 + b2
            z -= z.max(1, keepdims=True)
            p = np.exp(z); p /= p.sum(1, keepdims=True)
            g = p.copy(); g[np.arange(len(b)), Y[b]] -= 1; g /= len(b)
            gW2 = h.T @ g; gb2 = g.sum(0)
            gh = g @ W2.T * (1 - h * h)
            gW1 = Xn[b].T @ gh; gb1 = gh.sum(0)
            t += 1
            for i, (p_, g_) in enumerate(zip(params, [gW1, gb1, gW2, gb2])):
                m[i] = 0.9 * m[i] + 0.1 * g_; v[i] = 0.999 * v[i] + 0.001 * g_ * g_
                p_ -= lr * (m[i] / (1 - 0.9 ** t)) / (np.sqrt(v[i] / (1 - 0.999 ** t)) + 1e-8)
    pred = np.argmax(np.tanh(Xn @ W1 + b1) @ W2 + b2, 1)
    acc = (pred[te] == Y[te]).mean()
    base = (Y[te] == np.bincount(Y[tr]).argmax()).mean()
    move_te = te & np.isin(Y, [1, 2, 3, 5, 6])
    print(f"held-out class accuracy: learned {acc:.1%} | always-most-common {base:.1%}")
    # Movement intent alone (approach / retreat / sidestep / stay) ignoring the hit.
    intent = np.array([0, 1, 2, 3, 0, 1, 2]); acc_i = (intent[pred[te]] == intent[Y[te]]).mean()
    print(f"held-out movement intent accuracy (stay/approach/retreat/side): {acc_i:.1%}; hit yes/no: {((pred[te] >= 4) == (Y[te] >= 4)).mean():.1%}")
    # Per class recall.
    for k, name in enumerate(["stay", "approach", "retreat", "side", "hit+stay", "hit+app/side", "hit+retreat"]):
        sel = te & (Y == k)
        if sel.sum():
            print(f"   {name:13s} n {sel.sum():5d} recall {(pred[sel] == k).mean():.1%}")
    out = sys.argv[2] if len(sys.argv) > 2 else None
    if out:
        fmt = lambda a: ", ".join(f"{x:.6e}f" for x in a)
        with open(out, "w") as fh:
            fh.write("// Learned fight behaviour from real engine games (agent2/lab/behave_fit.py on fight_data.js logs).\n")
            fh.write(f"// Classes: stay, approach, retreat, sidestep, hit+stay, hit+approach/side, hit+retreat. Held-out accuracy {acc:.1%}.\n")
            fh.write("#pragma once\nnamespace act_model {\ninline constexpr int kIn = 40, kHidden = 32, kOut = 7;\n")
            fh.write(f"inline constexpr float kMu[40] = {{{fmt(mu)}}};\ninline constexpr float kSd[40] = {{{fmt(sd)}}};\n")
            fh.write(f"inline constexpr float kB1[32] = {{{fmt(b1)}}};\ninline constexpr float kB2[7] = {{{fmt(b2)}}};\n")
            fh.write("inline constexpr float kW1[kIn][kHidden] = {" + ", ".join("{" + fmt(r) + "}" for r in W1) + "};\n")
            fh.write("inline constexpr float kW2[kHidden][kOut] = {" + ", ".join("{" + fmt(r) + "}" for r in W2) + "};\n")
            fh.write("} // namespace act_model\n")
        print("wrote", out)


if __name__ == "__main__":
    main()
