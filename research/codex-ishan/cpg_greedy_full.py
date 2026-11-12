"""Bound the greedy fallback's enumeration while preserving the SDK's order."""
import argparse
from pathlib import Path

from bounded_verdict import apply
from cpg_decision_guard import verify
from cpg_runtime_release import prepare as prepare_runtime


NEAREST = """static vec2 greedy_nearest(const bc::bitboard& goals, vec2 pos) {
    constexpr int nearby_radius = 4;
    constexpr unsigned nearby_area = (2 * nearby_radius + 1) * (2 * nearby_radius + 1);
    const auto nearest_in_small_mask = [&](const bc::bitboard& mask) {
        std::array<vec2, nearby_area> positions;
        const auto count = mask.positions_into(positions);
        vec2 goal{-1, -1};
        int distance = 1 << 20;
        for (unsigned i = 0; i < count; ++i) {
            const int d = cheb(positions[i], pos);
            if (d < distance) distance = d, goal = positions[i];
        }
        return goal;
    };
    if (goals.count() <= nearby_area) return nearest_in_small_mask(goals);

    bc::bitboard nearby;
    nearby.draw_chebyshev(pos, static_cast<float>(nearby_radius));
    nearby &= goals;
    if (!nearby.is_empty()) return nearest_in_small_mask(nearby);

    const auto within = [&](int radius) {
        nearby.clear();
        nearby.draw_chebyshev(pos, static_cast<float>(radius));
        nearby &= goals;
        return !nearby.is_empty();
    };
    int low = nearby_radius + 1;
    int high = std::max({pos.x, goals.width() - 1 - pos.x, pos.y, goals.height() - 1 - pos.y});
    while (low < high) {
        const int mid = low + (high - low) / 2;
        if (within(mid)) high = mid;
        else low = mid + 1;
    }
    // Every set tile in this first nonempty square ties for nearest.
    within(low);
    vec2 first{-1, -1};
    return nearby.positions_into(std::span<vec2>{&first, 1}) ? first : vec2{-1, -1};
}
"""


def apply_full(src, enabled, *, scratch=False):
    header = src / "common.h"
    data = header.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    header.write_bytes(f"#define CODEX_GREEDY_FULL {int(enabled)}".encode() + nl + data)
    nearest = NEAREST
    if scratch:
        nearest = nearest.replace("        std::array<vec2, nearby_area> positions;",
                                  "        static std::array<vec2, nearby_area> positions;")
    apply(src / "bot.cpp", (
        ("bool Bot::greedy_step(const bc::bitboard& goals) {",
         "#if CODEX_GREEDY_FULL\n" + nearest + "#endif\n\nbool Bot::greedy_step(const bc::bitboard& goals) {"),
        ("""    vec2 goal{-1, -1};
    int gd = 1 << 20;
    for (vec2 g : goals.positions()) {
        const int d = cheb(g, pos);
        if (d < gd) gd = d, goal = g;
    }
    if (goal.x < 0) return false;""", """#if CODEX_GREEDY_FULL
    const vec2 goal = greedy_nearest(goals, pos);
    if (goal.x < 0) return false;
    const int gd = cheb(goal, pos);
#else
    vec2 goal{-1, -1};
    int gd = 1 << 20;
    for (vec2 g : goals.positions()) {
        const int d = cheb(g, pos);
        if (d < gd) gd = d, goal = g;
    }
    if (goal.x < 0) return false;
#endif"""),
    ))


def prepare(src, enabled, *, scratch=False):
    prepare_runtime(src, enabled, packed=True)
    apply_full(src, enabled, scratch=scratch)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--src", type=Path)
    target.add_argument("--verify", type=Path)
    parser.add_argument("--off", action="store_true")
    parser.add_argument("--scratch", action="store_true")
    args = parser.parse_args()
    if args.src:
        prepare(args.src, not args.off, scratch=args.scratch)
    else:
        verify(args.verify, variant="greedy-scratch" if args.scratch else "greedy-full")
