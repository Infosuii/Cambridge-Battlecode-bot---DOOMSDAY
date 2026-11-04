"""Reuse chunk addresses during the fixed travel-dash landing scan."""
import argparse
from pathlib import Path

from bounded_verdict import apply
from pg_dash_followup import verify
from pg_travel_tail import prepare as prepare_travel


def prepare(src, enabled):
    prepare_travel(src, enabled)
    header = src / "common.h"
    data = header.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    header.write_bytes(f"#define CODEX_PG_TRAVEL_SCAN {int(enabled)}".encode() + nl + data)
    apply(src / "bot.cpp", (
        ('''        for (int dx = -2; dx <= 2; ++dx)
            for (int dy = -2; dy <= 2; ++dy) {
                const vec2 q{pos.x + dx, pos.y + dy};
                if (!in_bounds(q, w.width, w.height) || bit(blocked, q)) continue;
                const std::uint16_t dq = fdist(field, q);
                if (dq + 1 < best_d) {
                    best_d = dq;
                    best = q;
                }
            }
        if (best == pos) return false;''',
         '''#if CODEX_PG_TRAVEL_SCAN
        const auto& layout = d::layout();
        const auto* distances = field.ptr();
        const auto* obstructions = blocked.ptr();
        const int min_x = std::max(pos.x - 2, 0), max_x = std::min(pos.x + 2, w.width - 1);
        const int min_y = std::max(pos.y - 2, 0), max_y = std::min(pos.y + 2, w.height - 1);
        for (int x = min_x; x <= max_x; ++x) {
            const int chunk_x = x >> 3;
            const int local_x = x & 7;
            for (int y = min_y; y <= max_y; ++y) {
                const int chunk_y = y >> 3;
                const int cell = ((y & 7) << 3) + local_x;
                const auto word = obstructions[chunk_y * layout.chunk_stride + chunk_x];
                if ((word >> cell) & 1u) continue;
                const auto dq = distances[(chunk_y * layout.chunked_width + chunk_x) * 64 + cell];
                if (dq + 1 < best_d) {
                    best_d = dq;
                    best = {x, y};
                }
            }
        }
#else
        for (int dx = -2; dx <= 2; ++dx)
            for (int dy = -2; dy <= 2; ++dy) {
                const vec2 q{pos.x + dx, pos.y + dy};
                if (!in_bounds(q, w.width, w.height) || bit(blocked, q)) continue;
                const std::uint16_t dq = fdist(field, q);
                if (dq + 1 < best_d) {
                    best_d = dq;
                    best = q;
                }
            }
#endif
        if (best == pos) return false;'''),
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
        verify(args.verify, travel_tail=True, name="pg-travel-scan")
