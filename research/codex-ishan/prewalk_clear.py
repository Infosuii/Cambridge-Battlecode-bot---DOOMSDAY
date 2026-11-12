"""Build and screen the registered one-cast clear before camp movement."""
import argparse
from pathlib import Path

from opening_window_behavior import main as behavior
from probe_cast_before_walk import prepare


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--src", type=Path)
    target.add_argument("--behavior", action="store_true")
    parser.add_argument("--off", action="store_true")
    args = parser.parse_args()
    if args.src:
        prepare(args.src, diagnostic=False, enabled=not args.off)
    else:
        behavior("prewalk-clear", "PREWALK_CLEAR_BUILDS.json", "PREWALK_CLEAR_BEHAVIOR.json", round_limit=300)
