"""Next-camp choice (E72): which camp group a champion captures next, as a conditional logit over every group of the map.

Decision points: a champion's capture, bank or respawn; the label is the group it captures next (within 150 rounds,
alive throughout). Captures are gem gains while standing within 1 of a group tile; banks are bag drops to 0 while
alive. Groups and terrain come from mapinfo/<map>.txt ('#' wall, 'o' hole, 'A' altar block walking).

Features per candidate group (the same can be computed by the bot):
  dist    log(1 + walking distance from the champion)
  gems    log(1 + gems)
  gold    gold / 100
  wait    rounds the group still respawns after we would arrive / 20 (0 = ready on arrival)
  side    (enemy-spawn walk - own-spawn walk) / 10 (positive = our side)
  mid     group between 35% and 65% of the way from our spawn to theirs
  ally5   living teammates within 5 of the group
  enemy5  living enemies within 5 of the group
  closer  a living teammate is nearer to the group (walking)
  bagdist own bag / 100 x dist
  hurtE   (1 - health share) x enemy5
  lateside round / 1000 x side

usage: python -I tools/next_camp.py DIR[:name] [DIR[:name] ...]   (fits each set, prints coefficients and held-out accuracy)
"""
import json
import math
import site
import sys
from collections import deque
from pathlib import Path

sys.path.append(site.getusersitepackages())
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
NAMES = ["dist", "gems", "gold", "wait", "side", "mid", "ally5", "enemy5", "closer", "bagdist", "hurtE", "lateside"]
NB = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
INF = 10 ** 6


def load_map(name):
    lines = [l.rstrip("\n") for l in open(ROOT / "mapinfo" / f"{name}.txt")]
    groups = []
    for l in lines:
        if not l.startswith("GROUP"):
            continue
        head, _, mons = l.partition(":")
        kv = dict(x.split("=") for x in head.split()[2:] if "=" in x)
        tiles = []
        for tok in mons.split():
            p = tok[tok.index("(") + 1:tok.index(")")].split(",")
            tiles.append((int(p[0]), int(p[1])))
        groups.append({"gems": int(kv["gems"]), "gold": int(kv["gold"]), "resp": int(kv["resp"]), "tiles": tiles})
    grid = [r for r in lines if r and not r.startswith(("MAP", "GROUP"))]
    return grid, groups


def bfs(grid, starts):
    H, W = len(grid), len(grid[0])
    dist = [[INF] * W for _ in range(H)]
    q = deque()
    for x, y in starts:
        if 0 <= x < W and 0 <= y < H:
            dist[y][x] = 0
            q.append((x, y))
    while q:
        x, y = q.popleft()
        for dx, dy in NB:
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H and grid[ny][nx] not in "#oA" and dist[ny][nx] == INF:
                dist[ny][nx] = dist[y][x] + 1
                q.append((nx, ny))
    return dist


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def game_decisions(mf):
    meta = json.loads(mf.read_text())
    name = meta["map"]
    if not (ROOT / "mapinfo" / f"{name}.txt").exists():
        return []
    pick = {int(k) for k, v in meta["sides"].items() if v.get("top")}
    if not pick:
        return []
    grid, groups = load_map(name)
    H, W = len(grid), len(grid[0])
    rounds = [r for r in json.loads(mf.with_name(mf.name.replace(".meta.json", ".json")).read_text())["rounds"] if r["champs"]]
    if len(rounds) < 50:
        return []
    spawns = {"1": [], "2": []}
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch in spawns:
                spawns[ch].append((x, y))
    if not spawns["1"] or not spawns["2"]:
        return []
    first = rounds[0]
    near = {}
    for c in first["champs"]:
        if c["x"] >= 0:
            near.setdefault(c["team"], []).append(min(cheb((c["x"], c["y"]), s) for s in spawns["1"]))
    if len(near) < 2:
        return []
    t1 = min(near, key=lambda t: sum(near[t]) / len(near[t]))
    spawn_of = {t1: spawns["1"], 1 - t1: spawns["2"]}
    gd = [bfs(grid, g["tiles"]) for g in groups]
    # Walking distance from a tile to a group: its field there (tiles next to blocked camp tiles included).
    def gdist(gi, p):
        x, y = p
        return gd[gi][y][x] if 0 <= x < W and 0 <= y < H else INF
    sp = {t: [min(gd[gi][y][x] for x, y in spawn_of[t]) for gi in range(len(groups))] for t in (0, 1)}
    # Events per champion; group captures by anyone (for respawn timers).
    seq = {}
    last_cap = [-10 ** 6] * len(groups)
    caps_by_round = []
    prev = {}
    for r in rounds:
        for c in r["champs"]:
            key = (c["team"], c["h"])
            p = prev.get(key)
            ev = None
            if p is not None:
                if c["alive"] and not p["alive"]:
                    ev = ("respawn", None)
                elif c["alive"] and p["alive"] and c["gems"] > p["gems"]:
                    pos = (c["x"], c["y"])
                    best, bd = None, 2
                    for gi, g in enumerate(groups):
                        d = min(cheb(pos, t) for t in g["tiles"])
                        if d < bd:
                            best, bd = gi, d
                    if best is not None:
                        ev = ("capture", best)
                        caps_by_round.append((r["round"], best))
                elif c["alive"] and p["alive"] and p["gems"] > 0 and c["gems"] == 0:
                    ev = ("bank", None)
            if ev:
                seq.setdefault(key, []).append((r["round"], ev[0], ev[1]))
            prev[key] = c
    caps_by_round.sort()
    by_round = {r["round"]: r for r in rounds}
    out = []
    for (team, h), evs in seq.items():
        if team not in pick:
            continue
        for (r0, k0, g0), (r1, k1, g1) in zip(evs, evs[1:]):
            if k1 != "capture" or r1 - r0 > 150 or r0 < 5 or (k0 == "capture" and g0 == g1 and r1 - r0 < 3):
                continue
            st = by_round.get(r0 + 1) or by_round.get(r0)
            if not st:
                continue
            me = next((c for c in st["champs"] if c["team"] == team and c["h"] == h), None)
            if not me or not me["alive"]:
                continue
            last_cap = [-10 ** 6] * len(groups)
            for rr, gi in caps_by_round:
                if rr > r0:
                    break
                last_cap[gi] = rr
            pos = (me["x"], me["y"])
            allies = [c for c in st["champs"] if c["team"] == team and c["h"] != h and c["alive"]]
            enemies = [c for c in st["champs"] if c["team"] != team and c["alive"]]
            hpf = me["hp"] / max(1.0, me["mhp"])
            rows = []
            for gi, g in enumerate(groups):
                d = gdist(gi, pos)
                if d >= INF:
                    d = 999
                dA, dE = sp[team][gi], sp[1 - team][gi]
                dA = min(dA, 999)
                dE = min(dE, 999)
                avail = last_cap[gi] + g["resp"]
                wait = max(0, avail - (r0 + d))
                a5 = sum(1 for a in allies if min(cheb((a["x"], a["y"]), t) for t in g["tiles"]) <= 5)
                e5 = sum(1 for e in enemies if min(cheb((e["x"], e["y"]), t) for t in g["tiles"]) <= 5)
                closer = 1.0 if any(gdist(gi, (a["x"], a["y"])) < d for a in allies) else 0.0
                side = (dE - dA) / 10.0
                ratio = dA / max(1, dA + dE)
                rows.append([math.log1p(d), math.log1p(g["gems"]), g["gold"] / 100.0, wait / 20.0, side, 1.0 if 0.35 <= ratio <= 0.65 else 0.0,
                             a5, e5, closer, me["gems"] / 100.0 * d / 10.0, (1 - hpf) * e5, r0 / 1000.0 * side])
            out.append((np.array(rows, dtype=np.float32), g1, mf.name))
    return out


def fit(data, l2=1e-3, iters=400):
    F = data[0][0].shape[1]
    w = np.zeros(F)
    for it in range(iters):
        g = np.zeros(F)
        Hm = np.zeros((F, F))
        ll = 0.0
        for X, y, _ in data:
            u = X @ w
            u -= u.max()
            p = np.exp(u)
            p /= p.sum()
            ll += math.log(max(p[y], 1e-12))
            mu = p @ X
            g += X[y] - mu
            Hm -= (X * p[:, None]).T @ X - np.outer(mu, mu)
        g -= l2 * len(data) * w
        Hm -= l2 * len(data) * np.eye(F)
        step = np.linalg.solve(Hm, g)
        w -= step
        if np.abs(step).max() < 1e-6:
            break
    se = np.sqrt(np.maximum(np.diag(np.linalg.inv(-Hm)), 0))
    return w, se, ll / len(data)


def acc(data, w):
    return sum(1 for X, y, _ in data if int(np.argmax(X @ w)) == y) / max(1, len(data))


def main():
    sets = []
    for a in sys.argv[1:]:
        d, _, name = a.partition(":")
        name = name or Path(d).name
        data = []
        for mf in sorted(Path(d).glob("*.meta.json")):
            data += game_decisions(mf)
        sets.append((name, data))
    for name, data in sets:
        games = sorted({g for _, _, g in data})
        test_games = set(games[::5])
        tr = [x for x in data if x[2] not in test_games]
        te = [x for x in data if x[2] in test_games]
        w, se, ll = fit(tr)
        base = np.zeros(len(NAMES))
        base[0] = -1.0  # nearest group
        valb = np.zeros(len(NAMES))
        valb[0], valb[1], valb[3] = -1.0, 1.0, -1.0
        ncand = np.mean([X.shape[0] for X, _, _ in data]) if data else 0
        print(f"== {name}: {len(data)} decisions ({len(tr)} train / {len(te)} test) from {len(games)} games, {ncand:.1f} groups each")
        print(f"   held-out top-1: model {acc(te, w):.3f} | nearest {acc(te, base):.3f} | gems-dist-wait {acc(te, valb):.3f} | train ll {ll:.3f}")
        print("   " + "  ".join(f"{n} {wi:+.2f}({s:.2f})" for n, wi, s in zip(NAMES, w, se)))
        np.save(ROOT / "agent2" / "lab" / f"nextcamp_w_{name}.npy", w)


if __name__ == "__main__":
    main()
