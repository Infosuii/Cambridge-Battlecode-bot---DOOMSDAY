"""Per-turn behaviour model from recorded engine fights (replay_lab.js trajectories): which tile does a champion end
its turn on? Each of the 9 candidate tiles (stay + 8 steps) gets features the bot's movement depends on; a small
network scores them (softmax over the legal tiles), trained on the real choices. Held-out tile accuracy is compared
with the simulator's greedy policy (45.9% on the 200-fight set).

usage: python behave2_fit.py traj.jsonl terrain.json [out_header]
"""
import json
import sys

import numpy as np

DIRS = [(0, 0), (-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
NC = 22  # candidate features
NX = 18  # context features (type one-hot 12, hp, ranged, ready0, ready1, n enemies, n allies)


def cheb(ax, ay, bx, by):
    return max(abs(ax - bx), abs(ay - by))


def samples(rec, terr):
    W, H, T = terr["W"], terr["H"], terr["t"]
    tile = lambda x, y: 1 if (x < 0 or y < 0 or x >= W or y >= H) else T[y * W + x]
    out = []
    for t in rec["traj"]:
        pre, post = t["pre"], t.get("post")
        ai = next((i for i, u in enumerate(pre) if u["h"] == t["actor"]), -1)
        if ai < 0 or not post or not pre[ai]["alive"] or pre[ai].get("stun"):
            continue
        acts = [a for a in t["acts"] if a[-1] == 0]
        if any(a[0] in ("recall", "submit_gems", "use_consumable_with_result") for a in acts):
            continue
        if any(a[0].startswith("cast") and a[2] == 0 for a in acts) and False:
            continue
        me = pre[ai]
        enemies = [u for u in pre if u["team"] != me["team"] and u["alive"]]
        allies = [u for j, u in enumerate(pre) if j != ai and u["team"] == me["team"] and u["alive"]]
        if not enemies:
            continue
        rx, ry = post[ai]["x"], post[ai]["y"]
        if cheb(rx, ry, me["x"], me["y"]) > 1:
            continue  # dashes and teleports are not in the 9-tile set
        occ = {(u["x"], u["y"]) for u in pre if u["alive"] and u is not me}
        rng = max(1, me["range"])
        tgt = min(enemies, key=lambda e: e["hp"] / max(1.0, me["str"]))
        d0 = min(cheb(me["x"], me["y"], e["x"], e["y"]) for e in enemies)
        a0 = min((cheb(me["x"], me["y"], a["x"], a["y"]) for a in allies), default=0)
        C = np.zeros((9, NC), np.float32)
        legal = np.zeros(9, bool)
        label = -1
        for k, (dx, dy) in enumerate(DIRS):
            x, y = me["x"] + dx, me["y"] + dy
            ok = k == 0 or (tile(x, y) != 1 and (x, y) not in occ)
            legal[k] = ok
            if not ok:
                continue
            if (x, y) == (rx, ry):
                label = k
            dn = min(cheb(x, y, e["x"], e["y"]) for e in enemies)
            reach = [e for e in enemies if cheb(x, y, e["x"], e["y"]) <= max(1, e["range"]) + 1]
            inmine = [e for e in enemies if cheb(x, y, e["x"], e["y"]) <= rng]
            an = min((cheb(x, y, a["x"], a["y"]) for a in allies), default=0)
            walls = sum(tile(x + i, y + j) == 1 for i in (-1, 0, 1) for j in (-1, 0, 1) if i or j)
            C[k] = [k == 0, dn / 8.0, dn - d0, dn == rng, dn < rng, dn > rng, len(reach), sum(e["str"] for e in reach) / max(1.0, me["hp"]),
                    len(inmine), cheb(x, y, tgt["x"], tgt["y"]) <= rng, cheb(x, y, tgt["x"], tgt["y"]) - cheb(me["x"], me["y"], tgt["x"], tgt["y"]),
                    an / 8.0, an - a0, tile(x, y) == 2, walls / 8.0, dn <= 1,
                    (dn - d0) * (me["hp"] / max(1, me["maxhp"])), (dn - d0) * (rng > 1), len(reach) * (me["hp"] / max(1, me["maxhp"])),
                    cheb(x, y, tgt["x"], tgt["y"]) <= rng and rng > 1, abs(dx) + abs(dy) == 2, 1.0]
        if label < 0:
            continue
        kit = me.get("kit") or [None, None]
        cd = me.get("cd") or [1, 1]
        ctx = np.zeros(NX, np.float32)
        if 0 <= me["type"] < 12:
            ctx[me["type"]] = 1
        ctx[12] = me["hp"] / max(1, me["maxhp"]); ctx[13] = rng > 1; ctx[14] = bool(kit[0]) and cd[0] == 0; ctx[15] = bool(kit[1]) and cd[1] == 0
        ctx[16] = len(enemies); ctx[17] = len(allies)
        out.append((C, ctx, legal, label))
    return out


def main():
    recs = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
    # The host is deterministic: a replayed scenario records the identical fight. Keep one copy, or held-out fights
    # leak from training (2,000 recorded = 873 unique; the leak read 78.7% for a model that holds out at ~54%).
    seen = set()
    recs = [r for r in recs if not (k := json.dumps([r["map"], r["traj"][0]["pre"], [t["acts"] for t in r["traj"]]], sort_keys=True)) in seen and not seen.add(k)]
    terr = json.load(open(sys.argv[2]))
    keep = float(__import__("os").environ.get("BEHAVE_TRAIN_FRAC", "1"))  # learning curve: share of training fights kept
    S = []
    for i, r in enumerate(recs):
        if i % 5 and (i * 0.618) % 1 >= keep:
            continue
        for s in samples(r, terr[r["map"]]):
            S.append((i,) + s)
    n = len(S)
    te = np.array([s[0] % 5 == 0 for s in S])
    # Input per candidate: candidate features + context + candidate x context interactions (via the hidden layer).
    X = np.stack([np.concatenate([s[1], np.repeat(s[2][None, :], 9, 0)], 1) for s in S])  # n x 9 x (NC + NX)
    L = np.stack([s[3] for s in S]); Y = np.array([s[4] for s in S])
    D = X.shape[2]
    mu = X[~te][L[~te]].mean(0); sd = X[~te][L[~te]].std(0) + 1e-3
    Xn = (X - mu) / sd
    rng = np.random.default_rng(7)
    Hd = 48
    W1 = rng.normal(0, 0.2, (D, Hd)); b1 = np.zeros(Hd); W2 = rng.normal(0, 0.2, Hd)
    ps = [W1, b1, W2]; m = [np.zeros_like(p) for p in ps]; v = [np.zeros_like(p) for p in ps]; t = 0
    tr = np.where(~te)[0]
    for ep in range(40):
        rng.shuffle(tr)
        for s0 in range(0, len(tr), 128):
            b = tr[s0:s0 + 128]
            h = np.tanh(Xn[b] @ W1 + b1)          # B x 9 x H
            z = h @ W2                             # B x 9
            z = np.where(L[b], z, -1e9)
            z -= z.max(1, keepdims=True)
            p = np.exp(z); p /= p.sum(1, keepdims=True)
            g = p.copy(); g[np.arange(len(b)), Y[b]] -= 1; g /= len(b)
            gW2 = np.einsum("bkh,bk->h", h, g)
            gh = g[:, :, None] * W2[None, None, :] * (1 - h * h)
            gW1 = np.einsum("bkd,bkh->dh", Xn[b], gh); gb1 = gh.sum((0, 1))
            t += 1
            for i, (p_, g_) in enumerate(zip(ps, [gW1, gb1, gW2])):
                g_ = g_ + 1e-4 * p_
                m[i] = 0.9 * m[i] + 0.1 * g_; v[i] = 0.999 * v[i] + 0.001 * g_ * g_
                p_ -= 3e-3 * (m[i] / (1 - 0.9 ** t)) / (np.sqrt(v[i] / (1 - 0.999 ** t)) + 1e-8)
    z = np.where(L, np.tanh(Xn @ W1 + b1) @ W2, -1e9)
    pred = z.argmax(1)
    acc = (pred[te] == Y[te]).mean()
    base_stay = (Y[te] == 0).mean()
    print(f"{n} turns ({te.sum()} held out, by fight). Tile chosen: learned {acc:.1%} | always stay {base_stay:.1%} | simulator greedy ~46%")
    if len(sys.argv) > 3:
        fmt = lambda a: ", ".join(f"{x:.6e}f" for x in np.ravel(a))
        with open(sys.argv[3], "w") as fh:
            fh.write(f"// Learned tile choice (agent2/lab/behave2_fit.py on engine trajectories). Held-out accuracy {acc:.1%}.\n#pragma once\nnamespace tile_model {{\n")
            fh.write(f"inline constexpr int kIn = {D}, kHidden = {Hd};\n")
            fh.write(f"inline constexpr float kMu[kIn] = {{{fmt(mu)}}};\ninline constexpr float kSd[kIn] = {{{fmt(sd)}}};\n")
            fh.write(f"inline constexpr float kW1[kIn][kHidden] = {{{', '.join('{' + fmt(r) + '}' for r in W1)}}};\n")
            fh.write(f"inline constexpr float kB1[kHidden] = {{{fmt(b1)}}};\ninline constexpr float kW2[kHidden] = {{{fmt(W2)}}};\n}}\n")
        print("wrote", sys.argv[3])


if __name__ == "__main__":
    main()
