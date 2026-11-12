"""Noise ceiling of the duel/micro labels (micro_lab.js with MICRO_EXTRA=2): every distinct option scored on 4
independent variants (v0, v1, vx[0], vx[1]). Split A = mean(v0, v1), B = mean(vx). How often does A's best option
stay within 0.5 of B's best, how well do A and B rank the options, and how big is the bot's shortfall on B when
measured from A's best (a fair, luck-free regret)?

usage: python noise_report.py noise.jsonl
"""
import json
import sys

import numpy as np


def rank_corr(a, b):
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return np.corrcoef(ra, rb)[0, 1] if len(a) > 2 else np.nan


def main():
    rows = [r for r in (json.loads(l) for l in open(sys.argv[1]) if l.strip()) if "options" in r]
    agree, corr, regA, sdiff, n = 0, [], [], [], 0
    for r in rows:
        opts = [o for o in r["options"] if o.get("vx") and None not in o["vx"] and o.get("v1") is not None]
        if len(opts) < 3:
            continue
        A = np.array([(o["v0"] + o["v1"]) / 2 for o in opts])
        B = np.array([sum(o["vx"]) / len(o["vx"]) for o in opts])
        n += 1
        ia = int(np.argmax(A))
        agree += B[ia] >= B.max() - 0.5
        corr.append(rank_corr(A, B))
        regA.append(B.max() - B[ia])
        sdiff.extend(list(np.abs(A - B)))
    print(f"{n} scenarios, options scored on 4 independent variants (A = two, B = the other two)")
    print(f"  A's best option is within 0.5 of B's best in {agree / n:.0%}")
    print(f"  rank correlation of options between A and B: mean {np.nanmean(corr):.2f}, median {np.nanmedian(corr):.2f}")
    print(f"  shortfall of A's best option measured on B: mean {np.mean(regA):.2f}, median {np.median(regA):.2f}")
    print(f"  typical |A - B| for one option: mean {np.mean(sdiff):.2f}, median {np.median(sdiff):.2f} (value; life 25, health bar 12)")


if __name__ == "__main__":
    main()
