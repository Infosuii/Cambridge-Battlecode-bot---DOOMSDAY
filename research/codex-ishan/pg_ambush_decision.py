"""Account for the remaining decision when admitting counter-ambush observation."""
import argparse
from pathlib import Path

from bounded_verdict import apply
from pg_stress_tail import HERE, prepare as prepare_tail, verify


def prepare(src, enabled):
    prepare_tail(src, enabled)
    apply(src / "bot.cpp", (("        if (!rb::fits(rb::kReserve.observe, rb::kTailReserve)) return;",
                            "        if (!rb::fits(rb::kReserve.observe, rb::kReserve.decide + rb::kTailReserve)) return;"),))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--src", type=Path)
    target.add_argument("--verify", type=Path)
    parser.add_argument("--off", action="store_true")
    args = parser.parse_args()
    if args.src:
        prepare(args.src, not args.off)
    else:
        verify(args.verify, "pg-ambush-decision", {"c_walked"}, HERE / "PG-STRESS-TAIL_EXACT_STRESS.json",
               {("pool_604288", "Marcella", 162), ("pool_604903", "Cassi", 408)})
