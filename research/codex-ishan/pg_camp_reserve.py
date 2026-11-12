"""Leave basic-attack fuel when an optional camp dash cannot fit."""
import argparse
from pathlib import Path

from bounded_verdict import apply
from pg_camp_strike import verify
from pg_siege_resume import prepare as prepare_resume


def prepare(src, enabled):
    prepare_resume(src, enabled)
    header = src / "common.h"
    data = header.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    header.write_bytes(f"#define CODEX_PG_CAMP_RESERVE {int(enabled)}".encode() + nl + data)
    apply(src / "bot.cpp", (("        int best_hits = 0, best_home = kUnreach;", """#if CODEX_PG_CAMP_RESERVE
        if (rb::turn_guard()) return false;
#endif
        int best_hits = 0, best_home = kUnreach;"""),))


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
        verify(args.verify, "pg-camp-reserve")
