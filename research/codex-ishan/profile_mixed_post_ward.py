"""Trace the standard-budget Heart crossings on the frozen mixed-roster fixture."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json

from bounded_verdict import apply
from cpg_safe_tribute_cap import prepare
from large_roster_stress import HERE, bench, read
import profile_cast_path_stress as trace
from profile_roster_stress import prepare_coarse
from qualify_local import build
from stress_mixed_post_ward import COMPILED_SEED, OUT as RAW

OUT = bench.CACHE / "post-ward-mixed-heart-trace"
STAGES = ("world", "support", "wardrev", "ambush", "e_in", "e_td", "e_prefight", "enemies",
          "route0", "farmsel", "c_zones", "c_cast", "d_farm", "decide", "tail", "fields", "bushpre")


def instrument_farm(src, condition):
    count = len(trace.FARM_PHASES)
    scoped = f"({condition}) && type == bc::champion_type::heart_of_ruin"

    def sample(phase):
        return f"if ({scoped}) codex_mixed_sample({trace.FARM_PHASES.index(phase)});"

    apply(src / "bot.cpp", (
        ('#include "bot.h"', f'''#include "bot.h"

static unsigned codex_mixed_round[{count}];
static unsigned long long codex_mixed_fuel[{count}];
static int codex_mixed_state = -1;
static bool codex_mixed_altar, codex_mixed_gated, codex_mixed_no_bank;

[[gnu::noinline]] static void codex_mixed_sample(int phase) {{
    codex_mixed_round[phase] = bc::round_number();
    codex_mixed_fuel[phase] = bc::fuel_remaining();
}}'''),
        ('        if (!farm()) mode = "nofarm";', '        ' + sample("farm_begin") + '\n        if (!farm()) mode = "nofarm";'),
        *((f'PROF_CHECK("{p}");', f'PROF_CHECK("{p}"); ' + sample(p)) for p in ("farmsel", "farmmove", "f_alive")),
        ('    switch (g.state) {\n    case GroupState::reward: {\n        mode = "capture";', f'''    if ({scoped}) {{
        codex_mixed_state = static_cast<int>(g.state);
        codex_mixed_altar = w.altar_ready;
        codex_mixed_gated = w.altar_gated;
        codex_mixed_no_bank = w.no_bank;
    }}
    switch (g.state) {{
    case GroupState::reward: {{
        mode = "capture";'''),
        ('        if (!walk_toward(g.tiles) && walk_unreachable) {',
         '        ' + sample("reward_walk_before") + '\n        if (!walk_toward(g.tiles) && walk_unreachable) {'),
        ('    case GroupState::respawning: {\n        mode = "wait-respawn";',
         '    case GroupState::respawning: {\n        ' + sample("wait_begin") + '\n        mode = "wait-respawn";'),
        ('            if (gems >= 10 && wait > altar_trip + 2) {\n                force_tribute = true;',
         '            if (gems >= 10 && wait > altar_trip + 2) {\n                ' + sample("bank_before") +
         '\n                force_tribute = true;'),
        ('        if (bit(g.tiles, pos) || !bit(goal, pos)) walk_toward(goal);',
         '        if (bit(g.tiles, pos) || !bit(goal, pos)) {\n            ' + sample("wait_walk_before") +
         '\n            walk_toward(goal);\n        }'),
        ('        PROF_CHECK("d_farm");', f'''        PROF_CHECK("d_farm");
        {sample("d_farm")}
        if ({scoped}) {{
            if (static_cast<int>(codex_mixed_round[{trace.FARM_PHASES.index('d_farm')}]) != round) {{
                std::printf("CODEX_PATH_STATE %d %d %d %d %d\\n", round, codex_mixed_state,
                            codex_mixed_altar, codex_mixed_gated, codex_mixed_no_bank);
                for (int i = 0; i < {count}; ++i)
                    if (codex_mixed_round[i])
                        std::printf("CODEX_PATH_FARM %d %d %u %llu\\n", round, i,
                                    codex_mixed_round[i], codex_mixed_fuel[i]);
            }}
            for (int i = 0; i < {count}; ++i) codex_mixed_round[i] = 0;
            codex_mixed_state = -1;
        }}'''),
    ))


def build_trace(directory, rounds, phase=None):
    (directory / "games").mkdir(parents=True)
    src = directory / "source/src"
    prepare(src, True, post_ward=True)
    condition = " || ".join(f"round == {rnd}" for rnd in rounds)
    if phase == "farm":
        instrument_farm(src, condition)
    elif phase == "farm-state":
        marker = 'PROF_CHECK("d_farm");'
        apply(src / "bot.cpp", ((marker, marker + f'''
        if (({condition}) && type == bc::champion_type::heart_of_ruin && static_cast<int>(bc::round_number()) != round) {{
            const int state = target_group >= 0 && static_cast<std::size_t>(target_group) < w.groups.size()
                ? static_cast<int>(w.groups[static_cast<std::size_t>(target_group)].state) : -1;
            std::printf("CODEX_STRESS R%d t%d d_farm\\n", round, static_cast<int>(type));
            std::printf("CODEX_PATH_MODE %d %s %d %d %d %d\\n", round, mode, target_group, state,
                        force_tribute, ward_refreshed_this_turn);
        }}'''),))
    elif phase:
        marker = f'PROF_CHECK("{phase}");'
        apply(src / "bot.cpp", ((marker, marker + f'''
    if (({condition}) && type == bc::champion_type::heart_of_ruin && static_cast<int>(bc::round_number()) != round)
        std::printf("CODEX_STRESS R%d t%d {phase}\\n", round, static_cast<int>(type));'''),))
    else:
        prepare_coarse(src, rounds, STAGES)
        apply(src / "bot.cpp", ((f"    codex_stress_trace = {condition};",
                                f"    codex_stress_trace = ({condition}) && type == bc::champion_type::heart_of_ruin;"),))
    return build(src, directory / "diagnostic", COMPILED_SEED)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--single-boundaries", action="store_true")
    mode.add_argument("--farm", action="store_true")
    mode.add_argument("--farm-state", action="store_true")
    args = parser.parse_args()
    single, farm = args.single_boundaries, args.farm
    frozen = read(HERE / "CPG_POST_WARD_MIXED_STRESS.json")
    assert frozen["seed"] == COMPILED_SEED and frozen["n"] == 800
    (case,) = frozen["affected"]
    rounds = [e["timestamp"]["round"] for e in case["events"]]
    assert rounds == [637, 639, 641] and {e["owner"]["name"] for e in case["events"]} == {"Heart of Ruin"}
    mp = RAW / "maps" / f"{case['map']}.map26a"
    assert bench.digest(mp) == case["map_hash"]
    file, expected = bench.OPPS[case["opponent"]]
    assert bench.digest(bench.CACHE / file) == expected
    trace.REFERENCE_OUT = RAW
    if single:
        phases = ("wardrev", "enemies", "d_farm")
        paths = {p: bench.CACHE / "post-ward-mixed-heart-boundaries" / p for p in phases}
        with ThreadPoolExecutor(max_workers=3) as pool:
            binaries = list(pool.map(lambda p: build_trace(paths[p], rounds, p), phases))
    elif farm:
        phases = ("farm",)
        paths = {"farm": bench.CACHE / "post-ward-mixed-heart-farm"}
        binaries = [build_trace(paths["farm"], rounds, "farm")]
    elif args.farm_state:
        phases = ("farm-state",)
        paths = {"farm-state": bench.CACHE / "post-ward-mixed-heart-farm-state"}
        binaries = [build_trace(paths["farm-state"], rounds, "farm-state")]
    else:
        phases = ("coarse",)
        paths = {"coarse": OUT}
        binaries = [build_trace(OUT, rounds)]
    rows = {}
    for phase, wasm in zip(phases, binaries, strict=True):
        bench.OUT = trace.OUT = paths[phase]
        row = trace.play((case, mp, wasm))
        rows[phase] = {"diagnostic": bench.digest(wasm),
                       "matches": {r["round"]: (r["fuel"] if farm else r["mode"] if args.farm_state else r["phases"])
                                   for r in row["checks"] if r["matched"]}, "row": row}
    report = {"engine": bench.ENGINE, "reference": frozen["wasm"], "seed": COMPILED_SEED}
    name = ("CPG_POST_WARD_MIXED_HEART_BOUNDARIES.json" if single else
            "CPG_POST_WARD_MIXED_HEART_FARM_STATE.json" if args.farm_state else
            "CPG_POST_WARD_MIXED_HEART_FARM.json" if farm else "CPG_POST_WARD_MIXED_HEART_TRACE.json")
    result = {**report, "boundaries": rows} if single else {**report, **rows[phases[0]]}
    with (HERE / name).open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print({**report, "matches": {p: rows[p]["matches"] for p in phases}}, flush=True)


if __name__ == "__main__":
    main()
