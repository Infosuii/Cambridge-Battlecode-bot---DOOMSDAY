"""Count one-round deposit opportunities available before voluntary shop trips."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from shutil import copytree
from zipfile import ZipFile
import argparse
import json
import re
import subprocess

import ablate_dev as bench

OUT = bench.CACHE / "shop-bank-probe"
PROJECT = OUT / "diagnostic"
WASM = PROJECT / "bot.wasm"
OPPONENTS = ("v92", "x3inv")

WRAPPER = r"""    if (rich && !low && !heading_home && round < 300 && gems > 0 && gems <= 10 &&
        !walked && w.enemies.empty() && !bit(w.hot_zone, pos) && w.altar_ready &&
        fdist(w.altar_field, pos) == 0 && !w.no_bank && round >= tribute_off_until &&
        tune::kTributeNearDist + static_cast<int>(std::lround(2.0f * LABK(36))) >= 0 &&
        !lab::active(static_cast<std::int32_t>(my_id), round, 3)) {
        bool nearby_threat = false;
        for (const auto& s : w.sightings)
            nearby_threat |= round - s.round <= 3 && cheb(s.pos, pos) <= 4;
        if (!nearby_threat) {
            for (const vec2 altar : w.altars) {
                if (cheb(altar, pos) > bc::constants::submit_gems_range) continue;
                if (!bc::vision::has_altar_lock(altar) || !bc::vision::altar_lock_at(altar).is_enemy())
                    std::printf("CODEX_SHOP_BANK R%d G%d\n", round, gems);
                break;
            }
        }
    }
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--recount", action="store_true", help="Reuse the finished native games")
    args = ap.parse_args()
    if not args.recount:
        copytree(bench.ROOT / "bots/v92/src", PROJECT / "src")
        bot = PROJECT / "src/bot.cpp"
        source = bot.read_bytes()
        start = source.index(b"bool Bot::go_home_if_needed() {")
        end = source.index(b"bool Bot::tribute_if_needed() {", start)
        anchor = b"    heading_home = true;"
        assert source[start:end].count(anchor) == 1
        patch = WRAPPER.encode()
        if b"\r\n" in source:
            patch = patch.replace(b"\n", b"\r\n")
        bot.write_bytes(source[:start] + source[start:end].replace(anchor, patch + anchor, 1) + source[end:])
        entry = PROJECT / "src/main.cpp"
        data = entry.read_bytes()
        nl = b"\r\n" if b"\r\n" in data else b"\n"
        draft = b"                play_draft();"
        assert data.count(draft) == 1
        capture = [
            b"                static bool capture_announced = false;",
            b'                if (!capture_announced) { std::puts("CODEX_SHOP_BANK_CAPTURE"); capture_announced = true; }',
            draft,
        ]
        entry.write_bytes(data.replace(draft, nl.join(capture), 1))
        subprocess.run([bench.CLI, "build", PROJECT, "--release", "--output", WASM],
                       cwd=bench.ROOT, check=True)

    bench.OUT = OUT
    maps = sorted((bench.CACHE / "jd-sets/conf").glob("*.map26a"))
    assert len(maps) == 16
    for opponent in OPPONENTS:
        path, expected = bench.OPPS[opponent]
        assert bench.digest(bench.CACHE / path) == expected
    jobs = [("diagnostic", 0, opponent, map_path, side, WASM)
            for map_path in maps for opponent in OPPONENTS for side in "AB"]
    if args.recount:
        rows = []
        for arm, seed, opponent, mp, side, _ in jobs:
            cell = OUT / "games" / f"{arm}-{seed}-{opponent}-{mp.stem}-{side}"
            doc = json.loads((cell / "native.json").read_bytes())
            assert doc["match"]["engineBuildHash"] == bench.ENGINE
            assert doc["diagnostics"]["detailedCaptureComplete"]
            team = "team" + side
            rows.append({"opponent":opponent, "map":mp.stem, "side":side,
                         "map_hash":doc["match"]["mapHash"], "engine_seed":doc["match"]["seed"],
                         "faults":doc["diagnostics"]["botFaults"][team], "score":0})
    else:
        (OUT / "games").mkdir()
        with ThreadPoolExecutor(max_workers=6) as pool:
            rows = list(pool.map(lambda job: bench.one(job, log_limit=1048576), jobs))
    for row in rows:
        cell = f"diagnostic-0-{row['opponent']}-{row['map']}-{row['side']}"
        (replay,) = (OUT / "games" / cell).glob("*.repl26a")
        with ZipFile(replay) as archive:
            log = archive.read(f"team-{row['side'].lower()}.stdout").replace(b"\0", b"")
        assert b"CODEX_SHOP_BANK_CAPTURE" in log, cell
        row["observations"] = [(int(r), int(g)) for r, g in re.findall(rb"CODEX_SHOP_BANK R(\d+) G(\d+)", log)]
        assert all(1 <= r < 300 and 1 <= g <= 10 for r, g in row["observations"])
        row.pop("score")
    result = {
        "engine_hash": bench.ENGINE,
        "diagnostic_sha256": bench.digest(WASM),
        "scope": "Charged diagnostic. No change to action priority.",
        "opportunities": sum(len(r["observations"]) for r in rows),
        "affected_maps": sorted({r["map"] for r in rows if r["observations"]}),
        "cells": rows,
    }
    with Path(__file__).with_name("SHOP_BANK_PROBE.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print({k: v for k, v in result.items() if k != "cells"}, flush=True)


if __name__ == "__main__":
    main()
