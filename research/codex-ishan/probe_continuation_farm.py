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
FORK_STAGES = ("s_dps", "s_stage", "c_staged", "stage_before", "stage_after", "disengage_before", "disengage_after")


def camp_sample(phase):
    index = (CAMP_STAGES + FORK_STAGES).index(phase)
    return f'''    if (round == 1077 && type == bc::champion_type::vendetta) {{
        codex_camp_fuel[{index}] = bc::fuel_remaining();
        codex_camp_round[{index}] = bc::round_number();
    }}'''


def instrument(src, champion, rnd, split, camp, fork, greedy):
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
        phases = CAMP_STAGES + FORK_STAGES[:3] if fork else CAMP_STAGES
        size = len(CAMP_STAGES + FORK_STAGES)
        apply(src / "bot.cpp", (
            ("static int codex_farm_group = -1, codex_farm_state = -1;",
             f'''static int codex_farm_group = -1, codex_farm_state = -1;
static unsigned codex_camp_round[{size}];
static unsigned long long codex_camp_fuel[{size}];'''),
            *((f'    PROF_CHECK("{phase}");', f'    PROF_CHECK("{phase}");\n' + camp_sample(phase))
              for phase in phases),
            ("        codex_farm_round = 0;", f'''        for (int i = 0; i < {size}; ++i)
            if (codex_camp_round[i])
                std::printf("CODEX_CAMP_PHASE %d %u %llu\\n", i, codex_camp_round[i], codex_camp_fuel[i]);
        codex_farm_round = 0;'''),
        ))
    if fork:
        apply(src / "bot.cpp", (
            ("        if (!bit(stage, pos)) walk_toward(stage);",
             "        if (!bit(stage, pos)) {\n" + camp_sample("stage_before") +
             "\n            walk_toward(stage);\n" + camp_sample("stage_after") + "\n        }"),
            ("        if (!moved) walk_toward(~danger_zone & ~w.static_blocked);",
             "        if (!moved) {\n" + camp_sample("disengage_before") +
             "\n            walk_toward(~danger_zone & ~w.static_blocked);\n" +
             camp_sample("disengage_after") + "\n        }"),
        ))
    if greedy:
        apply(src / "bot.cpp", (
            ('#include "bot.h"', '''#include "bot.h"

static unsigned codex_greedy_round, codex_goal_count;
static unsigned long long codex_greedy_before, codex_greedy_after;
static int codex_goal_distance;'''),
            ("    int gd = 1 << 20;\n    for (vec2 g : goals.positions()) {", """    int gd = 1 << 20;
    const bool sample = round == 1077 && type == bc::champion_type::vendetta;
    if (sample) {
        codex_goal_count = goals.count();
        codex_greedy_before = bc::fuel_remaining();
    }
    for (vec2 g : goals.positions()) {"""),
            ("    if (goal.x < 0) return false;\n    const bc::bitboard blocked = w.static_blocked | w.unit_tiles;", """    if (sample) {
        codex_greedy_after = bc::fuel_remaining();
        codex_greedy_round = bc::round_number();
        codex_goal_distance = gd;
    }
    if (goal.x < 0) return false;
    const bc::bitboard blocked = w.static_blocked | w.unit_tiles;"""),
            ("void Bot::play_turn() {", """void Bot::play_turn() {
    if (codex_greedy_round) {
        std::printf("CODEX_GREEDY_PHASE %u %u %llu %llu %d\\n", codex_greedy_round, codex_goal_count,
                    codex_greedy_before, codex_greedy_after, codex_goal_distance);
        codex_greedy_round = 0;
    }"""),
        ))


def run(case, split, camp, fork, greedy):
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
    instrument(src, champion, rnd, split, camp, fork, greedy)
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
    camp_phases = {(CAMP_STAGES + FORK_STAGES)[int(i)]: [int(r), int(f)]
                   for i, r, f in re.findall(rb"CODEX_CAMP_PHASE (\d+) (\d+) (\d+)", log)}
    greedy_samples = [list(map(int, r)) for r in re.findall(rb"CODEX_GREEDY_PHASE (\d+) (\d+) (\d+) (\d+) (\d+)", log)]
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
            "native_event": matched_event, "samples": samples, "phases": phases, "camp_phases": camp_phases,
            "greedy_samples": greedy_samples, "row": row}


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--split", action="store_true")
    modes.add_argument("--camp", action="store_true")
    modes.add_argument("--fork", action="store_true")
    modes.add_argument("--greedy", action="store_true")
    args = parser.parse_args()
    split = args.split or args.camp or args.fork or args.greedy
    if args.greedy:
        OUT = bench.CACHE / "continuation-farm-greedy"
    elif args.fork:
        OUT = bench.CACHE / "continuation-farm-fork"
    elif args.camp:
        OUT = bench.CACHE / "continuation-farm-camp"
    elif split:
        OUT = bench.CACHE / "continuation-farm-split"
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(lambda c: run(c, split, args.camp or args.fork, args.fork, args.greedy),
                             CASES[:1] if split else CASES))
    name = ("CPG_CONTINUATION_GREEDY.json" if args.greedy else "CPG_CONTINUATION_FORK.json" if args.fork else
            "CPG_CONTINUATION_CAMP.json" if args.camp else
            "CPG_CONTINUATION_FARM_SPLIT.json" if split else "CPG_CONTINUATION_FARM.json")
    with (HERE / name).open("x", encoding="utf8", newline="\n") as out:
        json.dump({"engine": bench.ENGINE, "rows": rows}, out, indent=2)
        out.write("\n")
    print(rows, flush=True)


if __name__ == "__main__":
    main()
