"""Measure existing current-source profiler stages, preserving all release controls."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
from shutil import copytree
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from bounded_verdict import apply
from engine3_pool import CLI, CLI_HASH, ENGINE, HERE, SDK_ROOT, read
from engine3_qualify import build
from freeze_engine3_discovery import write
from qualify_local import partition


def main():
    assert bench.digest(CLI) == CLI_HASH
    source = SDK_ROOT / "bots/live109/src"
    identity = read(HERE / "LIVE109_SOURCE_VERIFIED.json")
    assert all(bench.digest(source / name) == expected for name, expected in identity["source_file_hashes"].items())
    output = bench.CACHE / "engine3-live109-runtime-profile"
    output.mkdir()
    proposed = output / "source"
    copytree(source, proposed)
    header = proposed / "common.h"
    header.write_bytes(b"#define CLFP 1\n" + header.read_bytes())
    apply(proposed / "clfp.h", ((
        'std::printf("CLFP O %u %d %d\\n", r0, last, id);',
        'std::printf("CLFP O %u %d %d T%d\\n", r0, last, id, static_cast<int>(bc::self().champion_name()));'),))
    off_source = output / "off-source"
    copytree(source, off_source)
    header = off_source / "common.h"
    header.write_bytes(b"#define CLFP 0\n" + header.read_bytes())
    off = build(off_source, SDK_ROOT / "bots/live109-profiler-off-11801", 11801)
    recorded = read(HERE / "ENGINE3_LIVE109_GREEDY_DEV.json")
    assert bench.digest(off) == recorded["binaries"]["base-11801"]
    wasm = build(proposed, SDK_ROOT / "bots/live109-profiler-11801", 11801)
    manifest = read(HERE / "LIVE109_STELLAR_DEV_MAPS.json")
    dev = {mp.name: mp for mp in partition("dev")}
    maps = [min([dev[name] for name, info in manifest.items() if info["category"] == category], key=bench.digest) for category in ("C4", "C5", "C7")]
    opponents = ("x3inv", "public-khiri")
    for opponent in opponents:
        assert bench.digest(bench.CACHE / bench.OPPS[opponent][0]) == bench.OPPS[opponent][1]
    write(HERE / "LIVE109_RUNTIME_PROFILE_PLAN.json", {"off_binary": bench.digest(off), "diagnostic_binary": bench.digest(wasm),
          "source_reference": identity["wasm_sha256"], "maps": {mp.name: bench.digest(mp) for mp in maps}, "opponents": {o: bench.OPPS[o][1] for o in opponents}, "noise_seed": 11801})

    def run(job):
        mp, opponent, side = job
        directory = output / f"{mp.stem}-{side}-{opponent}"
        directory.mkdir()
        reference = bench.CACHE / bench.OPPS[opponent][0]
        bots = (wasm, reference) if side == "A" else (reference, wasm)
        with (directory / "run.log").open("wb") as log:
            subprocess.run([CLI, "run", *bots, "--map", mp, "--release", "--fuel", "100000", "--log-limit", "1048576", "--json", "--statistics", directory / "native.json", "--out-dir", directory], cwd=SDK_ROOT, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
        doc = read(directory / "native.json")
        assert (doc["match"]["engineVersion"], doc["match"]["engineBuildHash"]) == ("3.0.0", ENGINE)
        assert doc["match"]["mapHash"] == bench.digest(mp) and doc["diagnostics"]["detailedCaptureComplete"]
        (bundle,) = directory.glob("*.repl26a")
        with ZipFile(bundle) as archive:
            stdout = archive.read(f"team-{side.lower()}.stdout").replace(b"\0", b"")
        assert len(stdout) < 1048576
        stages = [[int(v) for v in row] for row in re.findall(rb"CLFP O (\d+) (\d+) (\d+) T(\d+)", stdout)]
        def fuel(document):
            return [{"actor": e["owner"]["id"], "name": e["owner"]["name"], "round": x["timestamp"]["round"]} for e in document["events"] if e["kind"] == "fuelExhausted" and e["owner"]["team"] == "team" + side for x in e["entries"]]
        base_directory = bench.CACHE / "engine3-live109-greedy" / f"11801-{opponent}" / f"{mp.stem}-{side}-base"
        baseline = read(base_directory / "native.json")
        assert baseline["match"]["seed"] == doc["match"]["seed"]
        return {"map": mp.stem, "map_hash": bench.digest(mp), "side": side, "opponent": opponent,
                "baseline_directory": base_directory.relative_to(bench.ROOT).as_posix(), "profile_directory": directory.relative_to(bench.ROOT).as_posix(),
                "baseline_events": fuel(baseline), "diagnostic_events": fuel(doc), "stages": stages,
                "faults": doc["diagnostics"]["botFaults"], "codes": doc["diagnostics"]["codes"]}

    jobs = [(mp, opponent, side) for mp in maps for opponent in opponents for side in "AB"]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(run, jobs))
    count = Counter(f"{a}->{b}" for row in rows for r, a, b, champion_type in row["stages"])
    report = {"engine": ENGINE, "n": len(rows), "diagnostic_binary": bench.digest(wasm), "off_matches_recorded_baseline": True,
              "baseline_events": sum(len(r["baseline_events"]) for r in rows), "diagnostic_events": sum(len(r["diagnostic_events"]) for r in rows),
              "stage_crossings": dict(count), "rows": rows}
    write(HERE / "LIVE109_RUNTIME_PROFILE.json", report)
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}, indent=2), flush=True)


if __name__ == "__main__":
    main()
