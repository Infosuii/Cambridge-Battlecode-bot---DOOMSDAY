"""Physics move scorer for in-fight turns, fitted to engine labels (micro_lab.js). For every option of the probe turn the
action is simulated exactly (order of step / spell / attack / reset, spell kinds, splash, retaliation, kills, stuns)
and the reply is bounded without a behaviour model: every surviving, unstunned enemy's maximum damage on the new tile
next turn (its step or ready dash, attack reach, ready spells). A linear model on these quantities, fitted per scenario
to the engine's option values, ranks the options; on held-out scenarios its pick is compared with the bot's own turn.

usage: python micro_phys.py micro.jsonl [out_header]
"""
import json
import sys

import numpy as np

DIRS = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
NAMES = ["dealt", "kills", "stun", "incoming", "death", "hp_after", "spell_used", "melee_adjacent", "ranged_at_range",
         "ranged_adjacent", "enemies_reach_me", "ally_support", "moved", "closer", "farther", "dealt_x_behind", "incoming_x_low"]
NF = len(NAMES)


def cheb(ax, ay, bx, by):
    return max(abs(ax - bx), abs(ay - by))


def simulate(start, acts):
    me = dict(start[0])
    team = me["team"]
    enemies = [dict(u) for u in start if u["team"] != team and u["alive"]]
    allies = [u for u in start[1:] if u["team"] == team and u["alive"]]
    if not enemies:
        return None
    hp0 = [e["hp"] for e in enemies]
    stunned = [bool(e.get("stun")) for e in enemies]
    my_hp = me["hp"]
    shield = me.get("shield") or 0.0
    kit = me.get("kit") or [None, None]
    used = 0
    enh = bool(me.get("enh"))
    a = acts.split() if acts and acts != "pass" else []
    moved = False

    def hit(i, dmg, can_ret=True):
        nonlocal my_hp
        e = enemies[i]
        if e["hp"] <= 0:
            return
        e["hp"] -= dmg
        if can_ret and e["type"] == 9:  # Ren retaliates 0.2 x focus
            my_hp -= 0.2 * e.get("focus", 100)

    for x in a:
        if x.startswith("move"):
            d = DIRS[int(x[4:])]
            me["x"] += d[0]; me["y"] += d[1]; moved = True
        elif x.startswith("attack"):
            i = int(x[6:])
            if i >= len(enemies):
                continue
            t = enemies[i]
            hit(i, me["str"])
            if enh:
                stunned[i] = True; enh = False
            if me["type"] == 10:  # Varg splash
                for j, o in enumerate(enemies):
                    if j != i and cheb(o["x"], o["y"], t["x"], t["y"]) <= 1:
                        hit(j, me["str"], False)
        elif x.startswith("cast"):
            s, tgt = x[4:].split(":")
            k = kit[int(s)] if int(s) < len(kit) else None
            if not k:
                continue
            used += 1
            val = (k.get("mod") or 0) * me.get("focus", 100)
            kind = k["kind"]
            if kind in (2, 4) and tgt.startswith("enemy"):
                i = int(tgt[5:])
                if i < len(enemies):
                    hit(i, val, False)
                    if kind == 4:
                        stunned[i] = True
            elif kind == 3 and (tgt.startswith("ground") or tgt.startswith("enemy")):
                i = int(tgt[6:] if tgt.startswith("ground") else tgt[5:])
                if i < len(enemies):
                    cx, cy, r = enemies[i]["x"], enemies[i]["y"], int(k.get("radius") or 1)
                    for j, o in enumerate(enemies):
                        if cheb(o["x"], o["y"], cx, cy) <= r:
                            hit(j, val, False)
                            if me["type"] == 0:
                                stunned[j] = True  # Ryth's area stun
            elif kind == 7:
                shield += val
            elif kind == 1 and me["type"] == 7:
                enh = True
    dealt = sum(max(0.0, min(h0, h0 - e["hp"])) / max(1.0, e["maxhp"]) for h0, e in zip(hp0, enemies))
    kills = sum(1 for h0, e in zip(hp0, enemies) if h0 > 0 and e["hp"] <= 0)
    stun = sum(1 for i, e in enumerate(enemies) if stunned[i] and e["hp"] > 0 and not enemies[i].get("stun"))
    # Worst plausible reply on the new tile.
    incoming = 0.0
    reach_me = 0
    for i, e in enumerate(enemies):
        if e["hp"] <= 0 or stunned[i]:
            continue
        d = cheb(me["x"], me["y"], e["x"], e["y"])
        ek = e.get("kit") or [None, None]
        cd = e.get("cd") or [1, 1]
        dash = any(k and k["kind"] == 6 and cd[s] == 0 for s, k in enumerate(ek))
        step = 3 if dash else 1
        dmg = 0.0
        if d <= max(1, e["range"]) + step:
            dmg += e["str"]
            reach_me += 1
        for s, k in enumerate(ek):
            if not k or cd[s] != 0 or k["kind"] not in (2, 3, 4):
                continue
            reach = int(round(k.get("range") or 0)) + (0 if (k.get("attrs", 0) & 1) else 1) + (int(k.get("radius") or 0) if k["kind"] == 3 else 0)
            if d <= reach:
                dmg += (k.get("mod") or 0) * e.get("focus", 100)
        incoming += dmg
    incoming = max(0.0, incoming - shield)
    behind = me["hp"] / max(1, me["maxhp"]) < sum(e["hp"] / max(1, e["maxhp"]) for e in enemies if e["hp"] > 0) / max(1, sum(1 for e in enemies if e["hp"] > 0))
    alive_e = [e for e in enemies if e["hp"] > 0] or enemies
    dn = min(cheb(me["x"], me["y"], e["x"], e["y"]) for e in alive_e)
    d0 = min(cheb(start[0]["x"], start[0]["y"], e["x"], e["y"]) for e in alive_e)
    rng = max(1, me["range"])
    tgt_support = 0.0
    for al in allies:
        if any(cheb(al["x"], al["y"], e["x"], e["y"]) <= max(1, al["range"]) + 1 for e in alive_e):
            tgt_support += 1
    low = my_hp / max(1, me["maxhp"]) < 0.4
    f = np.array([
        dealt, kills, stun, incoming / max(1.0, my_hp), 1.0 if incoming >= my_hp else 0.0, my_hp / max(1, me["maxhp"]),
        used, 1.0 if (rng == 1 and dn <= 1) else 0.0, 1.0 if (rng > 1 and dn == rng) else 0.0, 1.0 if (rng > 1 and dn <= 1) else 0.0,
        reach_me, tgt_support, 1.0 if moved else 0.0, 1.0 if dn < d0 else 0.0, 1.0 if dn > d0 else 0.0,
        dealt if behind else 0.0, incoming / max(1.0, my_hp) if low else 0.0], dtype=np.float64)
    return f


def own_to_acts(start, own_acts):
    """The bot's recorded actions as an option string (move index, cast slot:target, attack enemy index)."""
    me = start[0]
    team = me["team"]
    enemies = [u for u in start if u["team"] != team and u["alive"]]
    allies = [u for u in start[1:] if u["team"] == team and u["alive"]]
    x, y = me["x"], me["y"]
    out = []
    for a in own_acts:
        if a[0] == "move_to":
            d = (a[1] - x, a[2] - y)
            if d in DIRS:
                out.append(f"move{DIRS.index(d)}"); x, y = a[1], a[2]
        elif a[0] == "attack" and a[1] == 1:
            i = next((j for j, e in enumerate(enemies) if e["h"] == a[2]), None)
            if i is not None:
                out.append(f"attack{i}")
        elif a[0] == "cast":
            s, kind, h, cx, cy = a[1], a[2], a[3], a[4], a[5]
            if kind == 1 and h == me["h"]:
                tgt = "self"
            elif kind == 1 and any(e["h"] == h for e in enemies):
                tgt = "enemy" + str(next(j for j, e in enumerate(enemies) if e["h"] == h))
            elif kind == 1 and any(al["h"] == h for al in allies):
                tgt = "ally" + str(next(j for j, al in enumerate(allies) if al["h"] == h))
            elif kind == 0 and enemies:
                tgt = "ground" + str(min(range(len(enemies)), key=lambda j: cheb(enemies[j]["x"], enemies[j]["y"], cx, cy)))
            else:
                continue
            out.append(f"cast{s}:{tgt}")
    return " ".join(out) or "pass"


def main():
    recs = [r for r in (json.loads(l) for l in open(sys.argv[1]) if l.strip()) if "options" in r]
    S = []
    for r in recs:
        X, V = [], []
        for o in r["options"]:
            f = simulate(r["start"], o["acts"])
            if f is None:
                continue
            X.append(f); V.append(o["v"])
        fo = simulate(r["start"], own_to_acts(r["start"], r["own"]["acts"]))
        if len(X) >= 2 and fo is not None:
            S.append((np.stack(X), np.array(V), r["own"]["v"], fo))
    n = len(S)
    te = np.arange(n) % 4 == 0
    # Per-scenario centring: the model ranks options within a scenario.
    Xtr = np.concatenate([s[0] - s[0].mean(0) for s, t in zip(S, te) if not t])
    Ytr = np.concatenate([np.clip(s[1] - s[1].mean(), -40, 40) for s, t in zip(S, te) if not t])
    lam = 1.0
    w = np.linalg.solve(Xtr.T @ Xtr + lam * np.eye(NF), Xtr.T @ Ytr)
    # Override policy: take the scorer's pick only when it predicts a clear gain over the bot's own move.
    for thr in (0.0, 1.0, 2.0, 4.0, 8.0):
        sh, hit, n_over = [], 0, 0
        for s, t in zip(S, te):
            if not t:
                continue
            X, V, own, fo = s
            sc = X @ w
            k = int(np.argmax(sc))
            take = sc[k] - fo @ w > thr
            n_over += take
            v = V[k] if take else own
            sh.append(V.max() - v); hit += V.max() - v < 0.5
        print(f"  override if predicted gain > {thr:3.0f}: within 0.5 {hit / te.sum():.0%}, mean shortfall {np.mean(sh):.2f}, overrides {n_over}/{int(te.sum())}")
    own_short, pick_short, hit_own, hit_pick = [], [], 0, 0
    for s, t in zip(S, te):
        if not t:
            continue
        X, V, own, _fo = s
        best = V.max()
        pick = V[np.argmax(X @ w)]
        own_short.append(best - own); pick_short.append(best - pick)
        hit_own += best - own < 0.5; hit_pick += best - pick < 0.5
    nt = int(te.sum())
    print(f"{n} scenarios ({nt} held out)")
    print(f"  bot's own turn:   within 0.5 of best {hit_own / nt:.0%}, mean shortfall {np.mean(own_short):.2f}, median {np.median(own_short):.2f}")
    print(f"  physics scorer:   within 0.5 of best {hit_pick / nt:.0%}, mean shortfall {np.mean(pick_short):.2f}, median {np.median(pick_short):.2f}")
    print("  weights:", ", ".join(f"{k} {v:+.2f}" for k, v in zip(NAMES, w)))
    if len(sys.argv) > 2:
        with open(sys.argv[2], "w") as fh:
            fh.write("// Physics move scorer weights (agent2/lab/micro_phys.py, fitted to micro_lab.js engine labels).\n#pragma once\nnamespace mphys {\n")
            fh.write(f"inline constexpr float kW[{NF}] = {{{', '.join(f'{x:.6e}f' for x in w)}}}; // {' '.join(NAMES)}\n}}\n")
        print("wrote", sys.argv[2])
    return w


if __name__ == "__main__":
    main()
