"""Keep a successful travel dash when there is only tail fuel left."""
import argparse
from pathlib import Path

from bounded_verdict import apply
from pg_dash_followup import verify
from pg_heart_attack import prepare as prepare_heart


def prepare(src, enabled):
    prepare_heart(src, enabled)
    header = src / "common.h"
    data = header.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    header.write_bytes(f"#define CODEX_PG_TRAVEL_TAIL {int(enabled)}".encode() + nl + data)
    apply(src / "bot.cpp", (
        ('''    if (allow_dash) try_dash(field, blocked);
    const std::uint16_t here = fdist(field, pos);
    if (here == 0) return walked;''', '''#if CODEX_PG_TRAVEL_TAIL
    const bool dashed = allow_dash && try_dash(field, blocked);
#else
    if (allow_dash) try_dash(field, blocked);
#endif
    const std::uint16_t here = fdist(field, pos);
    if (here == 0) return walked;
#if CODEX_PG_TRAVEL_TAIL
    if (dashed && rb::turn_guard()) return true;
#endif'''),
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
        verify(args.verify, travel_tail=True)
