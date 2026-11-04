"""Test whether either six-round continuation crosses during its farm call."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import re
import subprocess
from zipfile import ZipFile

from bounded_verdict import apply
from cpg_runtime_release import prepare as prepare_cpg
from large_roster_stress import DENSE_OUT, HERE, OUT as GENERATED, bench, native_fuel, read
from pg_dash_followup import read_turn
from pg_travel_scan import prepare as prepare_pg
from qualify_local import build as build_noised

OUT = bench.CACHE / "continuation-farm"
CASES = (
    ("vendetta", 1077, 6, "B", "pool_719360", "x3inv", 0),
    ("marcella", 536, 4, "A", "pool_605209", "public-khiri", 7013),
)
CAMP_STAGES = ("c_zones", "s_inc", "sg_ring", "sg_init", "sg_los", "sg_seeing", "c_safe", "c_walked", "c_cast")


def instrument(src, champion, rnd, split, camp):
    apply(src / "bot.cpp", (
        ('#include "bot.h"', '''#include "bot.h"

static unsigned codex_farm_round;
static unsigned long long codex_farm_before, codex_farm_after;'''),
        ('        if (!farm()) mode = "nofarm";', f'''        const bool codex_sample = round == {rnd} && type == bc::champion_type::{champion};
        if (codex_sample) codex_farm_before = bc::fuel_remaining();
        if (!farm()) mode = "nofarm";
        if (codex_sample) {{
            codex_farm_after = bc::fuel_remaining();
            codex_farm_round = bc::round_number();
        }}'''),
        ("void Bot::play_turn() {", """void Bot::play_turn() {
    if (codex_farm_round) {
        std::printf("CODEX_FARM_BOUNDARY %u %llu %llu\\n", codex_farm_round, codex_farm_before, codex_farm_after);
        codex_farm_round = 0;
    }"""),
    ))
    if split:
        apply(src / "bot.cpp", (
            ("static unsigned codex_farm_round;", """static unsigned codex_farm_round, codex_select_round, codex_move_round;
static unsigned long long codex_select_fuel, codex_move_fuel;
static int codex_farm_group = -1, codex_farm_state = -1;"""),
            ('    PROF_CHECK("farmsel");', '''    PROF_CHECK("farmsel");
    if (round == 1077 && type == bc::champion_type::vendetta) {
        codex_select_fuel = bc::fuel_remaining();
        codex_select_round = bc::round_number();
    }'''),
            ('    PROF_CHECK("farmmove");', '''    PROF_CHECK("farmmove");
    if (round == 1077 && type == bc::champion_type::vendetta) {
        codex_move_fuel = bc::fuel_remaining();
        codex_move_round = bc::round_number();
        codex_farm_group = best;
        codex_farm_state = static_cast<int>(g.state);
    }'''),
            ("        codex_farm_round = 0;", """        std::printf("CODEX_FARM_SPLIT %u %llu %u %llu %d %d\\n",
                    codex_select_round, codex_select_fuel, codex_move_round, codex_move_fuel,
                    codex_farm_group, codex_farm_state);
        codex_farm_round = 0;"""),
        ))
    if camp:
        apply(src / "bot.cpp", (
            ("static int codex_farm_group = -1, codex_farm_state = -1;",
             f'''static int codex_farm_group = -1, codex_farm_state = -1;
static unsigned codex_camp_round[{len(CAMP_STAGES)}];
static unsigned long long codex_camp_fuel[{len(CAMP_STAGES)}];'''),
            *((f'    PROF_CHECK("{phase}");', f'''    PROF_CHECK("{phase}");
    if (round == 1077 && type == bc::champion_type::vendetta) {{
        codex_camp_fuel[{i}] = bc::fuel_remaining();
        codex_camp_round[{i}] = bc::round_number();
    }}''') for i, phase in enumerate(CAMP_STAGES)),
            ("        codex_farm_round = 0;", f'''        for (int i = 0; i < {len(CAMP_STAGES)}; ++i)
            if (codex_camp_round[i])
                std::printf("CODEX_CAMP_PHASE %d %u %llu\\n", i, codex_camp_round[i], codex_camp_fuel[i]);
        codex_farm_round = 0;'''),
        ))


def run(case, split, camp):
    champion, rnd, actor, side, name, opp, seed = case
    src = OUT / f"{champion}/src"
    if seed:
        prepare_pg(src, True)
        mp = GENERATED / "maps" / f"{name}.map26a"
        original = bench.CACHE / f"travel-scan-roster-noise/games/stress-{seed}-{opp}-{name}-{side}"
        original_hash = read(HERE / "TRAVEL_SCAN_ROSTER_NOISE.json")["binaries"][str(seed)]
        manifest = read(HERE / "LARGE_ROSTER_MAPS.json")["maps"]
    else:
        prepare_cpg(src, True, packed=True)
        mp = DENSE_OUT / "maps" / f"{name}.map26a"
        original = bench.CACHE / f"cpg-budget-margin/games/100000-0-{opp}-{name}-{side}"
        original_hash = read(HERE / "CPG_BUDGET_MARGIN.json")["sha256"]
        manifest = read(HERE / "DENSE_ROSTER_MAPS.json")["maps"]
    instrument(src, champion, rnd, split, camp)
    assert bench.digest(mp) == manifest[mp.name]
    file, expected = bench.OPPS[opp]
    assert bench.digest(bench.CACHE / file) == expected
    project = OUT / f"{champion}-build"
    if seed:
        wasm = build_noised(src, project, seed)
    else:
        project = src.parent
        wasm = project / "bot.wasm"
        with (project / "build.log").open("wb") as log:
            subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm], cwd=bench.ROOT,
                           stdout=log, stderr=subprocess.STDOUT, check=True)
    row = bench.one(("profile", seed, opp, mp, side, wasm), fuel=100000, log_limit=1048576)
    new = OUT / "games" / f"profile-{seed}-{opp}-{name}-{side}"
    (archive,) = new.glob("*.repl26a")
    with ZipFile(archive) as z:
        log = z.read(f"team-{side.lower()}.stdout")
    samples = [list(map(int, r)) for r in re.findall(rb"CODEX_FARM_BOUNDARY (\d+) (\d+) (\d+)", log)]
    phases = [list(map(int, r)) for r in re.findall(rb"CODEX_FARM_SPLIT (\d+) (\d+) (\d+) (\d+) (-?\d+) (-?\d+)", log)]
    camp_phases = {CAMP_STAGES[int(i)]: [int(r), int(f)]
                   for i, r, f in re.findall(rb"CODEX_CAMP_PHASE (\d+) (\d+) (\d+)", log)}
    a, b = (read(p / "native.json") for p in (original, new))
    assert all(a["match"][k] == b["match"][k] for k in ("seed", "mapHash", "engineBuildHash"))
    older, newer = (read_turn(p, rnd, side, actor) for p in (original, new))
    same = bool(older and newer and older["observation"] == newer["observation"])
    old_actions = [a for a in older["executed_actions"] if a["kind"] not in (3, 26)] if older else []
    new_actions = [a for a in newer["executed_actions"] if a["kind"] not in (3, 26)] if newer else []
    events = native_fuel(row, OUT)
    matched_event = any(e["timestamp"]["round"] == rnd and e["owner"]["id"] == actor for e in events)
    return {"map": name, "opponent": opp, "round": rnd, "champion": champion, "reference": original_hash,
            "diagnostic": bench.digest(wasm), "same_draft": a["roster"]["draft"] == b["roster"]["draft"],
            "same_observation": same, "same_actions": old_actions == new_actions,
            "native_event": matched_event, "samples": samples, "phases": phases, "camp_phases": camp_phases, "row": row}


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--split", action="store_true")
    modes.add_argument("--camp", action="store_true")
    args = parser.parse_args()
    split = args.split or args.camp
    if args.camp:
        OUT = bench.CACHE / "continuation-farm-camp"
    elif split:
        OUT = bench.CACHE / "continuation-farm-split"
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(lambda c: run(c, split, args.camp), CASES[:1] if split else CASES))
    name = ("CPG_CONTINUATION_CAMP.json" if args.camp else
            "CPG_CONTINUATION_FARM_SPLIT.json" if split else "CPG_CONTINUATION_FARM.json")
    with (HERE / name).open("x", encoding="utf8", newline="\n") as out:
        json.dump({"engine": bench.ENGINE, "rows": rows}, out, indent=2)
        out.write("\n")
    print(rows, flush=True)


if __name__ == "__main__":
    main()
