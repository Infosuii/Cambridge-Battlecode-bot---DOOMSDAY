"""Compare actual bush wrapper costs on identical row-major queries."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from shutil import copytree, copyfile
from zipfile import ZipFile
import json
import re
import subprocess

import ablate_dev as bench

OUT = bench.CACHE / "bush-wrapper-audit"
ARMS = ("v92", "codex-bushlinear", "codex-bushsparse")


def build(arm):
    project = OUT / arm
    source = project / "src"
    copytree(bench.ROOT / f"bots/{arm}/src", source)
    copyfile(Path(__file__).with_name("audit_bush_wrappers.h"), source / "audit_bush_wrappers.h")
    entry = source / "main.cpp"
    data = entry.read_bytes()
    newline = b"\r\n" if b"\r\n" in data else b"\n"
    include = b'#include "draft.h"'
    call = b"                play_draft();"
    assert data.count(include) == data.count(call) == 1
    injected = newline.join([
        b"                static bool audited = false;",
        b"                if (!audited) { audited = true; audit_bush_wrappers(); }",
        call,
    ])
    entry.write_bytes(data.replace(include, include + newline + b'#include "audit_bush_wrappers.h"')
                      .replace(call, injected))
    wasm = project / "bot.wasm"
    with (project / "build.log").open("wb") as log:
        proc = subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm],
                              cwd=bench.ROOT, stdout=log, stderr=subprocess.STDOUT)
    if proc.returncode:
        raise RuntimeError(f"Build failed. See {project / 'build.log'}")
    return wasm


def measure(job):
    arm, mp, wasm = job
    row = bench.one((arm, 0, "v92", mp, "A", wasm), log_limit=1048576)
    assert row["faults"] == 0
    cache = OUT / "games" / f"{arm}-0-v92-{mp.stem}-A"
    native = json.loads((cache / "native.json").read_bytes())
    assert not any(x["timestamp"]["round"] == 0
                   for e in native["events"] if e["kind"] == "fuelExhausted" and e["owner"]["team"] == "teamA"
                   for x in e["entries"])
    (replay,) = cache.glob("*.repl26a")
    with ZipFile(replay) as archive:
        log = archive.read("team-a.stdout").replace(b"\0", b"")
    (line,) = re.findall(rb"CODEX_BUSH_WRAPPER [^\r\n]+", log)
    values = {key.decode(): int(value) for key, value in re.findall(rb"(\w+)=(\d+)", line)}
    assert values["mask_equal"] == 1
    values["labels"] = str(values["labels"])
    return {"arm": arm, "map": mp.name, "map_sha256": bench.digest(mp), **values}


def main():
    bench.OUT = OUT
    frozen, expected = bench.OPPS["v92"]
    assert bench.digest(bench.CACHE / frozen) == expected
    maps = sorted((bench.CACHE / "jd-sets/conf").glob("*.map26a"))
    assert len(maps) == 16
    wasms = {}
    for arm in ARMS:
        wasms[arm] = build(arm)
        print("Built", arm, flush=True)
    (OUT / "games").mkdir()
    jobs = [(arm, mp, wasms[arm]) for mp in maps for arm in ARMS]
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(measure, jobs))
    for start in range(0, len(rows), len(ARMS)):
        group = rows[start:start + len(ARMS)]
        for field in ("map", "map_sha256", "tiles", "components", "labels"):
            assert len({row[field] for row in group}) == 1, (field, group)
    result = {
        "engine_hash": bench.ENGINE,
        "scope": "Native diagnostic. Costs include the same row-major query loop and digest on each arm.",
        "maps": len(maps),
        "fixtures": {arm: bench.digest(wasm) for arm, wasm in wasms.items()},
        "fuel": {arm: sum(r["fuel"] for r in rows if r["arm"] == arm) for arm in ARMS},
        "cells": rows,
    }
    with Path(__file__).with_name("BUSH_WRAPPER_AUDIT.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print({k: v for k, v in result.items() if k != "cells"}, flush=True)


if __name__ == "__main__":
    main()
