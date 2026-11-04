"""Generate and run an independent five-slot development runtime diagnostic."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess

import ablate_dev as bench
from qualify_local import DEV, partition, read

HERE = Path(__file__).resolve().parent
OUT = bench.CACHE / "large-roster-stress-604211"
DENSE_OUT = bench.CACHE / "dense-roster-stress-719331"
SOURCE = "548694e1:research/agent2-neural/code/mapmake6.js"
SOURCE_SHA = "5ff5ee85e96fa0e1deb3e871095df03ed1f9d0c077b34fe29f4496333041d763"
ENGINE_SHA = "d910a59eb8a01e1bc4ad4faed1c1f7ca9258b346f895e36446eb88a4d17f3b18"


def generate(output, dense):
    count, seed = (60, 719331) if dense else (100, 604211)
    gen = output / "mapmake6.js"
    gen.write_bytes(subprocess.check_output(["git", "show", SOURCE], cwd=bench.ROOT))
    assert bench.digest(gen) == SOURCE_SHA
    old = b"    const b = makeMap(jit(pw), pw === ph ? jit(pw) : jit(ph), sym, 3 + Math.floor(rng() * 3));"
    new = b"    rng(); // Keep the original roster draw in the random sequence.\n    const b = makeMap(jit(pw), pw === ph ? jit(pw) : jit(ph), sym, 5);"
    data = gen.read_bytes()
    assert data.count(old) == 1
    data = data.replace(old, new)
    if dense:
        for old, new in ((b"const ngroups = 5 +", b"const ngroups = 9 +"),
                         (b"0.015 + rng() * rng() * 0.12", b"0.035 + rng() * rng() * 0.18")):
            assert data.count(old) == 1
            data = data.replace(old, new)
    gen.write_bytes(data)
    folder = Path.home() / "AppData/Local/cambc/assets"
    asset = next(p for p in folder.glob("*/visualiser/assets/v2_0_0-hWOQ1R8f.wasm")
                 if bench.digest(p) == ENGINE_SHA)
    (output / "v2_0_0.wasm").write_bytes(asset.read_bytes())
    with (output / "generate.log").open("wb") as log:
        subprocess.run(["node", gen, output / "maps", str(count), str(seed)], cwd=bench.ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    maps = sorted((output / "maps").glob("*.map26a"))
    digests = {p.name: bench.digest(p) for p in maps}
    assert len(maps) == len(set(digests.values())) == count
    reference = {line.split()[0] for line in (bench.ROOT / "docs/codex/FRESH_HOLDOUT.sha256").read_text().splitlines()}
    reference.update(bench.digest(p) for p in partition("dev"))
    if dense:
        reference.update(read(HERE / "LARGE_ROSTER_MAPS.json")["maps"].values())
    assert not reference.intersection(digests.values())
    manifest = {"seed": seed, "slots": 5, "engine": ENGINE_SHA, "source": SOURCE, "source_sha": SOURCE_SHA,
                "stress_generator_sha": bench.digest(gen), "maps": digests}
    name = "DENSE_ROSTER_MAPS.json" if dense else "LARGE_ROSTER_MAPS.json"
    with (HERE / name).open("x", encoding="utf8", newline="\n") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dense", action="store_true")
    args = parser.parse_args()
    bench.OUT = output = DENSE_OUT if args.dense else OUT
    (output / "games").mkdir(parents=True)
    maps = generate(output, args.dense)
    name, hashes = ("pg-siege-resume", "PG_SIEGE_RESUME") if args.dense else ("pg-ambush", "PG_AMBUSH")
    wasm = bench.ROOT / f"bots/codex-{name}/bot.wasm"
    assert bench.digest(wasm) == read(HERE / f"{hashes}_BUILDS.json")["primary"]
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
        events = native_fuel(r, output)
        assert len(events) == r["fuel_outs"]
        if events or r["faults"] or r["diagnostic_codes"]:
            affected.append({**r, "events": events})
    result = {"engine": bench.ENGINE, "wasm": bench.digest(wasm), "n": len(rows),
              "opponents": {o: bench.OPPS[o][1] for o in DEV}, "fuel": sum(r["fuel_outs"] for r in rows),
              "round1": sum(r["round1_fuel_outs"] for r in rows),
              "fault_or_code_cells": sum(bool(r["faults"] or r["diagnostic_codes"]) for r in rows), "affected": affected}
    (output / "rows.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf8", newline="\n")
    report = "DENSE_ROSTER_STRESS.json" if args.dense else "LARGE_ROSTER_STRESS.json"
    with (HERE / report).open("x", encoding="utf8", newline="\n") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print({k: v for k, v in result.items() if k != "affected"}, flush=True)


if __name__ == "__main__":
    main()
