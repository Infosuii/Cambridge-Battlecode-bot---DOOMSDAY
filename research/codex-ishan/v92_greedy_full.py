"""Verify the fully bounded greedy scan in isolation on frozen v92."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from shutil import copytree
import subprocess

from cpg_greedy_full import apply_full
from large_roster_stress import HERE, bench, read
from qualify_local import DEV
from stress_greedy_pair import play
from stress_mixed_post_ward import OUT as MIXED

OUT = bench.CACHE / "v92-greedy-full-dev"
PRIMARY = bench.ROOT / "bots/codex-v92-greedy-full"


def build(project, enabled):
    src = project / "src"
    copytree(bench.ROOT / "bots/v92/src", src)
    apply_full(src, enabled)
    wasm = project / "bot.wasm"
    with (project / "build.log").open("wb") as log:
        subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm], cwd=bench.ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    return wasm


def main():
    assert read(HERE / "CPG_GREEDY_FULL_PROOF.json")["pass"]
    maps = sorted((MIXED / "maps").glob("*.map26a"), key=lambda p: sha256(f"exp144:{p.name}".encode()).digest())[:20]
    manifest = read(HERE / "POST_WARD_MIXED_MAPS.json")["maps"]
    assert len(maps) == 20 and all(bench.digest(p) == manifest[p.name] for p in maps)
    for opponent in DEV:
        file, expected = bench.OPPS[opponent]
        assert bench.digest(bench.CACHE / file) == expected
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    primary = build(PRIMARY, True)
    rebuilt = build(OUT / "rebuild", True)
    all_off = build(OUT / "off", False)
    builds = {"primary": bench.digest(primary), "rebuild": bench.digest(rebuilt), "off": bench.digest(all_off)}
    file, expected = bench.OPPS["v92"]
    assert builds["primary"] == builds["rebuild"] and builds["off"] == expected
    with (HERE / "V92_GREEDY_FULL_BUILDS.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump(builds, out, indent=2)
        out.write("\n")
    print(builds, flush=True)
    binaries = {"base": bench.CACHE / file, "full": primary}
    jobs = [(arm, 0, opponent, mp, side, wasm) for mp in maps for opponent in DEV
            for side in "AB" for arm, wasm in binaries.items()]
    rows = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for row in pool.map(play, jobs):
            rows.append(row)
            if len(rows) % 80 == 0:
                print(f"{len(rows)}/{len(jobs)}", flush=True)
    pairs = list(zip(rows[::2], rows[1::2], strict=True))
    assert all(all(a[k] == b[k] for k in ("map_hash", "engine_seed", "opponent", "side")) for a, b in pairs)
    errors = sum(r["errors"] for r in rows)
    draft_changes = sum(a["draft"] != b["draft"] for a, b in pairs)
    increases = sum(b["fuel_outs"] > a["fuel_outs"] or b["round1_fuel_outs"] > a["round1_fuel_outs"] for a, b in pairs)
    result = {"engine": bench.ENGINE, "release": builds["primary"], "reference": expected, "n_pairs": len(pairs),
              "maps": {p.name: manifest[p.name] for p in maps}, "opponents": {o: bench.OPPS[o][1] for o in DEV},
              "outcomes": bench.summary(pairs), "error_cells": errors, "draft_changes": draft_changes,
              "fuel_increases": increases, "pass": len(pairs) == 160 and not errors and not draft_changes and not increases}
    with (HERE / "V92_GREEDY_FULL_DEV.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    with (OUT / "rows.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump(rows, out, indent=2)
        out.write("\n")
    print({k: v for k, v in result.items() if k not in ("maps", "opponents")}, flush=True)


if __name__ == "__main__":
    main()
