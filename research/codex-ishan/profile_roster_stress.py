"""Profile the exact stress failures and fixed clean controls with charged markers."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import re
import subprocess
from zipfile import ZipFile

from bounded_verdict import apply
from large_roster_stress import HERE, OUT as STRESS, bench, read
from pg_ambush_guard import prepare
from profile_pg_budget_broad import augment
import profile_pg_runtime as trace
from trace_pg_dash_turns import add_move_trace

def prepare_coarse(src, rounds):
    code = src / "bot.cpp"
    condition = " || ".join(f"round == {r}" for r in sorted(rounds))
    stages = ("world", "support", "wardrev", "ambush", "enemies", "farmsel", "c_walked", "c_cast",
              "d_farm", "decide", "tail", "fields", "bushpre")
    apply(code, (
        ('#include "bot.h"', '''#include "bot.h"

static bool codex_stress_trace = false;
static int codex_last_suspension = -1;
#define CODEX_STRESS_CHECK(phase) \\
    do { \\
        if (codex_stress_trace && codex_last_suspension != round && static_cast<int>(bc::round_number()) != round) { \\
            codex_last_suspension = round; \\
            std::printf("CODEX_STRESS R%d t%d %s\\n", round, static_cast<int>(type), phase); \\
        } \\
    } while (false)'''),
        ("    round = static_cast<int>(bc::round_number());\n    if (!inited)",
         f"    round = static_cast<int>(bc::round_number());\n    codex_stress_trace = {condition};\n    if (!inited)"),
        *((f'PROF_CHECK("{stage}");', f'PROF_CHECK("{stage}"); CODEX_STRESS_CHECK("{stage}");') for stage in stages),
    ))


def play_scoped(job):
    row = bench.one(job, log_limit=trace.LIMIT)
    case = bench.OUT / "games" / f"profile-0-{row['opponent']}-{row['map']}-{row['side']}"
    with ZipFile(next(case.glob("*.repl26a"))) as bundle:
        log = bundle.read(f"team-{row['side'].lower()}.stdout")
    markers = re.findall(rb"CODEX_STRESS R\d+ t\d+ [a-z_]+", log)
    counts = Counter()
    examples = {}
    for item in markers:
        line = item.decode("ascii")
        phase = line.split()[-1]
        counts[phase] += 1
        examples.setdefault(phase, line)
    moves = [s.decode("ascii", "replace") for s in re.findall(rb"CODEX_MOVE [^\n]+", log)]
    return {**row, "crossings": dict(counts), "examples": examples, "moves": moves}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--coarse", action="store_true")
    mode.add_argument("--moves", action="store_true")
    args = parser.parse_args()
    stress = read(HERE / "LARGE_ROSTER_STRESS.json")
    affected = stress["affected"]
    selected = {r["map"] for r in affected}
    controls = []
    all_rows = read(STRESS / "rows.json")
    for r in sorted(all_rows, key=lambda r: sha256(f"exp045:{r['map']}:{r['opponent']}:{r['side']}".encode()).digest()):
        if r["map"] in selected or r["fuel_outs"]:
            continue
        selected.add(r["map"])
        controls.append(r)
        if len(controls) == 8:
            break
    assert len(affected) == 18 and len(controls) == 8
    variant = "moves" if args.moves else "coarse" if args.coarse else "profile"
    bench.OUT = trace.OUT = bench.CACHE / f"large-roster-{variant}-604211"
    (bench.OUT / "games").mkdir(parents=True)
    project = bench.OUT / "diagnostic"
    src = project / "src"
    prepare(src, True)
    rounds = {e["timestamp"]["round"] for r in affected for e in r["events"]}
    if args.coarse:
        prepare_coarse(src, rounds)
    elif args.moves:
        actors = {(e["timestamp"]["round"], e["owner"]["name"].lower()) for r in affected for e in r["events"]}
        add_move_trace(src, " || ".join(f"(round == {r} && type == bc::champion_type::{t})" for r, t in sorted(actors)))
    else:
        trace.instrument(src)
        augment(src)
    wasm = project / "bot.wasm"
    with (bench.OUT / "build.log").open("wb") as log:
        subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm], cwd=bench.ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    maps = {p.stem: p for p in (STRESS / "maps").glob("*.map26a")}
    manifest = read(HERE / "LARGE_ROSTER_MAPS.json")["maps"]
    for r in affected + controls:
        mp = maps[r["map"]]
        assert bench.digest(mp) == manifest[mp.name]
        file, expected = bench.OPPS[r["opponent"]]
        assert bench.digest(bench.CACHE / file) == expected
    jobs = [("profile", 0, r["opponent"], maps[r["map"]], r["side"], wasm) for r in affected + controls]
    with ThreadPoolExecutor(max_workers=8) as pool:
        profiled = list(pool.map(trace.play if variant == "profile" else play_scoped, jobs))
    counts = Counter()
    joins = []
    for base, row in zip(affected + controls, profiled, strict=True):
        assert all(base[k] == row[k] for k in ("map_hash", "engine_seed", "opponent", "side"))
        counts.update(row["crossings"])
        case = bench.OUT / "games" / f"profile-0-{row['opponent']}-{row['map']}-{row['side']}"
        native = read(case / "native.json")
        timed = {(e["owner"]["name"], a["timestamp"]["round"]) for e in native["events"]
                 if e["kind"] == "fuelExhausted" and e["owner"]["team"] == "team" + row["side"] for a in e["entries"]}
        exact = {(e["owner"]["name"], e["timestamp"]["round"]) for e in base.get("events", [])}
        if timed & exact:
            joint_rounds = {r for _, r in timed & exact}
            phases = {k: s for k, s in row["examples"].items() if int(re.search(r" R(\d+)", s).group(1)) in joint_rounds}
            joins.append({"map": row["map"], "opponent": row["opponent"], "side": row["side"],
                          "matched_native": sorted(timed & exact), "examples": phases})
    report = {"wasm": bench.digest(wasm), "n": len(profiled), "fuel": sum(r["fuel_outs"] for r in profiled),
              "error_cells": sum(bool(r["faults"] or r["diagnostic_codes"]) for r in profiled),
              "crossings": dict(counts.most_common()), "joins": joins, "rows": profiled}
    name = f"LARGE_ROSTER_{variant.upper()}.json"
    with (HERE / name).open("x", encoding="utf8", newline="\n") as f:
        json.dump(report, f, indent=2)
        f.write("\n")
    print({k: v for k, v in report.items() if k not in ("rows", "joins")}, flush=True)
    for j in joins:
        print(j["map"], j["matched_native"], list(j["examples"]), flush=True)


if __name__ == "__main__":
    main()
