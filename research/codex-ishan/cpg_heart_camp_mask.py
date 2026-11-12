"""Filter Heart's landing search using the world's existing camp tile mask."""
import argparse
from pathlib import Path

from bounded_verdict import apply
from cpg_decision_guard import verify
from cpg_greedy_full import prepare as prepare_full


FOREIGN_CAMPS = """static std::vector<vec2> live_foreign_camps(const World& world, int group, vec2 target, int radius) {
    bc::bitboard nearby;
    // A camp hit from a landing tile is at most two cast radii from the target.
    nearby.draw_chebyshev(target, static_cast<float>(2 * radius));
    nearby &= world.camp_tiles_all;
    auto tiles = nearby.positions();
    std::erase_if(tiles, [&](vec2 p) {
        const int other = world.group_of_camp_tile(p);
        return other < 0 || other == group || world.groups[static_cast<std::size_t>(other)].state != GroupState::alive;
    });
    return tiles;
}
"""


def prepare(src, enabled):
    prepare_full(src, enabled)
    header = src / "common.h"
    data = header.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    header.write_bytes(f"#define CODEX_HEART_CAMP_MASK {int(enabled)}".encode() + nl + data)
    apply(src / "bot.cpp", (
        ("#if V55_HEART_CAMP\nbool Bot::cast_camp_strike(int ci) {",
         "#if V55_HEART_CAMP\n#if CODEX_HEART_CAMP_MASK\n" + FOREIGN_CAMPS +
         "#endif\n\nbool Bot::cast_camp_strike(int ci) {"),
        ("        int best_hits = 0, best_home = kUnreach;", """#if CODEX_HEART_CAMP_MASK
        std::optional<std::vector<vec2>> foreign_camps;
#endif
        int best_hits = 0, best_home = kUnreach;"""),
        ("""            bool extra_group = false;
            for (int x = -radius; x <= radius; ++x) for (int y = -radius; y <= radius; ++y) {
                const int other = w.group_of_camp_tile({q.x + x, q.y + y});
                if (other >= 0 && other != gi && w.groups[static_cast<std::size_t>(other)].state == GroupState::alive) extra_group = true;
            }
            if (extra_group) continue;""", """#if CODEX_HEART_CAMP_MASK
            if (!foreign_camps) foreign_camps.emplace(live_foreign_camps(w, gi, target.pos, radius));
            if (std::any_of(foreign_camps->begin(), foreign_camps->end(), [&](vec2 p) { return cheb(p, q) <= radius; })) continue;
#else
            bool extra_group = false;
            for (int x = -radius; x <= radius; ++x) for (int y = -radius; y <= radius; ++y) {
                const int other = w.group_of_camp_tile({q.x + x, q.y + y});
                if (other >= 0 && other != gi && w.groups[static_cast<std::size_t>(other)].state == GroupState::alive) extra_group = true;
            }
            if (extra_group) continue;
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
        verify(args.verify, variant="heart-camp-mask")
