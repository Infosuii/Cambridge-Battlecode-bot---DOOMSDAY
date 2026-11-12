"""Probe unused basic attacks on early staging turns without taking them."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from shutil import copytree
from zipfile import ZipFile
import json
import re
import subprocess

import ablate_dev as bench

OUT = bench.CACHE / "stage-chip-probe"
PROJECT = OUT / "diagnostic"
WASM = PROJECT / "bot.wasm"
OPPONENTS = ("v92", "x3inv")
SIEGE_RETURN = b"            if (best >= 0) cast_on_camp(best);"
STAGE_RETURN = b"            if (!w.camps[ci].dead && bit(w.visible, w.camps[ci].pos) && cast_on_camp(ci)) break;"


def prepare():
    copytree(bench.ROOT / "bots/v92/src", PROJECT / "src")
    bot = PROJECT / "src/bot.cpp"
    source = bot.read_bytes()
    newline = b"\r\n" if b"\r\n" in source else b"\n"
    start = source.index(b"bool Bot::fight_camps(GroupRec& g, int need) {")
    end = source.index(newline.join([b"    staging_since = -1;", b"    staging_walk_since = -1;"]), start)
    fragment = source[start:end]
    for anchor, indent, phase in [(SIEGE_RETURN, 12, "siege"), (STAGE_RETURN, 8, "stage")]:
        assert fragment.count(anchor) == 1
        lines = [
            "if (round <= 150 && !walked && !cast_done && w.enemies.empty() &&",
            "    !bit(danger_zone, pos) && !bit(w.hot_zone, pos) &&",
            "    bc::self().can_attack() && pick_target() >= 0) {",
            f'    std::printf("CODEX_CHIP {phase} R%d\\n", round);',
            "}",
        ]
        body = newline.join(b" " * indent + line.encode() for line in lines)
        fragment = fragment.replace(anchor, anchor + newline + body, 1)
    bot.write_bytes(source[:start] + fragment + source[end:])
    subprocess.run([bench.CLI, "build", PROJECT, "--release", "--output", WASM],
                   cwd=bench.ROOT, check=True)


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
        rows = list(pool.map(lambda job: bench.one(job, log_limit=1048576), jobs))
    for row in rows:
        cell = f"diagnostic-0-{row['opponent']}-{row['map']}-{row['side']}"
        (replay,) = (OUT / "games" / cell).glob("*.repl26a")
        with ZipFile(replay) as archive:
            log = archive.read(f"team-{row['side'].lower()}.stdout").replace(b"\0", b"")
        matches = re.findall(rb"CODEX_CHIP (siege|stage) R(\d+)", log)
        assert all(1 <= int(r) <= 150 for _, r in matches)
        row["opportunities"] = len(matches)
        row["examples"] = [(mode.decode(), int(r)) for mode, r in matches[:6]]
        row.pop("score")
    result = {
        "engine_hash": bench.ENGINE,
        "diagnostic_sha256": bench.digest(WASM),
        "scope": "Charged diagnostic. No change to attack decisions.",
        "opportunities": sum(r["opportunities"] for r in rows),
        "cells_with_trigger": sum(r["opportunities"] > 0 for r in rows),
        "cells": rows,
    }
    with Path(__file__).with_name("STAGE_CHIP_PROBE.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print({k: v for k, v in result.items() if k != "cells"}, flush=True)


if __name__ == "__main__":
    prepare()
    run()
