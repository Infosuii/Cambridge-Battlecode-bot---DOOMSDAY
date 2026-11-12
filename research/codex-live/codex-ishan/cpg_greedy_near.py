"""Keep the original greedy target while limiting dense nearby enumeration."""
import argparse
from pathlib import Path

from bounded_verdict import apply
from cpg_decision_guard import verify
from cpg_runtime_release import prepare as prepare_runtime

NEARBY = """    constexpr int nearby_radius = 4;
    constexpr unsigned nearby_area = (2 * nearby_radius + 1) * (2 * nearby_radius + 1);
    std::optional<bc::bitboard> nearby;
    if (goals.count() > nearby_area) {
        nearby.emplace();
        nearby->clear();
        nearby->draw_chebyshev(pos, static_cast<float>(nearby_radius));
        *nearby &= goals;
    }
    const auto& candidates = nearby && !nearby->is_empty() ? *nearby : goals;
"""


def prepare(src, enabled):
    prepare_runtime(src, enabled, packed=True)
    apply_nearby(src, enabled)


def apply_nearby(src, enabled):
    header = src / "common.h"
    data = header.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    header.write_bytes(f"#define CODEX_GREEDY_NEAR {int(enabled)}".encode() + nl + data)
    apply(src / "bot.cpp", (
        ("    int gd = 1 << 20;\n    for (vec2 g : goals.positions()) {",
         """    int gd = 1 << 20;
#if CODEX_GREEDY_NEAR
""" + NEARBY + """    for (vec2 g : candidates.positions()) {
#else
    for (vec2 g : goals.positions()) {
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
        verify(args.verify, variant="greedy-near")
