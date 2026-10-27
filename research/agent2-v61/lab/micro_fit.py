"""Learned in-fight move scorer from engine labels (micro_lab.js). For every scenario, every distinct executed option
(step, spell slot/target/order, attack) has an engine value (6 rounds, lives 25 + health 12, two variants averaged).
Features use only what the bot can compute at its turn. A small network scores (state, option); per held-out
scenario the top-scored option is compared with the bot's own turn and the best option.

usage: python micro_fit.py micro.jsonl [out_header]
"""
import json
import sys

import numpy as np

DIRS = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
NF = 52


def cheb(ax, ay, bx, by):
    return max(abs(ax - bx), abs(ay - by))


def parse(acts):
    a = acts.split() if acts and acts != "pass" else []
    mv, casts, att = None, [], []
    for i, x in enumerate(a):
        if x.startswith("move"):
            mv = int(x[4:])
        elif x.startswith("cast"):
            s, t = x[4:].split(":")
            casts.append((int(s), t, mv is None, i))
        elif x.startswith("attack"):
            att.append(int(x[6:]))
    return mv, casts, att


def option_features(start, acts):
    me = start[0]
    team = me["team"]
    enemies = [u for u in start if u["team"] != team and u["alive"]]
    allies = [u for u in start[1:] if u["team"] == team and u["alive"]]
    if not enemies:
        return None
    mv, casts, att = parse(acts)
    nx, ny = me["x"], me["y"]
    if mv is not None:
        nx, ny = nx + DIRS[mv][0], ny + DIRS[mv][1]
    rng = max(1, me["range"])
    d_old = min(cheb(me["x"], me["y"], e["x"], e["y"]) for e in enemies)
    d_new = min(cheb(nx, ny, e["x"], e["y"]) for e in enemies)
    reach_me = sum(cheb(nx, ny, e["x"], e["y"]) <= max(1, e["range"]) + 1 for e in enemies)
    in_mine = sum(cheb(nx, ny, e["x"], e["y"]) <= rng for e in enemies)
    f = np.zeros(NF, np.float32)
    if 0 <= me["type"] < 12:
        f[me["type"]] = 1
    f[12] = me["hp"] / max(1, me["maxhp"])
    f[13] = 1.0 if rng > 1 else 0.0
    kit = me.get("kit") or [None, None]
    f[14] = 1.0 if kit[0] and me["cd"][0] == 0 else 0.0
    f[15] = 1.0 if kit[1] and me["cd"][1] == 0 else 0.0
    f[16] = len(enemies)
    f[17] = len(allies)
    f[18] = sum(e["hp"] / max(1, e["maxhp"]) for e in enemies) / len(enemies)
    f[19] = 1.0 if mv is not None else 0.0
    f[20] = d_new / 4.0
    f[21] = (d_new - d_old)
    f[22] = reach_me
    f[23] = in_mine
    if allies:
        f[24] = min(cheb(nx, ny, a["x"], a["y"]) for a in allies) / 4.0
    f[25] = len(att)
    if att:
        t = enemies[att[0]] if att[0] < len(enemies) else enemies[0]
        f[26] = t["hp"] / max(1, t["maxhp"])
        f[27] = 1.0 if t["hp"] == min(e["hp"] for e in enemies) else 0.0
        f[28] = me["str"] * len(att) / max(1.0, t["hp"])  # share of its health this turn
    for (s, tgt, pre, _i) in casts[:1]:
        k = kit[s] if s < len(kit) else None
        kind = k["kind"] if k else 0
        if 0 <= kind < 8:
            f[29 + kind] = 1  # 29..36 cast kind one-hot (0 unused)
        f[37] = 1.0 if tgt == "self" else 0.0
        f[38] = 1.0 if tgt.startswith("enemy") else 0.0
        f[39] = 1.0 if tgt.startswith("ground") else 0.0
        f[40] = 1.0 if tgt.startswith("ally") else 0.0
        f[41] = 1.0 if pre else 0.0
        if k and tgt.startswith("enemy"):
            ti = int(tgt[5:])
            if ti < len(enemies):
                f[42] = (k.get("mod", 0) * me["focus"]) / max(1.0, enemies[ti]["hp"])
    f[43] = 1.0 if (len(att) >= 2) else 0.0
    f[44] = 1.0 if (casts and att and casts[0][3] > 0 and not casts[0][2]) else 0.0  # cast after an attack (reset order)
    f[45] = min(e["hp"] / max(1, e["maxhp"]) for e in enemies)
    # Richer context (E32): enemy spells ready, the nearest enemy's reach on the new tile, the health race, the
    # attack target in reach after the step, and the damage enemies that reach the new tile can deal next turn.
    ready = 0
    for e in enemies:
        for s, k in enumerate(e.get("kit") or []):
            if k and k.get("kind") in (2, 3, 4) and (e.get("cd") or [1, 1])[s] == 0:
                ready += 1
    f[46] = ready
    ne = min(enemies, key=lambda e: cheb(nx, ny, e["x"], e["y"]))
    f[47] = 1.0 if cheb(nx, ny, ne["x"], ne["y"]) <= max(1, ne["range"]) else 0.0
    f[48] = me["hp"] / max(1, me["maxhp"]) - sum(e["hp"] / max(1, e["maxhp"]) for e in enemies) / len(enemies)
    if att:
        t = enemies[att[0]] if att[0] < len(enemies) else enemies[0]
        f[49] = 1.0 if cheb(nx, ny, t["x"], t["y"]) <= rng else 0.0
    f[50] = sum(e["str"] for e in enemies if cheb(nx, ny, e["x"], e["y"]) <= max(1, e["range"]) + 1) / max(1.0, me["hp"])
    f[51] = 1.0 if any(cheb(nx, ny, e["x"], e["y"]) <= 1 for e in enemies) else 0.0
    return f


def own_acts(own):
    """The bot's own turn as an acts string comparable to options (move index from its move_to, casts, attacks)."""
    return own


def main():
    recs = [r for r in (json.loads(l) for l in open(sys.argv[1]) if l.strip()) if "options" in r]  # skip abort lines
    S = []
    for r in recs:
        feats, vals, acts = [], [], []
        for o in r["options"]:
            x = option_features(r["start"], o["acts"])
            if x is None:
                continue
            feats.append(x); vals.append(o["v"]); acts.append(o["acts"])
        if len(feats) < 2:
            continue
        S.append((np.stack(feats), np.array(vals), r["own"]["v"], acts, r["size"], r["start"][0]["type"]))
    n = len(S)
    te = np.arange(n) % 4 == 0
    Xtr = np.concatenate([s[0] for s, t in zip(S, te) if not t])
    # Target: value relative to the scenario's mean option (what matters is the ranking within a scenario).
    Ytr = np.concatenate([np.clip(s[1] - s[1].mean(), -40, 40) for s, t in zip(S, te) if not t])
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-6
    rng = np.random.default_rng(3)
    H = 32
    W1 = rng.normal(0, 0.3, (NF, H)); b1 = np.zeros(H); W2 = rng.normal(0, 0.3, H); b2 = 0.0
    ps = [W1, b1, W2]; m = [np.zeros_like(p) for p in ps]; v = [np.zeros_like(p) for p in ps]; t = 0
    Xn = (Xtr - mu) / sd
    for _ in range(40):
        idx = rng.permutation(len(Xn))
        for s in range(0, len(idx), 256):
            b = idx[s:s + 256]
            h = np.tanh(Xn[b] @ W1 + b1); z = h @ W2 + b2
            g = 2 * (z - Ytr[b]) / len(b)
            gW2 = h.T @ g; gh = np.outer(g, W2) * (1 - h * h); gW1 = Xn[b].T @ gh; gb1 = gh.sum(0)
            b2 -= 1e-3 * g.sum()
            t += 1
            for i, (p_, g_) in enumerate(zip(ps, [gW1, gb1, gW2])):
                g_ = g_ + 1e-4 * p_
                m[i] = 0.9 * m[i] + 0.1 * g_; v[i] = 0.999 * v[i] + 0.001 * g_ * g_
                p_ -= 2e-3 * (m[i] / (1 - 0.9 ** t)) / (np.sqrt(v[i] / (1 - 0.999 ** t)) + 1e-8)
    score = lambda X: np.tanh((X - mu) / sd @ W1 + b1) @ W2 + b2
    res = {"own": [], "model": [], "best": [], "mean": []}
    hit_own = hit_model = 0
    for s, t_ in zip(S, te):
        if not t_:
            continue
        X, V, own_v = s[0], s[1], s[2]
        best = V.max()
        pick = V[np.argmax(score(X))]
        res["own"].append(best - own_v); res["model"].append(best - pick); res["mean"].append(best - V.mean())
        hit_own += best - own_v < 0.5; hit_model += best - pick < 0.5
    nt = te.sum()
    print(f"{n} scenarios ({nt} held out). Shortfall from the engine's best option (value; life 25, health bar 12):")
    for k in ("own", "model", "mean"):
        a = np.array(res[k]); print(f"  {k:6s} mean {a.mean():5.2f}  median {np.median(a):5.2f}")
    print(f"  within 0.5 of best: bot's own {hit_own / nt:.0%}, model's pick {hit_model / nt:.0%}")
    if len(sys.argv) > 2:
        fmt = lambda a: ", ".join(f"{x:.6e}f" for x in np.ravel(a))
        with open(sys.argv[2], "w") as fh:
            fh.write("// Learned in-fight move scorer (agent2/lab/micro_fit.py on micro_lab.js engine labels).\n")
            fh.write(f"#pragma once\nnamespace micro_model {{\ninline constexpr int kIn = {NF}, kHidden = {H};\n")
            fh.write(f"inline constexpr float kMu[kIn] = {{{fmt(mu)}}};\ninline constexpr float kSd[kIn] = {{{fmt(sd)}}};\n")
            fh.write(f"inline constexpr float kW1[kIn][kHidden] = {{{', '.join('{' + fmt(r) + '}' for r in W1)}}};\n")
            fh.write(f"inline constexpr float kB1[kHidden] = {{{fmt(b1)}}};\ninline constexpr float kW2[kHidden] = {{{fmt(W2)}}};\n")
            fh.write("} // namespace micro_model\n")
        print("wrote", sys.argv[2])


if __name__ == "__main__":
    main()
