"""Paired development stress of the two bounded greedy scans."""
from concurrent.futures import ThreadPoolExecutor
import json

from large_roster_stress import HERE, OUT as STRESS, bench, native_fuel, read
from qualify_local import DEV, build

OUT = bench.CACHE / "greedy-pair-stress"
SEED = 11173


def play(job):
    row = bench.one(job, fuel=100000)
    case = bench.OUT / "games" / f"{row['arm']}-{row['noise_seed']}-{row['opponent']}-{row['map']}-{row['side']}"
    native = read(case / "native.json")
    return {**row, "errors": bool(native["diagnostics"]["codes"] or any(native["diagnostics"]["botFaults"].values())),
            "draft": native["roster"]["draft"]}


def main():
    assert read(HERE / "CPG_GREEDY_FULL_PROOF.json")["pass"]
    assert read(HERE / "CPG_GREEDY_FULL_EXACT.json")["pass"]
    assert read(HERE / "MARCELLA_GREEDY_FULL.json")["pass"]
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    maps = sorted((STRESS / "maps").glob("*.map26a"))
    manifest = read(HERE / "LARGE_ROSTER_MAPS.json")["maps"]
    assert len(maps) == 100 and {m.name: bench.digest(m) for m in maps} == manifest
    for opponent in DEV:
        file, expected = bench.OPPS[opponent]
        assert bench.digest(bench.CACHE / file) == expected
    binaries, release = {}, {}
    for arm in ("near", "full"):
        project = bench.ROOT / f"bots/codex-cpg-greedy-{arm}"
        release[arm] = bench.digest(project / "bot.wasm")
        assert release[arm] == read(HERE / f"CPG_GREEDY_{arm.upper()}_BUILDS.json")["primary"]
        binaries[arm] = build(project / "src", OUT / arm, SEED)
    jobs = [(arm, SEED, opponent, mp, side, wasm) for mp in maps for opponent in DEV
            for side in "AB" for arm, wasm in binaries.items()]
    rows = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        for row in pool.map(play, jobs):
            rows.append(row)
            if len(rows) % 160 == 0:
                print(f"{len(rows)}/{len(jobs)}", flush=True)
    pairs = list(zip(rows[::2], rows[1::2], strict=True))
    assert all(all(a[k] == b[k] for k in ("map_hash", "engine_seed", "opponent", "side")) for a, b in pairs)
    affected = []
    for row in rows:
        if row["fuel_outs"] or row["errors"]:
            events = native_fuel(row, OUT)
            assert len(events) == row["fuel_outs"]
            affected.append({**row, "events": events})
    report = {"engine": bench.ENGINE, "release": release, "seed": SEED, "n_pairs": len(pairs),
              "opponents": {o: bench.OPPS[o][1] for o in DEV},
              "binaries": {arm: bench.digest(wasm) for arm, wasm in binaries.items()},
              "outcomes": bench.summary(pairs),
              "fuel": {arm: sum(r["fuel_outs"] for r in rows if r["arm"] == arm) for arm in binaries},
              "draft_changes": sum(a["draft"] != b["draft"] for a, b in pairs),
              "fuel_increases": sum(b["fuel_outs"] > a["fuel_outs"] for a, b in pairs),
              "error_cells": sum(r["errors"] for r in rows)}
    with (HERE / "CPG_GREEDY_PAIR_STRESS.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**report, "affected": affected}, out, indent=2)
        out.write("\n")
    with (OUT / "rows.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump(rows, out, indent=2)
        out.write("\n")
    print(report, flush=True)


if __name__ == "__main__":
    main()
