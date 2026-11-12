"""Transfer only the exact bounded target selector to a copy of the live source."""
import argparse
from pathlib import Path
from shutil import copytree

import ablate_dev as bench
from cpg_greedy_full import apply_full
from engine3_pool import HERE, SDK_ROOT, read


def prepare(target, enabled):
    source = SDK_ROOT / "bots/live109/src"
    identity = read(HERE / "LIVE109_SOURCE_VERIFIED.json")
    assert all(bench.digest(source / name) == expected for name, expected in identity["source_file_hashes"].items())
    copytree(source, target)
    apply_full(target, enabled)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path, required=True)
    parser.add_argument("--off", action="store_true")
    args = parser.parse_args()
    prepare(args.src, not args.off)
