"""Budget the threat-safe route when a respawn wait sends a carrier to bank."""
import argparse
from pathlib import Path

from bounded_verdict import apply
from cpg_decision_guard import verify
from cpg_heart_cast_path import prepare as prepare_path


def prepare(src, enabled):
    prepare_path(src, enabled)
    header = src / "common.h"
    data = header.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    header.write_bytes(f"#define CODEX_SAFE_TRIBUTE_CAP {int(enabled)}".encode() + nl + data)
    apply(src / "bot.h", (
        ("    bool tribute_if_needed();", """#if CODEX_SAFE_TRIBUTE_CAP
    bool tribute_if_needed(bool bounded_wait = false);
#else
    bool tribute_if_needed();
#endif"""),
    ))
    safe_search = """    if (sr_hold && !force_tribute) return false;
#else
    if (gems >= 15) {
        bc::bitboard threat = w.threat_zone(round, V58_SURVIVE ? 15 : 10, 4.0f);
        threat.set(pos, false);
        if (!threat.is_empty() || any_watch) {
            bc::bitboard blocked = w.static_blocked | threat;
            blocked.set(pos, false);
            bc::bitboard ring = w.altar_ring & ~blocked;
            if (any_watch) ring = ring & ~watched;
            if (!ring.is_empty()) {
                bc::bitboard visited;
                safe_field.compute_to(blocked, ring, single(pos), visited);"""
    apply(src / "bot.cpp", (
        ("bool Bot::tribute_if_needed() {", """#if CODEX_SAFE_TRIBUTE_CAP
bool Bot::tribute_if_needed(bool bounded_wait) {
#else
bool Bot::tribute_if_needed() {
#endif"""),
        ("""            if (gems >= 10 && wait > altar_trip + 2) {
                force_tribute = true;
                return tribute_if_needed();
            }""", """            if (gems >= 10 && wait > altar_trip + 2) {
                force_tribute = true;
#if CODEX_SAFE_TRIBUTE_CAP
                return tribute_if_needed(true);
#else
                return tribute_if_needed();
#endif
            }"""),
        (safe_search, safe_search.replace("                safe_field.compute_to(blocked, ring, single(pos), visited);", """#if CODEX_SAFE_TRIBUTE_CAP
                if (bounded_wait) {
                    const auto cap = rb::search_cap(rb::kTailReserve);
                    if (cap == 0) return true;
                    const auto levels = safe_field.compute_to_with_expansion_count(blocked, ring, single(pos), visited, cap);
                    // An unfinished search does not establish that the plain route is safe.
                    if (fdist(safe_field, pos) == kUnreach && levels + 1 >= cap) return true;
                } else
#endif
                {
                    safe_field.compute_to(blocked, ring, single(pos), visited);
                }""")),
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
        verify(args.verify, variant="safe-tribute-cap")
