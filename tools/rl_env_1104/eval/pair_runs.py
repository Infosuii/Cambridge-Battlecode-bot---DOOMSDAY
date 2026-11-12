"""Pair candidates from different run_eval runs on identical cells (the engine and our bots are deterministic: 348
cells repeated across five earlier runs all matched exactly), so a reference played once need not be replayed.

usage: python -I tools/rl_env_1104/eval/pair_runs.py --ref runs/.../fixes-01:v114 --cand runs/.../clfs-01:clfs11 [--cand ...]
A cell key covers map hash, side, opponent build hash, build mode, timeout and seed, so cells only pair when the
opponent WASMs are byte-identical.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_eval import paired  # noqa: E402


def load(spec):
    run, name = spec.rsplit(":", 1)
    rep = json.load(open(os.path.join(run, "report.json"), encoding="utf-8"))
    rows = {g["cell"]: g for g in rep["games"] if g["candidate"] == name}
    if not rows:
        raise SystemExit(f"{name} not in {run}")
    return name, rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("--cand", action="append", required=True)
    a = ap.parse_args()
    rn, ref = load(a.ref)
    for spec in a.cand:
        cn, cand = load(spec)
        expected = sorted(set(ref) & set(cand))
        pr = [dict(cell=c, family=cand[c]["family"], candidate_score=cand[c].get("score"),
                   reference_score=ref[c].get("score"), candidate_status=cand[c]["status"],
                   reference_status=ref[c]["status"]) for c in expected]
        v = paired(pr, expected)
        ok = [c for c in expected if cand[c]["status"] == "ok" and ref[c]["status"] == "ok"]
        cs, rs = sum(cand[c]["score"] for c in ok), sum(ref[c]["score"] for c in ok)
        cf, rf = sum(cand[c]["fuel_outs"] for c in ok), sum(ref[c]["fuel_outs"] for c in ok)
        by_opp = {}
        for c in ok:
            o = cand[c]["opponent"]
            d = by_opp.setdefault(o, [0, 0.0, 0.0])
            d[0] += 1
            d[1] += cand[c]["score"]
            d[2] += ref[c]["score"]
        print(f"{cn} - {rn}: {len(ok)}/{len(expected)} cells ({len(set(ref) - set(cand))} ref-only, "
              f"{len(set(cand) - set(ref))} cand-only); score {cs} vs {rs}; {v['status']} delta {v['paired_delta']} "
              f"ci95 {v['ci95']} family-balanced {v.get('family_balanced_delta')}; fuel-outs/game "
              f"{cf / max(1, len(ok)):.2f} vs {rf / max(1, len(ok)):.2f}")
        print("   by opponent: " + ", ".join(f"{o} {d[1]:.1f}-{d[2]:.1f}/{d[0]}" for o, d in sorted(by_opp.items())))


if __name__ == "__main__":
    main()
