"""Budget the threat-safe route when a respawn wait sends a carrier to bank."""
import argparse
from pathlib import Path
from textwrap import indent

from bounded_verdict import apply
from cpg_decision_guard import verify
from cpg_heart_cast_path import prepare as prepare_path


CAP_SEARCH = """const auto cap = rb::search_cap(rb::kTailReserve);
if (cap == 0) return true;
const auto levels = safe_field.compute_to_with_expansion_count(blocked, ring, single(pos), visited, cap);
// An unfinished search does not establish that the plain route is safe.
if (fdist(safe_field, pos) == kUnreach && levels + 1 >= cap) return true;"""


def prepare(src, enabled, *, specialized=False, shared=False, post_ward=False):
    prepare_path(src, enabled)
    header = src / "common.h"
    data = header.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    header.write_bytes(f"#define CODEX_SAFE_TRIBUTE_CAP {int(enabled)}".encode() + nl + data)
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
    original_search = "                safe_field.compute_to(blocked, ring, single(pos), visited);"
    if shared or post_ward:
        body = indent(CAP_SEARCH, " " * 16)
        if post_ward:
            body = ("                if (ward_refreshed_this_turn && rb::left() < rb::kReserve.observe) {\n" +
                    indent(CAP_SEARCH, " " * 20) + "\n                } else {\n    " + original_search + "\n                }")
        capped = "#if CODEX_SAFE_TRIBUTE_CAP\n" + body + "\n#else\n" + original_search + "\n#endif"
        apply(src / "bot.cpp", ((safe_search, safe_search.replace(original_search, capped)),))
        if post_ward:
            apply(src / "bot.h", (("    bool force_tribute = false;", """    bool force_tribute = false;
#if CODEX_SAFE_TRIBUTE_CAP
    bool ward_refreshed_this_turn = false;
#endif"""),))
            apply(src / "bot.cpp", (
                ("void Bot::play_turn() {", """void Bot::play_turn() {
#if CODEX_SAFE_TRIBUTE_CAP
    ward_refreshed_this_turn = false;
#endif"""),
                ("    if (ward_reveal()) w.update(round); // the ward shows the bush now: look again",
                 """#if CODEX_SAFE_TRIBUTE_CAP
    ward_refreshed_this_turn = ward_reveal();
    if (ward_refreshed_this_turn) w.update(round);
#else
    if (ward_reveal()) w.update(round); // the ward shows the bush now: look again
#endif"""),
            ))
        return

    apply(src / "bot.h", (
        ("    bool tribute_if_needed();", """#if CODEX_SAFE_TRIBUTE_CAP
    bool tribute_if_needed(bool bounded_wait = false);
#else
    bool tribute_if_needed();
#endif"""),
    ))
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
        (safe_search, safe_search.replace(original_search, """#if CODEX_SAFE_TRIBUTE_CAP
                if (bounded_wait) {
""" + indent(CAP_SEARCH, " " * 20) + """
                } else
#endif
                {
                    safe_field.compute_to(blocked, ring, single(pos), visited);
                }""")),
    ))
    if specialized:
        apply(src / "bot.h", (("    bool tribute_if_needed(bool bounded_wait = false);",
                               "    template<bool bounded_wait = false>\n    bool tribute_if_needed();"),))
        apply(src / "bot.cpp", (
            ("bool Bot::tribute_if_needed(bool bounded_wait) {",
             "template<bool bounded_wait>\nbool Bot::tribute_if_needed() {"),
            ("                if (bounded_wait) {", "                if constexpr (bounded_wait) {"),
            ("                return tribute_if_needed(true);", "                return tribute_if_needed<true>();"),
            ("float Bot::incoming_from_group(const GroupRec& g, vec2 at) const {",
             """#if CODEX_SAFE_TRIBUTE_CAP
template bool Bot::tribute_if_needed<false>();
#endif

float Bot::incoming_from_group(const GroupRec& g, vec2 at) const {"""),
        ))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--src", type=Path)
    target.add_argument("--verify", type=Path)
    parser.add_argument("--off", action="store_true")
    variant_args = parser.add_mutually_exclusive_group()
    variant_args.add_argument("--specialized", action="store_true")
    variant_args.add_argument("--shared", action="store_true")
    variant_args.add_argument("--post-ward", action="store_true")
    args = parser.parse_args()
    if args.src:
        prepare(args.src, not args.off, specialized=args.specialized, shared=args.shared, post_ward=args.post_ward)
    else:
        suffix = next((name for enabled, name in ((args.post_ward, "post-ward"), (args.shared, "shared"),
                                                  (args.specialized, "specialized")) if enabled), "cap")
        verify(args.verify, variant=f"safe-tribute-{suffix}")
