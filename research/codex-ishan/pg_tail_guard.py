"""Freeze and verify PG dash's existing reserve at two follow-up boundaries."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from bounded_verdict import apply
from pg_dash_camps import prepare as prepare_dash, read
import profile_pg_runtime as trace
from qualify_local import partition

HERE = Path(__file__).resolve().parent
SOURCE = bench.CACHE / "pg-dash-broad"
TAIL = {"bushpre -> end", "tail_prelock -> tail_priority", "tail_priority -> tail",
        "d_farm -> d_opp", "d_opp -> decide", "decide -> tail_drop"}


def prepare(src, enabled, diagnostic):
    prepare_dash(src, enabled, True, diagnostic)
    header = src / "common.h"
    data = header.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    header.write_bytes(f"#define CODEX_PG_TAIL_GUARD {int(enabled)}".encode() + nl + data)
    guard = """#if CODEX_PG_TAIL_GUARD
    if (rb::turn_guard()) {
#if CODEX_PG_RUNTIME
        codex_report_tail_guard = true;
#endif
        return;
    }
#endif"""
    farm_guard = "\n".join("    " + line if not line.startswith("#") else line for line in guard.splitlines())
    apply(src / "bot.cpp", (
        ("void Bot::play_turn() {\n    PROF(turn);", """#if CODEX_PG_TAIL_GUARD && CODEX_PG_RUNTIME
static bool codex_report_tail_guard = false;
#endif

void Bot::play_turn() {
    PROF(turn);
#if CODEX_PG_TAIL_GUARD && CODEX_PG_RUNTIME
    if (codex_report_tail_guard) {
        std::puts("CODEX_PG_TAIL_DEFERRED");
        codex_report_tail_guard = false;
    }
#endif"""),
        ('        PROF_CHECK("d_farm");\n        opportunistic_attack();',
         f'        PROF_CHECK("d_farm");\n{farm_guard}\n        opportunistic_attack();'),
        ('    PROF_CHECK("decide");\n#if A2_MICLOG', f'    PROF_CHECK("decide");\n{guard}\n#if A2_MICLOG'),
    ))


def frozen_cases():
    rows = read(SOURCE / "rows.json")
    pairs = list(zip(rows[::2], rows[1::2], strict=True))
    affected = [(e, p) for e, p in pairs if TAIL & p["crossings"].keys()]
    maps = {p["map"] for _, p in affected}
    controls = []
    ordered = sorted(pairs, key=lambda ep: sha256(
        f"exp041:{ep[0]['map']}:{ep[0]['side']}:{ep[0]['opponent']}".encode()).digest())
    for e, p in ordered:
        if p["map"] in maps or e["fuel_outs"] or p["fuel_outs"]:
            continue
        maps.add(p["map"])
        controls.append((e, p))
        if len(controls) == 8:
            break
    assert len(controls) == 8
    return affected, controls, [e for e, _ in pairs if e["fuel_outs"]]


def run(wasm):
    diagnostic = wasm is None
    arm = "profile" if diagnostic else "exact"
    bench.OUT = trace.OUT = bench.CACHE / f"pg-tail-{arm}-dev"
    (bench.OUT / "games").mkdir(parents=True)
    if diagnostic:
        project = bench.OUT / "bot"
        prepare(project / "src", True, True)
        wasm = project / "bot.wasm"
        with (project / "build.log").open("wb") as log:
            subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm], cwd=bench.ROOT,
                           stdout=log, stderr=subprocess.STDOUT, check=True)
    affected, controls, exact_affected = frozen_cases()
    if diagnostic:
        base = [p for _, p in affected + controls]
    else:
        base = [e for e, _ in affected + controls] + exact_affected
    maps = {p.stem: p for p in partition("dev")}
    for opp in {r["opponent"] for r in base}:
        file, digest = bench.OPPS[opp]
        assert bench.digest(bench.CACHE / file) == digest
    jobs = [(arm, 0, r["opponent"], maps[r["map"]], r["side"], wasm) for r in base]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(trace.play if diagnostic else bench.one, jobs))
    for b, c in zip(base, rows, strict=True):
        assert all(b[k] == c[k] for k in ("map_hash", "engine_seed", "opponent", "side"))
    info = {"wasm": bench.digest(wasm), "n": len(rows), "baseline": sum(r["fuel_outs"] for r in base),
            "candidate": sum(r["fuel_outs"] for r in rows),
            "error_cells": sum(bool(r["faults"] or r["diagnostic_codes"]) for r in rows)}
    passed = info["candidate"] < info["baseline"] and not info["error_cells"]
    if diagnostic:
        phase = Counter()
        guards = set()
        for index, row in enumerate(rows):
            phase.update(row["crossings"])
            path = bench.OUT / "games" / f"profile-0-{row['opponent']}-{row['map']}-{row['side']}"
            with ZipFile(next(path.glob("*.repl26a"))) as archive:
                raw = archive.read(f"team-{row['side'].lower()}.stdout")
            row["guards"] = raw.count(b"CODEX_PG_TAIL_DEFERRED")
            if row["guards"] and index < len(affected):
                guards.add(row["map"])
        old = sum(n for row in base for k, n in row["crossings"].items() if k in TAIL)
        new = sum(phase[k] for k in TAIL)
        info.update({"guarded_affected_maps": sorted(guards), "late_crossings": [old, new]})
        passed = passed and len(guards) >= 2 and new < old
    info["pass"] = passed
    out = HERE / f"PG_TAIL_{arm.upper()}.json"
    with out.open("x", encoding="utf8", newline="\n") as f:
        json.dump({**info, "baseline_rows": base, "rows": rows}, f, indent=2)
        f.write("\n")
    print(info, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path)
    parser.add_argument("--off", action="store_true")
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()
    if args.src:
        prepare(args.src, not args.off, False)
    else:
        run(args.verify)
