"""Localize late suspensions in the independent budget-margin fixture."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import re
import subprocess
from zipfile import ZipFile

from bounded_verdict import apply
from cpg_runtime_release import prepare
from large_roster_stress import DENSE_OUT, HERE, bench, native_fuel, read
from pg_dash_followup import read_turn
from probe_budget_margin import OUT as ORIGINAL
from profile_noised_stress import STAGES
from profile_roster_stress import prepare_coarse, summarize_scoped

OUT = bench.CACHE / "cpg-budget-margin-profile"


def instrument_escape(src):
    apply(src / "bot.cpp", (
        ('#include "bot.h"', '''#include "bot.h"

static unsigned codex_home_round;
static unsigned long long codex_home_before, codex_home_after;'''),
        ('''        mode = "home-escape";
        walk_toward(~w.hot_zone & ~w.static_blocked);
        return true;''', '''        mode = "home-escape";
        const bool sample = round == 1077 && type == bc::champion_type::vendetta;
        if (sample) codex_home_before = bc::fuel_remaining();
        walk_toward(~w.hot_zone & ~w.static_blocked);
        if (sample) {
            codex_home_after = bc::fuel_remaining();
            codex_home_round = bc::round_number();
        }
        return true;'''),
        ("void Bot::play_turn() {", '''void Bot::play_turn() {
    if (codex_home_round) {
        if (codex_home_round != 1077)
            std::printf("CODEX_STRESS R1077 t%d home_escape\\n", static_cast<int>(type));
        std::printf("CODEX_HOME_ESCAPE R%u %llu %llu\\n", codex_home_round, codex_home_before, codex_home_after);
        codex_home_round = 0;
    }'''),
    ))


def build(fuel, selected, escape):
    project = OUT / f"diagnostic-{fuel}"
    src = project / "src"
    prepare(src, True, packed=True)
    rounds = {e["timestamp"]["round"] for r in selected for e in r["events"] if e["timestamp"]["round"] > 3}
    if escape:
        instrument_escape(src)
    else:
        prepare_coarse(src, rounds, (*STAGES, "fields", "bushpre"))
    wasm = project / "bot.wasm"
    with (project / "build.log").open("wb") as log:
        subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm], cwd=bench.ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    return wasm


def play(item):
    row, mp, wasm = item
    fuel, opponent, name, side = (row[k] for k in ("arm", "opponent", "map", "side"))
    traced = bench.one((fuel, 0, opponent, mp, side, wasm), fuel=int(fuel), log_limit=1048576)
    key = f"{fuel}-0-{opponent}-{name}-{side}"
    original, diagnostic = (p / "games" / key for p in (ORIGINAL, OUT))
    traced = summarize_scoped(traced, diagnostic)
    (archive,) = diagnostic.glob("*.repl26a")
    with ZipFile(archive) as z:
        log = z.read(f"team-{side.lower()}.stdout")
    traced["escape_samples"] = [list(map(int, s)) for s in re.findall(rb"CODEX_HOME_ESCAPE R(\d+) (\d+) (\d+)", log)]
    a, b = (read(p / "native.json") for p in (original, diagnostic))
    same_draft = a["roster"]["draft"] == b["roster"]["draft"]
    original_events = {(e["timestamp"]["round"], e["owner"]["id"]): e["owner"]["name"] for e in row["events"]}
    current_events = {(e["timestamp"]["round"], e["owner"]["id"]) for e in native_fuel(traced, OUT)}
    confirmed = []
    if same_draft:
        for (r, actor), champion in original_events.items():
            if (r, actor) not in current_events or r <= 3:
                continue
            older, newer = (read_turn(folder, r, side, actor) for folder in (original, diagnostic))
            if not older or not newer or older["observation"] != newer["observation"]:
                continue
            stages = [phase for phase, line in traced["examples"].items() if int(re.search(r" R(\d+)", line)[1]) == r]
            if stages:
                confirmed.append({"round": r, "champion": champion, "stages": stages})
    return {"base": row, "trace": traced, "same_draft": same_draft, "confirmed": confirmed}


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home-escape", action="store_true")
    escape = parser.parse_args().home_escape
    if escape:
        OUT = bench.CACHE / "cpg-budget-home-escape"
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True, exist_ok=True)
    frozen = read(HERE / "CPG_BUDGET_MARGIN.json")
    selected = [r for r in frozen["rows"] if any(e["timestamp"]["round"] > 3 for e in r["events"])]
    assert len(selected) == 6
    fuels = ("80000", "100000")
    if escape:
        fuels = ("100000",)
        selected = [r for r in selected if r["arm"] in fuels]
    maps = {p.stem: p for p in (DENSE_OUT / "maps").glob("*.map26a")}
    for r in selected:
        mp = maps[r["map"]]
        assert bench.digest(mp) == frozen["maps"][mp.name]
        file, expected = bench.OPPS[r["opponent"]]
        assert bench.digest(bench.CACHE / file) == expected
    with ThreadPoolExecutor(max_workers=2) as pool:
        builds = dict(zip(fuels, pool.map(lambda fuel: build(fuel, [r for r in selected if r["arm"] == fuel], escape),
                                         fuels), strict=True))
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(play, ((r, maps[r["map"]], builds[r["arm"]]) for r in selected)))
    result = {"engine": bench.ENGINE, "reference": frozen["sha256"], "n": len(rows),
              "builds": {fuel: bench.digest(wasm) for fuel, wasm in builds.items()},
              "confirmed": sum(len(r["confirmed"]) for r in rows)}
    name = "CPG_BUDGET_HOME_ESCAPE.json" if escape else "CPG_BUDGET_MARGIN_PROFILE.json"
    with (HERE / name).open("x", encoding="utf8", newline="\n") as out:
        json.dump({**result, "rows": rows}, out, indent=2)
        out.write("\n")
    print(result, flush=True)


if __name__ == "__main__":
    main()
