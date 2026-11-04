"""Check the camp's fresh state before a low-fuel Heart follow-up attack."""
import argparse
from pathlib import Path

from bounded_verdict import apply
from pg_dash_followup import prepare as prepare_followup, verify


def prepare(src, enabled):
    prepare_followup(src, enabled, escape_only=True)
    header = src / "common.h"
    data = header.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    header.write_bytes(f"#define CODEX_PG_HEART_ATTACK {int(enabled)}".encode() + nl + data)
    apply(src / "bot.cpp", (
        ('    PROF_CHECK("c_cast"); if (attack_unit(w.camps[t].camp, w.camps[t].pos)) {',
         '''#if CODEX_PG_HEART_ATTACK
    if (cast_done && type == bc::champion_type::heart_of_ruin && rb::turn_guard()) {
        const auto handle = static_cast<bc::handle_camp_t>(w.camps[t].camp);
        d::camp_state fresh{};
        if (d::sdk_camp(static_cast<std::uint32_t>(handle), &fresh) != 0 || fresh.health <= 0.0f) return true;
    }
#endif
    PROF_CHECK("c_cast"); if (attack_unit(w.camps[t].camp, w.camps[t].pos)) {'''),
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
        verify(args.verify, heart_attack=True)
