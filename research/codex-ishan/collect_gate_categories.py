"""Read the existing atlas classifier on frozen maps using a charged diagnostic."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
import re
from shutil import copytree
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import CLI, CLI_HASH, HERE, SDK_ROOT, read
from qualify_local import partition


def collect(item):
    mp, wasm, directory = item
    directory.mkdir()
    with (directory / "run.log").open("wb") as log:
        subprocess.run([CLI, "run", wasm, SDK_ROOT / "bots/v92-e3/bot.wasm", "--map", mp,
                        "--release", "--rounds", "1", "--log-limit", "1048576", "--out-dir", directory],
                       cwd=SDK_ROOT, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=120)
    (bundle,) = directory.glob("*.repl26a")
    with ZipFile(bundle) as archive:
        stdout = archive.read("team-a.stdout")
    categories = {int(n) for n in re.findall(rb"CODEX_CATEGORY (\d+)", stdout)}
    assert len(categories) == 1 and categories.issubset(range(1, 8)), (mp, categories)
    category = "C" + str(categories.pop())
    return {"map": mp.stem, "map_hash": bench.digest(mp), "category": category,
            "atlas_lines": [line.decode().strip("\x00") for line in stdout.splitlines() if b"ATLAS fp=" in line]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("dev", "select"))
    parser.add_argument("--resume-build", action="store_true")
    args = parser.parse_args()
    assert bench.digest(CLI) == CLI_HASH
    project = SDK_ROOT / "bots" / f"atlas-category-canonical-{args.stage}"
    source = project / "src"
    copytree(SDK_ROOT / "bots/retry-e3/src", source, dirs_exist_ok=args.resume_build)
    (source / "main.cpp").write_bytes((HERE / "map_category_probe.cpp").read_bytes())
    wasm = project / "bot.wasm"
    with (project / "build.log").open("wb") as log:
        subprocess.run([CLI, "build", project, "--release", "--output", wasm], cwd=SDK_ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    output = bench.CACHE / f"engine3-categories-canonical-{args.stage}"
    output.mkdir()
    maps = partition(args.stage)
    if args.stage == "dev":
        maps = [*sorted((bench.ROOT / "maps/ladder-pool").glob("*.map26a")), *maps]
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(collect, ((mp, wasm, output / mp.stem) for mp in maps)))
    by_map = {r["map"]: r for r in rows}
    if args.stage == "dev":
        expected = read(bench.ROOT / "research/x3/atlas/categories.json")
        assert all(by_map[name]["category"] == category for name, category in expected.items())
    else:
        assert read(HERE / "ENGINE3_CATEGORIES_DEV.json")["pool_atlas_verified"]
    wanted = {mp.stem for mp in partition(args.stage)}
    counts = Counter(r["category"] for r in rows if r["map"] in wanted)
    result = {"stage": args.stage, "n_maps": len(rows), "categories": counts,
              "pool_atlas_verified": True, "diagnostic_wasm": bench.digest(wasm),
              "atlas_source": bench.digest(source / "x1_atlas.h"),
              "classifier_source": bench.digest(source / "x1_categories.h"),
              "rules_sha256": bench.digest(bench.ROOT / "research/x3/atlas/categories_rules.json"), "maps": by_map}
    with (HERE / f"ENGINE3_CATEGORIES_{args.stage.upper()}.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print({k: v for k, v in result.items() if k != "maps"}, flush=True)


if __name__ == "__main__":
    main()
