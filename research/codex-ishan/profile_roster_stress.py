"""Profile the exact stress failures and fixed clean controls with charged markers."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import re
import subprocess

from large_roster_stress import HERE, OUT as STRESS, bench, read
from pg_ambush_guard import prepare
from profile_pg_budget_broad import augment
import profile_pg_runtime as trace

OUT = bench.CACHE / "large-roster-profile-604211"


def main():
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
    bench.OUT = trace.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    project = OUT / "diagnostic"
    src = project / "src"
    prepare(src, True)
    trace.instrument(src)
    augment(src)
    wasm = project / "bot.wasm"
    with (OUT / "build.log").open("wb") as log:
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
        profiled = list(pool.map(trace.play, jobs))
    counts = Counter()
    joins = []
    for base, row in zip(affected + controls, profiled, strict=True):
        assert all(base[k] == row[k] for k in ("map_hash", "engine_seed", "opponent", "side"))
        counts.update(row["crossings"])
        case = OUT / "games" / f"profile-0-{row['opponent']}-{row['map']}-{row['side']}"
        native = read(case / "native.json")
        timed = {(e["owner"]["name"], a["timestamp"]["round"]) for e in native["events"]
                 if e["kind"] == "fuelExhausted" and e["owner"]["team"] == "team" + row["side"] for a in e["entries"]}
        exact = {(e["owner"]["name"], e["timestamp"]["round"]) for e in base.get("events", [])}
        if timed & exact:
            joint_rounds = {r for _, r in timed & exact}
            phases = {k: s for k, s in row["examples"].items() if int(re.search(r"A2SUS R(\d+)", s).group(1)) in joint_rounds}
            joins.append({"map": row["map"], "opponent": row["opponent"], "side": row["side"],
                          "matched_native": sorted(timed & exact), "examples": phases})
    report = {"wasm": bench.digest(wasm), "n": len(profiled), "fuel": sum(r["fuel_outs"] for r in profiled),
              "error_cells": sum(bool(r["faults"] or r["diagnostic_codes"]) for r in profiled),
              "crossings": dict(counts.most_common()), "joins": joins, "rows": profiled}
    with (HERE / "LARGE_ROSTER_PROFILE.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(report, f, indent=2)
        f.write("\n")
    print({k: v for k, v in report.items() if k not in ("rows", "joins")}, flush=True)
    for j in joins:
        print(j["map"], j["matched_native"], list(j["examples"]), flush=True)


if __name__ == "__main__":
    main()
