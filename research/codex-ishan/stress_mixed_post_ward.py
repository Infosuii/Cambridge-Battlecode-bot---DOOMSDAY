"""Run the frozen standard-budget mixed-roster diagnostic on the post-ward source."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess

from large_roster_stress import ENGINE_SHA, HERE, SOURCE, SOURCE_SHA, bench, native_fuel, read
from qualify_local import DEV, build, partition
from stress_greedy_pair import play

OUT = bench.CACHE / "post-ward-mixed-stress-802673"
MAP_SEED = 802673
COMPILED_SEED = 14821


def generate():
    generator = OUT / "mapmake6.js"
    generator.write_bytes(subprocess.check_output(["git", "show", SOURCE], cwd=bench.ROOT))
    assert bench.digest(generator) == SOURCE_SHA
    folder = Path.home() / "AppData/Local/cambc/assets"
    asset = next(p for p in folder.glob("*/visualiser/assets/v2_0_0-hWOQ1R8f.wasm") if bench.digest(p) == ENGINE_SHA)
    (OUT / "v2_0_0.wasm").write_bytes(asset.read_bytes())
    with (OUT / "generate.log").open("wb") as log:
        subprocess.run(["node", generator, OUT / "maps", "100", str(MAP_SEED)], cwd=bench.ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    maps = sorted((OUT / "maps").glob("*.map26a"))
    hashes = {p.name: bench.digest(p) for p in maps}
    assert len(maps) == len(set(hashes.values())) == 100
    reserved = {line.split()[0] for line in (bench.ROOT / "docs/codex/FRESH_HOLDOUT.sha256").read_text().splitlines()}
    reserved.update(bench.digest(p) for p in partition("dev"))
    reserved.update(bench.digest(p) for p in (bench.ROOT / "maps/ladder-pool").glob("*.map26a"))
    for name in ("LARGE_ROSTER_MAPS.json", "DENSE_ROSTER_MAPS.json"):
        reserved.update(read(HERE / name)["maps"].values())
    assert not reserved.intersection(hashes.values())
    manifest = {"seed": MAP_SEED, "source": SOURCE, "source_sha": SOURCE_SHA, "engine_wasm": ENGINE_SHA, "maps": hashes}
    with (HERE / "POST_WARD_MIXED_MAPS.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump(manifest, out, indent=2)
        out.write("\n")
    print("Froze", len(maps), "new mixed-roster maps", flush=True)
    return maps


def main():
    project = bench.ROOT / "bots/codex-cpg-safe-tribute-post-ward"
    release = bench.digest(project / "bot.wasm")
    assert release == read(HERE / "CPG_SAFE_TRIBUTE_POST_WARD_BUILDS.json")["primary"]
    assert all(read(HERE / f"CPG_SAFE_TRIBUTE_POST_WARD_{kind}.json")["pass"] for kind in ("EXACT", "FIXTURE", "HEART"))
    for opponent in DEV:
        file, expected = bench.OPPS[opponent]
        assert bench.digest(bench.CACHE / file) == expected
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    maps = generate()
    wasm = build(project / "src", OUT / "candidate", COMPILED_SEED)
    jobs = [("post-ward", COMPILED_SEED, opponent, mp, side, wasm) for mp in maps for opponent in DEV for side in "AB"]
    rows, affected, slots_by_map = [], [], {}
    with ThreadPoolExecutor(max_workers=10) as pool:
        for row in pool.map(play, jobs):
            slots = sum(p["team"] == "team" + row["side"] for p in row["draft"])
            assert 3 <= slots <= 5 and slots_by_map.setdefault(row["map"], slots) == slots
            rows.append({**row, "slots": slots})
            if row["fuel_outs"] or row["errors"]:
                events = native_fuel(row, OUT, slots=slots)
                assert len(events) == row["fuel_outs"]
                affected.append({**rows[-1], "events": events})
            if len(rows) % 160 == 0:
                print(f"{len(rows)}/{len(jobs)}", flush=True)
    report = {"engine": bench.ENGINE, "release": release, "wasm": bench.digest(wasm), "seed": COMPILED_SEED,
              "map_seed": MAP_SEED, "n": len(rows), "map_slots": dict(Counter(slots_by_map.values())),
              "opponents": {o: bench.OPPS[o][1] for o in DEV}, "fuel": sum(r["fuel_outs"] for r in rows),
              "round1": sum(r["round1_fuel_outs"] for r in rows), "error_cells": sum(r["errors"] for r in rows)}
    with (HERE / "CPG_POST_WARD_MIXED_STRESS.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**report, "affected": affected}, out, indent=2)
        out.write("\n")
    with (OUT / "rows.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump(rows, out, indent=2)
        out.write("\n")
    print(report, flush=True)


if __name__ == "__main__":
    main()
