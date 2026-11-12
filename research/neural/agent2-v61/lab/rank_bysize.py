"""Rank correlation with the engine per fight size (1v1 / 2v2), for sim_rank.js --dumpto files.

usage: python rank_bysize.py dump.jsonl [...]
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from rank_resid import corr  # noqa: E402

for f in sys.argv[1:]:
    rows = [json.loads(l) for l in open(f) if l.strip()]
    out = []
    for sz in (1, 2):
        c = [corr(np.array(r["sv"]), np.array(r["ev"])) for r in rows if len(r["start"]) == 2 * sz]
        out.append(f"{sz}v{sz} {np.nanmean(c):.3f} (n={len(c)})")
    allc = [corr(np.array(r["sv"]), np.array(r["ev"])) for r in rows]
    print(f"{os.path.basename(f):28s} all {np.nanmean(allc):.3f} | " + " | ".join(out))
