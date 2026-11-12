"""Where does the simulator's option ranking disagree with the engine? Per labelled scenario (sim_rank.js --dumpto),
regress the engine value on the simulator value plus option features, all de-meaned within the scenario, on one half
of the scenarios; report the fitted corrections and the rank correlation on the other half.

usage: python rank_resid.py dump.jsonl
"""
import json
import sys

import numpy as np

DIRS = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
KIND = ["none", "reset", "damage", "aoe", "cc", "heal", "dash", "shield"]
NAMES = ["sim value", "stay", "step in", "step out", "ends in my range of nearest", "ends adjacent", "enemies that reach me after",
         "attack", "attack then step", "cast damage", "cast cc", "cast aoe", "cast reset", "cast heal", "cast dash", "cast shield",
         "spell before step", "attacks weakest", "hp share x step in", "ranged x step in", "ranged x adjacent"]


def cheb(a, b, c, d):
    return max(abs(a - c), abs(b - d))


def feats(start, acts):
    me = start[0]
    en = [u for u in start if u["team"] != me["team"] and u["alive"]]
    x, y = me["x"], me["y"]
    toks = acts.split(" ") if acts and acts != "pass" else []
    mi = next((i for i, t in enumerate(toks) if t.startswith("move")), -1)
    for t in toks:
        if t.startswith("move"):
            dx, dy = DIRS[int(t[4:])]
            x, y = x + dx, y + dy
    d0 = min((cheb(me["x"], me["y"], e["x"], e["y"]) for e in en), default=9)
    dn = min((cheb(x, y, e["x"], e["y"]) for e in en), default=9)
    rng = max(1, me["range"])
    reach = sum(cheb(x, y, e["x"], e["y"]) <= max(1, e["range"]) + 1 for e in en)
    att = [t for t in toks if t.startswith("attack")]
    ai = next((i for i, t in enumerate(toks) if t.startswith("attack")), -1)
    kinds = [0] * 7
    pre = 0
    for i, t in enumerate(toks):
        if t.startswith("cast"):
            s = int(t[4:].split(":")[0])
            kit = (me.get("kit") or [None, None])[s]
            k = kit["kind"] if kit else 0
            if 1 <= k <= 7:
                kinds[[2, 4, 3, 1, 5, 6, 7].index(k)] = 1
            pre |= mi >= 0 and i < mi
    weakest = 0
    if att and en:
        e = int(att[0][6:])
        weakest = int(e < len(en) and en[e]["hp"] == min(v["hp"] for v in en))
    hpf = me["hp"] / max(1, me["maxhp"])
    return [mi < 0, dn < d0, dn > d0, dn <= rng, dn <= 1, reach, bool(att), ai >= 0 and mi > ai, *kinds, pre, weakest,
            hpf * (dn < d0), (rng > 1) * (dn < d0), (rng > 1) * (dn <= 1)]


def rank(v):
    r = np.empty(len(v))
    r[np.argsort(v, kind="stable")] = np.arange(len(v))
    return r


def corr(a, b):
    a, b = rank(a) - (len(a) - 1) / 2, rank(b) - (len(b) - 1) / 2
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return (a * b).sum() / d if d else np.nan


def main():
    rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
    if len(sys.argv) > 2:  # fight size filter: 1 = 1v1 only
        rows = [r for r in rows if len(r["start"]) == 2 * int(sys.argv[2])]
    data = []
    for r in rows:
        F = np.array([[sv] + [float(f) for f in feats(r["start"], a)] for sv, a in zip(r["sv"], r["acts"])])
        ev = np.array(r["ev"], float)
        # Rank scale (the score is a rank correlation; raw values are dominated by a few deaths).
        n = len(ev)
        F[:, 0] = rank(F[:, 0]) / max(1, n - 1)
        ev = rank(ev) / max(1, n - 1)
        data.append((F, ev))
    for half in (0, 1):
        tr = [d for i, d in enumerate(data) if i % 2 != half]
        te = [d for i, d in enumerate(data) if i % 2 == half]
        X = np.vstack([F - F.mean(0) for F, _ in tr])
        Y = np.concatenate([ev - ev.mean() for _, ev in tr])
        sd = X.std(0) + 1e-9
        w = np.linalg.solve((X / sd).T @ (X / sd) + 50 * np.eye(X.shape[1]), (X / sd).T @ Y) / sd
        base = np.nanmean([corr(F[:, 0], ev) for F, ev in te])
        fit = np.nanmean([corr(F @ w, ev) for F, ev in te])
        only = np.nanmean([corr(F[:, 1:] @ w[1:], ev) for F, ev in te])
        print(f"test half {half}: simulator {base:.3f} | simulator + corrections {fit:.3f} | corrections alone {only:.3f}")
    print("fitted (engine gems per unit of feature, within a scenario; last half's fit):")
    for n_, c in sorted(zip(NAMES, w), key=lambda t: -abs(t[1])):
        print(f"   {n_:32s} {c:+.2f}")


if __name__ == "__main__":
    main()
