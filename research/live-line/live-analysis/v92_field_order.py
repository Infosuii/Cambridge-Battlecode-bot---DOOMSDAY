"""Admit deterministic field ordering using the existing full-field allowance."""
import argparse
from pathlib import Path
from shutil import copytree

from bounded_verdict import apply
from large_roster_stress import bench
from v92_travel_scan import verify


def prepare(src, enabled):
    copytree(bench.ROOT / "bots/v92/src", src)
    header = src / "common.h"
    data = header.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    header.write_bytes(f"#define CODEX_V92_FIELD_ORDER {int(enabled)}".encode() + nl + data)
    apply(src / "bot.cpp", (
        ("        if (!w.fields_ready() && quota > 0) w.prepare_field_order();",
         """#if CODEX_V92_FIELD_ORDER
        if (!w.fields_ready() && quota > 0 && w.field_order.empty() && rb::fits(full, rb::kTailReserve))
            w.prepare_field_order();
#else
        if (!w.fields_ready() && quota > 0) w.prepare_field_order();
#endif"""),
    ))


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
        verify(args.verify, round1_only=True)
