"""Reuse the existing lazy siege masks with the validated observation reserve."""
import argparse
from pathlib import Path

from pg_ambush_decision import prepare as prepare_decision
from pg_stress_tail import HERE, verify
from prepare_siege_lazy import add_lazy_masks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--src", type=Path)
    target.add_argument("--verify", type=Path)
    parser.add_argument("--off", action="store_true")
    args = parser.parse_args()
    if args.src:
        prepare_decision(args.src, not args.off)
        add_lazy_masks(args.src, int(not args.off))
    else:
        verify(args.verify, "pg-siege-lazy", None, HERE / "PG-AMBUSH-DECISION_EXACT_STRESS.json",
               {("pool_604672", "Cassi", 315), ("pool_604770", "Marcella", 458)}, "LARGE_ROSTER_MOVES.json")
