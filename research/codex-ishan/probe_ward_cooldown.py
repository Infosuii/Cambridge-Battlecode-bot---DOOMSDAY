"""Measure late reactive ward cooldown checks on four frozen dev maps."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from shutil import copytree
from zipfile import ZipFile
import json
import re
import subprocess

import ablate_dev as bench

ROOT = bench.ROOT
OUT = bench.CACHE / "ward-cooldown-probe"
PROJECT = OUT / "diagnostic"
WASM = PROJECT / "bot.wasm"
OPPONENTS = ("v92", "x3inv")


def prepare():
    copytree(ROOT / "bots/v92/src", PROJECT / "src")
    bot = PROJECT / "src/bot.cpp"
    source = bot.read_bytes()
    start = source.index(b"bool Bot::ward_reveal() {")
    end = source.index(b"bool Bot::hidden_here()", start)
    original = b"        if (me.ward_cooldown() > 0) return false;"
    newline = b"\r\n" if b"\r\n" in source else b"\n"
    probe = newline.join([
        b"        if (me.ward_cooldown() > 0) {",
        b'            std::printf("CODEX_WARD_LATE R%d C%d\\n", round, n);',
        b"            return false;",
        b"        }",
    ])
    fragment = source[start:end]
    assert fragment.count(original) == 1
    bot.write_bytes(source[:start] + fragment.replace(original, probe) + source[end:])
    subprocess.run([bench.CLI, "build", PROJECT, "--release", "--output", WASM],
                   cwd=ROOT, check=True)


def run():
    bench.OUT = OUT
    maps = sorted((bench.CACHE / "jd-sets/conf").glob("*.map26a"))
    assert len(maps) == 16
    for opponent in OPPONENTS:
        path, expected = bench.OPPS[opponent]
        assert bench.digest(bench.CACHE / path) == expected
    (OUT / "games").mkdir()
    jobs = [("diagnostic", 0, opponent, map_path, side, WASM)
            for map_path in maps[:4] for opponent in OPPONENTS for side in "AB"]
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(bench.one, jobs))
    for row in rows:
        cell = f"diagnostic-0-{row['opponent']}-{row['map']}-{row['side']}"
        (replay,) = (OUT / "games" / cell).glob("*.repl26a")
        with ZipFile(replay) as archive:
            log = archive.read(f"team-{row['side'].lower()}.stdout").replace(b"\0", b"")
        calls = [(int(r), int(n)) for r, n in re.findall(rb"CODEX_WARD_LATE R(\d+) C(\d+)", log)]
        assert all(1 <= n <= 25 for _, n in calls)
        row["late_positive_cooldown"] = len(calls)
        row["example_rounds"] = [r for r, _ in calls[:6]]
    result = {
        "engine_hash": bench.ENGINE,
        "diagnostic_sha256": bench.digest(WASM),
        "scope": "Charged diagnostic. These outcomes are excluded from release comparisons.",
        "late_positive_cooldown": sum(r["late_positive_cooldown"] for r in rows),
        "cells_with_trigger": sum(r["late_positive_cooldown"] > 0 for r in rows),
        "cells": [{k: v for k, v in r.items() if k != "score"} for r in rows],
    }
    path = Path(__file__).with_name("WARD_COOLDOWN_PROBE.json")
    with path.open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print({k: v for k, v in result.items() if k != "cells"}, flush=True)


if __name__ == "__main__":
    prepare()
    run()
