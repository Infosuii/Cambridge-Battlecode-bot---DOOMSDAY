"""Count one-round deposit opportunities consumed by ordinary hunts."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from shutil import copytree
from zipfile import ZipFile
import json
import re
import subprocess

import ablate_dev as bench

OUT = bench.CACHE / "hunt-bank-probe"
PROJECT = OUT / "diagnostic"
WASM = PROJECT / "bot.wasm"
OPPONENTS = ("v92", "x3inv")

WRAPPER = r"""    } else if ([&]() {
        bool ready = round <= 300 && gems > 0 && gems <= 10 && !walked &&
                     w.enemies.empty() && !bit(w.hot_zone, pos) && w.altar_ready &&
                     fdist(w.altar_field, pos) == 0 && !w.no_bank &&
                     round >= tribute_off_until &&
                     !lab::active(static_cast<std::int32_t>(my_id), round, 3);
        if (ready) {
            for (const auto& s : w.sightings) {
                if (round - s.round <= 3 && cheb(s.pos, pos) <= 4) {
                    ready = false;
                    break;
                }
            }
        }
        if (ready) {
            ready = false;
            for (const vec2 a : w.altars) {
                if (cheb(a, pos) <= bc::constants::submit_gems_range &&
                    (!bc::vision::has_altar_lock(a) || !bc::vision::altar_lock_at(a).is_enemy())) {
                    ready = true;
                    break;
                }
            }
        }
        const bool pursued = hunt();
        if (ready && pursued && std::string_view(mode) == "hunt")
            std::printf("CODEX_HUNT_BANK R%d G%d\n", round, gems);
        return pursued;
    }()) {"""


def main():
    copytree(bench.ROOT / "bots/v92/src", PROJECT / "src")
    bot = PROJECT / "src/bot.cpp"
    source = bot.read_bytes()
    anchor = b"    } else if (hunt()) {"
    assert source.count(anchor) == 1
    patch = WRAPPER.encode()
    if b"\r\n" in source:
        patch = patch.replace(b"\n", b"\r\n")
    bot.write_bytes(source.replace(anchor, patch, 1))
    subprocess.run([bench.CLI, "build", PROJECT, "--release", "--output", WASM],
                   cwd=bench.ROOT, check=True)

    bench.OUT = OUT
    maps = sorted((bench.CACHE / "jd-sets/conf").glob("*.map26a"))
    assert len(maps) == 16
    for opponent in OPPONENTS:
        path, expected = bench.OPPS[opponent]
        assert bench.digest(bench.CACHE / path) == expected
    (OUT / "games").mkdir()
    jobs = [("diagnostic", 0, opponent, map_path, side, WASM)
            for map_path in maps for opponent in OPPONENTS for side in "AB"]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(lambda job: bench.one(job, log_limit=1048576), jobs))
    for row in rows:
        cell = f"diagnostic-0-{row['opponent']}-{row['map']}-{row['side']}"
        (replay,) = (OUT / "games" / cell).glob("*.repl26a")
        with ZipFile(replay) as archive:
            log = archive.read(f"team-{row['side'].lower()}.stdout").replace(b"\0", b"")
        row["observations"] = [(int(r), int(g)) for r, g in re.findall(rb"CODEX_HUNT_BANK R(\d+) G(\d+)", log)]
        assert all(1 <= r <= 300 and 1 <= g <= 10 for r, g in row["observations"])
        row.pop("score")
    result = {
        "engine_hash": bench.ENGINE,
        "diagnostic_sha256": bench.digest(WASM),
        "scope": "Charged diagnostic. No change to action priority.",
        "opportunities": sum(len(r["observations"]) for r in rows),
        "affected_maps": sorted({r["map"] for r in rows if r["observations"]}),
        "cells": rows,
    }
    with Path(__file__).with_name("HUNT_BANK_PROBE.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print({k: v for k, v in result.items() if k != "cells"}, flush=True)


if __name__ == "__main__":
    main()
