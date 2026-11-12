"""Apply the exact retarget from the measured redundant-arrival probe."""
import argparse
from pathlib import Path
from shutil import copytree

from bounded_verdict import apply
from opening_window_behavior import main as behavior
from probe_redundant_arrival import OBSERVE, bench


def prepare(src, enabled):
    copytree(bench.ROOT / "bots/v92/src", src)
    header = src / "common.h"
    data = header.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    header.write_bytes(f"#define CODEX_REDUNDANT_ARRIVAL {int(enabled)}".encode() + nl + data)
    mark = r'                std::printf("CODEX_REDUNDANT R%d S%d G%d A%d\n", round, slot, best, alt);'
    assert OBSERVE.count(mark) == 1
    change = OBSERVE.replace(mark, "                best = alt;\n                best_need = top[i].need;\n                best_score = top[i].score;")
    anchor = "    return best;\n}\n\n// Follow-up table for one champion alone"
    apply(src / "bot.cpp", ((anchor, "#if CODEX_REDUNDANT_ARRIVAL\n" + change + "#endif\n" + anchor),))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path)
    parser.add_argument("--off", action="store_true")
    args = parser.parse_args()
    if args.src:
        prepare(args.src, not args.off)
    else:
        behavior("redundant-arrival", "REDUNDANT_ARRIVAL_BUILDS.json", "REDUNDANT_ARRIVAL_BEHAVIOR.json")
