"""Generate and run an independent five-slot development runtime diagnostic."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess

import ablate_dev as bench
from qualify_local import DEV, partition, read

HERE = Path(__file__).resolve().parent
OUT = bench.CACHE / "large-roster-stress-604211"
SOURCE = "548694e1:research/agent2-neural/code/mapmake6.js"
SOURCE_SHA = "5ff5ee85e96fa0e1deb3e871095df03ed1f9d0c077b34fe29f4496333041d763"
ENGINE_SHA = "d910a59eb8a01e1bc4ad4faed1c1f7ca9258b346f895e36446eb88a4d17f3b18"


def generate():
    gen = OUT / "mapmake6.js"
    gen.write_bytes(subprocess.check_output(["git", "show", SOURCE], cwd=bench.ROOT))
    assert bench.digest(gen) == SOURCE_SHA
    old = b"    const b = makeMap(jit(pw), pw === ph ? jit(pw) : jit(ph), sym, 3 + Math.floor(rng() * 3));"
    new = b"    rng(); // Keep the original roster draw in the random sequence.\n    const b = makeMap(jit(pw), pw === ph ? jit(pw) : jit(ph), sym, 5);"
    data = gen.read_bytes()
    assert data.count(old) == 1
    gen.write_bytes(data.replace(old, new))
    folder = Path.home() / "AppData/Local/cambc/assets"
    asset = next(p for p in folder.glob("*/visualiser/assets/v2_0_0-hWOQ1R8f.wasm")
                 if bench.digest(p) == ENGINE_SHA)
    (OUT / "v2_0_0.wasm").write_bytes(asset.read_bytes())
    with (OUT / "generate.log").open("wb") as log:
        subprocess.run(["node", gen, OUT / "maps", "100", "604211"], cwd=bench.ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    maps = sorted((OUT / "maps").glob("*.map26a"))
    digests = {p.name: bench.digest(p) for p in maps}
    assert len(maps) == len(set(digests.values())) == 100
    reference = {line.split()[0] for line in (bench.ROOT / "docs/codex/FRESH_HOLDOUT.sha256").read_text().splitlines()}
    reference.update(bench.digest(p) for p in partition("dev"))
    assert not reference.intersection(digests.values())
    manifest = {"seed": 604211, "slots": 5, "engine": ENGINE_SHA, "source": SOURCE, "source_sha": SOURCE_SHA,
                "stress_generator_sha": bench.digest(gen), "maps": digests}
    (HERE / "LARGE_ROSTER_MAPS.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf8", newline="\n")
    print("Froze", len(maps), "unique diagnostic maps", flush=True)
    return maps


def native_fuel(row, output=OUT):
    case = output / "games" / f"{row['arm']}-{row['noise_seed']}-{row['opponent']}-{row['map']}-{row['side']}"
    native = read(case / "native.json")
    team = "team" + row["side"]
    assert sum(p["team"] == team for p in native["roster"]["draft"]) == 5
    return [{"owner": e["owner"], "timestamp": x["timestamp"]} for e in native["events"]
            if e["kind"] == "fuelExhausted" and e["owner"]["team"] == team for x in e["entries"]]


def main():
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    maps = generate()
    wasm = bench.ROOT / "bots/codex-pg-ambush/bot.wasm"
    assert bench.digest(wasm) == read(HERE / "PG_AMBUSH_BUILDS.json")["primary"]
    for opponent in DEV:
        file, expected = bench.OPPS[opponent]
        assert bench.digest(bench.CACHE / file) == expected
    jobs = [("stress", 0, o, m, s, wasm) for m in maps for o in DEV for s in "AB"]
    rows = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        for row in pool.map(bench.one, jobs):
            rows.append(row)
            if len(rows) % 160 == 0:
                print(f"{len(rows)}/{len(jobs)}", flush=True)
    affected = []
    for r in rows:
        events = native_fuel(r)
        assert len(events) == r["fuel_outs"]
        if events or r["faults"] or r["diagnostic_codes"]:
            affected.append({**r, "events": events})
    result = {"engine": bench.ENGINE, "wasm": bench.digest(wasm), "n": len(rows),
              "opponents": {o: bench.OPPS[o][1] for o in DEV}, "fuel": sum(r["fuel_outs"] for r in rows),
              "round1": sum(r["round1_fuel_outs"] for r in rows),
              "fault_or_code_cells": sum(bool(r["faults"] or r["diagnostic_codes"]) for r in rows), "affected": affected}
    (OUT / "rows.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf8", newline="\n")
    (HERE / "LARGE_ROSTER_STRESS.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf8", newline="\n")
    print({k: v for k, v in result.items() if k != "affected"}, flush=True)


if __name__ == "__main__":
    main()
