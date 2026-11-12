"""Capture a single exact dash boundary without logging in the low-fuel turn."""
import argparse
import json
import os
import re
import subprocess
from zipfile import ZipFile

from bounded_verdict import apply
from large_roster_stress import HERE, OUT as STRESS, bench, read
from pg_siege_resume import prepare

OUT = bench.CACHE / "remaining-dash-1215"
MAP = "pool_604904"


def state(game, output):
    replay = output.with_suffix(".repl26a")
    with ZipFile(next(game.glob("*.repl26a"))) as bundle:
        replay.write_bytes(bundle.read("replay.repl26a"))
    subprocess.run(["node", HERE / "trace_turn.mjs", replay, "1215", "1", "5", output], cwd=bench.ROOT,
                   env={**os.environ, "NFS_REPLAY_ENGINE": "2.0.0"}, check=True)
    result = read(output)
    result["observation"].pop("input")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cost", action="store_true")
    cost = parser.parse_args().cost
    out = bench.CACHE / "remaining-dash-cost" if cost else OUT
    project = out / "diagnostic"
    src = project / "src"
    if cost:
        from pg_travel_tail import prepare as prepare_travel
        prepare_travel(src, True)
    else:
        prepare(src, True)
    bot = src / "bot.cpp"
    data = bot.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    begin = data.index(b"bool Bot::try_dash(")
    end = data.index(b"bool Bot::follow_field(", begin)
    marker = nl.join([b"                cast_done = true;", b"                return true;"])
    injected = nl.join([b"                cast_done = true;",
                        b"                if (round == 1215 && type == bc::champion_type::vendetta)",
                        b"                    codex_dash = {true, bc::round_number(), bc::fuel_remaining(), pos};",
                        b"                return true;"])
    section = data[begin:end]
    assert section.count(marker) == 1
    bot.write_bytes(data[:begin] + section.replace(marker, injected) + data[end:])
    apply(bot, (
        ('#include "bot.h"', '''#include "bot.h"

static struct CodexDashSample {
    bool pending = false;
    std::uint32_t engine_round = 0;
    std::uint64_t fuel = 0;
    vec2 destination{};
} codex_dash;'''),
        ("void Bot::play_turn() {", '''void Bot::play_turn() {
    if (codex_dash.pending) {
        std::printf("CODEX_DASH_BOUNDARY engineR%u fuel%llu (%d,%d)\\n", codex_dash.engine_round,
                    static_cast<unsigned long long>(codex_dash.fuel), codex_dash.destination.x, codex_dash.destination.y);
        codex_dash.pending = false;
    }'''),
    ))
    if cost:
        data = bot.read_bytes()
        begin = data.index(b"bool Bot::try_dash(")
        end = data.index(b"bool Bot::follow_field(", begin)
        block = data[begin:end]
        for anchor, sample in (
            ("        for (int dx = -2; dx <= 2; ++dx)", "codex_dash_cost[0]"),
            ("        if (best == pos) return false;", "codex_dash_cost[1]"),
        ):
            needle = anchor.encode()
            assert block.count(needle) == 1
            block = block.replace(needle,
                ("        if (round == 1215 && type == bc::champion_type::vendetta) " +
                 sample + " = bc::fuel_remaining();").encode() + nl + needle)
        bot.write_bytes(data[:begin] + block + data[end:])
        apply(bot, (
            ("} codex_dash;", """} codex_dash;
static unsigned long long codex_dash_cost[3];"""),
            ("    if (dashed && rb::turn_guard()) return true;", """    if (dashed && rb::turn_guard()) {
        if (codex_dash.pending) codex_dash_cost[2] = bc::fuel_remaining();
        return true;
    }"""),
            ("        codex_dash.pending = false;", """        std::printf("CODEX_DASH_BOUNDARY costs %llu %llu %llu\\n",
                    codex_dash_cost[0], codex_dash_cost[1], codex_dash_cost[2]);
        codex_dash.pending = false;"""),
        ))
    wasm = project / "bot.wasm"
    with (out / "build.log").open("wb") as log:
        subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm], cwd=bench.ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    map_file = STRESS / "maps" / f"{MAP}.map26a"
    assert bench.digest(map_file) == read(HERE / "LARGE_ROSTER_MAPS.json")["maps"][map_file.name]
    opponent, expected = bench.OPPS["p65pack"]
    assert bench.digest(bench.CACHE / opponent) == expected
    bench.OUT = out
    (out / "games").mkdir()
    row = bench.one(("trace", 0, "p65pack", map_file, "B", wasm), log_limit=1048576)
    game = out / "games" / f"trace-0-p65pack-{MAP}-B"
    baseline = (bench.CACHE / f"pg-travel-tail-stress/games/candidate-0-p65pack-{MAP}-B" if cost else
                bench.CACHE / f"pg-siege-resume-exact-stress/games/exact-0-p65pack-{MAP}-B")
    base_state, trace_state = (state(p, out / f"{tag}.json") for tag, p in (("baseline", baseline), ("observed", game)))
    with ZipFile(next(game.glob("*.repl26a"))) as bundle:
        log = bundle.read("team-b.stdout")
    samples = [x.decode("ascii") for x in re.findall(rb"CODEX_DASH_BOUNDARY [^\n]+", log)]
    report = {"wasm": bench.digest(wasm), "row": row, "samples": samples,
              "same_observation": base_state["observation"] == trace_state["observation"],
              "same_first_action": base_state["executed_actions"][:1] == trace_state["executed_actions"][:1],
              "baseline_actions": base_state["executed_actions"], "trace_actions": trace_state["executed_actions"]}
    report_name = "REMAINING_DASH_COST.json" if cost else "REMAINING_DASH_TRACE.json"
    with (HERE / report_name).open("x", encoding="utf8", newline="\n") as f:
        json.dump(report, f, indent=2)
        f.write("\n")
    print({k: v for k, v in report.items() if not k.endswith("actions")}, flush=True)


if __name__ == "__main__":
    main()
