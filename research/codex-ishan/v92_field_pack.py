"""Construct the same sorted field order with one in-place packed vector."""
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
    header.write_bytes(f"#define CODEX_V92_FIELD_PACK {int(enabled)}".encode() + nl + data)
    apply(src / "world.cpp", (
        ("""    std::vector<std::uint32_t> keys;
    keys.reserve(groups.size());
    for (std::size_t gi = 0; gi < groups.size(); ++gi) {
        int d = kUnreach;
        for (int ci : groups[gi].camps) d = std::min<int>(d, fdist(spawn_field, camps[ci].pos));
        keys.push_back(static_cast<std::uint32_t>(d) << 12 | static_cast<std::uint32_t>(gi));
    }
    std::sort(keys.begin(), keys.end());
    field_order.reserve(keys.size());
    for (std::uint32_t k : keys) field_order.push_back(static_cast<int>(k & 0xFFF));""",
         """#if CODEX_V92_FIELD_PACK
    const auto width_in_chunks = bc::detail::layout().chunked_width;
    const auto* spawn_distances = spawn_field.ptr();
    field_order.resize(groups.size());
    for (std::size_t gi = 0; gi < groups.size(); ++gi) {
        auto closest = kUnreach;
        for (int ci : groups[gi].camps) {
            const vec2 p = camps[ci].pos;
            const auto chunk = (static_cast<std::uint32_t>(p.y) >> 3) * width_in_chunks +
                (static_cast<std::uint32_t>(p.x) >> 3);
            const auto cell = ((p.y & 7) << 3) + (p.x & 7);
            closest = std::min(closest, spawn_distances[chunk * 64 + cell]);
        }
        field_order[gi] = static_cast<int>(static_cast<std::uint32_t>(closest) << 12 |
                                           static_cast<std::uint32_t>(gi));
    }
    std::sort(field_order.begin(), field_order.end(), [](int lhs, int rhs) {
        return static_cast<std::uint32_t>(lhs) < static_cast<std::uint32_t>(rhs);
    });
    for (int& group : field_order) group &= 0xFFF;
#else
    std::vector<std::uint32_t> keys;
    keys.reserve(groups.size());
    for (std::size_t gi = 0; gi < groups.size(); ++gi) {
        int d = kUnreach;
        for (int ci : groups[gi].camps) d = std::min<int>(d, fdist(spawn_field, camps[ci].pos));
        keys.push_back(static_cast<std::uint32_t>(d) << 12 | static_cast<std::uint32_t>(gi));
    }
    std::sort(keys.begin(), keys.end());
    field_order.reserve(keys.size());
    for (std::uint32_t k : keys) field_order.push_back(static_cast<int>(k & 0xFFF));
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
        verify(args.verify, round1_only=True, field_pack=True)
