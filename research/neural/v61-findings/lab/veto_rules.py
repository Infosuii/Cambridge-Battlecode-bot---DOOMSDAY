"""Simulator as a veto on the bot's own turn (1v1 labels): keep the bot's move unless the simulator rates another
option better by more than a threshold. Scored on engine labels (loss = best option's value - chosen option's value).
Threshold picked on one half of the positions, confirmed on the other.

usage: python veto_rules.py dump.jsonl   (sim_rank.js --dumpto with own_acts / own_sv)
"""
import json
import sys

import numpy as np

SAME_TILE = "same tile"  # variant: only switch among options that end on the bot's own tile (keeps its positioning)


def tile(acts):
    return next((t for t in (acts or "").split(" ") if t.startswith("move")), "stay")


def choose(r, thr, mode):
    sv = np.array(r["sv"])
    cand = range(len(sv))
    if mode == SAME_TILE:
        cand = [j for j in cand if tile(r["acts"][j]) == tile(r["own_acts"])]
        if not cand:
            return r["own_ev"]
    j = max(cand, key=lambda j: sv[j])
    return r["ev"][j] if sv[j] - r["own_sv"] > thr else r["own_ev"]


def score(rows, thr, mode):
    loss = np.array([r["best"] - choose(r, thr, mode) for r in rows])
    switched = np.mean([choose(r, thr, mode) != r["own_ev"] for r in rows])
    return loss.mean(), np.mean(loss < 0.5), np.mean(loss > 15), switched


def main():
    rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
    rows = [r for r in rows if len(r["start"]) == 2 and r["own_acts"]]
    halves = [rows[0::2], rows[1::2]]
    print(f"{len(rows)} 1v1 positions (bot did not recall)")
    print(f"{'rule':34s} {'mean loss':>9s} {'near-best':>9s} {'deaths':>7s} {'switched':>8s}")
    show = lambda name, s: print(f"{name:34s} {s[0]:9.2f} {s[1]:9.0%} {s[2]:7.1%} {s[3]:8.0%}")
    show("bot's own move", score(rows, 1e9, "any"))
    show("simulator's top pick always", score(rows, -1e9, "any"))
    thrs = [0, 0.5, 1, 2, 3, 5, 8, 12, 16, 20, 25]
    for mode in ("any", SAME_TILE):
        for thr in thrs:
            show(f"veto ({mode}), switch if sim gain > {thr}", score(rows, thr, mode))
    print("\nheld out (threshold chosen on the other half by mean loss):")
    for mode in ("any", SAME_TILE):
        for h in (0, 1):
            tr, te = halves[1 - h], halves[h]
            thr = min(thrs, key=lambda t: score(tr, t, mode)[0])
            b, v = score(te, 1e9, mode), score(te, thr, mode)
            print(f"  {mode:9s} half {h}: threshold {thr:>4} | bot loss {b[0]:.2f} deaths {b[2]:.1%} | veto loss {v[0]:.2f} deaths {v[2]:.1%} near-best {b[1]:.0%} -> {v[1]:.0%} | switched {v[3]:.0%}")


if __name__ == "__main__":
    main()
