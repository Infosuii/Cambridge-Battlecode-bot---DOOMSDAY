"""Keep the siege ray predicates and use the static opacity bitboard directly."""
import argparse
from pathlib import Path

from bounded_verdict import apply
from pg_stress_tail import HERE, prepare as prepare_tail, verify


def prepare(src, enabled):
    prepare_tail(src, enabled)
    header = src / "common.h"
    data = header.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    header.write_bytes(f"#define CODEX_PG_SIEGE_OPACITY {int(enabled)}".encode() + nl + data)
    apply(src / "bot.cpp", (
        ("                static std::vector<std::uint8_t> opq;\n                static int opq_w = 0, opq_h = 0;",
         """#if CODEX_PG_SIEGE_OPACITY
                // Static terrain stays in its SDK bitboard; every ray asks the same opacity predicate.
                static const bc::bitboard opaque = bc::map::walls() | w.bushes;
                const int opq_w = w.width, opq_h = w.height;
#else
                static std::vector<std::uint8_t> opq;
                static int opq_w = 0, opq_h = 0;"""),
        ("                if (los.size() < w.camps.size()) { los.resize(w.camps.size()); los_ready.resize(w.camps.size(), 0); }",
         "#endif\n                if (los.size() < w.camps.size()) { los.resize(w.camps.size()); los_ready.resize(w.camps.size(), 0); }"),
        ("                auto opaque_at = [&](vec2 m) { return m.x < 0 || m.y < 0 || m.x >= opq_w || m.y >= opq_h || opq[static_cast<std::size_t>(m.y * opq_w + m.x)]; };",
         """#if CODEX_PG_SIEGE_OPACITY
                auto opaque_at = [&](vec2 m) { return !in_bounds(m, opq_w, opq_h) || bit(opaque, m); };
#else
                auto opaque_at = [&](vec2 m) { return m.x < 0 || m.y < 0 || m.x >= opq_w || m.y >= opq_h || opq[static_cast<std::size_t>(m.y * opq_w + m.x)]; };
#endif"""),
        ("#if JD_GOV & 2\n                }\n#endif\n            }\n            if (false)",
         "#if (JD_GOV & 2) && !CODEX_PG_SIEGE_OPACITY\n                }\n#endif\n            }\n            if (false)"),
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
        verify(args.verify, "pg-siege-opacity", None, HERE / "PG-STRESS-TAIL_EXACT_STRESS.json",
               {("pool_604672", "Cassi", 315), ("pool_604770", "Marcella", 458)}, "LARGE_ROSTER_MOVES.json")
