"""Prefer an adjacent reward tile while retaining the original camp approach."""
import argparse
from pathlib import Path
from shutil import copytree

from bounded_verdict import apply
from opening_window_behavior import main as behavior
from probe_reward_approach import bench


def prepare(src, enabled):
    copytree(bench.ROOT / "bots/v92/src", src)
    header = src / "common.h"
    data = header.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    header.write_bytes(f"#define CODEX_REWARD_APPROACH {int(enabled)}".encode() + nl + data)
    apply(src / "bot.cpp", (
        ("        if (!walk_toward(goal) && !bit(goal, pos)) {", """#if CODEX_REWARD_APPROACH
        bool reward_walk = false;
        if (round <= 300 && !walked && !bit(g.tiles, pos) && w.enemies.empty() && hp >= 0.65f * max_hp &&
            bc::fuel_remaining() > rb::kTailReserve) {
            int last = -1, remaining = 0;
            for (int ci : g.camps) {
                const auto& camp = w.camps[ci];
                if (camp.dead) continue;
                ++remaining;
                if (bit(w.visible, camp.pos) && camp.hp <= strength * camp_dealt_mult) last = ci;
            }
            if (remaining == 1 && last >= 0) {
                int closest = kUnreach, closest_reward = kUnreach;
                vec2 reward_tile{-1, -1};
                bool ordinary_step = false;
                for (vec2 dir : kDirs) {
                    const vec2 next = pos + dir;
                    if (!in_bounds(next, w.width, w.height) || !bit(goal, next) ||
                        bit(w.static_blocked, next) || bit(w.unit_tiles, next)) continue;
                    const int distance = cheb(next, w.camps[last].pos);
                    if (distance > range) continue;
                    if (!bit(g.tiles, next)) ordinary_step = true;
                    closest = std::min(closest, distance);
                    if (bit(g.tiles, next) && !bit(w.hot_zone, next) && distance < closest_reward) {
                        closest_reward = distance;
                        reward_tile = next;
                    }
                }
                if (ordinary_step && reward_tile.x >= 0 && closest_reward == closest)
                    reward_walk = walk_toward(single(reward_tile));
            }
        }
        if (!reward_walk && !walk_toward(goal) && !bit(goal, pos)) {
#else
        if (!walk_toward(goal) && !bit(goal, pos)) {
#endif"""),
    ))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--src", type=Path)
    target.add_argument("--behavior", action="store_true")
    parser.add_argument("--off", action="store_true")
    args = parser.parse_args()
    if args.src:
        prepare(args.src, not args.off)
    else:
        behavior("reward-approach", "REWARD_APPROACH_BUILDS.json", "REWARD_APPROACH_BEHAVIOR.json", round_limit=300)
