"""Retain the existing tail floor before starting a new decision phase."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

from bounded_verdict import apply
from cpg_runtime_release import prepare as prepare_runtime
from large_roster_stress import DENSE_OUT, HERE, bench, native_fuel, read
from pg_dash_followup import read_turn
from probe_budget_margin import OUT as ORIGINAL

OUT = bench.CACHE / "cpg-decision-guard-stress"


def prepare(src, enabled):
    prepare_runtime(src, enabled, packed=True)
    header = src / "common.h"
    data = header.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    header.write_bytes(f"#define CODEX_DECISION_GUARD {int(enabled)}".encode() + nl + data)
    apply(src / "bot.cpp", (
        ('    PROF_CHECK("wardrev");\n    if (counter_ambush()) {',
         '''    PROF_CHECK("wardrev");
#if CODEX_DECISION_GUARD
    if (rb::turn_guard()) return;
#endif
    if (counter_ambush()) {'''),
        ("    const bool fought =\n#if V58_SURVIVE", '''#if CODEX_DECISION_GUARD
    if (rb::turn_guard()) return;
#endif
    const bool fought =
#if V58_SURVIVE'''),
        ("bool Bot::fight_camps(GroupRec& g, int need) {", """bool Bot::fight_camps(GroupRec& g, int need) {
#if CODEX_DECISION_GUARD
    if (rb::turn_guard()) return true;
#endif"""),
    ))


def folder(root, row):
    return root / "games" / f"{row['arm']}-0-{row['opponent']}-{row['map']}-{row['side']}"


def pair(base, mp, wasm):
    arm, opponent, side = (base[k] for k in ("arm", "opponent", "side"))
    current = bench.one((arm, 0, opponent, mp, side, wasm), fuel=int(arm))
    assert all(current[k] == base[k] for k in ("arm", "opponent", "side", "map_hash", "engine_seed"))
    a, b = (read(folder(root, row) / "native.json") for root, row in ((ORIGINAL, base), (OUT, current)))
    draft_equal = a["roster"]["draft"] == b["roster"]["draft"]
    errors = any(any(d["diagnostics"]["botFaults"].values()) or d["diagnostics"]["codes"] for d in (a, b))
    return {"base": base, "candidate": current, "same_draft": draft_equal, "errors": bool(errors)}


def verify(wasm, *, variant="decision-guard"):
    global OUT
    OUT = bench.CACHE / f"cpg-{variant}-stress"
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    source = read(HERE / "CPG_BUDGET_MARGIN.json")
    maps = {p.stem: p for p in (DENSE_OUT / "maps").glob("*.map26a")}
    for r in source["rows"]:
        mp = maps[r["map"]]
        assert bench.digest(mp) == source["maps"][mp.name]
        file, expected = bench.OPPS[r["opponent"]]
        assert bench.digest(bench.CACHE / file) == expected
    with ThreadPoolExecutor(max_workers=10) as pool:
        rows = []
        for base, result in zip(source["rows"], pool.map(lambda r: pair(r, maps[r["map"]], wasm), source["rows"]), strict=True):
            assert result["base"] == base
            rows.append(result)
            if len(rows) % 80 == 0:
                print(f"{len(rows)}/{len(source['rows'])}", flush=True)
    case = next(r for r in rows if r["base"]["arm"] == "100000" and r["base"]["events"])
    first = case["base"]["events"][0]
    r, actor = first["timestamp"]["round"], first["owner"]["id"]
    b, c = (read_turn(folder(root, row), r, row["side"], actor)
            for root, row in ((ORIGINAL, case["base"]), (OUT, case["candidate"])))
    events = native_fuel(case["candidate"], OUT)
    removed = not any(e["owner"]["id"] == actor and e["timestamp"]["round"] == r for e in events)
    before = [a for a in b["executed_actions"] if a["kind"] not in (3, 26)] if b else []
    after = [a for a in c["executed_actions"] if a["kind"] not in (3, 26)] if c else []
    matched = bool(b and c and b["observation"] == c["observation"] and before == after[:len(before)])
    fuel = {arm: [sum(p[k]["fuel_outs"] for p in rows if p["base"]["arm"] == arm) for k in ("base", "candidate")]
            for arm in ("80000", "100000")}
    increases = sum(p["candidate"]["fuel_outs"] > p["base"]["fuel_outs"] for p in rows)
    errors = sum(p["errors"] or not p["same_draft"] for p in rows)
    passed = (len(rows) == 320 and fuel["100000"][1] < fuel["100000"][0] and
              not increases and not errors and removed and matched)
    result = {"reference": source["sha256"], "sha256": bench.digest(wasm), "engine": bench.ENGINE,
              "n": len(rows), "fuel": fuel, "increases": increases, "error_or_draft_cells": errors,
              "same_input_and_actions": matched, "standard_event_removed": removed, "pass": passed}
    name = f"CPG_{variant.upper().replace('-', '_')}_EXACT.json"
    with (HERE / name).open("x", encoding="utf8", newline="\n") as out:
        json.dump({**result, "rows": rows, "base_turn": b, "candidate_turn": c}, out, indent=2)
        out.write("\n")
    print(result, flush=True)


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
        verify(args.verify)
