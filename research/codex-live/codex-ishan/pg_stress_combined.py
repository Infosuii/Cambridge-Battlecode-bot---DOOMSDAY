"""Combine the two independently verified stress fixes without retuning."""
import argparse
from pathlib import Path

from pg_ambush_decision import add_reserve
from pg_siege_opacity import prepare as prepare_siege
from pg_stress_tail import HERE, read, verify


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--src", type=Path)
    target.add_argument("--verify", type=Path)
    parser.add_argument("--off", action="store_true")
    args = parser.parse_args()
    assert all(read(HERE / f"{arm}_EXACT_STRESS.json")["pass"] for arm in ("PG-AMBUSH-DECISION", "PG-SIEGE-OPACITY"))
    if args.src:
        prepare_siege(args.src, not args.off)
        add_reserve(args.src)
    else:
        verify(args.verify, "pg-stress-combined", None, HERE / "PG-STRESS-TAIL_EXACT_STRESS.json",
               {("pool_604288", "Marcella", 162), ("pool_604903", "Cassi", 408),
                ("pool_604672", "Cassi", 315), ("pool_604770", "Marcella", 458)}, "LARGE_ROSTER_MOVES.json")
