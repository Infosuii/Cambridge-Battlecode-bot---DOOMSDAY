"""Admit cold siege mask allocation under the existing reservation."""
import argparse
from pathlib import Path

from bounded_verdict import apply
from pg_ambush_decision import prepare as prepare_decision
from pg_stress_tail import HERE, verify


def prepare(src, enabled):
    prepare_decision(src, enabled)
    header = src / "common.h"
    data = header.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    header.write_bytes(f"#define CODEX_PG_SIEGE_RESUME {int(enabled)}".encode() + nl + data)
    apply(src / "bot.cpp", (
        ("                if (opq_rows < opq_h) {\n                    ring &= ~danger_zone & ~w.static_blocked;",
         """#if CODEX_PG_SIEGE_RESUME
                if (opq_rows == opq_h && los.size() < w.camps.size()) {
                    if (los_ready.empty() && rb::admit_optional(rb::kSiegeInit, rb::kSearchFixed)) {
                        los.reserve(w.camps.size());
                        los_ready.resize(w.camps.size(), 0);
                    }
                    const auto slot_cost = rb::kSearchFixed + field_chunks();
                    while (!los_ready.empty() && los.size() < w.camps.size() && rb::admit_optional(rb::kSiegeInit, slot_cost))
                        los.emplace_back();
                }
                if (opq_rows < opq_h || los.size() < w.camps.size()) {
#else
                if (opq_rows < opq_h) {
#endif
                    ring &= ~danger_zone & ~w.static_blocked;"""),
        ("                if (los.size() < w.camps.size()) { los.resize(w.camps.size()); los_ready.resize(w.camps.size(), 0); }",
         """#if !CODEX_PG_SIEGE_RESUME
                if (los.size() < w.camps.size()) { los.resize(w.camps.size()); los_ready.resize(w.camps.size(), 0); }
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
        verify(args.verify, "pg-siege-resume", None, HERE / "PG-AMBUSH-DECISION_EXACT_STRESS.json",
               {("pool_604672", "Cassi", 315), ("pool_604770", "Marcella", 458)}, "LARGE_ROSTER_MOVES.json")
