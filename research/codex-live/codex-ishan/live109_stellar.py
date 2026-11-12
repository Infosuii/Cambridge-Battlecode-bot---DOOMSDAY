"""Swap two draft priorities on the verified live source, keeping its typed play policy."""
import argparse
from pathlib import Path
from shutil import copytree

import ablate_dev as bench
from bounded_verdict import apply
from engine3_pool import HERE, SDK_ROOT, read


def prepare(target, enabled):
    source = SDK_ROOT / "bots/live109/src"
    identity = read(HERE / "LIVE109_SOURCE_VERIFIED.json")
    assert all(bench.digest(source / name) == expected for name, expected in identity["source_file_hashes"].items())
    copytree(source, target)
    header = target / "common.h"
    header.write_bytes(f"#define CODEX_BALANCE_STELLAR {int(enabled)}\n".encode() + header.read_bytes())
    apply(target / "draft.cpp", (("    for (auto pick : list) {", """    for (auto pick : list) {
#if CODEX_BALANCE_STELLAR
        if (pick == cd::marcella) pick = cd::stellar;
        else if (pick == cd::stellar) pick = cd::marcella;
#endif"""),))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path, required=True)
    parser.add_argument("--off", action="store_true")
    args = parser.parse_args()
    prepare(args.src, not args.off)
