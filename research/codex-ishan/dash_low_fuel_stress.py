"""Measure the successful-dash boundary across independent stress maps."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
import re
import subprocess
from zipfile import ZipFile

from bounded_verdict import apply
from large_roster_stress import HERE, OUT as MAPS, bench, read
from pg_siege_resume import prepare
from qualify_local import DEV

OUT = bench.CACHE / "dash-low-fuel-stress"


def instrument(src):
    bot = src / "bot.cpp"
    apply(bot, (
        ('#include "bot.h"', '''#include "bot.h"

static struct CodexDashStress {
    bool pending = false;
    int round = 0;
    int champion = 0;
    int distance = 0;
    std::uint64_t fuel = 0;
    vec2 destination{};
} codex_dash_stress;'''),
        ('''                return true;
            }
        } catch (const std::exception& e) {
            LOG("dash error %s\\n", e.what());''', '''                const std::uint64_t left = bc::fuel_remaining();
                if (left < rb::kTailReserve && best_d > 0)
                    codex_dash_stress = {true, round, static_cast<int>(type), best_d, left, pos};
                return true;
            }
        } catch (const std::exception& e) {
            LOG("dash error %s\\n", e.what());'''),
        ("void Bot::play_turn() {", '''void Bot::play_turn() {
    if (codex_dash_stress.pending) {
        const auto& s = codex_dash_stress;
        std::printf("CODEX_DASH_STRESS R%d t%d d%d fuel%llu x%d y%d\\n", s.round, s.champion, s.distance,
                    static_cast<unsigned long long>(s.fuel), s.destination.x, s.destination.y);
        codex_dash_stress.pending = false;
    }'''),
    ))


def play(job):
    row = bench.one(job, log_limit=1048576)
    case = OUT / "games" / f"stress-0-{row['opponent']}-{row['map']}-{row['side']}"
    with ZipFile(next(case.glob("*.repl26a"))) as bundle:
        log = bundle.read(f"team-{row['side'].lower()}.stdout")
    assert len(log) < 1048576
    pattern = rb"CODEX_DASH_STRESS R(\d+) t(\d+) d(\d+) fuel(\d+) x(\d+) y(\d+)"
    observations = [tuple(int(v) for v in m) for m in re.findall(pattern, log)]
    assert all(0 <= fuel < 6000 and distance > 0 for _, _, distance, fuel, _, _ in observations)
    return {**row, "observations": observations}


def main():
    bench.OUT = OUT
    project = OUT / "diagnostic"
    prepare(project / "src", True)
    instrument(project / "src")
    wasm = project / "bot.wasm"
    with (OUT / "build.log").open("wb") as log:
        subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm], cwd=bench.ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    manifest = read(HERE / "LARGE_ROSTER_MAPS.json")["maps"]
    maps = sorted((MAPS / "maps").glob("*.map26a"))
    assert len(maps) == 100 and {m.name: bench.digest(m) for m in maps} == manifest
    for o in DEV:
        file, expected = bench.OPPS[o]
        assert bench.digest(bench.CACHE / file) == expected
    (OUT / "games").mkdir()
    jobs = [("stress", 0, o, m, s, wasm) for m in maps for o in DEV for s in "AB"]
    rows = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        for row in pool.map(play, jobs):
            rows.append(row)
            if len(rows) % 160 == 0:
                print(f"{len(rows)}/{len(jobs)}", flush=True)
    affected = [r for r in rows if r["observations"]]
    by_map = Counter({m: sum(len(r["observations"]) for r in affected if r["map"] == m) for m in {r["map"] for r in affected}})
    result = {"engine": bench.ENGINE, "wasm": bench.digest(wasm), "n": len(rows), "maps": dict(by_map),
              "error_cells": sum(bool(r["faults"] or r["diagnostic_codes"]) for r in rows),
              "n_events": sum(by_map.values()), "affected": affected}
    with (HERE / "DASH_LOW_FUEL_STRESS.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print({k: v for k, v in result.items() if k != "affected"}, flush=True)


if __name__ == "__main__":
    main()
