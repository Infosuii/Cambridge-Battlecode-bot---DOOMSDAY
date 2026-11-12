"""Measure the exact camp-strike boundary on the five registered dense cells."""
from concurrent.futures import ThreadPoolExecutor
import json
import re
import subprocess
from zipfile import ZipFile

from bounded_verdict import apply
from large_roster_stress import DENSE_OUT as STRESS, HERE, bench, native_fuel, read
from pg_camp_strike import prepare as prepare_local
from pg_siege_resume import prepare as prepare_base

OUT = bench.CACHE / "camp-strike-budget"


def instrument(src):
    apply(src / "bot.cpp", (
        ('#include "bot.h"', '''#include "bot.h"

struct CodexStrikeBudget {
    int round;
    unsigned before_round, after_round;
    unsigned long long before_fuel, after_fuel;
};
static CodexStrikeBudget codex_strike_budget[4];
static int codex_strike_count = 0;'''),
        ("        int best_hits = 0, best_home = kUnreach;", '''        CodexStrikeBudget* sample = nullptr;
        if ((round == 51 || round == 229) && codex_strike_count < 4) {
            sample = &codex_strike_budget[codex_strike_count++];
            *sample = {round, bc::round_number(), 0, bc::fuel_remaining(), 0};
        }
        int best_hits = 0, best_home = kUnreach;'''),
        ("        if (best.x < 0 || best_hits <= 0) return false;", '''        if (sample) {
            sample->after_round = bc::round_number();
            sample->after_fuel = bc::fuel_remaining();
        }
        if (best.x < 0 || best_hits <= 0) return false;'''),
        ("void Bot::play_turn() {", '''void Bot::play_turn() {
    for (int i = 0; i < codex_strike_count; ++i) {
        const auto& s = codex_strike_budget[i];
        std::printf("CODEX_STRIKE_BUDGET R%d beforeR%u fuel%llu afterR%u fuel%llu\\n",
                    s.round, s.before_round, s.before_fuel, s.after_round, s.after_fuel);
    }
    codex_strike_count = 0;'''),
    ))


def build(arm, prepare):
    project = OUT / arm
    src = project / "src"
    prepare(src, True)
    instrument(src)
    wasm = project / "bot.wasm"
    with (project / "build.log").open("wb") as log:
        subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm], cwd=bench.ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    return wasm


def play(job):
    row = bench.one(job, log_limit=1048576)
    case = OUT / "games" / f"{row['arm']}-0-{row['opponent']}-{row['map']}-{row['side']}"
    with ZipFile(next(case.glob("*.repl26a"))) as bundle:
        log = bundle.read(f"team-{row['side'].lower()}.stdout")
    pattern = rb"CODEX_STRIKE_BUDGET R(\d+) beforeR(\d+) fuel(\d+) afterR(\d+) fuel(\d+)"
    samples = [tuple(int(v) for v in m) for m in re.findall(pattern, log)]
    events = [(e["owner"]["name"], e["timestamp"]["round"]) for e in native_fuel(row, OUT)]
    return {**row, "samples": samples, "events": events}


def main():
    profile = read(HERE / "DENSE_ROSTER_PROFILE.json")
    targets = [r for r in profile["matches"] if "camp_dash_done" in r["phases"]]
    assert len(targets) == 5
    maps = {p.stem: p for p in (STRESS / "maps").glob("*.map26a")}
    manifest = read(HERE / "DENSE_ROSTER_MAPS.json")["maps"]
    for r in targets:
        mp = maps[r["map"]]
        assert bench.digest(mp) == manifest[mp.name]
        file, expected = bench.OPPS[r["opponent"]]
        assert bench.digest(bench.CACHE / file) == expected
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        b = pool.submit(build, "base", prepare_base)
        c = pool.submit(build, "local", prepare_local)
        bins = {"base": b.result(), "local": c.result()}
    jobs = [(arm, 0, r["opponent"], maps[r["map"]], r["side"], wasm) for r in targets for arm, wasm in bins.items()]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(play, jobs))
    exact = {(r["map"], r["opponent"], r["side"]): r for r in profile["rows"]}
    for r in rows:
        old = exact[r["map"], r["opponent"], r["side"]]
        assert all(r[k] == old[k] for k in ("map_hash", "engine_seed"))
    result = {"binaries": {a: bench.digest(p) for a, p in bins.items()}, "engine": bench.ENGINE, "rows": rows}
    with (HERE / "CAMP_STRIKE_BUDGET.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    for r in rows:
        print(r["arm"], r["map"], r["opponent"], r["side"], r["samples"], r["events"], flush=True)


if __name__ == "__main__":
    main()
