"""Keep the failed-cast fallback when a known live camp blocks the only dash path."""
import argparse
from pathlib import Path

from bounded_verdict import apply
from cpg_decision_guard import verify
from cpg_heart_camp_mask import prepare as prepare_camp_mask


def prepare(src, enabled):
    prepare_camp_mask(src, enabled)
    header = src / "common.h"
    data = header.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    header.write_bytes(f"#define CODEX_HEART_CAST_PATH {int(enabled)}".encode() + nl + data)
    apply(src / "bot.cpp", (
        ("        if (best.x < 0 || best_hits <= 0) return false;\n        try {\n            if (bc::self().abilities()[s].use(best)) {",
         """        if (best.x < 0 || best_hits <= 0) return false;
#if CODEX_HEART_CAST_PATH
        const vec2 delta = best - pos;
        if (sp.range < 3.0f && std::abs(delta.x) == 2 && std::abs(delta.y) == 2) {
            const vec2 middle{pos.x + delta.x / 2, pos.y + delta.y / 2};
            // This diagonal has only one intermediate tile. Confirm current occupancy
            // because the cached world snapshot may predate an action this turn.
            if (bit(w.unit_tiles, middle) && bit(w.camp_tiles_all, middle)) {
                std::uint32_t handle = 0;
                d::camp_state camp{};
                if (d::sdk_camp_at(middle.x, middle.y, &handle) == 0 &&
                    d::sdk_camp(handle, &camp) == 0 && camp.health > 0.0f) continue;
            }
        }
#endif
        try {
            if (bc::self().abilities()[s].use(best)) {"""),
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
        verify(args.verify, variant="heart-cast-path")
